# PRD MVP

## 0. Ikhtisar Proyek Sensasiwangi.id
Sensasiwangi.id adalah inisiatif digital yang mengangkat produk wewangian lokal (parfum, aromaterapi, home fragrance) ke pasar nasional melalui storytelling Nusantara. Platform ini terdiri dari tiga komponen utama:
- **Marketplace**: etalase produk brand wewangian terkurasi yang menonjolkan identitas lokal, kemasan khas, dan kisah di balik aroma.
- **Nusantarum**: kanal editorial dengan artikel, panduan, dan kurasi cerita olfaktori yang mengedukasi konsumen sekaligus mengarahkan traffic ke brand pilot.
- **Profil Pengguna dan Brand**: ruang untuk membangun kepercayaan, menampilkan kredensial artisan, sertifikasi BPOM/halal, serta mengelola preferensi aroma konsumen.

Visi proyek adalah menjadikan sensasiwangi.id sebagai destinasi utama bagi pecinta aroma lokal, memfasilitasi hubungan langsung antara artisan dan konsumen urban. MVP berfokus pada validasi tiga hipotesis utama: (1) cerita Nusantarum mampu menggerakkan pengunjung ke listing produk, (2) automasi pemesanan menurunkan effort operasional, dan (3) profil brand terkurasi meningkatkan konversi inquiry.

## 1. Ringkasan Eksekutif
- Fokus pada peluncuran versi minimum yang memvalidasi automasi pemesanan sekaligus menyiapkan fondasi marketplace brand wewangian lokal.
- Target pengguna awal: tim operasional internal, 20 merchant pilot sebagai pemasok, dan 200 pengunjung marketplace hasil kampanye internal.
- MVP diharapkan membuktikan bahwa automasi proses pemesanan mengurangi waktu proses >=30% dan konten Nusantarum mampu mengarahkan traffic berkualitas ke brand pilot.

## 2. Tujuan MVP
- Memungkinkan merchant pilot membuat dan melacak pesanan melalui antarmuka web sederhana.
- Menyediakan visibilitas status pesanan waktu nyata bagi tim operasional.
- Menyediakan kanal marketplace ringan untuk menampilkan katalog brand pilot.
- Menghadirkan halaman Nusantarum sebagai kurasi editorial yang mengarahkan traffic ke listing marketplace.
- Menyediakan profil dasar untuk pengguna dan brand guna membangun kepercayaan awal.
- Menyediakan laporan harian yang dapat diekspor untuk analisis manual.

## 3. Persona & Kebutuhan Utama
- **Merchant Pilot / Brand Owner**: butuh cara mengelola pesanan, memamerkan signature scent, dan menampilkan kredensial produksi.
- **Pengunjung Marketplace**: butuh cara cepat menemukan produk unggulan, memahami cerita aroma, dan menghubungi merchant.
- **Operator Internal**: butuh dashboard status untuk memprioritaskan tindakan harian dan menindaklanjuti tiket Sambatan.
- **Manajer Operasional**: butuh data ringkas untuk menilai performa MVP.

## 4. Ruang Lingkup MVP
### 4.1 Fitur Inti
- Registrasi merchant pilot via undangan (setelah verifikasi, user membuat brand/etalase toko sebelum mengunggah produk).
- Pembuatan pesanan dengan detail dasar (produk, kuantitas, alamat, jadwal pengiriman).
- Pelacakan status pesanan (Draf, Diproses, Dikirim, Selesai, Dibatalkan).
- Dashboard operasional untuk memperbarui status pesanan dan menambahkan nomor resi pengiriman bagi pembeli.
- Ekspor CSV laporan pesanan harian.
- Marketplace listing produk brand pilot terbagi dalam empat tab (Parfum, Raw Material, Tools, Lainnya) dengan detail minimum (nama produk, harga indikatif, stok, foto utama, highlight aroma) dan pencarian teks di setiap tab.
- Halaman Nusantarum sebagai landing editorial dengan tiga tab (Parfum, Brand, Perfumer): setiap entri menaut ke profil pengguna, profil brand, atau produk terkait, dan menyediakan artikel kurasi (judul, ringkasan, gambar hero, tag aroma/asal).
- Fitur Sambatan (group-buy) memungkinkan penjual membuka batch produksi sekali jalan: slot partisipasi, harga khusus, dan deadline dikelola otomatis di satu listing.
- Profil pengguna (pengunjung marketplace) dengan data dasar (nama, email, preferensi aroma) untuk menyimpan favorit sederhana.
- Profil brand publik yang berfungsi sebagai etalase toko: menampilkan deskripsi singkat, kontak, katalog produk, story Nusantara, sertifikasi, dan tautan artikel Nusantarum terkait; setiap user harus membuat atau bergabung dengan brand sebelum menerbitkan produk.

