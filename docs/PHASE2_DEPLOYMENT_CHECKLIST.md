# Phase 2 Deployment Checklist

**Target**: Production deployment of Core Shopping & Checkout Flow  
**Date**: 2025-10-05  
**Priority**: HIGH

---

## Pre-Deployment Checklist

### 1. Database Preparation
- [ ] Backup production database
- [ ] Apply migration `0004_order_helpers.sql`
- [ ] Verify functions created successfully:
  ```sql
  SELECT routine_name, routine_type 
  FROM information_schema.routines 
  WHERE routine_name IN ('reserve_stock', 'release_stock', 'commit_stock', 'get_available_stock');
  ```
- [ ] Test functions with sample data
- [ ] Verify row-level security policies on orders tables

### 2. Code Deployment
- [ ] Merge feature branch to main
- [ ] Tag release: `v1.2.0-phase2`
- [ ] Deploy to staging first
- [ ] Run smoke tests on staging
- [ ] Deploy to production

### 3. Configuration
- [ ] Verify environment variables:
  - `SUPABASE_URL`
  - `SUPABASE_SERVICE_ROLE_KEY`
  - `SESSION_SECRET_KEY`
- [ ] Check rate limiting is enabled
- [ ] Configure CORS if needed
- [ ] Set up error monitoring (Sentry)

### 4. Testing on Staging
- [ ] Create test order end-to-end
- [ ] Verify inventory reservation
- [ ] Test order confirmation email (if configured)
- [ ] Check mobile responsiveness
- [ ] Validate payment status flow
- [ ] Test error scenarios (out of stock, etc.)

---

## Deployment Steps

### Step 1: Database Migration
```bash
# Using Supabase CLI
cd /workspace
supabase migration up

# Or in Supabase Dashboard
# 1. Go to SQL Editor
# 2. Copy contents of 0004_order_helpers.sql
# 3. Execute
# 4. Verify no errors
```

### Step 2: Deploy Application
```bash
# If using Vercel
vercel --prod

# If using Docker
docker build -t sensasiwangi:phase2 .
docker push sensasiwangi:phase2
kubectl apply -f k8s/deployment.yaml

# If using traditional server
git pull origin main
systemctl restart sensasiwangi
```

### Step 3: Verify Deployment
```bash
# Health check
curl https://sensasiwangi.id/api/health

# Test checkout endpoint
curl https://sensasiwangi.id/checkout
```

### Step 4: Monitor
- [ ] Check error logs for 5 minutes
- [ ] Verify no 500 errors
- [ ] Monitor database connections
- [ ] Check Supabase real-time logs

---

## Rollback Plan

If deployment fails:

### Option 1: Code Rollback
```bash
# Revert to previous version
git revert HEAD
vercel --prod

# Or redeploy previous tag
git checkout v1.1.0
vercel --prod
```

### Option 2: Database Rollback
```sql
-- Remove new functions
DROP FUNCTION IF EXISTS reserve_stock(uuid, integer);
DROP FUNCTION IF EXISTS release_stock(uuid, integer);
DROP FUNCTION IF EXISTS commit_stock(uuid, integer);
DROP FUNCTION IF EXISTS get_available_stock(uuid);
```

### Option 3: Feature Toggle
```python
# In application.py, comment out:
# app.include_router(checkout_routes.router)
```

---

## Post-Deployment Verification

### 1. Functional Tests (15 minutes)
- [ ] Navigate to marketplace
- [ ] Add product to cart
- [ ] View cart page
- [ ] Proceed to checkout
- [ ] Fill shipping form
- [ ] Submit order
- [ ] Verify confirmation page
- [ ] Check order details page
- [ ] Access order history

### 2. Database Checks (5 minutes)
```sql
-- Check recent orders
SELECT COUNT(*) FROM orders WHERE created_at > NOW() - INTERVAL '1 hour';

-- Check inventory status
SELECT COUNT(*) FROM marketplace_listings WHERE stock_reserved > 0;

-- Check order items
SELECT COUNT(*) FROM order_items WHERE created_at > NOW() - INTERVAL '1 hour';
```

### 3. Performance Checks (5 minutes)
- [ ] Checkout page loads < 2 seconds
- [ ] Order creation < 1 second
- [ ] No database deadlocks
- [ ] Rate limiting works correctly

