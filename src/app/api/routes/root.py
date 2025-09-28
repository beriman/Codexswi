"""Landing page routes for the MVP."""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.core.config import get_settings
from app.services.brand_dashboard import brand_dashboard_service
from app.services.moderation_dashboard import moderation_dashboard_service
from app.services.products import product_service
from app.services.sambatan import SambatanCampaign, sambatan_service

router = APIRouter()


STATUS_META = {
    "todo": {"icon": "☐", "label": "Belum mulai"},
    "progress": {"icon": "◐", "label": "Sedang berjalan"},
    "done": {"icon": "✅", "label": "Selesai"},
}


UIUX_IMPLEMENTATION_PLAN = [
    {
        "section": "0. Panduan Visual & Prinsip Umum",
        "slug": "panduan-visual",
        "tasks": [
            {
                "status": "todo",
                "title": "Kanvas inspirasi UI",
                "description": (
                    "Tangkap elemen kunci dari mockup (palet, tipografi serif+sans, bubble glass, "
                    "refleksi) dan tuangkan ke dokumen panduan kode. Sertakan referensi ukuran dan "
                    "behavior animasi dasar."
                ),
                "deliverable": "docs/ui-style-reference.md",
            },
            {
                "status": "todo",
                "title": "Susun token desain berbasis CSS",
                "description": (
                    "Definisikan CSS custom properties untuk warna, radius, blur, shadow, gradient dan "
                    "timing animasi sesuai mockup. Token dideklarasikan di :root dan dipublikasikan "
                    "melalui static/css/tokens.css."
                ),
                "deliverable": "src/app/web/static/css/tokens.css",
            },
            {
                "status": "todo",
                "title": "Setup tipografi & ikon",
                "description": (
                    "Implementasi font Playfair Display + Inter (atau alternatif open source mirip) via "
                    "@font-face/Google Fonts, serta siapkan set ikon Feather/Phosphor yang akan dipakai."
                ),
                "deliverable": "Perbarui base.html & static/css/base.css",
            },
        ],
    },
    {
        "section": "1. Sistem Desain Berbasis Kode",
        "slug": "sistem-desain",
        "tasks": [
            {
                "status": "todo",
                "title": "Utilitas glassmorphism",
                "description": (
                    "Buat kelas utilitas (mis. .glass-card, .glass-panel, .blur-pill) yang mengatur "
                    "backdrop-filter, border, dan shadow sesuai inspirasi UI."
                ),
                "deliverable": "static/css/glass.css + dokumentasi di docs/ui-style-reference.md",
            },
            {
                "status": "todo",
                "title": "Komponen tombol & chip",
                "description": (
                    "Rancang varian tombol utama/sekunder/ghost serta chip filter dengan state hover/active "
                    "menggunakan CSS variables & HTMX states."
                ),
                "deliverable": "templates/components/button.html + static/css/components/button.css",
            },
            {
                "status": "todo",
                "title": "Komponen kartu & badge status",
                "description": (
                    "Implementasikan kartu produk dengan preview gambar, badge sambatan, dan progress bar radial "
                    "sesuai sample 3D. Sediakan versi horizontal dan grid."
                ),
                "deliverable": "templates/components/product-card.html + aset animasi progress",
            },
            {
                "status": "todo",
                "title": "Layout responsif dasar",
                "description": (
                    "Definisikan grid dan spacing untuk breakpoint desktop/tablet/mobile menggunakan CSS Grid/Flex. "
                    "Sertakan helper kelas container-xl, stack-lg dsb."
                ),
                "deliverable": "static/css/layout.css + catatan README",
            },
        ],
    },
    {
        "section": "2. Navigasi & Struktur Global",
        "slug": "navigasi",
        "tasks": [
            {
                "status": "todo",
                "title": "Navbar sticky adaptif",
                "description": (
                    "Implementasikan navbar glass dengan menu utama, indikator halaman aktif, CTA login/signup, serta "
                    "varian mobile (drawer). Gunakan HTMX untuk aksi open/close."
                ),
                "deliverable": "templates/partials/navbar.html + static/css/components/navbar.css + static/js/navbar.js",
            },
            {
                "status": "todo",
                "title": "Footer komunitas",
                "description": (
                    "Bangun footer dengan CTA newsletter, link legal, sosial, dan highlight komunitas. Pastikan layout "
                    "stack rapi di mobile."
                ),
                "deliverable": "templates/partials/footer.html + CSS pendukung",
            },
            {
                "status": "todo",
                "title": "Breadcrumb reusable",
                "description": (
                    "Buat component breadcrumb HTML dengan data-props Jinja (list tuple). Sediakan styling glass pill dan "
                    "fallback mobile (horizontal scroll)."
                ),
                "deliverable": "templates/components/breadcrumb.html + CSS",
            },
        ],
    },
    {
        "section": "3. Halaman Prioritas MVP",
        "slug": "halaman-prioritas",
        "groups": [
            {
                "title": "3.1 Landing Page / Marketplace Overview",
                "tasks": [
                    {
                        "status": "todo",
                        "title": "Hero interaktif",
                        "description": (
                            "Bangun hero dengan headline besar, subcopy, CTA ganda, slider produk unggulan dan latar bubble 3D (SVG "
                            "atau Lottie). Sertakan animasi hover subtle."
                        ),
                        "deliverable": "templates/pages/landing.html section hero + asset di static/media/hero",
                    },
                    {
                        "status": "todo",
                        "title": "Tab kategori & filter",
                        "description": (
                            "Implementasikan tab + filter kaca menggunakan HTMX untuk swap konten tanpa reload. Sediakan chip "
                            "active/hover, search bar, dan sort toggle."
                        ),
                        "deliverable": "templates/components/category-tabs.html + static/js/tabs.js",
                    },
                    {
                        "status": "todo",
                        "title": "Grid produk responsif",
                        "description": (
                            "Layout grid dengan indikator sambatan (progress bar + deadline) dan varian card untuk desktop/tablet/"
                            "mobile. Pastikan aria label lengkap."
                        ),
                        "deliverable": "Blok di landing.html + static/css/components/product-grid.css",
                    },
                    {
                        "status": "todo",
                        "title": "Carousel highlight Nusantarum",
                        "description": (
                            "Implementasikan carousel horizontal dengan pill navigation dan auto-play opsional menggunakan Swiper.js "
                            "atau implementasi custom."
                        ),
                        "deliverable": "templates/components/story-carousel.html + static/js/carousel.js",
                    },
                    {
                        "status": "todo",
                        "title": "Footer CTA komunitas",
                        "description": (
                            "Section CTA akhir dengan glass panel dan call-to-action bergaya mockup."
                        ),
                        "deliverable": "Section di landing.html + styling khusus",
                    },
                ],
            },
            {
                "title": "3.2 Detail Produk",
                "tasks": [
                    {
                        "status": "todo",
                        "title": "Galeri foto produk",
                        "description": (
                            "Implementasikan viewer utama + thumbnail scroll dengan efek parallax ringan. Dukungan keyboard navigation "
                            "dan fallback non-JS."
                        ),
                        "deliverable": "templates/components/product-gallery.html + static/js/gallery.js",
                    },
                    {
                        "status": "todo",
                        "title": "Panel informasi produk",
                        "description": (
                            "Panel kanan berisi harga, stok, deskripsi aroma, CTA Sambatan/Pesanan dengan badge status. Pastikan sticky di desktop."
                        ),
                        "deliverable": "templates/pages/product_detail.html section info + CSS",
                    },
                    {
                        "status": "todo",
                        "title": "Modul info brand",
                        "description": (
                            "Kartu brand kaca dengan logo, sertifikasi, link Nusantarum, CTA follow."
                        ),
                        "deliverable": "templates/components/brand-module.html",
                    },
                    {
                        "status": "todo",
                        "title": "Panel sambatan",
                        "description": (
                            "Komponen progress radial, slot tersisa, countdown realtime (menggunakan Stimulus/HTMX). Varian state aktif/penuh/tutup."
                        ),
                        "deliverable": "static/js/sambatan-panel.js + partial HTML & CSS",
                    },
                ],
            },
            {
                "title": "3.3 Dashboard Internal (Ops)",
                "tasks": [
                    {
                        "status": "todo",
                        "title": "Layout dashboard",
                        "description": (
                            "Sidebar kaca, topbar, dan konten utama responsif. Gunakan CSS Grid dua kolom + collapse mobile."
                        ),
                        "deliverable": "templates/pages/dashboard/index.html + static/css/dashboard.css",
                    },
                    {
                        "status": "todo",
                        "title": "Header metrik",
                        "description": (
                            "Kartu KPI dengan gradient glow, icon, delta up/down. Animated counters optional."
                        ),
                        "deliverable": "templates/components/kpi-card.html + animasi angka",
                    },
                    {
                        "status": "todo",
                        "title": "Tabel pesanan",
                        "description": (
                            "Tabel dengan filter status (tabs), tombol ekspor, empty state ilustrasi. Responsif via CSS display: block di mobile."
                        ),
                        "deliverable": "templates/components/order-table.html + CSS/JS filter",
                    },
                    {
                        "status": "todo",
                        "title": "Drawer detail pesanan",
                        "description": (
                            "Drawer kanan yang muncul saat klik baris, menampilkan detail & log. Implementasi HTMX swap + overlay backdrop."
                        ),
                        "deliverable": "templates/components/order-drawer.html + static/js/drawer.js",
                    },
                ],
            },
            {
                "title": "3.4 Nusantarum Hub",
                "tasks": [
                    {
                        "status": "todo",
                        "title": "Hero kuratorial",
                        "description": (
                            "Hero kaca dengan headline, subcopy, CTA, background partikel (canvas/SVG)."
                        ),
                        "deliverable": "templates/pages/nusantarum.html section hero + asset",
                    },
                    {
                        "status": "todo",
                        "title": "Panel filter multiplatform",
                        "description": (
                            "Panel filter desktop + bottom sheet mobile (dialog). Gunakan CSS position: sticky dan HTMX update results."
                        ),
                        "deliverable": "templates/components/nusantarum-filter.html + static/js/filter-sheet.js",
                    },
                    {
                        "status": "todo",
                        "title": "Kartu cerita",
                        "description": (
                            "Kartu cerita dengan foto, tag brand/perfumer, CTA. Pastikan variant grid/list."
                        ),
                        "deliverable": "templates/components/story-card.html",
                    },
                    {
                        "status": "todo",
                        "title": "CTA ajukan cerita",
                        "description": (
                            "Form CTA dengan state hover, disabled, dan note integrasi backend."
                        ),
                        "deliverable": "Section + CSS di nusantarum.html",
                    },
                ],
            },
            {
                "title": "3.5 Profil Pengguna",
                "tasks": [
                    {
                        "status": "todo",
                        "title": "Header profil",
                        "description": (
                            "Header kaca dengan avatar, nama, preferensi aroma chip, dan tombol edit."
                        ),
                        "deliverable": "templates/pages/profile.html section header + CSS",
                    },
                    {
                        "status": "todo",
                        "title": "Tab aktivitas/favorit/sambatan",
                        "description": (
                            "Tab berbasis HTMX untuk switch konten tanpa reload, dengan animasi underline."
                        ),
                        "deliverable": "templates/components/profile-tabs.html + static/js/profile-tabs.js",
                    },
                    {
                        "status": "todo",
                        "title": "Timeline aktivitas",
                        "description": (
                            "Komponen timeline card dengan icon status, timestamp, deskripsi."
                        ),
                        "deliverable": "templates/components/activity-card.html",
                    },
                    {
                        "status": "todo",
                        "title": "Grid favorit & daftar sambatan",
                        "description": (
                            "Layout grid/list dengan status indicator & CTA lanjutkan."
                        ),
                        "deliverable": "Blok di profile.html + CSS",
                    },
                ],
            },
        ],
    },
    {
        "section": "4. Interaksi & Animasi",
        "slug": "interaksi",
        "tasks": [
            {
                "status": "todo",
                "title": "Token animasi global",
                "description": (
                    "Definisikan utilitas animasi (hover lift, fade-blur, glow pulse) dalam static/css/animation.css dan contoh di dokumentasi."
                ),
                "deliverable": "static/css/animation.css + update docs/ui-style-reference.md",
            },
            {
                "status": "todo",
                "title": "Transisi antar halaman",
                "description": (
                    "Implementasi transisi halus menggunakan HTMX hx-boost + CSS view-transition (jika didukung) atau fallback fade."
                ),
                "deliverable": "static/js/page-transitions.js + konfigurasi di base template",
            },
            {
                "status": "todo",
                "title": "Microinteraction komponen",
                "description": (
                    "Tambahkan feedback state untuk tombol, progress bar, badge sambatan (pulse countdown). Deskripsikan perilaku di dokumentasi."
                ),
                "deliverable": "Update CSS/JS terkait + dokumentasi",
            },
        ],
    },
    {
        "section": "5. Aset & Dokumentasi Handoff Developer",
        "slug": "aset-dokumentasi",
        "tasks": [
            {
                "status": "todo",
                "title": "Paket ikon & ilustrasi",
                "description": (
                    "Kumpulkan ikon SVG dan ilustrasi latar bubble sesuai gaya. Optimasi via SVGO."
                ),
                "deliverable": "Direktori static/icons/ & static/illustrations/ + README listing",
            },
            {
                "status": "todo",
                "title": "Placeholder produk & brand",
                "description": (
                    "Sediakan placeholder gambar dengan efek kaca (PNG/WebP) untuk fallback."
                ),
                "deliverable": "Folder static/media/placeholders/",
            },
            {
                "status": "todo",
                "title": "Dokumentasi spacing & shadow",
                "description": (
                    "Tuliskan guideline di docs/ui-style-reference.md terkait jarak, layering, depth."
                ),
                "deliverable": "Update docs/ui-style-reference.md",
            },
            {
                "status": "todo",
                "title": "Checklist QA visual",
                "description": (
                    "Buat checklist HTML/Markdown untuk review kontras, responsive, accesibility (keyboard, aria)."
                ),
                "deliverable": "docs/ui-qa-checklist.md",
            },
        ],
    },
    {
        "section": "6. Integrasi & Validasi",
        "slug": "integrasi",
        "tasks": [
            {
                "status": "todo",
                "title": "Mapping komponen ke backend",
                "description": (
                    "Dokumentasikan bagaimana tiap komponen template menerima data (context dict). Sertakan contoh payload."
                ),
                "deliverable": "docs/ui-component-contracts.md",
            },
            {
                "status": "todo",
                "title": "Prototipe interaktif via Storybook/Pattern Library",
                "description": (
                    "Setup Storybook (atau alternatif minimal docs/site dengan npm run dev) untuk preview komponen glass secara isolasi."
                ),
                "deliverable": "Konfigurasi Storybook di story/ + panduan run",
            },
            {
                "status": "todo",
                "title": "Usability testing ringan",
                "description": (
                    "Jalankan tes internal (5-7 orang) menggunakan build SSR aktual, catat temuan."
                ),
                "deliverable": "docs/research/usability-round1.md",
            },
            {
                "status": "todo",
                "title": "Revisi & finalisasi",
                "description": (
                    "Terapkan feedback, tandai komponen siap produksi, update changelog."
                ),
                "deliverable": "Update docs/ui-style-reference.md",
            },
        ],
    },
]


