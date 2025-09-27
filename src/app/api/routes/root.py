"""Landing page routes for the MVP."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.core.config import get_settings

router = APIRouter()


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
