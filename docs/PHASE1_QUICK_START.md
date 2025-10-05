# Phase 1 Quick Start Guide

Get up and running with Phase 1 implementation in 5 minutes! 🚀

---

## Prerequisites

- Python 3.10+
- Supabase account (free tier is fine)
- pip or poetry for package management

---

## 1. Install Dependencies

```bash
cd /workspace
pip install -r requirements.txt
```

**Key new dependency:**
- `supabase>=2.3.0` - Python client for Supabase

---

## 2. Setup Supabase

### Option A: Create New Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Create new project
3. Note down:
   - Project URL (e.g., `https://xxxxx.supabase.co`)
   - Service role key (Settings → API → service_role)

### Option B: Use Existing Project

If you already have a Supabase project, just get your credentials from the dashboard.

---

## 3. Run Database Migrations

Execute these SQL files in your Supabase SQL Editor:

1. `supabase/migrations/0001_initial_schema.sql`
2. `supabase/migrations/0002_profile_social_graph.sql`
3. `supabase/migrations/0003_nusantarum_schema.sql`

Or use Supabase CLI:

```bash
supabase db push
```

**Tables that will be created:**
- `auth_accounts`, `onboarding_registrations` (Auth)
- `products`, `marketplace_listings` (Products)
- `orders`, `order_items`, `order_shipping_addresses` (Orders)
- And more...

---

## 4. Configure Environment

Create `.env` file in project root:

```bash
# Supabase Configuration
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...

# Session Secret (generate with: python -c "import secrets; print(secrets.token_urlsafe(32))")
SESSION_SECRET=your-32-character-secret-here

# RajaOngkir (optional, for Phase 2)
# RAJAONGKIR_API_KEY=your-api-key
```

**Generate session secret:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 5. Start the Application

```bash
cd /workspace
python -m uvicorn app.main:app --reload
```

Or:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
INFO:     Supabase client initialized successfully
```

---

## 6. Verify Setup

### Check Application Health

Open browser: http://localhost:8000

You should see the homepage.

### Check Supabase Connection

Look for this log message:
```
INFO: Supabase client initialized successfully
```

If you see this instead:
```
WARNING: Supabase client not available - using fallback storage
```

Then check your `.env` file and make sure `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are set correctly.

---

## 7. Test Basic Flows

### Test 1: User Registration

**Via API:**
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "full_name": "Test User",
    "password": "Test1234"
  }'
```

**Expected response:**
```json
{
  "registration_id": "...",
  "account_id": "...",
  "email": "test@example.com",
  "full_name": "Test User",
  "status": "pending_verification",
  "message": "Registrasi berhasil. Cek email Anda untuk tautan verifikasi."
}
```

**Verify in Supabase:**
- Check `auth_accounts` table - should see new user
- Check `onboarding_registrations` table - should see verification record

### Test 2: Create Product

**Via Python console:**
```python
from app.services.products import ProductService
from app.core.supabase import get_supabase_client

db = get_supabase_client()
product_service = ProductService(db=db)

product = product_service.create_product(
    name="Rimba Embun Signature",
    base_price=420000,
    description="Parfum dengan aroma hutan tropis Indonesia"
)

print(f"Product created: {product.id}")
```

**Verify in Supabase:**
- Check `products` table - should see new product

### Test 3: Shopping Cart

**Add to cart:**
```bash
curl -X POST http://localhost:8000/api/cart/add \
  -F "product_id=prod-123" \
  -F "product_name=Rimba Embun" \
  -F "brand_name=Saung Aroma" \
  -F "unit_price=420000" \
  -F "quantity=1"
```

**View cart:**
```bash
curl http://localhost:8000/api/cart
```

**Expected response:**
```json
{
  "items": [
    {
      "product_id": "prod-123",
      "product_name": "Rimba Embun",
      "brand_name": "Saung Aroma",
      "unit_price": 420000,
      "quantity": 1
    }
  ],
  "item_count": 1,
  "subtotal": 420000,
  "shipping": 0,
  "total": 420000
}
```

### Test 4: Create Order

**Via Python console:**
```python
from app.services.orders import OrderService
from app.core.supabase import get_supabase_client
import asyncio

db = get_supabase_client()
order_service = OrderService(db=db)

order = asyncio.run(order_service.create_order(
    customer_id='user-123',
    items=[{
        'product_id': 'prod-123',
        'product_name': 'Rimba Embun',
        'unit_price': 420000,
        'quantity': 1
    }],
    shipping_address={
        'recipient_name': 'John Doe',
        'phone': '08123456789',
        'street_address': 'Jl. Example No. 123',
        'city': 'Jakarta',
        'province': 'DKI Jakarta',
        'postal_code': '12345'
    }
))

