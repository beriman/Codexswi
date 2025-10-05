# Task Breakdown - Implementasi Bertahap

**Tanggal**: 2025-10-05  
**Tujuan**: Panduan step-by-step untuk implementasi arsitektur sesuai PRD

---

## 📋 Overview

Dokumen ini memecah implementasi menjadi **31 task kecil** yang bisa dikerjakan secara bertahap. Setiap task memiliki:
- ✅ Checklist status
- ⏱️ Estimasi waktu
- 📁 File yang perlu dibuat/edit
- 🧪 Cara testing

---

## 🎯 TIER 1: FOUNDATION (Week 1)

### ✅ Task 1-4: Supabase Client Setup (2 hours) - COMPLETED

#### ✅ Task 1.1: Create Supabase Client Factory
- **File**: `src/app/core/supabase.py` ✅
- **Status**: COMPLETED
- **What**: Factory functions untuk Supabase client
- **Testing**: `python -c "from app.core.supabase import get_supabase_client; print('OK')"`

#### ✅ Task 1.2: Add Dependencies
- **File**: `requirements.txt` ✅
- **Status**: COMPLETED
- **What**: Add `supabase>=2.3`
- **Testing**: `pip install -r requirements.txt`

#### ✅ Task 1.3: Create DI Helpers
- **File**: `src/app/core/dependencies.py` ✅
- **Status**: COMPLETED
- **What**: FastAPI dependency injection helpers
- **Testing**: Import test

#### ✅ Task 1.4: Update Application Startup
- **File**: `src/app/core/application.py` ✅
- **Status**: COMPLETED
- **What**: Initialize Supabase on startup
- **Testing**: `uvicorn app.main:app --reload` → check logs

---

### 🚧 Task 5-9: Auth Service Refactor (8 hours) - 75% DONE

#### ✅ Task 5.1: Create Auth Service
- **File**: `src/app/services/auth_supabase.py` ✅
- **Status**: COMPLETED
- **Time**: 4 hours
- **What**: Rewrite auth dengan Supabase
- **Testing**: See test file

#### ✅ Task 5.2: Write Tests
- **File**: `tests/test_auth_supabase.py` ✅
- **Status**: COMPLETED
- **Time**: 2 hours
- **What**: Unit tests untuk auth service
- **Testing**: `pytest tests/test_auth_supabase.py -v`

#### 🔲 Task 5.3: Update Auth Routes
- **File**: `src/app/api/routes/auth.py`
- **Status**: TODO
- **Time**: 1 hour
- **What**: Gunakan `auth_supabase` di routes
- **Code**:
```python
from app.services.auth_supabase import get_auth_service
from app.core.dependencies import get_db

@router.post("/api/auth/register")
async def register_user(
    payload: RegisterRequest,
    db = Depends(get_db)
):
    auth_service = get_auth_service(db)
    result = auth_service.register(...)
    
    # Create session
    session_token = auth_service.create_session(result.id)
    request.session['token'] = session_token
    request.session['user'] = {
        'id': result.id,
        'email': result.email,
        'full_name': result.full_name
    }
    
    return {"status": "success"}
```

#### 🔲 Task 5.4: Test End-to-End
- **Status**: TODO
- **Time**: 1 hour
- **What**: Manual testing register → verify → login
- **Steps**:
  1. Start app: `uvicorn app.main:app --reload`
  2. Navigate to `/auth`
  3. Register new user
  4. Check email for verification link
  5. Click link → should verify
  6. Login with credentials
  7. Check session persists

---

### 🔲 Task 10-16: Product Service Refactor (12 hours)

#### 🔲 Task 10.1: Create Product Service
- **File**: `src/app/services/products_supabase.py`
- **Status**: TODO
- **Time**: 3 hours
- **What**: Basic CRUD dengan products table
- **Key Methods**:
  - `create_product()`
  - `get_product(product_id)`
  - `list_products(filters)`
  - `update_product(product_id, data)`
  - `delete_product(product_id)`

#### 🔲 Task 10.2: Marketplace Listing Integration
- **Status**: TODO
- **Time**: 2 hours
- **What**: Link dengan `marketplace_listings` table
- **Key Methods**:
  - `enable_marketplace_listing(product_id, price, stock)`
  - `update_stock(product_id, quantity)`
  - `disable_marketplace_listing(product_id)`

#### 🔲 Task 10.3: Search & Filter
- **Status**: TODO
- **Time**: 2 hours
- **What**: Full-text search dan filter
- **Key Methods**:
  - `search_products(query, category, brand, price_range)`
  - `filter_by_category(category_slug)`
  - `filter_by_brand(brand_id)`

