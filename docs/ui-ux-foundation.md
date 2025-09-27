# Sensasiwangi.id UI/UX Foundation

Dokumen ini merangkum bahasa desain, prinsip interaksi, serta wireframe tekstual yang menjadi fondasi implementasi MVP Sensasiwangi.id. Fokus utama adalah menghadirkan pengalaman glassmorphism yang hangat, navigasi intuitif, dan pola komponen reusable agar tim desain maupun engineering memiliki referensi tunggal.

## 1. Tujuan & Sasaran Pengalaman

- Menonjolkan karakter brand parfum Nusantara yang modern namun tetap organik.
- Menyatukan pengalaman marketplace (brand) dan sambatan (komunitas) dalam satu alur yang konsisten.
- Menyediakan kerangka kerja visual yang mudah diimplementasikan ke komponen frontend berbasis kartu kaca.
- Menjamin aksesibilitas dasar (kontras, fokus state, hierarki tipografi) sejak tahap awal.

## 2. Bahasa Visual & Token Desain

### 2.1 Palet Warna

| Token | Nilai | Penggunaan |
|-------|-------|------------|
| `--color-bg` | `linear-gradient(180deg, #0F172A 0%, #1E293B 100%)` | Latar belakang global, hero |
| `--color-surface` | `rgba(15, 23, 42, 0.65)` | Kartu kaca, panel filter |
| `--color-border` | `rgba(255, 255, 255, 0.20)` | Outline kartu, input |
| `--color-accent` | `linear-gradient(135deg, #F97316 0%, #C026D3 100%)` | Tombol utama, highlight progres |
| `--color-text-primary` | `#F8FAFC` | Heading, teks utama |
| `--color-text-secondary` | `#CBD5F5` | Copy sekunder, helper text |
| `--color-info` | `#38BDF8` | Link, badge info |
| `--color-success` | `#34D399` | Status terpenuhi |
| `--color-warning` | `#FB923C` | Batas waktu sambatan |

### 2.2 Tipografi

- Heading: **Playfair Display** (serif modern) untuk judul hero, heading seksi, CTA hero.
- Body & UI: **Inter** untuk isi teks, label form, dan meta informasi.
- Ukuran dasar: `16px` dengan skala modular `1.125` (16 → 18 → 20 → 24 → 27 → 32 → 36 → 48).

### 2.3 Ikonografi & Imagery

- Ikon garis tipis (Feather) dengan glow samar (`drop-shadow(0 6px 12px rgba(236, 72, 153, 0.25))`).
- Placeholder gambar menggunakan kartu kaca dengan blur `20px`, sudut `24px`, dan highlight gradien diagonal.
- Media komunitas menampilkan overlay partikel aroma (SVG ringan) untuk konsistensi brand.

## 3. Pola Layout & Responsivitas

- **Grid Desktop (≥1280px)**: Lebar maksimum 1200px dengan gutter 32px. Produk ditampilkan 3 kolom.
- **Tablet (768–1279px)**: Grid 2 kolom, panel filter menjadi horizontal scroll, navigasi berubah menjadi hamburger.
- **Mobile (≤767px)**: Satu kolom penuh, filter menjadi bottom sheet dengan tombol sticky "Filter".
- Margin vertikal utama menggunakan kelipatan 40px desktop, 32px tablet, 24px mobile.

## 4. Navigasi Global & Template Dasar

```
┌──────────────────────────────────────────────────────────────┐
│ Navbar kaca: Logo | Marketplace | Sambatan | Nusantarum | ... │
│ CTA sekunder "Gabung Komunitas" (ghost glass button)         │
└──────────────────────────────────────────────────────────────┘
```

- Navbar sticky dengan blur `backdrop-filter: blur(24px)` dan border kaca.
- Mode mobile: tombol hamburger membuka drawer kaca penuh dengan daftar menu dan CTA.
- Footer menampilkan CTA newsletter, tautan legal, sosial media, serta highlight komunitas terbaru.

## 5. Wireframe Tekstual Layar Kunci

### 5.1 Landing / Marketplace Overview

```
Hero Kolaboratif
┌──────────────────────────────────────────────┐
│ Background gradient + animasi partikel aroma │
│ Headline: "Eksplorasi Wewangian Nusantara"   │
│ Subcopy + CTA: "Telusuri Marketplace"       │
│ Stat Card: Brand Terkurasi | Sambatan Aktif  │
└──────────────────────────────────────────────┘

Filter & Tabs Kategori
┌───────────┬───────────────┬────────────┬───────────────┐
│ Tab: Parfum | Raw Material | Peralatan | Lain-lain     │
│ Search kaca│ Sort chip     │ Aroma tags │ Reset filter  │
└───────────┴───────────────┴────────────┴───────────────┘

Grid Produk 3 kolom
┌───────┐ ┌───────┐ ┌───────┐
│ Foto  │ │ Foto  │ │ Foto  │
│ Nama  │ │ Nama  │ │ Nama  │
│ Harga │ │ Harga │ │ Harga │
│ Progress Sambatan (jika ada)               │
└───────┘ └───────┘ └───────┘

Highlight Nusantarum (carousel kaca)
CTA Komunitas & Newsletter
```

