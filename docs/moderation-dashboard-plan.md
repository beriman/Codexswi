# Rencana Dashboard Moderator, Admin, dan Kurator

## 1. Tujuan Utama Dashboard
- Memberikan kontrol terpusat bagi admin utama untuk mengelola moderator dan kurator.
- Mempercepat proses review konten (produk, profil brand, kampanye) agar sesuai standar platform.
- Menyediakan alat monitoring kualitas ekosistem (pelanggaran, status review, SLA respon).
- Mendukung kolaborasi lintas peran dengan visibilitas status dan histori keputusan.

## 2. Persona Pengguna
- **Admin Utama**: Memiliki akses penuh, bertanggung jawab menambah/mengelola akun moderator dan kurator, mengatur kebijakan, dan memantau metrik kinerja keseluruhan.
- **Moderator**: Fokus pada peninjauan laporan komunitas, penegakan aturan, dan eskalasi kasus berat ke admin.
- **Kurator**: Bertugas mengkurasi konten/brand/produk yang akan ditampilkan, melakukan penilaian kualitas, dan memberi rekomendasi tindak lanjut.
- **Quality Lead / Supervisor** (opsional): Memantau performa tim moderator/kurator, melakukan audit sample, dan mengelola pelatihan.

## 3. Struktur Informasi & Navigasi
1. **Overview & Alerts**
   - Ringkasan jumlah item yang menunggu review (laporan komunitas, pengajuan brand, kampanye).
   - SLA tracker (jumlah overdue, rata-rata waktu respon per peran).
   - Notifikasi pelanggaran berat atau eskalasi.
2. **Manajemen Tim & Peran** (khusus admin utama)
   - Daftar pengguna dengan peran (admin, moderator, kurator).
   - Tombol "Tambah Pengguna" untuk mengundang/menetapkan peran baru.
   - Pengaturan izin granular (akses modul, kemampuan approve/reject, eskalasi).
   - Riwayat aktivitas (audit log) tiap anggota.
3. **Moderasi Laporan**
   - Antrian laporan (konten, pengguna, transaksi) dengan status (baru, dalam review, selesai, ditolak).
   - Filter berdasar kategori pelanggaran, tingkat prioritas, sumber laporan.
   - Detail laporan: konten terkait, riwayat tindakan, catatan internal.
   - Aksi cepat: tandai valid/tidak valid, suspend sementara, eskalasi ke admin.
4. **Kurasi Konten & Brand**
   - Daftar pengajuan brand/produk/kampanye untuk kurasi.
   - Checklist kualitas (foto, deskripsi, legalitas, reputasi seller).
   - Penilaian kurator (skor, rekomendasi tampil, perlu revisi).
   - Kolaborasi: komentar antar kurator/moderator, tag admin untuk keputusan final.
   - Mekanisme verifikasi berjenjang yang fokus pada level brand; ketika brand disetujui, seluruh produk turunannya otomatis berstatus terverifikasi.
5. **Analitik & Insight**
   - Tren jumlah laporan dan pengajuan per periode.
   - Top kategori pelanggaran, tingkat keberhasilan kurasi, repeat offenders.
   - Performa tim (SLA dipenuhi, jumlah review per orang, tingkat kesalahan ditemukan saat audit).
6. **Pengaturan Kebijakan & Template**
   - Dokumen SOP dan kebijakan moderasi/kurasi terbaru.
   - Template pesan keputusan (disetujui, ditolak, minta revisi) yang dapat diubah oleh admin.
   - Setting auto-escalation (misal laporan >3 kali otomatis suspend sementara).
7. **Pusat Bantuan Internal**
   - FAQ internal, materi pelatihan, jadwal coaching.
   - Form feedback dari moderator/kurator ke admin.

## 4. Fitur & Komponen UI Prioritas
- **Header**: Logo, switch peran (bagi user multi-role), notifikasi, profil.
- **Sidebar Navigasi**: Modul sesuai peran, item khusus admin disembunyikan untuk peran lain.
- **Cards KPI**: Total item pending, SLA rata-rata, jumlah eskalasi.
- **Tabel Antrian**: Kolom dapat disesuaikan, quick actions, status color-coded.
- **Panel Detail**: Slide-over modal untuk lihat detail laporan/pengajuan tanpa keluar dari antrian.
- **Form Undang Pengguna**: Multi-step (data akun, peran, level akses), hanya untuk admin utama.
- **Audit Trail Viewer**: Timeline interaktif menampilkan tindakan dan siapa yang melakukan.
- **Komentar Internal**: Thread diskusi pada setiap kasus pengajuan/laporan.
- **Bulk Actions**: Untuk moderator/kurator melakukan tindakan pada banyak item sekaligus (jika SOP mengizinkan).

