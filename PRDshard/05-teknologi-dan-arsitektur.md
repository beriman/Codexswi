# 5. Teknologi & Arsitektur MVP

## 5.1 Backend & API
- Python 3.11 dengan FastAPI sebagai kerangka utama, dijalankan secara async di atas Uvicorn (dev) dan Gunicorn + uvicorn.workers.UvicornWorker (prod).
- Pola modular monolith yang memisahkan domain (product, wallet, mobile, dsb) dengan service layer; akses database hanya melalui layanan domain.
- SQLAlchemy 2.0 AsyncSession sebagai ORM, Pydantic v2 untuk skema request/response, serta dependency injection FastAPI untuk session dan service binding.
- Alembic digunakan untuk migrasi skema; skrip `scripts/create_migration.py` menjaga versioning database.

## 5.2 Frontend & Presentasi
- Server-side rendering menggunakan Jinja2 template, dengan HTMX untuk partial update (form submission, pagination, filter tanpa full reload).
- Komponen UI mengikuti prinsip progresif: fallback HTML penuh, enhancement HTMX opsional.
- Asset statis (CSS/JS ringan, gambar hero) disajikan dari direktori `static/`; pipeline build memanfaatkan tooling yang ada di `web-bundles/` bila dibutuhkan.
- Komponen tab marketplace (Parfum, Raw Material, Tools, Lainnya) dibangun dengan HTMX swap agar perpindahan kategori tanpa reload halaman penuh.
- Form Sambatan menggunakan modal HTMX dengan validasi dasar dan konfirmasi penerimaan otomatis di layar.
- Komponen kaca mengikuti guideline `docs/guideline-glassmorphism.md`: gunakan utilitas `.glass-panel` (rgba(255,255,255,0.35), blur 12px, radius 16px, border tipis) dan font Poppins dengan kontras #1A1A1A; tab/CTA memakai varian hover lebih terang.

## 5.3 Data & Infrastruktur
- Supabase (managed PostgreSQL 15) sebagai basis data utama dengan proyek terpisah untuk staging dan production, berikut role-based access untuk domain layanan.
- Sebelum sprint dimulai, tim infrastruktur menyiapkan dua proyek Supabase (staging & production), mengaktifkan RLS default, serta membuat bucket Storage awal.
- Supabase Storage sebagai repositori media dengan bucket privat per modul (produk, artikel) dan CDN bawaan untuk deliver konten statis.
- Skema Supabase Sambatan mencakup tabel `sambatan_participants`, `sambatan_transactions`, `sambatan_audit_logs`, dan `sambatan_lifecycle_states` (lihat `src/product/models/`) untuk mendukung satu produk multi pembeli beserta audit finansial.
- Skema Nusantarum mencakup tabel konten kurasi (parfum, brand, perfumer) dengan relasi opsional ke entitas produk/brand/perfumer sehingga konten bisa dipublikasikan lebih dulu lalu di-link oleh kurator.
- Konfigurasi lingkungan melalui variabel environment (.env lokal tidak ikut repo); kunci Supabase (anon+service) disimpan di secret manager, tidak dalam kode.

## 5.4 Observability & Quality
- Logging terstruktur dengan standar Python logging; event penting (pembuatan pesanan, publikasi artikel) dicatat untuk audit trail.
- Pipeline audit Sambatan memakai `SambatanAuditLog` dan `SambatanTransaction` untuk mencatat progres, refund, serta payout; data ini menggerakkan dashboard operasional agar kesehatan setiap group-buy terlihat end-to-end.
- QA UI mengikuti tes kontras dan fallback glassmorphism (cek `backdrop-filter` support, fallback panel semi transparan) sebagaimana pedoman glass guideline.
- QA menyiapkan checklist UAT per modul (marketplace reguler, Sambatan, Nusantarum, brand onboarding) sebelum fase Minggu 8.
- Agen AI/otomasi wajib menggunakan tool CLI lokal: Playwright MCP untuk testing UI, Supabase CLI/MCP untuk migrasi & data seeding, Vercel CLI untuk deployment, serta GitHub CLI/MCP untuk workflow git; semua pengerjaan dilakukan via terminal di lingkungan pengguna.
- UAT mencakup pengujian linking ulang oleh kurator: memastikan entri Nusantarum dapat diperbarui dengan produk/brand/perfumer setelah tersedia tanpa menyalahi audit trail.
- Antrian notifikasi internal Sambatan (deadline reminder, payout follow-up) dicatat lewat logging dan dashboard metrik supaya respon operator terhadap pembeli terukur.
- Test otomatis menggunakan pytest (async + coverage) serta linting dengan Ruff dan Black sebelum rilis.
- Monitoring dasar melalui log streaming; integrasi APM/Sentry menjadi backlog pasca-MVP.

## 5.5 Pengiriman & Operasional
- Deployment produksi menggunakan Vercel (serverless FastAPI adaptor) dengan fallback opsi kontainer/VM (`PYTHONPATH=. gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker`) untuk kebutuhan khusus.
- CI/CD mengeksekusi Black, Ruff, dan `pytest --cov=src`; pipeline staging memanfaatkan database PostgreSQL terpisah.
- Background job `SambatanScheduler` (`src/core/scheduler.py`) dijalankan sebagai service terpisah/PM2 task untuk memproses deadline, payout, dan pengingat fitur Sambatan.
- Sinkronisasi skema Supabase dilakukan via Alembic (menggunakan `SUPABASE_DATABASE_URL`) sebelum deployment; backup harian memanfaatkan PITR Supabase.
- Strategi rollback: migrasi database reversible via Alembic, deployment blue-green bila infrastruktur memungkinkan.

## 5.6 SLA Sambatan & Dukungan Operasional
- Target respon L1: tiket Sambatan baru harus diakui oleh operator dalam <=30 menit jam operasional; eskalasi ke L2 (lead operasional) jika belum ada tindak lanjut setelah 60 menit.
- Target penyelesaian: kendala pembayaran/refund harus tuntas <=4 jam kerja; isu logistik maksimal 1 hari; pencatatan status dilakukan di dashboard Sambatan dan dicap waktu secara otomatis.
- Fallback manual: jika `SambatanLifecycleService` gagal memproses refund/payout, operator menjalankan SOP manual (ekspor partisipan, verifikasi transfer, update status lewat `ProductService.complete_sambatan`) sebelum menutup tiket.
- SOP rinci (refund Sambatan, update resi massal) didokumentasikan terpisah di `docs/ops/sop_sambatan.md` dan wajib direview tiap kuartal.
- Post-mortem ringan disiapkan untuk kegagalan besar (lebih dari 10 pembeli terdampak) dan hasilnya digunakan sebagai checklist regresi otomatis.
