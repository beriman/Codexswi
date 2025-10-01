# Nusantarum – Ensiklopedia Aroma SensasiWangi.id

Dokumen ini mendeskripsikan fitur Nusantarum secara menyeluruh—mulai dari tujuan produk, arsitektur UI, alur data, hingga kebutuhan teknis dan operasional. Dokumentasi disusun agar dapat dijadikan referensi tunggal untuk tim produk, desain, dan engineering ketika membangun atau memelihara halaman `/nusantarum`.

---

## 1. Tujuan Produk dan Nilai Utama

- **Elevasi komunitas parfum lokal** – Menjadi etalase utama untuk menampilkan perfumer dan brand lokal yang terkurasi.
- **Kemudahan penemuan** – Menyediakan satu pengalaman pencarian lintas entitas (perfumer, brand, parfum) sehingga pengguna tidak perlu berpindah halaman.
- **Legitimasi bagi kreator** – Memberikan badge "Terverifikasi" sebagai bentuk pengakuan setelah melewati proses kurasi manual.
- **Kredibilitas platform** – Memastikan hanya profil autentik yang muncul sehingga reputasi SensasiWangi terjaga.

### 1.1 Sasaran Pengguna

| Segment | Kebutuhan | Nilai yang Diberikan |
| --- | --- | --- |
| Pengunjung umum | Menemukan referensi parfum lokal tepercaya | Pencarian terpadu, filter terstruktur, akses cepat ke profil & produk |
| Perfumer & brand | Mendapatkan pengakuan serta visibilitas | Badge kurasi, tautan ke profil lengkap, statistik eksposur |
| Tim internal SensasiWangi | Mengelola proses kurasi | Dashboard admin, status kurasi, audit log |

### 1.2 Indikator Keberhasilan

- Meningkatnya jumlah profil terkurasi (perfumer/brand) dari waktu ke waktu.
- Peningkatan rasio klik ke profil (`View Profile`) dan produk dari halaman `/nusantarum`.
- Tingkat konversi pengajuan kurasi menjadi persetujuan yang terdokumentasi.
- Feedback pengguna yang menunjukkan kepercayaan terhadap kurasi Nusantarum.

---

## 2. Struktur Halaman `/nusantarum`

### 2.1 Header & Hero Section

- Menggunakan `AppHeader` global sebagai navigasi utama beserta CTA login/daftar.
- Hero memuat judul utama **"Nusantarum"** dan subjudul satu kalimat yang menegaskan peran sebagai ensiklopedia aroma lokal.
- Background menerapkan estetika **glassmorphism**: kombinasi `bg-card/60`, `backdrop-blur-lg`, `border border-white/20`, dan `shadow-glow` untuk menegaskan kesan premium.
- Menyediakan teks penjelas singkat (2–3 kalimat) mengenai manfaat halaman, serta angka ringkas (misal jumlah perfumer terkurasi) apabila data tersedia.

### 2.2 Bilah Pencarian Global

- Ditempatkan tepat di bawah hero, dengan label placeholder "Cari perfumer, brand, atau parfum…".
- Input tunggal yang memicu pencarian lintas entitas secara real-time (debounce ±300ms untuk performa).
- Menyimpan kata kunci pada state global (React context/Zustand) agar konsisten ketika pengguna berpindah tab.
- Mendukung keyboard shortcut `/` untuk fokus ke kolom pencarian dan `Esc` untuk menghapus input.

### 2.3 Tabs Navigasi

- Menggunakan komponen `Tabs` ShadCN dengan opsi: **Perfumers**, **Brands**, **Parfums**.
- Tab aktif memperoleh gaya gradien `bg-accent-gradient` dan border terang agar kontras dengan panel glassmorphism.
- State tab tersimpan di query string `?tab=perfumers|brands|parfums` sehingga shareable dan mudah diuji QA.
- Setiap tab memuat ringkasan jumlah item yang lolos filter (misal badge kecil "24" di sebelah label tab).

---

## 3. Konten Per Tab

### 3.1 Tab **Perfumers**

- Menampilkan grid responsif dari komponen `PerfumerCard`.
- Layout responsif:
  - 1 kolom pada `<640px` (mobile),
  - 2 kolom pada `640–1024px`,
  - 3 kolom pada `>1024px`.
