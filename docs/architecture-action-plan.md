# Rencana Aksi: Menyesuaikan Arsitektur dengan PRD MVP

**Tanggal**: 2025-10-05  
**Status**: Ready for Implementation  
**Priority**: KRITIS - Diperlukan untuk MVP launch

---

## Executive Summary

Berdasarkan analisis gap di `docs/architecture-prd-gap-analysis.md`, kami mengidentifikasi **13 komponen yang perlu dikerjakan** untuk menyesuaikan arsitektur dengan PRD_MVP.md. Dokumen ini memberikan **langkah-langkah konkret** untuk setiap komponen.

---

## Priority Matrix

### 🔴 TIER 1: KRITIS (Week 1-2)
Tanpa ini, MVP tidak bisa melakukan transaksi sama sekali.

1. **Setup Supabase Client** - Foundation untuk semua service
2. **Refactor Auth Service** - User persistence
3. **Refactor Product Service** - Catalog persistence  
4. **Implement Order Service** - Core shopping flow
5. **Implement Cart Management** - Shopping basket

### 🟠 TIER 2: TINGGI (Week 3-4)
Fitur unggulan MVP yang membedakan dengan kompetitor.

6. **Checkout Flow** - Complete purchase experience
7. **Sambatan Scheduler** - Automated lifecycle
8. **Sambatan Service Refactor** - Persistent campaigns
9. **RajaOngkir Integration** - Realistic shipping costs

### 🟡 TIER 3: MEDIUM (Week 5-6)
Enhancement dan reporting untuk operations.

10. **Order Templates** - User-facing order pages
11. **Reporting Refactor** - Real data analytics
12. **Brand Service Enhancement** - Complete brand management
13. **Nusantarum Service Check** - Curator workflow

---

## Detailed Action Items

## 1. Setup Supabase Client ⏱️ 2 hours

**File**: `src/app/core/supabase.py` (NEW)

### Buat Supabase Client Factory

```python
"""Supabase client initialization and configuration."""

from functools import lru_cache
from typing import Optional

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None  # type: ignore

from app.core.config import get_settings


class SupabaseError(Exception):
    """Raised when Supabase operations fail."""


@lru_cache
def get_supabase_client() -> Optional[Client]:
    """Return a configured Supabase client or None if unavailable."""
    
    if not SUPABASE_AVAILABLE:
        return None
    
    settings = get_settings()
    
    if not settings.supabase_url or not settings.supabase_service_role_key:
        return None
    
    return create_client(
        settings.supabase_url,
        settings.supabase_service_role_key
    )


def require_supabase() -> Client:
    """Return Supabase client or raise if not configured."""
    
    client = get_supabase_client()
    if client is None:
        raise SupabaseError(
            "Supabase is not configured. Please set SUPABASE_URL and "
            "SUPABASE_SERVICE_ROLE_KEY environment variables."
        )
    return client
```

### Update Application Startup

**File**: `src/app/core/application.py`

```python
from app.core.supabase import get_supabase_client

def create_app() -> FastAPI:
    # ... existing code ...
    
    # Initialize Supabase client on startup
    @app.on_event("startup")
    async def startup():
        client = get_supabase_client()
        if client:
            app.state.supabase = client
            logger.info("Supabase client initialized successfully")
        else:
            logger.warning("Supabase client not available - using fallback storage")
    
    return app
```

### Dependencies untuk Routes

**File**: `src/app/core/dependencies.py` (NEW)

```python
"""FastAPI dependencies for dependency injection."""

from fastapi import Depends, Request
from supabase import Client

from app.core.supabase import get_supabase_client


def get_db(request: Request) -> Client:
    """Provide Supabase client to route handlers."""
    
    if hasattr(request.app.state, 'supabase'):
        return request.app.state.supabase
    
    # Fallback to creating new client
    client = get_supabase_client()
    if not client:
        raise RuntimeError("Supabase client not initialized")
    return client
```

**Testing**:
```bash
# Set environment variables
export SUPABASE_URL="https://xxxxx.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="eyJhbGc..."

# Run app and check logs
python -m uvicorn app.main:app --reload
# Should see: "Supabase client initialized successfully"
```

---

## 2. Refactor Auth Service ⏱️ 8 hours

**File**: `src/app/services/auth.py`

### Replace In-Memory Storage with Supabase

