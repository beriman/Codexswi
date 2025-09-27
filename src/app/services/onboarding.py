"""Services and data structures to orchestrate the onboarding flow."""

from __future__ import annotations

import hashlib
import re
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Iterable, List, MutableMapping, Optional


class OnboardingError(Exception):
    """Base class for onboarding related errors."""

    status_code: int = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class EmailAlreadyRegistered(OnboardingError):
    status_code = 409


class RegistrationRateLimited(OnboardingError):
    status_code = 429


class OnboardingNotFound(OnboardingError):
    status_code = 404


class VerificationTokenExpired(OnboardingError):
    status_code = 410


class VerificationAttemptsExceeded(OnboardingError):
    status_code = 423


class InvalidVerificationToken(OnboardingError):
    status_code = 400


class ProfileIncomplete(OnboardingError):
    status_code = 400


class OnboardingStatus(str, Enum):
    """Represents the current step of a user in the onboarding flow."""

    REGISTERED = "registered"
    EMAIL_VERIFIED = "email_verified"
    PROFILE_COMPLETED = "profile_completed"


@dataclass
class OnboardingEvent:
    """Represents a log entry generated during the onboarding flow."""

    onboarding_id: str
    event: str
    timestamp: datetime
    metadata: dict = field(default_factory=dict)


@dataclass
class OnboardingProfile:
    """Stores optional profile information collected during onboarding."""

    display_name: str
    business_goal: str
    experience_level: str


@dataclass
class OnboardingUser:
    """Aggregates onboarding state for a specific user."""

    id: str
    email: str
    full_name: str
    password_hash: str
    status: OnboardingStatus
    created_at: datetime
    updated_at: datetime
    verification_token: Optional[str] = None
    verification_expires_at: Optional[datetime] = None
    verification_attempts: int = 0
    profile: Optional[OnboardingProfile] = None


