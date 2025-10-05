"""Application configuration module."""

import logging
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Centralized application settings loaded from environment variables.

    The fields reflect integrations highlighted in the PRD such as Supabase and
    RajaOngkir. Additional configuration values can be appended as features are
    implemented.
    """

    app_name: str = "Sensasiwangi.id"
    environment: str = "development"

    # Supabase configuration
    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    supabase_service_role_key: str | None = None

    # RajaOngkir integration
    rajaongkir_api_key: str | None = None

    # Session management
    session_secret: str = "development-session-secret-placeholder"
    static_asset_version: str = "2024051901"

    @field_validator("session_secret")
    @classmethod
    def _validate_session_secret(cls, value: str) -> str:
        # Only validate in production environments
        # In development, allow shorter secrets for convenience
        import os
        env = os.getenv("ENVIRONMENT", "development")
        if env == "production" and len(value) < 32:
            raise ValueError(
                "SESSION_SECRET harus terdiri dari minimal 32 karakter untuk keamanan."
            )
        return value

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"  # Ignore extra environment variables
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    try:
        settings = Settings()
        logger.info("Settings loaded successfully")
        return settings
    except Exception as e:
        logger.error(f"Failed to load settings: {e}", exc_info=True)
        # Return settings with defaults only
        logger.warning("Using default settings without environment variables")
        return Settings(_env_file=None)
