"""FastAPI endpoints exposing Sambatan campaigns and lifecycle."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.services.products import ProductError, ProductService, product_service
from app.services.sambatan import (
    CampaignNotFound,
    ParticipationNotFound,
    ParticipationStateInvalid,
    SambatanAuditLog,
    SambatanCampaign,
    SambatanError,
    SambatanLifecycleService,
    SambatanParticipant,
    SambatanService,
    SambatanStatus,
    ParticipationStatus,
    sambatan_lifecycle_service,
    sambatan_service,
)


router = APIRouter(prefix="/api/sambatan", tags=["sambatan"])


class CampaignCreateRequest(BaseModel):
    product_id: str
    title: str = Field(..., min_length=3, max_length=120)
    total_slots: int = Field(..., ge=1)
    price_per_slot: int = Field(..., ge=1)
    deadline: datetime


class CampaignResponse(BaseModel):
    id: str
    product_id: str
    title: str
    total_slots: int
    price_per_slot: int
    deadline: datetime
    status: SambatanStatus
    slots_taken: int
    progress_percent: int
    slots_remaining: int


class ParticipationRequest(BaseModel):
    user_id: str
    quantity: int = Field(..., ge=1)
    shipping_address: str = Field(..., min_length=10, max_length=240)
    note: Optional[str] = Field(None, max_length=160)


class ParticipationResponse(BaseModel):
    id: str
    campaign_id: str
    user_id: str
    quantity: int
    status: ParticipationStatus
    shipping_address: str
    note: Optional[str]
    joined_at: datetime
    updated_at: datetime


class DashboardSummaryResponse(BaseModel):
    total_campaigns: int
    active_campaigns: int
    full_campaigns: int
    completed_campaigns: int
    failed_campaigns: int
    total_slots_taken: int


class LifecycleRunResponse(BaseModel):
    executed_at: datetime
    transitions: List[Dict[str, Any]]


def get_sambatan_service() -> SambatanService:
    return sambatan_service


def get_lifecycle_service() -> SambatanLifecycleService:
    return sambatan_lifecycle_service


def get_product_service() -> ProductService:
    return product_service


def _serialize_campaign(campaign: SambatanCampaign) -> Dict[str, Any]:
    return {
        "id": campaign.id,
        "product_id": campaign.product_id,
        "title": campaign.title,
        "total_slots": campaign.total_slots,
        "price_per_slot": campaign.price_per_slot,
        "deadline": campaign.deadline,
        "status": campaign.status,
        "slots_taken": campaign.slots_taken,
        "progress_percent": campaign.progress_percent(),
        "slots_remaining": campaign.slots_remaining(),
    }


def _serialize_participant(participant: SambatanParticipant) -> Dict[str, Any]:
    return {
        "id": participant.id,
        "campaign_id": participant.campaign_id,
        "user_id": participant.user_id,
        "quantity": participant.quantity,
        "status": participant.status,
        "shipping_address": participant.shipping_address,
        "note": participant.note,
        "joined_at": participant.joined_at,
        "updated_at": participant.updated_at,
    }


def _serialize_audit(log: SambatanAuditLog) -> Dict[str, Any]:
    return {
        "campaign_id": log.campaign_id,
        "event": log.event,
        "timestamp": log.timestamp,
        "metadata": log.metadata,
    }


def _handle_error(exc: SambatanError | ProductError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.post("/campaigns", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
def create_campaign(
    payload: CampaignCreateRequest,
    service: SambatanService = Depends(get_sambatan_service),
    product_service: ProductService = Depends(get_product_service),
) -> CampaignResponse:
    try:
        product_service.get_product(payload.product_id)
    except ProductError as exc:
        _handle_error(exc)

    try:
        campaign = service.create_campaign(
            product_id=payload.product_id,
            title=payload.title,
            total_slots=payload.total_slots,
            price_per_slot=payload.price_per_slot,
            deadline=payload.deadline,
        )
    except SambatanError as exc:
        _handle_error(exc)

    return CampaignResponse(**_serialize_campaign(campaign))


@router.get("/campaigns", response_model=List[CampaignResponse])
def list_campaigns(service: SambatanService = Depends(get_sambatan_service)) -> List[CampaignResponse]:
    return [CampaignResponse(**_serialize_campaign(campaign)) for campaign in service.list_campaigns()]


@router.get("/campaigns/{campaign_id}", response_model=CampaignResponse)
def get_campaign(campaign_id: str, service: SambatanService = Depends(get_sambatan_service)) -> CampaignResponse:
    try:
        campaign = service.get_campaign(campaign_id)
    except SambatanError as exc:
        _handle_error(exc)

    return CampaignResponse(**_serialize_campaign(campaign))


@router.post("/campaigns/{campaign_id}/join", response_model=ParticipationResponse, status_code=status.HTTP_201_CREATED)
def join_campaign(
    campaign_id: str,
    payload: ParticipationRequest,
    service: SambatanService = Depends(get_sambatan_service),
) -> ParticipationResponse:
    try:
        participant = service.join_campaign(
            campaign_id=campaign_id,
            user_id=payload.user_id,
            quantity=payload.quantity,
            shipping_address=payload.shipping_address,
            note=payload.note,
        )
    except SambatanError as exc:
        _handle_error(exc)

    return ParticipationResponse(**_serialize_participant(participant))


@router.post("/participations/{participation_id}/cancel", response_model=ParticipationResponse)
def cancel_participation(
    participation_id: str,
    reason: Optional[str] = None,
    service: SambatanService = Depends(get_sambatan_service),
) -> ParticipationResponse:
    try:
        participant = service.cancel_participation(participation_id=participation_id, reason=reason)
    except SambatanError as exc:
        _handle_error(exc)

    return ParticipationResponse(**_serialize_participant(participant))


@router.post("/participations/{participation_id}/confirm", response_model=ParticipationResponse)
def confirm_participation(
    participation_id: str,
    service: SambatanService = Depends(get_sambatan_service),
) -> ParticipationResponse:
    try:
        participant = service.confirm_participation(participation_id=participation_id)
    except SambatanError as exc:
        _handle_error(exc)

    return ParticipationResponse(**_serialize_participant(participant))


@router.get("/campaigns/{campaign_id}/participants", response_model=List[ParticipationResponse])
def list_participants(campaign_id: str, service: SambatanService = Depends(get_sambatan_service)) -> List[ParticipationResponse]:
    try:
        participants = service.list_participants(campaign_id)
    except SambatanError as exc:
        _handle_error(exc)

    return [ParticipationResponse(**_serialize_participant(participant)) for participant in participants]


@router.get("/dashboard/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(service: SambatanService = Depends(get_sambatan_service)) -> DashboardSummaryResponse:
    return DashboardSummaryResponse(**service.get_dashboard_summary())


@router.post("/lifecycle/run", response_model=LifecycleRunResponse)
def run_lifecycle(service: SambatanLifecycleService = Depends(get_lifecycle_service)) -> LifecycleRunResponse:
    transitions = service.run()
    executed_at = service.last_run or datetime.now(UTC)
    return LifecycleRunResponse(
        executed_at=executed_at,
        transitions=[_serialize_audit(log) for log in transitions],
    )


@router.get("/campaigns/{campaign_id}/logs", response_model=List[Dict[str, Any]])
def get_audit_logs(campaign_id: str, service: SambatanService = Depends(get_sambatan_service)) -> List[Dict[str, Any]]:
    try:
        service.get_campaign(campaign_id)
    except SambatanError as exc:
        _handle_error(exc)

    return [_serialize_audit(log) for log in service.get_audit_logs(campaign_id)]

