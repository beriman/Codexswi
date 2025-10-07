"""Settlement Service - Handle order and sambatan payout with platform fee."""

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Dict, Any
from enum import Enum

from supabase import Client

from app.services.wallet import WalletService, WalletError, InsufficientBalance
from app.services.bri_api import BRIAPIClient, BRITransferError
from app.services.settings import SettingsService

logger = logging.getLogger(__name__)


class SettlementType(str, Enum):
    """Settlement type enum."""
    ORDER = "order"
    SAMBATAN = "sambatan"
    REFUND = "refund"


class SettlementStatus(str, Enum):
    """Settlement status enum."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class SettlementError(Exception):
    """Settlement error."""
    pass


class SettlementService:
    """Service for handling settlements with platform fee deduction."""
    
    def __init__(
        self,
        db: Client,
        wallet_service: Optional[WalletService] = None,
        bri_client: Optional[BRIAPIClient] = None
    ):
        """Initialize settlement service.
        
        Args:
            db: Supabase client
            wallet_service: Wallet service instance
            bri_client: BRI API client
        """
        self.db = db
        self.wallet_service = wallet_service
        self.bri_client = bri_client
        self.settings_service = SettingsService(db)
    
    async def get_platform_fee_rate(self) -> Decimal:
        """Get current platform fee rate from settings.
        
        Returns:
            Platform fee rate percentage (e.g., 3.00 for 3%)
        """
        try:
            return await self.settings_service.get_platform_fee_rate()
        except Exception as e:
            logger.warning(f"Failed to get platform fee rate from settings, using default 3%: {e}")
            return Decimal("3.00")
    
    async def calculate_platform_fee(self, gross_amount: Decimal, fee_rate: Optional[Decimal] = None) -> Decimal:
        """Calculate platform fee based on settings or provided rate.
        
        Args:
            gross_amount: Total amount
            fee_rate: Optional fee rate override (uses settings if not provided)
            
        Returns:
            Platform fee amount
        """
        if fee_rate is None:
            fee_rate = await self.get_platform_fee_rate()
        
        return (gross_amount * fee_rate / Decimal("100")).quantize(Decimal("0.01"))
    
    async def calculate_net_amount(self, gross_amount: Decimal, fee_rate: Optional[Decimal] = None) -> Decimal:
        """Calculate net amount after platform fee.
        
        Args:
            gross_amount: Total amount
            fee_rate: Optional fee rate override (uses settings if not provided)
            
        Returns:
            Net amount (gross - platform fee)
        """
        fee = await self.calculate_platform_fee(gross_amount, fee_rate)
        return gross_amount - fee
    
    async def settle_order(
        self,
        order_id: str,
        seller_user_id: str,
        gross_amount: Decimal,
        settlement_note: Optional[str] = None
    ) -> Dict[str, Any]:
        """Settle order payment to seller with platform fee deduction.
        
        This is called when buyer confirms delivery (order status = completed).
        
        Args:
            order_id: Order ID
            seller_user_id: Seller user ID
            gross_amount: Total order amount
            settlement_note: Optional settlement note
            
        Returns:
            Settlement record
            
        Raises:
            SettlementError: If settlement fails
        """
        if not self.wallet_service:
            raise SettlementError("Wallet service not available")
        
        # Get current platform fee rate from settings
        fee_rate = await self.get_platform_fee_rate()
        
        # Calculate amounts
        platform_fee = await self.calculate_platform_fee(gross_amount, fee_rate)
        net_amount = gross_amount - platform_fee
        
        logger.info(
            f"Order settlement {order_id}: Gross={gross_amount}, "
            f"Fee={platform_fee} ({fee_rate}%), Net={net_amount}"
        )
        
        # Create settlement record
        settlement_data = {
            'settlement_type': SettlementType.ORDER.value,
            'reference_id': order_id,
            'seller_user_id': seller_user_id,
            'gross_amount': float(gross_amount),
            'platform_fee': float(platform_fee),
            'net_amount': float(net_amount),
            'status': SettlementStatus.PROCESSING.value,
            'settlement_note': settlement_note,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        result = self.db.table('order_settlements').insert(settlement_data).execute()
        settlement = result.data[0] if result.data else None
        
        if not settlement:
            raise SettlementError("Failed to create settlement record")
        
        try:
            # Credit seller wallet with net amount
            await self.wallet_service._credit_wallet(
                wallet_id=(await self.wallet_service.get_wallet(seller_user_id)).id,
                amount=net_amount,
                transaction_type='payout',
                reference_type='order',
                reference_id=order_id,
                description=f"Payout dari order (after {fee_rate}% platform fee)"
            )
            
            # Update settlement status
            self.db.table('order_settlements').update({
                'status': SettlementStatus.COMPLETED.value,
                'settled_at': datetime.now(timezone.utc).isoformat()
            }).eq('id', settlement['id']).execute()
            
            settlement['status'] = SettlementStatus.COMPLETED.value
            
            logger.info(f"Order settlement completed: {settlement['id']}")
            
        except Exception as e:
            logger.error(f"Order settlement failed: {e}")
            
            # Update settlement status to failed
            self.db.table('order_settlements').update({
                'status': SettlementStatus.FAILED.value,
                'error_message': str(e)
            }).eq('id', settlement['id']).execute()
            
            raise SettlementError(f"Settlement failed: {e}")
        
        return settlement
    
    async def settle_sambatan(
        self,
        campaign_id: str,
        brand_owner_user_id: str,
        total_collected: Decimal,
        settlement_note: Optional[str] = None
    ) -> Dict[str, Any]:
        """Settle sambatan payout to brand owner with platform fee deduction.
        
        This is called when sambatan campaign is completed successfully.
        
        Args:
            campaign_id: Sambatan campaign ID
            brand_owner_user_id: Brand owner user ID
            total_collected: Total amount collected from participants
            settlement_note: Optional settlement note
            
        Returns:
            Settlement record
            
        Raises:
            SettlementError: If settlement fails
        """
        if not self.wallet_service:
            raise SettlementError("Wallet service not available")
        
        # Get current platform fee rate from settings
        fee_rate = await self.get_platform_fee_rate()
        
        # Calculate amounts
        platform_fee = await self.calculate_platform_fee(total_collected, fee_rate)
        net_amount = total_collected - platform_fee
        
        logger.info(
            f"Sambatan settlement {campaign_id}: Collected={total_collected}, "
            f"Fee={platform_fee} ({fee_rate}%), Net={net_amount}"
        )
        
        # Create settlement record
        settlement_data = {
            'settlement_type': SettlementType.SAMBATAN.value,
            'reference_id': campaign_id,
            'seller_user_id': brand_owner_user_id,
            'gross_amount': float(total_collected),
            'platform_fee': float(platform_fee),
            'net_amount': float(net_amount),
            'status': SettlementStatus.PROCESSING.value,
            'settlement_note': settlement_note,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        result = self.db.table('order_settlements').insert(settlement_data).execute()
        settlement = result.data[0] if result.data else None
        
        if not settlement:
            raise SettlementError("Failed to create settlement record")
        
        try:
            # Credit brand owner wallet with net amount
            await self.wallet_service._credit_wallet(
                wallet_id=(await self.wallet_service.get_wallet(brand_owner_user_id)).id,
                amount=net_amount,
                transaction_type='payout',
                reference_type='sambatan',
                reference_id=campaign_id,
                description=f"Payout dari sambatan (after {fee_rate}% platform fee)"
            )
            
            # Update settlement status
            self.db.table('order_settlements').update({
                'status': SettlementStatus.COMPLETED.value,
                'settled_at': datetime.now(timezone.utc).isoformat()
            }).eq('id', settlement['id']).execute()
            
            settlement['status'] = SettlementStatus.COMPLETED.value
            
            logger.info(f"Sambatan settlement completed: {settlement['id']}")
            
        except Exception as e:
            logger.error(f"Sambatan settlement failed: {e}")
            
            # Update settlement status to failed
            self.db.table('order_settlements').update({
                'status': SettlementStatus.FAILED.value,
                'error_message': str(e)
            }).eq('id', settlement['id']).execute()
            
            raise SettlementError(f"Settlement failed: {e}")
        
        return settlement
    
    async def create_order_settlement(
        self,
        order_id: str,
        gross_amount: Decimal,
        seller_user_id: str,
        settlement_note: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create settlement record for order (for tracking purposes).
        
        This is used when wallet service handles the actual fund transfer
        but we need to track the settlement separately.
        
        Args:
            order_id: Order ID
            gross_amount: Total order amount
            seller_user_id: Seller user ID
            settlement_note: Optional settlement note
            
        Returns:
            Settlement record
        """
        # Get current platform fee rate from settings
        fee_rate = await self.get_platform_fee_rate()
        
        # Calculate amounts
        platform_fee = await self.calculate_platform_fee(gross_amount, fee_rate)
        net_amount = gross_amount - platform_fee
        
        settlement_data = {
            'settlement_type': SettlementType.ORDER.value,
            'reference_id': order_id,
            'seller_user_id': seller_user_id,
            'gross_amount': float(gross_amount),
            'platform_fee': float(platform_fee),
            'net_amount': float(net_amount),
            'status': SettlementStatus.COMPLETED.value,
            'settlement_note': settlement_note,
            'settled_at': datetime.now(timezone.utc).isoformat(),
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        result = self.db.table('order_settlements').insert(settlement_data).execute()
        settlement = result.data[0] if result.data else None
        
        if not settlement:
            raise SettlementError("Failed to create settlement record")
        
        logger.info(f"Settlement record created for order {order_id}: {settlement['id']}")
        
        return settlement
    
    async def get_settlement(self, settlement_id: str) -> Optional[Dict[str, Any]]:
        """Get settlement details.
        
        Args:
            settlement_id: Settlement ID
            
        Returns:
            Settlement record or None
        """
        result = self.db.table('order_settlements').select('*').eq('id', settlement_id).execute()
        return result.data[0] if result.data else None
    
    async def list_settlements(
        self,
        seller_user_id: Optional[str] = None,
        settlement_type: Optional[SettlementType] = None,
        status: Optional[SettlementStatus] = None,
        limit: int = 50
    ) -> list[Dict[str, Any]]:
        """List settlements with filters.
        
        Args:
            seller_user_id: Filter by seller user ID
            settlement_type: Filter by settlement type
            status: Filter by status
            limit: Maximum records to return
            
        Returns:
            List of settlement records
        """
        query = self.db.table('order_settlements').select('*')
        
        if seller_user_id:
            query = query.eq('seller_user_id', seller_user_id)
        
        if settlement_type:
            query = query.eq('settlement_type', settlement_type.value)
        
        if status:
            query = query.eq('status', status.value)
        
        result = query.order('created_at', desc=True).limit(limit).execute()
        return result.data
