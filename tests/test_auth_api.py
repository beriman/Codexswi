import asyncio
import json
from http.cookies import SimpleCookie
from typing import Dict, Tuple

from app.api.routes.auth import get_auth_service
from app.main import app
from app.services.auth import AuthService


async def _send_request(
    method: str,
    path: str,
    *,
    json_body: Dict | None = None,
    cookies: Dict[str, str] | None = None,
) -> Tuple[int, Dict[str, str], bytes, Dict[str, str]]:
    body_bytes = b""
    headers = []

    if json_body is not None:
        body_bytes = json.dumps(json_body).encode("utf-8")
        headers.append((b"content-type", b"application/json"))

    if cookies:
        cookie_header = "; ".join(f"{key}={value}" for key, value in cookies.items())
        headers.append((b"cookie", cookie_header.encode("latin-1")))

    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode("ascii"),
        "query_string": b"",
        "headers": headers,
        "client": ("127.0.0.1", 0),
        "server": ("testserver", 80),
    }

    messages = []

    async def receive() -> dict:
        nonlocal body_bytes
        chunk = body_bytes
        body_bytes = b""
        return {"type": "http.request", "body": chunk, "more_body": False}

    async def send(message: dict) -> None:
        messages.append(message)

    await app(scope, receive, send)

    status = next(
        message["status"]
        for message in messages
        if message["type"] == "http.response.start"
    )
    raw_headers = next(
        message["headers"]
        for message in messages
        if message["type"] == "http.response.start"
    )
    body = b"".join(
        message["body"] for message in messages if message["type"] == "http.response.body"
    )

    response_headers = {key.decode().lower(): value.decode() for key, value in raw_headers}

    new_cookies: Dict[str, str] = {}
    for key, value in raw_headers:
        if key.decode().lower() == "set-cookie":
            parsed = SimpleCookie()
            parsed.load(value.decode())
            for cookie_key in parsed:
                new_cookies[cookie_key] = parsed[cookie_key].value

    return status, response_headers, body, new_cookies


def test_register_login_logout_flow():
    service = AuthService()
    app.dependency_overrides[get_auth_service] = lambda: service

    jar: Dict[str, str] = {}

    try:
        status, headers, body, new_cookies = asyncio.run(
            _send_request(
                "POST",
                "/api/auth/register",
                json_body={
                    "full_name": "Tester Sukses",
                    "email": "tester@example.com",
                    "password": "Password123",
                },
            )
        )
        assert status == 201
        payload = json.loads(body.decode())
        assert payload["email"] == "tester@example.com"
        jar.update(new_cookies)

        status, headers, body, new_cookies = asyncio.run(
            _send_request(
                "POST",
                "/api/auth/login",
                json_body={"email": "tester@example.com", "password": "Password123"},
                cookies=jar,
            )
        )
        assert status == 200
        payload = json.loads(body.decode())
        assert payload["message"] == "Login berhasil"
        jar.update(new_cookies)
        assert jar.get("session")

        status, headers, body, new_cookies = asyncio.run(
            _send_request("GET", "/api/auth/session", cookies=jar)
        )
        assert status == 200
        payload = json.loads(body.decode())
        assert payload["is_authenticated"] is True
        assert payload["user"]["email"] == "tester@example.com"

        status, headers, body, new_cookies = asyncio.run(
            _send_request("POST", "/api/auth/logout", cookies=jar)
        )
        assert status == 204
        jar.update(new_cookies)

        status, headers, body, _ = asyncio.run(
            _send_request("GET", "/api/auth/session", cookies=jar)
        )
        payload = json.loads(body.decode())
        assert payload["is_authenticated"] is False
    finally:
        app.dependency_overrides.pop(get_auth_service, None)