### 4.2 Pengalaman Pengguna
- Antarmuka web SSR menggunakan HTMX + Jinja2 dengan navigasi utama: Dashboard, Marketplace, Nusantarum, Profil.
- Navbar glass-panel menampilkan logo sensasiwangi.id di kiri, menu halaman utama di tengah, serta tombol Login/Logout (bergantung sesi) di kanan; setelah user login, navbar menampilkan ikon keranjang dan foto profil (klik membuka halaman profil pengguna).
- Footer menggunakan latar solid bernuansa gradien global (tanpa efek kaca) untuk menampung info kontak, tautan kebijakan, dan sosial sesuai pedoman glassmorphism.
- Form sederhana dengan validasi dasar dan notifikasi sukses/gagal.
- Marketplace menampilkan grid produk dalam empat tab (Parfum, Raw Material, Tools, Lainnya) dengan filter kategori aroma tambahan dan pencarian teks di masing-masing tab.
- Halaman Nusantarum menampilkan highlight hero dan tiga tab (Parfum, Brand, Perfumer) dengan filter per tab (mis. aroma, asal, kurator); setiap entri bisa dilihat walau belum memiliki link produk/brand/perfumer lalu dikurasi ulang ketika data tersedia.
- Tab Nusantarum memiliki panel filter kaca (kategori aroma, wilayah, kurator, status linked) dan pencarian teks untuk mempercepat navigasi konten kurasi.
- Fitur Sambatan menghadirkan blok khusus di halaman produk berisi progress bar, jumlah slot tersisa, countdown deadline, tombol "Gabung Sambatan", serta daftar kontribusi terakhir.
- Alur onboarding penjual dimulai dari pembuatan brand (etalase toko) dengan logo, narasi, dan identitas visual; setelah brand aktif, penjual dapat mengelola produk dan Sambatan di bawah etalase tersebut.
- Seluruh UI publik dan dashboard menerapkan tema glassmorphism terinspirasi botol parfum kaca: panel utama memakai kelas utilitas `.glass-panel`, gradien latar lembut, dan efek blur sesuai pedoman `docs/guideline-glassmorphism.md`.
- Sebelum sprint frontend, tim desain menyiapkan wireframe dan style tile bertema glassmorphism (logo, palet gradien, komponen `.glass-panel`) sebagai acuan implementasi.
- Profil pengguna dan brand dapat diedit melalui form internal tanpa fitur sosial lanjutan.

### 4.3 Integrasi & Data
- Supabase menjadi backend data utama (managed PostgreSQL 15) yang menampung skema pesanan, brand (etalase), produk, artikel Nusantarum, dan profil pengguna.
- Supabase Auth menyediakan otentikasi dasar (email + magic link) untuk akses merchant dan pengguna awal; perluasan metode lain direncanakan pasca-MVP.
- Skema brand di Supabase menyertakan relasi user-brand (owner, admin, kontributor) sehingga setiap akun dapat membangun etalase dan menambahkan anggota tim sebelum produk dipublikasikan.
- Supabase Storage menyimpan aset ringan (gambar produk, hero artikel) dengan batasan 5MB per file dan struktur folder per brand/artikel.
- Integrasi Supabase mengikuti panduan `docs/SUPABASE_IMPLEMENTATION_GUIDE.md` (env `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`) dan migrasi via `verify_supabase_migration.py`.
- Integrasi Supabase mengikuti panduan `docs/SUPABASE_IMPLEMENTATION_GUIDE.md` (env `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`) dan migrasi via `verify_supabase_migration.py`.
- Tidak ada integrasi pembayaran; permintaan pesanan diarahkan ke alur internal melalui dashboard operasional.
- Integrasi logistik menggunakan API RajaOngkir sesuai `docs/RajaOngkir-API-Integration-Deep-Dive.md` untuk cek ongkir, kota, dan provinsi pada saat checkout (env `RAJAONGKIR_API_KEY`).
- Struktur alamat pengguna mengikuti standar field RajaOngkir (province_id, city_id, subdistrict_id, postal_code) agar request ongkir valid dan dapat disinkronkan dengan data Supabase.
- Logging aktivitas dasar (audit trail pesanan, update profil, publikasi artikel) disimpan di Supabase dengan retensi 90 hari.
- Rekam jejak Sambatan (partisipan, transaksi, audit) disimpan di Supabase sehingga satu listing group-buy tersinkronisasi dengan data operasional.

