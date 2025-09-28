# Rencana Implementasi Nusantarum

## 1. Visi Produk & Sasaran
- Menyediakan basis data terpadu parfum lokal Indonesia (produk, brand, perfumer) yang terhubung dengan marketplace Sensasiwangi dan profil komunitas.
- Menjadi referensi edukatif bagi pengguna serta alat kurasi bagi tim internal untuk mengelola katalog.
- Memastikan data sinkron otomatis dengan inventori marketplace dan metadata profil brand/user agar tidak terjadi duplikasi input.

## 2. Gambaran Pengalaman Pengguna
1. **Struktur Halaman**
   - Layout SSR dengan tema glassmorphism dan komponen yang konsisten dengan panduan UI/UX.
   - Header minimalis berisi judul halaman dan search bar global tanpa CTA tambahan.
   - Konten utama berupa list vertikal pada tiga tab HTMX (parfum, brand, perfumer); elemen visual (foto produk, logo, atau foto profil) hanya muncul ketika pengguna melakukan hover pada item list.
   - Tiga tab utama menggunakan HTMX untuk loading konten parsial tanpa refresh:
     - `Parfum`: list parfum (nama, brand, perfumer, rating marketplace) dari brand yang telah terverifikasi.
     - `Brand`: list brand terverifikasi beserta kota asal dan jumlah parfum aktif.
     - `Perfumer`: list perfumer yang telah ditandai pada parfum aktif, lengkap dengan highlight signature scent saat di-hover.
2. **Fitur Pencarian & Filter**
   - Search bar global yang memanggil endpoint `/nusantarum/search` dengan query.
   - Filter panel (aroma families, lokasi, kisaran harga) dengan HTMX toggle chips dan opsi filter status verifikasi (default: hanya data terverifikasi).
3. **Sinkronisasi Data**
   - Lencana (badge) menandai data hasil sinkron vs input manual.
   - Timestamp update terakhir per entitas + status sinkronisasi.
   - Validasi status `verified` pada brand sebelum parfum atau perfumer terkait ditampilkan.
4. **Empty/Error State**
   - Pesan kurasi manual jika data belum tersedia, tanpa CTA tambahan; arahkan pengguna ke pencarian atau filter lain.

## 3. Arsitektur Data & Supabase
### 3.1 Entitas Inti
- **parfums**: metadata parfum (nama, deskripsi, catatan, harga referensi, brand_id, perfumer_id, marketplace_product_id) dengan flag turunan `is_displayable` yang hanya true jika brand terasosiasi terverifikasi.
- **brands**: rujukan ke tabel marketplace `brands` (reuse jika sudah ada, atau view join) dengan kolom tambahan `nusantarum_status` dan flag `is_verified`.
- **perfumers**: profil perfumer (terhubung ke `user_profiles` jika mereka punya akun) dan kolom `is_linked_to_active_perfume` untuk memastikan hanya perfumer yang ditandai pada parfum aktif yang tampil.
- **perfume_notes**: tabel child untuk top/middle/base notes.
- **perfume_assets**: foto tambahan & dokumen.

### 3.2 Integrasi Marketplace
- Tambahkan kolom `marketplace_product_id` pada `parfums` untuk mapping ke produk marketplace.
- Buat **view** `marketplace_product_snapshot` yang mengambil stok/harga terkini (read-only) agar halaman selalu up-to-date.
- Gunakan Supabase Function terjadwal (cron) `sync_marketplace_products()` untuk menarik data baru (melalui REST/RPC yang sudah ada).
- Simpan riwayat sinkronisasi di tabel `sync_logs`.

### 3.3 Integrasi Profil Brand & User
- Kolom `brand_profile_id` pada `brands` yang referensi ke `brand_profiles` (atau `user_profiles` dengan role brand owner).
- Kolom `perfumer_profile_id` pada `perfumers` yang referensi ke `user_profiles`.
- View `perfumer_showcase` menggabungkan parfum besutan perfumer untuk halaman profil dan hanya memuat data dari brand terverifikasi.
- Trigger Supabase untuk update otomatis status badge Perfumer/Brand Owner bila ada relasi baru dan memelihara flag `is_verified`.

### 3.4 RLS & Akses Data
- Mode publik read-only menggunakan policy `select` terbuka.
- Insert/update dibatasi untuk admin kurator atau brand owner terkait.
- Audit log di tabel `parfum_audits` untuk melacak perubahan manual.

