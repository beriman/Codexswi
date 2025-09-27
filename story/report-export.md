# Story: Fitur Ekspor Laporan Penjualan ke CSV & XLSX

- **Status:** Backlog
- **Epic/Theme:** Pelaporan & Analitik
- **Target Sprint:** Sprint 6 (tentatif)
- **Dependencies:** Penyesuaian endpoint agregasi penjualan
- **Owner:** TBA

## Latar Belakang
Tim sales memerlukan kemampuan untuk mengekspor laporan penjualan harian dan mingguan ke format CSV maupun XLSX agar dapat dianalisis secara offline atau dibagikan ke mitra. Saat ini hanya tersedia tampilan dashboard tanpa opsi unduh.

## Tujuan & Nilai Bisnis
- Memudahkan tim sales & finance melakukan analisis lanjutan.
- Mengurangi waktu manual pembuatan laporan harian.
- Menyediakan format standar untuk berbagi data ke pihak eksternal.

## Workflow & Checklist
1. **Desain & Wireframe – UI/UX dasar dulu**
   - [ ] Identifikasi lokasi tombol ekspor pada dashboard laporan penjualan.
   - [ ] Desain wireframe pop-up pilihan format & rentang tanggal.
   - [ ] Sinkronkan desain dengan guideline brand & aksesibilitas.
   - [ ] Review desain bersama stakeholder sales & finance.
2. **Schema & DB Models – bikin tabel & schema, pastikan migrate jalan**
   - [ ] Evaluasi kebutuhan tabel baru untuk menyimpan histori ekspor (audit trail).
   - [ ] Definisikan migration untuk tabel `report_exports` dengan metadata (user, rentang tanggal, status).
   - [ ] Siapkan indeks pada kolom `created_at` dan `requested_by` untuk pelacakan cepat.
   - [ ] Uji migration di environment development.
3. **CRUD & Service – logika bisnis + unit test**
   - [ ] Implementasi service agregasi data penjualan per periode dengan pagination.
   - [ ] Buat generator file CSV & XLSX dengan pembatasan ukuran.
   - [ ] Tambahkan endpoint request ekspor beserta otentikasi & otorisasi per role.
   - [ ] Unit test untuk service agregasi, generator file, dan controller.
4. **Frontend Integration – bikin UI connect ke API**
   - [ ] Integrasikan tombol ekspor dan modal pemilihan format.
   - [ ] Tambahkan indikator progres & notifikasi keberhasilan/gagal.
   - [ ] Pastikan UI tetap responsif di berbagai resolusi.
   - [ ] Dokumentasikan alur di handbook tim sales.
5. **Testing & QA – test end-to-end**
   - [ ] Buat test case E2E untuk ekspor CSV & XLSX (berhasil dan gagal).
   - [ ] Verifikasi ukuran file & struktur kolom sesuai spesifikasi bisnis.
   - [ ] Lakukan uji performa untuk memastikan proses ekspor < 15 detik.
   - [ ] QA regression pada modul dashboard laporan.
6. **Deploy – staging dulu, lalu production**
   - [ ] Deploy backend & frontend ke staging, cantumkan panduan testing di release note.
   - [ ] Validasi monitoring queue/background job jika digunakan.
   - [ ] Latih tim sales menggunakan fitur baru di staging.
   - [ ] Rilis ke production dengan jadwal low traffic & buat announcement.

## Acceptance Criteria
- Pengguna dapat memilih rentang tanggal dan format (CSV/XLSX) sebelum ekspor.
- File terunduh memiliki header kolom sesuai definisi bisnis dan tidak korup.
- Tersedia log histori ekspor yang dapat dilihat oleh admin.
- Unit test modul ekspor lulus dengan coverage minimal 80%.

## Catatan Pengembangan (diisi oleh agent developer)
- Tanggal mulai:
- Ringkasan progres:
- Risiko/Blocker:
- Catatan lintas tim:

## Catatan Review & QA (diisi oleh agent reviewer)
- Checklist review kode:
- Hasil QA & bug yang ditemukan:
- Rekomendasi penerimaan:
- Catatan deployment:
