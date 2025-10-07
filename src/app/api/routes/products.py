"""FastAPI endpoints for product management."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.services.products import ProductError, ProductService, product_service


router = APIRouter(prefix="/api/products", tags=["products"])


class ProductCreateRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=200)
    base_price: int = Field(..., ge=1, description="Harga dasar dalam Rupiah")
    category_id: int = Field(..., ge=1, le=4, description="Category ID (1-4)")
    marketplace_enabled: bool = Field(True, description="Enable for regular marketplace")
    sambatan_enabled: bool = Field(False, description="Enable for Sambatan group-buy")
    description: Optional[str] = Field(None, max_length=2000)
    brand_id: Optional[str] = None


class ProductResponse(BaseModel):
    id: str
    name: str
    base_price: int
    is_sambatan_enabled: bool
    created_at: str
    updated_at: str


def get_product_service() -> ProductService:
    return product_service


def _serialize_product(product: Any) -> Dict[str, Any]:
    return {
        "id": product.id,
        "name": product.name,
        "base_price": product.base_price,
        "is_sambatan_enabled": product.is_sambatan_enabled,
        "created_at": product.created_at.isoformat(),
        "updated_at": product.updated_at.isoformat(),
    }


def _handle_error(exc: ProductError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreateRequest,
    service: ProductService = Depends(get_product_service),
) -> ProductResponse:
    """Create a new product with category and type settings."""
    try:
        # Create base product through service (service signature doesn't include category/types)
        product = service.create_product(
            name=payload.name,
            base_price=payload.base_price,
            description=payload.description,
            brand_id=payload.brand_id,
        )
        
        # Update product with marketplace/sambatan flags directly in database
        if service.db:
            update_data = {
                'marketplace_enabled': payload.marketplace_enabled,
                'sambatan_enabled': payload.sambatan_enabled,
            }
            service.db.table('products').update(update_data).eq('id', product.id).execute()
            
            # Create category link
            category_link = {
                'product_id': product.id,
                'category_id': payload.category_id
            }
            service.db.table('product_category_links').insert(category_link).execute()
        
        return ProductResponse(**_serialize_product(product))
    except ProductError as exc:
        _handle_error(exc)
        raise


@router.get("/", response_model=List[ProductResponse])
def list_products(service: ProductService = Depends(get_product_service)) -> List[ProductResponse]:
    """List all products."""
    products = service.list_products()
    return [ProductResponse(**_serialize_product(p)) for p in products]


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: str, service: ProductService = Depends(get_product_service)) -> ProductResponse:
    """Get a single product by ID."""
    try:
        product = service.get_product(product_id)
        return ProductResponse(**_serialize_product(product))
    except ProductError as exc:
        _handle_error(exc)
        raise
