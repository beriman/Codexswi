# Daftar To-Do Implementasi UI/UX Sensasiwangi.id

Dokumen ini memecah fondasi desain ke rangkaian tugas implementasi yang siap dieksekusi dalam alat desain (Figma) sebelum handoff ke tim frontend. Checklist disusun mengikuti prioritas MVP dan sudah dilengkapi status awal, output yang diharapkan, serta dependensi lintas tim.

## Ringkasan Sprint & Dependency

| Sprint | Fokus Utama | Dependency Utama | Catatan |
| --- | --- | --- | --- |
| Sprint 1 | Setup sistem desain & navigasi global | Finalisasi fondasi visual | Pastikan asset font & warna tersimpan di shared library.
| Sprint 2 | Halaman marketplace & detail produk | Copywriting hero & CTA | Validasi dengan tim marketing sebelum prototyping.
| Sprint 3 | Dashboard internal & Nusantarum Hub | Data struktur CMS | Koordinasi dengan tim ops untuk requirement filter.
| Sprint 4 | Profil pengguna, animasi & handoff | Integrasi autentikasi | Kolaborasi dengan frontend untuk microinteraction.

Status legend: ☐ belum mulai · ◐ in-progress · ✅ selesai.

## 1. Setup Desain & Sistem Komponen

| Status | Task | Deskripsi | Deliverable |
| --- | --- | --- | --- |
| ☐ | Siapkan file desain kolaboratif | Buat file Figma baru dengan struktur page "Foundations", "Components", "Screens" dan atur permission editor untuk tim. | File Figma `Sensasiwangi_UI-MVP`. |
| ☐ | Definisikan style guide global | Implementasikan palet warna, token tipografi (Playfair Display & Inter), scale heading, dan state warna teks (default/hover/disabled). | Page "Foundations" berisi style guide lengkap. |
| ☐ | Bangun library komponen dasar | Desain button, card, input, badge, progress bar dengan variant state (default, hover, active, disabled). Gunakan Auto Layout dan component properties. | Page "Components" dengan publish library internal. |
| ☐ | Buat auto-layout responsif | Konfigurasi grid & Auto Layout untuk breakpoint desktop, tablet, mobile sesuai panduan foundation. Sertakan template frame untuk tiap breakpoint. | Template frame pada page "Foundations". |

## 2. Navigasi & Struktur Global

| Status | Task | Deskripsi | Deliverable |
| --- | --- | --- | --- |
| ☐ | Navbar sticky desktop & mobile | Desain versi desktop (menu penuh) dan mobile (hamburger drawer) dengan interaction notes. | Komponen navbar + prototipe open drawer. |
| ☐ | Struktur footer lengkap | Susun footer dengan CTA newsletter, tautan legal, sosial, highlight komunitas. Sertakan layout untuk mobile stack. | Frame footer + komponen auto layout. |
| ☐ | Breadcrumb template | Buat komponen breadcrumb dengan variant untuk 2-4 level halaman. | Komponen breadcrumb siap instansi. |

## 3. Halaman Prioritas MVP

### 3.1 Landing Page / Marketplace Overview

| Status | Task | Deskripsi | Deliverable |
| --- | --- | --- | --- |
| ☐ | Hero section | Desain headline, subcopy, CTA ganda, kartu statistik dengan background glassmorphism. Sertakan guideline animasi hero. | Frame hero + notes animasi. |
| ☐ | Tab kategori & filter | Implementasikan tab kategori, filter kaca, search bar, sort chip lengkap variant active/hover. | Komponen tab/filter + prototipe flow pencarian. |
| ☐ | Grid produk responsif | Buat grid dengan state hover, indikator sambatan (progress bar + deadline). Sertakan breakpoint desktop/tablet/mobile. | Frame grid multi breakpoint. |
| ☐ | Carousel highlight Nusantarum | Desain carousel kaca dengan navigation pill & CTA baca cerita. | Prototipe carousel (Figma smart animate). |
| ☐ | Footer CTA komunitas | Rancang footer CTA komunitas + newsletter dengan copy placeholder. | Frame footer section. |

### 3.2 Detail Produk

| Status | Task | Deskripsi | Deliverable |
| --- | --- | --- | --- |
| ☐ | Galeri foto | Buat komponen galeri dengan thumbnail, view utama, dan interaction untuk swap gambar. | Prototipe galeri interaktif. |
| ☐ | Panel informasi produk | Desain area harga, stok, deskripsi aroma (notes), CTA Sambatan/Pesanan dengan badge status. | Frame panel info produk. |
| ☐ | Modul info brand & cerita | Susun modul brand termasuk logo kaca, sertifikasi, link ke Nusantarum. | Komponen modul brand. |
| ☐ | Panel sambatan | Implementasi progress circle, slot tersisa, countdown, daftar kontributor terbaru. Sertakan property variant (aktif/penuh). | Frame panel sambatan dengan component properties. |

