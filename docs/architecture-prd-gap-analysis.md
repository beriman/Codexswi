# Analisis Gap Arsitektur vs PRD MVP

**Tanggal**: 2025-10-05  
**Status**: Review Komprehensif  
**Tujuan**: Memastikan arsitektur implementasi sesuai dengan spesifikasi PRD_MVP.md

---

## 1. Executive Summary

Arsitektur saat ini memiliki fondasi yang kuat dengan database schema komprehensif dan beberapa service layer. Namun, ada beberapa komponen kritis yang **masih menggunakan implementasi in-memory** atau **belum diimplementasikan** yang perlu diselaraskan dengan PRD untuk mencapai target MVP.

### Status Keseluruhan
- ✅ **Database Schema**: 100% lengkap dan sesuai PRD
- ⚠️ **Service Layer**: 60% implementasi (beberapa masih in-memory)
- ❌ **Order & Checkout Flow**: Belum diimplementasikan
- ❌ **RajaOngkir Integration**: Belum diimplementasikan
- ❌ **Sambatan Scheduler**: Belum diimplementasikan
- ✅ **Frontend Templates**: 70% tersedia

---

## 2. Database Schema - ✅ SESUAI PRD

### Yang Sudah Benar
✅ Semua tabel yang diperlukan sudah ada di migrasi Supabase:
- `auth_accounts`, `auth_sessions`, `user_profiles`
- `brands`, `brand_members`, `brand_addresses`
- `products`, `product_variants`, `product_images`, `marketplace_listings`
- `orders`, `order_items`, `order_shipping_addresses`, `order_status_history`
- `sambatan_campaigns`, `sambatan_participants`, `sambatan_transactions`, `sambatan_audit_logs`, `sambatan_lifecycle_states`
- `nusantarum_articles`, `parfums`, `perfumers`, `perfume_notes`
- `user_addresses`, `user_follows`, `product_perfumers`

✅ Enums sesuai PRD:
- `onboarding_status`, `brand_status`, `product_status`, `order_status`
- `sambatan_status`, `sambatan_participant_status`, `sambatan_transaction_type`
- `article_status`, `article_category`, `marketplace_listing_status`
- `payment_status`, `order_channel`

✅ Views untuk performa:
- `sambatan_dashboard_summary`
- `profile_brand_summary`
- `user_profile_stats`
- `marketplace_product_snapshot`
- `nusantarum_perfume_directory`
- `nusantarum_brand_directory`
- `nusantarum_perfumer_directory`

✅ Triggers dan functions:
- `set_updated_at()` untuk timestamp otomatis
- `set_parfum_displayable()` untuk validasi Nusantarum
- `refresh_perfumer_link()` untuk sinkronisasi
- `log_parfum_audit()` untuk audit trail

### Rekomendasi
✅ **Database schema sudah lengkap dan siap digunakan**

---

## 3. Backend Services - ⚠️ SEBAGIAN SESUAI

### 3.1 Auth Service (`src/app/services/auth.py`) - ⚠️ IN-MEMORY

**Status**: Implementasi lengkap tapi menggunakan storage in-memory

**Yang Ada**:
- ✅ User registration dengan password hashing (PBKDF2)
- ✅ Email verification flow dengan token expiry
- ✅ Login/logout dengan session management
- ✅ Password policy validation (minimal 8 karakter)
- ✅ Integration dengan email service

**Gap**:
- ❌ **Tidak tersinkron dengan Supabase** - data disimpan di dictionary in-memory
- ❌ Tidak menggunakan tabel `auth_accounts` dan `auth_sessions` dari migrasi
- ❌ Data hilang saat restart aplikasi

**Rekomendasi**:
```python
# Perlu refactor untuk menggunakan Supabase client
# Ubah dari: self._accounts: Dict[str, AuthUser] = {}
# Menjadi: self._client = supabase.create_client(url, key)
# Dan gunakan: await self._client.table('auth_accounts').select(...).execute()
```

**Prioritas**: 🔴 **TINGGI** - Kritis untuk persistence data pengguna

---

### 3.2 Product Service (`src/app/services/products.py`) - ⚠️ IN-MEMORY

