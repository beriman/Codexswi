import pytest

from app.services.auth import (
    AuthService,
    InvalidCredentials,
    PasswordPolicyError,
    SupabaseAuthRepository,
    UserAlreadyExists,
)


def test_register_and_authenticate_user():
    # Use in-memory repository for testing
    service = AuthService(repository=SupabaseAuthRepository())

    user = service.register_user(
        email="tester@example.com",
        full_name="Tester Sukses",
        password="Password123",
    )

    assert user.email == "tester@example.com"
    assert user.password_hash != "Password123"

    authenticated = service.authenticate(email="tester@example.com", password="Password123")
    assert authenticated.last_login_at is not None


def test_register_duplicate_email():
    # Use in-memory repository for testing
    service = AuthService(repository=SupabaseAuthRepository())
    service.register_user(email="tester@example.com", full_name="Tester", password="Password123")

    with pytest.raises(UserAlreadyExists):
        service.register_user(email="tester@example.com", full_name="Tester Dua", password="Password456")


def test_password_policy_enforced():
    # Use in-memory repository for testing
    service = AuthService(repository=SupabaseAuthRepository())

    with pytest.raises(PasswordPolicyError):
        service.register_user(email="tester@example.com", full_name="Tester", password="short")

    with pytest.raises(PasswordPolicyError):
        service.register_user(email="tester2@example.com", full_name="Tester", password="passwordonly")


def test_invalid_credentials_raise_error():
    # Use in-memory repository for testing
    service = AuthService(repository=SupabaseAuthRepository())
    service.register_user(email="tester@example.com", full_name="Tester", password="Password123")

    with pytest.raises(InvalidCredentials):
        service.authenticate(email="tester@example.com", password="Password456")

    with pytest.raises(InvalidCredentials):
        service.authenticate(email="unknown@example.com", password="Password123")
