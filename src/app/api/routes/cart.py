"""Shopping cart routes."""

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

from app.services.cart import cart_service

router = APIRouter(tags=["cart"])


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
        "request": request,
        "title": "Keranjang Belanja",
        "cart": cart
    }

    return templates.TemplateResponse("cart.html", context)


@router.get("/api/cart")
async def get_cart_data(request: Request):
    """Get cart data as JSON."""

    cart = cart_service.get_cart(request.session)
    return JSONResponse(cart)


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


@router.post("/api/cart/clear")
async def clear_cart(request: Request):
    """Clear all items from cart."""

    cart_service.clear_cart(request.session)

    return {"status": "success", "message": "Keranjang telah dikosongkan"}