## 5. Alur Pengguna Kunci
1. **Admin Menambah Moderator/Kurator**
   - Admin buka modul Manajemen Tim → klik "Tambah Pengguna" → isi data (nama, email, peran utama: moderator/kurator, modul akses tambahan) → kirim undangan → sistem kirim email aktivasi.
2. **Moderator Menangani Laporan**
   - Moderator lihat antrian laporan → filter prioritas tinggi → buka detail → cek histori & bukti → pilih tindakan (valid/invalid/suspend) → catat alasan → tandai selesai atau eskalasi.
3. **Kurator Menilai Pengajuan Brand**
   - Kurator masuk modul Kurasi → pilih pengajuan baru → review checklist & lampiran → beri skor + rekomendasi → kirim hasil ke admin atau minta revisi ke brand owner.
   - Jika brand disetujui, sistem menandai semua produk turunan brand tersebut sebagai terverifikasi tanpa perlu peninjauan ulang per produk.
4. **Admin Menetapkan Kebijakan Baru**
   - Admin buka modul Pengaturan Kebijakan → edit SOP/template → publish → moderator & kurator menerima notifikasi perubahan.
5. **Quality Lead Audit**
   - Quality Lead akses analitik → pilih sample kasus → buka audit trail → beri feedback ke moderator/kurator melalui komentar internal atau form evaluasi.

## 6. Integrasi Data & Teknologi
- **Sistem Autentikasi**: Integrasi dengan modul role-based access control, termasuk manajemen undangan dan verifikasi email.
- **Database Moderasi**: Menyimpan laporan, status, bukti, dan histori tindakan.
- **Workflow Engine**: Mendukung status multi-step (baru → dalam review → selesai/eskalasi) dan SLA tracker.
- **Notifikasi**: Email, in-app notification, dan mungkin integrasi Slack untuk eskalasi cepat.
- **Analitik**: Dashboard berbasis BI atau modul statistik internal untuk KPI moderasi/kurasi.
- **Penyimpanan Dokumen**: Untuk lampiran bukti pelanggaran dan dokumen pendukung brand.

## 7. Kebijakan Akses & Peran
- **Admin Utama**
  - Membuat/menghapus/mengubah peran pengguna.
  - Mengatur izin modul, membuat kebijakan, melihat semua data.
  - Menyetujui eskalasi dan keputusan akhir pada kasus kritis.
- **Moderator**
  - Mengelola antrian laporan, mengambil tindakan sesuai SOP.
  - Tidak dapat menambah pengguna baru atau mengubah kebijakan.
  - Dapat mengeskalasi kasus ke admin.
- **Kurator**
  - Menilai pengajuan konten/brand/produk.
  - Memberi rekomendasi tampil, revisi, atau tolak.
  - Fokus verifikasi pada level brand; setelah brand disetujui, produk turunannya otomatis dianggap terverifikasi.
  - Tidak dapat mengubah peran pengguna.
- **Quality Lead (opsional)**
  - Membaca semua kasus, menambahkan catatan audit.
  - Melihat analitik performa.

## 8. KPI & Monitoring Keberhasilan
- SLA penyelesaian laporan (median & 90th percentile).
- Jumlah laporan tertangani per moderator per hari.
- Persentase keputusan kurasi yang membutuhkan revisi ulang.
- Waktu rata-rata aktivasi moderator/kurator baru sejak diundang admin.
- Jumlah eskalasi ke admin dan waktu penyelesaiannya.
- Skor kualitas dari audit (kesesuaian keputusan dengan SOP).

## 9. Roadmap & Prioritas
1. **Rilis V1**: Overview & Alerts, Moderasi Laporan, Kurasi Konten dasar, Manajemen Tim sederhana (undang pengguna, ubah peran).
2. **Rilis V2**: Analitik performa, audit trail detail, komentar internal.
3. **Rilis V3**: Automation (auto-escalation, rekomendasi AI), integrasi chat internal, modul pelatihan.

## 10. Next Steps
- Lakukan workshop dengan admin dan 3-5 perwakilan moderator/kurator untuk validasi kebutuhan.
- Buat sketsa navigasi dan wireframe low-fidelity per modul.
- Definisikan matriks izin (CRUD per modul) bersama tim keamanan & legal.
- Rancang struktur data laporan dan pengajuan kurasi untuk mendukung analitik.
- Susun SOP aktivasi pengguna baru (undangan, onboarding, pelatihan awal).
