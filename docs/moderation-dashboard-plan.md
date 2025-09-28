# Rencana Dashboard Moderator, Admin, dan Kurator

## 1. Tujuan Utama Dashboard
- Memberikan kontrol terpusat bagi admin utama untuk mengelola moderator dan kurator.
- Mempercepat proses review konten (produk, profil brand, kampanye) agar sesuai standar platform.
- Menyediakan alat monitoring kualitas ekosistem (pelanggaran, status review, SLA respon).
- Mendukung kolaborasi lintas peran dengan visibilitas status dan histori keputusan.
- Menyediakan landasan data yang dapat diaudit guna memenuhi kebutuhan legal dan kepatuhan.

### Indikator Sukses
| Indikator | Target 6 bulan | Catatan |
| --- | --- | --- |
| SLA penanganan laporan prioritas tinggi | ≤ 4 jam | Dipantau harian oleh admin utama |
| Waktu aktivasi akun moderator baru | ≤ 24 jam | Dihitung sejak undangan dikirim |
| Tingkat akurasi keputusan kurasi | ≥ 90% | Diverifikasi melalui audit Quality Lead |
| Jumlah pelanggaran berulang | Turun 30% | Dibandingkan baseline sebelum peluncuran |

## 2. Persona Pengguna
- **Admin Utama**: Memiliki akses penuh, bertanggung jawab menambah/mengelola akun moderator dan kurator, mengatur kebijakan, dan memantau metrik kinerja keseluruhan.
- **Moderator**: Fokus pada peninjauan laporan komunitas, penegakan aturan, dan eskalasi kasus berat ke admin.
- **Kurator**: Bertugas mengkurasi konten/brand/produk yang akan ditampilkan, melakukan penilaian kualitas, dan memberi rekomendasi tindak lanjut.
- **Quality Lead / Supervisor** (opsional): Memantau performa tim moderator/kurator, melakukan audit sample, dan mengelola pelatihan.

### Kebutuhan Khusus per Persona
| Persona | Kebutuhan Utama | Hambatan Saat Ini |
| --- | --- | --- |
| Admin Utama | Visibilitas menyeluruh, kontrol peran, audit trail | Data tersebar, sulit melacak keputusan akhir |
| Moderator | Antrian prioritas, bukti lengkap, akses cepat ke SOP | Tools manual, keputusan lambat karena info terpisah |
| Kurator | Checklist kualitas, riwayat brand, kolaborasi mudah | Review dilakukan lewat spreadsheet dan chat terpisah |
| Quality Lead | Sampling kasus, metrik performa, catatan audit | Tidak ada dashboard audit terpusat |

## 3. Struktur Informasi & Navigasi
1. **Overview & Alerts**
   - Ringkasan jumlah item yang menunggu review (laporan komunitas, pengajuan brand, kampanye).
   - SLA tracker (jumlah overdue, rata-rata waktu respon per peran).
   - Notifikasi pelanggaran berat atau eskalasi.
   - Widget "Kasus Prioritas" dengan filter cepat ke kasus kritis.
2. **Manajemen Tim & Peran** (khusus admin utama)
   - Daftar pengguna dengan peran (admin, moderator, kurator).
   - Tombol "Tambah Pengguna" untuk mengundang/menetapkan peran baru.
   - Pengaturan izin granular (akses modul, kemampuan approve/reject, eskalasi).
   - Riwayat aktivitas (audit log) tiap anggota.
   - Pengaturan shift/jam kerja untuk distribusi antrian.
3. **Moderasi Laporan**
   - Antrian laporan (konten, pengguna, transaksi) dengan status (baru, dalam review, selesai, ditolak).
   - Filter berdasar kategori pelanggaran, tingkat prioritas, sumber laporan.
   - Detail laporan: konten terkait, riwayat tindakan, catatan internal.
   - Aksi cepat: tandai valid/tidak valid, suspend sementara, eskalasi ke admin.
   - Mekanisme penugasan otomatis berdasarkan kapasitas moderator.
4. **Kurasi Konten & Brand**
   - Daftar pengajuan brand/produk/kampanye untuk kurasi.
   - Checklist kualitas (foto, deskripsi, legalitas, reputasi seller).
   - Penilaian kurator (skor, rekomendasi tampil, perlu revisi).
   - Kolaborasi: komentar antar kurator/moderator, tag admin untuk keputusan final.
   - Mekanisme verifikasi berjenjang yang fokus pada level brand; ketika brand disetujui, seluruh produk turunannya otomatis berstatus terverifikasi.
   - Riwayat interaksi brand dan status produk turunannya.
5. **Analitik & Insight**
   - Tren jumlah laporan dan pengajuan per periode.
   - Top kategori pelanggaran, tingkat keberhasilan kurasi, repeat offenders.
   - Performa tim (SLA dipenuhi, jumlah review per orang, tingkat kesalahan ditemukan saat audit).
   - Heatmap waktu sibuk dan sumber laporan terbanyak.
