"""Authentication service with Supabase persistence.

This is the refactored version of auth.py that uses Supabase tables instead
of in-memory storage. It replaces the original in-memory implementation while
maintaining the same API interface.

Migration path:
    1. Deploy this alongside existing auth.py
    2. Update routes to import from auth_supabase instead of auth
    3. Test thoroughly
    4. Remove old auth.py when confidence is high
"""

from __future__ import annotations

import hashlib
import re
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Dict, Optional

from supabase import Client

from app.core.supabase import require_supabase
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


class VerificationError(AuthError):
    """Raised when email verification fails."""

    status_code = 400


class AccountStatus(str, Enum):
    """Account states stored in Supabase auth_accounts table."""

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

    @property
    def id(self) -> str:
        """Proxy to the underlying account identifier."""
        return self.account.id

    @property
    def email(self) -> str:
        """Expose the registered email like an AuthUser instance."""
        return self.account.email

    @property
    def full_name(self) -> str:
        """Expose the full name."""
        return self.account.full_name


class AuthService:
    """Authentication service using Supabase for persistence."""

    def __init__(self, db: Optional[Client] = None):
        """Initialize auth service with Supabase client.
        
        Args:
            db: Supabase client. If None, will use require_supabase()
        """
        self.db = db or require_supabase()
        self.password_min_length = 8
        self.verification_token_expiry_hours = 24
        self.session_expiry_days = 30

    # -------------------------------------------------------------------------
    # Registration & Verification
    # -------------------------------------------------------------------------

    def register(
        self,
        email: str,
        password: str,
        full_name: str,
        marketing_opt_in: bool = False
    ) -> RegistrationResult:
        """Register new user in Supabase auth_accounts table.
        
        Args:
            email: User email address
            password: Plain text password (will be hashed)
            full_name: User's full name
            marketing_opt_in: Whether user opted in to marketing emails
        
        Returns:
            RegistrationResult with account and registration details
        
        Raises:
            UserAlreadyExists: If email is already registered
            PasswordPolicyError: If password doesn't meet requirements
        """
        # Normalize email
        email = email.strip().lower()
        
        # Validate password
        self._validate_password(password)
        
        # Check if email exists
        existing = self.db.table('auth_accounts') \
            .select('id') \
            .eq('email', email) \
            .execute()
        
        if existing.data:
            raise UserAlreadyExists("Email sudah terdaftar")
        
        # Hash password
        password_hash = self._hash_password(password)
        
        # Create account
        account_data = {
            'email': email,
            'password_hash': password_hash,
            'full_name': full_name,
            'status': AccountStatus.PENDING_VERIFICATION.value
        }
        
        account_result = self.db.table('auth_accounts') \
            .insert(account_data) \
            .execute()
        
        if not account_result.data:
            raise AuthError("Gagal membuat akun")
        
        account = account_result.data[0]
        
        # Create registration record for verification flow
        verification_token = secrets.token_urlsafe(32)
        expires_at = datetime.now(UTC) + timedelta(hours=self.verification_token_expiry_hours)
        
        registration_data = {
            'email': email,
            'full_name': full_name,
            'password_hash': password_hash,
            'status': 'registered',
            'verification_token': verification_token,
            'verification_sent_at': datetime.now(UTC).isoformat(),
            'verification_expires_at': expires_at.isoformat(),
            'marketing_opt_in': marketing_opt_in
        }
        
        registration_result = self.db.table('onboarding_registrations') \
            .insert(registration_data) \
            .execute()
        
        if not registration_result.data:
            raise AuthError("Gagal membuat registration record")
        
        registration = registration_result.data[0]
        
        # Send verification email
        send_verification_email(email, verification_token)
        
        return RegistrationResult(
            account=self._map_account(account),
            registration=self._map_registration(registration)
        )

    def verify_email(self, token: str) -> AuthUser:
        """Verify email using token from registration.
        
        Args:
            token: Verification token from email
        
        Returns:
            Verified AuthUser
        
        Raises:
            VerificationError: If token is invalid or expired
        """
        # Find registration with token
        result = self.db.table('onboarding_registrations') \
            .select('*') \
            .eq('verification_token', token) \
            .execute()
        
        if not result.data:
            raise VerificationError("Token verifikasi tidak valid")
        
        registration = result.data[0]
        
        # Check expiry
        expires_at = datetime.fromisoformat(registration['verification_expires_at'])
        if expires_at < datetime.now(UTC):
            raise VerificationError("Token verifikasi sudah kadaluarsa")
        
        # Update account status to active
        account_update = self.db.table('auth_accounts') \
            .update({'status': AccountStatus.ACTIVE.value}) \
            .eq('email', registration['email']) \
            .execute()
        
        if not account_update.data:
            raise AuthError("Gagal mengaktifkan akun")
        
        # Update registration status
        self.db.table('onboarding_registrations') \
            .update({'status': 'email_verified'}) \
            .eq('id', registration['id']) \
            .execute()
        
        # Log onboarding event
        self.db.table('onboarding_events') \
            .insert({
                'onboarding_id': registration['id'],
                'event': 'email_verified',
                'metadata': {'verified_at': datetime.now(UTC).isoformat()}
            }) \
            .execute()
        
        return self._map_account(account_update.data[0])

    # -------------------------------------------------------------------------
    # Login & Session Management
    # -------------------------------------------------------------------------

    def login(self, email: str, password: str) -> AuthUser:
        """Authenticate user and return account details.
        
        Args:
            email: User email
            password: Plain text password
        
        Returns:
            Authenticated AuthUser
        
        Raises:
            InvalidCredentials: If email/password is wrong
            AuthError: If account is disabled
        """
        # Normalize email
        email = email.strip().lower()
        
        # Get account
        result = self.db.table('auth_accounts') \
            .select('*') \
            .eq('email', email) \
            .execute()
        
        if not result.data:
            raise InvalidCredentials("Email atau password salah")
        
        account = result.data[0]
        
        # Verify password
        if not self._verify_password(password, account['password_hash']):
            raise InvalidCredentials("Email atau password salah")
        
        # Check status
        if account['status'] == AccountStatus.DISABLED.value:
            raise AuthError("Akun telah dinonaktifkan")
        
        # Update last login
        self.db.table('auth_accounts') \
            .update({'last_login_at': datetime.now(UTC).isoformat()}) \
            .eq('id', account['id']) \
            .execute()
        
        return self._map_account(account)

    def create_session(
        self,
        account_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> str:
        """Create a new session token for user.
        
        Args:
            account_id: User account ID
            ip_address: Client IP address (optional)
            user_agent: Client user agent (optional)
        
        Returns:
            Session token string
        """
        session_token = secrets.token_urlsafe(32)
        expires_at = datetime.now(UTC) + timedelta(days=self.session_expiry_days)
        
        session_data = {
            'account_id': account_id,
            'session_token': session_token,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'expires_at': expires_at.isoformat()
        }
        
        self.db.table('auth_sessions') \
            .insert(session_data) \
            .execute()
        
        return session_token

    def verify_session(self, session_token: str) -> Optional[AuthUser]:
        """Verify session token and return user.
        
        Args:
            session_token: Session token to verify
        
        Returns:
            AuthUser if valid, None if invalid/expired
        """
        # Get session
        result = self.db.table('auth_sessions') \
            .select('account_id, expires_at') \
            .eq('session_token', session_token) \
            .execute()
        
        if not result.data:
            return None
        
        session = result.data[0]
        
        # Check expiry
        expires_at = datetime.fromisoformat(session['expires_at'])
        if expires_at < datetime.now(UTC):
            return None
        
        # Get account
        account_result = self.db.table('auth_accounts') \
            .select('*') \
            .eq('id', session['account_id']) \
            .execute()
        
        if not account_result.data:
            return None
        
        return self._map_account(account_result.data[0])

    def logout(self, session_token: str) -> None:
        """Invalidate a session token.
        
        Args:
            session_token: Session token to invalidate
        """
        self.db.table('auth_sessions') \
            .delete() \
            .eq('session_token', session_token) \
            .execute()

    # -------------------------------------------------------------------------
    # Password Management
    # -------------------------------------------------------------------------

    def _validate_password(self, password: str) -> None:
        """Validate password meets policy requirements.
        
        Args:
            password: Plain text password
        
        Raises:
            PasswordPolicyError: If password doesn't meet requirements
        """
        if len(password) < self.password_min_length:
            raise PasswordPolicyError(
                f"Password harus minimal {self.password_min_length} karakter"
            )
        
        # Add more validation as needed
        # - Must contain uppercase
        # - Must contain number
        # - Must contain special char
        # etc.

    def _hash_password(self, password: str) -> str:
        """Hash password using PBKDF2 with SHA256.
        
        Args:
            password: Plain text password
        
        Returns:
            Hashed password string
        """
        salt = secrets.token_bytes(32)
        key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return salt.hex() + key.hex()

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against stored hash.
        
        Args:
            password: Plain text password
            password_hash: Stored hash
        
        Returns:
            True if password matches, False otherwise
        """
        try:
            salt = bytes.fromhex(password_hash[:64])
            stored_key = password_hash[64:]
            key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
            return key.hex() == stored_key
        except (ValueError, AttributeError):
            return False

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    def _map_account(self, data: Dict) -> AuthUser:
        """Map database row to AuthUser dataclass.
        
        Args:
            data: Database row dict
        
        Returns:
            AuthUser instance
        """
        return AuthUser(
            id=data['id'],
            email=data['email'],
            full_name=data['full_name'],
            password_hash=data['password_hash'],
            status=AccountStatus(data['status']),
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            last_login_at=datetime.fromisoformat(data['last_login_at']) if data.get('last_login_at') else None
        )

    def _map_registration(self, data: Dict) -> AuthRegistration:
        """Map database row to AuthRegistration dataclass.
        
        Args:
            data: Database row dict
        
        Returns:
            AuthRegistration instance
        """
        return AuthRegistration(
            id=data['id'],
            email=data['email'],
            full_name=data['full_name'],
            password_hash=data['password_hash'],
            verification_token=data.get('verification_token'),
            verification_sent_at=datetime.fromisoformat(data['verification_sent_at']) if data.get('verification_sent_at') else None,
            verification_expires_at=datetime.fromisoformat(data['verification_expires_at']) if data.get('verification_expires_at') else None,
            status=data['status'],
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at'])
        )


# Singleton instance for convenience
_auth_service_instance: Optional[AuthService] = None


def get_auth_service(db: Optional[Client] = None) -> AuthService:
    """Get or create singleton auth service instance.
    
    Args:
        db: Optional Supabase client
    
    Returns:
        AuthService instance
    """
    global _auth_service_instance
    
    if _auth_service_instance is None:
        _auth_service_instance = AuthService(db)
    
    return _auth_service_instance
