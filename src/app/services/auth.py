"""Simple authentication service for the MVP stage."""

from __future__ import annotations

import hashlib
import re
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Dict, Optional, Any

try:
    from supabase import Client
except ImportError:
    Client = None  # type: ignore

from app.services.email import send_verification_email


class AuthError(Exception):
    """Base class for authentication related errors."""

    status_code: int = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class UserAlreadyExists(AuthError):
    """Raised when attempting to register a duplicate email."""

    status_code = 409


class InvalidCredentials(AuthError):
    """Raised when login credentials fail validation."""

    status_code = 401


class PasswordPolicyError(AuthError):
    """Raised when the supplied password does not meet requirements."""

    status_code = 422


class AccountStatus(str, Enum):
    """Account states stored in Supabase ``auth_accounts`` table."""

    PENDING_VERIFICATION = "pending_verification"
    ACTIVE = "active"
    DISABLED = "disabled"


@dataclass
class AuthUser:
    """Represents an authenticated account."""

    id: str
    email: str
    full_name: str
    password_hash: str
    status: AccountStatus
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None


@dataclass
class AuthRegistration:
    """Represents an onboarding registration awaiting verification."""

    id: str
    email: str
    full_name: str
    password_hash: str
    verification_token: Optional[str]
    verification_sent_at: Optional[datetime]
    verification_expires_at: Optional[datetime]
    status: str
    created_at: datetime
    updated_at: datetime


@dataclass
class RegistrationResult:
    """Outcome of a user registration attempt."""

    account: AuthUser
    registration: AuthRegistration

    # Convenience accessors -------------------------------------------------
    @property
    def id(self) -> str:
        """Proxy to the underlying account identifier."""

        return self.account.id

    @property
    def email(self) -> str:
        """Expose the registered email like an ``AuthUser`` instance."""

        return self.account.email

    @property
    def full_name(self) -> str:
        return self.account.full_name

    @property
    def status(self) -> AccountStatus:
        return self.account.status

    @property
    def password_hash(self) -> str:
        return self.account.password_hash


