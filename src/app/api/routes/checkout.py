"""Checkout flow routes for marketplace orders."""

import logging
from typing import Optional
from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse

from app.core.rate_limit import limiter, RATE_LIMITS
from app.core.dependencies import get_db
from app.services.cart import cart_service
from app.services.orders import OrderService, OrderError, InsufficientStock

try:
    from supabase import Client
except ImportError:
    Client = None  # type: ignore

logger = logging.getLogger(__name__)

router = APIRouter(tags=["checkout"])


@router.get("/checkout", response_class=HTMLResponse)
async def checkout_page(request: Request):
    """Display checkout page with shipping address form."""
    
    # Check if cart has items
    cart = cart_service.get_cart(request.session)
    if not cart['items']:
        return RedirectResponse(url="/cart", status_code=303)
    
    # Get current user (from session)
    user = request.session.get('user')
    if not user:
        # For MVP, we'll allow guest checkout
        # In production, redirect to login
        user = None
    
    templates = request.app.state.templates
    
    context = {
        "request": request,
        "title": "Checkout - Sensasiwangi.id",
        "cart": cart,
        "user": user
    }
    
    return templates.TemplateResponse("checkout.html", context)


@router.post("/api/checkout/create-order")
@limiter.limit(RATE_LIMITS["checkout"])
async def create_order(
    request: Request,
    recipient_name: str = Form(...),
    phone_number: str = Form(...),
    province_name: str = Form(...),
    city_name: str = Form(...),
    subdistrict_name: Optional[str] = Form(None),
    postal_code: Optional[str] = Form(None),
    address_line: str = Form(...),
    additional_info: Optional[str] = Form(None),
    db: Client = Depends(get_db)
):
    """Create order from cart and redirect to confirmation."""
    
    # Get cart items
    cart = cart_service.get_cart(request.session)
    if not cart['items']:
        raise HTTPException(status_code=400, detail="Keranjang kosong")
    
    # Get or create customer_id (for MVP, use session or create guest)
    user = request.session.get('user')
    customer_id = user.get('id') if user else None
    
    # If no customer_id, we need to handle guest checkout
    if not customer_id:
        # For MVP, you might want to create a guest user or require login
        raise HTTPException(
            status_code=401, 
            detail="Silakan login terlebih dahulu untuk melanjutkan checkout"
        )
    
    # Prepare order items
    order_items = []
    for item in cart['items']:
        order_items.append({
            'product_id': item['product_id'],
            'product_name': item['product_name'],
            'brand_name': item.get('brand_name', ''),
            'unit_price': item['unit_price'],
            'quantity': item['quantity'],
            'sku': item.get('sku'),
            'variant_id': item.get('variant_id')
        })
    
    # Prepare shipping address
    shipping_address = {
        'recipient_name': recipient_name,
        'phone_number': phone_number,
        'province_name': province_name,
        'city_name': city_name,
        'subdistrict_name': subdistrict_name,
        'postal_code': postal_code,
        'address_line': address_line,
        'additional_info': additional_info
    }
    
    # Create order
    try:
        order_service = OrderService(db)
        order = await order_service.create_order(
            customer_id=customer_id,
            items=order_items,
            shipping_address=shipping_address,
            channel='marketplace'
        )
        
        # Clear cart after successful order creation
        cart_service.clear_cart(request.session)
        
        logger.info(f"Order created successfully: {order['order_number']}")
        
        # Redirect to order confirmation page
        return RedirectResponse(
            url=f"/order/confirmation/{order['id']}", 
            status_code=303
        )
        
    except InsufficientStock as e:
        logger.warning(f"Checkout failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except OrderError as e:
        logger.error(f"Order creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error during checkout: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="Terjadi kesalahan saat membuat pesanan. Silakan coba lagi."
        )


@router.get("/order/confirmation/{order_id}", response_class=HTMLResponse)
async def order_confirmation(
    request: Request,
    order_id: str,
    db: Client = Depends(get_db)
):
    """Display order confirmation page after successful checkout."""
    
    order_service = OrderService(db)
    order = await order_service.get_order(order_id)
    
    if not order:
        raise HTTPException(status_code=404, detail="Pesanan tidak ditemukan")
    
    # Verify that the order belongs to the current user
    user = request.session.get('user')
    if user and order.get('customer_id') != user.get('id'):
        raise HTTPException(status_code=403, detail="Akses ditolak")
    
    templates = request.app.state.templates
    
    context = {
        "request": request,
        "title": f"Konfirmasi Pesanan - {order['order_number']}",
        "order": order
    }
    
    return templates.TemplateResponse("order_confirmation.html", context)


@router.get("/order/{order_id}", response_class=HTMLResponse)
async def order_details(
    request: Request,
    order_id: str,
    db: Client = Depends(get_db)
):
    """Display order details and tracking page."""
    
    order_service = OrderService(db)
    order = await order_service.get_order(order_id)
    
    if not order:
        raise HTTPException(status_code=404, detail="Pesanan tidak ditemukan")
    
    # Verify that the order belongs to the current user
    user = request.session.get('user')
    if user and order.get('customer_id') != user.get('id'):
        raise HTTPException(status_code=403, detail="Akses ditolak")
    
    templates = request.app.state.templates
    
    context = {
        "request": request,
        "title": f"Detail Pesanan - {order['order_number']}",
        "order": order
    }
    
    return templates.TemplateResponse("order_details.html", context)


@router.get("/orders", response_class=HTMLResponse)
async def my_orders(
    request: Request,
    db: Client = Depends(get_db)
):
    """Display user's order history."""
    
    user = request.session.get('user')
    if not user:
        return RedirectResponse(url="/auth/login?next=/orders", status_code=303)
    
    order_service = OrderService(db)
    orders = await order_service.list_customer_orders(customer_id=user['id'])
    
    templates = request.app.state.templates
    
    context = {
        "request": request,
        "title": "Pesanan Saya",
        "orders": orders
    }
    
    return templates.TemplateResponse("my_orders.html", context)