PURCHASE_FLOW_STATUS_META = {
    "in-discovery": {
        "label": "Discovery",
        "icon": "🔍",
        "description": "Sedang dimatangkan oleh tim produk & riset pengguna.",
    },
    "in-design": {
        "label": "Desain",
        "icon": "🎨",
        "description": "UI/UX sedang distabilisasi berdasarkan panduan glassmorphism.",
    },
    "ready": {
        "label": "Siap Implementasi",
        "icon": "🚀",
        "description": "Spesifikasi visual dan interaksi sudah dikunci untuk developer.",
    },
    "live": {
        "label": "Telah Dibangun",
        "icon": "✅",
        "description": "Flow sudah tersedia di staging/production build MVP.",
    },
}


PURCHASE_FLOW_BLUEPRINT = [
    {
        "slug": "regular",
        "title": "Belanja Produk Regular",
        "summary": "Flow standar untuk pembelian katalog marketplace tanpa mekanisme sambatan.",
        "status": "ready",
        "persona": "Pembeli retail dan B2B ringan yang ingin checkout cepat.",
        "success_metrics": [
            "Waktu dari landing ke checkout < 3 menit",
            "Rasio keranjang → pembayaran sukses > 60%",
            "Validasi alamat berhasil dalam satu kali input",
        ],
        "steps": [
            {
                "stage": "Eksplorasi & Pencarian",
                "goal": "Menemukan produk yang relevan",
                "status": "live",
                "touchpoints": [
                    "Landing/Marketplace menampilkan search bar kaca dengan auto-suggest",
                    "Filter aroma dan sort toggle untuk mempersonalisasi katalog",
                    "Grid kartu produk dengan foto, harga, dan badge stok",
                ],
                "notes": [
                    "Microcopy jumlah hasil dan skeleton loading saat filter berubah",
                    "Optimasi keyboard navigation untuk aksesibilitas",
                ],
            },
            {
                "stage": "Melihat Detail Produk",
                "goal": "Memahami deskripsi dan manfaat",
                "status": "ready",
                "touchpoints": [
                    "Halaman detail dengan galeri foto dan deskripsi top-mid-base notes",
                    "Panel info brand serta highlight review singkat",
                    "CTA utama 'Tambah ke Keranjang' dengan varian quantity stepper",
                ],
                "notes": [
                    "Toast info saat varian berubah dan disabled state ketika stok habis",
                    "Badge Sambatan disembunyikan untuk produk non-sambatan",
                ],
            },
            {
                "stage": "Menambahkan ke Keranjang",
                "goal": "Mengelola item yang akan dibeli",
                "status": "ready",
                "touchpoints": [
                    "Drawer keranjang kaca dari sisi kanan dengan daftar item",
                    "Kontrol kuantitas in-line dan subtotal dinamis",
                    "CTA 'Checkout' dan aksi 'Lanjutkan Belanja'",
                ],
                "notes": [
                    "Badge jumlah item pada ikon navbar diperbarui real time",
                    "Toast sukses ketika produk berhasil masuk keranjang",
                ],
            },
            {
                "stage": "Checkout Informasi",
                "goal": "Mengisi data pengiriman & opsi pengiriman",
                "status": "in-design",
                "touchpoints": [
                    "Checkout multi-step dengan breadcrumb Keranjang → Alamat → Pengiriman → Pembayaran",
                    "Form alamat kaca dengan auto-complete dan opsi simpan alamat default",
                    "Pilihan pengiriman (Reguler, Same Day) dalam kartu radio glass",
                ],
                "notes": [
                    "Validasi inline dengan ikon cek/eror",
                    "Order summary sticky di kanan menampilkan estimasi tiba",
                ],
            },
            {
                "stage": "Pembayaran",
                "goal": "Memilih metode dan melakukan pembayaran",
                "status": "in-discovery",
                "touchpoints": [
                    "Opsi e-wallet, transfer bank, dan kartu kredit dengan ikon brand",
                    "Panel instruksi dinamis setelah metode dipilih",
                    "Countdown batas waktu pembayaran dan CTA salin nomor tujuan",
                ],
                "notes": [
                    "State tombol lanjut disabled sampai metode dipilih",
                    "Rencana integrasi webhook pembayaran untuk update status otomatis",
                ],
            },
            {
                "stage": "Pelacakan & Penerimaan",
                "goal": "Memantau status sampai barang diterima",
                "status": "in-design",
                "touchpoints": [
                    "Timeline status di riwayat pesanan (Dibuat → Diproses → Dikirim → Selesai)",
                    "Notifikasi email/push saat status berubah",
                    "CTA 'Konfirmasi Terima Barang' saat status dikirim",
                ],
                "notes": [
                    "Setelah konfirmasi, munculkan prompt rating produk",
                    "Simpan log aktivitas untuk dashboard ops",
                ],
            },
        ],
    },
    {
        "slug": "sambatan",
        "title": "Belanja Produk Sambatan",
        "summary": "Flow kolaboratif ketika produk dijual melalui kampanye sambatan komunitas.",
        "status": "in-design",
        "persona": "Kontributor komunitas yang berbagi slot pembelian batch.",
        "success_metrics": [
            "80% kampanye mencapai target slot sebelum deadline",
            "< 24 jam untuk menyelesaikan checkout akhir setelah sambatan sukses",
            "Minim pertanyaan support terkait status sambatan berkat UI jelas",
        ],
        "steps": [
            {
                "stage": "Eksplorasi Sambatan",
                "goal": "Menemukan kampanye sambatan aktif",
                "status": "ready",
                "touchpoints": [
                    "Tab Sambatan di landing dengan kartu progress radial dan badge deadline",
                    "Filter tambahan untuk kategori sambatan dan progress",
                    "Label urgensi seperti 'Butuh 5 lagi' untuk sense of urgency",
                ],
                "notes": [
                    "Progress bar beranimasi saat hover",
                    "Tooltip menjelaskan istilah sambatan untuk pendatang baru",
                ],
            },
            {
                "stage": "Detail Kampanye",
                "goal": "Memahami mekanisme sambatan dan benefit",
                "status": "ready",
                "touchpoints": [
                    "Panel progres besar dengan countdown dan daftar kontribusi terbaru",
                    "Breakdown harga normal vs sambatan dan minimum slot",
                    "CTA utama 'Gabung Sambatan' serta CTA sekunder 'Tanya Tim'",
                ],
                "notes": [
                    "Banner info saat kampanye hampir penuh atau mendekati deadline",
                    "Tooltip untuk istilah teknis dan modul FAQ ringan",
                ],
            },
            {
                "stage": "Gabung Sambatan",
                "goal": "Memilih jumlah slot dan komitmen pembayaran",
                "status": "in-design",
                "touchpoints": [
                    "Modal stepper: pilih jumlah slot → konfirmasi total → pilih metode pembayaran",
                    "Konfirmasi bahwa dana ditahan (escrow) sampai slot terpenuhi",
                    "Badge status 'Menunggu Slot Terpenuhi' di akhir modal",
                ],
                "notes": [
                    "Notifikasi email/in-app berisi ringkasan komitmen",
                    "Pertimbangkan progress share untuk ajak teman (link copy)",
                ],
            },
            {
                "stage": "Progres Sambatan",
                "goal": "Memantau apakah sambatan terpenuhi",
                "status": "in-design",
                "touchpoints": [
                    "Halaman profil > Sambatan Saya dengan progress radial besar",
                    "Countdown dan CTA 'Ajak Teman' untuk membagikan kampanye",
                    "Status otomatis berubah menjadi 'Sambatan Terkonfirmasi' saat target tercapai",
                ],
                "notes": [
                    "Notifikasi otomatis ketika progress menyentuh 80%",
                    "State fallback 'Sambatan Gagal' menampilkan estimasi refund",
                ],
            },
            {
                "stage": "Checkout Akhir",
                "goal": "Menuntaskan detail pengiriman setelah sambatan sukses",
                "status": "in-discovery",
                "touchpoints": [
                    "Redirect ke flow checkout reguler dengan harga final sambatan",
                    "Form alamat pre-populated bila sudah pernah diisi",
                    "Banner hijau 'Selamat! Sambatan berhasil' dengan countdown pembayaran akhir",
                ],
                "notes": [
                    "Validasi ulang jadwal produksi/pengiriman batch",
                    "Instruksi pembayaran bertahap bila metode tersebut dipilih",
                ],
            },
            {
                "stage": "Pemrosesan & Penerimaan",
                "goal": "Menunggu produksi/pengiriman kolektif",
                "status": "in-discovery",
                "touchpoints": [
                    "Timeline status menambahkan fase 'Produksi/Batching' sebelum dikirim",
                    "Notifikasi di setiap tahapan dan update refund jika gagal",
                    "Permintaan testimoni sambatan setelah barang tiba",
                ],
                "notes": [
                    "Tampilkan estimasi waktu refund di status gagal",
                    "Log detail tersedia untuk tim ops di dashboard",
                ],
            },
        ],
    },
]


