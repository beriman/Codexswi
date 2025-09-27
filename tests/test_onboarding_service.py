from datetime import datetime, timedelta

import pytest

from app.services.onboarding import (
    OnboardingService,
    OnboardingStatus,
    RegistrationRateLimited,
    VerificationTokenExpired,
    VerificationAttemptsExceeded,
    InvalidVerificationToken,
    ProfileIncomplete,
    OnboardingError,
)


def test_register_user_generates_token_and_logs():
    service = OnboardingService()
    now = datetime(2024, 4, 1, 9, 0, 0)

    user = service.register_user(
        email="artisan@sensasiwangi.id",
        full_name="Ayu Laras",
        password="secret123",
        now=now,
    )

    assert user.status is OnboardingStatus.REGISTERED
    assert user.verification_token is not None

    progress = service.get_progress(user.id)
    assert progress["step_index"] == 1
    assert progress["verification"]["expires_at"] is not None

    events = service.get_events(user.id)
    assert [event.event for event in events][:2] == ["registered", "verification_token_issued"]


def test_register_user_rate_limited():
    service = OnboardingService()
    now = datetime(2024, 4, 1, 9, 0, 0)

    service.register_user(
        email="artisan@sensasiwangi.id",
        full_name="Ayu Laras",
        password="secret123",
        now=now,
    )

    with pytest.raises(RegistrationRateLimited):
        service.register_user(
            email="artisan@sensasiwangi.id",
            full_name="Ayu Laras",
            password="secret123",
            now=now + timedelta(seconds=5),
        )


def test_verify_email_success_and_attempts_reset():
    service = OnboardingService()
    now = datetime(2024, 4, 1, 9, 0, 0)
    user = service.register_user(
        email="artisan@sensasiwangi.id",
        full_name="Ayu Laras",
        password="secret123",
        now=now,
    )

    with pytest.raises(InvalidVerificationToken):
        service.verify_email(
            onboarding_id=user.id,
            token="salah",
            now=now + timedelta(minutes=1),
        )

    assert service.get_user(user.id).verification_attempts == 1

    service.verify_email(
        onboarding_id=user.id,
        token=user.verification_token or "",
        now=now + timedelta(minutes=2),
    )

    verified = service.get_user(user.id)
    assert verified.status is OnboardingStatus.EMAIL_VERIFIED
    assert verified.verification_token is None
    assert verified.verification_attempts == 0


def test_verify_email_expired_token():
    service = OnboardingService()
    now = datetime(2024, 4, 1, 9, 0, 0)
    user = service.register_user(
        email="artisan@sensasiwangi.id",
        full_name="Ayu Laras",
        password="secret123",
        now=now,
    )

    with pytest.raises(VerificationTokenExpired):
        service.verify_email(
            onboarding_id=user.id,
            token=user.verification_token or "",
            now=now + service.TOKEN_TTL + timedelta(seconds=1),
        )


def test_complete_profile_requires_verification():
    service = OnboardingService()
    now = datetime(2024, 4, 1, 9, 0, 0)
    user = service.register_user(
        email="artisan@sensasiwangi.id",
        full_name="Ayu Laras",
        password="secret123",
        now=now,
    )

    with pytest.raises(ProfileIncomplete):
        service.complete_profile(
            onboarding_id=user.id,
            display_name="Studio Senja",
            business_goal="Skala produksi parfum",
            experience_level="Eksperimen Mandiri",
            now=now,
        )

    service.verify_email(
        onboarding_id=user.id,
        token=user.verification_token or "",
        now=now + timedelta(minutes=2),
    )

    service.complete_profile(
        onboarding_id=user.id,
        display_name="Studio Senja",
        business_goal="Skala produksi parfum",
        experience_level="Eksperimen Mandiri",
        now=now + timedelta(minutes=5),
    )

    progress = service.get_progress(user.id)
    assert progress["is_complete"] is True
    assert progress["profile"]["display_name"] == "Studio Senja"


def test_verification_attempt_limit():
    service = OnboardingService()
    now = datetime(2024, 4, 1, 9, 0, 0)
    user = service.register_user(
        email="artisan@sensasiwangi.id",
        full_name="Ayu Laras",
        password="secret123",
        now=now,
    )

    for attempt in range(3):
        with pytest.raises(InvalidVerificationToken):
            service.verify_email(
                onboarding_id=user.id,
                token="tidak cocok",
                now=now + timedelta(minutes=attempt + 1),
            )

    with pytest.raises(VerificationAttemptsExceeded):
        service.verify_email(
            onboarding_id=user.id,
            token="tidak cocok",
            now=now + timedelta(minutes=5),
        )


def test_resend_token_only_for_unverified():
    service = OnboardingService()
    now = datetime(2024, 4, 1, 9, 0, 0)
    user = service.register_user(
        email="artisan@sensasiwangi.id",
        full_name="Ayu Laras",
        password="secret123",
        now=now,
    )

    original_token = user.verification_token
    new_token = service.resend_verification_token(onboarding_id=user.id, now=now + timedelta(minutes=1))
    assert new_token != original_token

    service.verify_email(
        onboarding_id=user.id,
        token=new_token,
        now=now + timedelta(minutes=2),
    )

    with pytest.raises(OnboardingError):
        service.resend_verification_token(onboarding_id=user.id)