## 4. Layanan Backend & API
1. **Router `nusantarum`** (`src/app/routers/nusantarum.py`)
   - Endpoint `GET /nusantarum` untuk SSR halaman utama (memuat default tab parfum).
   - Endpoint `GET /nusantarum/tab/{slug}` untuk HTMX partial (parfum/brand/perfumer) dengan pagination & filter.
   - Endpoint `GET /nusantarum/search` untuk autocomplete/search suggestions.
2. **Service Layer** (`src/app/services/nusantarum_service.py`)
   - Fungsi `list_perfumes`, `list_brands`, `list_perfumers` dengan caching (Redis) untuk query umum dan parameter default `verified_only=True`.
   - Fungsi `get_sync_status` memanggil Supabase RPC/logs.
3. **Background Jobs**
   - Worker (Celery/RQ) `sync_nusantarum_marketplace` menjalankan fungsi Supabase + injest media serta memperbarui status verifikasi brand.
   - Worker `sync_nusantarum_profiles` memastikan perubahan profil brand/perfumer ikut memperbarui deskripsi & avatar, serta memvalidasi bahwa perfumer hanya ditampilkan bila memiliki relasi parfum aktif.

## 5. Rencana Implementasi Frontend
1. **Template**
   - `templates/pages/nusantarum/index.html`: layout utama dengan header minimalis dan tab container.
   - Partial `templates/components/nusantarum/perfume-list-item.html`, `brand-list-item.html`, `perfumer-list-item.html` dengan struktur list dan state hover untuk menampilkan gambar.
   - Partial `templates/components/nusantarum/filter-panel.html` untuk filter aroma & lokasi serta status verifikasi.
2. **Interaksi HTMX**
   - Tab button `hx-get` ke `/nusantarum/tab/{slug}` dan swap ke container.
   - Filter chips memicu request HTMX dengan query param.
   - Search bar menggunakan `hx-post` dengan debounce untuk suggestion dropdown.
   - Interaksi hover memicu permintaan HTMX ringan (opsional) untuk memuat media jika belum ada di cache.
3. **State Sinkronisasi**
   - Badge `sync-status` (ikon cloud) menggunakan data binding (HTMX) untuk menampilkan status update.
   - Timestamp update di-render dari view `sync_logs`.
4. **Responsiveness & A11y**
   - Struktur list responsif dengan satu kolom vertikal; spacing diperlebar di desktop.
   - Keyboard navigation untuk tab, filter, dan fokus item list (hover effect diganti focus-visible pada keyboard).

## 6. Integrasi dengan Marketplace & Profil Komunitas
- Item parfum mencantumkan link teks sederhana ke halaman produk marketplace (tanpa CTA button) yang hanya muncul untuk brand terverifikasi.
- Item brand menyertakan link teks ke profil brand SSR marketplace jika status verifikasi terpenuhi.
- Item perfumer memuat link teks ke halaman profil komunitas (menggunakan slug user) hanya jika perfumer terkait parfum aktif.
- Data yang belum memenuhi kriteria verifikasi tidak ditampilkan pada list.

## 7. Observabilitas & Analitik
- Tambah event tracking (`nusantarum_tab_view`, `nusantarum_search`, `nusantarum_hover_media`).
- Dashboard Supabase/Metabase untuk memonitor jumlah parfum terdaftar, status sinkron, dan CTR ke marketplace.

## 8. Roadmap Implementasi
1. **Fase 1 – Fondasi Data (1 sprint)**
   - Definisikan skema Supabase (`parfums`, `perfumers`, `perfume_notes`, relasi brand/perfumer).
   - Buat migrasi, RLS, dan seed awal (import 10 brand & parfum pilot).
   - Siapkan view/sync log dasar.
2. **Fase 2 – Backend & Sync (1 sprint)**
   - Implementasi service + router dasar untuk tab parfum.
   - Integrasi job sinkronisasi marketplace (produk & harga) + profil (logo/avatar).
   - Implement cache + pagination.
3. **Fase 3 – Frontend Tab (1 sprint)**
   - Kembangkan template & partial + interaksi HTMX untuk ketiga tab.
   - Implement filter & search, state sinkronisasi.
   - QA tampilan responsive dan accessibility.
4. **Fase 4 – Peluncuran & Iterasi (ongoing)**
   - Tambah konten editorial (artikel parfum/brand).
   - Kumpulkan feedback pengguna, perbaiki bug, optimasi performa query.
   - Rencana jangka panjang: API publik untuk partner.
