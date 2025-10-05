"""Rate limiting configuration for API endpoints."""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Create limiter instance
limiter = Limiter(key_func=get_remote_address)

# Rate limit configurations
RATE_LIMITS = {
    "auth_register": "5/hour",      # 5 registrations per hour per IP
    "auth_login": "10/minute",       # 10 login attempts per minute per IP
    "auth_verify": "20/hour",        # 20 verification attempts per hour per IP
    "cart_add": "30/minute",         # 30 cart additions per minute per IP
    "checkout": "10/hour",           # 10 checkouts per hour per IP
    "order_create": "10/hour",       # 10 orders per hour per IP
    "default": "60/minute",          # Default: 60 requests per minute per IP
}
