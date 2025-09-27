# Daftar To-Do Implementasi UI/UX Sensasiwangi.id (Versi Tanpa Figma)

Dokumen ini memetakan pekerjaan UI/UX langsung ke artefak kode pada stack FastAPI + HTMX + Jinja2. Referensi visual utama menggunakan contoh mockup (glassmorphism futuristik) yang sudah diberikan, sehingga setiap tugas berfokus pada implementasi HTML/CSS/JS dan dokumentasi teknis tanpa perantara file desain.

Legenda status: ☐ belum mulai · ◐ in-progress · ✅ selesai.

## 0. Panduan Visual & Prinsip Umum

| Status | Task | Deskripsi Implementasi | Deliverable |
| --- | --- | --- | --- |
| ☐ | Kanvas inspirasi UI | Tangkap elemen kunci dari mockup (palet, tipografi serif+sans, bubble glass, refleksi) dan tuangkan ke dokumen panduan kode. Sertakan referensi ukuran dan behavior animasi dasar. | `docs/ui-style-reference.md` berisi moodboard singkat + token awal. |
| ☐ | Susun token desain berbasis CSS | Definisikan CSS custom properties untuk warna, radius, blur, shadow, gradient dan timing animasi sesuai mockup. Token dideklarasikan di `:root` dan dipublikasikan melalui `static/css/tokens.css`. | File `src/app/web/static/css/tokens.css` berisi token komprehensif. |
| ☐ | Setup tipografi & ikon | Implementasi font Playfair Display + Inter (atau alternatif open source mirip) via `@font-face`/Google Fonts, serta siapkan set ikon Feather/Phosphor yang akan dipakai. | Update `base.html` + `static/css/base.css` untuk import font & ikon. |

## 1. Sistem Desain Berbasis Kode

| Status | Task | Deskripsi Implementasi | Deliverable |
| --- | --- | --- | --- |
| ☐ | Utilitas glassmorphism | Buat kelas utilitas (mis. `.glass-card`, `.glass-panel`, `.blur-pill`) yang mengatur backdrop-filter, border, dan shadow sesuai inspirasi UI. | `static/css/glass.css` + dokumentasi pemakaian di `docs/ui-style-reference.md`. |
| ☐ | Komponen tombol & chip | Rancang varian tombol utama/sekunder/ghost serta chip filter dengan state hover/active menggunakan CSS variables & HTMX states. | Partial `templates/components/button.html` + CSS di `static/css/components/button.css`. |
| ☐ | Komponen kartu & badge status | Implementasikan kartu produk dengan preview gambar, badge sambatan, dan progress bar radial sesuai sample 3D. Sediakan versi horizontal dan grid. | `templates/components/product-card.html` + CSS & script animasi progress. |
| ☐ | Layout responsif dasar | Definisikan grid dan spacing untuk breakpoint desktop/tablet/mobile menggunakan CSS Grid/Flex. Sertakan helper kelas `container-xl`, `stack-lg` dsb. | `static/css/layout.css` + README singkat pada file yang sama. |

## 2. Navigasi & Struktur Global

| Status | Task | Deskripsi Implementasi | Deliverable |
| --- | --- | --- | --- |
| ☐ | Navbar sticky adaptif | Implementasikan navbar glass dengan menu utama, indikator halaman aktif, CTA login/signup, serta varian mobile (drawer). Gunakan HTMX untuk aksi open/close. | `templates/partials/navbar.html`, CSS di `static/css/components/navbar.css`, dan skrip `static/js/navbar.js`. |
| ☐ | Footer komunitas | Bangun footer dengan CTA newsletter, link legal, sosial, dan highlight komunitas. Pastikan layout stack rapi di mobile. | `templates/partials/footer.html` + CSS pendukung. |
| ☐ | Breadcrumb reusable | Buat component breadcrumb HTML dengan data-props Jinja (list tuple). Sediakan styling glass pill dan fallback mobile (horizontal scroll). | `templates/components/breadcrumb.html` + CSS. |

## 3. Halaman Prioritas MVP

### 3.1 Landing Page / Marketplace Overview

