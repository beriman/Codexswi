"""Shopping cart service using session storage."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import json


@dataclass
class CartItem:
    """Represents an item in the shopping cart."""
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


cart_service = CartService()
"""Singleton cart service instance."""
