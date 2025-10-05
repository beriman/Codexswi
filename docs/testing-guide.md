# Testing Guide - Auth Service Refactor

**Last Updated**: 2025-10-05

---

## Quick Tests

### 1. Test Imports

```bash
python3 test_imports.py
```

Expected output:
```
✓ Supabase client imports successful
✓ Dependencies imports successful
✓ AuthService imports successful
✓ Auth routes imports successful
✓ Application factory imports successful

✅ All imports successful!
```

### 2. Run Unit Tests

```bash
# Test auth service
pytest tests/test_auth_supabase.py -v

# Run with coverage
pytest tests/test_auth_supabase.py -v --cov=app.services.auth_supabase
```

Expected: All tests pass ✅

### 3. Start Application

```bash
# Set environment variables first (if using real Supabase)
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"

# Start app
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Expected logs:
```
INFO: Starting Sensasiwangi.id (development)
INFO: ✓ Supabase client initialized successfully
INFO: ✓ Supabase connection healthy
INFO: Application startup complete
INFO: Uvicorn running on http://0.0.0.0:8000
```

### 4. Test API Endpoints

#### Register User

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "securepass123",
    "full_name": "Test User"
  }'
```

Expected response (201):
```json
{
  "registration_id": "...",
  "account_id": "...",
  "email": "test@example.com",
  "full_name": "Test User",
  "status": "pending_verification",
  "verification_expires_at": "...",
  "message": "Registrasi berhasil. Cek email Anda untuk tautan verifikasi."
}
```

#### Verify Email (requires token from email)

```bash
curl -X POST http://localhost:8000/api/auth/verify \
  -H "Content-Type: application/json" \
  -d '{
    "token": "your-verification-token"
  }'
```

Expected response (200):
```json
{
  "user_id": "...",
  "email": "test@example.com",
  "full_name": "Test User",
  "status": "active",
  "message": "Verifikasi berhasil. Silakan login."
}
```

#### Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "securepass123"
  }' \
  -c cookies.txt
```

Expected response (200):
```json
{
  "user_id": "...",
  "email": "test@example.com",
  "full_name": "Test User",
  "status": "active",
  "message": "Login berhasil"
}
```

#### Check Session

```bash
curl -X GET http://localhost:8000/api/auth/session \
  -b cookies.txt
```

Expected response (200):
```json
{
  "is_authenticated": true,
  "user": {
    "user_id": "...",
    "email": "test@example.com",
    "full_name": "Test User",
    "status": "active"
  }
}
```

#### Logout

```bash
curl -X POST http://localhost:8000/api/auth/logout \
  -b cookies.txt
```

Expected response (204): No content

---

## Integration Testing

### Full Registration Flow

Create a test script:

```python
# test_auth_flow.py
import requests
import time

BASE_URL = "http://localhost:8000/api/auth"

def test_full_auth_flow():
    """Test complete auth flow."""
    
    # 1. Register
    print("1. Testing registration...")
    response = requests.post(f"{BASE_URL}/register", json={
        "email": f"test-{int(time.time())}@example.com",
        "password": "securepass123",
        "full_name": "Test User"
    })
    assert response.status_code == 201, f"Registration failed: {response.text}"
    data = response.json()
    print(f"✓ Registered: {data['email']}")
    
    # 2. Login (skip verification for now - would need real Supabase)
    # In real scenario, you'd verify email first
    
    print("\n✅ Registration flow working!")

if __name__ == "__main__":
    test_full_auth_flow()
```

Run:
```bash
python3 test_auth_flow.py
```

---

## Manual Testing Checklist

### Registration Flow
- [ ] Open http://localhost:8000/auth
- [ ] Fill registration form
- [ ] Submit
- [ ] Check console for success message
- [ ] Check database: `auth_accounts` table should have new row
- [ ] Check database: `onboarding_registrations` table should have new row
- [ ] Check email was sent (if configured)

### Verification Flow
- [ ] Get verification token from database or email
- [ ] Use verify endpoint
- [ ] Check account status changed to 'active'
- [ ] Check onboarding_events logged

### Login Flow
- [ ] Open http://localhost:8000/auth
- [ ] Enter credentials
- [ ] Submit
- [ ] Check session cookie created
- [ ] Check database: `auth_sessions` table has new row
- [ ] Refresh page - should still be logged in

### Session Persistence
- [ ] Login successfully
- [ ] Close browser
- [ ] Open browser again
- [ ] Visit site
- [ ] Should still be logged in (if within 30 days)

### Logout Flow
- [ ] Click logout
- [ ] Check session cookie cleared
- [ ] Check database: session row deleted
- [ ] Try to access protected route - should fail

---

## Troubleshooting

### Issue: Supabase not configured

**Error**:
```
WARNING: ⚠ Supabase client not available - using fallback storage
```

**Fix**:
```bash
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"
```

### Issue: Import errors

**Error**:
```
ModuleNotFoundError: No module named 'supabase'
```

**Fix**:
```bash
pip install -r requirements.txt
```

### Issue: Database table not found

**Error**:
```
relation "auth_accounts" does not exist
```

**Fix**: Run migrations
```bash
# Connect to Supabase and run migrations
psql $SUPABASE_DATABASE_URL < supabase/migrations/0001_initial_schema.sql
```

### Issue: Session not persisting

**Problem**: User logged out after refresh

**Check**:
1. Session middleware configured? ✓
2. Session cookie being set? Check browser DevTools
3. Session token in database? Check `auth_sessions` table
4. Session not expired? Check `expires_at` column

---

## Database Verification

### Check User Created

```sql
SELECT id, email, full_name, status, created_at 
FROM auth_accounts 
WHERE email = 'test@example.com';
```

### Check Session Created

```sql
SELECT id, account_id, expires_at, created_at
FROM auth_sessions
WHERE account_id = 'your-user-id';
```

### Check Registration Record

```sql
SELECT id, email, status, verification_token
FROM onboarding_registrations
WHERE email = 'test@example.com';
```

---

## Performance Testing

### Load Test Registration

```bash
# Install apache bench
sudo apt-get install apache2-utils

# Test 100 concurrent registration requests
ab -n 100 -c 10 -p register.json -T application/json \
  http://localhost:8000/api/auth/register
```

Expected:
- Success rate > 95%
- Mean response time < 200ms
- No database errors

---

## Automated Testing

### Setup pytest

```bash
pip install pytest pytest-cov pytest-asyncio
```

### Run All Tests

```bash
# All tests
pytest -v

# Just auth tests
pytest tests/test_auth_supabase.py -v

# With coverage
pytest --cov=app --cov-report=html

# Open coverage report
open htmlcov/index.html
```

### Continuous Testing

```bash
# Watch mode - reruns tests on file changes
pytest-watch
```

---

## Next Steps

After auth testing passes:

1. **Move to Product Service** (12 hours)
   - Test product CRUD
   - Test marketplace listing
   - Test search/filter

2. **Move to Cart Service** (6 hours)
   - Test add to cart
   - Test update quantity
   - Test remove from cart

3. **Move to Order Service** (16 hours)
   - Test order creation
   - Test inventory reservation
   - Test status transitions

---

## Success Criteria

Auth service is considered **production ready** when:

✅ All unit tests pass  
✅ All integration tests pass  
✅ Manual testing checklist complete  
✅ Performance tests pass  
✅ Database tables populated correctly  
✅ Sessions persist across restarts  
✅ Error handling works properly  
✅ Logging is appropriate  

---

**Happy Testing!** 🧪✨