```python
"""Authentication service with Supabase persistence."""

from supabase import Client
from app.core.supabase import require_supabase


class AuthService:
    def __init__(self, db: Client = None):
        self.db = db or require_supabase()
    
    async def register(
        self,
        email: str,
        password: str,
        full_name: str
    ) -> RegistrationResult:
        """Register new user in Supabase auth_accounts table."""
        
        # Check if email exists
        existing = self.db.table('auth_accounts') \
            .select('id') \
            .eq('email', email) \
            .execute()
        
        if existing.data:
            raise UserAlreadyExists("Email sudah terdaftar")
        
        # Hash password
        password_hash = self._hash_password(password)
        
        # Create account
        account_data = {
            'email': email,
            'password_hash': password_hash,
            'full_name': full_name,
            'status': AccountStatus.PENDING_VERIFICATION.value
        }
        
        account_result = self.db.table('auth_accounts') \
            .insert(account_data) \
            .execute()
        
        account = account_result.data[0]
        
        # Create registration record
        verification_token = secrets.token_urlsafe(32)
        expires_at = datetime.now(UTC) + timedelta(hours=24)
        
        registration_data = {
            'email': email,
            'full_name': full_name,
            'password_hash': password_hash,
            'status': 'registered',
            'verification_token': verification_token,
            'verification_sent_at': datetime.now(UTC).isoformat(),
            'verification_expires_at': expires_at.isoformat()
        }
        
        registration_result = self.db.table('onboarding_registrations') \
            .insert(registration_data) \
            .execute()
        
        registration = registration_result.data[0]
        
        # Send verification email
        send_verification_email(email, verification_token)
        
        return RegistrationResult(
            account=self._map_account(account),
            registration=self._map_registration(registration)
        )
    
    async def login(self, email: str, password: str) -> AuthUser:
        """Authenticate user and create session."""
        
        # Get account
        result = self.db.table('auth_accounts') \
            .select('*') \
            .eq('email', email) \
            .execute()
        
        if not result.data:
            raise InvalidCredentials("Email atau password salah")
        
        account = result.data[0]
        
        # Verify password
        if not self._verify_password(password, account['password_hash']):
            raise InvalidCredentials("Email atau password salah")
        
        # Check status
        if account['status'] == 'disabled':
            raise AuthError("Akun telah dinonaktifkan")
        
        # Update last login
        self.db.table('auth_accounts') \
            .update({'last_login_at': datetime.now(UTC).isoformat()}) \
            .eq('id', account['id']) \
            .execute()
        
        return self._map_account(account)
    
    async def create_session(
        self,
        account_id: str,
        ip_address: str = None,
        user_agent: str = None
    ) -> str:
        """Create a new session token."""
        
        session_token = secrets.token_urlsafe(32)
        expires_at = datetime.now(UTC) + timedelta(days=30)
        
        session_data = {
            'account_id': account_id,
            'session_token': session_token,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'expires_at': expires_at.isoformat()
        }
        
        self.db.table('auth_sessions') \
            .insert(session_data) \
            .execute()
        
        return session_token
    
    async def verify_session(self, session_token: str) -> Optional[AuthUser]:
        """Verify and return user from session token."""
        
        result = self.db.table('auth_sessions') \
            .select('account_id, expires_at') \
            .eq('session_token', session_token) \
            .execute()
        
        if not result.data:
            return None
        
        session = result.data[0]
        
        # Check expiry
        expires_at = datetime.fromisoformat(session['expires_at'])
        if expires_at < datetime.now(UTC):
            return None
        
        # Get account
        account_result = self.db.table('auth_accounts') \
            .select('*') \
            .eq('id', session['account_id']) \
            .execute()
        
        if not account_result.data:
            return None
        
        return self._map_account(account_result.data[0])
    
    # ... other methods ...
```

### Update Routes

**File**: `src/app/api/routes/auth.py`

```python
from fastapi import Depends, Request
from app.core.dependencies import get_db
from app.services.auth import AuthService


@router.post("/api/auth/register")
async def register_user(
    payload: RegisterRequest,
    db: Client = Depends(get_db)
):
    auth_service = AuthService(db)
    result = await auth_service.register(
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name
    )
    return {"status": "success", "user_id": result.id}
```

**Testing**:
```python
# tests/test_auth_supabase.py
async def test_register_persists_to_database():
    auth_service = AuthService(test_db)
    result = await auth_service.register(
        email="test@example.com",
        password="securepass123",
        full_name="Test User"
    )
    
    # Verify in database
    accounts = test_db.table('auth_accounts') \
        .select('*') \
        .eq('email', 'test@example.com') \
        .execute()
    
    assert len(accounts.data) == 1
    assert accounts.data[0]['full_name'] == 'Test User'
```