- Isi kartu mencakup:
  - Avatar perfumer (fallback inisial bila kosong).
  - Nama lengkap, `@username`, dan kota asal jika tersedia.
  - Bio singkat maksimal 120 karakter dengan ellipsis otomatis.
  - Statistik: jumlah parfum yang dirilis, jumlah follower, dan tahun aktif.
  - Badge `BadgeCheck` bertuliskan **"Terverifikasi"** apabila `isCurated: true`.
  - Tombol `View Profile` (variant `ghost`) yang menaut ke `/profile/[slug]`.
- Empty state: ilustrasi ringan + teks "Belum ada perfumer yang cocok dengan pencarian Anda" + tautan ajakan untuk menjelajah semua perfumer.

### 3.2 Tab **Brands**

- Menggunakan komponen kartu dengan struktur serupa, namun label menggambarkan identitas brand.
- Field utama: logo, nama brand, `@username`, tagline singkat, jumlah parfum yang tersedia, dan status kurasi.
- Jika brand memiliki web eksternal, tampilkan ikon tautan di kartu (membuka tab baru).
- Memastikan kartu menampilkan `PerfumerCard` versi `type="brand"` agar styling konsisten namun copywriting menyesuaikan (misal CTA `View Brand`).

### 3.3 Tab **Parfums**

- Ditampilkan dalam komponen `DataTable` dengan fitur sort dan pagination.
- Kolom default:
  1. **Nama Parfum** (link ke `/products/[id]`).
  2. **Brand** (link sekunder ke `/profile/[brandSlug]`).
  3. **Profil Aroma** (kumpulan `Badge` kecil: "Floral", "Woody", dll).
  4. **Tahun Rilis** (opsional, sort ascending/descending).
- Mendukung pencarian global dan filter tambahan:
  - Filter dropdown "Kategori Aroma".
  - Toggle "Tersedia di marketplace" bila informasi stock diintegrasikan.
- Empty state menampilkan rekomendasi pencarian populer.

---

## 4. Sistem Kurasi Nusantarum

### 4.1 Pengajuan Kurasi

- Di halaman profil (`/profile/[slug]`), pemilik akun bertipe *Perfumer* atau *Brand* menekan tombol **"Ajukan Kurasi"**.
- Tombol dirender hanya jika:
  - Pengguna yang sedang login adalah pemilik profil,
  - `isCurated === false`,
  - Profil memenuhi syarat minimum (misal: minimal 1 produk terdaftar, informasi profil lengkap).
- Klik tombol memicu `CurationDialog`.

### 4.2 Dialog `CurationDialog`

- Formulir berisi:
  - Textarea "Cerita & Filosofi" (wajib minimal 200 karakter).
  - Upload bukti (opsional) seperti sertifikat atau foto workshop.
  - Checkbox persetujuan syarat & ketentuan.
- Setelah submit, data disimpan ke tabel `curation_requests` dengan status awal `pending` dan timestamp.
- Pengguna menerima snackbar konfirmasi serta email otomatis (via Supabase Function) mengenai estimasi waktu kurasi.

### 4.3 Peninjauan Manual

- Kurator mengakses panel admin untuk meninjau daftar `pending`.
- Aksi yang tersedia: `approve`, `reject`, `request_revision`.
- Keputusan memicu notifikasi email ke pemilik profil dan pencatatan audit log (ID kurator, catatan keputusan).

### 4.4 Publikasi Badge & Sinkronisasi

- Jika disetujui, sistem:
  1. Mengubah `profiles.isCurated` menjadi `true`.
  2. Menambahkan entri ke `badge_awards` dengan tipe `nusantarum_verified`.
  3. Mengirim webhook ke sistem eksternal (bila ada) untuk sinkron status.
- UI `/nusantarum` otomatis menampilkan badge melalui refetch data atau subscription real-time Supabase.
- Penolakan/revisi ditampilkan di profil pemilik dengan status dan catatan kurator.

---

## 5. Integrasi dengan Fitur Lain

- **Halaman Profil** – CTA `View Profile` dari tab perfumer & brand mengarah ke profil untuk aksi lanjut (follow, lihat katalog produk, hubungi).
- **Halaman Produk** – Baris pada tabel parfum menuju halaman detail produk (`/products/[id]`), memperkuat funnel eksplorasi ke pembelian.
- **Panel Admin** – Menjadi pusat pengelolaan kurasi, memanfaatkan data `curation_requests` dan `profiles`.
- **Sistem Lencana** – Badge "Nusantarum Verified" dipakai di seluruh halaman (profil, kartu rekomendasi, hasil pencarian global) untuk menjaga konsistensi identitas.
- **Analitik** – Event tracking (misal via Segment/GA) untuk `search`, `view_profile_click`, `curation_submit`, `tab_switch` guna mengukur penggunaan.