#### 🔲 Task 10.4: Image Upload
- **Status**: TODO
- **Time**: 2 hours
- **What**: Upload ke Supabase Storage
- **Key Methods**:
  - `upload_product_image(product_id, file)`
  - `delete_product_image(image_id)`
  - `set_primary_image(product_id, image_id)`

#### 🔲 Task 10.5: Variants Management
- **Status**: TODO
- **Time**: 1 hour
- **What**: Product variants (size, volume)
- **Key Methods**:
  - `add_variant(product_id, data)`
  - `update_variant(variant_id, data)`
  - `delete_variant(variant_id)`

#### 🔲 Task 10.6: Update Routes
- **File**: Update `src/app/api/routes/root.py` atau create new
- **Status**: TODO
- **Time**: 1 hour

#### 🔲 Task 10.7: Write Tests
- **File**: `tests/test_products_supabase.py`
- **Status**: TODO
- **Time**: 1 hour

---

## 🎯 TIER 2: SHOPPING FLOW (Week 2)

### 🔲 Task 17-19: Cart Management (6 hours)

#### 🔲 Task 17.1: Create Cart Service
- **File**: `src/app/services/cart.py`
- **Status**: TODO
- **Time**: 2 hours
- **What**: Session-based cart
- **Key Methods**:
  - `add_item(session, product_id, quantity)`
  - `remove_item(session, product_id)`
  - `update_quantity(session, product_id, quantity)`
  - `get_cart(session)`
  - `clear_cart(session)`

#### 🔲 Task 17.2: Create Cart Routes
- **File**: `src/app/api/routes/cart.py`
- **Status**: TODO
- **Time**: 2 hours
- **Routes**:
  - `POST /api/cart/add`
  - `POST /api/cart/remove`
  - `POST /api/cart/update`
  - `GET /cart` (render page)

#### 🔲 Task 17.3: Create Cart Template
- **File**: `src/app/web/templates/cart.html`
- **Status**: TODO
- **Time**: 2 hours
- **What**: Shopping cart UI dengan glassmorphism

---

### 🔲 Task 20-28: Order Service (16 hours)

#### 🔲 Task 20.1: Create Database Functions
- **File**: `supabase/migrations/0004_order_helpers.sql`
- **Status**: TODO
- **Time**: 1 hour
- **What**: `reserve_stock()` dan `release_stock()` functions

#### 🔲 Task 20.2: Create Order Service
- **File**: `src/app/services/orders.py`
- **Status**: TODO
- **Time**: 4 hours
- **Key Methods**:
  - `create_order(customer_id, items, shipping_address)`
  - `get_order(order_id)`
  - `list_customer_orders(customer_id)`

#### 🔲 Task 20.3: Order Status Management
- **Status**: TODO
- **Time**: 2 hours
- **Key Methods**:
  - `update_order_status(order_id, new_status, actor_id)`
  - `add_tracking_number(order_id, tracking_number)`
  - Status flow: draft → paid → processing → shipped → completed

#### 🔲 Task 20.4: Inventory Management
- **Status**: TODO
- **Time**: 2 hours
- **Key Methods**:
  - `_reserve_inventory(order_id, items)`
  - `_release_inventory(order_id)` (for cancelled orders)
  - `_log_inventory_adjustment(product_id, adjustment, reason)`

#### 🔲 Task 20.5: Order History
- **Status**: TODO
- **Time**: 1 hour
- **Key Methods**:
  - `get_order_history(customer_id, filters)`
  - `_log_status_change(order_id, status, actor_id, note)`

#### 🔲 Task 20.6: Create Order Routes
- **File**: `src/app/api/routes/orders.py`
- **Status**: TODO
- **Time**: 2 hours
- **Routes**:
  - `POST /api/orders/create`
  - `GET /orders` (history page)
  - `GET /orders/{order_id}` (detail page)
  - `POST /api/orders/{order_id}/status` (admin only)

#### 🔲 Task 20.7: Create Order Templates
- **Files**:
  - `src/app/web/templates/order_confirmation.html`
  - `src/app/web/templates/order_detail.html`
  - `src/app/web/templates/order_history.html`
- **Status**: TODO
- **Time**: 3 hours

#### 🔲 Task 20.8: Write Tests
- **File**: `tests/test_orders.py`
- **Status**: TODO
- **Time**: 1 hour

---

## 🎯 TIER 3: ENHANCEMENTS (Week 3-4)

### 🔲 Task 29-31: Additional Features

#### 🔲 Task 29: RajaOngkir Integration
- **File**: `src/app/services/rajaongkir.py`
- **Status**: TODO
- **Time**: 4 hours
- **What**: Shipping cost calculation
- **Key Methods**:
  - `get_provinces()`
  - `get_cities(province_id)`
  - `calculate_cost(origin, destination, weight, courier)`