---

## 3. Refactor Product Service ⏱️ 12 hours

**File**: `src/app/services/products.py`

### Complete Rewrite with Supabase

```python
"""Product catalog service with Supabase persistence."""

from typing import List, Optional, Dict, Any
from uuid import UUID
from supabase import Client

from app.core.supabase import require_supabase


class ProductService:
    def __init__(self, db: Client = None):
        self.db = db or require_supabase()
    
    async def create_product(
        self,
        brand_id: str,
        name: str,
        description: str,
        price_low: float,
        price_high: Optional[float] = None,
        highlight_aroma: Optional[str] = None,
        tags: List[str] = None,
        category_ids: List[int] = None
    ) -> Dict[str, Any]:
        """Create a new product in the catalog."""
        
        # Generate slug
        slug = self._slugify(name)
        
        # Insert product
        product_data = {
            'brand_id': brand_id,
            'slug': slug,
            'name': name,
            'description': description,
            'price_low': price_low,
            'price_high': price_high,
            'highlight_aroma': highlight_aroma,
            'tags': tags or [],
            'status': 'draft',
            'is_active': False,
            'marketplace_enabled': False
        }
        
        result = self.db.table('products') \
            .insert(product_data) \
            .execute()
        
        product = result.data[0]
        
        # Link categories
        if category_ids:
            category_links = [
                {'product_id': product['id'], 'category_id': cat_id}
                for cat_id in category_ids
            ]
            self.db.table('product_category_links') \
                .insert(category_links) \
                .execute()
        
        return product
    
    async def enable_marketplace_listing(
        self,
        product_id: str,
        list_price: float,
        stock_on_hand: int
    ):
        """Enable a product for marketplace sales."""
        
        # Update product
        self.db.table('products') \
            .update({
                'marketplace_enabled': True,
                'is_active': True,
                'status': 'active'
            }) \
            .eq('id', product_id) \
            .execute()
        
        # Create marketplace listing
        listing_data = {
            'product_id': product_id,
            'status': 'published',
            'list_price': list_price,
            'stock_on_hand': stock_on_hand,
            'stock_reserved': 0,
            'published_at': datetime.now(UTC).isoformat()
        }
        
        self.db.table('marketplace_listings') \
            .upsert(listing_data) \
            .execute()
    
    async def search_products(
        self,
        query: Optional[str] = None,
        category_slug: Optional[str] = None,
        brand_id: Optional[str] = None,
        marketplace_only: bool = True,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Search products with filters."""
        
        # Base query
        db_query = self.db.table('products') \
            .select('''
                *,
                brands(id, name, slug),
                marketplace_listings(list_price, stock_on_hand, status),
                product_category_links(category_id),
                product_images(file_path, is_primary)
            ''')
        
        if marketplace_only:
            db_query = db_query.eq('marketplace_enabled', True)
        
        if brand_id:
            db_query = db_query.eq('brand_id', brand_id)
        
        if category_slug:
            # Join with category
            db_query = db_query.eq('product_category_links.product_categories.slug', category_slug)
        
        if query:
            # Full-text search (requires tsvector in future)
            db_query = db_query.or_(
                f"name.ilike.%{query}%,"
                f"description.ilike.%{query}%,"
                f"highlight_aroma.ilike.%{query}%"
            )
        
        result = db_query.limit(limit).execute()
        
        return result.data
    
    async def enable_sambatan(
        self,
        product_id: str,
        total_slots: int,
        slot_price: float,
        deadline: datetime
    ):
        """Enable Sambatan mode for a product."""
        
        # Update product
        self.db.table('products') \
            .update({'sambatan_enabled': True}) \
            .eq('id', product_id) \
            .execute()
        
        # Create campaign
        campaign_data = {
            'product_id': product_id,
            'title': f"Sambatan Batch {datetime.now().strftime('%Y%m')}",
            'status': 'active',
            'total_slots': total_slots,
            'filled_slots': 0,
            'slot_price': slot_price,
            'deadline': deadline.isoformat()
        }
        
        self.db.table('sambatan_campaigns') \
            .insert(campaign_data) \
            .execute()
    
    # ... other methods ...
```

