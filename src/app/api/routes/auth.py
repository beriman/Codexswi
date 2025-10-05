"""Authentication API endpoints.

Updated to use Supabase-backed authentication service for persistent storage.
"""

from __future__ import annotations

from datetime import datetime
import logging

from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from supabase import Client

from app.core.dependencies import get_db
from app.services.auth_supabase import (
    AccountStatus,
    AuthService,
    AuthUser,
    AuthError,
    RegistrationResult,
    get_auth_service as get_auth_service_instance,
    UserAlreadyExists,
    InvalidCredentials,
    PasswordPolicyError,
    VerificationError,
)

logger = logging.getLogger(__name__)

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


def get_auth_service(db: Client = Depends(get_db)) -> AuthService:
    """Get auth service instance with Supabase client."""
    return AuthService(db)


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
def register_user(
    payload: RegisterRequest, 
    service: AuthService = Depends(get_auth_service)
) -> RegisterResponse:
    """Register a new user with email verification.
    
    This creates an account in auth_accounts table and sends verification email.
    """
    try:
        result = service.register(
            email=payload.email,
            full_name=payload.full_name,
            password=payload.password,
        )
        logger.info(f"User registered successfully: {result.email}")
    except UserAlreadyExists as exc:
        logger.warning(f"Registration failed - duplicate email: {payload.email}")
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except PasswordPolicyError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except AuthError as exc:
        logger.error(f"Registration failed: {exc.message}")
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    return _handle_registration_result(result)


@router.post("/verify", response_model=VerificationResponse)
def verify_user(
    payload: VerificationRequest, 
    service: AuthService = Depends(get_auth_service)
) -> VerificationResponse:
    """Verify user email using token from registration email.
    
    This updates account status to 'active' in the database.
    """
    try:
        user = service.verify_email(token=payload.token)
        logger.info(f"Email verified successfully: {user.email}")
    except VerificationError as exc:
        logger.warning(f"Verification failed: {exc.message}")
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except AuthError as exc:
        logger.error(f"Verification error: {exc.message}")
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    return VerificationResponse(
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        status=user.status,
        message="Verifikasi berhasil. Silakan login.",
    )


@router.post("/login", response_model=AuthPayload)
async def login_user(
    request: Request,
    payload: LoginRequest | None = Body(None),
    service: AuthService = Depends(get_auth_service),
) -> AuthPayload:
    """Authenticate user and create session.
    
    This validates credentials against auth_accounts table and creates
    a persistent session in auth_sessions table.
    """
    if payload is None:
        form = await request.form()
        payload = LoginRequest(**dict(form))

    try:
        # Authenticate user
        user = service.login(email=payload.email, password=payload.password)
        logger.info(f"User logged in: {user.email}")
        
        # Create persistent session in database
        session_token = service.create_session(
            account_id=user.id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        # Store in session cookie
        request.session["token"] = session_token
        request.session["user"] = _serialize_user(user)
        
    except InvalidCredentials as exc:
        logger.warning(f"Login failed for {payload.email}: invalid credentials")
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except AuthError as exc:
        logger.error(f"Login error for {payload.email}: {exc.message}")
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    return AuthPayload(
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        status=user.status,
        message="Login berhasil",
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout_user(
    request: Request,
    service: AuthService = Depends(get_auth_service)
) -> Response:
    """Logout user and destroy session.
    
    This removes the session from auth_sessions table and clears the cookie.
    """
    session_token = request.session.get("token")
    
    if session_token:
        try:
            # Delete session from database
            service.logout(session_token)
            logger.info("User logged out, session destroyed")
        except Exception as exc:
            logger.warning(f"Error destroying session: {exc}")
            # Continue anyway to clear local session
    
    # Clear session cookie
    request.session.pop("user", None)
    request.session.pop("token", None)
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/session", response_model=SessionResponse)
def read_session(
    request: Request,
    service: AuthService = Depends(get_auth_service)
) -> SessionResponse:
    """Get current session status.
    
    This verifies the session token against auth_sessions table to ensure
    it hasn't expired or been invalidated.
    """
    session_token = request.session.get("token")
    user_data = request.session.get("user")
    
    # If no token in session, not authenticated
    if not session_token:
        return SessionResponse(is_authenticated=False, user=None)
    
    try:
        # Verify session is still valid in database
        user = service.verify_session(session_token)
        
        if user:
            # Session valid - return user data
            return SessionResponse(
                is_authenticated=True,
                user=_serialize_user(user)
            )
        else:
            # Session expired or invalid - clear cookie
            request.session.pop("user", None)
            request.session.pop("token", None)
            return SessionResponse(is_authenticated=False, user=None)
            
    except Exception as exc:
        logger.warning(f"Session verification error: {exc}")
        # Clear invalid session
        request.session.pop("user", None)
        request.session.pop("token", None)
        return SessionResponse(is_authenticated=False, user=None)