6. **Pengaturan Kebijakan & Template**
   - Dokumen SOP dan kebijakan moderasi/kurasi terbaru.
   - Template pesan keputusan (disetujui, ditolak, minta revisi) yang dapat diubah oleh admin.
   - Setting auto-escalation (misal laporan >3 kali otomatis suspend sementara).
   - Log perubahan kebijakan dengan versi dan pemberi persetujuan.
7. **Pusat Bantuan Internal**
   - FAQ internal, materi pelatihan, jadwal coaching.
   - Form feedback dari moderator/kurator ke admin.
   - Direktori kontak (admin, Quality Lead, legal) untuk eskalasi langsung.

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
- **Mode Fokus**: Layout bebas distraksi untuk moderator yang mengerjakan kasus prioritas tinggi.
- **Pencarian Global**: Akses cepat ke brand, produk, atau tiket laporan dengan keyword.

### Komponen State Utama
| Komponen | State | Deskripsi |
| --- | --- | --- |
| Tabel Antrian | Empty, Loading, Error, Populated | Memastikan feedback visual pada setiap skenario data |
| Panel Detail | Read-only, Editable, Locked | Locked muncul saat kasus dipegang user lain |
| Form Undang Pengguna | Draft, Validated, Sent | Validated memastikan semua izin sesuai compliance |

## 5. Alur Pengguna Kunci
1. **Admin Menambah Moderator/Kurator**
   - Admin buka modul Manajemen Tim → klik "Tambah Pengguna" → isi data (nama, email, peran utama: moderator/kurator, modul akses tambahan) → kirim undangan → sistem kirim email aktivasi.
   - Setelah aktivasi, admin dapat menetapkan mentor/pelatih dan jadwal onboarding.
2. **Moderator Menangani Laporan**
   - Moderator lihat antrian laporan → filter prioritas tinggi → buka detail → cek histori & bukti → pilih tindakan (valid/invalid/suspend) → catat alasan → tandai selesai atau eskalasi.
   - Jika diperlukan bukti tambahan, moderator dapat meminta klarifikasi kepada pelapor lewat template pesan.
3. **Kurator Menilai Pengajuan Brand**
   - Kurator masuk modul Kurasi → pilih pengajuan baru → review checklist & lampiran → beri skor + rekomendasi → kirim hasil ke admin atau minta revisi ke brand owner.
   - Jika brand disetujui, sistem menandai semua produk turunan brand tersebut sebagai terverifikasi tanpa perlu peninjauan ulang per produk.
   - Kurator dapat membuat catatan pembelajaran untuk tim lain.
4. **Admin Menetapkan Kebijakan Baru**
   - Admin buka modul Pengaturan Kebijakan → edit SOP/template → publish → moderator & kurator menerima notifikasi perubahan.
   - Sistem menyimpan versi kebijakan lama untuk referensi audit.
5. **Quality Lead Audit**
   - Quality Lead akses analitik → pilih sample kasus → buka audit trail → beri feedback ke moderator/kurator melalui komentar internal atau form evaluasi.
   - Feedback masuk ke backlog perbaikan dan dapat ditandai selesai oleh pemilik tugas.

### User Story Tambahan
- Sebagai admin, saya ingin melihat siapa yang belum menyelesaikan onboarding agar dapat menindaklanjuti.
- Sebagai moderator, saya ingin menyimpan template catatan sehingga keputusan konsisten.
- Sebagai kurator, saya ingin mengetahui perubahan terbaru pada brand sebelum menyetujui kampanye baru.
- Sebagai Quality Lead, saya ingin menarik laporan audit dalam format CSV untuk dibahas pada weekly review.

## 6. Integrasi Data & Teknologi
- **Sistem Autentikasi**: Integrasi dengan modul role-based access control, termasuk manajemen undangan dan verifikasi email.
- **Database Moderasi**: Menyimpan laporan, status, bukti, dan histori tindakan.
- **Workflow Engine**: Mendukung status multi-step (baru → dalam review → selesai/eskalasi) dan SLA tracker.
- **Notifikasi**: Email, in-app notification, dan mungkin integrasi Slack untuk eskalasi cepat.
- **Analitik**: Dashboard berbasis BI atau modul statistik internal untuk KPI moderasi/kurasi.
- **Penyimpanan Dokumen**: Untuk lampiran bukti pelanggaran dan dokumen pendukung brand.
- **Integrasi Produk**: Sinkronisasi status brand dan produk dari katalog utama secara near real-time.
- **Sistem Logging**: Audit log terpusat dengan retensi minimal 1 tahun.

### Arsitektur Data Ringkas
| Entity | Atribut Kunci | Relasi |
| --- | --- | --- |
| User | id, nama, email, role, status onboarding | Memiliki banyak Assignment, ActivityLog |
| Assignment | id, tipe (laporan/kurasi), status, SLA_due | Terhubung ke User (assigned_to) dan Case |
| Case | id, tipe, sumber, bukti, history | Memiliki banyak Comment, Action |
| Brand | id, nama, status verifikasi, skor risiko | Memiliki banyak Product |
| Policy | id, versi, kategori, status publikasi | Memiliki banyak PolicyChangeLog |

