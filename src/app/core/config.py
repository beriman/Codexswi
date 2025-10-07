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

    # BRI BaaS API configuration
    bri_client_id: str | None = None
    bri_client_secret: str | None = None
    bri_api_key: str | None = None
    bri_merchant_account: str = "201101000546304"  # Sensasiwangi marketplace account
    bri_environment: str = "sandbox"  # or "production"

    # Session management
    session_secret: str = ""
    static_asset_version: str = "2024051901"

    @field_validator("session_secret")
    @classmethod
    def _validate_session_secret(cls, value: str) -> str:
        if not value:
            raise ValueError(
                "SESSION_SECRET environment variable is required for security. "
                "Please set it in your environment."
            )
        if len(value) < 32:
            raise ValueError(
                "SESSION_SECRET must be at least 32 characters for security."
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
    settings = Settings()
    logger.info("Settings loaded successfully")
    return settings