def _ensure_timezone(dt: datetime) -> datetime:
    """Normalize datetimes to timezone-aware UTC instances."""

    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _format_deadline(deadline: datetime, *, now: datetime | None = None) -> str:
    now = _ensure_timezone(now or datetime.now(UTC))
    deadline = _ensure_timezone(deadline)
    delta = deadline - now
    if delta.total_seconds() <= 0:
        return "Berakhir"
    days = delta.days
    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60
    if days > 0:
        return f"{days} hari lagi"
    if hours > 0:
        return f"{hours} jam lagi"
    return f"{minutes} menit lagi"


def _ensure_demo_sambatan(now: datetime | None = None) -> None:
    now = _ensure_timezone(now or datetime.now(UTC))
    if list(sambatan_service.list_campaigns()):
        return

    product = product_service.create_product(name="Kidung Laut Sambatan", base_price=250_000)
    product_service.toggle_sambatan(
        product_id=product.id,
        enabled=True,
        total_slots=60,
        deadline=now + timedelta(days=6),
    )

    campaign = sambatan_service.create_campaign(
        product_id=product.id,
        title="Kidung Laut Batch Komunitas",
        total_slots=60,
        price_per_slot=250_000,
        deadline=now + timedelta(days=6, hours=12),
        now=now,
    )

    sambatan_service.join_campaign(
        campaign_id=campaign.id,
        user_id="demo-user-1",
        quantity=8,
        shipping_address="Jl. Kenanga No. 12, Bandung, Jawa Barat",
        note="Pickup komunitas setelah produksi",
        now=now,
    )
    sambatan_service.join_campaign(
        campaign_id=campaign.id,
        user_id="demo-user-2",
        quantity=12,
        shipping_address="Perumahan Harmoni Blok B5, Surabaya",
        now=now + timedelta(hours=2),
    )


