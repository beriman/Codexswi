"""In-memory brand catalog and collaboration workflow service."""

from __future__ import annotations

import secrets
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional

from app.services.storage import BrandLogoStorage, LogoUpload, StorageUploadFailed


class BrandError(Exception):
    """Base error raised for invalid brand operations."""

    status_code: int = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class BrandNotFound(BrandError):
    """Raised when attempting to access an unknown brand."""

    status_code = 404


class BrandAlreadyExists(BrandError):
    """Raised when trying to create a duplicate brand."""


class BrandMemberExists(BrandError):
    """Raised when inviting a member that already has a role in the brand."""


@dataclass
class BrandMember:
    """Represents a brand collaborator with a specific role."""

    profile_id: str
    full_name: str
    username: str
    role: str
    status: str
    avatar_url: Optional[str] = None
    expertise: Optional[str] = None
    invited_by: Optional[str] = None

    @property
    def is_pending(self) -> bool:
        return self.status == "pending"


@dataclass
class BrandProduct:
    """Represents a product highlighted on the brand page."""

    id: str
    name: str
    slug: str
    price_label: str
    hero_note: str
    availability: str
    is_sambatan: bool = False


@dataclass
class BrandHighlight:
    """Represents a recognition or milestone achieved by the brand."""

    title: str
    description: str
    timestamp: str


@dataclass
class Brand:
    """Rich brand record powering the public brand page."""

    id: str
    name: str
    slug: str
    tagline: str
    summary: str
    origin_city: str
    established_year: int
    hero_image_url: str
    aroma_focus: List[str]
    story_points: List[str]
    logo_url: Optional[str] = None
    is_verified: bool = False
    members: List[BrandMember] = field(default_factory=list)
    products: List[BrandProduct] = field(default_factory=list)
    highlights: List[BrandHighlight] = field(default_factory=list)

    def list_members_by_status(self, status: str) -> List[BrandMember]:
        return [member for member in self.members if member.status == status]

    def list_active_members(self) -> List[BrandMember]:
        return self.list_members_by_status("active")

    def list_pending_members(self) -> List[BrandMember]:
        return self.list_members_by_status("pending")

    def list_owners(self) -> List[BrandMember]:
        return [member for member in self.list_active_members() if member.role == "owner"]

    @property
    def description(self) -> str:
        """Alias to expose summary as a richer description in templates."""

        return self.summary


def _slugify(value: str) -> str:
    """Generate a slug suitable for URLs from arbitrary input."""

    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = "-".join(part for part in ascii_value.lower().split() if part)
    return slug or secrets.token_urlsafe(6)


