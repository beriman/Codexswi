"""Authentication API endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field

try:
    from supabase import Client
except ImportError:
    Client = None  # type: ignore

from app.core.dependencies import get_db
from app.core.rate_limit import limiter, RATE_LIMITS
from app.services.auth import (
    AccountStatus,
    AuthService,
    AuthUser,
    AuthError,
    RegistrationResult,
    auth_service,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=3, max_length=120)
    email: str = Field(..., pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(..., min_length=8, max_length=128)


class AuthPayload(BaseModel):
    user_id: str
    email: str
    full_name: str
    status: AccountStatus
    message: str


class RegisterResponse(BaseModel):
    registration_id: str
    account_id: str
    email: str
    full_name: str
    status: AccountStatus
    verification_expires_at: datetime
    message: str


class LoginRequest(BaseModel):
    email: str = Field(..., pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(..., min_length=8, max_length=128)


class VerificationRequest(BaseModel):
    token: str = Field(..., min_length=8)


class VerificationResponse(BaseModel):
    user_id: str
    email: str
    full_name: str
    status: AccountStatus
    message: str


class SessionResponse(BaseModel):
    is_authenticated: bool
    user: dict | None = None


def get_auth_service(db: Optional[Client] = Depends(get_db)) -> AuthService:
    if db:
        return AuthService(db=db)
    return auth_service


def _serialize_user(user: AuthUser) -> dict:
    return {
        "user_id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "status": user.status.value,
    }


def _handle_registration_result(result: RegistrationResult) -> RegisterResponse:
    registration = result.registration
    account = result.account
    expires_at = registration.verification_expires_at or account.updated_at
    return RegisterResponse(
        registration_id=registration.id,
        account_id=account.id,
        email=account.email,
        full_name=account.full_name,
        status=account.status,
        verification_expires_at=expires_at,
        message="Registrasi berhasil. Cek email Anda untuk tautan verifikasi.",
    )


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(RATE_LIMITS["auth_register"])
def register_user(request: Request, payload: RegisterRequest, service: AuthService = Depends(get_auth_service)) -> RegisterResponse:
    try:
        result = service.register_user(
            email=payload.email,
            full_name=payload.full_name,
            password=payload.password,
        )
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    return _handle_registration_result(result)


@router.post("/verify", response_model=VerificationResponse)
@limiter.limit(RATE_LIMITS["auth_verify"])
def verify_user(
    request: Request, payload: VerificationRequest, service: AuthService = Depends(get_auth_service)
) -> VerificationResponse:
    try:
        user = service.verify_email(token=payload.token)
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    return VerificationResponse(
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        status=user.status,
        message="Verifikasi berhasil",
    )


@router.post("/login", response_model=AuthPayload)
@limiter.limit(RATE_LIMITS["auth_login"])
async def login_user(
    request: Request,
    payload: LoginRequest | None = Body(None),
    service: AuthService = Depends(get_auth_service),
) -> AuthPayload:
    if payload is None:
        form = await request.form()
        payload = LoginRequest(**dict(form))

    try:
        user = service.authenticate(email=payload.email, password=payload.password)
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    request.session["user"] = _serialize_user(user)

    return AuthPayload(
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        status=user.status,
        message="Login berhasil",
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout_user(request: Request) -> Response:
    request.session.pop("user", None)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/session", response_model=SessionResponse)
def read_session(request: Request) -> SessionResponse:
    user = request.session.get("user")
    return SessionResponse(is_authenticated=bool(user), user=user)
