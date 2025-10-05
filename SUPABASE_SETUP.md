# Supabase Integration Setup Guide

Panduan ini menjelaskan cara setup dan mengintegrasikan aplikasi Sensasiwangi dengan Supabase.

## ✅ Status Integrasi

Integrasi Supabase telah berhasil dikonfigurasi dengan komponen berikut:

### 1. Environment Variables
File `.env` telah dibuat dengan kredensial Supabase:
- ✅ `SUPABASE_URL`
- ✅ `SUPABASE_ANON_KEY`
- ✅ `SUPABASE_SERVICE_ROLE_KEY`

### 2. Dependencies
Library Python yang diperlukan telah ditambahkan:
- ✅ `supabase>=2.0.0` - Official Supabase Python client
- ✅ Dependencies lainnya di `requirements.txt` dan `pyproject.toml`

### 3. Supabase Client Module
File `src/app/core/supabase.py` menyediakan:
- ✅ `get_supabase_client()` - Client dengan anon key untuk frontend
- ✅ `get_supabase_admin_client()` - Client dengan service role untuk backend
- ✅ `get_database_url()` - PostgreSQL connection string

### 4. Auth Service Integration
File `src/app/services/auth.py` telah diupdate:
- ✅ `SupabaseAuthRepositoryLive` - Repository yang menggunakan koneksi Supabase aktual
- ✅ `AuthService` otomatis menggunakan koneksi live jika tersedia
- ✅ Fallback ke in-memory repository untuk testing

## 📋 Langkah Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Apply Database Migrations

Migrasi database perlu diapply ke Supabase. Ada beberapa cara:

#### Option A: Via Supabase Dashboard (Recommended)
1. Login ke [Supabase Dashboard](https://app.supabase.com)
2. Pilih project: `yguckgrnvzvbxtygbzke`
3. Buka **SQL Editor**
4. Copy-paste isi file berikut satu per satu:
   - `supabase/migrations/0001_initial_schema.sql`
   - `supabase/migrations/0002_profile_social_graph.sql`
   - `supabase/migrations/0003_nusantarum_schema.sql`
5. Jalankan (Run) setiap file

#### Option B: Via Supabase CLI
```bash
# Install Supabase CLI
npm install -g supabase

# Login
supabase login

# Link to project
supabase link --project-ref yguckgrnvzvbxtygbzke

# Push migrations
supabase db push
```

#### Option C: Via psql (Jika tersedia)
```bash
PGPASSWORD="<SERVICE_ROLE_KEY>" psql \
  -h db.yguckgrnvzvbxtygbzke.supabase.co \
  -p 5432 \
  -U postgres \
  -d postgres \
  -f supabase/migrations/0001_initial_schema.sql
```

### 3. Verify Integration
Jalankan test untuk memverifikasi setup:
```bash
python3 test_supabase_integration.py
```

Expected output:
```
============================================================
Supabase Integration Tests
============================================================
Testing Supabase configuration...
  ✅ SUPABASE_URL: https://yguckgrnvzvbxtygbzke.supabase.co
  ✅ SUPABASE_ANON_KEY: eyJhbGciOiJIUzI1NiIs...
  ✅ SUPABASE_SERVICE_ROLE_KEY: eyJhbGciOiJIUzI1NiIs...

Testing Supabase client creation...
  ✅ Supabase client created successfully
  ✅ Supabase admin client created successfully

Testing AuthService initialization...
  ✅ AuthService initialized with repository: SupabaseAuthRepositoryLive
  ✅ Using SupabaseAuthRepositoryLive (connected to database)

============================================================
✅ All tests passed!
============================================================
```

### 4. Run Application
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Atau menggunakan Python module:
```bash
python3 -m uvicorn app.main:app --reload
```

## 🗄️ Database Schema

Setelah migrasi diapply, database akan memiliki tabel-tabel berikut:

### Authentication & User Management
- `auth_accounts` - User authentication credentials
- `auth_sessions` - Active user sessions
- `user_profiles` - Extended user profile information
- `onboarding_registrations` - Email verification tracking
- `onboarding_events` - Onboarding event logs

### Marketplace & Products
- `brands` - Brand information
- `brand_members` - Brand team members
- `brand_followers` - Users following brands
- `products` - Product catalog
- `product_variants` - Product variants (size, scent, etc.)
- `product_images` - Product media
- `marketplace_listings` - Active marketplace listings
- `orders` - Customer orders
- `order_items` - Order line items

### Sambatan (Group Buy)
- `sambatan_campaigns` - Group buy campaigns
- `sambatan_participants` - Campaign participants
- `sambatan_transactions` - Financial transactions
- `sambatan_audit_logs` - Audit trail
- `sambatan_lifecycle_states` - State transitions

### Content (Nusantarum)
- `articles` - Educational content articles
- `article_tags` - Article categorization
- `article_brand_mentions` - Brand mentions in articles
- `article_product_mentions` - Product mentions in articles

## 🔧 Configuration

### Environment Variables
Semua environment variables dibaca dari file `.env`:

```env
# Supabase configuration
SUPABASE_URL=https://yguckgrnvzvbxtygbzke.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Session secret (minimal 32 karakter)
SESSION_SECRET=development-session-secret-change-in-production-12345678

# RajaOngkir (optional)
RAJAONGKIR_API_KEY=
```

### Using Supabase Client

#### In Services/Repositories:
```python
from app.core.supabase import get_supabase_admin_client

client = get_supabase_admin_client()
result = client.table("auth_accounts").select("*").eq("email", email).execute()
```

#### In API Routes (for user-specific queries):
```python
from app.core.supabase import get_supabase_client

# This uses anon key and respects Row Level Security (RLS)
client = get_supabase_client()
result = client.table("user_profiles").select("*").execute()
```

## 🧪 Testing

### Run All Tests
```bash
pytest tests/
```

### Run Specific Test
```bash
pytest tests/test_auth_service.py
```

Note: Tests menggunakan in-memory repository secara default untuk isolasi. 
Untuk test dengan database aktual, gunakan:

```python
from app.services.auth import AuthService, SupabaseAuthRepositoryLive

service = AuthService(repository=SupabaseAuthRepositoryLive())
```

## 🚀 Next Steps

1. ✅ Environment variables configured
2. ✅ Dependencies installed
3. ✅ Supabase client integrated
4. ✅ Auth service updated
5. ⏳ **Apply database migrations** (manual step required)
6. ⏳ Test authentication endpoints
7. ⏳ Update other services (brands, products, etc.) to use Supabase
8. ⏳ Deploy to production

## 📚 Resources

- [Supabase Python Documentation](https://supabase.com/docs/reference/python)
- [Supabase Dashboard](https://app.supabase.com)
- [Project Migrations](./supabase/migrations/)
- [Implementation Guide](./docs/SUPABASE_IMPLEMENTATION_GUIDE.md)

## 🆘 Troubleshooting

### Error: "Could not find the table 'public.auth_accounts'"
→ Database migrations belum diapply. Ikuti langkah #2 di atas.

### Error: "Supabase client not configured"
→ Pastikan file `.env` ada dan berisi kredensial yang benar.

### Error: "ModuleNotFoundError: No module named 'supabase'"
→ Install dependencies: `pip install -r requirements.txt`

### Tests failing
→ Tests menggunakan in-memory repository. Ini normal dan expected.
   Untuk test dengan database, gunakan integration tests.
