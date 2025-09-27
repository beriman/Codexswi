# Sensasiwangi.id UI/UX Foundations

Dokumen ini merangkum panduan desain dasar dan wireframe tekstual untuk MVP Sensasiwangi.id sesuai PRD. Fokus utama adalah membangun pengalaman glassmorphism yang elegan, navigasi intuitif, serta mendefinisikan komponen inti sebelum fase implementasi.

## 1. Prinsip Desain

1. **Glassmorphism Hangat**  
   - Lapisan kartu semi-transparan dengan blur latar (`backdrop-filter: blur(20px)`), border tipis (#FFFFFF33), dan highlight gradien jingga-ke-ungu sebagai aksen utama.  
   - Background global: gradasi lembut `#0F172A` → `#1E293B` dengan pola cahaya samar sebagai ambience parfum.
2. **Tipografi**  
   - Heading: `Playfair Display` (serif modern) untuk kesan premium.  
   - Body & UI: `Inter` untuk keterbacaan tinggi.  
   - Hierarki warna teks: `#F8FAFC` (utama), `#CBD5F5` (sekunder), `#38BDF8` (link/CTA sekunder).
3. **Ikonografi & Ilustrasi**  
   - Gunakan ikon garis tipis (Feather Icons) dengan efek neon tipis.  
   - Placeholder foto produk/brand menggunakan kontainer kaca dengan drop shadow lembut (`0 20px 40px rgba(15, 23, 42, 0.45)`).
4. **Micro-Interaction**  
   - Transisi hover `transform: translateY(-2px)` pada kartu.  
   - Tombol utama: `background: linear-gradient(135deg, #F97316, #C026D3); color: #0F172A` dengan animasi kilau halus.

## 2. Struktur Navigasi Global

```
┌───────────────────────────────────────────────────────────────┐
│ Navbar (blur kaca)                                            │
│ Logo | Marketplace | Sambatan | Nusantarum | Dashboard | Profil│
│ CTA: "Gabung Komunitas" (glass button)                        │
└───────────────────────────────────────────────────────────────┘
```

- Navbar sticky dengan blur dan border kaca.  
- Mode mobile: hamburger menu membuka drawer kaca penuh.  
- Breadcrumb ditampilkan pada halaman dalam (Dashboard, Profil).

Footer global: CTA newsletter, tautan legal, sosial media, serta highlight komunitas.

## 3. Wireframe Tekstual Halaman Utama

### 3.1 Landing Page / Marketplace Overview

```
Hero Section
┌──────────────────────────────────────────────┐
│ Background gradient + aroma particle animasi │
│ Headline: "Eksplorasi Wewangian Nusantara"   │
│ Subcopy + CTA ganda (Eksplor Marketplace,    │
│   Pelajari Sambatan)                         │
│ Kartu statistik (Brand Terkurasi, Sambatan   │
│   Aktif, Stories Terbaru)                    │
└──────────────────────────────────────────────┘

Tabs Kategori (Parfum | Raw Material | Tools | Lainnya)
┌────────────┬────────────┬───────────┬────────────┐
│ Filter kaca│ Search bar │ Sort chip │ Aroma tags │
└────────────┴────────────┴───────────┴────────────┘

Grid Produk (3 kol desktop, 1 kol mobile)
┌───────┐ ┌───────┐ ┌───────┐
│ Foto  │ │ Foto  │ │ Foto  │
│ Nama  │ │ Nama  │ │ Nama  │
│ Harga │ │ Harga │ │ Harga │
│ Sambatan progress bar + deadline (jika ada) │
└───────┘ └───────┘ └───────┘

Highlight Nusantarum (carousel kaca)
┌──────────────────────────────────────────────┐
│ Card cerita, kurator, CTA baca cerita        │
└──────────────────────────────────────────────┘

Footer CTA Komunitas + Newsletter
```

### 3.2 Detail Produk

```
┌──────────────┬──────────────────────────────────┐
│ Galeri foto  │ Nama produk + badge Sambatan     │
│ thumbnail    │ Harga indikatif + stok           │
│              │ Deskripsi aroma (notes top-mid-  │
│              │ base)                            │
│              │ CTA: "Ajukan Pesanan" / "Gabung  │
│              │ Sambatan"                        │
└──────────────┴──────────────────────────────────┘

Info Brand & Story Link
┌──────────────────────────────────────────────┐
│ Logo brand kaca kecil + ring highlight       │
│ Deskripsi singkat                            │
│ Sertifikasi ikon                             │
│ Link ke cerita Nusantarum & CTA chat         │
└──────────────────────────────────────────────┘

Panel Sambatan
┌────────────────────┐
│ Progress circle    │
│ Slot tersisa       │
│ Deadline countdown │
│ Kontributor terbaru│
└────────────────────┘
```

### 3.3 Dashboard Internal (Tim Ops)

```
Sidebar kaca (ikon vertikal) | Konten utama

Header: Ringkasan metrik (Pesanan aktif, Sambatan aktif, Slot terisi)

Tab: Pesanan | Sambatan | Brand | Konten

Pesanan Table
┌─────────┬───────────────┬─────────┬─────────────┐
│ ID      │ Nama Brand    │ Status  │ Jadwal Kirim│
└─────────┴───────────────┴─────────┴─────────────┘
Toolbar: filter status, tombol ekspor CSV

Panel kanan (drawer) ketika baris dipilih: detail pesanan, log aktivitas.
```

### 3.4 Nusantarum Hub

```
Hero kaca dengan headline kuratorial
Filter panel (kategori aroma, wilayah, kurator) di sisi kiri (desktop)
Konten grid 2 kolom (card cerita) dengan tag brand/perfumer terkait
CTA: "Ajukan cerita" (untuk kurator)
```

### 3.5 Profil Pengguna

```
Header profil (avatar kaca, nama, preferensi aroma chip)
Tab: Aktivitas | Favorit | Sambatan Saya

Aktivitas: timeline kartu kaca (pesanan terakhir, sambatan join)
Favorit: grid produk/brand tersimpan
Sambatan Saya: daftar progress bar dan status
```

## 4. Komponen UI Standar

| Komponen           | Deskripsi Visual | Status Interaksi |
|--------------------|------------------|-------------------|
| Primary Button     | Gradien jingga→ungu, glass shadow, radius 999px | Hover naik 2px, glow border |
| Secondary Button   | Latar kaca transparan, border `#38BDF833`, teks aqua | Hover ubah border menjadi solid |
| Card                | Background `rgba(15, 23, 42, 0.65)`, blur 20px, border 1px translucent | Hover shading naik |
| Input Field         | Kaca dengan icon prefix, placeholder `#94A3B8` | Fokus: border gradien |
| Progress Bar        | Track kaca, fill gradien, label persentase di atas | Animasi fill lembut |
| Badge Sambatan      | Chip kaca kecil dengan ikon tangan terangkat | Pulse halus bila mendekati deadline |

## 5. Grid & Breakpoint

- **Desktop (≥1280px)**: Konten maksimum 1200px dengan gutter 32px. 3 kolom untuk grid produk.  
- **Tablet (768-1279px)**: Navbar tetap, grid 2 kolom, sidebar berubah jadi top tabs.  
- **Mobile (≤767px)**: Satu kolom, hero lebih ringkas, filter menjadi bottom sheet.

## 6. Alur Pengguna Kunci (User Flow Ringkas)

1. **Eksplorasi Sambatan**: Landing → pilih kartu Sambatan → detail produk → klik "Gabung Sambatan" → login magic link → konfirmasi slot.  
2. **Kurator Nusantarum**: Dashboard → tab Konten → buat cerita → tautkan ke brand → publish → tampil di Nusantarum.  
3. **Ops Pesanan**: Dashboard → tab Pesanan → filter status Draft → buka drawer → update status & nomor resi → simpan.

## 7. Checklist Implementasi UI

- [ ] Siapkan partial template `base.html` dengan theme token & navbar/footer.  
- [ ] Implementasikan komponen reusable: `GlassCard`, `GradientButton`, `ProgressIndicator`.  
- [ ] Pastikan CSS variable untuk warna/opacity terdefinisi di `:root`.  
- [ ] Uji kontras teks terhadap background kaca (WCAG AA).  
- [ ] Dokumentasikan varian mobile vs desktop sebelum sprint implementasi.

---

Dokumen ini menjadi referensi tim desain dan engineering untuk menyelaraskan ekspektasi visual serta struktur halaman sebelum pengembangan lebih lanjut.
