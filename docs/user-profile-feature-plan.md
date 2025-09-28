# Rencana Implementasi Halaman Profil Pengguna Sensasiwangi.id

## 1. Tujuan & Sasaran Pengalaman
- Menyediakan halaman profil yang mencerminkan identitas pengguna layaknya sosial media (avatar, bio singkat, daftar produk favorit/aktivitas).
- Menghadirkan interaksi follow/unfollow antar pengguna marketplace untuk memunculkan jejaring komunitas.
- Menandai kredibilitas pengguna melalui badge **Perfumer** (ditag oleh produk) dan **Brand Owner** (memiliki/mengelola brand) berikut daftar produk/brand terkait.
- Menjaga konsistensi tema glassmorphism dan pola SSR + HTMX agar sesuai pedoman UI yang sudah ada.

## 2. Gambaran Pengalaman Pengguna
1. **Header Profil**
   - Avatar, nama lengkap, preferensi aroma, tombol edit (jika pemilik profil) atau tombol Follow/Unfollow (jika pengunjung lain).
   - Badges ditampilkan sebagai chip kaca (ikon + label) dengan tooltip yang menjelaskan sumber lencana.
2. **Statistik Komunitas**
   - Counter follower, following, dan jumlah produk racikan (perfumer) serta brand yang dimiliki (owner).
   - Klik pada angka membuka modal HTMX dengan daftar pengguna terkait.
3. **Seksyen Konten**
   - Tab `Aktivitas`, `Favorit`, `Sambatan`, `Karya Perfumer`, `Brand Dimiliki`.
   - Tab baru `Karya Perfumer` menampilkan daftar produk di mana user ditandai sebagai perfumer (grid card reusable dari marketplace).
   - Tab `Brand Dimiliki` menampilkan kartu brand (logo + CTA kunjungi) untuk brand yang mereka miliki/ditandai owner.
4. **Aksi Follow/Unfollow**
   - Tombol follow menggunakan HTMX POST ke endpoint follow dan swap state ke `Mengikuti`.
   - HTMX juga memperbarui counter follower tanpa refresh halaman penuh.
5. **Empty State**
   - Jika belum memiliki badge, tampilkan ilustrasi/teks ajakan kolaborasi.
   - Untuk `Karya Perfumer` kosong: ajak brand untuk menandai perfumer.

## 3. Kebutuhan Data & Skema Supabase
### 3.1 Relasi Follow
- **Tabel baru `user_follows`**
  ```sql
  create table user_follows (
      follower_id uuid references user_profiles(id) on delete cascade,
      following_id uuid references user_profiles(id) on delete cascade,
      created_at timestamptz default timezone('utc', now()),
      primary key (follower_id, following_id)
  );
  create index idx_user_follows_following on user_follows(following_id);
  create index idx_user_follows_follower on user_follows(follower_id);
  ```
- Trigger validasi untuk mencegah self-follow dan menjaga audit log (opsional: tambahkan constraint `check (follower_id <> following_id)`).

### 3.2 Tag Perfumer pada Produk
- **Tabel baru `product_perfumers`** untuk mapping banyak-ke-banyak antara produk dan perfumer.
  ```sql
  create table product_perfumers (
      product_id uuid not null references products(id) on delete cascade,
      perfumer_profile_id uuid not null references user_profiles(id) on delete cascade,
      role text default 'lead', -- menampung role tambahan jika dibutuhkan kelak
      assigned_by uuid references user_profiles(id),
      assigned_at timestamptz default timezone('utc', now()),
      primary key (product_id, perfumer_profile_id)
  );
  ```
- Opsional: tambahkan kolom `notes` untuk catatan brand.
- Supabase RLS (nanti) memastikan hanya brand owner/admin yang dapat menandai perfumer untuk produk mereka.

### 3.3 Penanda Brand Owner
- Memanfaatkan tabel `brand_members` yang sudah ada dengan `role = 'owner'`.
- Siapkan **view `profile_brand_summary`** untuk mengambil daftar brand dan peran pengguna.
  ```sql
  create or replace view profile_brand_summary as
  select
      bm.profile_id,
      b.id as brand_id,
      b.name,
      b.slug,
      b.logo_path,
      bm.role
  from brand_members bm
  join brands b on b.id = bm.brand_id
  where bm.role in ('owner','admin'); -- owner untuk badge, admin untuk daftar brand dimiliki
  ```
- Badge Brand Owner diberikan jika ada minimal satu record dengan `role = 'owner'`.

