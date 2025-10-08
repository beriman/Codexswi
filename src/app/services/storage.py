"""Utility helpers for persisting uploaded assets such as brand logos."""

from __future__ import annotations

import mimetypes
import secrets
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from app.core.config import get_settings

try:  # pragma: no cover - optional dependency for Supabase integration
    import httpx
except ImportError:  # pragma: no cover - handled by fallback storage
    httpx = None  # type: ignore[assignment]


class StorageError(Exception):
    """Base error for storage related failures."""


class StorageUnavailable(StorageError):
    """Raised when the primary storage backend cannot be used."""


class StorageUploadFailed(StorageError):
    """Raised when an upload cannot be completed in any backend."""


@dataclass
class LogoUpload:
    """Structure describing an uploaded logo file."""

    filename: str
    content_type: str
    data: bytes


class BrandLogoStorage:
    """Persist brand logos to Supabase Storage with a local fallback."""

    def __init__(self, *, bucket: str = "brand-assets") -> None:
        self._bucket = bucket
        self._settings = get_settings()

    def store_logo(self, *, slug: str, upload: LogoUpload) -> str:
        """Persist the provided logo and return a public URL."""

        object_name = self._build_object_name(slug, upload)
        return self._upload_to_supabase(object_name, upload)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _build_object_name(self, slug: str, upload: LogoUpload) -> str:
        safe_slug = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in slug) or "brand"
        extension = Path(upload.filename).suffix.lower()
        if not extension:
            guessed = mimetypes.guess_extension(upload.content_type)
            extension = guessed or ""
        if extension == ".jpe":  # normalise jpeg extension
            extension = ".jpg"
        if extension and not extension.startswith("."):
            extension = f".{extension}"
        if not extension:
            extension = ".bin"
        unique = secrets.token_hex(8)
        return f"brand-logos/{safe_slug}-{unique}{extension}"

    def _upload_to_supabase(self, object_name: str, upload: LogoUpload) -> str:
        settings = self._settings
        if not settings.supabase_url or not settings.supabase_service_role_key:
            raise StorageUnavailable("Supabase Storage belum dikonfigurasi.")
        if httpx is None:
            raise StorageUnavailable("Dependensi httpx belum tersedia untuk Supabase Storage.")

        url = f"{settings.supabase_url}/storage/v1/object/{self._bucket}/{object_name}"
        headers = {
            "Authorization": f"Bearer {settings.supabase_service_role_key}",
            "Content-Type": upload.content_type,
            "x-upsert": "true",
        }
        try:
            with httpx.Client(timeout=10.0) as client:  # type: ignore[attr-defined]
                response = client.post(url, content=upload.data, headers=headers)
        except httpx.HTTPError as exc:  # pragma: no cover - network failures are environment specific
            raise StorageUnavailable("Gagal terhubung ke Supabase Storage.") from exc

        if response.status_code >= 400:
            raise StorageUploadFailed("Supabase menolak unggahan logo brand.")

        return f"{settings.supabase_url}/storage/v1/object/public/{self._bucket}/{object_name}"
