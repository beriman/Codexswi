"""Wallet Service - Digital wallet management with BRI BaaS integration."""

import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from supabase import Client

from app.services.bri_api import BRIAPIClient, BRIAPIError, BRIInsufficientBalanceError

logger = logging.getLogger(__name__)


# ============================================================================
# Exceptions
# ============================================================================

class WalletError(Exception):
    """Base wallet exception."""
    pass


class WalletNotFound(WalletError):
    """Wallet not found."""
    pass


class InsufficientBalance(WalletError):
    """Insufficient wallet balance."""
    pass


class TopUpError(WalletError):
    """Top-up related error."""
    pass


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class Wallet:
    """User wallet."""
    id: str
    user_id: str
    balance: Decimal
    bri_account_number: Optional[str]
    bri_customer_id: Optional[str]
    status: str
    kyc_status: str
    created_at: datetime
    updated_at: datetime


@dataclass
class WalletTransaction:
    """Wallet transaction."""
    id: str
    wallet_id: str
    transaction_type: str
    amount: Decimal
    balance_before: Decimal
    balance_after: Decimal
    status: str
    reference_type: Optional[str]
    reference_id: Optional[str]
    description: Optional[str]
    created_at: datetime


@dataclass
class TopUpRequest:
    """Top-up request."""
    id: str
    wallet_id: str
    amount: Decimal
    virtual_account: str
    status: str
    expires_at: datetime
    created_at: datetime
    bri_va_data: Optional[Dict[str, Any]] = None


# ============================================================================
# Wallet Service
# ============================================================================

