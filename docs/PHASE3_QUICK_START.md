# Phase 3 Quick Start: Sambatan Persistent Storage & Scheduler

Panduan cepat untuk memulai menggunakan Sambatan dengan persistent storage dan automated scheduler.

---

## 🚀 Setup (5 menit)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup Environment Variables
```bash
# .env file
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...
```

### 3. Apply Database Migrations
```bash
# Via Supabase CLI
supabase db push

# Or manual via psql
psql -h db.xxxxx.supabase.co -U postgres -d postgres \
  -f supabase/migrations/0005_sambatan_helpers.sql
```

### 4. Start Application
```bash
uvicorn app.main:app --reload
```

**Expected output:**
```
INFO: Supabase client initialized successfully
INFO: Sambatan lifecycle scheduler started
INFO: Application startup complete
```

---

## 📝 Usage Examples

### Create a Campaign

```python
from app.services.sambatan import sambatan_service
from datetime import datetime, UTC, timedelta

campaign = sambatan_service.create_campaign(
    product_id="product-uuid-here",
    title="Sambatan Batch Oktober",
    total_slots=20,
    price_per_slot=150000,
    deadline=datetime.now(UTC) + timedelta(days=7)
)

print(f"Campaign created: {campaign.id}")
```

### Join a Campaign

```python
participant = sambatan_service.join_campaign(
    campaign_id=campaign.id,
    user_id="user-uuid",
    quantity=2,
    shipping_address="Jl. Melati No. 15, Jakarta Selatan"
)

print(f"Joined with {participant.quantity} slots")
```

### Check Campaign Status

```python
campaign = sambatan_service.get_campaign(campaign.id)
print(f"Status: {campaign.status}")
print(f"Progress: {campaign.progress_percent()}%")
print(f"Slots: {campaign.slots_taken}/{campaign.total_slots}")
```

---

## 🔧 API Endpoints

### Campaign Management

**Create Campaign:**
```bash
curl -X POST http://localhost:8000/api/sambatan/campaigns \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "uuid",
    "title": "Test Campaign",
    "total_slots": 10,
    "price_per_slot": 100000,
    "deadline": "2025-10-10T00:00:00Z"
  }'
```

**List Campaigns:**
```bash
curl http://localhost:8000/api/sambatan/campaigns
```

**Get Campaign Details:**
```bash
curl http://localhost:8000/api/sambatan/campaigns/{campaign_id}
```

### Participation

**Join Campaign:**
```bash
curl -X POST http://localhost:8000/api/sambatan/campaigns/{id}/join \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-uuid",
    "quantity": 2,
    "shipping_address": "Your address",
    "note": "Optional note"
  }'
```

**Cancel Participation:**
```bash
curl -X POST http://localhost:8000/api/sambatan/participations/{id}/cancel \
  -H "Content-Type: application/json" \
  -d '{"reason": "Changed my mind"}'
```

### Scheduler Control

**Check Scheduler Status:**
```bash
curl http://localhost:8000/api/sambatan/scheduler/status
```

**Trigger Lifecycle Manually:**
```bash
curl -X POST http://localhost:8000/api/sambatan/scheduler/trigger
```

---

## 🧪 Testing

### Run Unit Tests
```bash
pytest tests/test_sambatan_service.py -v
```

### Run API Tests
```bash
pytest tests/test_sambatan_api.py -v
```

### Manual Test Flow

**1. Create product and enable sambatan:**
```python
from app.services.products import product_service
from datetime import datetime, UTC, timedelta

product = product_service.create_product(
    name="Rimba Embun",
    base_price=420000
)

product_service.toggle_sambatan(
    product_id=product.id,
    enabled=True,
    total_slots=10,
    deadline=datetime.now(UTC) + timedelta(days=3)
)
```

**2. Create campaign:**
```python
campaign = sambatan_service.create_campaign(
    product_id=product.id,
    title="Batch Oktober",
    total_slots=10,
    price_per_slot=210000,
    deadline=datetime.now(UTC) + timedelta(days=3)
)
```

**3. Join as multiple users:**
```python
# User 1
p1 = sambatan_service.join_campaign(
    campaign_id=campaign.id,
    user_id="user-1",
    quantity=3,
    shipping_address="Address 1"
)

# User 2
p2 = sambatan_service.join_campaign(
    campaign_id=campaign.id,
    user_id="user-2",
    quantity=7,
    shipping_address="Address 2"
)
```

**4. Check if campaign is full:**
```python
campaign = sambatan_service.get_campaign(campaign.id)
assert campaign.status == SambatanStatus.FULL
assert campaign.slots_taken == 10
```

**5. Wait for scheduler to complete it:**
```python
# Scheduler will auto-complete after 5 minutes
# Or trigger manually:
from app.services.scheduler import get_scheduler

scheduler = get_scheduler()
scheduler.run_now()

# Check status
campaign = sambatan_service.get_campaign(campaign.id)
assert campaign.status == SambatanStatus.COMPLETED
```

