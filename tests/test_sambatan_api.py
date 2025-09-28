import asyncio
import json
from datetime import UTC, datetime, timedelta

import pytest

from app.api.routes.sambatan import (
    get_lifecycle_service,
    get_product_service,
    get_sambatan_service,
)
from app.main import app
from app.services.products import ProductService
from app.services.sambatan import SambatanLifecycleService, SambatanService


async def _send_request(method: str, path: str, *, json_body: dict | None = None) -> tuple[int, dict, bytes]:
    body_bytes = b""
    headers = []
    if json_body is not None:
        body_bytes = json.dumps(json_body).encode("utf-8")
        headers.append((b"content-type", b"application/json"))

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

    start = next(m for m in messages if m["type"] == "http.response.start")
    body = b"".join(m["body"] for m in messages if m["type"] == "http.response.body")
    headers = {key.decode().lower(): value.decode() for key, value in start.get("headers", [])}
    return start["status"], headers, body


@pytest.fixture()
def sambatan_services() -> tuple[ProductService, SambatanService, SambatanLifecycleService]:
    product_service = ProductService()
    sambatan_service = SambatanService(product_service)
    lifecycle_service = SambatanLifecycleService(sambatan_service)

    app.dependency_overrides[get_product_service] = lambda: product_service
    app.dependency_overrides[get_sambatan_service] = lambda: sambatan_service
    app.dependency_overrides[get_lifecycle_service] = lambda: lifecycle_service

    try:
        yield product_service, sambatan_service, lifecycle_service
    finally:
        app.dependency_overrides.pop(get_product_service, None)
        app.dependency_overrides.pop(get_sambatan_service, None)
        app.dependency_overrides.pop(get_lifecycle_service, None)


def _prepare_product(product_service: ProductService) -> str:
    product = product_service.create_product(name="Kidung Laut", base_price=250_000)
    product_service.toggle_sambatan(
        product_id=product.id,
        enabled=True,
        total_slots=10,
        deadline=datetime.now(UTC) + timedelta(days=3),
    )
    return product.id


def test_sambatan_campaign_flow(sambatan_services) -> None:
    product_service, sambatan_service, lifecycle_service = sambatan_services

    product_id = _prepare_product(product_service)
    deadline = (datetime.now(UTC) + timedelta(hours=4)).isoformat()

    status, _, body = asyncio.run(
        _send_request(
            "POST",
            "/api/sambatan/campaigns",
            json_body={
                "product_id": product_id,
                "title": "Batch Komunitas",
                "total_slots": 10,
                "price_per_slot": 250000,
                "deadline": deadline,
            },
        )
    )
    assert status == 201
    campaign_data = json.loads(body.decode())
    campaign_id = campaign_data["id"]

    status, _, body = asyncio.run(
        _send_request(
            "POST",
            f"/api/sambatan/campaigns/{campaign_id}/join",
            json_body={
                "user_id": "user-1",
                "quantity": 10,
                "shipping_address": "Jl. Kenanga No. 3, Bandung",
            },
        )
    )
    assert status == 201
    join_data = json.loads(body.decode())
    assert join_data["status"] == "reserved"

    status, _, body = asyncio.run(_send_request("GET", f"/api/sambatan/campaigns/{campaign_id}"))
    assert status == 200
    detail_data = json.loads(body.decode())
    assert detail_data["status"] == "full"

    status, _, body = asyncio.run(_send_request("POST", "/api/sambatan/lifecycle/run"))
    assert status == 200
    lifecycle_payload = json.loads(body.decode())
    assert lifecycle_payload["transitions"]

    status, _, body = asyncio.run(_send_request("GET", f"/api/sambatan/campaigns/{campaign_id}"))
    assert json.loads(body.decode())["status"] == "completed"

    status, _, body = asyncio.run(_send_request("GET", "/api/sambatan/dashboard/summary"))
    assert status == 200
    summary_data = json.loads(body.decode())
    assert summary_data["completed_campaigns"] == 1

    status, _, body = asyncio.run(_send_request("GET", f"/api/sambatan/campaigns/{campaign_id}/logs"))
    assert status == 200
    events = [entry["event"] for entry in json.loads(body.decode())]
    assert "campaign_created" in events
    assert "campaign_completed" in events


def test_join_campaign_validations(sambatan_services) -> None:
    product_service, sambatan_service, lifecycle_service = sambatan_services
    product_id = _prepare_product(product_service)

    deadline = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
    status, _, body = asyncio.run(
        _send_request(
            "POST",
            "/api/sambatan/campaigns",
            json_body={
                "product_id": product_id,
                "title": "Batch Test",
                "total_slots": 2,
                "price_per_slot": 150000,
                "deadline": deadline,
            },
        )
    )
    campaign_id = json.loads(body.decode())["id"]

    status, _, _ = asyncio.run(
        _send_request(
            "POST",
            f"/api/sambatan/campaigns/{campaign_id}/join",
            json_body={
                "user_id": "alpha",
                "quantity": 2,
                "shipping_address": "Jl. Melati No. 5",
            },
        )
    )
    assert status == 201

    status, _, body = asyncio.run(
        _send_request(
            "POST",
            f"/api/sambatan/campaigns/{campaign_id}/join",
            json_body={
                "user_id": "beta",
                "quantity": 1,
                "shipping_address": "Jl. Anggrek No. 2",
            },
        )
    )
    assert status == 409
    assert "tidak menerima" in json.loads(body.decode())["detail"]