### 3.4 Statistik Profil
- View agregasi untuk memudahkan rendering cepat di SSR:
  ```sql
  create or replace view user_profile_stats as
  select
      p.id as profile_id,
      count(distinct f.following_id) filter (where f.follower_id = p.id) as following_count,
      count(distinct f.follower_id) filter (where f.following_id = p.id) as follower_count,
      count(distinct pp.product_id) as perfumer_product_count,
      count(distinct case when bm.role = 'owner' then bm.brand_id end) as owned_brand_count
  from user_profiles p
  left join user_follows f on f.follower_id = p.id or f.following_id = p.id
  left join product_perfumers pp on pp.perfumer_profile_id = p.id
  left join brand_members bm on bm.profile_id = p.id
  group by p.id;
  ```
- Alternatif: gunakan materialized view + trigger refresh jika performa dibutuhkan.

## 4. API & Layanan Backend
### 4.1 Endpoint Profil
- `GET /profile/{username_or_id}`
  - Mengembalikan data profil, stats, badges, list produk perfumer (batasi pagination), brand dimiliki.
  - Response JSON untuk HTMX partial (header + body) serta full SSR render.
- `GET /profile/{id}/followers` & `/following` untuk modal daftar.
- `GET /profile/{id}/perfumer-products` & `/owned-brands` untuk tab HTMX.

### 4.2 Endpoint Follow
- `POST /profile/{id}/follow`
  - Auth required, cek self-follow dan duplikasi.
  - Insert ke `user_follows`, balas status success + snippet HTML untuk tombol.
- `DELETE /profile/{id}/follow`
  - Menghapus relasi.
- Endpoint disertai rate limit ringan (middleware) guna cegah spam.

### 4.3 Service Layer
- Tambahkan `ProfileService` di `src/app/services/profile.py`:
  - `get_profile(profile_id, viewer_id)` mengembalikan dictionary untuk template (profil, stats, badges, viewer_status).
  - `follow_profile`, `unfollow_profile` (mengelola transaksional).
  - `list_perfumer_products(profile_id, pagination)` dan `list_owned_brands(profile_id)`.
- Update dependency injection pada router profile.

## 5. Rencana Implementasi Frontend (Jinja2 + HTMX)
1. **Template Baru** `templates/pages/profile/detail.html`
   - Menggunakan layout base, memuat header, stats, tab container.
2. **Partial Components**
   - `components/profile-badge.html`: modul badge reusable.
   - `components/profile-stats.html`: modul counter.
   - `components/profile-follow-button.html`: state follow/unfollow.
   - Reuse `components/product-card.html` (ketika tersedia) untuk grid `Karya Perfumer`.
   - `components/brand-card.html` (baru) untuk brand list.
3. **HTMX Hooks**
   - `hx-post` dan `hx-delete` pada tombol follow, target swap area.
   - Tabs memanfaatkan `hx-get` untuk memuat konten per view (list followers, products, brand) agar lazy load.
4. **Styling**
   - CSS utilitas: `.badge-perfumer`, `.badge-brand-owner` memanfaatkan glass gradient oranye/ungu sesuai identitas.
   - Pastikan responsive (stack pada mobile, grid 2 kolom minimal 320px).

## 6. Integrasi Badge & Listing
- **Perfumer Badge**: logic backend mengecek `product_perfumers` > 0. Tampilkan label "Perfumer" + jumlah produk.
- **Brand Owner Badge**: cek `brand_members.role = 'owner'`. Sertakan link CTA "Kelola Brand" jika viewer = owner.
- Pada tab `Karya Perfumer`, tampilkan meta `Diracik untuk {brand}` + status sambatan jika ada.
- Tab `Brand Dimiliki` memanfaatkan data brand (logo, tagline singkat, status). Tampilkan badge status brand (draft/active) untuk owner sendiri.

## 7. Migrasi & Deployment
1. Buat migration Supabase baru menambahkan tabel `user_follows`, `product_perfumers`, view `user_profile_stats`, `profile_brand_summary`.
2. Tambahkan seed/dev data pada `supabase/seed/` (jika ada) untuk contoh perfumer & brand owner.
3. Update dokumentasi RLS untuk tabel baru (brand owner/perfumer assignment).
4. Pastikan `verify_supabase_migration.py` diperbarui jika memerlukan validasi.

## 8. QA & Monitoring
- Unit test service: follow/unfollow toggles, stats aggregator, permission (self follow).
- Integration test HTMX: response snippet follow button & stats update.
- Visual QA: periksa badge kontras & responsive state.
- Analitik: log event `profile_follow` dan `profile_badge_view` (opsional) untuk metrik komunitas.

## 9. Roadmap Lanjutan
- Menambahkan rekomendasi perfumer/brand di sidebar profil.
- Notifikasi ketika user baru mengikuti atau produk menandai perfumer.
- Opsi private profile (perlu field tambahan).
- Sinkronisasi badge ke modul Nusantarum (link ke cerita perfumer).
