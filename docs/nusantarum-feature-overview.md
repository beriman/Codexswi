# Nusantarum - Ensiklopedia Aroma SensasiWangi.id

## Ringkasan Fitur
Nusantarum adalah ensiklopedia aroma yang dikurasi secara khusus untuk mengangkat perfumer dan brand parfum lokal Indonesia. Halaman `/nusantarum` menjadi etalase publik yang menghadirkan profil perfumer, brand, dan katalog parfum dalam satu pengalaman pencarian terpadu. Semua data yang tampil telah melewati proses kurasi manual oleh tim SensasiWangi sehingga pengguna dapat mengidentifikasi pembuat parfum autentik dan membedakan mereka dari penjual biasa.

Fitur ini melayani dua sasaran utama:
- **Pengguna umum** yang ingin menemukan referensi parfum lokal tepercaya.
- **Perajin/brand** yang ingin mendapatkan legitimasi melalui badge "Terverifikasi" setelah lolos kurasi.

## Struktur Halaman `/nusantarum`
### Header dan Hero
- Halaman menggunakan `AppHeader` global sebagai navigasi utama.
- Tepat di bawah header terdapat judul besar **"Nusantarum"** dan subjudul yang menjelaskan perannya sebagai ensiklopedia aroma lokal.
- Seluruh tampilan mengadopsi estetika **glassmorphism**: panel berlapis `bg-card/60`, `backdrop-blur-lg`, serta `border border-white/20` untuk membangun nuansa premium dan transparan.

### Bilah Pencarian Global
- Terletak di bagian atas konten, di bawah judul utama.
- Menggunakan input tunggal yang mengeksekusi pencarian lintas-tab secara real-time. Ketika pengguna mengetik kata kunci, daftar pada tab yang sedang aktif langsung terfilter.
- Fungsi pencarian memanfaatkan query gabungan yang mencakup koleksi perfumer, brand, dan parfum sehingga pengguna dapat menavigasi ensiklopedia tanpa berpindah tab terlebih dahulu.

### Tabs Navigasi
- Menggunakan komponen `Tabs` dari ShadCN dengan tiga opsi: **Perfumers**, **Brands**, dan **Parfums**.
- Tab aktif memiliki gaya gradien khusus (`bg-accent-gradient`) yang menonjol di atas panel glassmorphism.
- Komponen tab ditempatkan persis di bawah bilah pencarian sehingga alur eksplorasi menjadi lurus dari pencarian ke konten.

## Konten per Tab
### Tab "Perfumers"
- Menampilkan grid responsif berisi `PerfumerCard` untuk seluruh profil bertipe *Perfumer*.
- Setiap kartu memuat:
  - Avatar perfumer di sisi kiri.
  - Nama lengkap, `@username`, dan bio singkat (dipotong otomatis bila melebihi batas karakter).
  - Statistik ringkas seperti jumlah pengikut atau karya yang dipublikasikan.
  - **Badge "Terverifikasi"** dengan ikon `BadgeCheck` bila `isCurated: true`. Badge ini menjadi indikator utama bahwa perfumer sudah lolos kurasi Nusantarum.
  - Tombol **"View Profile"** yang membawa pengguna ke halaman detail `/profile/[slug]` untuk mempelajari kisah serta katalog lengkap perfumer.
- Grid menyesuaikan kolom berdasarkan lebar layar: satu kolom di mobile, dua hingga tiga kolom di tablet/desktop.

### Tab "Brands"
- Struktur identik dengan tab perfumer, menggunakan `PerfumerCard` (atau varian brand) bergaya glassmorphism.
- Item yang ditampilkan adalah semua profil bertipe *Brand*.
- Setiap kartu memuat logo brand, nama, `@username`, ringkasan visi brand, dan statistik (misalnya jumlah parfum di katalog).
- Badge verifikasi juga tampil otomatis untuk brand yang telah disetujui kurator.
- Tombol **"View Profile"** menaut ke `/profile/[slug]` milik brand.

### Tab "Parfums"
- Disajikan dalam komponen `Table` yang dapat diurutkan.
- Kolom yang tersedia:
  - **Nama Parfum**: berbentuk tautan menuju halaman detail `/products/[id]`.
  - **Brand**: menampilkan nama brand pembuat parfum.
  - **Profil Aroma**: deretan `Badge` bertema glassmorphism yang menandai keluarga aroma, seperti "Floral", "Woody", atau "Citrus".
