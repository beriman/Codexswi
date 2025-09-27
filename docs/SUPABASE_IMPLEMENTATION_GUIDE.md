# Panduan Implementasi Supabase

Dokumen ini menjelaskan cara mensinkronkan skema database Supabase untuk
Sensasiwangi.id menggunakan file migrasi yang tersimpan di repositori.
Struktur mengikuti kebutuhan modul marketplace, Sambatan, onboarding, dan
konten Nusantarum sebagaimana dijelaskan pada PRD.

## Prasyarat

1. **Supabase CLI** versi 1.153 atau lebih baru terinstal.
2. Akses ke proyek Supabase (URL dan API key). Untuk lingkungan pengujian yang
   disediakan product team, gunakan:

   - Project URL: `https://yguckgrnvzvbxtygbzke.supabase.co`
   - Anon public API key: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlndWNrZ3Judnp2Ynh0eWdiemtlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTg5Mzg0NTIsImV4cCI6MjA3NDUxNDQ1Mn0.psMSy6vys-6rEKzJbUmX87j9zmB6dE94zc1_nVakuLU`

   Untuk menjalankan migrasi schema diperlukan **service role key**. Simpan key
   tersebut sebagai variabel lingkungan `SUPABASE_SERVICE_ROLE_KEY` di mesin
   lokal atau CI. Jangan commit key ke repository publik.

3. `psql` (PostgreSQL client) bila ingin menerapkan migrasi secara manual.

## Struktur Direktori

```
supabase/
└── migrations/
    └── 0001_initial_schema.sql
```

File `0001_initial_schema.sql` berisi DDL lengkap untuk tabel, enum, index, dan
view yang dibutuhkan modul MVP. Migrasi tambahan dapat ditambahkan dengan
penamaan berurutan (`0002_*.sql`, dst.).

## Ringkasan Skema Domain

- **Marketplace produk reguler**
  - `products` menyimpan metadata produk lintas channel dengan flag
    `marketplace_enabled` dan `sambatan_enabled` untuk mengaktifkan mode jualan.
  - `marketplace_listings` memegang detail listing reguler (harga, stok,
    channel, profil pengiriman) dan otomatis memperbarui `updated_at` via
    trigger.
  - `product_variants`, `product_images`, `product_history`, serta
    `marketplace_inventory_adjustments` membantu pengelolaan varian, media,
    audit status, dan mutasi stok reguler.
  - `orders` dan `order_items` menggunakan enum `order_channel` untuk membedakan
    item reguler (`marketplace`) dan Sambatan (`sambatan`). Satu pesanan dapat
    menjadi `mixed` jika berisi kedua jenis item.
- **Sambatan (group-buy)**
  - `sambatan_campaigns` memisahkan konfigurasi batch (slot, harga slot,
    deadline, status) dari tabel produk reguler sehingga satu produk bisa aktif
    di marketplace dan Sambatan secara terkontrol.
  - `sambatan_participants`, `sambatan_transactions`, `sambatan_audit_logs`, dan
    `sambatan_lifecycle_states` terhubung ke `sambatan_campaigns` untuk
    memastikan semua catatan partisipasi, finansial, dan audit merujuk ke batch
    tertentu.
  - `order_items` menyimpan relasi `campaign_id` serta snapshot deadline untuk
    Sambatan, sekaligus menegakkan aturan lewat constraint bahwa item Sambatan
    wajib memiliki `sambatan_slot_count`.
  - View `sambatan_dashboard_summary` merangkum progres kampanye (slot, total
    kontribusi, aktivitas terakhir) untuk dashboard operasional.
- **Onboarding & konten**: tetap mengikuti definisi sebelumnya (profil pengguna,
  brand, artikel Nusantarum, relasi artikel-brand-produk).

Dengan struktur ini database siap menampung alur marketplace reguler maupun
Sambatan tanpa tumpang tindih kolom dan dengan indeks yang mendukung laporan
operasional.

## Menjalankan Migrasi Menggunakan Supabase CLI

1. **Set variabel lingkungan**:

   ```bash
   export SUPABASE_DB_URL="postgresql://postgres:<SERVICE_ROLE_KEY>@db.yguckgrnvzvbxtygbzke.supabase.co:5432/postgres"
   export SUPABASE_ACCESS_TOKEN="<SERVICE_ROLE_KEY>"
   ```

   Ganti `<SERVICE_ROLE_KEY>` dengan service role key yang valid.

2. **Jalankan migrasi** menggunakan perintah bawaan CLI:

   ```bash
   supabase db push --db-url "$SUPABASE_DB_URL" --file supabase/migrations/0001_initial_schema.sql
   ```

   Perintah di atas akan menerapkan seluruh DDL pada database target. Tambahkan
   flag `--dry-run` untuk melihat rencana eksekusi tanpa mengubah database.

3. **Verifikasi** tabel dan enum telah terbentuk:

   ```bash
   supabase db remote commit --db-url "$SUPABASE_DB_URL" --schema public --out supabase/schema_snapshot.sql
   ```

   Bandingkan file snapshot dengan migrasi untuk memastikan konsistensi.

## Menjalankan Migrasi Manual via psql

Sebagai alternatif, jalankan file SQL langsung menggunakan `psql`:

```bash
PGPASSWORD=<SERVICE_ROLE_KEY> psql \
  -h db.yguckgrnvzvbxtygbzke.supabase.co \
  -p 5432 \
  -U postgres \
  -d postgres \
  -f supabase/migrations/0001_initial_schema.sql
```

## Langkah Lanjutan

- Tambahkan migrasi baru untuk perubahan skema berikutnya dan commit ke repositori.
- Gunakan skrip CI/CD untuk menjalankan migrasi otomatis saat deployment.
- Setelah skema siap, seed data referensi tambahan (mis. daftar aroma) menggunakan
  file SQL terpisah di folder `supabase/seeds/`.