class WalletService:
    """Wallet service for managing user digital wallets."""
    
    PLATFORM_FEE_RATE = Decimal("3.00")  # 3%
    
    def __init__(self, db: Optional[Client] = None, bri_client: Optional[BRIAPIClient] = None):
        """Initialize wallet service.
        
        Args:
            db: Supabase client
            bri_client: BRI API client
        """
        self.db = db
        self.bri_client = bri_client
    
    # ========================================================================
    # Wallet Management
    # ========================================================================
    
    async def create_wallet(self, user_id: str) -> Wallet:
        """Create wallet for user.
        
        Args:
            user_id: User ID
            
        Returns:
            Created wallet
            
        Raises:
            WalletError: If wallet creation fails
        """
        if not self.db:
            raise WalletError("Database not available")
        
        # Check if wallet already exists
        existing = self.db.table('user_wallets').select('*').eq('user_id', user_id).execute()
        if existing.data:
            return self._map_wallet(existing.data[0])
        
        # Create new wallet
        wallet_data = {
            'user_id': user_id,
            'balance': 0,
            'status': 'active',
            'kyc_status': 'pending'
        }
        
        result = self.db.table('user_wallets').insert(wallet_data).execute()
        
        if not result.data:
            raise WalletError("Failed to create wallet")
        
        wallet = self._map_wallet(result.data[0])
        logger.info(f"Wallet created for user {user_id}: {wallet.id}")
        
        return wallet
    
    async def get_wallet(self, user_id: str) -> Wallet:
        """Get user wallet.
        
        Args:
            user_id: User ID
            
        Returns:
            User wallet
            
        Raises:
            WalletNotFound: If wallet doesn't exist
        """
        if not self.db:
            raise WalletError("Database not available")
        
        result = self.db.table('user_wallets').select('*').eq('user_id', user_id).execute()
        
        if not result.data:
            raise WalletNotFound(f"Wallet not found for user {user_id}")
        
        return self._map_wallet(result.data[0])
    
    async def get_wallet_by_id(self, wallet_id: str) -> Wallet:
        """Get wallet by ID.
        
        Args:
            wallet_id: Wallet ID
            
        Returns:
            Wallet
            
        Raises:
            WalletNotFound: If wallet doesn't exist
        """
        if not self.db:
            raise WalletError("Database not available")
        
        result = self.db.table('user_wallets').select('*').eq('id', wallet_id).execute()
        
        if not result.data:
            raise WalletNotFound(f"Wallet not found: {wallet_id}")
        
        return self._map_wallet(result.data[0])
    
    async def sync_balance_with_bri(self, wallet_id: str) -> Wallet:
        """Sync wallet balance with BRI account.
        
        Args:
            wallet_id: Wallet ID
            
        Returns:
            Updated wallet
        """
        if not self.bri_client:
            logger.warning("BRI client not available, skipping balance sync")
            return await self.get_wallet_by_id(wallet_id)
        
        wallet = await self.get_wallet_by_id(wallet_id)
        
        if not wallet.bri_account_number:
            return wallet
        
        try:
            balance_response = await self.bri_client.get_account_balance(wallet.bri_account_number)
            
            if wallet.balance != balance_response.balance:
                logger.info(
                    f"Balance mismatch for wallet {wallet_id}. "
                    f"Local: {wallet.balance}, BRI: {balance_response.balance}"
                )
                
                # Update local balance
                self.db.table('user_wallets').update({
                    'balance': float(balance_response.balance),
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }).eq('id', wallet_id).execute()
                
                wallet.balance = balance_response.balance
        
        except BRIAPIError as e:
            logger.error(f"Failed to sync balance for wallet {wallet_id}: {e}")
        
        return wallet
    
    # ========================================================================
    # Top-Up
    # ========================================================================
    
    async def create_topup_request(
        self,
        user_id: str,
        amount: Decimal,
        customer_name: str
    ) -> TopUpRequest:
        """Create top-up request with BRIVA.
        
        Args:
            user_id: User ID
            amount: Top-up amount
            customer_name: Customer name for BRIVA
            
        Returns:
            Top-up request with virtual account
            
        Raises:
            TopUpError: If top-up creation fails
        """
        if not self.db:
            raise TopUpError("Database not available")
        
        if not self.bri_client:
            raise TopUpError("BRI client not available")
        
        if amount < Decimal("10000"):  # Min Rp 10.000
            raise TopUpError("Minimum top-up amount is Rp 10.000")
        
        # Get or create wallet
        try:
            wallet = await self.get_wallet(user_id)
        except WalletNotFound:
            wallet = await self.create_wallet(user_id)
        
        # Generate unique customer code
        import uuid
        customer_code = f"TOP{uuid.uuid4().hex[:8].upper()}"
        
        # Create BRIVA
        try:
            briva_response = await self.bri_client.create_briva(
                amount=amount,
                customer_name=customer_name,
                customer_code=customer_code,
                description=f"Top-up wallet {wallet.id[:8]}"
            )
        except BRIAPIError as e:
            logger.error(f"Failed to create BRIVA: {e}")
            raise TopUpError(f"Failed to create top-up request: {e}")
        
        # Save top-up request
        expires_at = datetime.now(timezone.utc) + timedelta(hours=48)
        
        topup_data = {
            'wallet_id': wallet.id,
            'amount': float(amount),
            'virtual_account': briva_response.virtual_account,
            'status': 'pending',
            'expires_at': expires_at.isoformat(),
            'bri_va_data': {
                'institution_code': briva_response.institution_code,
                'briva_no': briva_response.briva_no,
                'cust_code': briva_response.cust_code,
                'expired_date': briva_response.expired_date
            }
        }
        
        result = self.db.table('wallet_topup_requests').insert(topup_data).execute()
        
        if not result.data:
            raise TopUpError("Failed to save top-up request")
        
        topup = self._map_topup(result.data[0])
        logger.info(f"Top-up request created: {topup.id}, VA: {topup.virtual_account}")
        
        return topup
    
    async def process_topup_payment(self, virtual_account: str, paid_amount: Decimal) -> TopUpRequest:
        """Process top-up payment confirmation from webhook.
        
        Args:
            virtual_account: BRIVA virtual account number
            paid_amount: Amount paid
            
        Returns:
            Updated top-up request
            
        Raises:
            TopUpError: If processing fails
        """
        if not self.db:
            raise TopUpError("Database not available")
        
        # Find top-up request
        result = self.db.table('wallet_topup_requests').select('*').eq(
            'virtual_account', virtual_account
        ).eq('status', 'pending').execute()
        
        if not result.data:
            raise TopUpError(f"Top-up request not found for VA: {virtual_account}")
        
        topup_data = result.data[0]
        topup = self._map_topup(topup_data)
        
        # Validate amount
        if paid_amount != topup.amount:
            logger.warning(
                f"Payment amount mismatch for VA {virtual_account}. "
                f"Expected: {topup.amount}, Paid: {paid_amount}"
            )
        
        # Credit wallet
        try:
            await self._credit_wallet(
                wallet_id=topup.wallet_id,
                amount=paid_amount,
                transaction_type='topup',
                reference_type='topup',
                reference_id=topup.id,
                description=f"Top-up via BRIVA {virtual_account}"
            )
        except Exception as e:
            logger.error(f"Failed to credit wallet: {e}")
            raise TopUpError(f"Failed to process top-up: {e}")
        
        # Update top-up status
        self.db.table('wallet_topup_requests').update({
            'status': 'paid',
            'paid_at': datetime.now(timezone.utc).isoformat()
        }).eq('id', topup.id).execute()
        
        topup.status = 'paid'
        logger.info(f"Top-up processed: {topup.id}, Amount: {paid_amount}")
        
        return topup
    
    # ========================================================================
    # Transactions
    # ========================================================================
    
    async def debit_wallet(
        self,
        user_id: str,
        amount: Decimal,
        transaction_type: str,
        reference_type: Optional[str] = None,
        reference_id: Optional[str] = None,
        description: Optional[str] = None
    ) -> WalletTransaction:
        """Debit amount from wallet.
        
        Args:
            user_id: User ID
            amount: Amount to debit
            transaction_type: Transaction type (payment, withdrawal, etc)
            reference_type: Reference type (order, sambatan, etc)
            reference_id: Reference ID
            description: Transaction description
            
        Returns:
            Transaction record
            
        Raises:
            InsufficientBalance: If balance insufficient
        """
        wallet = await self.get_wallet(user_id)
        
        if wallet.balance < amount:
            raise InsufficientBalance(
                f"Insufficient balance. Available: {wallet.balance}, Required: {amount}"
            )
        
        return await self._debit_wallet(
            wallet_id=wallet.id,
            amount=amount,
            transaction_type=transaction_type,
            reference_type=reference_type,
            reference_id=reference_id,
            description=description
        )
    
    async def _debit_wallet(
        self,
        wallet_id: str,
        amount: Decimal,
        transaction_type: str,
        reference_type: Optional[str] = None,
        reference_id: Optional[str] = None,
        description: Optional[str] = None
    ) -> WalletTransaction:
        """Internal debit wallet function."""
        if not self.db:
            raise WalletError("Database not available")
        
        # Use database function for atomic operation
        result = self.db.rpc('debit_wallet', {
            'p_wallet_id': wallet_id,
            'p_amount': float(amount),
            'p_transaction_type': transaction_type,
            'p_reference_type': reference_type,
            'p_reference_id': reference_id,
            'p_description': description
        }).execute()
        
        transaction_id = result.data
        
        # Get transaction details
        tx_result = self.db.table('wallet_transactions').select('*').eq('id', transaction_id).execute()
        
        return self._map_transaction(tx_result.data[0])
    
    async def _credit_wallet(
        self,
        wallet_id: str,
        amount: Decimal,
        transaction_type: str,
        reference_type: Optional[str] = None,
        reference_id: Optional[str] = None,
        description: Optional[str] = None
    ) -> WalletTransaction:
        """Internal credit wallet function."""
        if not self.db:
            raise WalletError("Database not available")
        
        # Use database function for atomic operation
        result = self.db.rpc('credit_wallet', {
            'p_wallet_id': wallet_id,
            'p_amount': float(amount),
            'p_transaction_type': transaction_type,
            'p_reference_type': reference_type,
            'p_reference_id': reference_id,
            'p_description': description
        }).execute()
        
        transaction_id = result.data
        
        # Get transaction details
        tx_result = self.db.table('wallet_transactions').select('*').eq('id', transaction_id).execute()
        
        return self._map_transaction(tx_result.data[0])
    
    async def get_transactions(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        transaction_type: Optional[str] = None
    ) -> List[WalletTransaction]:
        """Get wallet transaction history.
        
        Args:
            user_id: User ID
            limit: Number of transactions to retrieve
            offset: Offset for pagination
            transaction_type: Filter by transaction type
            
        Returns:
            List of transactions
        """
        if not self.db:
            return []
        
        wallet = await self.get_wallet(user_id)
        
        query = self.db.table('wallet_transactions').select('*').eq('wallet_id', wallet.id)
        
        if transaction_type:
            query = query.eq('transaction_type', transaction_type)
        
        result = query.order('created_at', desc=True).limit(limit).offset(offset).execute()
        
        return [self._map_transaction(tx) for tx in result.data]
    
    # ========================================================================
    # Platform Fee & Settlement
    # ========================================================================
    
    @classmethod
    def calculate_platform_fee(cls, amount: Decimal) -> Decimal:
        """Calculate platform fee (3%).
        
        Args:
            amount: Gross amount
            
        Returns:
            Platform fee amount
        """
        return (amount * cls.PLATFORM_FEE_RATE / Decimal("100")).quantize(Decimal("0.01"))
    
    @classmethod
    def calculate_seller_payout(cls, gross_amount: Decimal) -> Decimal:
        """Calculate seller payout after platform fee.
        
        Args:
            gross_amount: Total payment amount
            
        Returns:
            Amount to pay seller (gross - platform fee)
        """
        fee = cls.calculate_platform_fee(gross_amount)
        return gross_amount - fee
    
    # ========================================================================
    # Mappers
    # ========================================================================
    
    def _map_wallet(self, data: Dict[str, Any]) -> Wallet:
        """Map database row to Wallet."""
        return Wallet(
            id=data['id'],
            user_id=data['user_id'],
            balance=Decimal(str(data['balance'])),
            bri_account_number=data.get('bri_account_number'),
            bri_customer_id=data.get('bri_customer_id'),
            status=data['status'],
            kyc_status=data['kyc_status'],
            created_at=datetime.fromisoformat(data['created_at'].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00'))
        )
    
    def _map_transaction(self, data: Dict[str, Any]) -> WalletTransaction:
        """Map database row to WalletTransaction."""
        return WalletTransaction(
            id=data['id'],
            wallet_id=data['wallet_id'],
            transaction_type=data['transaction_type'],
            amount=Decimal(str(data['amount'])),
            balance_before=Decimal(str(data['balance_before'])),
            balance_after=Decimal(str(data['balance_after'])),
            status=data['status'],
            reference_type=data.get('reference_type'),
            reference_id=data.get('reference_id'),
            description=data.get('description'),
            created_at=datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
        )
    
    def _map_topup(self, data: Dict[str, Any]) -> TopUpRequest:
        """Map database row to TopUpRequest."""
        return TopUpRequest(
            id=data['id'],
            wallet_id=data['wallet_id'],
            amount=Decimal(str(data['amount'])),
            virtual_account=data['virtual_account'],
            status=data['status'],
            expires_at=datetime.fromisoformat(data['expires_at'].replace('Z', '+00:00')),
            created_at=datetime.fromisoformat(data['created_at'].replace('Z', '+00:00')),
            bri_va_data=data.get('bri_va_data')
        )


# ============================================================================
# Factory & Singleton
# ============================================================================

_wallet_service: Optional[WalletService] = None


def get_wallet_service(db: Optional[Client] = None, bri_client: Optional[BRIAPIClient] = None) -> WalletService:
    """Get wallet service instance.
    
    Args:
        db: Supabase client
        bri_client: BRI API client
        
    Returns:
        Wallet service
    """
    global _wallet_service
    
    if _wallet_service is None:
        _wallet_service = WalletService(db=db, bri_client=bri_client)
    
    return _wallet_service
