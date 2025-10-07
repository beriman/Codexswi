"""Order management service for marketplace transactions."""

import logging
from datetime import datetime, UTC
from typing import List, Dict, Any, Optional
from decimal import Decimal

try:
    from supabase import Client
except ImportError:
    Client = None  # type: ignore

from app.services.wallet import WalletService
from app.services.settlement import SettlementService

logger = logging.getLogger(__name__)


class OrderError(Exception):
    """Base exception for order operations."""
    status_code: int = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class InsufficientStock(OrderError):
    """Raised when product stock is insufficient."""
    status_code = 400


class OrderNotFound(OrderError):
    """Raised when order is not found."""
    status_code = 404


class OrderService:
    """Service for managing marketplace orders with Supabase persistence."""

    def __init__(self, db: Optional[Client] = None):
        self.db = db

    async def create_order(
        self,
        customer_id: str,
        items: List[Dict[str, Any]],
        shipping_address: Dict[str, str],
        channel: str = 'marketplace',
        payment_method: str = 'wallet'
    ) -> Dict[str, Any]:
        """Create a new order with items and shipping address."""
        if not self.db:
            logger.error("Order creation attempted without database connection")
            raise OrderError("Database connection required for order operations")

        # Generate order number
        order_number = self._generate_order_number()
        logger.info(f"Creating order {order_number} for customer {customer_id} with {len(items)} items")

        # Validate stock
        try:
            await self._validate_stock(items)
        except InsufficientStock as e:
            logger.warning(f"Order creation failed for {order_number}: {str(e)}")
            raise

        # Calculate totals
        subtotal = sum(
            Decimal(str(item['unit_price'])) * item['quantity']
            for item in items
        )

        # Create order
        order_data = {
            'order_number': order_number,
            'customer_id': customer_id,
            'channel': channel,
            'status': 'draft',
            'payment_status': 'pending',
            'subtotal_amount': float(subtotal),
            'shipping_amount': 0,  # Will be calculated with RajaOngkir
            'discount_amount': 0,
            'total_amount': float(subtotal),
            'metadata': {'payment_method': payment_method}
        }

        order_result = self.db.table('orders').insert(order_data).execute()

        if not order_result.data:
            raise OrderError("Failed to create order")

        order = order_result.data[0]
        order_id = order['id']

        # Create order items
        order_items = []
        for item in items:
            item_data = {
                'order_id': order_id,
                'product_id': item['product_id'],
                'variant_id': item.get('variant_id'),
                'channel': channel,
                'product_name': item['product_name'],
                'brand_name': item.get('brand_name'),
                'sku': item.get('sku'),
                'unit_price': item['unit_price'],
                'quantity': item['quantity'],
                'subtotal_amount': item['unit_price'] * item['quantity']
            }
            order_items.append(item_data)

        self.db.table('order_items').insert(order_items).execute()

        # Create shipping address
        address_data = {
            'order_id': order_id,
            **shipping_address
        }

        self.db.table('order_shipping_addresses').insert(address_data).execute()

        # Reserve inventory
        await self._reserve_inventory(order_id, items)

        # Log status
        await self._log_status_change(
            order_id,
            'draft',
            'pending',
            actor_id=customer_id,
            note="Order dibuat"
        )

        logger.info(f"Order {order_number} created successfully with ID {order_id}")
        return order

    async def update_order_status(
        self,
        order_id: str,
        new_status: str,
        actor_id: str,
        note: Optional[str] = None,
        tracking_number: Optional[str] = None
    ):
        """Update order status and log the change."""
        if not self.db:
            logger.error("Order status update attempted without database connection")
            raise OrderError("Database connection required")

        logger.info(f"Updating order {order_id} status to {new_status} by actor {actor_id}")

        # Get current order
        order_result = self.db.table('orders').select('status, payment_status').eq('id', order_id).execute()

        if not order_result.data:
            logger.warning(f"Order status update failed: order {order_id} not found")
            raise OrderNotFound(f"Order dengan ID {order_id} tidak ditemukan")

        current_order = order_result.data[0]

        # Update order
        update_data = {'status': new_status}

        # Set timestamps based on status
        if new_status == 'paid':
            update_data['paid_at'] = datetime.now(UTC).isoformat()
            update_data['payment_status'] = 'paid'
        elif new_status == 'shipped':
            update_data['fulfilled_at'] = datetime.now(UTC).isoformat()
            if tracking_number:
                metadata = {'tracking_number': tracking_number}
                update_data['metadata'] = metadata
        elif new_status == 'completed':
            update_data['completed_at'] = datetime.now(UTC).isoformat()
            
            # Auto-release wallet funds to seller with platform fee
            await self._release_wallet_payment(order_id)
        elif new_status == 'cancelled':
            update_data['cancelled_at'] = datetime.now(UTC).isoformat()
            update_data['cancellation_reason'] = note

        self.db.table('orders').update(update_data).eq('id', order_id).execute()

        # Log status change
        await self._log_status_change(
            order_id,
            new_status,
            current_order.get('payment_status', 'pending'),
            actor_id,
            note
        )

        # Handle cancellation - release inventory and refund wallet
        if new_status == 'cancelled':
            await self._release_inventory(order_id)
            await self._refund_wallet_payment(order_id, note)

    async def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get order details with items and shipping address."""
        if not self.db:
            raise OrderError("Database connection required")

        result = self.db.table('orders') \
            .select('*, order_items(*), order_shipping_addresses(*), order_status_history(*)') \
            .eq('id', order_id) \
            .execute()

        return result.data[0] if result.data else None

    async def list_customer_orders(
        self,
        customer_id: str,
        status_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List all orders for a customer."""
        if not self.db:
            raise OrderError("Database connection required")

        query = self.db.table('orders') \
            .select('*, order_items(count)') \
            .eq('customer_id', customer_id) \
            .order('created_at', desc=True)

        if status_filter:
            query = query.eq('status', status_filter)

        result = query.execute()
        return result.data

    async def update_order_metadata(self, order_id: str, metadata: Dict[str, Any]) -> None:
        """Update order metadata."""
        if not self.db:
            raise OrderError("Database connection required")
        
        self.db.table('orders').update({'metadata': metadata}).eq('id', order_id).execute()
        logger.info(f"Updated metadata for order {order_id}")

    async def cancel_order(self, order_id: str, reason: str) -> None:
        """Cancel order and release inventory."""
        if not self.db:
            raise OrderError("Database connection required")
        
        # Update order status to cancelled
        update_data = {
            'status': 'cancelled',
            'cancelled_at': datetime.now(UTC).isoformat(),
            'cancellation_reason': reason
        }
        
        self.db.table('orders').update(update_data).eq('id', order_id).execute()
        
        # Release reserved inventory
        await self._release_inventory(order_id)
        
        # Log cancellation
        await self._log_status_change(
            order_id,
            'cancelled',
            'pending',
            actor_id=None,
            note=reason
        )
        
        logger.info(f"Order {order_id} cancelled: {reason}")

    # Private helpers

    def _generate_order_number(self) -> str:
        """Generate unique order number."""
        import secrets

        date_part = datetime.now().strftime('%Y%m%d')
        random_part = secrets.token_hex(4).upper()
        return f"ORD-{date_part}-{random_part}"

    async def _validate_stock(self, items: List[Dict]) -> None:
        """Validate that all items have sufficient stock."""
        if not self.db:
            return

        for item in items:
            listing = self.db.table('marketplace_listings') \
                .select('stock_on_hand, stock_reserved') \
                .eq('product_id', item['product_id']) \
                .execute()

            if not listing.data:
                raise OrderError(f"Produk {item['product_name']} tidak tersedia")

            available = listing.data[0]['stock_on_hand'] - listing.data[0]['stock_reserved']
            if available < item['quantity']:
                raise InsufficientStock(
                    f"Stok {item['product_name']} tidak mencukupi. "
                    f"Tersedia: {available}, diminta: {item['quantity']}"
                )

    async def _reserve_inventory(self, order_id: str, items: List[Dict]) -> None:
        """Reserve inventory for order items using atomic database function."""
        if not self.db:
            return

        for item in items:
            try:
                # Use atomic function from migration 0004 to prevent race conditions
                self.db.rpc('reserve_stock', {
                    'p_product_id': item['product_id'],
                    'p_quantity': item['quantity']
                }).execute()
                
                logger.debug(f"Reserved {item['quantity']} units of {item['product_id']} for order {order_id}")
                
            except Exception as e:
                # If reservation fails, this will bubble up and prevent order creation
                logger.error(f"Failed to reserve stock for {item['product_id']}: {str(e)}")
                raise InsufficientStock(
                    f"Gagal mereservasi stok untuk {item['product_name']}. "
                    f"Mungkin stok telah habis atau sedang direservasi."
                )

            # Log adjustment for audit trail
            adjustment_data = {
                'product_id': item['product_id'],
                'adjustment': -item['quantity'],
                'reason': 'order_reservation',
                'reference_order_id': order_id,
                'note': f"Reserved for order {order_id}"
            }

            self.db.table('marketplace_inventory_adjustments').insert(adjustment_data).execute()

    async def _release_inventory(self, order_id: str) -> None:
        """Release reserved inventory for cancelled order using atomic database function."""
        if not self.db:
            return

        # Get order items
        items_result = self.db.table('order_items') \
            .select('product_id, quantity') \
            .eq('order_id', order_id) \
            .execute()

        for item in items_result.data:
            try:
                # Use atomic function from migration 0004
                self.db.rpc('release_stock', {
                    'p_product_id': item['product_id'],
                    'p_quantity': item['quantity']
                }).execute()
                
                logger.debug(f"Released {item['quantity']} units of {item['product_id']} from order {order_id}")
                
            except Exception as e:
                # Log but don't fail - product might have been deleted
                logger.warning(f"Failed to release stock for {item['product_id']}: {str(e)}")

            # Log adjustment for audit trail
            adjustment_data = {
                'product_id': item['product_id'],
                'adjustment': item['quantity'],
                'reason': 'order_release',
                'reference_order_id': order_id,
                'note': f"Released from cancelled order {order_id}"
            }

            self.db.table('marketplace_inventory_adjustments').insert(adjustment_data).execute()

    async def _log_status_change(
        self,
        order_id: str,
        status: str,
        payment_status: str,
        actor_id: str,
        note: Optional[str]
    ) -> None:
        """Log order status change to history."""
        if not self.db:
            return

        log_data = {
            'order_id': order_id,
            'status': status,
            'payment_status': payment_status,
            'actor_id': actor_id,
            'note': note
        }

        self.db.table('order_status_history').insert(log_data).execute()

    async def _release_wallet_payment(self, order_id: str) -> None:
        """Release held wallet funds to seller with platform fee deduction."""
        if not self.db:
            return
        
        # Get order with metadata
        order = await self.get_order(order_id)
        if not order:
            logger.warning(f"Cannot release wallet payment: order {order_id} not found")
            return
        
        metadata = order.get('metadata', {})
        payment_method = metadata.get('payment_method')
        hold_transaction_id = metadata.get('wallet_hold_transaction_id')
        
        # Only process if payment method is wallet and we have hold transaction
        if payment_method != 'wallet' or not hold_transaction_id:
            logger.debug(f"Skipping wallet release for order {order_id}: payment_method={payment_method}")
            return
        
        try:
            # Get seller from first order item (assuming single seller per order for MVP)
            items = order.get('order_items', [])
            if not items:
                logger.error(f"No items found for order {order_id}")
                return
            
            # Get product to find seller/brand owner
            first_item = items[0]
            product_result = self.db.table('products').select('brand_id').eq(
                'id', first_item['product_id']
            ).execute()
            
            if not product_result.data:
                logger.error(f"Product not found for order {order_id}")
                return
            
            brand_id = product_result.data[0]['brand_id']
            
            # Get brand owner
            brand_result = self.db.table('brand_members').select('profile_id').eq(
                'brand_id', brand_id
            ).eq('role', 'owner').execute()
            
            if not brand_result.data:
                logger.error(f"Brand owner not found for brand {brand_id}")
                return
            
            seller_profile_id = brand_result.data[0]['profile_id']
            
            # Get seller user_id from profile
            profile_result = self.db.table('user_profiles').select('user_id').eq(
                'id', seller_profile_id
            ).execute()
            
            if not profile_result.data:
                logger.error(f"User not found for profile {seller_profile_id}")
                return
            
            seller_user_id = profile_result.data[0]['user_id']
            
            # Release funds using wallet service
            wallet_service = WalletService(self.db)
            release_result = await wallet_service.release_held_funds(
                hold_transaction_id=hold_transaction_id,
                seller_user_id=seller_user_id
            )
            
            # Create settlement record
            settlement_service = SettlementService(self.db)
            await settlement_service.create_order_settlement(
                order_id=order_id,
                gross_amount=Decimal(str(order['total_amount'])),
                seller_user_id=seller_user_id
            )
            
            logger.info(
                f"Wallet payment released for order {order_id}: "
                f"gross={release_result['gross_amount']}, "
                f"fee={release_result['platform_fee']}, "
                f"net={release_result['net_amount']}"
            )
            
        except Exception as e:
            logger.error(f"Failed to release wallet payment for order {order_id}: {str(e)}")

    async def _refund_wallet_payment(self, order_id: str, reason: Optional[str] = None) -> None:
        """Refund held wallet funds to buyer."""
        if not self.db:
            return
        
        # Get order with metadata
        order = await self.get_order(order_id)
        if not order:
            logger.warning(f"Cannot refund wallet payment: order {order_id} not found")
            return
        
        metadata = order.get('metadata', {})
        payment_method = metadata.get('payment_method')
        hold_transaction_id = metadata.get('wallet_hold_transaction_id')
        
        # Only process if payment method is wallet and we have hold transaction
        if payment_method != 'wallet' or not hold_transaction_id:
            logger.debug(f"Skipping wallet refund for order {order_id}: payment_method={payment_method}")
            return
        
        try:
            # Refund using wallet service
            wallet_service = WalletService(self.db)
            refund_tx_id = await wallet_service.refund_held_funds(
                hold_transaction_id=hold_transaction_id,
                reason=reason or f"Order {order['order_number']} cancelled"
            )
            
            logger.info(f"Wallet payment refunded for order {order_id}: {refund_tx_id}")
            
        except Exception as e:
            logger.error(f"Failed to refund wallet payment for order {order_id}: {str(e)}")
