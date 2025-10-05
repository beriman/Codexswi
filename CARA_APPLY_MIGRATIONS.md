# 📋 Cara Apply Database Migrations ke Supabase

## 🎯 Ringkasan Situasi

✅ **Integrasi Supabase sudah selesai!** Semua kode sudah siap.
⚠️ **Migrations belum diapply** karena keterbatasan network di environment remote.

**Yang perlu dilakukan**: Apply migrations ke database Supabase Anda.

---

## 🚀 Cara Tercepat: Supabase Dashboard (RECOMMENDED)

### Langkah 1: Buka Supabase Dashboard
1. Buka browser dan kunjungi: **https://app.supabase.com**
2. Login dengan akun Supabase Anda
3. Pilih project: **yguckgrnvzvbxtygbzke**

### Langkah 2: Buka SQL Editor
1. Di sidebar kiri, klik **"SQL Editor"**
2. Klik tombol **"New query"** atau **"+ New"**

### Langkah 3: Copy Isi File Migration
Anda punya 2 pilihan:

#### Pilihan A: Apply Satu per Satu (Lebih Aman)
Copy dan jalankan file-file ini secara berurutan:

**1. Migration Pertama** (0001_initial_schema.sql)
```bash
File: supabase/migrations/0001_initial_schema.sql
Size: 24.1 KB
```
- Copy seluruh isi file `0001_initial_schema.sql`
- Paste di SQL Editor
- Klik tombol **"Run"** atau tekan `Ctrl+Enter` / `Cmd+Enter`
- Tunggu sampai selesai (hijau centang muncul)

**2. Migration Kedua** (0002_profile_social_graph.sql)
```bash
File: supabase/migrations/0002_profile_social_graph.sql
Size: 3.0 KB
```
- Copy seluruh isi file `0002_profile_social_graph.sql`
- Paste di SQL Editor (buat query baru atau ganti yang lama)
- Klik **"Run"**
- Tunggu sampai selesai

**3. Migration Ketiga** (0003_nusantarum_schema.sql)
```bash
File: supabase/migrations/0003_nusantarum_schema.sql
Size: 13.7 KB
```
- Copy seluruh isi file `0003_nusantarum_schema.sql`
- Paste di SQL Editor
- Klik **"Run"**
- Tunggu sampai selesai

#### Pilihan B: Apply Sekaligus (Lebih Cepat)
**Gunakan file gabungan:**
```bash
File: COMBINED_MIGRATIONS.sql
Size: ~42 KB (gabungan dari ketiga migrations)
```
- Copy seluruh isi file `COMBINED_MIGRATIONS.sql`
- Paste di SQL Editor Supabase
- Klik **"Run"**
- Tunggu sampai selesai (bisa 10-30 detik)

### Langkah 4: Verifikasi
Setelah berhasil, verify bahwa tables sudah dibuat:

1. Di Supabase Dashboard, klik **"Table Editor"** di sidebar
2. Anda akan melihat banyak tabel baru, termasuk:
   - ✅ `auth_accounts`
   - ✅ `user_profiles`
   - ✅ `brands`
   - ✅ `products`
   - ✅ `orders`
   - ✅ `sambatan_campaigns`
   - ✅ `articles`
   - Dan 20+ tabel lainnya

3. Atau jalankan query ini di SQL Editor untuk check:
```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;
```

---

## 🔧 Alternatif: Menggunakan psql (Jika Anda Punya)

Jika Anda memiliki `psql` installed di komputer lokal Anda:

```bash
# Set password sebagai environment variable
export PGPASSWORD='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlndWNrZ3Judnp2Ynh0eWdiemtlIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1ODkzODQ1MiwiZXhwIjoyMDc0NTE0NDUyfQ.QYhkQk59D3Y_GBEhNz8amto-RP_WHL-2_tQtGnE8Ia0'

# Jalankan migrations satu per satu
psql -h db.yguckgrnvzvbxtygbzke.supabase.co \
     -p 5432 \
     -U postgres \
     -d postgres \
     -f supabase/migrations/0001_initial_schema.sql

psql -h db.yguckgrnvzvbxtygbzke.supabase.co \
     -p 5432 \
     -U postgres \
     -d postgres \
     -f supabase/migrations/0002_profile_social_graph.sql

psql -h db.yguckgrnvzvbxtygbzke.supabase.co \
     -p 5432 \
     -U postgres \
     -d postgres \
     -f supabase/migrations/0003_nusantarum_schema.sql
```

---