def _serialize_campaign_for_ui(campaign: SambatanCampaign, *, now: datetime | None = None) -> dict[str, object]:
    return {
        "id": campaign.id,
        "title": campaign.title,
        "status": campaign.status.value,
        "progress": campaign.progress_percent(),
        "slots_taken": campaign.slots_taken,
        "total_slots": campaign.total_slots,
        "slots_remaining": campaign.slots_remaining(),
        "deadline_label": _format_deadline(campaign.deadline, now=now),
    }


@router.get("/", response_class=HTMLResponse)
async def read_home(request: Request) -> HTMLResponse:
    """Render the marketplace landing page placeholder."""

    settings = get_settings()
    templates = request.app.state.templates
    context = {
        "app_name": settings.app_name,
        "environment": settings.environment,
    }
    return templates.TemplateResponse(request, "index.html", context)


@router.get("/marketplace", response_class=HTMLResponse)
async def read_marketplace(request: Request) -> HTMLResponse:
    """Render the marketplace catalog preview page with curated data."""

    settings = get_settings()
    templates = request.app.state.templates

    now = datetime.now(UTC)
    _ensure_demo_sambatan(now=now)

    sambatan_campaigns = list(sambatan_service.list_campaigns())
    sambatan_cards = [_serialize_campaign_for_ui(campaign, now=now) for campaign in sambatan_campaigns]

    marketplace_catalog = [
        {
            "slug": "parfum",
            "label": "Parfum",
            "description": "Rilisan parfum artisan dan kolaborasi komunitas dengan stok sambatan aktif.",
            "products": [
                {
                    "name": "Rimba Embun",
                    "origin": "Atar Nusantara",
                    "brand_slug": "atar-nusantara",
                    "origin_type": "Brand Partner",
                    "category": "Parfum Artisan",
                    "notes": ["Jasmine sambac", "Vetiver Bali", "Cedar Atlas"],
                    "perfumer": "Ayu Prameswari",
                    "price": "Rp420K",
                    "media_class": "parfum-aurora",
                    "tags": ["Bestseller", "Signature"],
                },
                {
                    "name": "Pelangi Senja",
                    "origin": "Studio Senja",
                    "brand_slug": "studio-senja",
                    "origin_type": "Brand Partner",
                    "category": "Signature Blend",
                    "notes": ["Ylang-ylang", "Patchouli Sulawesi", "Amber Praline"],
                    "perfumer": "Devi Larasati",
                    "price": "Rp380K",
                    "media_class": "parfum-tropis",
                    "tags": ["Baru", "Eksklusif"],
                },
                {
                    "name": "Kidung Laut",
                    "origin": "Rara Widyanti",
                    "origin_type": "Kreator Komunitas",
                    "category": "Kolaborasi Sambatan",
                    "notes": ["Sea salt accord", "Kelopak kenanga", "Oud Kalimantan"],
                    "perfumer": "Rara Widyanti",
                    "price": "Mulai Rp250K",
                    "media_class": "community-lagoon",
                    "sambatan": None,
                },
            ],
        },
        {
            "slug": "raw-material",
            "label": "Raw Material",
            "description": "Bahan baku terpilih dari petani dan distilator lokal siap untuk eksperimen Anda.",
            "products": [
                {
                    "name": "Minyak Sereh Wangi",
                    "origin": "Koperasi Aroma Purbalingga",
                    "origin_type": "Pemasok Komunitas",
                    "category": "Essential Oil",
                    "description": "Batch suling terbaru dengan kandungan citral tinggi dan dokumentasi GC-MS.",
                    "price": "Rp180K / 50ml",
                    "media_class": "material-citronella",
                    "availability": "Tersisa 32 botol",
                    "tags": ["Traceable", "Batch 0424"],
                },
                {
                    "name": "Resin Benzoin Sumatra",
                    "origin": "UMKM Harum Andalas",
                    "origin_type": "Pemasok Komunitas",
                    "category": "Resinoid",
                    "description": "Resin kering kelas eksport siap diolah menjadi tincture atau absolute.",
                    "price": "Rp95K / 250gr",
                    "media_class": "material-benzoin",
                    "availability": "Pengiriman mingguan",
                },
            ],
        },
        {
            "slug": "peralatan",
            "label": "Peralatan",
            "description": "Peralatan laboratorium skala kecil yang sering direkomendasikan kreator Nusantarum.",
            "products": [
                {
                    "name": "Pipet Gelas Set 3 Ukuran",
                    "origin": "LabKit.ID",
                    "origin_type": "Brand Partner",
                    "category": "Alat Ukur",
                    "description": "Set pipet borosilikat 1ml, 3ml, dan 5ml lengkap dengan karet pipette.",
                    "price": "Rp150K / set",
                    "media_class": "equipment-pipette",
                    "availability": "Ready stock",
                    "tags": ["Best value"],
                },
                {
                    "name": "Timbangan Digital 0.01g",
                    "origin": "Studio Senja",
                    "brand_slug": "studio-senja",
                    "origin_type": "Brand Partner",
                    "category": "Peralatan Produksi",
                    "description": "Akurasi 0.01g dengan kalibrasi otomatis dan penutup kaca mini.",
                    "price": "Rp420K",
                    "media_class": "equipment-scale",
                    "availability": "Garansi 1 tahun",
                },
            ],
        },
        {
            "slug": "lain-lain",
            "label": "Lain-lain",
            "description": "Dukungan lain mulai dari kemasan hingga pengalaman workshop untuk memperluas bisnis parfum Anda.",
            "products": [
                {
                    "name": "Botol Roll-On Frosted 10ml",
                    "origin": "Kemasan Harmoni",
                    "origin_type": "UMKM Partner",
                    "category": "Kemasan",
                    "description": "Bundle 24 botol lengkap dengan bola stainless dan tutup aluminium.",
                    "price": "Rp210K / dus",
                    "media_class": "misc-packaging",
                    "availability": "Pre-order 5 hari",
                },
                {
                    "name": "Voucher Workshop Formulasi",
                    "origin": "Komunitas Nusantarum",
                    "origin_type": "Kreator Komunitas",
                    "category": "Pengalaman",
                    "description": "Sesi daring 2 jam membahas blending dasar bersama mentor komunitas.",
                    "price": "Rp275K",
                    "media_class": "misc-workshop",
                    "availability": "Jadwal batch Mei",
                },
            ],
        },
    ]

    if sambatan_cards:
        highlight = sambatan_cards[0]
        marketplace_catalog[0]["products"][2]["sambatan"] = {
            "progress_percent": highlight["progress"],
            "slots_left": highlight["slots_remaining"],
            "deadline": highlight["deadline_label"],
        }

    context = {
        "app_name": settings.app_name,
        "environment": settings.environment,
        "title": "Marketplace",
        "marketplace_catalog": marketplace_catalog,
    }
    return templates.TemplateResponse(request, "marketplace.html", context)