**Status**: Implementasi minimal in-memory

**Yang Ada**:
- ✅ CRUD produk dasar (create, get, list)
- ✅ Toggle Sambatan dengan validasi
- ✅ Validation slot dan deadline

**Gap**:
- ❌ **Tidak tersinkron dengan Supabase** - data disimpan di dictionary
- ❌ Tidak menggunakan tabel `products`, `marketplace_listings`, `product_variants`
- ❌ Tidak ada integrasi dengan brand ownership
- ❌ Tidak ada pencarian teks dan filter kategori
- ❌ Tidak ada pengelolaan stok dan inventory
- ❌ Tidak ada upload gambar produk
- ❌ Tidak ada aroma notes dan metadata

**Rekomendasi**:
```python
# Buat ProductService yang menggunakan Supabase:
class ProductService:
    def __init__(self, supabase_client):
        self.db = supabase_client
    
    async def create_product(self, brand_id: str, data: ProductCreateRequest):
        # Insert ke products table
        # Insert ke marketplace_listings jika enabled
        # Upload images ke Supabase Storage
        
    async def search_products(self, query: str, filters: dict):
        # Full-text search dengan PostgreSQL
        # Filter by category, price, brand
```

**Prioritas**: 🔴 **TINGGI** - Katalog marketplace tidak berfungsi tanpa ini

---

### 3.3 Order Service - ❌ TIDAK ADA

**Status**: **Belum diimplementasikan sama sekali**

**Yang Diperlukan (sesuai PRD §4.1, §4.5)**:
- ❌ Order creation service
- ❌ Cart management (add, remove, update quantity)
- ❌ Checkout flow dengan address validation
- ❌ Order status management (Draft → Diproses → Dikirim → Selesai → Dibatalkan)
- ❌ Order tracking dengan resi pengiriman
- ❌ Order history untuk pembeli dan operator

**Rekomendasi**:
```python
# Buat file: src/app/services/orders.py
class OrderService:
    async def create_order(self, customer_id, items, shipping_address):
        # Validasi stok
        # Hitung subtotal dan shipping
        # Insert ke orders, order_items, order_shipping_addresses
        # Reserve inventory
        # Return order dengan status 'draft'
    
    async def update_order_status(self, order_id, new_status, actor_id, note):
        # Update order status
        # Log ke order_status_history
        # Trigger notifications
    
    async def add_tracking_number(self, order_id, tracking_number):
        # Update order metadata
        # Notify customer
```

**Prioritas**: 🔴 **KRITIS** - Tanpa ini tidak ada transaksi di marketplace

---

### 3.4 RajaOngkir Integration - ❌ TIDAK ADA

**Status**: **Belum diimplementasikan** (PRD §4.3, §4.5)

**Yang Diperlukan**:
- ❌ Integration dengan RajaOngkir API
- ❌ Cek ongkir berdasarkan origin-destination
- ❌ List provinsi, kota, kecamatan
- ❌ Cost calculation untuk multiple couriers

**Rekomendasi**:
```python
# Buat file: src/app/services/rajaongkir.py
class RajaOngkirService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://pro.rajaongkir.com/api"
    
    async def get_provinces(self):
        # GET /province
        
    async def get_cities(self, province_id: str):
        # GET /city?province={province_id}
        
    async def get_subdistricts(self, city_id: str):
        # GET /subdistrict?city={city_id}
        
    async def calculate_cost(self, origin, destination, weight, courier):
        # POST /cost
        # Return shipping options with estimates
```

**Prioritas**: 🟡 **MEDIUM** - Diperlukan untuk checkout yang realistis

---

### 3.5 Sambatan Service (`src/app/services/sambatan.py`) - ⚠️ IN-MEMORY

**Status**: Business logic ada tapi storage in-memory

**Yang Ada**:
- ✅ Campaign lifecycle management
- ✅ Participant join dengan slot validation
- ✅ Progress calculation
- ✅ Status transitions (draft → active → locked → fulfilled)
- ✅ Refund/payout logic

