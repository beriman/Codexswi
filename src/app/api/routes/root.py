"""Landing page routes for the MVP."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.core.config import get_settings

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


@router.get("/", response_class=HTMLResponse)
async def read_home(request: Request) -> HTMLResponse:
    """Render the marketplace landing page placeholder."""

    settings = get_settings()
    templates = request.app.state.templates
    context = {
        "request": request,
        "app_name": settings.app_name,
        "environment": settings.environment,
    }
    return templates.TemplateResponse("index.html", context)


@router.get("/marketplace", response_class=HTMLResponse)
async def read_marketplace(request: Request) -> HTMLResponse:
    """Render the marketplace catalog preview page with curated data."""

    settings = get_settings()
    templates = request.app.state.templates

    marketplace_catalog = [
        {
            "slug": "parfum",
            "label": "Parfum",
            "description": "Rilisan parfum artisan dan kolaborasi komunitas dengan stok sambatan aktif.",
            "products": [
                {
                    "name": "Rimba Embun",
                    "origin": "Atar Nusantara",
                    "origin_type": "Brand Partner",
                    "category": "Parfum Artisan",
                    "notes": ["Jasmine sambac", "Vetiver Bali", "Cedar Atlas"],
                    "price": "Rp420K",
                    "media_class": "parfum-aurora",
                    "tags": ["Bestseller", "Signature"],
                },
                {
                    "name": "Pelangi Senja",
                    "origin": "Studio Senja",
                    "origin_type": "Brand Partner",
                    "category": "Signature Blend",
                    "notes": ["Ylang-ylang", "Patchouli Sulawesi", "Amber Praline"],
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
                    "price": "Mulai Rp250K",
                    "media_class": "community-lagoon",
                    "sambatan": {
                        "progress_percent": 68,
                        "slots_left": 12,
                        "deadline": "6 hari lagi",
                    },
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
            "slug": "lainlain",
            "label": "Lainlain",
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

    context = {
        "request": request,
        "app_name": settings.app_name,
        "environment": settings.environment,
        "title": "Marketplace",
        "marketplace_catalog": marketplace_catalog,
    }
    return templates.TemplateResponse("marketplace.html", context)


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
        "request": request,
        "app_name": settings.app_name,
        "environment": settings.environment,
        "title": "Onboarding Pengguna",
        "steps": steps,
    }
    return templates.TemplateResponse("onboarding.html", context)


@router.get("/ui-ux/implementation", response_class=HTMLResponse)
async def read_uiux_tracker(request: Request) -> HTMLResponse:
    """Render a glassmorphism-flavored tracker of the UI/UX implementation to-do list."""

    settings = get_settings()
    templates = request.app.state.templates

    context = {
        "request": request,
        "app_name": settings.app_name,
        "environment": settings.environment,
        "title": "UI/UX Implementation Tracker",
        "status_meta": STATUS_META,
        "sections": UIUX_IMPLEMENTATION_PLAN,
    }
    return templates.TemplateResponse("ui_ux_tracker.html", context)