@router.get("/onboarding", response_class=HTMLResponse)
async def read_onboarding(request: Request) -> HTMLResponse:
    """Render the onboarding flow playground used by the product team."""

    settings = get_settings()
    templates = request.app.state.templates

    steps = [
        {
            "key": "register",
            "title": "Buat Akun",
            "description": "Isi data dasar dan konfirmasi email untuk mulai eksplorasi Sensasiwangi.",
        },
        {
            "key": "verify",
            "title": "Verifikasi Email",
            "description": "Masukkan kode yang kami kirim dan pantau batas waktunya secara real-time.",
        },
        {
            "key": "profile",
            "title": "Lengkapi Profil",
            "description": "Beritahu kami tujuan bisnis parfum Anda untuk rekomendasi kurasi.",
        },
    ]

    context = {
        "app_name": settings.app_name,
        "environment": settings.environment,
        "title": "Onboarding Pengguna",
        "steps": steps,
    }
    return templates.TemplateResponse(request, "onboarding.html", context)


@router.get("/auth", response_class=HTMLResponse)
async def read_auth(request: Request) -> HTMLResponse:
    """Render the combined register/login playground."""

    settings = get_settings()
    templates = request.app.state.templates

    perks = [
        {
            "title": "Satu akun untuk semua modul",
            "description": "Akses marketplace, sambatan, dan analitik dengan sekali login.",
        },
        {
            "title": "Pengingat personal",
            "description": "Tim produk dapat menguji flow notifikasi dan email komunitas.",
        },
        {
            "title": "Keamanan dasar",
            "description": "Password divalidasi di sisi server dan disimpan dengan hashing.",
        },
    ]

    context = {
        "app_name": settings.app_name,
        "environment": settings.environment,
        "title": "Masuk & Daftar",
        "perks": perks,
        "session_user": request.session.get("user"),
    }
    return templates.TemplateResponse(request, "auth.html", context)


