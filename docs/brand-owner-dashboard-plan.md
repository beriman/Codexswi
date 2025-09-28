# Rencana Halaman Dashboard Brand Owner

## 1. Tujuan Utama Dashboard
- Memberikan gambaran real-time atas performa penjualan dan aktivitas toko.
- Mempermudah brand owner dalam mengelola katalog produk.
- Menyediakan akses cepat ke tindakan operasional penting (promosi, restock, pengelolaan pesanan).

## 2. Persona Pengguna
- **Brand Owner / Admin Toko**: Fokus pada monitoring KPI, penjualan, stok, dan performa kampanye.
- **Co-founder / Admin Tambahan**: Memiliki akses peran tinggi untuk membantu pengelolaan strategis toko, termasuk pengaturan tim dan kebijakan operasional.
- **Staff Operasional**: Mendukung brand owner dalam update produk, stok, dan penanganan pesanan.

## 3. Struktur Informasi & Navigasi Utama
1. **Ringkasan (Overview)**
   - KPI penjualan (total penjualan hari ini/bulan ini, rata-rata order value, jumlah pesanan).
   - Status pesanan (baru, diproses, terkirim, bermasalah).
   - Pemberitahuan penting (stok menipis, produk pending approval, komplain terbaru).
2. **Manajemen Produk**
   - Daftar produk dengan status (aktif, draft, stok habis).
   - Aksi cepat: tambah produk, duplikasi, arsipkan.
   - Filter & pencarian (kategori, status, stok, harga).
3. **Manajemen Pesanan**
   - Tabel pesanan terbaru dengan status, nilai pesanan, pelanggan.
   - Akses ke detail pesanan dan tindakan (konfirmasi, ubah status, hubungi pelanggan).
4. **Analitik Penjualan**
   - Grafik tren penjualan harian/mingguan/bulanan.
   - Top produk terlaris dan kontribusinya.
   - Segmentasi pelanggan (baru vs kembali, wilayah utama).
5. **Promosi & Kampanye**
   - Status kampanye aktif dan performa (CTR, konversi, penjualan).
   - Rekomendasi kampanye atau voucher baru.
6. **Verifikasi Brand**
   - Status pengajuan verifikasi (draft, dikirim, disetujui, revisi diperlukan).
   - Checklist dokumen persyaratan (legalitas, identitas penanggung jawab, portofolio brand).
   - Riwayat komunikasi dengan admin/kurator platform.
7. **Pengaturan & Tim**
   - Pengelolaan akun, peran, dan izin (angkat/demosi co-founder atau admin tambahan, atur batasan akses).
   - Riwayat aktivitas tim untuk audit cepat.
   - Integrasi (payment gateway, ekspedisi).

## 4. Komponen UI Prioritas
- **Header**: Nama brand, tombol tambah produk, notifikasi, profil user.
- **KPI Cards**: Total penjualan, jumlah pesanan, revenue rata-rata, stok kritis.
- **Grafik Penjualan**: Line chart dengan range waktu fleksibel.
- **Tabel Pesanan & Produk**: Kolom dapat disesuaikan, aksi cepat.
- **Sidebar Navigasi**: Ikon dan label jelas untuk tiap modul.
- **Panel Notifikasi**: Alert stok, pesanan bermasalah, pesan pelanggan.
- **Modal/Drawer Manajemen Tim**: Form untuk mengundang anggota, memilih peran (co-founder, admin, staff), dan meninjau izin.
- **Form Wizard Verifikasi Brand**: Langkah-langkah pengisian data legalitas, unggah dokumen, dan konfirmasi submission ke admin/kurator.
- **Timeline Komunikasi Verifikasi**: Panel percakapan dengan admin/kurator beserta status aksi terakhir.

## 5. Alur Pengguna Kunci
1. **Monitoring Penjualan**
   - Masuk dashboard → lihat KPI ringkas → buka analitik detail jika perlu.
2. **Menambahkan Produk Baru**
   - Klik "Tambah Produk" → form multistep (informasi dasar, harga & stok, media, pengaturan variasi) → preview → submit.
3. **Mengelola Pesanan**
   - Buka modul pesanan → filter status → pilih pesanan → update status & catat nomor resi → kirim notifikasi ke pelanggan.
4. **Menjalankan Promosi**
   - Masuk modul kampanye → lihat performa → buat kampanye baru → pilih produk & diskon → jadwalkan → monitor hasil.
5. **Mengelola Tim & Peran**
   - Masuk modul Pengaturan & Tim → pilih "Undang Anggota" → masukkan email dan tentukan peran (co-founder/admin/staff) → kirim undangan → kelola status (aktif/nonaktif) dan izin granular.
6. **Mengajukan Verifikasi Brand**
   - Masuk modul Verifikasi → isi data legalitas brand dan penanggung jawab → unggah dokumen pendukung → kirim pengajuan → pantau status serta respon dari admin/kurator dan lakukan revisi bila diminta.

## 6. Integrasi Data & Teknologi
- **Sumber Data**: Penjualan, inventori, pelanggan dari backend utama; kampanye dari modul marketing.
- **Pembaruan Real-time**: Gunakan WebSocket atau polling untuk notifikasi stok & pesanan baru.
- **Analitik**: Integrasi dengan tool BI atau modul analitik internal untuk perhitungan KPI.
- **Manajemen Akses**: Integrasi dengan modul autentikasi/otorisasi untuk mengatur undangan pengguna, verifikasi email, dan audit log aktivitas tim.
- **Verifikasi Brand**: Integrasi layanan penyimpanan dokumen terenkripsi, workflow approval admin/kurator, dan notifikasi dua arah (dashboard + email) terkait status pengajuan.

## 7. Prioritas Pengembangan
1. Rilis awal: Overview, Manajemen Produk, Manajemen Pesanan.
2. Iterasi 2: Analitik penjualan detail & kampanye.
3. Iterasi 3: Pengaturan tim, integrasi advanced, rekomendasi berbasis AI.

## 8. Pertimbangan UX
- Gunakan visualisasi yang mudah dibaca, warna kontras untuk status kritis.
- Sediakan breadcrumb dan tooltip untuk istilah teknis.
- Pastikan aksesibilitas (kontras, keyboard navigation, alt text).

## 9. KPI Keberhasilan Dashboard
- Waktu rata-rata brand owner menemukan informasi penjualan harian < 30 detik.
- Peningkatan jumlah produk aktif per bulan.
- Penurunan pesanan bermasalah karena respon cepat dari notifikasi.
- Jumlah undangan admin/co-founder yang berhasil diaktifkan dan tingkat aktivitas mereka dalam 30 hari.
- Persentase pengajuan verifikasi brand yang selesai disetujui tanpa revisi lebih dari satu kali.
- Rata-rata waktu respon admin/kurator terhadap pengajuan verifikasi brand.

## 10. Next Steps
- Validasi kebutuhan dengan 3-5 brand owner.
- Buat wireframe low-fidelity untuk tiap modul.
- Susun backlog tugas berdasarkan prioritas rilis.
- Definisikan matriks peran & izin (brand owner, co-founder, admin, staff) bersama tim produk & legal.
- Tetapkan SOP verifikasi brand bersama tim kurasi dan rancang SLA respon admin/kurator.