**Testing**:
```bash
pytest tests/test_products_supabase.py -v
```

---

## 4. Implement Order Service ⏱️ 16 hours

**File**: `src/app/services/orders.py` (NEW)

```python
"""Order management service for marketplace transactions."""

from datetime import datetime, UTC
from typing import List, Dict, Any, Optional
from decimal import Decimal
from supabase import Client

from app.core.supabase import require_supabase


class OrderError(Exception):
    """Base exception for order operations."""


class InsufficientStock(OrderError):
    """Raised when product stock is insufficient."""


class OrderService:
    def __init__(self, db: Client = None):
        self.db = db or require_supabase()
    
    async def create_order(
        self,
        customer_id: str,
        items: List[Dict[str, Any]],
        shipping_address: Dict[str, str],
        channel: str = 'marketplace'
    ) -> Dict[str, Any]:
        """Create a new order with items and shipping address."""
        
        # Generate order number
        order_number = self._generate_order_number()
        
        # Validate stock
        await self._validate_stock(items)
        
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
            'total_amount': float(subtotal)
        }
        
        order_result = self.db.table('orders') \
            .insert(order_data) \
            .execute()
        
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
        
        self.db.table('order_items') \
            .insert(order_items) \
            .execute()
        
        # Create shipping address
        address_data = {
            'order_id': order_id,
            **shipping_address
        }
        
        self.db.table('order_shipping_addresses') \
            .insert(address_data) \
            .execute()
        
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
        
        # Get current order
        order_result = self.db.table('orders') \
            .select('status, payment_status') \
            .eq('id', order_id) \
            .execute()
        
        if not order_result.data:
            raise OrderError("Order tidak ditemukan")
        
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
        elif new_status == 'cancelled':
            update_data['cancelled_at'] = datetime.now(UTC).isoformat()
            update_data['cancellation_reason'] = note
        
        self.db.table('orders') \
            .update(update_data) \
            .eq('id', order_id) \
            .execute()
        
        # Log status change
        await self._log_status_change(
            order_id,
            new_status,
            current_order.get('payment_status', 'pending'),
            actor_id,
            note
        )
        
        # Release inventory if cancelled
        if new_status == 'cancelled':
            await self._release_inventory(order_id)
    
    async def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get order details with items and shipping address."""
        
        result = self.db.table('orders') \
            .select('''
                *,
                order_items(*),
                order_shipping_addresses(*),
                order_status_history(*)
            ''') \
            .eq('id', order_id) \
            .execute()
        
        return result.data[0] if result.data else None
    
    async def list_customer_orders(
        self,
        customer_id: str,
        status_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List all orders for a customer."""
        
        query = self.db.table('orders') \
            .select('*, order_items(count)') \
            .eq('customer_id', customer_id) \
            .order('created_at', desc=True)
        
        if status_filter:
            query = query.eq('status', status_filter)
        
        result = query.execute()
        return result.data
    
    # Private helpers
    
    def _generate_order_number(self) -> str:
        """Generate unique order number."""
        from datetime import datetime
        import secrets
        
        date_part = datetime.now().strftime('%Y%m%d')
        random_part = secrets.token_hex(4).upper()
        return f"ORD-{date_part}-{random_part}"
    
    async def _validate_stock(self, items: List[Dict]) -> None:
        """Validate that all items have sufficient stock."""
        
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
        """Reserve inventory for order items."""
        
        for item in items:
            # Update marketplace listing
            self.db.rpc('reserve_stock', {
                'p_product_id': item['product_id'],
                'p_quantity': item['quantity']
            }).execute()
            
            # Log adjustment
            adjustment_data = {
                'product_id': item['product_id'],
                'adjustment': -item['quantity'],
                'reason': 'order_reservation',
                'reference_order_id': order_id,
                'note': f"Reserved for order {order_id}"
            }
            
            self.db.table('marketplace_inventory_adjustments') \
                .insert(adjustment_data) \
                .execute()
    
    async def _release_inventory(self, order_id: str) -> None:
        """Release reserved inventory for cancelled order."""
        
        # Get order items
        items_result = self.db.table('order_items') \
            .select('product_id, quantity') \
            .eq('order_id', order_id) \
            .execute()
        
        for item in items_result.data:
            # Update marketplace listing
            self.db.rpc('release_stock', {
                'p_product_id': item['product_id'],
                'p_quantity': item['quantity']
            }).execute()
            
            # Log adjustment
            adjustment_data = {
                'product_id': item['product_id'],
                'adjustment': item['quantity'],
                'reason': 'order_release',
                'reference_order_id': order_id,
                'note': f"Released from cancelled order {order_id}"
            }
            
            self.db.table('marketplace_inventory_adjustments') \
                .insert(adjustment_data) \
                .execute()
    
    async def _log_status_change(
        self,
        order_id: str,
        status: str,
        payment_status: str,
        actor_id: str,
        note: Optional[str]
    ) -> None:
        """Log order status change to history."""
        
        log_data = {
            'order_id': order_id,
            'status': status,
            'payment_status': payment_status,
            'actor_id': actor_id,
            'note': note
        }
        
        self.db.table('order_status_history') \
            .insert(log_data) \
            .execute()
```

