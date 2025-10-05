# Phase 2 Quick Start Guide

**Purpose**: Test the Core Shopping & Checkout Flow  
**Time Required**: 15-20 minutes  
**Prerequisites**: Phase 1 completed, Supabase configured

---

## Step 1: Apply Database Migration

Run the new migration to add inventory helper functions:

```bash
# Navigate to your Supabase project dashboard
# Or use Supabase CLI:
supabase migration up
```

Or apply manually in Supabase SQL Editor:
```sql
-- Copy and execute: supabase/migrations/0004_order_helpers.sql
```

---

## Step 2: Start the Application

```bash
cd /workspace
uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Supabase client initialized successfully
```

---

## Step 3: Setup Test Data

### 3.1 Create Test User
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "email=test@example.com&password=securepass123&full_name=Test User"
```

### 3.2 Create Test Product
Use Supabase dashboard or:
```sql
-- In Supabase SQL Editor
INSERT INTO brands (id, name, slug, status)
VALUES (gen_random_uuid(), 'Test Brand', 'test-brand', 'active');

INSERT INTO products (id, brand_id, name, slug, price_low, marketplace_enabled, status)
VALUES (
  gen_random_uuid(), 
  (SELECT id FROM brands WHERE slug = 'test-brand'), 
  'Test Parfum', 
  'test-parfum', 
  150000, 
  true, 
  'active'
);

INSERT INTO marketplace_listings (product_id, list_price, stock_on_hand, status)
VALUES (
  (SELECT id FROM products WHERE slug = 'test-parfum'),
  150000,
  10,
  'published'
);
```

---

## Step 4: Test Shopping Flow

### 4.1 Browse Marketplace
```
Visit: http://localhost:8000/marketplace
```
Expected: See products including "Test Parfum"

### 4.2 Add to Cart
```
Click "Tambah ke Keranjang" on any product
Visit: http://localhost:8000/cart
```
Expected: Cart shows added items with totals

### 4.3 Proceed to Checkout
```
Click "Checkout" button in cart
Visit: http://localhost:8000/checkout
```
Expected: 
- Checkout form appears
- Order summary in sidebar
- Cart items displayed

### 4.4 Fill Shipping Address
Complete the form:
- **Nama Penerima**: John Doe
- **Nomor Telepon**: 081234567890
- **Provinsi**: Jawa Barat
- **Kota**: Bandung
- **Kecamatan**: Coblong
- **Kode Pos**: 40132
- **Alamat**: Jl. Merdeka No. 123

Click "Buat Pesanan"

Expected:
- Redirects to `/order/confirmation/{order_id}`
- Shows success message
- Displays order number (ORD-YYYYMMDD-XXXX)

### 4.5 View Order Details
```
Click "Lihat Detail Pesanan"
URL: http://localhost:8000/order/{order_id}
```
Expected:
- Order timeline visible
- Items listed
- Shipping address displayed
- Payment status shown

### 4.6 Check Order History
```
Visit: http://localhost:8000/orders
```
Expected: List of all orders for logged-in user

---

## Step 5: Verify Database Changes

### 5.1 Check Order Created
```sql
SELECT * FROM orders WHERE order_number LIKE 'ORD-%' ORDER BY created_at DESC LIMIT 1;
```

Expected fields:
- `order_number`: ORD-YYYYMMDD-XXXX
- `status`: draft
- `payment_status`: pending
- `total_amount`: Sum of items

### 5.2 Check Order Items
```sql
SELECT * FROM order_items WHERE order_id = '<order_id_from_above>';
```

Expected: Row for each cart item with:
- `product_name`
- `quantity`
- `unit_price`
- `subtotal_amount`

### 5.3 Check Inventory Reserved
```sql
SELECT product_id, stock_on_hand, stock_reserved 
FROM marketplace_listings 
WHERE product_id IN (
  SELECT product_id FROM order_items WHERE order_id = '<order_id>'
);
```

Expected: `stock_reserved` increased by order quantity

### 5.4 Check Shipping Address
```sql
SELECT * FROM order_shipping_addresses WHERE order_id = '<order_id>';
```

Expected: All address fields populated

---

## Step 6: Test Error Handling

### 6.1 Insufficient Stock
1. Update product stock to 0
2. Try to add to cart and checkout
3. Expected: "Stok tidak mencukupi" error

### 6.2 Empty Cart Checkout
1. Visit `/checkout` with empty cart
2. Expected: Redirect to `/cart`

### 6.3 Unauthorized Access
1. Logout or clear session
2. Visit `/order/{order_id}` of another user
3. Expected: 403 Forbidden or redirect

---

## Step 7: Test Cart Operations

### 7.1 Update Quantity
```
In cart page:
- Change quantity using number input
- Expected: Subtotal recalculates
```

### 7.2 Remove Item
```
Click "Hapus" on any cart item
Expected: Item removed, totals updated
```

### 7.3 Clear Cart
```bash
curl -X POST http://localhost:8000/api/cart/clear \
  -H "Cookie: session=<your-session-cookie>"
