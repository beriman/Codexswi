"""Simple authentication service for the MVP stage."""

from __future__ import annotations

import hashlib
import re
import secrets
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, Optional


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
    """Minimal account status representation."""

    ACTIVE = "active"
    DISABLED = "disabled"


@dataclass
class AuthUser:
    """Represents a registered user."""

    id: str
    email: str
    full_name: str
    password_hash: str
    status: AccountStatus
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None


def _hash_password(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class AuthService:
    """Minimal in-memory authentication workflow for demos and tests."""

    def __init__(self) -> None:
        self._users_by_id: Dict[str, AuthUser] = {}
        self._users_by_email: Dict[str, str] = {}

    def register_user(self, *, email: str, full_name: str, password: str) -> AuthUser:
        normalized_email = email.strip().lower()
        self._validate_email(normalized_email)
        self._validate_full_name(full_name)
        self._validate_password(password)

        if normalized_email in self._users_by_email:
            raise UserAlreadyExists("Email sudah terdaftar. Silakan login.")

        user_id = secrets.token_urlsafe(8)
        now = datetime.utcnow()
        user = AuthUser(
            id=user_id,
            email=normalized_email,
            full_name=full_name.strip(),
            password_hash=_hash_password(password),
            status=AccountStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        self._users_by_id[user_id] = user
        self._users_by_email[normalized_email] = user_id
        return user

    def authenticate(self, *, email: str, password: str) -> AuthUser:
        normalized_email = email.strip().lower()
        user = self._get_user_by_email(normalized_email)

        if user.status is not AccountStatus.ACTIVE:
            raise InvalidCredentials("Akun tidak aktif.")

        if not secrets.compare_digest(user.password_hash, _hash_password(password)):
            raise InvalidCredentials("Email atau password salah.")

        now = datetime.utcnow()
        user.last_login_at = now
        user.updated_at = now
        return user

    def _get_user_by_email(self, email: str) -> AuthUser:
        try:
            user_id = self._users_by_email[email]
        except KeyError as exc:
            raise InvalidCredentials("Email atau password salah.") from exc
        return self._users_by_id[user_id]

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
