# Story: Optimasi Alur Onboarding Pengguna

- **Status:** Dalam Pengembangan
- **Epic/Theme:** Aktivasi Pengguna
- **Target Sprint:** Sprint 5
- **Dependencies:** Integrasi layanan email verifikasi
- **Owner:** TBA

## Latar Belakang
Alur onboarding saat ini memiliki drop-off tinggi pada tahap verifikasi email dan pengisian profil. Kita perlu menyederhanakan langkah-langkah dan memberikan umpan balik yang lebih jelas kepada pengguna baru.

## Tujuan & Nilai Bisnis
- Meningkatkan tingkat aktivasi pengguna baru sebesar 25%.
- Mempercepat proses onboarding menjadi maksimal 2 menit.
- Mengurangi tiket bantuan terkait onboarding.

## Workflow & Checklist
1. **Desain & Wireframe – UI/UX dasar dulu**
   - [ ] Audit alur onboarding eksisting dan identifikasi pain point.
   - [ ] Buat flowchart onboarding baru dengan reduksi langkah.
   - [ ] Desain wireframe mobile & desktop untuk form registrasi dan verifikasi.
   - [ ] Validasi desain dengan stakeholder produk & CS.
2. **Schema & DB Models – bikin tabel & schema, pastikan migrate jalan**
   - [ ] Review struktur tabel `users` dan `profiles` untuk kolom tambahan (mis. status onboarding).
   - [ ] Definisikan migration untuk log aktivitas onboarding dan timestamp verifikasi.
   - [ ] Pastikan indexing pada kolom email & token verifikasi untuk performa.
   - [ ] Jalankan migration di lingkungan development dan staging.
3. **CRUD & Service – logika bisnis + unit test**
   - [ ] Implementasi endpoint registrasi dengan validasi kuat & rate limiting.
   - [ ] Buat service verifikasi email dengan token kadaluarsa dan retry limit.
   - [ ] Tambahkan unit test untuk service registrasi, verifikasi, dan logging onboarding.
   - [ ] Dokumentasi API untuk tim frontend.
4. **Frontend Integration – bikin UI connect ke API**
   - [ ] Hubungkan form registrasi dengan endpoint baru (error handling & loading state).
   - [ ] Implementasi halaman verifikasi dengan feedback status real-time.
   - [ ] Tambahkan progress indicator onboarding dan CTA ke langkah berikutnya.
   - [ ] Lakukan tes usability singkat dengan minimal 3 pengguna internal.
5. **Testing & QA – test end-to-end**
   - [ ] Siapkan skenario E2E (registrasi → verifikasi → pengisian profil).
   - [ ] Jalankan automated E2E test (desktop & mobile viewport).
   - [ ] Regression test modul login & profil untuk memastikan tidak ada dampak.
   - [ ] Kumpulkan feedback QA dan validasi perbaikan.
6. **Deploy – staging dulu, lalu production**
   - [ ] Deploy perubahan backend & frontend ke staging, sertakan checklist release.
   - [ ] Verifikasi monitoring log & alerting di staging selama 24 jam.
   - [ ] Koordinasi dengan CS sebelum deploy ke production.
   - [ ] Deploy ke production dan lakukan post-deploy review + rollback plan.

## Acceptance Criteria
- Pengguna baru dapat menyelesaikan onboarding dalam ≤ 3 langkah.
- Email verifikasi terkirim < 10 detik dan log status tersimpan.
- Terdapat progress indicator yang menunjukkan status onboarding.
- Unit test lulus dengan coverage > 80% untuk modul onboarding.

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