### 5.2 Halaman Marketplace Mandiri

```
Hero dua kolom: copy kolaboratif + panel filter kaca
Filter responsif: kategori, rentang harga, asal brand, status sambatan
Seksi "Kurasi Brand": kartu produk brand dengan badge Bestseller/Limited
Seksi "Karya Komunitas": kartu sambatan + progres, slots left, deadline
Kartu CTA kurator: "Hubungi Kurator" & "Panduan Listing"
```

### 5.3 Detail Produk

```
┌──────────────┬────────────────────────────────────┐
│ Galeri foto  │ Nama produk + badge Sambatan       │
│ thumbnail    │ Harga indikatif + stok             │
│              │ Deskripsi aroma (notes top-mid-base)│
│              │ CTA: "Ajukan Pesanan" / "Gabung"   │
└──────────────┴────────────────────────────────────┘

Info Brand & Story Link
┌──────────────────────────────────────────────┐
│ Logo kaca kecil, deskripsi singkat, sertifikasi│
│ Link ke cerita Nusantarum & CTA chat          │
└──────────────────────────────────────────────┘

Panel Sambatan
┌────────────────────┐
│ Progress circle    │
│ Slot tersisa       │
│ Deadline countdown │
│ Kontributor terbaru│
└────────────────────┘
```

### 5.4 Dashboard Internal (Ops)

```
Sidebar kaca vertikal | Konten utama
Header ringkasan metrik (Pesanan aktif, Sambatan aktif, Slot terisi)
Tab: Pesanan | Sambatan | Brand | Konten
Tabel pesanan dengan filter status + tombol ekspor CSV
Drawer kanan ketika baris dipilih menampilkan detail & log aktivitas
```

### 5.5 Nusantarum Hub

```
Hero kaca dengan headline kuratorial
Filter kiri (desktop): kategori aroma, wilayah, kurator
Grid 2 kolom berisi card cerita + tag brand/perfumer
CTA: "Ajukan cerita" untuk kurator dan form submission ringan
```

### 5.6 Profil Pengguna

```
Header profil: avatar kaca, nama, chip preferensi aroma
Tab: Aktivitas | Favorit | Sambatan Saya
Aktivitas → timeline kartu kaca (pesanan terakhir, sambatan bergabung)
Favorit → grid produk/brand tersimpan
Sambatan Saya → daftar progres bar + status
```

## 6. Komponen Reusable

| Komponen | Visual | Status Interaksi |
|----------|--------|------------------|
| **Primary Button** | Gradien jingga→ungu, radius 999px, shadow kaca | Hover: naik 2px, glow border |
| **Secondary Button** | Latar kaca transparan, border `#38BDF833`, teks aqua | Hover: border solid |
| **Glass Card** | Surface kaca, blur 20px, border tipis | Hover: `transform: translateY(-2px)` |
| **Input Field** | Prefix icon, placeholder `#94A3B8` | Fokus: border gradien & glow lembut |
| **Progress Bar** | Track kaca, fill gradien, label persentase | Animasi fill halus |
| **Badge Sambatan** | Chip kaca kecil dengan ikon tangan | Pulse halus menjelang deadline |

State fokus untuk setiap komponen harus menggunakan outline `2px` dengan warna `#38BDF8` dan offset `2px` agar aksesibilitas keyboard terjaga.

## 7. Prinsip Interaksi

1. **Transisi Halus** – Gunakan durasi `200ms` untuk hover, `300ms` untuk overlay masuk/keluar.
2. **Feedback Langsung** – Setiap aksi (tambah favorit, gabung sambatan) menampilkan toast kaca di pojok kanan atas.
3. **Status Availability** – Produk terbatas menampilkan indikator label & progres; item habis stok memiliki overlay redup + CTA daftar tunggu.
4. **Konten Prioritas** – Hero menonjolkan kampanye kolaboratif, sedangkan grid menampilkan kombinasi brand resmi dan kreasi komunitas secara seimbang.

## 8. Checklist Implementasi

- [ ] Partial `base.html` memuat token warna, font, dan slot navbar/footer.
- [ ] Komponen `GlassCard`, `GradientButton`, `ProgressIndicator`, dan `Badge` tersedia sebagai utilitas CSS.
- [ ] Validasi kontras teks terhadap latar kaca mengikuti standar WCAG AA.
- [ ] Pastikan animasi dapat dinonaktifkan saat prefers-reduced-motion aktif.
- [ ] Dokumentasikan variasi mobile vs desktop sebelum handoff ke engineering.

---

Dokumen ini menjadi referensi utama bagi tim lintas fungsi untuk menjaga konsistensi UI/UX, mempermudah iterasi, dan meminimalkan konflik saat implementasi lintas branch berikutnya.