---

## 🔍 Monitoring

### Check Logs
```bash
# View application logs
tail -f app.log | grep "Sambatan"

# View scheduler activity
tail -f app.log | grep "lifecycle"
```

### Database Queries

**Active campaigns:**
```sql
SELECT 
  id, 
  title, 
  status, 
  filled_slots, 
  total_slots,
  deadline 
FROM sambatan_campaigns 
WHERE status IN ('active', 'locked')
ORDER BY deadline ASC;
```

**Recent transitions:**
```sql
SELECT 
  c.title,
  l.event,
  l.created_at,
  l.metadata
FROM sambatan_audit_logs l
JOIN sambatan_campaigns c ON c.id = l.campaign_id
WHERE l.created_at > NOW() - INTERVAL '1 hour'
ORDER BY l.created_at DESC;
```

**Campaign progress:**
```sql
SELECT * FROM get_sambatan_campaign_progress('campaign-uuid');
```

---

## ⚙️ Configuration

### Scheduler Interval

**Default: 5 minutes**

To change:
```python
# In src/app/core/application.py
scheduler = start_scheduler(interval_minutes=10)  # 10 minutes
```

### Database Connection

**Using Supabase:**
```python
from app.core.supabase import get_supabase_client

client = get_supabase_client()
```

**Custom database for testing:**
```python
from app.services.sambatan import SambatanService
from tests.conftest import FakeSupabaseClient

fake_db = FakeSupabaseClient()
service = SambatanService(db=fake_db)
```

---

## 🐛 Troubleshooting

### Scheduler not running

**Check logs:**
```bash
grep "scheduler" app.log
```

**Expected:**
```
INFO: Sambatan lifecycle scheduler started
```

**If missing:**
- Check Supabase connection
- Verify environment variables
- Check for startup errors

### Campaigns not transitioning

**Manual trigger:**
```bash
curl -X POST http://localhost:8000/api/sambatan/scheduler/trigger
```

**Check campaign deadline:**
```python
campaign = sambatan_service.get_campaign(campaign_id)
print(f"Deadline: {campaign.deadline}")
print(f"Status: {campaign.status}")
```

### Race condition on joins

**Should not happen** - atomic operations prevent this.

**If you see issues:**
```sql
-- Check for negative available slots
SELECT 
  id, 
  title, 
  total_slots,
  filled_slots,
  total_slots - filled_slots as available
FROM sambatan_campaigns
WHERE (total_slots - filled_slots) < 0;
```

---

## 📚 Related Documentation

- [Phase 3 Implementation Summary](PHASE3_IMPLEMENTATION_SUMMARY.md) - Complete technical details
- [Architecture Action Plan](architecture-action-plan.md) - Overall roadmap
- [PRD MVP](../PRD_MVP.md) - Product requirements

---

## 💡 Tips & Best Practices

### 1. Always use atomic operations
```python
# ✅ Good - uses atomic RPC
participant = sambatan_service.join_campaign(...)

# ❌ Bad - manual slot updates
# campaign.slots_taken += 1  # Race condition!
```

### 2. Handle exceptions properly
```python
from app.services.sambatan import InsufficientSlots, CampaignClosed

try:
    participant = sambatan_service.join_campaign(...)
except InsufficientSlots:
    print("Sorry, not enough slots available")
except CampaignClosed:
    print("Campaign is no longer accepting participants")
```

### 3. Monitor scheduler health
```python
from app.services.scheduler import get_scheduler

scheduler = get_scheduler()
if not scheduler.is_running:
    # Alert! Scheduler is down
    scheduler.start()
```

### 4. Use deadline wisely
```python
# ✅ Good - reasonable deadline
deadline = datetime.now(UTC) + timedelta(days=7)

# ❌ Bad - too short
deadline = datetime.now(UTC) + timedelta(hours=1)
```

### 5. Test before production
```python
# Use fake client for tests
from tests.conftest import FakeSupabaseClient

def test_my_feature():
    fake_db = FakeSupabaseClient()
    service = SambatanService(db=fake_db)
    # Test without touching real database
```

---

## 🎯 Next Steps

1. **Read Full Documentation**: [PHASE3_IMPLEMENTATION_SUMMARY.md](PHASE3_IMPLEMENTATION_SUMMARY.md)
2. **Run Tests**: `pytest tests/test_sambatan_*.py -v`
3. **Try Examples**: Use code snippets above
4. **Monitor Logs**: Watch scheduler activity
5. **Check Database**: Verify data persistence

---

**Need Help?**
- Check logs: `tail -f app.log | grep Sambatan`
- Database: `psql` and run monitoring queries
- API: Test with curl examples above

**Happy Coding! 🚀**
