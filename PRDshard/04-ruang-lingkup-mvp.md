# 4. Ruang Lingkup MVP

## 4.1 Fitur Inti
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

## 4.2 Pengalaman Pengguna
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

## 4.3 Integrasi & Data
- Supabase menjadi backend data utama (managed PostgreSQL 15) yang menampung skema pesanan, brand (etalase), produk, artikel Nusantarum, dan profil pengguna.
- Supabase Auth menyediakan otentikasi dasar (email + magic link) untuk akses merchant dan pengguna awal; perluasan metode lain direncanakan pasca-MVP.
- Skema brand di Supabase menyertakan relasi user-brand (owner, admin, kontributor) sehingga setiap akun dapat membangun etalase dan menambahkan anggota tim sebelum produk dipublikasikan.
- Supabase Storage menyimpan aset ringan (gambar produk, hero artikel) dengan batasan 5MB per file dan struktur folder per brand/artikel.
- Integrasi Supabase mengikuti panduan `docs/SUPABASE_IMPLEMENTATION_GUIDE.md` (env `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`) dan migrasi via `verify_supabase_migration.py`.
- Tidak ada integrasi pembayaran; permintaan pesanan diarahkan ke alur internal melalui dashboard operasional.
- Integrasi logistik menggunakan API RajaOngkir sesuai `docs/RajaOngkir-API-Integration-Deep-Dive.md` untuk cek ongkir, kota, dan provinsi pada saat checkout (env `RAJAONGKIR_API_KEY`).
- Struktur alamat pengguna mengikuti standar field RajaOngkir (province_id, city_id, subdistrict_id, postal_code) agar request ongkir valid dan dapat disinkronkan dengan data Supabase.
- Logging aktivitas dasar (audit trail pesanan, update profil, publikasi artikel) disimpan di Supabase dengan retensi 90 hari.
- Rekam jejak Sambatan (partisipan, transaksi, audit) disimpan di Supabase sehingga satu listing group-buy tersinkronisasi dengan data operasional.

## 4.4 Fitur Sambatan Marketplace
- Mode Sambatan pada pengelolaan produk memungkinkan penjual menerbitkan satu listing untuk banyak pembeli sekaligus: toggle `is_sambatan`, `total_slots`, dan `sambatan_deadline` tersedia di `ProductCreateRequest` serta direkam di model `Product` (`is_sambatan`, `total_slots`, `filled_slots`, `sambatan_status`).
- Slot dan status terkelola otomatis: layanan `ProductService` menghitung `remaining_slots` dan `sambatan_progress_percentage`, sementara status bergeser dari INACTIVE -> ACTIVE -> FULL -> COMPLETED/FAILED sesuai `filled_slots` dan tindak lanjut seller.
- Buyer bergabung melalui formulir Sambatan yang memanfaatkan `SambatanJoinRequest`; `SambatanParticipationService.join_sambatan` memakai transaksi SELECT FOR UPDATE dan validasi alamat pengiriman agar banyak pembeli dapat mengambil slot tanpa bentrok.
- Lifecycle otomatis: `SambatanLifecycleService` dan `SambatanScheduler` menjalankan pengecekan deadline, pemrosesan refund/payout, serta pengingat; seluruh kejadian dicatat ke `SambatanAuditLog`, `SambatanTransaction`, dan `SambatanLifecycleState` untuk pelacakan satu produk multi-pembeli.
- Seller dashboard (`ProductService.get_seller_sambatan_dashboard`) menampilkan statistik aktif, progress bar, dan daftar partisipan sehingga satu SKU Sambatan dapat dimonitor dalam satu layar.
- Kurator Nusantarum memiliki panel manajemen (glass dashboard) untuk menambah entri parfum/brand/perfumer, menandai status verifikasi, dan melakukan linking ke profil produk/brand/perfumer saat data sudah tersedia.
- Setelah Sambatan selesai, status produk otomatis menjadi tidak aktif dan perubahan terekam di `ProductHistory`, menjaga jejak audit untuk produk yang melayani banyak pembeli.

## 4.5 Alur Belanja Pengguna
1. Pengguna mencari produk melalui pencarian teks, filter kategori/tab, atau rekomendasi Nusantarum.
2. Pengguna membuka halaman detail produk; dapat memilih varian, melihat ketersediaan Sambatan, dan membaca story brand.
3. Pengguna menambahkan produk ke keranjang atau bergabung Sambatan (memilih jumlah slot dan alamat pengiriman).
4. Pengguna meninjau keranjang (produk reguler + Sambatan aktif), mengisi alamat dan kontak sesuai format RajaOngkir (provinsi, kota/kabupaten, kecamatan, kode pos, nomor telepon), lalu mengirim permintaan pesanan.
5. Sistem mencatat pesanan dengan status awal **Draf** dan mengirim instruksi pembayaran/konfirmasi manual ke pengguna.
6. Operator memverifikasi pembayaran/slot, mengubah status ke **Diproses**, dan menyiapkan pengiriman.
7. Pesanan dikirim; operator menambahkan nomor resi pada status **Dikirim** sehingga pembeli dapat melakukan pelacakan, dan pengguna menerima notifikasi.
8. Setelah barang diterima atau Sambatan selesai, operator menandai status **Selesai**; bila ada kendala pengiriman, status **Dibatalkan**/refund sesuai SOP.
9. Pengguna dapat meninjau riwayat pesanan dari dashboard dan memberikan umpan balik ke tim operasi.
