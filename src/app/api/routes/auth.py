"""Authentication API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field

from app.services.auth import AuthService, AuthError, auth_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=3, max_length=120)
    email: str = Field(..., pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(..., min_length=8, max_length=128)


class AuthPayload(BaseModel):
    user_id: str
    email: str
    full_name: str
    message: str


class LoginRequest(BaseModel):
    email: str = Field(..., pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(..., min_length=8, max_length=128)


class SessionResponse(BaseModel):
    is_authenticated: bool
    user: dict | None = None


def get_auth_service() -> AuthService:
    return auth_service


def _serialize_user(user) -> dict:
    return {"user_id": user.id, "email": user.email, "full_name": user.full_name}


@router.post("/register", response_model=AuthPayload, status_code=status.HTTP_201_CREATED)
def register_user(payload: RegisterRequest, service: AuthService = Depends(get_auth_service)) -> AuthPayload:
    try:
        user = service.register_user(
            email=payload.email,
            full_name=payload.full_name,
            password=payload.password,
        )
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    return AuthPayload(
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        message="Registrasi berhasil",
    )


@router.post("/login", response_model=AuthPayload)
def login_user(
    payload: LoginRequest,
    request: Request,
    service: AuthService = Depends(get_auth_service),
) -> AuthPayload:
    try:
        user = service.authenticate(email=payload.email, password=payload.password)
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    request.session["user"] = _serialize_user(user)

    return AuthPayload(
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
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