**Gap**:
- ❌ Tidak tersinkron dengan Supabase
- ❌ Tidak menggunakan tabel `sambatan_campaigns`, `sambatan_participants`
- ❌ Tidak ada audit log ke `sambatan_audit_logs`
- ❌ Tidak ada scheduler untuk deadline checking

**Rekomendasi**:
```python
# Refactor untuk menggunakan Supabase:
class SambatanService:
    async def create_campaign(self, product_id, data):
        # Insert ke sambatan_campaigns
        # Link ke products table
        # Log ke sambatan_audit_logs
    
    async def join_campaign(self, campaign_id, user_id, slots):
        # SELECT FOR UPDATE untuk concurrent safety
        # Insert sambatan_participants
        # Update filled_slots
        # Create sambatan_transactions
```

**Prioritas**: 🟠 **TINGGI** - Fitur unggulan MVP harus persistent

---

### 3.6 Sambatan Scheduler - ❌ TIDAK ADA

**Status**: **Belum ada** (PRD §5.5, §4.4)

**Yang Diperlukan**:
- ❌ Background worker untuk check deadline
- ❌ Auto-lock campaigns saat deadline tercapai
- ❌ Refund processing untuk failed campaigns
- ❌ Payout processing untuk successful campaigns
- ❌ Reminder notifications (80% progress, 1 day before deadline)

**Rekomendasi**:
```python
# Buat file: src/core/scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler

class SambatanScheduler:
    def __init__(self, sambatan_service):
        self.scheduler = AsyncIOScheduler()
        self.service = sambatan_service
    
    def start(self):
        # Check deadlines every 5 minutes
        self.scheduler.add_job(
            self.check_deadlines, 
            'interval', 
            minutes=5
        )
        # Send reminders daily
        self.scheduler.add_job(
            self.send_reminders,
            'cron',
            hour=9
        )
        self.scheduler.start()
    
    async def check_deadlines(self):
        # Find campaigns past deadline
        # Lock if target met
        # Mark as expired if not
    
    async def send_reminders(self):
        # Find campaigns near deadline
        # Notify participants
```

**Prioritas**: 🟠 **TINGGI** - Otomasi kritis untuk Sambatan

---

### 3.7 Reporting Service (`src/app/services/reporting.py`) - ⚠️ IN-MEMORY

**Status**: Struktur ada tapi data dummy

**Yang Ada**:
- ✅ CSV export
- ✅ XLSX export (tanpa library eksternal)
- ✅ Date range filtering

**Gap**:
- ❌ Menggunakan seed data statis, bukan dari database orders
- ❌ Tidak ada export untuk Sambatan reports
- ❌ Tidak ada brand-specific reports

**Rekomendasi**:
```python
# Refactor untuk query real data:
async def get_sales_report(self, start_date, end_date, brand_id=None):
    query = self.db.table('orders') \
        .select('*, order_items(*), order_shipping_addresses(*)') \
        .gte('created_at', start_date) \
        .lte('created_at', end_date)
    
    if brand_id:
        query = query.eq('brand_id', brand_id)
    
    result = await query.execute()
    return result.data
```

**Prioritas**: 🟡 **MEDIUM** - Bisa dikerjakan setelah Order service siap

---

### 3.8 Storage Service (`src/app/services/storage.py`) - ✅ SESUAI

**Status**: Sudah terintegrasi dengan Supabase Storage

**Yang Ada**:
- ✅ Upload ke Supabase Storage bucket
- ✅ Fallback ke local filesystem
- ✅ Secure filename generation
- ✅ MIME type detection

**Rekomendasi**:
✅ **Sudah sesuai PRD** - Tidak perlu perubahan

---

### 3.9 Email Service (`src/app/services/email.py`) - ✅ SESUAI

**Status**: Sudah mendukung magic link dan verification

**Yang Ada**:
- ✅ Email verification flow
- ✅ Postmark integration
- ✅ SMTP fallback
- ✅ Console logging untuk development

**Rekomendasi**:
✅ **Sudah sesuai PRD** - Siap untuk Supabase Auth magic link

---

### 3.10 Brand Service (`src/app/services/brands.py`)

**Status**: Perlu dicek implementasinya