def _hash_password(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class AccountNotFound(AuthError):
    """Raised when an account lookup fails."""

    status_code = 404


class VerificationError(AuthError):
    """Base error for verification flow."""


class VerificationTokenInvalid(VerificationError):
    """Raised when the supplied verification token is unknown."""

    status_code = 404


class VerificationTokenExpired(VerificationError):
    """Raised when the supplied verification token has expired."""

    status_code = 410


class SupabaseAuthRepository:
    """Real Supabase repository using auth_accounts and onboarding_registrations tables."""

    def __init__(self, db: Optional[Client] = None) -> None:
        self.db = db

    def _map_account(self, data: Dict[str, Any]) -> AuthUser:
        """Map Supabase row to AuthUser dataclass."""
        return AuthUser(
            id=data['id'],
            email=data['email'],
            full_name=data['full_name'],
            password_hash=data['password_hash'],
            status=AccountStatus(data['status']),
            created_at=datetime.fromisoformat(data['created_at']) if isinstance(data['created_at'], str) else data['created_at'],
            updated_at=datetime.fromisoformat(data['updated_at']) if isinstance(data['updated_at'], str) else data['updated_at'],
            last_login_at=datetime.fromisoformat(data['last_login_at']) if data.get('last_login_at') and isinstance(data['last_login_at'], str) else data.get('last_login_at'),
        )

    def _map_registration(self, data: Dict[str, Any]) -> AuthRegistration:
        """Map Supabase row to AuthRegistration dataclass."""
        return AuthRegistration(
            id=data['id'],
            email=data['email'],
            full_name=data['full_name'],
            password_hash=data['password_hash'],
            verification_token=data.get('verification_token'),
            verification_sent_at=datetime.fromisoformat(data['verification_sent_at']) if data.get('verification_sent_at') and isinstance(data['verification_sent_at'], str) else data.get('verification_sent_at'),
            verification_expires_at=datetime.fromisoformat(data['verification_expires_at']) if data.get('verification_expires_at') and isinstance(data['verification_expires_at'], str) else data.get('verification_expires_at'),
            status=data.get('status', 'registered'),
            created_at=datetime.fromisoformat(data['created_at']) if isinstance(data['created_at'], str) else data['created_at'],
            updated_at=datetime.fromisoformat(data['updated_at']) if isinstance(data['updated_at'], str) else data['updated_at'],
        )

    # ``auth_accounts`` helpers -------------------------------------------------
    def upsert_account(
        self,
        *,
        email: str,
        full_name: str,
        password_hash: str,
        status: AccountStatus,
    ) -> AuthUser:
        if not self.db:
            raise AuthError("Database not available")

        # Check if account exists
        existing = self.db.table('auth_accounts').select('*').eq('email', email).execute()

        if existing.data:
            # Update existing account
            account_data = {
                'full_name': full_name,
                'password_hash': password_hash,
                'status': status.value,
                'updated_at': datetime.now(UTC).isoformat()
            }
            result = self.db.table('auth_accounts').update(account_data).eq('email', email).execute()
            return self._map_account(result.data[0])
        else:
            # Create new account
            account_data = {
                'email': email,
                'full_name': full_name,
                'password_hash': password_hash,
                'status': status.value
            }
            result = self.db.table('auth_accounts').insert(account_data).execute()
            return self._map_account(result.data[0])

    def get_account_by_email(self, email: str) -> AuthUser:
        if not self.db:
            raise AuthError("Database not available")

        result = self.db.table('auth_accounts').select('*').eq('email', email).execute()

        if not result.data:
            raise AccountNotFound("Akun tidak ditemukan.")

        return self._map_account(result.data[0])

    def set_account_status(self, account_id: str, status: AccountStatus) -> AuthUser:
        if not self.db:
            raise AuthError("Database not available")

        update_data = {
            'status': status.value,
            'updated_at': datetime.now(UTC).isoformat()
        }
        result = self.db.table('auth_accounts').update(update_data).eq('id', account_id).execute()

        if not result.data:
            raise AccountNotFound("Akun tidak ditemukan.")

        return self._map_account(result.data[0])

    def record_login(self, account_id: str, timestamp: datetime) -> AuthUser:
        if not self.db:
            raise AuthError("Database not available")

        update_data = {
            'last_login_at': timestamp.isoformat(),
            'updated_at': timestamp.isoformat()
        }
        result = self.db.table('auth_accounts').update(update_data).eq('id', account_id).execute()

        if not result.data:
            raise AccountNotFound("Akun tidak ditemukan.")

        return self._map_account(result.data[0])

    # ``onboarding_registrations`` helpers -------------------------------------
    def upsert_registration(
        self,
        *,
        email: str,
        full_name: str,
        password_hash: str,
        token: str,
        expires_at: datetime,
    ) -> AuthRegistration:
        if not self.db:
            raise AuthError("Database not available")

        # Check if registration exists
        existing = self.db.table('onboarding_registrations').select('*').eq('email', email).execute()

        registration_data = {
            'email': email,
            'full_name': full_name,
            'password_hash': password_hash,
            'verification_token': token,
            'verification_sent_at': datetime.now(UTC).isoformat(),
            'verification_expires_at': expires_at.isoformat(),
            'status': 'registered'
        }

        if existing.data:
            # Update existing registration
            result = self.db.table('onboarding_registrations').update(registration_data).eq('email', email).execute()
            return self._map_registration(result.data[0])
        else:
            # Create new registration
            result = self.db.table('onboarding_registrations').insert(registration_data).execute()
            return self._map_registration(result.data[0])

    def get_registration_by_token(self, token: str) -> AuthRegistration:
        if not self.db:
            raise AuthError("Database not available")

        result = self.db.table('onboarding_registrations').select('*').eq('verification_token', token).execute()

        if not result.data:
            raise VerificationTokenInvalid("Token verifikasi tidak ditemukan.")

        return self._map_registration(result.data[0])

    def mark_registration_verified(self, registration_id: str) -> AuthRegistration:
        if not self.db:
            raise AuthError("Database not available")

        update_data = {
            'status': 'email_verified',
            'verification_token': None,
            'verification_expires_at': datetime.now(UTC).isoformat(),
            'updated_at': datetime.now(UTC).isoformat()
        }
        result = self.db.table('onboarding_registrations').update(update_data).eq('id', registration_id).execute()

        if not result.data:
            raise VerificationError("Registrasi tidak ditemukan.")

        return self._map_registration(result.data[0])


class InMemoryAuthRepository:
    """In-memory repository simulating Supabase ``auth`` tables.

    The tests exercise behaviour without a real Supabase instance, therefore the
    repository keeps state in dictionaries while mirroring the schema from the
    migration file.
    """

    def __init__(self) -> None:
        self._accounts_by_id: Dict[str, AuthUser] = {}
        self._accounts_by_email: Dict[str, str] = {}
        self._registrations_by_id: Dict[str, AuthRegistration] = {}
        self._registrations_by_token: Dict[str, str] = {}
        self._registrations_by_email: Dict[str, str] = {}

    # ``auth_accounts`` helpers -------------------------------------------------
    def upsert_account(
        self,
        *,
        email: str,
        full_name: str,
        password_hash: str,
        status: AccountStatus,
    ) -> AuthUser:
        now = datetime.now(UTC)
        existing_id = self._accounts_by_email.get(email)

        if existing_id:
            account = self._accounts_by_id[existing_id]
            account.full_name = full_name
            account.password_hash = password_hash
            account.status = status
            account.updated_at = now
        else:
            account_id = secrets.token_urlsafe(8)
            account = AuthUser(
                id=account_id,
                email=email,
                full_name=full_name,
                password_hash=password_hash,
                status=status,
                created_at=now,
                updated_at=now,
            )
            self._accounts_by_id[account_id] = account
            self._accounts_by_email[email] = account_id
        return account

    def get_account_by_email(self, email: str) -> AuthUser:
        try:
            account_id = self._accounts_by_email[email]
        except KeyError as exc:
            raise AccountNotFound("Akun tidak ditemukan.") from exc
        return self._accounts_by_id[account_id]

    def set_account_status(self, account_id: str, status: AccountStatus) -> AuthUser:
        account = self._accounts_by_id[account_id]
        account.status = status
        account.updated_at = datetime.now(UTC)
        return account

    def record_login(self, account_id: str, timestamp: datetime) -> AuthUser:
        account = self._accounts_by_id[account_id]
        account.last_login_at = timestamp
        account.updated_at = timestamp
        return account

    # ``onboarding_registrations`` helpers -------------------------------------
    def upsert_registration(
        self,
        *,
        email: str,
        full_name: str,
        password_hash: str,
        token: str,
        expires_at: datetime,
    ) -> AuthRegistration:
        now = datetime.now(UTC)
        existing_id = self._registrations_by_email.get(email)

        if existing_id:
            registration = self._registrations_by_id[existing_id]
            if registration.verification_token:
                self._registrations_by_token.pop(registration.verification_token, None)
            registration.full_name = full_name
            registration.password_hash = password_hash
            registration.verification_token = token
            registration.verification_expires_at = expires_at
            registration.verification_sent_at = now
            registration.updated_at = now
            registration.status = "registered"
            self._registrations_by_token[token] = existing_id
        else:
            registration_id = secrets.token_urlsafe(8)
            registration = AuthRegistration(
                id=registration_id,
                email=email,
                full_name=full_name,
                password_hash=password_hash,
                verification_token=token,
                verification_sent_at=now,
                verification_expires_at=expires_at,
                status="registered",
                created_at=now,
                updated_at=now,
            )
            self._registrations_by_id[registration_id] = registration
            self._registrations_by_email[email] = registration_id
            self._registrations_by_token[token] = registration_id
        return registration

    def get_registration_by_token(self, token: str) -> AuthRegistration:
        try:
            registration_id = self._registrations_by_token[token]
        except KeyError as exc:
            raise VerificationTokenInvalid("Token verifikasi tidak ditemukan.") from exc
        return self._registrations_by_id[registration_id]

    def mark_registration_verified(self, registration_id: str) -> AuthRegistration:
        registration = self._registrations_by_id[registration_id]
        registration.status = "email_verified"
        registration.updated_at = datetime.now(UTC)
        if registration.verification_token:
            self._registrations_by_token.pop(registration.verification_token, None)
        registration.verification_token = None
        registration.verification_expires_at = registration.updated_at
        return registration


class AuthService:
    """Authentication workflow backed by the Supabase repository."""

    def __init__(self, repository = None, db: Optional[Client] = None) -> None:
        if repository is not None:
            self._repository = repository
        elif db is not None:
            # Use Supabase if db client is provided
            self._repository = SupabaseAuthRepository(db)
        else:
            # Fall back to in-memory for tests
            self._repository = InMemoryAuthRepository()

    def register_user(self, *, email: str, full_name: str, password: str) -> RegistrationResult:
        normalized_email = email.strip().lower()
        self._validate_email(normalized_email)
        self._validate_full_name(full_name)
        self._validate_password(password)

        password_hash = _hash_password(password)

        try:
            existing_account = self._repository.get_account_by_email(normalized_email)
        except AccountNotFound:
            existing_account = None

        if existing_account:
            raise UserAlreadyExists("Email sudah terdaftar. Silakan login.")

        verification_token = secrets.token_urlsafe(24)
        verification_expires = datetime.now(UTC) + timedelta(hours=24)

        account = self._repository.upsert_account(
            email=normalized_email,
            full_name=full_name.strip(),
            password_hash=password_hash,
            status=AccountStatus.PENDING_VERIFICATION,
        )

        registration = self._repository.upsert_registration(
            email=normalized_email,
            full_name=full_name.strip(),
            password_hash=password_hash,
            token=verification_token,
            expires_at=verification_expires,
        )

        send_verification_email(account.email, verification_token)

        return RegistrationResult(account=account, registration=registration)

    def verify_email(self, *, token: str) -> AuthUser:
        registration = self._repository.get_registration_by_token(token)
        now = datetime.now(UTC)
        if registration.verification_expires_at and registration.verification_expires_at < now:
            raise VerificationTokenExpired("Token verifikasi sudah kedaluwarsa.")

        account = self._repository.get_account_by_email(registration.email)
        account = self._repository.set_account_status(account.id, AccountStatus.ACTIVE)
        self._repository.mark_registration_verified(registration.id)
        return account

    def verify_registration(self, *, token: str) -> AuthUser:
        return self.verify_email(token=token)

    def authenticate(self, *, email: str, password: str) -> AuthUser:
        normalized_email = email.strip().lower()
        try:
            user = self._repository.get_account_by_email(normalized_email)
        except AccountNotFound as exc:
            raise InvalidCredentials("Email atau password salah.") from exc

        if user.status is AccountStatus.DISABLED:
            raise InvalidCredentials("Akun belum aktif. Selesaikan verifikasi email terlebih dahulu.")

        if not secrets.compare_digest(user.password_hash, _hash_password(password)):
            raise InvalidCredentials("Email atau password salah.")

        now = datetime.now(UTC)
        self._repository.record_login(user.id, now)
        return user

    def _validate_email(self, email: str) -> None:
        pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        if not re.match(pattern, email):
            raise AuthError("Format email tidak valid.")

    def _validate_full_name(self, full_name: str) -> None:
        if len(full_name.strip()) < 3:
            raise AuthError("Nama lengkap minimal 3 karakter.")

    def _validate_password(self, password: str) -> None:
        if len(password) < 8:
            raise PasswordPolicyError("Password minimal 8 karakter.")
        if not re.search(r"[A-Za-z]", password) or not re.search(r"[0-9]", password):
            raise PasswordPolicyError("Password harus mengandung huruf dan angka.")


auth_service = AuthService()
"""Singleton instance to be shared across the application."""
