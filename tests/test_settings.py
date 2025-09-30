"""Tests for application settings helpers."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_session_secret_requires_minimum_length() -> None:
    with pytest.raises(ValidationError):
        Settings(session_secret="short-secret")


def test_default_session_secret_is_valid() -> None:
    settings = Settings()
    assert len(settings.session_secret) >= 32