**Yang Diperlukan (PRD §4.1, §4.2)**:
- Brand CRUD dengan owner assignment
- Brand member management (owner, admin, contributor)
- Brand address management (untuk shipping origin)
- Brand verification workflow untuk Nusantarum

---

### 3.11 Profile Service (`src/app/services/profile.py`) - ✅ MOSTLY OK

**Status**: Sudah ada ProfileGateway protocol untuk Supabase

**Yang Ada**:
- ✅ Protocol interface untuk Supabase integration
- ✅ Follow/unfollow functionality
- ✅ Profile stats aggregation
- ✅ Perfumer and brand associations

**Gap**:
- ⚠️ Implementation class perlu dicek apakah sudah ada

---

### 3.12 Nusantarum Service (`src/app/services/nusantarum_service.py`) - ⚠️ PERLU DICEK

**Yang Diperlukan (PRD §4.1, §4.2)**:
- Parfum CRUD dengan link ke products
- Brand directory management
- Perfumer directory management
- Content curation workflow
- Marketplace sync

---

## 4. API Routes - ⚠️ SEBAGIAN ADA

### Yang Sudah Ada
- ✅ `/` - Landing/marketplace catalog (root.py)
- ✅ `/marketplace` - Product listing dengan tabs
- ✅ `/marketplace/products/{slug}` - Product detail
- ✅ `/auth` - Register/login page
- ✅ `/onboarding` - Onboarding flow
- ✅ `/dashboard/brand-owner` - Brand owner dashboard
- ✅ `/dashboard/moderation` - Moderation dashboard
- ✅ API routes untuk brands, sambatan, profile, nusantarum, reports

### Yang Belum Ada
- ❌ `/cart` - Keranjang belanja
- ❌ `/checkout` - Checkout flow
- ❌ `/orders` - Order history
- ❌ `/orders/{order_id}` - Order detail & tracking
- ❌ `/api/cart/*` - Cart management endpoints
- ❌ `/api/orders/*` - Order management endpoints
- ❌ `/api/rajaongkir/*` - Shipping cost calculation

**Rekomendasi**:
```python
# Buat file: src/app/api/routes/cart.py
@router.post("/api/cart/add")
async def add_to_cart(product_id: str, quantity: int):
    # Add item to session cart
    
@router.get("/cart")
async def view_cart(request: Request):
    # Render cart page with items

# Buat file: src/app/api/routes/orders.py
@router.post("/api/orders/create")
async def create_order(items: List[CartItem], address: Address):
    # Create order from cart
    
@router.get("/orders/{order_id}")
async def view_order(order_id: str):
    # Show order detail with tracking
```

**Prioritas**: 🔴 **KRITIS** - Alur belanja tidak lengkap tanpa ini

---

## 5. Frontend Templates - ✅ MOSTLY OK

### Yang Ada
- ✅ `base.html` - Base template dengan glassmorphism
- ✅ `marketplace.html` - Katalog dengan tabs
- ✅ `marketplace_product_detail.html` - Detail produk
- ✅ `auth.html` - Login/register
- ✅ `onboarding.html` - Onboarding flow
- ✅ `pages/dashboard/brand_owner.html`
- ✅ `pages/dashboard/moderation.html`
- ✅ Nusantarum components (8 files)
- ✅ Profile components (10 files)

### Yang Belum Ada (PRD §4.2)
- ❌ `cart.html` - Shopping cart page
- ❌ `checkout.html` - Checkout form dengan address & shipping
- ❌ `order_confirmation.html` - Order success page
- ❌ `order_detail.html` - Order tracking page
- ❌ `order_history.html` - List semua pesanan pengguna

**Prioritas**: 🟠 **TINGGI** - Diperlukan bersamaan dengan Order routes

---

## 6. Configuration & Infrastructure - ⚠️ PERLU PENAMBAHAN

### Yang Ada
- ✅ `Settings` class dengan Supabase keys
- ✅ `Settings` class dengan RajaOngkir key
- ✅ Session middleware
- ✅ Static files mounting
- ✅ CORS middleware
- ✅ Jinja2 templates engine

### Yang Belum Ada
- ❌ Supabase client initialization di app startup
- ❌ Database connection pooling
- ❌ Scheduler initialization untuk background jobs
- ❌ RajaOngkir client initialization

