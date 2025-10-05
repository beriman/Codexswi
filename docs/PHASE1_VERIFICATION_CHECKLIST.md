# Phase 1 Verification Checklist

Use this checklist to verify that Phase 1 implementation is working correctly.

---

## 🔧 Environment Setup

- [ ] Create `.env` file in project root
- [ ] Add Supabase configuration:
  ```bash
  SUPABASE_URL=https://xxxxx.supabase.co
  SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...
  SESSION_SECRET=<generate-32-char-secret>
  ```
- [ ] Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```

---

## 🗄️ Database Setup

- [ ] Run Supabase migrations:
  ```bash
  supabase db push
  ```
  Or manually execute:
  - `supabase/migrations/0001_initial_schema.sql`
  - `supabase/migrations/0002_profile_social_graph.sql`
  - `supabase/migrations/0003_nusantarum_schema.sql`

- [ ] Verify tables exist in Supabase dashboard:
  - [ ] `auth_accounts`
  - [ ] `onboarding_registrations`
  - [ ] `products`
  - [ ] `marketplace_listings`
  - [ ] `orders`
  - [ ] `order_items`
  - [ ] `order_shipping_addresses`
  - [ ] `order_status_history`
  - [ ] `marketplace_inventory_adjustments`

---

## 🚀 Application Startup

- [ ] Start the application:
  ```bash
  python -m uvicorn app.main:app --reload
  # or
  uvicorn app.main:app --reload
  ```

- [ ] Check logs for successful Supabase initialization:
  ```
  INFO: Supabase client initialized successfully
  ```

- [ ] If you see warning instead (expected if no env vars):
  ```
  WARNING: Supabase client not available - using fallback storage
  ```

- [ ] Access application at: http://localhost:8000

---

## ✅ Functional Testing

### 1. Auth Service

#### Registration Flow
- [ ] Navigate to registration page
- [ ] Fill in form:
  - Email: test@example.com
  - Full Name: Test User
  - Password: Test1234
- [ ] Submit registration
- [ ] Check Supabase `auth_accounts` table - should see new record
- [ ] Check `onboarding_registrations` table - should see verification token
- [ ] Status should be `pending_verification`

#### Verification Flow
- [ ] Get verification token from database
- [ ] Navigate to: `/api/auth/verify` with token
- [ ] Check `auth_accounts` - status should change to `active`
- [ ] Check `onboarding_registrations` - status should be `email_verified`

#### Login Flow
- [ ] Navigate to login page
- [ ] Enter credentials
- [ ] Submit login
- [ ] Should receive success response
- [ ] Check `auth_accounts` - `last_login_at` should be updated
- [ ] Check session storage - user should be in session

### 2. Products Service

#### Create Product
- [ ] Use API or admin interface to create product
- [ ] Check `products` table - should see new record
- [ ] Verify fields:
  - [ ] name
  - [ ] slug (auto-generated)
  - [ ] price_low
  - [ ] status = 'draft'
  - [ ] marketplace_enabled = false

#### Enable Marketplace
- [ ] Call `enable_marketplace()` method or API endpoint
- [ ] Check `products` table:
  - [ ] marketplace_enabled = true
  - [ ] status = 'active'
- [ ] Check `marketplace_listings` table - should see new listing
- [ ] Verify listing fields:
  - [ ] list_price
  - [ ] stock_on_hand
  - [ ] stock_reserved = 0
  - [ ] status = 'published'

#### Search Products
- [ ] Call search API with query
- [ ] Verify results filtered correctly
- [ ] Test marketplace_only filter
- [ ] Test text search in name/description

### 3. Cart Service

#### Add to Cart
- [ ] Navigate to a product page
- [ ] Click "Add to Cart"
- [ ] POST to `/api/cart/add` with:
  ```json
  {
    "product_id": "prod-123",
    "product_name": "Test Product",
    "brand_name": "Test Brand",
    "unit_price": 100000,
    "quantity": 2
  }
  ```
- [ ] Check session - should contain cart data
- [ ] Navigate to `/cart` - should see item

#### Update Quantity
- [ ] In cart page, change quantity
- [ ] Submit update
- [ ] Verify cart total recalculated
- [ ] Check session updated

#### Remove Item
- [ ] Click "Remove" button
- [ ] Item should disappear from cart
- [ ] Cart total should update
- [ ] Check session updated

#### Get Cart
- [ ] Call `/api/cart` (GET)
- [ ] Verify JSON response contains:
  - [ ] items array
  - [ ] item_count
  - [ ] subtotal
  - [ ] total

### 4. Order Service

#### Create Order
- [ ] Add items to cart
- [ ] Initiate checkout
- [ ] Create order via API:
  ```python
  order = await order_service.create_order(
      customer_id='user-123',
      items=[{...}],
      shipping_address={...}
  )
  ```
- [ ] Check `orders` table - new record created
- [ ] Check `order_items` table - line items created
- [ ] Check `order_shipping_addresses` table - address saved
- [ ] Check `order_status_history` table - initial log entry
- [ ] Check `marketplace_listings` - stock_reserved incremented
- [ ] Check `marketplace_inventory_adjustments` - adjustment logged

#### Update Order Status
- [ ] Update order to 'paid':
  ```python
  await order_service.update_order_status(
      order_id='order-123',
      new_status='paid',
      actor_id='user-123'
  )
  ```
- [ ] Check `orders` table:
  - [ ] status = 'paid'
  - [ ] payment_status = 'paid'
  - [ ] paid_at timestamp set
- [ ] Check `order_status_history` - new log entry

#### Cancel Order
- [ ] Cancel order
- [ ] Check `orders` table:
  - [ ] status = 'cancelled'
  - [ ] cancelled_at timestamp set
  - [ ] cancellation_reason populated
- [ ] Check `marketplace_listings` - stock_reserved decremented
- [ ] Check `marketplace_inventory_adjustments` - release logged

#### Get Order
- [ ] Fetch order by ID
- [ ] Verify all related data included:
  - [ ] Order details
  - [ ] Order items
  - [ ] Shipping address
  - [ ] Status history

#### List Customer Orders
- [ ] Fetch orders for customer
- [ ] Verify orders sorted by created_at DESC
- [ ] Test status filter
- [ ] Verify item count aggregated

---

## 🧪 Integration Tests

### Auth Integration
- [ ] Register → Verify → Login → Logout flow works end-to-end
- [ ] Duplicate email registration properly rejected
- [ ] Invalid credentials properly rejected
- [ ] Expired verification token properly rejected

### Product Integration
- [ ] Create product → Enable marketplace → Search → Find it
- [ ] Update product details persist correctly
- [ ] Toggle sambatan mode works

### Order Integration
- [ ] Full purchase flow:
  1. [ ] Browse products
  2. [ ] Add to cart
  3. [ ] Update quantities
  4. [ ] Checkout
  5. [ ] Create order
  6. [ ] Reserve inventory
  7. [ ] Update status
  8. [ ] View order history

### Inventory Management
- [ ] Create product with stock = 10
- [ ] Create order for 5 units
- [ ] Verify stock_reserved = 5
- [ ] Verify available stock = 5
- [ ] Try to order 6 units
- [ ] Should fail with InsufficientStock
- [ ] Cancel first order
- [ ] Verify stock_reserved = 0
- [ ] Verify available stock = 10

---

## 🔍 Edge Cases

### Auth Edge Cases
- [ ] Registration with existing email → 409 Conflict
- [ ] Login with wrong password → 401 Unauthorized
- [ ] Login with non-existent email → 401 Unauthorized
- [ ] Verify with invalid token → 404 Not Found
- [ ] Verify with expired token → 410 Gone
- [ ] Login with disabled account → 401 Unauthorized

### Product Edge Cases
- [ ] Create product with negative price → Error
- [ ] Search with empty query → Returns all products
- [ ] Enable marketplace without stock → Works (stock = 0)
- [ ] Toggle sambatan without slots/deadline → Error

### Cart Edge Cases
- [ ] Add same product twice → Quantity increments
- [ ] Update quantity to 0 → Item removed
- [ ] Update quantity to negative → Item removed
- [ ] Remove non-existent item → No error
- [ ] Clear empty cart → No error

### Order Edge Cases
- [ ] Create order with insufficient stock → Error
- [ ] Create order with invalid product → Error
- [ ] Update non-existent order → 404 Not Found
- [ ] Cancel already cancelled order → Idempotent
- [ ] Release inventory twice → Idempotent (stock_reserved doesn't go negative)

---

## 🛡️ Security Checks

- [ ] Password is hashed (not stored in plain text)
- [ ] Supabase service role key not exposed to client
- [ ] Session secret is properly configured (32+ chars)
- [ ] SQL injection protected (using parameterized queries)
- [ ] XSS protection in templates
- [ ] CORS configured appropriately

---

## 📊 Performance Checks

- [ ] Application starts in < 5 seconds
- [ ] Auth operations complete in < 1 second
- [ ] Product search completes in < 2 seconds
- [ ] Order creation completes in < 3 seconds
- [ ] Cart operations complete instantly (session-based)
- [ ] No memory leaks during extended use

---

## 📝 Code Quality Checks

- [ ] All new files have docstrings
- [ ] All public methods have type hints
- [ ] Error handling implemented consistently
- [ ] Logging added where appropriate
- [ ] No commented-out code
- [ ] No TODO comments (or tracked in issues)
- [ ] Code follows PEP 8 style guide
- [ ] Imports organized consistently

---

## 📚 Documentation Checks

- [ ] `PHASE1_IMPLEMENTATION_SUMMARY.md` is complete
- [ ] Code comments explain "why", not "what"
- [ ] API endpoints documented (or OpenAPI spec generated)
- [ ] Environment variables documented
- [ ] Database schema documented

---

## 🧹 Cleanup

- [ ] No temporary files committed
- [ ] No sensitive data in code
- [ ] `.env` in `.gitignore`
- [ ] `__pycache__` in `.gitignore`
- [ ] Unused imports removed

---

## ✨ Fallback Mode Testing

Test that application works WITHOUT Supabase:

- [ ] Remove or comment out Supabase env vars
- [ ] Restart application
- [ ] Should see: "Supabase client not available - using fallback storage"
- [ ] Auth operations should work (in-memory)
- [ ] Product operations should work (in-memory)
- [ ] Cart operations should work (session-based)
- [ ] Order operations should fail gracefully with clear error

---

## 🎯 Acceptance Criteria

Phase 1 is considered complete when:

- ✅ All tasks in todo list completed
- ✅ All functional tests pass
- ✅ All integration tests pass
- ✅ All edge cases handled
- ✅ Security checks pass
- ✅ Performance acceptable
- ✅ Code quality standards met
- ✅ Documentation complete
- ✅ Fallback mode works
- ✅ No critical bugs

---

## 📋 Test Execution Log

Use this section to track test execution:

```
Date: __________
Tester: __________

Completed Tests:
- [ ] Environment Setup
- [ ] Database Setup
- [ ] Application Startup
- [ ] Auth Service Tests
- [ ] Products Service Tests
- [ ] Cart Service Tests
- [ ] Order Service Tests
- [ ] Integration Tests
- [ ] Edge Cases
- [ ] Security Checks
- [ ] Performance Checks
- [ ] Code Quality Checks
- [ ] Documentation Checks
- [ ] Cleanup
- [ ] Fallback Mode Testing

Issues Found:
1. __________________________________________
2. __________________________________________
3. __________________________________________

Status: [ ] PASS  [ ] FAIL  [ ] BLOCKED

Notes:
__________________________________________
__________________________________________
__________________________________________
```

---

## 🚀 Next Steps After Verification

Once all checks pass:

1. [ ] Commit changes with descriptive message
2. [ ] Create pull request
3. [ ] Request code review
4. [ ] Merge to main branch
5. [ ] Tag release: `v1.0.0-phase1`
6. [ ] Begin Phase 2 implementation

---

**Document Owner**: Development Team  
**Last Updated**: 2025-10-05
