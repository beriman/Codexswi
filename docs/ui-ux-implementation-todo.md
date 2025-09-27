# Daftar To-Do Implementasi UI/UX Sensasiwangi.id

Dokumen ini merinci langkah implementasi UI/UX dari fondasi desain ke dalam antarmuka yang siap dikembangkan. Urutan tugas disusun berdasarkan prioritas delivery MVP.

## 1. Setup Desain & Sistem Komponen
- [ ] Siapkan file desain kolaboratif (Figma/penyunting setara) dengan gaya glassmorphism sesuai panduan foundation.
- [ ] Definisikan style guide global: warna, tipografi (Playfair Display & Inter), ukuran heading, dan states warna teks.
- [ ] Bangun library komponen dasar (button, card, input, badge, progress bar) lengkap dengan variasi state (default, hover, aktif, disabled).
- [ ] Buat auto-layout/grid responsif untuk breakpoint desktop, tablet, dan mobile.

## 2. Navigasi & Struktur Global
- [ ] Rancang layout navbar sticky dengan versi desktop dan mobile (hamburger drawer).
- [ ] Definisikan struktur footer lengkap (CTA newsletter, tautan legal, sosial, highlight komunitas).
- [ ] Siapkan breadcrumb template untuk halaman dalam (Dashboard, Profil).

## 3. Halaman Prioritas MVP
### 3.1 Landing Page / Marketplace Overview
- [ ] Desain hero section dengan headline, subcopy, CTA ganda, dan kartu statistik.
- [ ] Implementasikan tab kategori, filter kaca, search bar, dan sort chip.
- [ ] Buat grid produk responsif dengan states hover dan indikator sambatan (progress bar + deadline).
- [ ] Rancang carousel highlight Nusantarum.
- [ ] Bangun footer CTA komunitas + newsletter.

### 3.2 Detail Produk
- [ ] Siapkan galeri foto dengan thumbnail dan view utama.
- [ ] Desain panel informasi produk (harga, stok, deskripsi aroma, CTA Sambatan/Pesanan).
- [ ] Buat modul info brand dan tautan cerita Nusantarum.
- [ ] Implementasikan panel sambatan (progress circle, slot tersisa, countdown, kontributor terbaru).

### 3.3 Dashboard Internal (Tim Ops)
- [ ] Susun layout dengan sidebar kaca dan konten utama.
- [ ] Definisikan header ringkasan metrik (kartu KPI).
- [ ] Buat tabel pesanan dengan filter status dan tombol ekspor.
- [ ] Desain panel drawer detail pesanan yang muncul saat baris dipilih.

### 3.4 Nusantarum Hub
- [ ] Desain hero kaca dengan headline kuratorial.
- [ ] Buat panel filter (kategori aroma, wilayah, kurator) untuk desktop & mobile.
- [ ] Rancang kartu cerita Nusantarum termasuk tag brand/perfumer.
- [ ] Siapkan CTA "Ajukan cerita" dengan state hover.

### 3.5 Profil Pengguna
- [ ] Bangun header profil (avatar kaca, nama, preferensi aroma chip).
- [ ] Implementasikan tab Aktivitas, Favorit, Sambatan Saya.
- [ ] Desain timeline aktivitas dengan kartu kaca.
- [ ] Buat grid favorit dan daftar sambatan dengan indikator status.

## 4. Interaksi & Animasi
- [ ] Definisikan animasi hover umum (translateY -2px, glow border) dan timing function.
- [ ] Rancang transisi antar halaman (mis. fade-in + blur subtle) untuk menjaga kesan premium.
- [ ] Siapkan guideline microinteraction untuk tombol, progress bar, dan badge sambatan.

## 5. Aset & Dokumentasi Developer Handoff
- [ ] Export ikon Feather dengan gaya garis tipis + efek neon bila diperlukan.
- [ ] Siapkan placeholder foto produk/brand dengan kontainer kaca dan drop shadow.
- [ ] Dokumentasikan spesifikasi spacing, padding, dan shadow di setiap komponen.
- [ ] Susun checklist QA visual sebelum handoff (kontras, keterbacaan, konsistensi grid).

## 6. Integrasi & Validasi
- [ ] Kolaborasikan dengan tim frontend untuk mapping komponen desain ke stack teknologi.
- [ ] Buat prototipe interaktif utama (landing, detail produk, dashboard) untuk validasi flow.
- [ ] Lakukan usability testing ringan (5-7 pengguna internal) dan catat temuan prioritas.
- [ ] Revisi desain berdasarkan feedback dan siapkan versi final untuk development sprint.

