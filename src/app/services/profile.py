"""Profile service powering the community-centric profile page."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


class ProfileError(Exception):
    """Base error class for profile operations."""

    status_code: int = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ProfileNotFound(ProfileError):
    """Raised when attempting to access an unknown profile."""

    status_code = 404


@dataclass
class ProfileBadge:
    """Represents a badge rendered on the profile header."""

    slug: str
    label: str
    description: str
    icon: str
    count: Optional[int] = None


@dataclass
class ProfileStats:
    """Aggregated counters displayed on the profile."""

    follower_count: int
    following_count: int
    perfumer_product_count: int
    owned_brand_count: int


@dataclass
class PerfumerProduct:
    """Represents a product credited to a perfumer."""

    id: str
    name: str
    brand_name: str
    brand_slug: str
    aroma_notes: str
    highlight: str


@dataclass
class OwnedBrand:
    """Represents a brand owned or administered by the profile."""

    id: str
    name: str
    slug: str
    logo_url: str
    status: str
    tagline: str


@dataclass
class TimelineEntry:
    """Represents an activity entry shown on the profile."""

    title: str
    timestamp: str
    description: str


@dataclass
class ProfileRecord:
    """Internal representation of a user profile."""

    id: str
    username: str
    full_name: str
    bio: str
    preferred_aroma: Optional[str]
    avatar_url: Optional[str]
    location: Optional[str]
    tagline: Optional[str]
    followers: set[str] = field(default_factory=set)
    following: set[str] = field(default_factory=set)
    perfumer_products: List[PerfumerProduct] = field(default_factory=list)
    owned_brands: List[OwnedBrand] = field(default_factory=list)
    activities: List[TimelineEntry] = field(default_factory=list)
    favorites: List[str] = field(default_factory=list)
    sambatan_updates: List[str] = field(default_factory=list)

    def clone_relationships(self) -> tuple[set[str], set[str]]:
        return set(self.followers), set(self.following)


@dataclass
class ProfileViewerState:
    """Viewer metadata that determines CTA state."""

    id: Optional[str]
    is_owner: bool
    is_following: bool

    @property
    def can_follow(self) -> bool:
        return bool(self.id) and not self.is_owner


@dataclass
class ProfileView:
    """Bundle of data required to render a profile page."""

    profile: ProfileRecord
    stats: ProfileStats
    badges: List[ProfileBadge]
    viewer: ProfileViewerState


class ProfileService:
    """Simple in-memory profile store used for SSR demos."""

    def __init__(self) -> None:
        self._profiles: Dict[str, ProfileRecord] = {}
        self._profiles_by_username: Dict[str, ProfileRecord] = {}
        self._initial_relationships: Dict[str, tuple[set[str], set[str]]] = {}
        self._seed_demo_profiles()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_profile(self, profile_identifier: str, *, viewer_id: Optional[str] = None) -> ProfileView:
        profile = self._resolve_profile(profile_identifier)

        stats = ProfileStats(
            follower_count=len(profile.followers),
            following_count=len(profile.following),
            perfumer_product_count=len(profile.perfumer_products),
            owned_brand_count=len(profile.owned_brands),
        )

        badges: List[ProfileBadge] = []
        if profile.perfumer_products:
            badges.append(
                ProfileBadge(
                    slug="perfumer",
                    label="Perfumer",
                    description="Diracik pada produk marketplace Sensasiwangi.",
                    icon="🧪",
                    count=len(profile.perfumer_products),
                )
            )
        if any(brand for brand in profile.owned_brands if brand.status == "active"):
            badges.append(
                ProfileBadge(
                    slug="brand-owner",
                    label="Brand Owner",
                    description="Mengelola brand parfum independen di platform.",
                    icon="🏷️",
                    count=len(profile.owned_brands),
                )
            )

        viewer = ProfileViewerState(
            id=viewer_id,
            is_owner=viewer_id == profile.id if viewer_id else False,
            is_following=viewer_id in profile.followers if viewer_id else False,
        )

        return ProfileView(profile=profile, stats=stats, badges=badges, viewer=viewer)

    def follow_profile(self, target_identifier: str, *, follower_id: str) -> ProfileView:
        follower = self._resolve_profile(follower_id)
        target = self._resolve_profile(target_identifier)

        if follower.id == target.id:
            raise ProfileError("Tidak dapat mengikuti profil sendiri.")

        if follower.id in target.followers:
            # Idempotent response to simplify HTMX interactions.
            return self.get_profile(target.id, viewer_id=follower.id)

        target.followers.add(follower.id)
        follower.following.add(target.id)
        return self.get_profile(target.id, viewer_id=follower.id)

    def unfollow_profile(self, target_identifier: str, *, follower_id: str) -> ProfileView:
        follower = self._resolve_profile(follower_id)
        target = self._resolve_profile(target_identifier)

        if follower.id == target.id:
            raise ProfileError("Tidak dapat berhenti mengikuti profil sendiri.")

        if follower.id in target.followers:
            target.followers.remove(follower.id)
            follower.following.remove(target.id)

        return self.get_profile(target.id, viewer_id=follower.id)

    def list_followers(self, profile_identifier: str) -> List[ProfileRecord]:
        profile = self._resolve_profile(profile_identifier)
        return sorted((self._profiles[follower_id] for follower_id in profile.followers), key=lambda p: p.full_name)

    def list_following(self, profile_identifier: str) -> List[ProfileRecord]:
        profile = self._resolve_profile(profile_identifier)
        return sorted((self._profiles[following_id] for following_id in profile.following), key=lambda p: p.full_name)

    def list_perfumer_products(self, profile_identifier: str) -> List[PerfumerProduct]:
        profile = self._resolve_profile(profile_identifier)
        return profile.perfumer_products

    def list_owned_brands(self, profile_identifier: str) -> List[OwnedBrand]:
        profile = self._resolve_profile(profile_identifier)
        return profile.owned_brands

    def reset_relationships(self) -> None:
        """Reset follow relationships to the initial demo state (used in tests)."""

        for profile_id, snapshot in self._initial_relationships.items():
            followers, following = snapshot
            profile = self._profiles[profile_id]
            profile.followers.clear()
            profile.followers.update(followers)
            profile.following.clear()
            profile.following.update(following)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _resolve_profile(self, profile_identifier: str) -> ProfileRecord:
        if profile_identifier in self._profiles:
            return self._profiles[profile_identifier]
        if profile_identifier in self._profiles_by_username:
            return self._profiles_by_username[profile_identifier]
        raise ProfileNotFound("Profil tidak ditemukan.")

    def _register_profile(self, profile: ProfileRecord) -> None:
        self._profiles[profile.id] = profile
        self._profiles_by_username[profile.username] = profile

    def _seed_demo_profiles(self) -> None:
        """Create demo data to satisfy the profile UX mocks."""

        amelia = ProfileRecord(
            id="user_amelia",
            username="amelia-damayanti",
            full_name="Amelia Damayanti",
            bio=(
                "Perfumer independen yang gemar mengeksplorasi aroma rempah Nusantara. "
                "Percaya bahwa setiap wewangian punya cerita manis untuk dibagikan."
            ),
            preferred_aroma="Rempah hangat & floral gourmand",
            avatar_url="https://images.unsplash.com/photo-1542293787938-4d2226c3d9f1?auto=format&fit=crop&w=300&q=80",
            location="Bandung, Indonesia",
            tagline="Meracik cerita wangi untuk komunitas.",
            perfumer_products=[
                PerfumerProduct(
                    id="prod_langitsepia",
                    name="Langit Sepia",
                    brand_name="Langit Senja",
                    brand_slug="langit-senja",
                    aroma_notes="Bergamot • Tonka Bean • Patchouli",
                    highlight="Racikan signature bertema golden hour dengan nuansa cozy.",
                ),
                PerfumerProduct(
                    id="prod_hujanpagi",
                    name="Hujan Pagi",
                    brand_name="Langit Senja",
                    brand_slug="langit-senja",
                    aroma_notes="Rain Accord • Vetiver • White Musk",
                    highlight="Aroma petrichor lembut yang menenangkan suasana pagi.",
                ),
            ],
            owned_brands=[
                OwnedBrand(
                    id="brand_langitsenja",
                    name="Langit Senja",
                    slug="langit-senja",
                    logo_url="https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=120&q=80",
                    status="active",
                    tagline="Cerita aroma hangat untuk nostalgia senja.",
                ),
            ],
            activities=[
                TimelineEntry(
                    title="Merilis batch perdana Langit Sepia",
                    timestamp="2 hari lalu",
                    description="Batch pertama ludes dalam 36 jam setelah teaser di komunitas PerfumeLoka.",
                ),
                TimelineEntry(
                    title="Sesi live blending dengan komunitas",
                    timestamp="1 minggu lalu",
                    description="Berbagi proses layering rempah manis dan musk yang bisa dicoba di rumah.",
                ),
            ],
            favorites=[
                "Aroma Senopati – Rumah Wangi",
                "Kopi Sore – SukaSuara",
                "Damar Biru – Cahaya Laut",
            ],
            sambatan_updates=[
                "Mengkurasi 12 peserta untuk Sambatan Hujan Pagi batch 2.",
                "Membantu brand Arunika memilih packaging eco friendly.",
            ],
        )

        bintang = ProfileRecord(
            id="user_bintang",
            username="bintang-waskita",
            full_name="Bintang Waskita",
            bio="Founder Arunika Fragrance. Fokus mengangkat aroma kopi dan cokelat Indonesia.",
            preferred_aroma="Gourmand & woody",
            avatar_url="https://images.unsplash.com/photo-1502323777036-f29e3972d82f?auto=format&fit=crop&w=300&q=80",
            location="Yogyakarta, Indonesia",
            tagline="Menguatkan rasa lokal lewat aroma.",
            owned_brands=[
                OwnedBrand(
                    id="brand_arunika",
                    name="Arunika",
                    slug="arunika",
                    logo_url="https://images.unsplash.com/photo-1545239351-1141bd82e8a6?auto=format&fit=crop&w=120&q=80",
                    status="active",
                    tagline="Eksperimen rasa kopi dan cokelat premium.",
                ),
            ],
            activities=[
                TimelineEntry(
                    title="Memenangkan penghargaan UKM Aroma 2024",
                    timestamp="5 hari lalu",
                    description="Arunika terpilih sebagai brand parfum terinovatif kategori bahan lokal.",
                ),
            ],
            favorites=[
                "Langit Sepia – Langit Senja",
                "Rimba Malam – Cahaya Laut",
            ],
            sambatan_updates=[
                "Mengajak 20 anggota komunitas mencoba eksperimen Macchiato Accord.",
            ],
        )

        chandra = ProfileRecord(
            id="user_chandra",
            username="chandra-pratama",
            full_name="Chandra Pratama",
            bio="Collector fragrance niche dan reviewer tetap di Nusantarum.",
            preferred_aroma="Citrus aromatic",
            avatar_url="https://images.unsplash.com/photo-1544723795-3fb6469f5b39?auto=format&fit=crop&w=300&q=80",
            location="Jakarta, Indonesia",
            tagline="Berbagi insight wewangian buat pemula.",
            activities=[
                TimelineEntry(
                    title="Mengulas Langit Sepia",
                    timestamp="3 hari lalu",
                    description="Memberi rating 4.5/5 dan highlight pada dry-down manisnya yang tahan lama.",
                ),
                TimelineEntry(
                    title="Membuka diskusi komunitas tentang teknik layering",
                    timestamp="2 minggu lalu",
                    description="Mengulas cara memadukan citrus segar dengan gourmand berat.",
                ),
            ],
            favorites=[
                "Hujan Pagi – Langit Senja",
                "Macchiato Drift – Arunika",
                "Teh Senja – Rumah Wangi",
            ],
            sambatan_updates=[
                "Mengikuti Sambatan Macchiato Drift batch 1.",
            ],
        )

        # Register demo profiles.
        for profile in (amelia, bintang, chandra):
            self._register_profile(profile)

        # Establish initial follow graph.
        amelia.followers.update({"user_bintang", "user_chandra"})
        amelia.following.update({"user_bintang"})

        bintang.followers.update({"user_chandra"})
        bintang.following.update({"user_amelia"})

        chandra.followers.update(set())
        chandra.following.update({"user_amelia", "user_bintang"})

        # Snapshot initial relationships for test resets.
        self._initial_relationships = {
            profile.id: profile.clone_relationships() for profile in (amelia, bintang, chandra)
        }


profile_service = ProfileService()
"""Singleton profile service instance shared across routers and tests."""