print(f"Order created: {order['order_number']}")
```

**Verify in Supabase:**
- Check `orders` table
- Check `order_items` table
- Check `order_shipping_addresses` table
- Check `marketplace_listings` - stock_reserved should increment

---

## 8. Explore the API

### Interactive API Docs

Visit: http://localhost:8000/docs

FastAPI automatically generates interactive API documentation where you can:
- See all available endpoints
- Test endpoints directly in the browser
- View request/response schemas

### Alternative API Docs

Visit: http://localhost:8000/redoc

ReDoc provides an alternative documentation interface.

---

## 9. Development Workflow

### Hot Reload

The `--reload` flag enables hot reload. Any code changes will automatically restart the server.

### Check Logs

All logs appear in the terminal. Watch for:
- `INFO` - Normal operations
- `WARNING` - Fallback modes or missing configs
- `ERROR` - Problems that need attention

### Database Changes

After modifying the database:
1. Update migration files
2. Run migrations in Supabase
3. Update service code if schema changed

---

## 10. Troubleshooting

### Problem: "Supabase client not available"

**Solution:**
- Check `.env` file exists and has correct values
- Verify `SUPABASE_URL` is in format: `https://xxxxx.supabase.co`
- Verify `SUPABASE_SERVICE_ROLE_KEY` starts with `eyJhbGc...`
- Restart the application

### Problem: "Module not found" errors

**Solution:**
```bash
pip install -r requirements.txt
```

### Problem: Database errors

**Solution:**
- Check Supabase dashboard - is the project active?
- Verify migrations were run
- Check table names match exactly (case-sensitive)
- Look at Supabase logs in dashboard

### Problem: Import errors

**Solution:**
```bash
export PYTHONPATH=/workspace/src:$PYTHONPATH
```

Or run from project root:
```bash
cd /workspace
python -m uvicorn app.main:app --reload
```

### Problem: Port already in use

**Solution:**
```bash
# Use different port
uvicorn app.main:app --reload --port 8001

# Or kill process on port 8000
lsof -ti:8000 | xargs kill -9
```

---

## 11. Testing Without Supabase

For testing/development without Supabase:

1. Don't set `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`
2. Application will use in-memory storage
3. Data will be lost on restart
4. Good for unit tests and quick prototyping

**Set minimal env:**
```bash
SESSION_SECRET=development-secret-key-32-chars-min
```

---

## 12. Next Steps

Once everything is working:

1. ✅ Complete verification checklist: `docs/PHASE1_VERIFICATION_CHECKLIST.md`
2. 📚 Read implementation summary: `docs/PHASE1_IMPLEMENTATION_SUMMARY.md`
3. 🚀 Start Phase 2: Checkout flow and RajaOngkir integration
4. 🧪 Write integration tests
5. 🎨 Customize templates and styles

---

## Common Commands Cheat Sheet

```bash
# Start development server
uvicorn app.main:app --reload

# Start with specific host/port
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Check code syntax
python -m py_compile src/app/**/*.py

# Generate secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Format code
black src/app
isort src/app

# Type check
mypy src/app
```

---

## Project Structure

```
/workspace/
├── src/app/
│   ├── core/
│   │   ├── supabase.py          ← NEW: Supabase client
│   │   ├── dependencies.py      ← NEW: DI helpers
│   │   ├── application.py       ← MODIFIED: Startup event
│   │   └── config.py
│   ├── services/
│   │   ├── auth.py              ← MODIFIED: Supabase integration
│   │   ├── products.py          ← MODIFIED: Supabase integration
│   │   ├── orders.py            ← NEW: Order management
│   │   ├── cart.py              ← NEW: Cart management
│   │   └── ...
│   ├── api/routes/
│   │   ├── auth.py              ← MODIFIED: DI pattern
│   │   ├── cart.py              ← NEW: Cart routes
│   │   └── ...
│   └── web/templates/
│       ├── cart.html            ← NEW: Cart page
│       └── ...
├── docs/
│   ├── PHASE1_IMPLEMENTATION_SUMMARY.md    ← Implementation details
│   ├── PHASE1_VERIFICATION_CHECKLIST.md    ← Testing guide
│   └── PHASE1_QUICK_START.md              ← This file
├── supabase/migrations/
│   ├── 0001_initial_schema.sql
│   ├── 0002_profile_social_graph.sql
│   └── 0003_nusantarum_schema.sql
├── requirements.txt             ← MODIFIED: Added supabase
└── .env                        ← CREATE THIS: Your config
```

---

## Support

- 📖 Documentation: `docs/` directory
- 🐛 Issues: Check GitHub issues
- 💬 Questions: Team chat or email

---

## Success! 🎉

If you've completed all steps and tests pass, you're ready to:
- Build features on top of this foundation
- Deploy to production
- Start Phase 2 implementation

**Happy coding!** 💻✨

---

**Document Owner**: Development Team  
**Last Updated**: 2025-10-05