## 📋 File Locations

Semua migration files ada di folder:
```
supabase/migrations/
├── 0001_initial_schema.sql       (24.1 KB)
├── 0002_profile_social_graph.sql (3.0 KB)
└── 0003_nusantarum_schema.sql    (13.7 KB)
```

File gabungan (untuk kemudahan):
```
COMBINED_MIGRATIONS.sql           (~42 KB total)
```

---

## ✅ Setelah Migrations Berhasil Diapply

### 1. Test Aplikasi
Jalankan aplikasi dan test connection:

```bash
cd /workspace

# Test integration
python3 test_supabase_integration.py

# Jalankan aplikasi
PYTHONPATH=/workspace/src python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Expected output dari test:
```
============================================================
✅ All tests passed!
✅ Using SupabaseAuthRepositoryLive (connected to database)
============================================================
```

### 2. Test Authentication Endpoints

Buka di browser atau gunakan curl:

**Register User:**
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "email=test@example.com&full_name=Test User&password=Password123"
```

**Login:**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "email=test@example.com&password=Password123"
```

### 3. Verify di Supabase Dashboard

Setelah register user, check di Supabase:
1. Buka **Table Editor**
2. Pilih table **`auth_accounts`**
3. Anda akan melihat user baru yang terdaftar!

---

## 🗄️ Database Schema Overview

Setelah migrations, database akan memiliki struktur lengkap:

### Authentication & Users (5 tables)
- `auth_accounts` - User credentials
- `auth_sessions` - Active sessions
- `user_profiles` - Extended user info
- `onboarding_registrations` - Email verification
- `onboarding_events` - Onboarding logs

### Brands & Products (8 tables)
- `brands` - Brand catalog
- `brand_members` - Team members
- `brand_followers` - Followers
- `products` - Product listings
- `product_variants` - Product variants
- `product_images` - Media
- `product_history` - Audit trail
- `marketplace_listings` - Active listings

### Orders & Transactions (3 tables)
- `orders` - Customer orders
- `order_items` - Order line items
- `marketplace_inventory_adjustments` - Stock changes

### Sambatan/Group Buy (5 tables)
- `sambatan_campaigns` - Campaign definitions
- `sambatan_participants` - Participants
- `sambatan_transactions` - Financials
- `sambatan_audit_logs` - Audit trail
- `sambatan_lifecycle_states` - State changes

### Content/Nusantarum (4 tables)
- `articles` - Educational articles
- `article_tags` - Tags
- `article_brand_mentions` - Brand mentions
- `article_product_mentions` - Product mentions

### Others
- `user_follows` - Social graph
- `sambatan_dashboard_summary` - Dashboard view
- And more...

**Total: 30+ tables** siap untuk MVP!

---

## 🆘 Troubleshooting

### Error: "relation already exists"
✅ **Itu normal!** Artinya table sudah ada. Migration sudah pernah dijalankan sebelumnya.
Continue saja dengan migrations berikutnya.

### Error: "permission denied"
❌ Pastikan Anda menggunakan **service_role_key**, bukan anon_key.
Service role key diperlukan untuk membuat tables.

### SQL Editor tidak muncul
1. Pastikan project sudah di-setup dengan benar
2. Coba refresh browser
3. Atau gunakan metode psql

### Migrations terlalu panjang
Gunakan **COMBINED_MIGRATIONS.sql** atau apply satu per satu dengan sabar.
Setiap migration bisa memakan waktu 5-15 detik.

---

## 📚 Resources

- **Supabase Dashboard**: https://app.supabase.com
- **Project ID**: yguckgrnvzvbxtygbzke
- **Migration Files**: `supabase/migrations/`
- **Setup Guide**: `SUPABASE_SETUP.md`
- **Integration Guide**: `README_SUPABASE_INTEGRATION.md`

---

## 🎯 Summary

**Status Sekarang:**
- ✅ Kode integrasi Supabase: SELESAI
- ✅ Environment variables: TERKONFIGURASI
- ✅ Dependencies: TERINSTALL
- ⏳ **Migrations: MENUNGGU ANDA APPLY**

**Next Step:**
1. 🔗 Buka https://app.supabase.com
2. 📝 Copy-paste `COMBINED_MIGRATIONS.sql` ke SQL Editor
3. ▶️  Run the query
4. ✅ Done! Database siap digunakan!

**Estimasi waktu:** 5-10 menit

---

Setelah migrations berhasil, aplikasi Anda siap 100% untuk development dan testing! 🚀