### 3.3 Dashboard Internal (Tim Ops)

| Status | Task | Deskripsi | Deliverable |
| --- | --- | --- | --- |
| ☐ | Layout sidebar + konten utama | Desain struktur dashboard dengan sidebar kaca, topbar, dan konten utama responsive. | Frame dashboard utama. |
| ☐ | Header metrik | Buat kartu KPI dengan highlight gradien & icon. | Komponen KPI card + variant status (naik/turun). |
| ☐ | Tabel pesanan | Desain tabel pesanan dengan filter status, tombol ekspor, empty state. | Komponen tabel + overlay filter. |
| ☐ | Drawer detail pesanan | Implementasikan panel kanan yang muncul saat baris dipilih berisi detail dan log aktivitas. | Prototipe interaction open drawer. |

### 3.4 Nusantarum Hub

| Status | Task | Deskripsi | Deliverable |
| --- | --- | --- | --- |
| ☐ | Hero kaca kuratorial | Desain hero section dengan headline, subcopy, CTA, background partikel aroma. | Frame hero Nusantarum. |
| ☐ | Panel filter multiplatform | Buat panel filter kategori aroma, wilayah, kurator untuk desktop & bottom sheet mobile. | Komponen filter + variant platform. |
| ☐ | Kartu cerita | Rancang kartu cerita Nusantarum termasuk foto, tag brand/perfumer, CTA baca. | Komponen kartu cerita. |
| ☐ | CTA ajukan cerita | Desain CTA dengan state hover & disabled, sertakan note integrasi form. | Komponen CTA + guideline handoff. |

### 3.5 Profil Pengguna

| Status | Task | Deskripsi | Deliverable |
| --- | --- | --- | --- |
| ☐ | Header profil | Bangun header profil (avatar kaca, nama, preferensi aroma chip) dengan editing state. | Frame header profil. |
| ☐ | Tab Aktivitas/Favorit/Sambatan | Implementasikan tab dan konten default per tab menggunakan component set. | Prototipe switch tab. |
| ☐ | Timeline aktivitas | Desain kartu timeline untuk aktivitas terbaru dengan icon status. | Komponen timeline card. |
| ☐ | Grid favorit & daftar sambatan | Buat layout favorit (grid) dan sambatan (list) dengan indicator status. | Frame tab Favorit & Sambatan. |

## 4. Interaksi & Animasi

| Status | Task | Deskripsi | Deliverable |
| --- | --- | --- | --- |
| ☐ | Animasi hover global | Dokumentasikan token animasi hover (translateY -2px, glow border, timing `ease-out 180ms`). | Guideline animasi pada page Foundations. |
| ☐ | Transisi antar halaman | Rancang transisi (fade-in + blur subtle) dan demokan dengan Smart Animate antar frame utama. | Prototipe transisi antar frame. |
| ☐ | Microinteraction komponen | Definisikan state dan feedback untuk tombol, progress bar, badge sambatan (mis. pulse countdown). | Notes interaksi + komponen variant. |

## 5. Aset & Dokumentasi Developer Handoff

| Status | Task | Deskripsi | Deliverable |
| --- | --- | --- | --- |
| ☐ | Export ikon Feather kustom | Kurasi ikon Feather dengan stroke 1.5px + neon glow jika perlu, export set SVG. | Folder aset ikon. |
| ☐ | Placeholder foto produk/brand | Siapkan template kontainer kaca dengan drop shadow, buat 3 variasi. | Frame placeholder siap export. |
| ☐ | Spesifikasi spacing & shadow | Dokumentasikan spacing, padding, shadow per komponen menggunakan Figma Measure. | Page dokumentasi komponen. |
| ☐ | Checklist QA visual | Susun checklist (kontras, keterbacaan, konsistensi grid) untuk review pra-handoff. | Checklist di Notion/Figma FigJam. |

## 6. Integrasi & Validasi

| Status | Task | Deskripsi | Deliverable |
| --- | --- | --- | --- |
| ☐ | Mapping komponen ke stack frontend | Workshop dengan tim frontend untuk menyelaraskan tokens dengan teknologi (Tailwind/React). | Dokumen mapping (Notion/Confluence). |
| ☐ | Prototipe interaktif utama | Buat prototipe interaktif (landing, detail produk, dashboard) untuk validasi flow. | Figma prototype siap user testing. |
| ☐ | Usability testing ringan | Jalankan testing 5-7 pengguna internal, catat temuan prioritas & rekomendasi. | Laporan testing singkat. |
| ☐ | Revisi & finalisasi desain | Terapkan feedback prioritas, tandai frame final, dan serahkan ke sprint development. | Page "Final Screens" terkunci. |

> Catatan: update status minimal setiap akhir sprint dan lampirkan link relevant (library, prototipe, dokumen QA) untuk menjaga alignment lintas tim.