### 4.4 Fitur Sambatan Marketplace
- Mode Sambatan pada pengelolaan produk memungkinkan penjual menerbitkan satu listing untuk banyak pembeli sekaligus: toggle `is_sambatan`, `total_slots`, dan `sambatan_deadline` tersedia di `ProductCreateRequest` serta direkam di model `Product` (`is_sambatan`, `total_slots`, `filled_slots`, `sambatan_status`).
- Slot dan status terkelola otomatis: layanan `ProductService` menghitung `remaining_slots` dan `sambatan_progress_percentage`, sementara status bergeser dari INACTIVE -> ACTIVE -> FULL -> COMPLETED/FAILED sesuai `filled_slots` dan tindak lanjut seller.
- Buyer bergabung melalui formulir Sambatan yang memanfaatkan `SambatanJoinRequest`; `SambatanParticipationService.join_sambatan` memakai transaksi SELECT FOR UPDATE dan validasi alamat pengiriman agar banyak pembeli dapat mengambil slot tanpa bentrok.
- Lifecycle otomatis: `SambatanLifecycleService` dan `SambatanScheduler` menjalankan pengecekan deadline, pemrosesan refund/payout, serta pengingat; seluruh kejadian dicatat ke `SambatanAuditLog`, `SambatanTransaction`, dan `SambatanLifecycleState` untuk pelacakan satu produk multi-pembeli.
- Seller dashboard (`ProductService.get_seller_sambatan_dashboard`) menampilkan statistik aktif, progress bar, dan daftar partisipan sehingga satu SKU Sambatan dapat dimonitor dalam satu layar.
- Kurator Nusantarum memiliki panel manajemen (glass dashboard) untuk menambah entri parfum/brand/perfumer, menandai status verifikasi, dan melakukan linking ke profil produk/brand/perfumer saat data sudah tersedia.
- Setelah Sambatan selesai, status produk otomatis menjadi tidak aktif dan perubahan terekam di `ProductHistory`, menjaga jejak audit untuk produk yang melayani banyak pembeli.

### 4.5 Alur Belanja Pengguna
1. Pengguna mencari produk melalui pencarian teks, filter kategori/tab, atau rekomendasi Nusantarum.
2. Pengguna membuka halaman detail produk; dapat memilih varian, melihat ketersediaan Sambatan, dan membaca story brand.
3. Pengguna menambahkan produk ke keranjang atau bergabung Sambatan (memilih jumlah slot dan alamat pengiriman).
4. Pengguna meninjau keranjang (produk reguler + Sambatan aktif), mengisi alamat dan kontak sesuai format RajaOngkir (provinsi, kota/kabupaten, kecamatan, kode pos, nomor telepon), lalu mengirim permintaan pesanan.
5. Sistem mencatat pesanan dengan status awal **Draf** dan mengirim instruksi pembayaran/konfirmasi manual ke pengguna.
6. Operator memverifikasi pembayaran/slot, mengubah status ke **Diproses**, dan menyiapkan pengiriman.
7. Pesanan dikirim; operator menambahkan nomor resi pada status **Dikirim** sehingga pembeli dapat melakukan pelacakan, dan pengguna menerima notifikasi.
8. Setelah barang diterima atau Sambatan selesai, operator menandai status **Selesai**; bila ada kendala pengiriman, status **Dibatalkan**/refund sesuai SOP.
9. Pengguna dapat meninjau riwayat pesanan dari dashboard dan memberikan umpan balik ke tim operasi.
## 5. Teknologi & Arsitektur MVP
### 5.1 Backend & API
- Python 3.11 dengan FastAPI sebagai kerangka utama, dijalankan secara async di atas Uvicorn (dev) dan Gunicorn + uvicorn.workers.UvicornWorker (prod).
- Pola modular monolith yang memisahkan domain (product, wallet, mobile, dsb) dengan service layer; akses database hanya melalui layanan domain.
- SQLAlchemy 2.0 AsyncSession sebagai ORM, Pydantic v2 untuk skema request/response, serta dependency injection FastAPI untuk session dan service binding.
- Alembic digunakan untuk migrasi skema; skrip scripts/create_migration.py menjaga versioning database.

