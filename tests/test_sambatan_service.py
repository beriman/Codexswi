from datetime import datetime, timedelta

import pytest

from app.services.products import ProductService
from app.services.sambatan import (
    CampaignClosed,
    InsufficientSlots,
    SambatanService,
    SambatanStatus,
    SambatanError,
    ParticipationStatus,
)


def create_services() -> tuple[ProductService, SambatanService]:
    product_service = ProductService()
    sambatan_service = SambatanService(product_service)
    return product_service, sambatan_service


def enable_product(product_service: ProductService) -> str:
    product = product_service.create_product(name="Kidung Laut", base_price=250_000)
    product_service.toggle_sambatan(
        product_id=product.id,
        enabled=True,
        total_slots=20,
        deadline=datetime.utcnow() + timedelta(days=5),
    )
    return product.id


def test_create_campaign_requires_enabled_product() -> None:
    product_service, sambatan_service = create_services()
    product = product_service.create_product(name="Regular", base_price=100_000)

    with pytest.raises(SambatanError):
        sambatan_service.create_campaign(
            product_id=product.id,
            title="Batch Tanpa Toggle",
            total_slots=10,
            price_per_slot=150_000,
            deadline=datetime.utcnow() + timedelta(days=2),
        )


def test_join_campaign_updates_progress_and_status() -> None:
    product_service, sambatan_service = create_services()
    product_id = enable_product(product_service)
    campaign = sambatan_service.create_campaign(
        product_id=product_id,
        title="Batch Perdana",
        total_slots=10,
        price_per_slot=200_000,
        deadline=datetime.utcnow() + timedelta(days=2),
    )

    participant = sambatan_service.join_campaign(
        campaign_id=campaign.id,
        user_id="user-1",
        quantity=4,
        shipping_address="Jl. Kenanga No. 8, Jakarta",
    )

    assert participant.status is ParticipationStatus.RESERVED
    assert sambatan_service.get_campaign(campaign.id).slots_taken == 4

    second = sambatan_service.join_campaign(
        campaign_id=campaign.id,
        user_id="user-2",
        quantity=6,
        shipping_address="Komplek Harmoni Blok C2",
    )

    assert second.status is ParticipationStatus.RESERVED
    campaign_state = sambatan_service.get_campaign(campaign.id)
    assert campaign_state.status is SambatanStatus.FULL
    assert campaign_state.slots_remaining() == 0

    with pytest.raises(CampaignClosed):
        sambatan_service.join_campaign(
            campaign_id=campaign.id,
            user_id="user-3",
            quantity=1,
            shipping_address="Jl. Teratai No. 1",
        )


def test_lifecycle_completes_and_fails_based_on_deadline() -> None:
    product_service, sambatan_service = create_services()
    product_id = enable_product(product_service)

    complete_campaign = sambatan_service.create_campaign(
        product_id=product_id,
        title="Batch Lengkap",
        total_slots=5,
        price_per_slot=210_000,
        deadline=datetime.utcnow() + timedelta(hours=2),
    )
    sambatan_service.join_campaign(
        campaign_id=complete_campaign.id,
        user_id="user-a",
        quantity=5,
        shipping_address="Jl. Dahlia No. 9",
    )

    failing_campaign = sambatan_service.create_campaign(
        product_id=product_id,
        title="Batch Pending",
        total_slots=4,
        price_per_slot=195_000,
        deadline=datetime.utcnow() + timedelta(hours=1),
    )
    sambatan_service.join_campaign(
        campaign_id=failing_campaign.id,
        user_id="user-b",
        quantity=1,
        shipping_address="Jl. Cendana No. 3",
    )

    future = datetime.utcnow() + timedelta(hours=3)
    logs = sambatan_service.run_lifecycle(now=future)

    assert any(log.event == "campaign_completed" for log in logs)
    assert any(log.event == "campaign_failed" for log in logs)

    completed = sambatan_service.get_campaign(complete_campaign.id)
    assert completed.status is SambatanStatus.COMPLETED
    assert all(p.status is ParticipationStatus.CONFIRMED for p in sambatan_service.list_participants(completed.id))

    failed = sambatan_service.get_campaign(failing_campaign.id)
    assert failed.status is SambatanStatus.FAILED
    assert all(p.status is ParticipationStatus.REFUNDED for p in sambatan_service.list_participants(failed.id))
