"""API endpoints for the onboarding workflow."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Type, TypeVar

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field, ValidationError

from app.services.onboarding import (
    OnboardingEvent,
    OnboardingService,
    OnboardingStatus,
    OnboardingError,
    onboarding_service,
)

router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])

ModelT = TypeVar("ModelT", bound=BaseModel)


class RegistrationRequest(BaseModel):
    email: str = Field(..., pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", description="Email utama pengguna")
    full_name: str = Field(..., min_length=3, max_length=120)
    password: str = Field(..., min_length=8, max_length=128)
    marketing_opt_in: bool | None = Field(False, description="Apakah pengguna ingin menerima email komunitas")


class RegistrationResponse(BaseModel):
    onboarding_id: str
    status: OnboardingStatus
    verification_expires_at: datetime | None
    progress: Dict[str, Any]
    verification_token: str | None = Field(None, description="Token debug yang disediakan untuk lingkungan pengujian")


class VerificationRequest(BaseModel):
    onboarding_id: str
    token: str = Field(..., min_length=4, max_length=64)


class VerificationResponse(BaseModel):
    onboarding_id: str
    status: OnboardingStatus
    progress: Dict[str, Any]


class ProfileRequest(BaseModel):
    onboarding_id: str
    display_name: str = Field(..., min_length=2, max_length=80)
    business_goal: str = Field(..., min_length=3, max_length=160)
    experience_level: str = Field(..., min_length=3, max_length=120)


class ProfileResponse(BaseModel):
    onboarding_id: str
    status: OnboardingStatus
    profile: Dict[str, Any]
    progress: Dict[str, Any]


class EventLogResponse(BaseModel):
    onboarding_id: str
    events: List[Dict[str, Any]]


class ResendRequest(BaseModel):
    onboarding_id: str


def get_onboarding_service() -> OnboardingService:
    return onboarding_service


def _serialize_events(events: List[OnboardingEvent]) -> List[Dict[str, Any]]:
    return [
        {
            "event": event.event,
            "timestamp": event.timestamp.isoformat(),
            "metadata": event.metadata,
        }
        for event in events
    ]


def _serialize_progress(service: OnboardingService, onboarding_id: str) -> Dict[str, Any]:
    return service.get_progress(onboarding_id)


def _handle_error(exc: OnboardingError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.message)


async def _resolve_payload(
    model_cls: Type[ModelT],
    request: Request,
    payload: ModelT | None,
) -> ModelT:
    if payload is not None:
        return payload

    form = await request.form()
    data: Dict[str, Any] = {}
    for key, value in form.multi_items():
        data[key] = value

    try:
        return model_cls(**data)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.errors(),
        ) from exc


@router.post("/register", response_model=RegistrationResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    request: Request,
    payload: RegistrationRequest | None = Body(None),
    service: OnboardingService = Depends(get_onboarding_service),
) -> RegistrationResponse:
    payload = await _resolve_payload(RegistrationRequest, request, payload)
    try:
        user = service.register_user(
            email=payload.email,
            full_name=payload.full_name,
            password=payload.password,
            marketing_opt_in=bool(payload.marketing_opt_in),
        )
    except OnboardingError as exc:
        _handle_error(exc)

    progress = _serialize_progress(service, user.id)
    return RegistrationResponse(
        onboarding_id=user.id,
        status=user.status,
        verification_expires_at=progress["verification"]["expires_at"],
        progress=progress,
        verification_token=user.verification_token,
    )


@router.post("/verify", response_model=VerificationResponse)
async def verify_email(
    request: Request,
    payload: VerificationRequest | None = Body(None),
    service: OnboardingService = Depends(get_onboarding_service),
) -> VerificationResponse:
    payload = await _resolve_payload(VerificationRequest, request, payload)
    try:
        user = service.verify_email(
            onboarding_id=payload.onboarding_id,
            token=payload.token,
        )
    except OnboardingError as exc:
        _handle_error(exc)

    progress = _serialize_progress(service, user.id)
    return VerificationResponse(onboarding_id=user.id, status=user.status, progress=progress)


@router.post("/profile", response_model=ProfileResponse)
async def complete_profile(
    request: Request,
    payload: ProfileRequest | None = Body(None),
    service: OnboardingService = Depends(get_onboarding_service),
) -> ProfileResponse:
    payload = await _resolve_payload(ProfileRequest, request, payload)
    try:
        user = service.complete_profile(
            onboarding_id=payload.onboarding_id,
            display_name=payload.display_name,
            business_goal=payload.business_goal,
            experience_level=payload.experience_level,
        )
    except OnboardingError as exc:
        _handle_error(exc)

    progress = _serialize_progress(service, user.id)
    profile = progress["profile"] or {}
    return ProfileResponse(
        onboarding_id=user.id,
        status=user.status,
        profile=profile,
        progress=progress,
    )


@router.post("/resend", response_model=RegistrationResponse)
async def resend_token(
    request: Request,
    payload: ResendRequest | None = Body(None),
    service: OnboardingService = Depends(get_onboarding_service),
) -> RegistrationResponse:
    payload = await _resolve_payload(ResendRequest, request, payload)
    try:
        token = service.resend_verification_token(onboarding_id=payload.onboarding_id)
        user = service.get_user(payload.onboarding_id)
    except OnboardingError as exc:
        _handle_error(exc)

    progress = _serialize_progress(service, user.id)
    return RegistrationResponse(
        onboarding_id=user.id,
        status=user.status,
        verification_expires_at=progress["verification"]["expires_at"],
        progress=progress,
        verification_token=token,
    )


@router.get("/progress/{onboarding_id}", response_model=VerificationResponse)
def get_progress(
    onboarding_id: str,
    service: OnboardingService = Depends(get_onboarding_service),
) -> VerificationResponse:
    try:
        user = service.get_user(onboarding_id)
    except OnboardingError as exc:
        _handle_error(exc)

    progress = _serialize_progress(service, user.id)
    return VerificationResponse(onboarding_id=user.id, status=user.status, progress=progress)


@router.get("/events/{onboarding_id}", response_model=EventLogResponse)
def get_event_log(
    onboarding_id: str,
    service: OnboardingService = Depends(get_onboarding_service),
) -> EventLogResponse:
    try:
        service.get_user(onboarding_id)
    except OnboardingError as exc:
        _handle_error(exc)

    events = _serialize_events(service.get_events(onboarding_id))
    return EventLogResponse(onboarding_id=onboarding_id, events=events)