### Add Database Functions

**File**: `supabase/migrations/0004_order_helpers.sql` (NEW)

```sql
-- Helper function to reserve stock atomically
CREATE OR REPLACE FUNCTION reserve_stock(p_product_id uuid, p_quantity integer)
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE marketplace_listings
    SET stock_reserved = stock_reserved + p_quantity
    WHERE product_id = p_product_id
      AND (stock_on_hand - stock_reserved) >= p_quantity;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Insufficient stock for product %', p_product_id;
    END IF;
END;
$$;

-- Helper function to release stock atomically
CREATE OR REPLACE FUNCTION release_stock(p_product_id uuid, p_quantity integer)
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE marketplace_listings
    SET stock_reserved = GREATEST(0, stock_reserved - p_quantity)
    WHERE product_id = p_product_id;
END;
$$;
```

**Testing**:
```python
# tests/test_orders.py
async def test_create_order_reserves_inventory():
    order_service = OrderService(test_db)
    
    items = [{
        'product_id': 'prod-123',
        'product_name': 'Rimba Embun',
        'unit_price': 420000,
        'quantity': 2
    }]
    
    order = await order_service.create_order(
        customer_id='user-123',
        items=items,
        shipping_address={...}
    )
    
    # Check inventory reserved
    listing = test_db.table('marketplace_listings') \
        .select('stock_reserved') \
        .eq('product_id', 'prod-123') \
        .execute()
    
    assert listing.data[0]['stock_reserved'] == 2
```

---

## 5. Implement Cart Management ⏱️ 6 hours

**File**: `src/app/services/cart.py` (NEW)

```python
"""Shopping cart service using session storage."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import json


@dataclass
class CartItem:
    product_id: str
    product_name: str
    brand_name: str
    unit_price: float
    quantity: int
    image_url: Optional[str] = None
    variant_id: Optional[str] = None
    
    @property
    def subtotal(self) -> float:
        return self.unit_price * self.quantity


class CartService:
    """Session-based cart management before order creation."""
    
    CART_SESSION_KEY = 'shopping_cart'
    
    def add_item(
        self,
        session: dict,
        product_id: str,
        product_name: str,
        brand_name: str,
        unit_price: float,
        quantity: int = 1,
        **kwargs
    ) -> None:
        """Add or update item in cart."""
        
        cart_items = self._get_cart_items(session)
        
        # Check if item already exists
        existing_index = None
        for i, item in enumerate(cart_items):
            if item['product_id'] == product_id:
                existing_index = i
                break
        
        if existing_index is not None:
            # Update quantity
            cart_items[existing_index]['quantity'] += quantity
        else:
            # Add new item
            cart_items.append({
                'product_id': product_id,
                'product_name': product_name,
                'brand_name': brand_name,
                'unit_price': unit_price,
                'quantity': quantity,
                **kwargs
            })
        
        self._save_cart_items(session, cart_items)
    
    def remove_item(self, session: dict, product_id: str) -> None:
        """Remove item from cart."""
        
        cart_items = self._get_cart_items(session)
        cart_items = [
            item for item in cart_items
            if item['product_id'] != product_id
        ]
        self._save_cart_items(session, cart_items)
    
    def update_quantity(
        self,
        session: dict,
        product_id: str,
        quantity: int
    ) -> None:
        """Update item quantity in cart."""
        
        if quantity < 1:
            return self.remove_item(session, product_id)
        
        cart_items = self._get_cart_items(session)
        for item in cart_items:
            if item['product_id'] == product_id:
                item['quantity'] = quantity
                break
        
        self._save_cart_items(session, cart_items)
    
    def get_cart(self, session: dict) -> Dict[str, Any]:
        """Get cart summary with items and totals."""
        
        items = self._get_cart_items(session)
        
        subtotal = sum(
            item['unit_price'] * item['quantity']
            for item in items
        )
        
        return {
            'items': items,
            'item_count': sum(item['quantity'] for item in items),
            'subtotal': subtotal,
            'shipping': 0,  # Will be calculated with RajaOngkir
            'total': subtotal
        }
    
    def clear_cart(self, session: dict) -> None:
        """Clear all items from cart."""
        
        session.pop(self.CART_SESSION_KEY, None)
    
    # Private helpers
    
    def _get_cart_items(self, session: dict) -> List[Dict]:
        """Get cart items from session."""
        
        cart_data = session.get(self.CART_SESSION_KEY, '[]')
        if isinstance(cart_data, str):
            return json.loads(cart_data)
        return cart_data or []
    
    def _save_cart_items(self, session: dict, items: List[Dict]) -> None:
        """Save cart items to session."""
        
        session[self.CART_SESSION_KEY] = json.dumps(items)
```