**Rekomendasi**:
```python
# Di src/app/core/application.py tambahkan:

@app.on_event("startup")
async def startup():
    settings = get_settings()
    
    # Initialize Supabase client
    app.state.supabase = create_supabase_client(
        settings.supabase_url,
        settings.supabase_service_role_key
    )
    
    # Initialize RajaOngkir
    app.state.rajaongkir = RajaOngkirService(
        settings.rajaongkir_api_key
    )
    
    # Start Sambatan scheduler
    app.state.scheduler = SambatanScheduler(sambatan_service)
    app.state.scheduler.start()

@app.on_event("shutdown")
async def shutdown():
    app.state.scheduler.shutdown()
```

**Prioritas**: 🔴 **TINGGI** - Foundation untuk semua service lainnya

---

## 7. Missing Components Summary

### Tier 1: KRITIS - MVP tidak bisa jalan tanpa ini
1. ❌ **Order Service** - Transaksi marketplace
2. ❌ **Cart Management** - Keranjang belanja
3. ❌ **Checkout Flow** - Pembelian lengkap
4. ❌ **Products Service refactor** - Dari in-memory ke Supabase
5. ❌ **Auth Service refactor** - Dari in-memory ke Supabase
6. ❌ **Supabase client setup** - Di application startup

### Tier 2: TINGGI - Fitur unggulan MVP
7. ❌ **Sambatan Scheduler** - Otomasi deadline & refund
8. ❌ **Sambatan Service refactor** - Persistent storage
9. ❌ **RajaOngkir Integration** - Shipping cost calculation
10. ❌ **Order Templates** - Cart, Checkout, Order detail pages

### Tier 3: MEDIUM - Enhancement & reporting
11. ❌ **Reporting refactor** - Real data dari orders
12. ⚠️ **Brand Service check** - Pastikan terintegrasi Supabase
13. ⚠️ **Nusantarum Service check** - Pastikan CRUD lengkap

---

## 8. Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
1. Setup Supabase client di application startup
2. Refactor Auth Service → gunakan `auth_accounts` table
3. Refactor Products Service → gunakan `products` & `marketplace_listings`
4. Setup RajaOngkir client

### Phase 2: Core Shopping Flow (Week 3-4)
5. Implement Cart Service & routes
6. Implement Order Service dengan status management
7. Implement Checkout flow dengan address & shipping
8. Create cart, checkout, order templates

### Phase 3: Sambatan Enhancement (Week 5)
9. Refactor Sambatan Service → persistent storage
10. Implement Sambatan Scheduler untuk background jobs
11. Test full Sambatan lifecycle end-to-end

### Phase 4: Reporting & Polish (Week 6-7)
12. Refactor Reporting Service → real order data
13. Implement brand-specific reports
14. UAT & bug fixes

---

## 9. Kesimpulan

### Temuan Utama
1. **Database schema sudah sangat baik** ✅ - Tidak perlu perubahan
2. **Service layer 40% masih in-memory** ⚠️ - Perlu refactor ke Supabase
3. **Order & Cart management 0%** ❌ - Belum ada implementasi
4. **RajaOngkir integration 0%** ❌ - Belum ada implementasi
5. **Sambatan Scheduler 0%** ❌ - Belum ada background worker

### Risiko Jika Tidak Diperbaiki
- 🔴 **KRITIS**: Marketplace tidak bisa digunakan untuk transaksi nyata
- 🔴 **KRITIS**: Data user hilang saat restart aplikasi
- 🟠 **TINGGI**: Sambatan tidak otomatis, butuh manual intervention
- 🟡 **MEDIUM**: Shipping cost tidak akurat tanpa RajaOngkir

### Next Steps
1. Review dokumen ini dengan tim
2. Prioritaskan implementasi Tier 1 (Order & Auth)
3. Buat tiket untuk setiap komponen yang missing
4. Mulai Phase 1 implementation roadmap

---

**Document Owner**: Architecture Review Team  
**Last Updated**: 2025-10-05  
**Next Review**: Setelah Phase 1 selesai
