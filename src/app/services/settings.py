"""Platform settings service for configurable parameters."""

import logging
from typing import Dict, Any, Optional
from decimal import Decimal

try:
    from supabase import Client
except ImportError:
    Client = None  # type: ignore

logger = logging.getLogger(__name__)


class SettingsService:
    """Service for managing platform-wide settings."""
    
    SETTINGS_ID = '00000000-0000-0000-0000-000000000001'  # Single row constraint
    
    def __init__(self, db: Client):
        """Initialize settings service.
        
        Args:
            db: Supabase client instance
        """
        self.db = db
    
    async def get_settings(self) -> Dict[str, Any]:
        """Get current platform settings.
        
        Returns:
            Dict containing platform settings
            
        Raises:
            Exception if settings not found or database error
        """
        if not self.db:
            raise Exception("Database client not initialized")
        
        try:
            result = self.db.table('platform_settings').select('*').eq(
                'id', self.SETTINGS_ID
            ).execute()
            
            if not result.data:
                # Return default settings if not found
                logger.warning("Platform settings not found, returning defaults")
                return {
                    'bank_account_number': '201101000546304',
                    'bank_account_name': 'SENSASI WANGI INDONE',
                    'bank_name': 'BRI',
                    'platform_fee_rate': Decimal('3.00')
                }
            
            settings = result.data[0]
            
            # Convert fee rate to Decimal for precision
            settings['platform_fee_rate'] = Decimal(str(settings['platform_fee_rate']))
            
            return settings
            
        except Exception as e:
            logger.error(f"Failed to get platform settings: {str(e)}")
            raise
    
    async def get_platform_fee_rate(self) -> Decimal:
        """Get current platform fee rate.
        
        Returns:
            Decimal: Platform fee rate (e.g., 3.00 for 3%)
        """
        settings = await self.get_settings()
        return settings['platform_fee_rate']
    
    async def get_platform_bank_account(self) -> Dict[str, str]:
        """Get platform bank account details.
        
        Returns:
            Dict with bank_account_number, bank_account_name, bank_name
        """
        settings = await self.get_settings()
        return {
            'bank_account_number': settings['bank_account_number'],
            'bank_account_name': settings['bank_account_name'],
            'bank_name': settings['bank_name']
        }
    
    async def update_settings(
        self,
        bank_account_number: Optional[str] = None,
        bank_account_name: Optional[str] = None,
        bank_name: Optional[str] = None,
        platform_fee_rate: Optional[Decimal] = None,
        updated_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update platform settings.
        
        Args:
            bank_account_number: Platform bank account number
            bank_account_name: Account holder name
            bank_name: Bank name
            platform_fee_rate: Fee percentage (0-100)
            updated_by: User ID who updated settings
            
        Returns:
            Updated settings dict
            
        Raises:
            ValueError if fee rate is out of range
            Exception if database error
        """
        if not self.db:
            raise Exception("Database client not initialized")
        
        # Validate fee rate
        if platform_fee_rate is not None:
            if platform_fee_rate < 0 or platform_fee_rate > 100:
                raise ValueError("Platform fee rate must be between 0 and 100")
        
        # Build update dict with only provided fields
        update_data = {}
        if bank_account_number is not None:
            update_data['bank_account_number'] = bank_account_number
        if bank_account_name is not None:
            update_data['bank_account_name'] = bank_account_name
        if bank_name is not None:
            update_data['bank_name'] = bank_name
        if platform_fee_rate is not None:
            update_data['platform_fee_rate'] = float(platform_fee_rate)
        if updated_by is not None:
            update_data['updated_by'] = updated_by
        
        if not update_data:
            raise ValueError("No fields provided for update")
        
        try:
            result = self.db.table('platform_settings').update(update_data).eq(
                'id', self.SETTINGS_ID
            ).execute()
            
            if not result.data:
                raise Exception("Failed to update platform settings")
            
            updated_settings = result.data[0]
            updated_settings['platform_fee_rate'] = Decimal(str(updated_settings['platform_fee_rate']))
            
            logger.info(f"Platform settings updated by {updated_by}: {list(update_data.keys())}")
            
            return updated_settings
            
        except Exception as e:
            logger.error(f"Failed to update platform settings: {str(e)}")
            raise
