"""In-memory product catalog service with Sambatan toggles."""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Iterable, Optional


class ProductError(Exception):
    """Base error class for product operations."""

    status_code: int = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ProductNotFound(ProductError):
    """Raised when attempting to access a missing product."""

    status_code = 404


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
        if deadline <= datetime.utcnow():
            raise ProductError("Deadline sambatan harus berada di masa depan.")

        self.is_sambatan_enabled = True
        self.sambatan_total_slots = total_slots
        self.sambatan_deadline = deadline
        self.updated_at = datetime.utcnow()

    def disable_sambatan(self) -> None:
        self.is_sambatan_enabled = False
        self.sambatan_total_slots = None
        self.sambatan_deadline = None
        self.updated_at = datetime.utcnow()


class ProductService:
    """Minimal catalog service to support Sambatan campaign planning."""

    def __init__(self) -> None:
        self._products: Dict[str, Product] = {}

    def create_product(self, *, name: str, base_price: int) -> Product:
        if base_price <= 0:
            raise ProductError("Harga dasar produk harus lebih dari 0.")

        product_id = secrets.token_urlsafe(8)
        now = datetime.utcnow()
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
        else:
            product.disable_sambatan()
        return product

    def get_product(self, product_id: str) -> Product:
        try:
            return self._products[product_id]
        except KeyError as exc:
            raise ProductNotFound("Produk tidak ditemukan.") from exc

    def list_products(self) -> Iterable[Product]:
        return self._products.values()


product_service = ProductService()
"""Singleton product service instance shared across the app."""

