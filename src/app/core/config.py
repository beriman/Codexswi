"""Application configuration module."""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    
    # Performance optimizations
    use_minified_assets: bool = False
    enable_compression: bool = True

    @field_validator("session_secret")
    @classmethod
    def _validate_session_secret(cls, value: str) -> str:
        if len(value) < 32:
            raise ValueError(
                "SESSION_SECRET harus terdiri dari minimal 32 karakter untuk keamanan."
            )
        return value

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()