---

## Monitoring Setup

### 1. Alerts to Configure
- Order creation errors > 5% in 10 minutes
- Database connection failures
- Inventory reservation conflicts
- Checkout abandonment rate > 50%

### 2. Metrics to Track
- Orders created per day
- Average order value
- Checkout completion rate
- Cart abandonment rate
- Inventory turnover

### 3. Logs to Monitor
```bash
# Application logs
tail -f /var/log/sensasiwangi/app.log | grep -E "checkout|order"

# Database logs (via Supabase dashboard)
# Filter by: operations on orders table
```

---

## Known Issues & Workarounds

### Issue 1: Guest Checkout Not Supported
**Status**: By design for MVP  
**Workaround**: Users must register/login first  
**Future Fix**: Implement guest checkout in Phase 4

### Issue 2: Shipping Cost Manual
**Status**: Awaiting RajaOngkir integration (Phase 3)  
**Workaround**: Show "Akan dihitung" in checkout  
**Process**: Admin confirms shipping cost manually

### Issue 3: No Payment Gateway
**Status**: Manual payment confirmation for MVP  
**Workaround**: Customer service contacts buyer  
**Future Fix**: Midtrans integration in Phase 3

---

## Communication Plan

### 1. Internal Team
**Before Deployment**:
- Notify team 24 hours in advance
- Share deployment window: [Date/Time]
- Brief on rollback procedures

**After Deployment**:
- Send deployment complete notification
- Share quick start guide link
- Schedule demo session

### 2. Customer Service Team
**Training Required**:
- [ ] How to view orders in admin panel
- [ ] How to update order status
- [ ] How to handle inventory issues
- [ ] Contact procedures for shipping

**Documentation**:
- [ ] Create CS manual for order management
- [ ] Prepare FAQs for customers
- [ ] Setup response templates

### 3. Customers (If applicable)
**Announcement**:
- Email: "New Online Shopping Feature"
- Social media: Feature highlight
- In-app banner: "Try our new checkout"

---

## Success Metrics (First 7 Days)

### Technical Metrics
- [ ] Uptime > 99.5%
- [ ] Average response time < 500ms
- [ ] Error rate < 1%
- [ ] Successful checkouts > 90%

### Business Metrics
- [ ] Number of orders created: ___
- [ ] Average order value: Rp ___
- [ ] Checkout completion rate: ____%
- [ ] Customer complaints: < 5

---

## Maintenance Tasks

### Daily
- [ ] Check order creation logs
- [ ] Monitor inventory levels
- [ ] Review failed orders
- [ ] Respond to customer issues

### Weekly
- [ ] Analyze checkout abandonment
- [ ] Review order status distribution
- [ ] Check inventory discrepancies
- [ ] Update product availability

### Monthly
- [ ] Generate order reports
- [ ] Review system performance
- [ ] Plan feature enhancements
- [ ] Customer satisfaction survey

---

## Phase 3 Preparation

While monitoring Phase 2:
- [ ] Design payment gateway integration
- [ ] Plan RajaOngkir API setup
- [ ] Prepare email notification templates
- [ ] Design order status webhooks
- [ ] Plan reporting dashboard

---

## Emergency Contacts

**Technical Issues**:
- Backend Lead: [Contact]
- Database Admin: [Contact]
- DevOps: [Contact]

**Business Issues**:
- Product Manager: [Contact]
- Customer Service Lead: [Contact]
- Operations: [Contact]

**Vendor Support**:
- Supabase: support@supabase.io
- Vercel: support@vercel.com

---

## Sign-off

### Development Team
- [ ] Code reviewed
- [ ] Tests passed
- [ ] Documentation complete
- Signed by: _______________ Date: ___________

### QA Team
- [ ] Functional tests passed
- [ ] Performance acceptable
- [ ] Security reviewed
- Signed by: _______________ Date: ___________

### Product Manager
- [ ] Features verified
- [ ] User flows tested
- [ ] Approved for deployment
- Signed by: _______________ Date: ___________

---

**Last Updated**: 2025-10-05  
**Status**: Ready for Deployment  
**Next Review**: After 7 days in production
