"""In-memory session middleware without external dependencies."""

from __future__ import annotations

import secrets
from typing import Any, Dict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SessionData(dict):
    """Dictionary wrapper that tracks modification status."""

    def __init__(self, initial: Dict[str, Any] | None = None) -> None:
        super().__init__(initial or {})
        self.modified = False

    def _mark_modified(self) -> None:
        self.modified = True

    def __setitem__(self, key: str, value: Any) -> None:  # type: ignore[override]
        super().__setitem__(key, value)
        self._mark_modified()

    def __delitem__(self, key: str) -> None:  # type: ignore[override]
        super().__delitem__(key)
        self._mark_modified()

    def clear(self) -> None:  # type: ignore[override]
        super().clear()
        self._mark_modified()

    def pop(self, key: str, default: Any | None = None) -> Any:  # type: ignore[override]
        value = super().pop(key, default)
        self._mark_modified()
        return value

    def popitem(self) -> tuple[str, Any]:  # type: ignore[override]
        item = super().popitem()
        self._mark_modified()
        return item

    def setdefault(self, key: str, default: Any = None) -> Any:  # type: ignore[override]
        if key not in self:
            self._mark_modified()
        return super().setdefault(key, default)

    def update(self, *args: Any, **kwargs: Any) -> None:  # type: ignore[override]
        super().update(*args, **kwargs)
        if args or kwargs:
            self._mark_modified()


class InMemorySessionMiddleware(BaseHTTPMiddleware):
    """Provide `request.session` support using an in-memory store."""

    def __init__(
        self,
        app,
        *,
        cookie_name: str = "session",
        max_age: int = 60 * 60 * 24 * 30,
        same_site: str = "lax",
        https_only: bool = False,
    ) -> None:
        super().__init__(app)
        self.cookie_name = cookie_name
        self.max_age = max_age
        self.same_site = same_site
        self.https_only = https_only
        self._store: Dict[str, Dict[str, Any]] = {}

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        session_id = request.cookies.get(self.cookie_name)
        session_payload = self._store.get(session_id) if session_id else None
        new_session = False

        if session_payload is None:
            session_id = secrets.token_urlsafe(32)
            session_payload = {}
            new_session = True

        session = SessionData(session_payload)
        request.scope["session"] = session
        request.scope["session_id"] = session_id

        response = await call_next(request)

        if session.modified:
            if session:
                self._store[session_id] = dict(session)
                self._set_cookie(response, session_id)
            else:
                self._store.pop(session_id, None)
                self._delete_cookie(response)
        elif new_session:
            if session:
                self._store[session_id] = dict(session)
                self._set_cookie(response, session_id)
            else:
                self._store.pop(session_id, None)

        return response

    def _set_cookie(self, response: Response, session_id: str) -> None:
        response.set_cookie(
            self.cookie_name,
            session_id,
            max_age=self.max_age,
            httponly=True,
            secure=self.https_only,
            samesite=self.same_site,
            path="/",
        )

    def _delete_cookie(self, response: Response) -> None:
        response.delete_cookie(self.cookie_name, path="/")
