# Sensasiwangi.id MVP Workspace

Repositori ini memuat dokumen dan kode awal pengembangan untuk proyek
**Sensasiwangi.id**, platform wewangian lokal yang dijelaskan pada dokumen
[PRD_MVP.md](PRD_MVP.md).

## Arsitektur Aplikasi

MVP dibangun menggunakan FastAPI dengan rendering server-side (SSR) melalui
Jinja2 dan integrasi HTMX untuk interaksi progresif sesuai PRD. Struktur modul
utama:

```
src/app/
├── api/              # Router HTTP dan handler tampilan
├── core/             # Konfigurasi aplikasi & factory
├── services/         # Tempat logika domain (akan diisi bertahap)
└── web/
    ├── static/       # Asset glassmorphism (CSS, ikon, dsb.)
    └── templates/    # Template Jinja2 + partial navbar/footer
```

`create_app` pada `src/app/core/application.py` menyiapkan middleware, static
files, dan registrasi router untuk halaman landing awal.

## Menjalankan Secara Lokal

1. Buat virtualenv dan instal dependensi:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .[dev]
   ```

2. Jalankan server pengembangan dengan Uvicorn:

   ```bash
   uvicorn app.main:app --reload
   ```

3. Akses `http://localhost:8000` untuk melihat landing page awal bertema
glassmorphism.

## Pengujian

Gunakan `pytest` untuk menjalankan test dasar yang memverifikasi homepage SSR:

```bash
pytest
```

## To-Do List Implementasi Berdasarkan PRD

Daftar berikut dirinci mengikuti fase prioritas dan milestone yang disebutkan di
PRD. Checklist dapat disesuaikan selama sprint planning, namun urutan menjaga
dependensi utama.

### Fase Fondasi Teknis (Minggu 1-2)
- [ ] Finalisasi skema data inti di Supabase untuk modul: pesanan, produk
      (termasuk atribut Sambatan), brand/etalase, artikel Nusantarum, profil
      pengguna, dan relasi user-brand.
- [ ] Provisioning proyek Supabase (staging & production), termasuk konfigurasi
      Auth (magic link), Storage bucket per brand/artikel, dan variabel
      lingkungan (`SUPABASE_URL`, `SUPABASE_ANON_KEY`,
      `SUPABASE_SERVICE_ROLE_KEY`).
- [ ] Menyiapkan repositori kode backend (FastAPI + HTMX/Jinja2) dengan struktur
      modul sesuai layanan yang dibutuhkan (OrderService, ProductService,
      SambatanLifecycle, dsb.).
- [ ] Menyiapkan panduan desain awal: wireframe navigasi utama (Dashboard,
      Marketplace, Nusantarum, Profil) dan style tile bertema glassmorphism
      (rujuk `docs/guideline-glassmorphism.md` ketika tersedia).
- [ ] Menentukan SOP verifikasi merchant pilot & kurasi konten awal sebagai
      input onboarding.

### Fase Pesanan & Operasional (Minggu 3-4)
- [ ] Implementasi alur pembuatan pesanan: form produk, kuantitas, alamat
      RajaOngkir, jadwal pengiriman, dan status awal `Draf`.
- [ ] Membangun dashboard operasional internal untuk memperbarui status pesanan,
      menambahkan nomor resi, dan mencatat audit trail.
- [ ] Implementasi ekspor CSV laporan pesanan harian.
- [ ] Membuat profil brand internal (form data brand, sertifikasi, kontak) serta
      relasi user-brand (owner/admin/kontributor).
- [ ] Integrasi API RajaOngkir untuk validasi alamat dan estimasi ongkir saat
      checkout internal.

### Fase Marketplace & Brand Publik (Minggu 5)
- [ ] Mengimplementasikan halaman marketplace dengan empat tab kategori
      (Parfum, Raw Material, Tools, Lainnya), pencarian teks per tab, dan filter
      aroma tambahan.
- [ ] Menampilkan detail produk minimum (nama, harga indikatif, stok, foto
      utama, highlight aroma) dengan dukungan mode Sambatan.
- [ ] Menyelesaikan profil brand publik: deskripsi singkat, katalog produk,
      story Nusantara, sertifikasi, tautan artikel Nusantarum, dan CTA kontak.
- [ ] Menyiapkan grid listing Sambatan beserta indikator progress bar dan
      countdown di halaman produk.

### Fase Nusantarum & Konten (Minggu 6)
- [ ] Mengembangkan halaman Nusantarum dengan highlight hero dan tiga tab
      (Parfum, Brand, Perfumer) plus panel filter kaca (kategori aroma, wilayah,
      kurator, status linked) dan pencarian teks.
- [ ] Membangun panel manajemen konten kurator untuk menambah entri, menandai
      status verifikasi, serta melakukan linking ke profil terkait.
- [ ] Menautkan artikel Nusantarum ke produk/brand/perfumer relevan guna
      mengarahkan traffic.

### Fase Profil Pengguna & Sambatan (Minggu 7)
- [ ] Membuat profil pengguna marketplace (nama, email, preferensi aroma) dan
      fitur favorit sederhana.
- [ ] Implementasi alur Sambatan: create request (`is_sambatan`, `total_slots`,
      `sambatan_deadline`), join request dengan transaksi aman, progress otomatis
      (`remaining_slots`, `sambatan_progress_percentage`).
- [ ] Mengembangkan `SambatanLifecycleService` & scheduler untuk menangani
      deadline, payout/refund, serta logging ke `SambatanAuditLog`.
- [ ] Membuat dashboard seller Sambatan dengan statistik slot, kontribusi
      terakhir, dan kontrol status.

### Fase QA, Peluncuran, & Operasional (Minggu 8)
- [ ] Menjalankan suite QA lintas modul: pytest (async + coverage), linting Ruff
      & Black, dan verifikasi migrasi Supabase.
- [ ] Melaksanakan UAT internal dengan skenario marketplace, Nusantarum, dan
      Sambatan (termasuk linking ulang oleh kurator).
- [ ] Menyusun SOP operasional akhir: respon tiket Sambatan, fallback manual
      refund/payout, dan monitoring log dasar.
- [ ] Menyiapkan deployment ke Vercel atau alternatif kontainer (Gunicorn +
      Uvicorn) dan strategi rollback.
- [ ] Mengaktifkan monitoring dasar serta menyiapkan checklist post-mortem jika
      terjadi kegagalan besar.

### Backlog Pasca-MVP
- [ ] Notifikasi otomatis (email/push) untuk event pesanan dan Sambatan.
- [ ] Integrasi pembayaran pihak ketiga.
- [ ] Fitur analitik lanjutan & rekomendasi produk.
- [ ] Aplikasi mobile native dan multi-bahasa.

## Referensi

- [PRD Sensasiwangi.id](PRD_MVP.md)