### 5.2 Frontend & Presentasi
- Server-side rendering menggunakan Jinja2 template, dengan HTMX untuk partial update (form submission, pagination, filter tanpa full reload).
- Komponen UI mengikuti prinsip progresif: fallback HTML penuh, enhancement HTMX opsional.
- Asset statis (CSS/JS ringan, gambar hero) disajikan dari direktori static/; pipeline build memanfaatkan tooling yang ada di web-bundles/ bila dibutuhkan.
- Komponen tab marketplace (Parfum, Raw Material, Tools, Lainnya) dibangun dengan HTMX swap agar perpindahan kategori tanpa reload halaman penuh.
- Form Sambatan menggunakan modal HTMX dengan validasi dasar dan konfirmasi penerimaan otomatis di layar.
- Komponen kaca mengikuti guideline `docs/guideline-glassmorphism.md`: gunakan utilitas `.glass-panel` (rgba(255,255,255,0.35), blur 12px, radius 16px, border tipis) dan font Poppins dengan kontras #1A1A1A; tab/CTA memakai varian hover lebih terang.

### 5.3 Data & Infrastruktur
- Supabase (managed PostgreSQL 15) sebagai basis data utama dengan proyek terpisah untuk staging dan production, berikut role-based access untuk domain layanan.
- Sebelum sprint dimulai, tim infrastruktur menyiapkan dua proyek Supabase (staging & production), mengaktifkan RLS default, serta membuat bucket Storage per kategori (produk, artikel, sambatan).
- Supabase Storage sebagai repositori media dengan bucket privat per modul (produk, artikel) dan CDN bawaan untuk deliver konten statis.
- Skema Supabase Sambatan mencakup tabel `sambatan_participants`, `sambatan_transactions`, `sambatan_audit_logs`, dan `sambatan_lifecycle_states` (lihat `src/product/models/`) untuk mendukung satu produk multi pembeli beserta audit finansial.
- Skema Nusantarum mencakup tabel konten kurasi (parfum, brand, perfumer) dengan relasi opsional ke entitas produk/brand/perfumer sehingga konten bisa dipublikasikan lebih dulu lalu di-link oleh kurator.
- Konfigurasi lingkungan melalui variabel environment (.env lokal tidak ikut repo); kunci Supabase (anon+service) disimpan di secret manager, tidak dalam kode.

### 5.4 Observability & Quality
- Logging terstruktur dengan standar Python logging; event penting (pembuatan pesanan, publikasi artikel) dicatat untuk audit trail.
- Pipeline audit Sambatan memakai `SambatanAuditLog` dan `SambatanTransaction` untuk mencatat progres, refund, serta payout; data ini menggerakkan dashboard operasional agar kesehatan setiap group-buy terlihat end-to-end.
- QA UI mengikuti tes kontras dan fallback glassmorphism (cek `backdrop-filter` support, fallback panel semi transparan) sebagaimana pedoman glass guideline.
- QA menyiapkan checklist UAT per modul (marketplace reguler, Sambatan, Nusantarum, brand onboarding) sebelum fase Minggu 8.
- Agen AI/otomasi wajib menggunakan tool CLI lokal: Playwright MCP untuk testing UI, Supabase CLI/MCP untuk migrasi & data seeding, Vercel CLI untuk deployment, serta GitHub CLI/MCP untuk workflow git; semua pengerjaan dilakukan via terminal di lingkungan pengguna.
- UAT mencakup pengujian linking ulang oleh kurator: memastikan entri Nusantarum dapat diperbarui dengan produk/brand/perfumer setelah tersedia tanpa menyalahi audit trail.
- Antrian notifikasi internal Sambatan (deadline reminder, payout follow-up) dicatat lewat logging dan dashboard metrik supaya respon operator terhadap pembeli terukur.
- Test otomatis menggunakan pytest (async + coverage) serta linting dengan Ruff dan Black sebelum rilis.
- Monitoring dasar melalui log streaming; integrasi APM/Sentry menjadi backlog pasca-MVP.

### 5.5 Pengiriman & Operasional
- Deployment produksi menggunakan Vercel (serverless FastAPI adaptor) dengan fallback opsi kontainer/VM (`PYTHONPATH=. gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker`) untuk kebutuhan khusus.
- CI/CD mengeksekusi Black, Ruff, dan pytest --cov=src; pipeline staging memanfaatkan database PostgreSQL terpisah.
- Background job `SambatanScheduler` (src/core/scheduler.py) dijalankan sebagai service terpisah/PM2 task untuk memproses deadline, payout, dan pengingat fitur Sambatan.
- Sinkronisasi skema Supabase dilakukan via Alembic (menggunakan SUPABASE_DATABASE_URL) sebelum deployment; backup harian memanfaatkan PITR Supabase.
- Strategi rollback: migrasi database reversible via Alembic, deployment blue-green bila infrastruktur memungkinkan.