#### 🔲 Task 30: Sambatan Scheduler
- **File**: `src/core/scheduler.py`
- **Status**: TODO
- **Time**: 6 hours
- **What**: Background worker untuk Sambatan
- **Key Methods**:
  - `check_deadlines()` - setiap 5 menit
  - `send_reminders()` - daily at 9am
  - `process_refunds()` - untuk failed campaigns

#### 🔲 Task 31: Reporting Enhancement
- **File**: Update `src/app/services/reporting.py`
- **Status**: TODO
- **Time**: 2 hours
- **What**: Real data dari orders table

---

## 📊 Progress Tracking

### Current Status
```
Phase 1: Supabase Setup     [████████████████████] 100% ✅
Phase 2: Auth Service       [███████████████░░░░░]  75% 🚧
Phase 3: Product Service    [░░░░░░░░░░░░░░░░░░░░]   0% ⏸️
Phase 4: Cart Service       [░░░░░░░░░░░░░░░░░░░░]   0% ⏸️
Phase 5: Order Service      [░░░░░░░░░░░░░░░░░░░░]   0% ⏸️
─────────────────────────────────────────────────────
Overall Progress            [████░░░░░░░░░░░░░░░░]  23%
```

### Time Tracking
- **Completed**: 8 hours
- **Remaining**: 36 hours
- **Total**: 44 hours

---

## 🚀 Quick Start Guide

### Setup Supabase (Required)

1. **Create Supabase Project** di https://supabase.com
2. **Set environment variables**:
```bash
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"
```

3. **Run migrations**:
```bash
# Apply existing migrations
psql $SUPABASE_DATABASE_URL < supabase/migrations/0001_initial_schema.sql
psql $SUPABASE_DATABASE_URL < supabase/migrations/0002_profile_social_graph.sql
psql $SUPABASE_DATABASE_URL < supabase/migrations/0003_nusantarum_schema.sql
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run Tests

```bash
# Unit tests (no Supabase needed)
pytest tests/test_auth_supabase.py -v

# Integration tests (needs Supabase)
pytest tests/test_auth_supabase.py -v -m integration
```

### Run Application

```bash
uvicorn app.main:app --reload

# Check logs for:
# ✓ Supabase client initialized successfully
# ✓ Supabase connection healthy
```

---

## 🎯 Recommended Order

### Week 1: Foundation
1. ✅ Setup Supabase Client (Done)
2. 🚧 Finish Auth Service (2h remaining)
3. Start Product Service (12h)

### Week 2: Shopping Flow
4. Finish Product Service
5. Cart Management (6h)
6. Order Service basics (10h)

### Week 3: Complete & Polish
7. Finish Order Service (6h)
8. Templates (cart, orders) (5h)
9. Testing & bug fixes

### Week 4: Enhancements
10. RajaOngkir integration
11. Sambatan scheduler
12. Reporting improvements

---

## 💡 Tips

### Development Workflow
1. **Work on one task at a time** - Don't jump around
2. **Test immediately** - Don't accumulate untested code
3. **Commit frequently** - Small commits are better
4. **Document as you go** - Update this file

### Testing Strategy
1. **Unit tests first** - Mock Supabase
2. **Integration tests second** - Real Supabase (staging)
3. **Manual testing last** - Full flow

### Common Pitfalls
1. ❌ **Don't skip tests** - They save time later
2. ❌ **Don't hardcode credentials** - Use environment variables
3. ❌ **Don't commit sensitive data** - Add to .gitignore
4. ❌ **Don't break existing features** - Keep old code until confident

---

## 📞 Need Help?

### Debugging Supabase
```python
# Check connection
from app.core.supabase import check_supabase_connection
print(check_supabase_connection())

# Get client
from app.core.supabase import get_supabase_client
client = get_supabase_client()
if client:
    result = client.table('product_categories').select('*').execute()
    print(result.data)
```

### Common Errors

**Error**: `SupabaseNotConfigured`
- **Fix**: Set `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` env vars

**Error**: `HTTPException 503`
- **Fix**: Check Supabase connection, verify credentials

**Error**: Import errors
- **Fix**: Run `pip install -r requirements.txt`

---

## 📚 Reference Documents

- `docs/architecture-prd-gap-analysis.md` - Original analysis
- `docs/architecture-action-plan.md` - Detailed implementation guide
- `docs/implementation-progress.md` - Current progress tracking
- `PRD_MVP.md` - Product requirements

---

**Last Updated**: 2025-10-05  
**Maintainer**: Development Team  
**Status**: Living document - update as you progress
