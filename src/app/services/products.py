"""In-memory product catalog service with Sambatan toggles."""

from __future__ import annotations

import secrets
import re
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Dict, Iterable, Optional, List, Any

try:
    from supabase import Client
except ImportError:
    Client = None  # type: ignore

logger = logging.getLogger(__name__)


class ProductError(Exception):
    """Base error class for product operations."""

    status_code: int = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ProductNotFound(ProductError):
    """Raised when attempting to access a missing product."""

    status_code = 404


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


@dataclass
class Product:
    """Represents an item listed in the marketplace catalog."""

    id: str
    name: str
    base_price: int
    created_at: datetime
    updated_at: datetime
    is_sambatan_enabled: bool = False
    sambatan_total_slots: Optional[int] = None
    sambatan_deadline: Optional[datetime] = None

    def enable_sambatan(self, *, total_slots: int, deadline: datetime) -> None:
        if total_slots <= 0:
            raise ProductError("Total slot sambatan harus lebih dari 0.")
        deadline = _ensure_utc(deadline)
        now = datetime.now(UTC)
        if deadline <= now:
            raise ProductError("Deadline sambatan harus berada di masa depan.")

        self.is_sambatan_enabled = True
        self.sambatan_total_slots = total_slots
        self.sambatan_deadline = deadline
        self.updated_at = now

    def disable_sambatan(self) -> None:
        self.is_sambatan_enabled = False
        self.sambatan_total_slots = None
        self.sambatan_deadline = None
        self.updated_at = datetime.now(UTC)


class ProductService:
    """Product catalog service with Supabase persistence and fallback to in-memory."""

    def __init__(self, db: Optional[Client] = None) -> None:
        self.db = db
        self._products: Dict[str, Product] = {}  # Fallback for in-memory mode

    def _slugify(self, text: str) -> str:
        """Generate URL-friendly slug from text."""
        text = text.lower().strip()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[-\s]+', '-', text)
        return text

    def _map_product(self, data: Dict[str, Any]) -> Product:
        """Map Supabase row to Product dataclass."""
        return Product(
            id=data['id'],
            name=data['name'],
            base_price=int(data.get('price_low', 0)),
            created_at=datetime.fromisoformat(data['created_at']) if isinstance(data['created_at'], str) else data['created_at'],
            updated_at=datetime.fromisoformat(data['updated_at']) if isinstance(data['updated_at'], str) else data['updated_at'],
            is_sambatan_enabled=data.get('sambatan_enabled', False),
            sambatan_total_slots=data.get('sambatan_total_slots'),
            sambatan_deadline=datetime.fromisoformat(data['sambatan_deadline']) if data.get('sambatan_deadline') and isinstance(data['sambatan_deadline'], str) else data.get('sambatan_deadline'),
        )

    def create_product(
        self,
        *,
        name: str,
        base_price: int,
        brand_id: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Product:
        if base_price <= 0:
            logger.warning(f"Product creation failed: invalid price {base_price}")
            raise ProductError("Harga dasar produk harus lebih dari 0 (minimal Rp 1).")

        logger.info(f"Creating product: {name} with price {base_price}")
        now = datetime.now(UTC)

        if self.db:
            # Use Supabase
            slug = self._slugify(name)
            product_data = {
                'name': name.strip(),
                'slug': slug,
                'description': description or '',
                'price_low': base_price,
                'status': 'draft',
                'is_active': False,
                'marketplace_enabled': False,
                'sambatan_enabled': False,
            }
            if brand_id:
                product_data['brand_id'] = brand_id

            result = self.db.table('products').insert(product_data).execute()
            return self._map_product(result.data[0])
        else:
            # Fallback to in-memory
            product_id = secrets.token_urlsafe(8)
            product = Product(
                id=product_id,
                name=name.strip(),
                base_price=base_price,
                created_at=now,
                updated_at=now,
            )
            self._products[product_id] = product
            return product

    def toggle_sambatan(
        self,
        *,
        product_id: str,
        enabled: bool,
        total_slots: Optional[int] = None,
        deadline: Optional[datetime] = None,
    ) -> Product:
        product = self.get_product(product_id)

        if enabled:
            if total_slots is None or deadline is None:
                raise ProductError("Total slot dan deadline wajib saat mengaktifkan Sambatan.")
            product.enable_sambatan(total_slots=total_slots, deadline=deadline)

            if self.db:
                # Update in Supabase
                update_data = {
                    'sambatan_enabled': True,
                    'updated_at': datetime.now(UTC).isoformat()
                }
                self.db.table('products').update(update_data).eq('id', product_id).execute()
        else:
            product.disable_sambatan()

            if self.db:
                # Update in Supabase
                update_data = {
                    'sambatan_enabled': False,
                    'updated_at': datetime.now(UTC).isoformat()
                }
                self.db.table('products').update(update_data).eq('id', product_id).execute()

        return product

    def get_product(self, product_id: str) -> Product:
        if self.db:
            # Use Supabase
            result = self.db.table('products').select('*').eq('id', product_id).execute()
            if not result.data:
                raise ProductNotFound("Produk tidak ditemukan.")
            return self._map_product(result.data[0])
        else:
            # Fallback to in-memory
            try:
                return self._products[product_id]
            except KeyError as exc:
                raise ProductNotFound("Produk tidak ditemukan.") from exc

    def list_products(self) -> Iterable[Product]:
        if self.db:
            # Use Supabase
            result = self.db.table('products').select('*').order('created_at', desc=True).execute()
            return [self._map_product(row) for row in result.data]
        else:
            # Fallback to in-memory
            return self._products.values()

    def search_products(
        self,
        query: Optional[str] = None,
        marketplace_only: bool = True,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Search products with filters."""
        if not self.db:
            # Fallback to listing all products
            return [
                {
                    'id': p.id,
                    'name': p.name,
                    'base_price': p.base_price,
                    'created_at': p.created_at.isoformat(),
                }
                for p in self._products.values()
            ]

        # Build Supabase query
        db_query = self.db.table('products').select('*')

        if marketplace_only:
            db_query = db_query.eq('marketplace_enabled', True)

        if query:
            # Simple text search
            db_query = db_query.or_(
                f"name.ilike.%{query}%,"
                f"description.ilike.%{query}%"
            )

        result = db_query.limit(limit).execute()
        return result.data

    def enable_marketplace(
        self,
        product_id: str,
        list_price: float,
        stock_on_hand: int
    ) -> None:
        """Enable a product for marketplace sales."""
        if not self.db:
            raise ProductError("Marketplace features require Supabase connection")

        # Update product
        self.db.table('products').update({
            'marketplace_enabled': True,
            'is_active': True,
            'status': 'active'
        }).eq('id', product_id).execute()

        # Create or update marketplace listing
        listing_data = {
            'product_id': product_id,
            'status': 'published',
            'list_price': list_price,
            'stock_on_hand': stock_on_hand,
            'stock_reserved': 0,
            'published_at': datetime.now(UTC).isoformat()
        }

        # Try to upsert (insert or update)
        existing = self.db.table('marketplace_listings').select('id').eq('product_id', product_id).execute()
        if existing.data:
            self.db.table('marketplace_listings').update(listing_data).eq('product_id', product_id).execute()
        else:
            self.db.table('marketplace_listings').insert(listing_data).execute()


product_service = ProductService()
"""Singleton product service instance shared across the app."""