| Status | Task | Deskripsi Implementasi | Deliverable |
| --- | --- | --- | --- |
| ☐ | Hero interaktif | Bangun hero dengan headline besar, subcopy, CTA ganda, slider produk unggulan dan latar bubble 3D (SVG atau Lottie). Sertakan animasi hover subtle. | `templates/pages/landing.html` (section hero) + asset di `static/media/hero`. |
| ☐ | Tab kategori & filter | Implementasikan tab + filter kaca menggunakan HTMX untuk swap konten tanpa reload. Sediakan chip active/hover, search bar, dan sort toggle. | Partial `templates/components/category-tabs.html` + JS `static/js/tabs.js`. |
| ☐ | Grid produk responsif | Layout grid dengan indikator sambatan (progress bar + deadline) dan varian card untuk desktop/tablet/mobile. Pastikan `aria` label lengkap. | Block pada landing.html + CSS di `components/product-grid.css`. |
| ☐ | Carousel highlight Nusantarum | Implementasikan carousel horizontal dengan pill navigation dan auto-play opsional menggunakan Swiper.js atau implementasi custom. | Partial `templates/components/story-carousel.html` + JS `static/js/carousel.js`. |
| ☐ | Footer CTA komunitas | Section CTA akhir dengan glass panel dan call-to-action bergaya mockup. | Section di landing.html + CSS section. |

### 3.2 Detail Produk

| Status | Task | Deskripsi Implementasi | Deliverable |
| --- | --- | --- | --- |
| ☐ | Galeri foto produk | Implementasikan viewer utama + thumbnail scroll dengan efek parallax ringan. Dukungan keyboard navigation dan fallback non-JS. | Partial `templates/components/product-gallery.html` + JS `static/js/gallery.js`. |
| ☐ | Panel informasi produk | Panel kanan berisi harga, stok, deskripsi aroma, CTA Sambatan/Pesanan dengan badge status. Pastikan sticky di desktop. | `templates/pages/product_detail.html` section info + CSS. |
| ☐ | Modul info brand | Kartu brand kaca dengan logo, sertifikasi, link Nusantarum, CTA follow. | Partial `templates/components/brand-module.html`. |
| ☐ | Panel sambatan | Komponen progress radial, slot tersisa, countdown realtime (menggunakan Stimulus/HTMX). Varian state aktif/penuh/tutup. | JS `static/js/sambatan-panel.js` + partial HTML & CSS. |

### 3.3 Dashboard Internal (Ops)

| Status | Task | Deskripsi Implementasi | Deliverable |
| --- | --- | --- | --- |
| ☐ | Layout dashboard | Sidebar kaca, topbar, dan konten utama responsif. Gunakan CSS Grid dua kolom + collapse mobile. | `templates/pages/dashboard/index.html` + CSS `static/css/dashboard.css`. |
| ☐ | Header metrik | Kartu KPI dengan gradient glow, icon, delta up/down. Animated counters optional. | Partial `templates/components/kpi-card.html` + JS kecil untuk animasi angka. |
| ☐ | Tabel pesanan | Tabel dengan filter status (tabs), tombol ekspor, empty state ilustrasi. Responsif via CSS `display: block` di mobile. | Partial `templates/components/order-table.html` + CSS/JS filter. |
| ☐ | Drawer detail pesanan | Drawer kanan yang muncul saat klik baris, menampilkan detail & log. Implementasi HTMX swap + overlay backdrop. | Template `templates/components/order-drawer.html` + JS `static/js/drawer.js`. |

### 3.4 Nusantarum Hub

| Status | Task | Deskripsi Implementasi | Deliverable |
| --- | --- | --- | --- |
| ☐ | Hero kuratorial | Hero kaca dengan headline, subcopy, CTA, background partikel (canvas/SVG). | Section `templates/pages/nusantarum.html` + asset. |
| ☐ | Panel filter multiplatform | Panel filter desktop + bottom sheet mobile (dialog). Gunakan CSS `position: sticky` dan HTMX update results. | `templates/components/nusantarum-filter.html` + JS `static/js/filter-sheet.js`. |
| ☐ | Kartu cerita | Kartu cerita dengan foto, tag brand/perfumer, CTA. Pastikan variant grid/list. | Partial `templates/components/story-card.html`. |
| ☐ | CTA ajukan cerita | Form CTA dengan state hover, disabled, dan note integrasi backend. | Section + CSS. |