class BrandService:
    """Minimal service to manage brand storefronts for the MVP."""

    def __init__(self, logo_storage: Optional[BrandLogoStorage] = None) -> None:
        self._brands: Dict[str, Brand] = {}
        self._brands_by_slug: Dict[str, Brand] = {}
        self._logo_storage = logo_storage or BrandLogoStorage()
        self._seed_demo_brands()

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------
    def list_brands(self) -> Iterable[Brand]:
        return sorted(self._brands.values(), key=lambda brand: brand.name.lower())

    def search_brands(self, query: Optional[str] = None) -> List[Brand]:
        if not query:
            return list(self.list_brands())

        keyword = query.strip().lower()
        results = []
        for brand in self._brands.values():
            haystack = " ".join(
                [
                    brand.name.lower(),
                    brand.tagline.lower(),
                    brand.summary.lower(),
                    " ".join(focus.lower() for focus in brand.aroma_focus),
                ]
            )
            if keyword in haystack:
                results.append(brand)
        return sorted(results, key=lambda brand: brand.name.lower())

    def get_brand(self, identifier: str) -> Brand:
        if identifier in self._brands:
            return self._brands[identifier]
        if identifier in self._brands_by_slug:
            return self._brands_by_slug[identifier]
        raise BrandNotFound("Brand tidak ditemukan.")

    # ------------------------------------------------------------------
    # Mutating operations
    # ------------------------------------------------------------------
    def _normalise_brand_attributes(
        self,
        *,
        name: str,
        slug: Optional[str],
        tagline: str,
        summary: str,
        origin_city: str,
        established_year: int | str,
        hero_image_url: str,
        logo_url: Optional[str] = None,
        aroma_focus: Optional[Iterable[str]] = None,
        story_points: Optional[Iterable[str]] = None,
        is_verified: bool = False,
    ) -> Dict[str, Any]:
        name_value = name.strip()
        if not name_value:
            raise BrandError("Nama brand wajib diisi.")

        slug_value = _slugify(slug.strip() if slug else name_value)
        if not slug_value:
            raise BrandError("Slug brand tidak valid.")

        tagline_value = tagline.strip()
        if not tagline_value:
            raise BrandError("Tagline brand wajib diisi.")

        summary_value = summary.strip()
        if not summary_value:
            raise BrandError("Ringkasan brand wajib diisi.")

        origin_value = origin_city.strip()
        if not origin_value:
            raise BrandError("Kota asal brand wajib diisi.")

        try:
            year_value = int(established_year)
        except (TypeError, ValueError) as exc:
            raise BrandError("Tahun berdiri brand tidak valid.") from exc

        if year_value <= 0:
            raise BrandError("Tahun berdiri brand tidak valid.")

        hero_value = hero_image_url.strip()
        if not hero_value:
            raise BrandError("URL hero image brand wajib diisi.")

        def _clean_collection(items: Optional[Iterable[str]]) -> List[str]:
            if not items:
                return []
            cleaned = []
            for item in items:
                text = (item or "").strip()
                if text:
                    cleaned.append(text)
            return cleaned

        aroma_value = _clean_collection(aroma_focus)
        story_value = _clean_collection(story_points)

        logo_value = (logo_url or "").strip() or None

        return {
            "name": name_value,
            "slug": slug_value,
            "tagline": tagline_value,
            "summary": summary_value,
            "origin_city": origin_value,
            "established_year": year_value,
            "hero_image_url": hero_value,
            "logo_url": logo_value,
            "aroma_focus": aroma_value,
            "story_points": story_value,
            "is_verified": bool(is_verified),
        }

    def create_brand(
        self,
        *,
        owner_profile_id: str,
        owner_name: str,
        owner_username: str,
        owner_avatar: Optional[str],
        name: str,
        slug: Optional[str] = None,
        tagline: str,
        summary: str,
        origin_city: str,
        established_year: int,
        hero_image_url: str,
        logo_url: Optional[str] = None,
        aroma_focus: Optional[List[str]] = None,
        story_points: Optional[List[str]] = None,
        is_verified: bool = False,
    ) -> Brand:
        attributes = self._normalise_brand_attributes(
            name=name,
            slug=slug,
            tagline=tagline,
            summary=summary,
            origin_city=origin_city,
            established_year=established_year,
            hero_image_url=hero_image_url,
            logo_url=logo_url,
            aroma_focus=aroma_focus,
            story_points=story_points,
            is_verified=is_verified,
        )

        slug_value = attributes["slug"]
        if slug_value in self._brands_by_slug:
            raise BrandAlreadyExists("Nama brand sudah digunakan pada etalase lain.")

        brand_id = secrets.token_urlsafe(8)
        brand = Brand(
            id=brand_id,
            name=attributes["name"],
            slug=attributes["slug"],
            tagline=attributes["tagline"],
            summary=attributes["summary"],
            origin_city=attributes["origin_city"],
            established_year=attributes["established_year"],
            hero_image_url=attributes["hero_image_url"],
            logo_url=attributes["logo_url"],
            aroma_focus=attributes["aroma_focus"],
            story_points=attributes["story_points"],
            is_verified=attributes["is_verified"],
        )
        owner_member = BrandMember(
            profile_id=owner_profile_id,
            full_name=owner_name,
            username=owner_username,
            role="owner",
            status="active",
            avatar_url=owner_avatar,
            expertise="Pendiri",
        )
        brand.members.append(owner_member)
        self._register_brand(brand)
        return brand

    def update_brand(
        self,
        brand_slug: str,
        *,
        name: str,
        slug: Optional[str],
        tagline: str,
        summary: str,
        origin_city: str,
        established_year: int | str,
        hero_image_url: str,
        logo_url: Optional[str] = None,
        aroma_focus: Optional[Iterable[str]] = None,
        story_points: Optional[Iterable[str]] = None,
        is_verified: bool = False,
    ) -> Brand:
        brand = self.get_brand(brand_slug)
        attributes = self._normalise_brand_attributes(
            name=name,
            slug=slug if slug is not None else brand.slug,
            tagline=tagline,
            summary=summary,
            origin_city=origin_city,
            established_year=established_year,
            hero_image_url=hero_image_url,
            logo_url=logo_url,
            aroma_focus=aroma_focus,
            story_points=story_points,
            is_verified=is_verified,
        )

        new_slug = attributes["slug"]
        if new_slug != brand.slug and new_slug in self._brands_by_slug:
            raise BrandAlreadyExists("Slug brand sudah digunakan oleh etalase lain.")

        if new_slug != brand.slug:
            self._brands_by_slug.pop(brand.slug, None)
            brand.slug = new_slug
            self._brands_by_slug[brand.slug] = brand

        brand.name = attributes["name"]
        brand.tagline = attributes["tagline"]
        brand.summary = attributes["summary"]
        brand.origin_city = attributes["origin_city"]
        brand.established_year = attributes["established_year"]
        brand.hero_image_url = attributes["hero_image_url"]
        brand.logo_url = attributes["logo_url"]
        brand.aroma_focus = attributes["aroma_focus"]
        brand.story_points = attributes["story_points"]
        brand.is_verified = attributes["is_verified"]

        # Ensure id index remains in sync
        self._brands[brand.id] = brand
        self._brands_by_slug[brand.slug] = brand
        return brand

    def update_members(
        self,
        brand_slug: str,
        *,
        members: Iterable[Dict[str, Any]],
    ) -> List[BrandMember]:
        brand = self.get_brand(brand_slug)

        normalized: List[BrandMember] = []
        seen_ids: set[str] = set()
        active_owner_exists = False

        for payload in members:
            profile_id = (payload.get("profile_id") or "").strip()
            full_name = (payload.get("full_name") or "").strip()
            username = (payload.get("username") or "").strip()
            role = (payload.get("role") or "co-owner").strip() or "co-owner"
            status = (payload.get("status") or "pending").strip() or "pending"
            avatar_url = (payload.get("avatar_url") or "").strip() or None
            expertise = (payload.get("expertise") or "").strip() or None
            invited_by = (payload.get("invited_by") or "").strip() or None

            if not full_name:
                raise BrandError("Nama member brand wajib diisi.")
            if not username:
                raise BrandError("Username member brand wajib diisi.")

            if not profile_id:
                profile_id = secrets.token_urlsafe(6)

            if profile_id in seen_ids:
                raise BrandError("Duplikasi member dengan profile ID yang sama terdeteksi.")
            seen_ids.add(profile_id)

            member = BrandMember(
                profile_id=profile_id,
                full_name=full_name,
                username=username,
                role=role,
                status=status,
                avatar_url=avatar_url,
                expertise=expertise,
                invited_by=invited_by,
            )

            if member.role == "owner" and member.status == "active":
                active_owner_exists = True

            normalized.append(member)

        if not normalized:
            raise BrandError("Minimal satu member brand wajib tersedia.")

        if not active_owner_exists:
            raise BrandError("Setidaknya satu owner aktif diperlukan untuk brand.")

        brand.members = normalized
        return normalized

    def update_logo(
        self,
        brand_slug: str,
        *,
        logo_url: Optional[str] = None,
        logo_upload: Optional[LogoUpload] = None,
    ) -> Brand:
        """Assign or replace the public logo for a brand."""

        brand = self.get_brand(brand_slug)
        resolved_url: Optional[str] = None

        if logo_upload is not None:
            try:
                resolved_url = self._logo_storage.store_logo(slug=brand.slug, upload=logo_upload)
            except StorageUploadFailed as exc:
                raise BrandError(str(exc)) from exc
        elif logo_url is not None:
            stripped = logo_url.strip()
            resolved_url = stripped or None

        brand.logo_url = resolved_url
        return brand

    def add_product(
        self,
        brand_slug: str,
        *,
        name: str,
        slug: str,
        price_label: str,
        hero_note: str,
        availability: str,
        is_sambatan: bool = False,
    ) -> BrandProduct:
        brand = self.get_brand(brand_slug)
        product = BrandProduct(
            id=secrets.token_urlsafe(6),
            name=name,
            slug=slug,
            price_label=price_label,
            hero_note=hero_note,
            availability=availability,
            is_sambatan=is_sambatan,
        )
        brand.products.append(product)
        return product

    def add_highlight(
        self,
        brand_slug: str,
        *,
        title: str,
        description: str,
        timestamp: str,
    ) -> BrandHighlight:
        brand = self.get_brand(brand_slug)
        highlight = BrandHighlight(title=title, description=description, timestamp=timestamp)
        brand.highlights.append(highlight)
        return highlight

    def invite_co_owner(
        self,
        brand_slug: str,
        *,
        profile_id: str,
        full_name: str,
        username: str,
        expertise: Optional[str] = None,
        avatar_url: Optional[str] = None,
        invited_by: Optional[str] = None,
    ) -> BrandMember:
        brand = self.get_brand(brand_slug)

        if any(member.profile_id == profile_id for member in brand.members):
            raise BrandMemberExists("Pengguna sudah terdaftar pada brand ini.")

        member = BrandMember(
            profile_id=profile_id,
            full_name=full_name,
            username=username,
            role="co-owner",
            status="pending",
            expertise=expertise,
            avatar_url=avatar_url,
            invited_by=invited_by,
        )
        brand.members.append(member)
        return member

    def approve_co_owner(self, brand_slug: str, profile_id: str) -> BrandMember:
        brand = self.get_brand(brand_slug)
        for member in brand.members:
            if member.profile_id == profile_id and member.role == "co-owner":
                member.status = "active"
                return member
        raise BrandError("Undangan co-owner tidak ditemukan untuk brand ini.")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _register_brand(self, brand: Brand) -> None:
        self._brands[brand.id] = brand
        self._brands_by_slug[brand.slug] = brand

    def _seed_demo_brands(self) -> None:
        langit = self.create_brand(
            owner_profile_id="user_amelia",
            owner_name="Amelia Damayanti",
            owner_username="amelia-damayanti",
            owner_avatar="https://images.unsplash.com/photo-1542293787938-4d2226c3d9f1?auto=format&fit=crop&w=160&q=80",
            name="Langit Senja",
            tagline="Cerita aroma hangat untuk nostalgia senja.",
            summary="Brand parfum craft yang merayakan perpaduan rempah hangat dan nuansa gourmand manis.",
            origin_city="Bandung, Indonesia",
            established_year=2019,
            hero_image_url="https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=80",
            logo_url="https://images.unsplash.com/photo-1612626253558-4fb0d8c2b993?auto=format&fit=crop&w=240&q=80",
            aroma_focus=["Rempah hangat", "Gourmand lembut", "Aroma nostalgia"],
            story_points=[
                "Menyuplai batch terbatas dengan bahan utama dari petani lokal.",
                "Rutin mengadakan sesi sambatan untuk transparansi proses produksi.",
                "Mengkurasi komunitas pecinta aroma untuk eksplorasi kolaborasi.",
            ],
            is_verified=True,
        )
        self.add_product(
            langit.slug,
            name="Langit Sepia",
            slug="langit-sepia",
            price_label="Mulai Rp 420.000",
            hero_note="Tonka bean dan patchouli yang menghangatkan momen senja",
            availability="Batch Mei tersisa 18 botol",
        )
        self.add_product(
            langit.slug,
            name="Hujan Pagi",
            slug="hujan-pagi",
            price_label="Mulai Rp 390.000",
            hero_note="Rain accord dengan vetiver basah khas Bandung",
            availability="Pre-order sambatan batch Juni",
            is_sambatan=True,
        )
        self.add_highlight(
            langit.slug,
            title="Kolaborasi Sambatan Batch #2",
            description="Mengajak 25 anggota komunitas untuk uji coba aroma petrichor baru.",
            timestamp="April 2024",
        )
        self.add_highlight(
            langit.slug,
            title="Featured di Nusantarum",
            description="Menjadi salah satu brand pilihan editor pada edisi 'Hangat di Musim Hujan'.",
            timestamp="Maret 2024",
        )

        studio = self.create_brand(
            owner_profile_id="user_bintang",
            owner_name="Bintang Waskita",
            owner_username="bintang-waskita",
            owner_avatar="https://images.unsplash.com/photo-1502323777036-f29e3972d82f?auto=format&fit=crop&w=160&q=80",
            name="Studio Senja",
            tagline="Peralatan dan aroma untuk studio parfum rumahan.",
            summary="Studio butik yang menyediakan racikan wangi signature serta tools pendukung produksi rumahan.",
            origin_city="Yogyakarta, Indonesia",
            established_year=2020,
            hero_image_url="https://images.unsplash.com/photo-1524504388940-b1c1722653e1?auto=format&fit=crop&w=1200&q=80",
            logo_url="https://images.unsplash.com/photo-1616628182508-45138c88b4ce?auto=format&fit=crop&w=240&q=80",
            aroma_focus=["Gourmand", "Aroma kopi", "Peralatan produksi"],
            story_points=[
                "Membantu UMKM parfum menyiapkan toolkit lengkap untuk batch perdana.",
                "Menawarkan sesi konsultasi blending untuk pemula.",
            ],
        )
        self.add_product(
            studio.slug,
            name="Pelangi Senja",
            slug="pelangi-senja",
            price_label="Rp 380.000",
            hero_note="Ylang-ylang dan amber praline dengan sentuhan patchouli",
            availability="Ready stock",
        )
        self.add_product(
            studio.slug,
            name="Timbangan Digital 0.01g",
            slug="timbangan-digital-senja",
            price_label="Rp 420.000",
            hero_note="Akurasi tinggi untuk formula kecil",
            availability="Garansi 1 tahun",
        )
        self.add_highlight(
            studio.slug,
            title="Penggerak Program Inkubasi Sensasiwangi",
            description="Membimbing 12 brand baru menyiapkan SOP produksi rumahan.",
            timestamp="Februari 2024",
        )

        self.invite_co_owner(
            studio.slug,
            profile_id="user_chandra",
            full_name="Chandra Pratama",
            username="chandra-pratama",
            expertise="Kurator komunitas",
            avatar_url="https://images.unsplash.com/photo-1544723795-3fb6469f5b39?auto=format&fit=crop&w=160&q=80",
            invited_by="Bintang Waskita",
        )

        self.add_highlight(
            studio.slug,
            title="Marketplace Favorite Tools",
            description="Dinobatkan sebagai penyedia peralatan favorit oleh komunitas Nusantarum.",
            timestamp="Desember 2023",
        )

        atar = self.create_brand(
            owner_profile_id="brand_atar_owner",
            owner_name="Atar Nusantara",
            owner_username="atar-nusantara",
            owner_avatar="https://images.unsplash.com/photo-1509042239860-f550ce710b93?auto=format&fit=crop&w=160&q=80",
            name="Atar Nusantara",
            tagline="Signature oud dan floral tropis dengan karakter modern.",
            summary="Label parfum niche yang berfokus pada interpretasi aroma hutan hujan Indonesia.",
            origin_city="Jakarta, Indonesia",
            established_year=2016,
            hero_image_url="https://images.unsplash.com/photo-1499695867787-121ffbfa0f5e?auto=format&fit=crop&w=1200&q=80",
            logo_url="https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?auto=format&fit=crop&w=240&q=80",
            aroma_focus=["Floral tropis", "Oud modern", "Resin eksotik"],
            story_points=[
                "Berkolaborasi dengan perfumer independen lintas kota.",
                "Menjaga traceability bahan baku melalui petani binaan.",
            ],
            is_verified=True,
        )
        self.add_product(
            atar.slug,
            name="Rimba Embun",
            slug="rimba-embun",
            price_label="Rp 420.000",
            hero_note="Jasmine sambac dan cedar atlas yang seimbang",
            availability="Pre-order batch Juni",
        )


brand_service = BrandService()
"""Singleton brand service instance shared across routers and tests."""

