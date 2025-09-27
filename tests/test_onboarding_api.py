import pytest
from fastapi import HTTPException

from app.api.routes.onboarding import (
    RegistrationRequest,
    VerificationRequest,
    ProfileRequest,
    ResendRequest,
    register_user,
    verify_email,
    complete_profile,
    get_event_log,
    resend_token,
)
from app.services.onboarding import OnboardingService


def test_onboarding_flow_handlers():
    service = OnboardingService()

    registration = register_user(
        RegistrationRequest(
            email="artisan@sensasiwangi.id",
            full_name="Ayu Laras",
            password="secret123",
        ),
        service=service,
    )

    assert registration.status.value == "registered"
    assert registration.verification_token is not None

    verification = verify_email(
        VerificationRequest(onboarding_id=registration.onboarding_id, token=registration.verification_token or ""),
        service=service,
    )

    assert verification.status.value == "email_verified"

    profile = complete_profile(
        ProfileRequest(
            onboarding_id=registration.onboarding_id,
            display_name="Studio Senja",
            business_goal="Skala produksi parfum",
            experience_level="Eksperimen Mandiri",
        ),
        service=service,
    )

    assert profile.progress["is_complete"] is True

    events = get_event_log(registration.onboarding_id, service=service)
    event_names = [event["event"] for event in events.events]
    assert "registered" in event_names
    assert "email_verified" in event_names
    assert "profile_completed" in event_names

    with pytest.raises(HTTPException) as excinfo:
        resend_token(ResendRequest(onboarding_id=registration.onboarding_id), service=service)
    assert excinfo.value.status_code == 400


def test_verify_email_with_invalid_token():
    service = OnboardingService()
    registration = register_user(
        RegistrationRequest(
            email="artisan@sensasiwangi.id",
            full_name="Ayu Laras",
            password="secret123",
        ),
        service=service,
    )

    with pytest.raises(HTTPException) as excinfo:
        verify_email(
            VerificationRequest(onboarding_id=registration.onboarding_id, token="SALAH"),
            service=service,
        )

    assert excinfo.value.status_code == 400
    assert "Token" in excinfo.value.detail

    resend = resend_token(ResendRequest(onboarding_id=registration.onboarding_id), service=service)
    assert resend.verification_token is not None