---

## 6. Perspektif Teknis & Alur Data

### 6.1 Arsitektur Frontend

- Framework utama: Next.js (App Router) dengan Tailwind dan komponen ShadCN.
- State global menggunakan Zustand untuk menyimpan kata kunci pencarian, tab aktif, dan preferensi tampilan.
- Data di-fetch melalui Supabase client atau endpoint REST internal dengan pagination (limit 12 untuk kartu, 25 untuk tabel).
- Implementasi pencarian memakai parameter query `search` yang dikirim ke Supabase `ilike` filter di kolom nama, username, dan deskripsi.

### 6.2 Model Data (Supabase)

```
profiles (
  id UUID PK,
  slug TEXT UNIQUE,
  type ENUM('perfumer','brand'),
  display_name TEXT,
  username TEXT,
  bio TEXT,
  city TEXT,
  avatar_url TEXT,
  is_curated BOOLEAN,
  stats JSONB -- { followers: number, perfumes: number }
)

products (
  id UUID PK,
  name TEXT,
  brand_id UUID FK -> profiles.id,
  aroma_profiles TEXT[]
)

curation_requests (
  id UUID PK,
  profile_id UUID FK -> profiles.id,
  status ENUM('pending','approved','rejected','revision'),
  statement TEXT,
  attachments JSONB,
  reviewer_id UUID,
  reviewed_at TIMESTAMP
)
```

### 6.3 Alur Data Pencarian

1. Pengguna mengetik di bilah pencarian → state global `searchQuery` diperbarui.
2. Hook `useDebouncedValue` men-trigger `useQuery` untuk tab aktif.
3. Query Supabase mem-filter berdasarkan kata kunci dan menerapkan pagination.
4. Hasil disimpan di cache React Query untuk reuse ketika tab berpindah.
5. Saat pengguna ganti tab, data diambil dari cache atau difetch ulang jika parameter berubah.

### 6.4 Performa & Aksesibilitas

- Lazy load gambar avatar/logo dengan `next/image` dan blur placeholder.
- Gunakan skeleton loader untuk kartu & tabel selama menunggu data.
- Kontras warna badge diverifikasi memenuhi rasio aksesibilitas WCAG (≥ 4.5:1).
- Navigasi keyboard: tab order logis, fokus jelas, tab list mengikuti `role="tablist"`.

---

## 7. Edge Case & Error Handling

- **Data Kosong** – Tampilkan empty state yang edukatif dengan CTA untuk menghapus filter.
- **Koneksi Gagal** – Munculkan `Alert` pada area konten dengan opsi retry.
- **Profil Tanpa Avatar** – Gunakan fallback inisial agar tampilan tetap konsisten.
- **Perfumer/Brand Nonaktif** – Jika status `isActive` false, jangan tampilkan di `/nusantarum` meski lolos kurasi.
- **Pengajuan Duplikat** – Validasi agar hanya satu `curation_requests` berstatus `pending` per profil.
- **Pencarian Tanpa Hasil** – Simpan histori pencarian pengguna untuk menawarkan rekomendasi lain.

---

## 8. Rencana Pengembangan Bertahap

| Tahap | Fokus | Deliverables |
| --- | --- | --- |
| V1 (MVP) | Peluncuran ensiklopedia dasar | Tabs, pencarian lintas entitas, badge verifikasi pasif |
| V2 | Kurasi interaktif | Form `CurationDialog`, integrasi admin panel, notifikasi email |
| V3 | Personalisasi | Rekomendasi berdasarkan histori, filter tambahan aroma, analytics dashboard |
| V4 | Komunitas | Ulasan user, kolaborasi perfumer-brand, program ambassador |

---

## 9. Dampak Pengalaman Pengguna

- **Pengguna umum**: Eksplorasi intuitif dan tepercaya karena kurasi manual serta badge verifikasi yang jelas.
- **Perfumer/brand**: Jalur resmi memperoleh pengakuan meningkatkan legitimasi dan visibilitas di ekosistem SensasiWangi.
- **Tim SensasiWangi**: Mendapat proses kurasi yang terdokumentasi, memudahkan pemantauan kualitas dan evaluasi program.

Dokumen ini harus diperbarui secara berkala seiring evolusi fitur Nusantarum, termasuk penambahan metrik baru, iterasi desain, ataupun integrasi teknologi terbaru.

