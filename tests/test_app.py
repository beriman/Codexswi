import asyncio

from app.main import app


def test_homepage_returns_success():
    async def _run() -> None:
        scope = {
            "type": "http",
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/",
            "raw_path": b"/",
            "query_string": b"",
            "headers": [],
            "client": ("127.0.0.1", 0),
            "server": ("testserver", 80),
        }
        messages = []

        async def receive() -> dict:
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(message: dict) -> None:
            messages.append(message)

        await app(scope, receive, send)

        status = next(
            (
                message["status"]
                for message in messages
                if message["type"] == "http.response.start"
            ),
            None,
        )
        body = b"".join(
            message["body"] for message in messages if message["type"] == "http.response.body"
        )

        assert status == 200
        assert b"Sensasiwangi" in body

    asyncio.run(_run())


def test_purchase_workflow_page_renders():
    async def _run() -> None:
        scope = {
            "type": "http",
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/ui-ux/foundation/purchase",
            "raw_path": b"/ui-ux/foundation/purchase",
            "query_string": b"",
            "headers": [],
            "client": ("127.0.0.1", 0),
            "server": ("testserver", 80),
        }
        messages: list[dict] = []

        async def receive() -> dict:
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(message: dict) -> None:
            messages.append(message)

        await app(scope, receive, send)

        status = next(
            (
                message["status"]
                for message in messages
                if message["type"] == "http.response.start"
            ),
            None,
        )
        body = b"".join(
            message["body"] for message in messages if message["type"] == "http.response.body"
        )

        assert status == 200
        assert b"Blueprint workflow pembelian produk" in body

    asyncio.run(_run())