def _hash_password(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class OnboardingService:
    """Coordinator for the onboarding workflow."""

    TOKEN_TTL = timedelta(minutes=15)
    RATE_LIMIT_WINDOW = timedelta(seconds=10)
    MAX_VERIFICATION_ATTEMPTS = 3

    def __init__(self) -> None:
        self._users_by_id: Dict[str, OnboardingUser] = {}
        self._users_by_email: Dict[str, str] = {}
        self._events: List[OnboardingEvent] = []
        self._rate_limit: MutableMapping[str, datetime] = {}

    def register_user(
        self,
        *,
        email: str,
        full_name: str,
        password: str,
        marketing_opt_in: bool = False,
        now: Optional[datetime] = None,
    ) -> OnboardingUser:
        """Register a new onboarding user and issue an email token."""

        now = now or datetime.utcnow()

        normalized_email = email.strip().lower()
        self._validate_email(normalized_email)
        self._validate_password(password)
        self._validate_full_name(full_name)

        last_attempt = self._rate_limit.get(normalized_email)
        if last_attempt and now - last_attempt < self.RATE_LIMIT_WINDOW:
            retry_after = int((self.RATE_LIMIT_WINDOW - (now - last_attempt)).total_seconds()) + 1
            raise RegistrationRateLimited(
                f"Percobaan registrasi terlalu sering. Coba lagi dalam {retry_after} detik."
            )

        if normalized_email in self._users_by_email:
            raise EmailAlreadyRegistered("Email sudah terdaftar untuk onboarding.")

        onboarding_id = secrets.token_urlsafe(8)
        password_hash = _hash_password(password)

        user = OnboardingUser(
            id=onboarding_id,
            email=normalized_email,
            full_name=full_name.strip(),
            password_hash=password_hash,
            status=OnboardingStatus.REGISTERED,
            created_at=now,
            updated_at=now,
        )

        self._issue_verification_token(user, now=now)

        self._users_by_id[onboarding_id] = user
        self._users_by_email[normalized_email] = onboarding_id
        self._rate_limit[normalized_email] = now

        self._log(
            user.id,
            "registered",
            now,
            {"email": normalized_email, "marketing_opt_in": marketing_opt_in},
        )
        self._log(
            user.id,
            "verification_token_issued",
            now,
            {
                "expires_at": user.verification_expires_at.isoformat() if user.verification_expires_at else None,
                "dispatch_ms": 1200,
            },
        )

        return user

    def verify_email(
        self,
        *,
        onboarding_id: str,
        token: str,
        now: Optional[datetime] = None,
    ) -> OnboardingUser:
        """Validate an email verification token."""

        now = now or datetime.utcnow()
        user = self._get_user(onboarding_id)

        if user.verification_attempts >= self.MAX_VERIFICATION_ATTEMPTS:
            raise VerificationAttemptsExceeded(
                "Percobaan verifikasi melebihi batas. Hubungi dukungan kami."
            )

        if not user.verification_token or not user.verification_expires_at:
            raise InvalidVerificationToken("Tidak ada token verifikasi aktif.")

        if now > user.verification_expires_at:
            user.verification_token = None
            raise VerificationTokenExpired("Token verifikasi telah kedaluwarsa.")

        if secrets.compare_digest(user.verification_token, token.strip()):
            user.status = OnboardingStatus.EMAIL_VERIFIED
            user.verification_token = None
            user.verification_expires_at = None
            user.verification_attempts = 0
            user.updated_at = now
            self._log(user.id, "email_verified", now)
        else:
            user.verification_attempts += 1
            self._log(
                user.id,
                "verification_failed",
                now,
                {"attempts": user.verification_attempts},
            )
            raise InvalidVerificationToken("Token verifikasi tidak valid.")

        return user

    def resend_verification_token(
        self,
        *,
        onboarding_id: str,
        now: Optional[datetime] = None,
    ) -> str:
        """Generate a new verification token for a user."""

        now = now or datetime.utcnow()
        user = self._get_user(onboarding_id)

        if user.status is not OnboardingStatus.REGISTERED:
            raise OnboardingError("Email sudah terverifikasi, token baru tidak diperlukan.")

        token = self._issue_verification_token(user, now=now)
        self._log(
            user.id,
            "verification_token_resent",
            now,
            {"expires_at": user.verification_expires_at.isoformat()},
        )
        return token

    def complete_profile(
        self,
        *,
        onboarding_id: str,
        display_name: str,
        business_goal: str,
        experience_level: str,
        now: Optional[datetime] = None,
    ) -> OnboardingUser:
        """Mark the onboarding profile as completed."""

        now = now or datetime.utcnow()
        user = self._get_user(onboarding_id)

        if user.status is not OnboardingStatus.EMAIL_VERIFIED:
            raise ProfileIncomplete("Email harus terverifikasi sebelum melengkapi profil.")

        profile = OnboardingProfile(
            display_name=display_name.strip(),
            business_goal=business_goal.strip(),
            experience_level=experience_level.strip(),
        )
        user.profile = profile
        user.status = OnboardingStatus.PROFILE_COMPLETED
        user.updated_at = now
        self._log(
            user.id,
            "profile_completed",
            now,
            {"experience_level": experience_level.strip()},
        )
        return user

    def get_progress(self, onboarding_id: str) -> dict:
        user = self._get_user(onboarding_id)
        step_index = {
            OnboardingStatus.REGISTERED: 1,
            OnboardingStatus.EMAIL_VERIFIED: 2,
            OnboardingStatus.PROFILE_COMPLETED: 3,
        }[user.status]

        return {
            "onboarding_id": user.id,
            "email": user.email,
            "status": user.status.value,
            "step_index": step_index,
            "total_steps": 3,
            "is_complete": user.status is OnboardingStatus.PROFILE_COMPLETED,
            "profile": (
                {
                    "display_name": user.profile.display_name,
                    "business_goal": user.profile.business_goal,
                    "experience_level": user.profile.experience_level,
                }
                if user.profile
                else None
            ),
            "verification": {
                "active": bool(user.verification_token),
                "expires_at": user.verification_expires_at.isoformat()
                if user.verification_expires_at
                else None,
            },
        }

    def get_events(self, onboarding_id: str) -> List[OnboardingEvent]:
        return [event for event in self._events if event.onboarding_id == onboarding_id]

    def get_user(self, onboarding_id: str) -> OnboardingUser:
        return self._get_user(onboarding_id)

    def iter_users(self) -> Iterable[OnboardingUser]:
        return list(self._users_by_id.values())

    def _get_user(self, onboarding_id: str) -> OnboardingUser:
        try:
            return self._users_by_id[onboarding_id]
        except KeyError as exc:  # pragma: no cover - defensive
            raise OnboardingNotFound("Onboarding ID tidak ditemukan.") from exc

    def _issue_verification_token(
        self,
        user: OnboardingUser,
        *,
        now: datetime,
    ) -> str:
        token = secrets.token_urlsafe(6)
        user.verification_token = token
        user.verification_expires_at = now + self.TOKEN_TTL
        user.updated_at = now
        user.verification_attempts = 0
        return token

    def _log(
        self,
        onboarding_id: str,
        event: str,
        timestamp: datetime,
        metadata: Optional[dict] = None,
    ) -> None:
        self._events.append(
            OnboardingEvent(
                onboarding_id=onboarding_id,
                event=event,
                timestamp=timestamp,
                metadata=metadata or {},
            )
        )

    def _validate_email(self, email: str) -> None:
        pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        if not re.match(pattern, email):
            raise OnboardingError("Format email tidak valid.")

    def _validate_password(self, password: str) -> None:
        if len(password) < 8:
            raise OnboardingError("Password minimal 8 karakter.")
        if not re.search(r"[A-Za-z]", password) or not re.search(r"[0-9]", password):
            raise OnboardingError("Password harus mengandung huruf dan angka.")

    def _validate_full_name(self, full_name: str) -> None:
        if len(full_name.strip()) < 3:
            raise OnboardingError("Nama lengkap minimal 3 karakter.")


onboarding_service = OnboardingService()
"""Singleton instance used across the application."""