### Cart Routes

**File**: `src/app/api/routes/cart.py` (NEW)

```python
"""Shopping cart routes."""

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from app.services.cart import CartService

router = APIRouter(tags=["cart"])
cart_service = CartService()


@router.post("/api/cart/add")
async def add_to_cart(
    request: Request,
    product_id: str = Form(...),
    product_name: str = Form(...),
    brand_name: str = Form(...),
    unit_price: float = Form(...),
    quantity: int = Form(1)
):
    """Add item to cart."""
    
    cart_service.add_item(
        session=request.session,
        product_id=product_id,
        product_name=product_name,
        brand_name=brand_name,
        unit_price=unit_price,
        quantity=quantity
    )
    
    return {"status": "success", "message": "Produk ditambahkan ke keranjang"}


@router.get("/cart", response_class=HTMLResponse)
async def view_cart(request: Request):
    """View shopping cart page."""
    
    cart = cart_service.get_cart(request.session)
    templates = request.app.state.templates
    
    context = {
        "title": "Keranjang Belanja",
        "cart": cart
    }
    
    return templates.TemplateResponse(request, "cart.html", context)


@router.post("/api/cart/update")
async def update_cart_item(
    request: Request,
    product_id: str = Form(...),
    quantity: int = Form(...)
):
    """Update cart item quantity."""
    
    cart_service.update_quantity(
        session=request.session,
        product_id=product_id,
        quantity=quantity
    )
    
    return {"status": "success"}


@router.post("/api/cart/remove")
async def remove_from_cart(
    request: Request,
    product_id: str = Form(...)
):
    """Remove item from cart."""
    
    cart_service.remove_item(
        session=request.session,
        product_id=product_id
    )
    
    return {"status": "success"}
```

**Register in application.py**:
```python
from app.api.routes import cart as cart_routes
app.include_router(cart_routes.router)
```

---

## Summary Status

### Completed in this Document:
✅ 1. Supabase Client Setup - Implementation ready  
✅ 2. Auth Service Refactor - Complete rewrite provided  
✅ 3. Product Service Refactor - Complete rewrite provided  
✅ 4. Order Service - Full implementation provided  
✅ 5. Cart Management - Full implementation provided  

### Still TODO (Next Documents):
⏳ 6. Checkout Flow (Week 2)  
⏳ 7. Sambatan Scheduler (Week 3)  
⏳ 8. Sambatan Service Refactor (Week 3)  
⏳ 9. RajaOngkir Integration (Week 3)  
⏳ 10-13. Templates, Reporting, etc. (Week 4-6)

---

## Timeline Estimate

- **Week 1**: Items 1-3 (Setup, Auth, Products) → Foundation solid
- **Week 2**: Items 4-6 (Orders, Cart, Checkout) → Shopping flow complete
- **Week 3**: Items 7-9 (Sambatan features) → MVP feature parity
- **Week 4**: Items 10-11 (Templates, Reporting) → User experience polish
- **Week 5-6**: Testing, UAT, deployment prep

---

**Next Steps**:
1. Start with Item 1 (Supabase setup) - 2 hours
2. Proceed to Item 2 (Auth refactor) - 8 hours
3. Continue sequentially through items 3-5
4. Schedule code review after Item 3 is complete
5. Begin Phase 2 after Week 1 milestone

**Document Owner**: Development Team  
**Last Updated**: 2025-10-05