### 3.5 Profil Pengguna

| Status | Task | Deskripsi Implementasi | Deliverable |
| --- | --- | --- | --- |
| ☐ | Header profil | Header kaca dengan avatar, nama, preferensi aroma chip, dan tombol edit. | Section `templates/pages/profile.html` + CSS. |
| ☐ | Tab aktivitas/favorit/sambatan | Tab berbasis HTMX untuk switch konten tanpa reload, dengan animasi underline. | `templates/components/profile-tabs.html` + JS `static/js/profile-tabs.js`. |
| ☐ | Timeline aktivitas | Komponen timeline card dengan icon status, timestamp, deskripsi. | Partial `templates/components/activity-card.html`. |
| ☐ | Grid favorit & daftar sambatan | Layout grid/list dengan status indicator & CTA lanjutkan. | Blocks di profile.html + CSS. |

## 4. Interaksi & Animasi

| Status | Task | Deskripsi Implementasi | Deliverable |
| --- | --- | --- | --- |
| ☐ | Token animasi global | Definisikan utilitas animasi (hover lift, fade-blur, glow pulse) dalam `static/css/animation.css` dan contoh di dokumentasi. | File animasi + update doc gaya. |
| ☐ | Transisi antar halaman | Implementasi transisi halus menggunakan HTMX `hx-boost` + CSS `view-transition` (jika didukung) atau fallback fade. | Skrip `static/js/page-transitions.js` + konfigurasi di base template. |
| ☐ | Microinteraction komponen | Tambahkan feedback state untuk tombol, progress bar, badge sambatan (pulse countdown). Deskripsikan perilaku di dokumentasi. | Update CSS/JS terkait + section dokumentasi. |

## 5. Aset & Dokumentasi Handoff Developer

| Status | Task | Deskripsi Implementasi | Deliverable |
| --- | --- | --- | --- |
| ☐ | Paket ikon & ilustrasi | Kumpulkan ikon SVG dan ilustrasi latar bubble sesuai gaya. Optimasi via SVGO. | Direktori `static/icons/` & `static/illustrations/` + README listing. |
| ☐ | Placeholder produk & brand | Sediakan placeholder gambar dengan efek kaca (PNG/WebP) untuk fallback. | Folder `static/media/placeholders/`. |
| ☐ | Dokumentasi spacing & shadow | Tuliskan guideline di `docs/ui-style-reference.md` terkait jarak, layering, depth. | Update dokumen referensi. |
| ☐ | Checklist QA visual | Buat checklist HTML/Markdown untuk review kontras, responsive, accesibility (keyboard, aria). | `docs/ui-qa-checklist.md`. |

## 6. Integrasi & Validasi

| Status | Task | Deskripsi Implementasi | Deliverable |
| --- | --- | --- | --- |
| ☐ | Mapping komponen ke backend | Dokumentasikan bagaimana tiap komponen template menerima data (context dict). Sertakan contoh payload. | `docs/ui-component-contracts.md`. |
| ☐ | Prototipe interaktif via Storybook/Pattern Library | Setup Storybook (atau alternatif minimal `docs/site` dengan `npm run dev`) untuk preview komponen glass secara isolasi. | Konfigurasi Storybook di `story/` + panduan run. |
| ☐ | Usability testing ringan | Jalankan tes internal (5-7 orang) menggunakan build SSR aktual, catat temuan. | Laporan `docs/research/usability-round1.md`. |
| ☐ | Revisi & finalisasi | Terapkan feedback, tandai komponen siap produksi, update changelog. | Update doc + commit changelog di `docs/ui-style-reference.md`. |

> Catatan: seluruh deliverable harus versioned di repo ini. Gunakan screenshot dari implementasi aktual (bukan Figma) untuk dokumentasi visual.