@router.get("/ui-ux/implementation", response_class=HTMLResponse)
async def read_uiux_tracker(request: Request) -> HTMLResponse:
    """Render a glassmorphism-flavored tracker of the UI/UX implementation to-do list."""

    settings = get_settings()
    templates = request.app.state.templates

    context = {
        "app_name": settings.app_name,
        "environment": settings.environment,
        "title": "UI/UX Implementation Tracker",
        "status_meta": STATUS_META,
        "sections": UIUX_IMPLEMENTATION_PLAN,
    }
    return templates.TemplateResponse(request, "ui_ux_tracker.html", context)


@router.get("/ui-ux/foundation/purchase", response_class=HTMLResponse)
async def read_purchase_foundation(request: Request) -> HTMLResponse:
    """Render the product purchase workflow blueprint derived from the foundation document."""

    settings = get_settings()
    templates = request.app.state.templates

    context = {
        "app_name": settings.app_name,
        "environment": settings.environment,
        "title": "Blueprint Flow Pembelian",
        "flow_status_meta": PURCHASE_FLOW_STATUS_META,
        "flows": PURCHASE_FLOW_BLUEPRINT,
    }
    return templates.TemplateResponse(request, "purchase_workflow.html", context)


@router.get("/dashboard/brand-owner", response_class=HTMLResponse)
async def read_brand_owner_dashboard(request: Request) -> HTMLResponse:
    """Render the operational dashboard playground for brand owners."""

    settings = get_settings()
    templates = request.app.state.templates
    snapshot = brand_dashboard_service.get_snapshot()

    context = {
        "app_name": settings.app_name,
        "environment": settings.environment,
        "title": "Dashboard Brand Owner",
        "snapshot": snapshot,
    }
    return templates.TemplateResponse(request, "pages/dashboard/brand_owner.html", context)


@router.get("/dashboard/moderation", response_class=HTMLResponse)
async def read_moderation_dashboard(request: Request) -> HTMLResponse:
    """Render the moderation, admin, and curator control center."""

    settings = get_settings()
    templates = request.app.state.templates
    snapshot = moderation_dashboard_service.get_snapshot()

    context = {
        "app_name": settings.app_name,
        "environment": settings.environment,
        "title": "Dashboard Moderasi",
        "snapshot": snapshot,
    }
    return templates.TemplateResponse(request, "pages/dashboard/moderation.html", context)
