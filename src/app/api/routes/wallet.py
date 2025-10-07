"""Wallet API endpoints and web pages."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from supabase import Client
else:
    try:
        from supabase import Client
    except ImportError:
        Client = Any  # type: ignore

from app.core.dependencies import get_db
from app.core.config import get_settings
from app.services.wallet import (
    WalletService,
    WalletError,
    WalletNotFound,
    InsufficientBalance,
    TopUpError,
    get_wallet_service
)
from app.services.bri_api import create_bri_client

router = APIRouter(tags=["wallet"])


# ============================================================================
# Request/Response Models
# ============================================================================

class WalletBalanceResponse(BaseModel):
    balance: float
    currency: str = "IDR"
    wallet_id: str


class TopUpCreateRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Top-up amount in IDR")


class TopUpResponse(BaseModel):
    id: str
    amount: float
    virtual_account: str
    expires_at: datetime
    status: str


class TransactionResponse(BaseModel):
    id: str
    transaction_type: str
    amount: float
    balance_before: float
    balance_after: float
    status: str
    description: Optional[str]
    created_at: datetime


class BRIVAWebhookRequest(BaseModel):
    """BRIVA payment webhook payload."""
    virtual_account: str
    payment_amount: str
    transaction_date: str
    customer_code: str


# ============================================================================
# Dependencies
# ============================================================================

def get_wallet_service_dep(db: Client | None = Depends(get_db)) -> WalletService:
    """Get wallet service with dependencies."""
    if not db:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available"
        )
    
    settings = get_settings()
    
    # Create BRI client if credentials available
    bri_client = None
    if settings.bri_client_id and settings.bri_client_secret and settings.bri_api_key:
        bri_client = create_bri_client(
            client_id=settings.bri_client_id,
            client_secret=settings.bri_client_secret,
            api_key=settings.bri_api_key,
            is_production=settings.bri_environment == "production"
        )
    
    return WalletService(db=db, bri_client=bri_client)


def require_authenticated_user(request: Request) -> dict:
    """Require authenticated user session."""
    user = request.session.get("user")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return user


# ============================================================================
# Web Pages
# ============================================================================

@router.get("/wallet", response_class=HTMLResponse, name="wallet_dashboard")
async def wallet_dashboard(
    request: Request,
    user: dict = Depends(require_authenticated_user),
    wallet_service: WalletService = Depends(get_wallet_service_dep)
):
    """Wallet dashboard page."""
    templates = request.app.state.templates
    user_id = user["user_id"]
    
    try:
        # Get or create wallet
        try:
            wallet = await wallet_service.get_wallet(user_id)
        except WalletNotFound:
            wallet = await wallet_service.create_wallet(user_id)
        
        # Get recent transactions
        transactions = await wallet_service.get_transactions(user_id, limit=20)
        
        # Check for pending top-ups
        if wallet_service.db:
            pending_topups = wallet_service.db.table('wallet_topup_requests').select('*').eq(
                'wallet_id', wallet.id
            ).eq('status', 'pending').order('created_at', desc=True).limit(5).execute()
            
            topups = []
            if pending_topups.data:
                for topup_data in pending_topups.data:
                    topups.append({
                        'id': topup_data['id'],
                        'amount': float(topup_data['amount']),
                        'virtual_account': topup_data['virtual_account'],
                        'expires_at': topup_data['expires_at'],
                        'status': topup_data['status']
                    })
        else:
            topups = []
        
        context = {
            "wallet": {
                "id": wallet.id,
                "balance": float(wallet.balance),
                "status": wallet.status,
                "kyc_status": wallet.kyc_status
            },
            "transactions": [
                {
                    "id": tx.id,
                    "type": tx.transaction_type,
                    "amount": float(tx.amount),
                    "balance_after": float(tx.balance_after),
                    "description": tx.description,
                    "created_at": tx.created_at
                }
                for tx in transactions
            ],
            "pending_topups": topups,
            "user": user
        }
        
        return templates.TemplateResponse(
            request,
            "wallet/dashboard.html",
            context
        )
    
    except WalletError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/api/wallet/balance", response_model=WalletBalanceResponse)
async def get_wallet_balance(
    user: dict = Depends(require_authenticated_user),
    wallet_service: WalletService = Depends(get_wallet_service_dep)
):
    """Get current wallet balance."""
    user_id = user["user_id"]
    
    try:
        # Get or create wallet
        try:
            wallet = await wallet_service.get_wallet(user_id)
        except WalletNotFound:
            wallet = await wallet_service.create_wallet(user_id)
        
        return WalletBalanceResponse(
            balance=float(wallet.balance),
            currency="IDR",
            wallet_id=wallet.id
        )
    
    except WalletError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/api/wallet/topup", response_model=TopUpResponse, status_code=status.HTTP_201_CREATED)
async def create_topup_request(
    payload: TopUpCreateRequest,
    user: dict = Depends(require_authenticated_user),
    wallet_service: WalletService = Depends(get_wallet_service_dep)
):
    """Create top-up request with BRIVA virtual account."""
    user_id = user["user_id"]
    user_name = user.get("full_name", "User")
    
    try:
        amount = Decimal(str(payload.amount))
        
        topup = await wallet_service.create_topup_request(
            user_id=user_id,
            amount=amount,
            customer_name=user_name
        )
        
        return TopUpResponse(
            id=topup.id,
            amount=float(topup.amount),
            virtual_account=topup.virtual_account,
            expires_at=topup.expires_at,
            status=topup.status
        )
    
    except TopUpError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create top-up request: {str(e)}"
        )


@router.get("/api/wallet/transactions", response_model=List[TransactionResponse])
async def get_wallet_transactions(
    limit: int = 50,
    offset: int = 0,
    user: dict = Depends(require_authenticated_user),
    wallet_service: WalletService = Depends(get_wallet_service_dep)
):
    """Get wallet transaction history."""
    user_id = user["user_id"]
    
    try:
        transactions = await wallet_service.get_transactions(
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        
        return [
            TransactionResponse(
                id=tx.id,
                transaction_type=tx.transaction_type,
                amount=float(tx.amount),
                balance_before=float(tx.balance_before),
                balance_after=float(tx.balance_after),
                status=tx.status,
                description=tx.description,
                created_at=tx.created_at
            )
            for tx in transactions
        ]
    
    except WalletError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============================================================================
# Webhook
# ============================================================================

@router.post("/webhook/briva/payment", status_code=status.HTTP_200_OK)
async def briva_payment_webhook(
    payload: BRIVAWebhookRequest,
    wallet_service: WalletService = Depends(get_wallet_service_dep)
):
    """Handle BRIVA payment confirmation webhook from BRI.
    
    This endpoint receives payment notifications from BRI when a BRIVA payment
    is completed. It updates the wallet balance and marks the top-up as paid.
    """
    try:
        amount = Decimal(payload.payment_amount)
        
        topup = await wallet_service.process_topup_payment(
            virtual_account=payload.virtual_account,
            paid_amount=amount
        )
        
        return {
            "status": "success",
            "message": "Payment processed successfully",
            "topup_id": topup.id,
            "amount": float(amount)
        }
    
    except TopUpError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process payment: {str(e)}"
        )
