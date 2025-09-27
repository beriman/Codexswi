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

## 6. Alur Pengguna Kunci (User Flow)

### 6.1 Belanja Produk Regular

| Tahap | Tujuan Pengguna | Tampilan & Komponen Kunci | Status/Notifikasi |
|-------|-----------------|---------------------------|-------------------|
| 1. Eksplorasi & Pencarian | Menemukan produk yang relevan | Landing/Marketplace: search bar kaca dengan auto-suggest, chip filter aroma, sort toggle. Grid kartu produk reguler menampilkan foto, nama, harga, badge stok. | Micro-copy "Menampilkan 24 produk" + skeleton loading saat filter diubah. |
| 2. Melihat Detail Produk | Memahami deskripsi dan manfaat | Halaman detail reguler: galeri foto, deskripsi top-mid-base notes, info brand, highlight review (average rating + testimoni singkat). CTA utama "Tambah ke Keranjang" dengan varian quantity stepper. | Toast info saat perubahan varian (mis. ukuran) dan state tombol disabled bila stok habis. |
| 3. Menambahkan ke Keranjang | Mengelola item yang akan dibeli | Drawer keranjang kaca muncul dari kanan berisi list item, kontrol kuantitas, subtotal dinamis. Tersedia tombol "Lanjutkan Belanja" dan CTA primer "Checkout". | Badge jumlah item pada ikon keranjang di navbar diperbarui real time, toast sukses setelah item ditambahkan. |
| 4. Checkout Informasi | Mengisi data pengiriman & opsi pengiriman | Halaman checkout multi-step (breadcrumbs: Keranjang → Alamat → Pengiriman → Pembayaran). Form alamat menggunakan input kaca dengan auto-complete, opsi simpan alamat default. Pilihan pengiriman (Reguler, Same Day) dalam kartu radio glass. | Validasi inline dengan ikon cek/eror, summary order sticky di sisi kanan menampilkan estimasi tiba. |
| 5. Pembayaran | Memilih metode dan melakukan pembayaran | Step pembayaran menampilkan opsi e-wallet, transfer bank, kartu kredit. UI tombol radio dengan ikon brand dan estimasi biaya admin. Setelah memilih, panel instruksi muncul (mis. nomor virtual account). | Countdown batas waktu pembayaran + CTA "Salin". Setelah sukses redirect ke halaman konfirmasi dengan status "Menunggu Konfirmasi". |
| 6. Pelacakan & Penerimaan | Memantau status sampai barang diterima | Halaman riwayat pesanan/profil menampilkan kartu status dengan timeline (Pesanan dibuat → Diproses → Dikirim → Selesai). Notifikasi push/email dikirim saat status berubah. Tombol "Konfirmasi Terima Barang" muncul saat status dikirim. | Setelah pengguna menekan konfirmasi, status berubah menjadi "Selesai" dan tombol rating produk muncul untuk mendorong ulasan. |

### 6.2 Belanja Produk Sambatan

| Tahap | Tujuan Pengguna | Tampilan & Komponen Kunci | Status/Notifikasi |
|-------|-----------------|---------------------------|-------------------|
| 1. Eksplorasi Sambatan | Menemukan kampanye sambatan aktif | Landing memiliki tab "Sambatan". Kartu sambatan menampilkan progress radial, badge deadline (contoh: "3 hari lagi"), harga estimasi setelah sambatan berhasil, jumlah slot tersisa. Search & filter sama dengan reguler namun dengan filter tambahan (mis. kategori sambatan, progress). | Progress bar beranimasi saat hover, label "Butuh 5 lagi" untuk sense urgensi. |
| 2. Detail Kampanye | Memahami mekanisme sambatan dan benefit | Halaman detail sambatan memiliki panel progres besar, daftar kontribusi terbaru (avatar), breakdown harga: harga normal vs harga sambatan, minimum slot, batas waktu. CTA utama "Gabung Sambatan"; secondary CTA "Tanya Tim" (chat). | Banner info jika kampanye hampir penuh atau mendekati deadline, tooltip yang menjelaskan istilah sambatan. |
| 3. Gabung Sambatan | Memilih jumlah slot dan komitmen pembayaran | Setelah klik CTA, muncul modal stepper: (1) Pilih jumlah slot (dengan stok maksimal), (2) Konfirmasi total komitmen, (3) Pilih metode pembayaran. Sistem memegang dana (escrow) sampai sambatan sukses. | Badge status "Menunggu Slot Terpenuhi" muncul pada modal konfirmasi, notifikasi email/in-app mengenai komitmen. |
| 4. Progres Sambatan | Memantau apakah sambatan terpenuhi | Di halaman profil > tab Sambatan Saya, tiap kampanye memiliki kartu dengan progress radial besar, countdown, dan CTA "Ajak Teman" (share). Jika slot terpenuhi sebelum deadline, status berubah menjadi "Sambatan Terkonfirmasi". Bila gagal, dana direfund otomatis. | Notifikasi otomatis: "Sisa 2 slot lagi" saat progress 80%, "Sambatan Terpenuhi" atau "Sambatan Gagal" dengan instruksi lanjutan. |
| 5. Checkout Akhir | Menuntaskan detail pengiriman setelah sambatan sukses | Ketika status "Sambatan Terkonfirmasi", pengguna diarahkan ke flow checkout mirip produk reguler tetapi dengan harga final sambatan. Form alamat + opsi pengiriman di-prepopulate bila pernah diisi. | Banner hijau "Selamat! Sambatan berhasil" di atas page, countdown waktu untuk melengkapi pembayaran akhir bila menggunakan pembayaran bertahap. |
| 6. Pemrosesan & Penerimaan | Menunggu produksi/pengiriman kolektif | Timeline status memiliki tahapan tambahan: "Produksi/Batching" sebelum "Dikirim". Notifikasi dikirim setiap tahapan selesai. Setelah barang tiba, pengguna konfirmasi penerimaan dan diminta memberi review khusus sambatan (testimonial untuk komunitas). | Jika sambatan gagal, timeline menampilkan status "Refund Diproses" dengan estimasi selesai dan CTA cek detail pembayaran. |

### 6.3 Flow Non-Marketplace

1. **Kurator Nusantarum**: Dashboard → tab Konten → buat cerita → tautkan ke brand → publish → tampil di Nusantarum.
2. **Ops Pesanan**: Dashboard → tab Pesanan → filter status Draft → buka drawer → update status & nomor resi → simpan.

## 7. Checklist Implementasi UI

- [ ] Siapkan partial template `base.html` dengan theme token & navbar/footer.  
- [ ] Implementasikan komponen reusable: `GlassCard`, `GradientButton`, `ProgressIndicator`.  
- [ ] Pastikan CSS variable untuk warna/opacity terdefinisi di `:root`.  
- [ ] Uji kontras teks terhadap background kaca (WCAG AA).  
- [ ] Dokumentasikan varian mobile vs desktop sebelum sprint implementasi.

---

Dokumen ini menjadi referensi tim desain dan engineering untuk menyelaraskan ekspektasi visual serta struktur halaman sebelum pengembangan lebih lanjut.