## 7. Kebijakan Akses & Peran
- **Admin Utama**
  - Membuat/menghapus/mengubah peran pengguna.
  - Mengatur izin modul, membuat kebijakan, melihat semua data.
  - Menyetujui eskalasi dan keputusan akhir pada kasus kritis.
  - Mampu mengakses log audit lengkap.
- **Moderator**
  - Mengelola antrian laporan, mengambil tindakan sesuai SOP.
  - Tidak dapat menambah pengguna baru atau mengubah kebijakan.
  - Dapat mengeskalasi kasus ke admin.
  - Hanya melihat laporan yang relevan dengan peran/shift.
- **Kurator**
  - Menilai pengajuan konten/brand/produk.
  - Memberi rekomendasi tampil, revisi, atau tolak.
  - Fokus verifikasi pada level brand; setelah brand disetujui, produk turunannya otomatis dianggap terverifikasi.
  - Tidak dapat mengubah peran pengguna.
  - Dapat mengakses insight performa kurasi brand.
- **Quality Lead (opsional)**
  - Membaca semua kasus, menambahkan catatan audit.
  - Melihat analitik performa.
  - Mengunci kasus sementara untuk audit tanpa mengubah keputusan final.

### Matriks Izin Tingkat Tinggi
| Modul | Admin | Moderator | Kurator | Quality Lead |
| --- | --- | --- | --- | --- |
| Overview & Alerts | R/W | R | R | R |
| Manajemen Tim | R/W | - | - | R |
| Moderasi Laporan | R/W | R/W | R | R |
| Kurasi Konten | R/W | R | R/W | R |
| Analitik & Insight | R/W | R | R | R/W |
| Pengaturan Kebijakan | R/W | R | R | R |
| Pusat Bantuan | R/W | R/W | R/W | R/W |

## 8. KPI & Monitoring Keberhasilan
- SLA penyelesaian laporan (median & 90th percentile).
- Jumlah laporan tertangani per moderator per hari.
- Persentase keputusan kurasi yang membutuhkan revisi ulang.
- Waktu rata-rata aktivasi moderator/kurator baru sejak diundang admin.
- Jumlah eskalasi ke admin dan waktu penyelesaiannya.
- Skor kualitas dari audit (kesesuaian keputusan dengan SOP).
- Skor kepuasan internal tim moderasi terhadap tools (survei triwulan).
- Persentase kasus yang memerlukan banding ulang setelah keputusan final.

### Mekanisme Monitoring
- Automasi laporan mingguan dikirim ke admin & Quality Lead.
- Widget SLA di dashboard memberikan indikator merah/kuning/hijau.
- Audit sampling minimum 5% dari total keputusan kurasi setiap bulan.

## 9. Roadmap & Prioritas
1. **Rilis V1**: Overview & Alerts, Moderasi Laporan, Kurasi Konten dasar, Manajemen Tim sederhana (undang pengguna, ubah peran).
   - Fokus pada antrian, tindakan dasar, dan audit log minimum.
2. **Rilis V2**: Analitik performa, audit trail detail, komentar internal.
   - Termasuk role Quality Lead dan mode fokus untuk moderator.
3. **Rilis V3**: Automation (auto-escalation, rekomendasi AI), integrasi chat internal, modul pelatihan.
   - Integrasi advanced, rekomendasi prioritas otomatis, personalisasi insight.

### Dependensi Teknis
- Rilis V1 bergantung pada sistem autentikasi & RBAC stabil.
- Rilis V2 memerlukan data warehouse minimal 3 bulan sebagai baseline.
- Rilis V3 membutuhkan API internal untuk rekomendasi machine learning.

## 10. Next Steps
- Lakukan workshop dengan admin dan 3-5 perwakilan moderator/kurator untuk validasi kebutuhan.
- Buat sketsa navigasi dan wireframe low-fidelity per modul.
- Definisikan matriks izin (CRUD per modul) bersama tim keamanan & legal.
- Rancang struktur data laporan dan pengajuan kurasi untuk mendukung analitik.
- Susun SOP aktivasi pengguna baru (undangan, onboarding, pelatihan awal).
- Mulai pengumpulan baseline metrik (SLA, jumlah kasus, tingkat eskalasi) sebelum peluncuran.
- Tetapkan channel komunikasi eskalasi darurat (Slack/Email prioritas) dan protokolnya.

## 11. Risiko & Mitigasi
- **Kepatuhan Data**: Risiko data sensitif bocor. → Terapkan masking data dan audit akses berkala.
- **Overload Moderator**: Lonjakan laporan tanpa distribusi. → Gunakan auto-assignment berdasarkan kapasitas dan alert shift lead.
- **Perubahan Kebijakan Mendadak**: Kebingungan pada tim. → Implementasi notifikasi wajib dibaca dengan acknowledgement.
- **Ketergantungan Integrasi**: Modul gagal sinkron dengan sistem produk. → Siapkan fallback manual upload dan status healthcheck.

## 12. Lampiran Referensi
- Contoh template pesan keputusan (disetujui/ditolak/perlu revisi).
- Draft struktur tabel database (User, Case, Assignment, Comment, Policy).
- Checklist pelatihan onboarding moderator (SOP, simulasi kasus, evaluasi akhir).