```
Expected: Cart becomes empty

---

## Common Issues & Solutions

### Issue 1: "Database connection required"
**Solution**: 
- Verify `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` in environment
- Check Supabase dashboard for service status

### Issue 2: "Product listing not found"
**Solution**:
- Ensure product has `marketplace_enabled = true`
- Check `marketplace_listings` table has entry for product

### Issue 3: "Silakan login terlebih dahulu"
**Solution**:
- Login via `/auth/login` first
- Verify session cookie is set

### Issue 4: Migration fails
**Solution**:
- Check for existing functions: `DROP FUNCTION IF EXISTS reserve_stock;`
- Run migration again

---

## API Endpoints Reference

### Cart APIs
```
POST   /api/cart/add       - Add item to cart
POST   /api/cart/update    - Update quantity
POST   /api/cart/remove    - Remove item
POST   /api/cart/clear     - Clear cart
GET    /api/cart           - Get cart JSON
```

### Checkout APIs
```
GET    /checkout                         - Show checkout form
POST   /api/checkout/create-order        - Process checkout
GET    /order/confirmation/{order_id}    - Confirmation page
GET    /order/{order_id}                 - Order details
GET    /orders                           - Order history
```

---

## Performance Testing

### Load Test Checkout (Optional)
```bash
# Install Apache Bench
apt-get install apache2-utils

# Test checkout endpoint
ab -n 100 -c 10 http://localhost:8000/checkout
```

Expected:
- Response time < 500ms
- No 500 errors
- Rate limiting kicks in after threshold

---

## Monitoring Commands

### Watch Order Creation
```sql
-- In Supabase SQL Editor
SELECT order_number, status, total_amount, created_at 
FROM orders 
ORDER BY created_at DESC 
LIMIT 10;
```

### Monitor Inventory
```sql
SELECT p.name, ml.stock_on_hand, ml.stock_reserved, 
       (ml.stock_on_hand - ml.stock_reserved) as available
FROM marketplace_listings ml
JOIN products p ON p.id = ml.product_id
WHERE ml.stock_on_hand > 0;
```

### Check Cart Activity
```sql
-- This would require session storage analysis
-- For now, use application logs
```

---

## Next Steps After Testing

1. ✅ Verify all templates render correctly
2. ✅ Test on mobile devices (responsive design)
3. ✅ Check Indonesian language consistency
4. ✅ Validate accessibility (keyboard navigation)
5. ⏳ Integrate payment gateway (Phase 3)
6. ⏳ Add email notifications (Phase 3)
7. ⏳ Implement RajaOngkir shipping (Phase 3)

---

## Success Criteria

Your Phase 2 implementation is successful if:

- ✅ Can add products to cart
- ✅ Cart persists during session
- ✅ Checkout form submits successfully
- ✅ Order is created in database
- ✅ Inventory is reserved correctly
- ✅ Confirmation page displays
- ✅ Order details are accessible
- ✅ Order history loads
- ✅ No console errors
- ✅ Mobile responsive

---

## Support

If you encounter issues:
1. Check application logs: `tail -f logs/app.log`
2. Review Supabase logs in dashboard
3. Validate session cookies in browser dev tools
4. Check database constraints and triggers

**Documentation**: See `PHASE2_IMPLEMENTATION_SUMMARY.md`

---

**Last Updated**: 2025-10-05  
**Tested By**: Development Team  
**Status**: Ready for UAT