- Pengguna dapat melakukan sortasi berdasarkan nama parfum maupun brand untuk mempercepat penemuan produk.

## Sistem Kurasi Nusantarum
### 1. Pengajuan dari Halaman Profil
- Di halaman profil (`/profile/[slug]`), pemilik akun bertipe *Perfumer* atau *Brand* yang belum terverifikasi melihat tombol **"Ajukan Kurasi"**.
- Tombol hanya muncul ketika profil dilihat oleh pemiliknya sendiri dan `isCurated` bernilai `false`.

### 2. Dialog Pengajuan (`CurationDialog`)
- Menekan "Ajukan Kurasi" membuka `CurationDialog`.
- Dialog meminta pemilik brand/perfumer menulis pernyataan kurasi yang menjelaskan filosofi, proses kreatif, dan bahan yang digunakan sebagai bukti autentisitas.

### 3. Peninjauan Manual & Persetujuan
- Permohonan diteruskan ke panel admin (backend Nusantarum) yang dikelola kurator manusia.
- Kurator memeriksa data pendukung dan menandai pengajuan sebagai disetujui bila memenuhi kriteria autentisitas.

### 4. Publikasi Badge
- Ketika pengajuan disetujui, field `isCurated` pada profil diperbarui menjadi `true`.
- Lencana "Terverifikasi" secara otomatis muncul di kartu Nusantarum dan di halaman profil pengguna tersebut.
- Badge ini adalah bagian dari sistem gamifikasi platform dan menjadi simbol prestise tinggi.

## Integrasi Antar-Fitur
- **Halaman Profil**: Nusantarum berfungsi sebagai pintu masuk menuju profil detail. Semua tombol "View Profile" mengarahkan ke halaman profil untuk melanjutkan interaksi (misal mengikuti atau melihat produk terkait).
- **Halaman Produk**: Tabel "Parfums" menaut langsung ke detail produk, memberikan jalur cepat bagi pengguna untuk membaca catatan aroma atau melakukan pembelian.
- **Panel Admin**: Menjadi pusat keputusan kurasi; seluruh alur pengajuan dari pengguna ditinjau dan diputuskan di sini sebelum badge diberikan.
- **Sistem Lencana**: Badge "Nusantarum Verified" tersinkron ke seluruh ekosistem SensasiWangi, memastikan status kredibilitas terlihat di setiap tempat pengguna muncul.

## Perspektif Teknis & Alur Data
- **Pencarian Global**: Menggunakan satu state pencarian yang diteruskan ke query masing-masing tab. Implementasi dapat berupa store global (misal Zustand/Redux) atau context yang memicu fetch ulang data aktif.
- **Tabs ShadCN**: Tab terhubung ke kontainer konten yang merender komponen grid atau tabel sesuai pilihan. Transisi antar tab mempertahankan kata kunci pencarian agar pengalaman konsisten.
- **Komponen `PerfumerCard`**: Mengambil data profil termasuk status kurasi. Kartu memformat bio, menampilkan avatar (fallback jika kosong), dan menyediakan CTA ke profil.
- **Tabel Parfum**: Menyusun data parfum dengan kemampuan sort (client-side atau server-side) dan memformat profil aroma menjadi badge.
- **Kondisi Tombol Kurasi**: Validasi di halaman profil memeriksa identitas pengguna yang login, tipe profil, serta status kurasi sebelum merender tombol "Ajukan Kurasi".
- **Dialog Kurasi**: Menyimpan statement pengguna ke backend (misal melalui Supabase/REST). Data diteruskan ke panel admin untuk peninjauan.
- **Sinkronisasi Badge**: Setelah admin menyetujui, status `isCurated` diperbarui. UI otomatis merefleksikan perubahan melalui fetch ulang data atau subscription real-time.

## Dampak Pengalaman Pengguna
- Pengguna umum merasakan eksplorasi yang intuitif berkat pencarian terpadu dan tampilan tab yang konsisten.
- Perajin merasa dihargai karena ada jalur resmi untuk memperoleh pengakuan, dan badge verifikasi meningkatkan visibilitas mereka.
- Komunitas mendapatkan referensi kurasi yang dapat dipercaya, memperkuat ekosistem parfum lokal Indonesia.