### 5.6 SLA Sambatan & Dukungan Operasional
- Target respon L1: tiket Sambatan baru harus diakui oleh operator dalam <=30 menit jam operasional; eskalasi ke L2 (lead operasional) jika belum ada tindak lanjut setelah 60 menit.
- Target penyelesaian: kendala pembayaran/refund harus tuntas <=4 jam kerja; isu logistik maksimal 1 hari; pencatatan status dilakukan di dashboard Sambatan dan dicap waktu secara otomatis.
- Fallback manual: jika `SambatanLifecycleService` gagal memproses refund/payout, operator menjalankan SOP manual (ekspor partisipan, verifikasi transfer, update status lewat `ProductService.complete_sambatan`) sebelum menutup tiket.
- SOP rinci (refund Sambatan, update resi massal) didokumentasikan terpisah di `docs/ops/sop_sambatan.md` dan wajib direview tiap kuartal.
- Post-mortem ringan disiapkan untuk kegagalan besar (lebih dari 10 pembeli terdampak) dan hasilnya digunakan sebagai checklist regresi otomatis.
## 6. Di Luar Ruang Lingkup
- Aplikasi mobile native.
- Otomatisasi pembayaran atau integrasi gateway.
- Sistem notifikasi push/email otomatis.
- Fitur analitik lanjutan atau rekomendasi produk.
- Multi-bahasa selain bahasa Indonesia.
- Fitur advanced marketplace (keranjang belanja, checkout publik, rating dan ulasan, multi-vendor onboarding self-service).

## 7. Metrik Sukses Awal
- >=15 merchant pilot aktif dalam 30 hari.
- >=80% pesanan dibuat tanpa bantuan tim internal.
- Rata-rata waktu penyelesaian pesanan turun >=30% dibanding baseline manual.
- Feedback NPS merchant pilot >=30.
- >=3 artikel Nusantarum dipublikasikan dan menghasilkan >=100 klik ke brand terkait dalam 30 hari.
- >=50 interaksi Nusantarum (simpan/favorit/tab Perfumer ke profil) dalam 30 hari sebagai indikator efektivitas kurasi.
- >=20 profil pengguna marketplace terverifikasi dengan aktivitas kunjungan ulang dalam 30 hari.
- >=2 Sambatan live mencapai >=80% slot terisi dalam 30 hari, membuktikan model sekali-terbit untuk banyak pembeli.

## 8. Timeline & Milestone MVP
- Minggu 1-2: Finalisasi skema data (pesanan, produk, brand, artikel) dan desain alur pengguna marketplace, serta provisioning proyek Supabase (staging & production) lengkap dengan bucket Storage awal.
- Minggu 3-4: Pengembangan fitur pembuatan dan pelacakan pesanan + profil brand internal.
- Minggu 5: Implementasi marketplace listing dan profil brand publik.
- Minggu 6: Pembuatan halaman Nusantarum beserta alur input konten.
- Minggu 7: Integrasi profil pengguna marketplace, implementasi fitur Sambatan, dan QA lintas modul.
- Minggu 8: UAT internal, perbaikan prioritas, dan peluncuran pilot terpandu.

## 9. Risiko & Mitigasi
- **Supabase rate limit & RLS salah konfigurasi**: tetapkan kuota koneksi, audit role, dan siapkan monitor kueri lambat sebelum go-live.
- **Keterlambatan refund Sambatan**: dokumentasikan SOP manual dan lakukan drill berkala agar operator siap ketika otomasi gagal.
- **Adopsi rendah di marketplace**: kampanye konten Nusantarum terjadwal serta navigasi konten yang tegas mengarahkan pengunjung ke brand.
- **Konten/asset brand tidak konsisten**: sediakan template upload dan review internal sebelum publikasi.
- **Beban operasional meningkat**: batasi merchant pilot, sediakan SOP eskalasi, dan prioritas otomatis di dashboard.
- **Kegagalan Sambatan**: fallback refund/payout otomatis harus diuji dan didukung checklist manual agar satu produk multi pembeli tidak menimbulkan sengketa massal.
- **Skalabilitas data**: terapkan indeks dasar pada tabel produk dan artikel, rencanakan sharding ringan untuk fase berikutnya.

## 10. Pertanyaan Terbuka
- Bagaimana kriteria kurasi brand dan artikel Nusantarum untuk tahap awal?
- Apakah diperlukan moderasi konten pengguna sebelum dipublikasikan?
- Format akhir laporan harian, termasuk metrik marketplace apa saja yang harus dilacak?
- Siapa pemilik konten Nusantarum dan seberapa sering pembaruan dijadwalkan?
- Berapa batas minimal slot Sambatan dan siapa yang menyetujui campaign sebelum go-live agar kualitas produk sekali jalan tetap terjaga?
















































