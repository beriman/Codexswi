"""Profile service powering the community-centric profile page."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Protocol

try:  # pragma: no cover - optional dependency for the Supabase gateway
    import httpx
except ModuleNotFoundError:  # pragma: no cover - environments without httpx
    httpx = None  # type: ignore[assignment]


class ProfileError(Exception):
    """Base error class for profile operations."""

    status_code: int = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ProfileNotFound(ProfileError):
    """Raised when attempting to access an unknown profile."""

    status_code = 404


@dataclass(frozen=True)
class ProfileUpdate:
    """Payload for profile mutation submitted from the edit form."""

    full_name: str
    bio: Optional[str] = None
    preferred_aroma: Optional[str] = None
    avatar_url: Optional[str] = None
    location: Optional[str] = None

    def to_payload(self) -> Dict[str, Any]:
        data = {
            "full_name": self.full_name,
            "bio": self.bio,
            "preferred_aroma": self.preferred_aroma,
            "avatar_url": self.avatar_url,
            "location": self.location,
        }
        return data


class ProfileGateway(Protocol):
    """Abstraction for profile persistence backed by Supabase."""

    async def fetch_profile(self, identifier: str) -> Optional[Dict[str, Any]]:
        ...

    async def fetch_profile_stats(self, profile_id: str) -> Optional[Dict[str, Any]]:
        ...

    async def fetch_follow_graph(self, profile_id: str) -> Dict[str, List[str]]:
        ...

    async def fetch_followers(self, profile_id: str) -> List[Dict[str, Any]]:
        ...

    async def fetch_following(self, profile_id: str) -> List[Dict[str, Any]]:
        ...

    async def fetch_perfumer_products(self, profile_id: str) -> List[Dict[str, Any]]:
        ...

    async def fetch_owned_brands(self, profile_id: str) -> List[Dict[str, Any]]:
        ...

    async def check_following(self, *, follower_id: str, following_id: str) -> bool:
        ...

    async def create_follow(self, *, follower_id: str, following_id: str) -> None:
        ...

    async def delete_follow(self, *, follower_id: str, following_id: str) -> None:
        ...

    async def update_profile(self, profile_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        ...


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
    """Representation of a user profile loaded from Supabase."""

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


class SupabaseProfileGateway(ProfileGateway):
    """HTTP-based gateway that interacts with Supabase PostgREST endpoints."""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        schema: str = "public",
        timeout: float = 10.0,
    ) -> None:
        if httpx is None:  # pragma: no cover - handled during runtime configuration
            raise RuntimeError(
                "httpx package is required for Supabase integration. "
                "Install httpx to enable the Supabase profile gateway."
            )

        base = base_url.rstrip("/") + "/rest/v1"
        self._client = httpx.AsyncClient(base_url=base, timeout=timeout)
        self._schema = schema
        self._headers = {
            "apikey": api_key,
            "Authorization": f"Bearer {api_key}",
            "Accept-Profile": schema,
        }

    async def _get(self, resource: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        response = await self._client.get(resource, params=params, headers=self._headers)
        response.raise_for_status()
        return response.json()

    async def fetch_profile(self, identifier: str) -> Optional[Dict[str, Any]]:
        params = {
            "select": "id,username,full_name,bio,preferred_aroma,avatar_url,location,tagline",
            "or": f"(username.eq.{identifier},id.eq.{identifier})",
            "limit": 1,
        }
        rows = await self._get("/user_profiles", params)
        return rows[0] if rows else None

    async def fetch_profile_stats(self, profile_id: str) -> Optional[Dict[str, Any]]:
        params = {
            "select": "profile_id,follower_count,following_count,perfumer_product_count,owned_brand_count",
            "profile_id": f"eq.{profile_id}",
            "limit": 1,
        }
        rows = await self._get("/user_profile_stats", params)
        return rows[0] if rows else None

    async def fetch_follow_graph(self, profile_id: str) -> Dict[str, List[str]]:
        params = {
            "select": "follower_id,following_id",
            "or": f"(follower_id.eq.{profile_id},following_id.eq.{profile_id})",
        }
        rows = await self._get("/user_follows", params)
        followers = [row["follower_id"] for row in rows if row["following_id"] == profile_id]
        following = [row["following_id"] for row in rows if row["follower_id"] == profile_id]
        return {"followers": followers, "following": following}

    async def fetch_followers(self, profile_id: str) -> List[Dict[str, Any]]:
        graph = await self.fetch_follow_graph(profile_id)
        follower_ids = graph.get("followers", [])
        if not follower_ids:
            return []
        params = {
            "select": "id,username,full_name,avatar_url",
            "id": f"in.({','.join(follower_ids)})",
        }
        rows = await self._get("/user_profiles", params)
        return sorted(rows, key=lambda item: item.get("full_name", ""))

    async def fetch_following(self, profile_id: str) -> List[Dict[str, Any]]:
        graph = await self.fetch_follow_graph(profile_id)
        following_ids = graph.get("following", [])
        if not following_ids:
            return []
        params = {
            "select": "id,username,full_name,avatar_url",
            "id": f"in.({','.join(following_ids)})",
        }
        rows = await self._get("/user_profiles", params)
        return sorted(rows, key=lambda item: item.get("full_name", ""))

    async def fetch_perfumer_products(self, profile_id: str) -> List[Dict[str, Any]]:
        params = {
            "select": (
                "product_id:id,role,"
                "product:products(id,name,highlight,aroma_notes,"
                "brand:brands(id,name,slug))"
            ),
            "perfumer_profile_id": f"eq.{profile_id}",
        }
        rows = await self._get("/product_perfumers", params)
        items: List[Dict[str, Any]] = []
        for row in rows:
            product = row.get("product", {})
            brand = product.get("brand", {})
            items.append(
                {
                    "id": product.get("id", ""),
                    "name": product.get("name", ""),
                    "brand_name": brand.get("name", ""),
                    "brand_slug": brand.get("slug", ""),
                    "aroma_notes": product.get("aroma_notes", ""),
                    "highlight": product.get("highlight", ""),
                }
            )
        return items

    async def fetch_owned_brands(self, profile_id: str) -> List[Dict[str, Any]]:
        params = {
            "select": "brand_id:id,name,slug,logo_path,status,tagline",
            "profile_id": f"eq.{profile_id}",
        }
        rows = await self._get("/profile_brand_summary", params)
        items: List[Dict[str, Any]] = []
        for row in rows:
            items.append(
                {
                    "id": row.get("brand_id", ""),
                    "name": row.get("name", ""),
                    "slug": row.get("slug", ""),
                    "logo_url": row.get("logo_path", ""),
                    "status": row.get("status", ""),
                    "tagline": row.get("tagline", ""),
                }
            )
        return items

    async def check_following(self, *, follower_id: str, following_id: str) -> bool:
        params = {
            "select": "follower_id,following_id",
            "follower_id": f"eq.{follower_id}",
            "following_id": f"eq.{following_id}",
            "limit": 1,
        }
        rows = await self._get("/user_follows", params)
        return bool(rows)

    async def create_follow(self, *, follower_id: str, following_id: str) -> None:
        payload = {"follower_id": follower_id, "following_id": following_id}
        headers = {"Prefer": "return=minimal", **self._headers}
        response = await self._client.post("/user_follows", json=payload, headers=headers)
        if response.status_code not in (200, 201, 204):  # pragma: no cover - httpx raises elsewhere
            response.raise_for_status()

    async def delete_follow(self, *, follower_id: str, following_id: str) -> None:
        params = {
            "follower_id": f"eq.{follower_id}",
            "following_id": f"eq.{following_id}",
        }
        headers = {"Prefer": "return=minimal", **self._headers}
        response = await self._client.delete("/user_follows", params=params, headers=headers)
        if response.status_code not in (200, 204):  # pragma: no cover - httpx raises elsewhere
            response.raise_for_status()

    async def update_profile(self, profile_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        headers = {"Prefer": "return=representation", **self._headers}
        params = {"id": f"eq.{profile_id}"}
        response = await self._client.patch(
            "/user_profiles", params=params, json=payload, headers=headers
        )
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list):
            return data[0] if data else {}
        return data


class InMemoryProfileGateway(ProfileGateway):
    """In-memory implementation used for local development and tests."""

    def __init__(self) -> None:
        self._profiles: Dict[str, Dict[str, Any]] = {}
        self._profiles_by_username: Dict[str, Dict[str, Any]] = {}
        self._followers: Dict[str, set[str]] = {}
        self._following: Dict[str, set[str]] = {}
        self._perfumer_products: Dict[str, List[Dict[str, Any]]] = {}
        self._owned_brands: Dict[str, List[Dict[str, Any]]] = {}
        self._initial_relationships: Dict[str, tuple[set[str], set[str]]] = {}
        self._seed_demo_profiles()

    async def fetch_profile(self, identifier: str) -> Optional[Dict[str, Any]]:
        if identifier in self._profiles:
            return dict(self._profiles[identifier])
        if identifier in self._profiles_by_username:
            return dict(self._profiles_by_username[identifier])
        return None

    async def fetch_profile_stats(self, profile_id: str) -> Optional[Dict[str, Any]]:
        follower_ids = self._followers.get(profile_id, set())
        following_ids = self._following.get(profile_id, set())
        perfumer_products = self._perfumer_products.get(profile_id, [])
        owned_brands = [
            brand for brand in self._owned_brands.get(profile_id, []) if brand.get("status") == "active"
        ]
        return {
            "profile_id": profile_id,
            "follower_count": len(follower_ids),
            "following_count": len(following_ids),
            "perfumer_product_count": len(perfumer_products),
            "owned_brand_count": len(owned_brands),
        }

    async def fetch_follow_graph(self, profile_id: str) -> Dict[str, List[str]]:
        followers = list(self._followers.get(profile_id, set()))
        following = list(self._following.get(profile_id, set()))
        return {"followers": followers, "following": following}

    async def fetch_followers(self, profile_id: str) -> List[Dict[str, Any]]:
        follower_ids = self._followers.get(profile_id, set())
        profiles = [dict(self._profiles[follower_id]) for follower_id in follower_ids]
        return sorted(profiles, key=lambda item: item.get("full_name", ""))

    async def fetch_following(self, profile_id: str) -> List[Dict[str, Any]]:
        following_ids = self._following.get(profile_id, set())
        profiles = [dict(self._profiles[following_id]) for following_id in following_ids]
        return sorted(profiles, key=lambda item: item.get("full_name", ""))

    async def fetch_perfumer_products(self, profile_id: str) -> List[Dict[str, Any]]:
        return [dict(item) for item in self._perfumer_products.get(profile_id, [])]

    async def fetch_owned_brands(self, profile_id: str) -> List[Dict[str, Any]]:
        return [dict(item) for item in self._owned_brands.get(profile_id, [])]

    async def check_following(self, *, follower_id: str, following_id: str) -> bool:
        return follower_id in self._followers.get(following_id, set())

    async def create_follow(self, *, follower_id: str, following_id: str) -> None:
        self._followers.setdefault(following_id, set()).add(follower_id)
        self._following.setdefault(follower_id, set()).add(following_id)

    async def delete_follow(self, *, follower_id: str, following_id: str) -> None:
        self._followers.setdefault(following_id, set()).discard(follower_id)
        self._following.setdefault(follower_id, set()).discard(following_id)

    async def update_profile(self, profile_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        profile = self._profiles.get(profile_id)
        if not profile:
            raise ProfileNotFound("Profil tidak ditemukan.")

        username = profile.get("username")
        profile.update(payload)
        if username:
            self._profiles_by_username[username] = profile
        return dict(profile)

    async def reset_relationships(self) -> None:
        for profile_id, snapshot in self._initial_relationships.items():
            followers, following = snapshot
            self._followers[profile_id] = set(followers)
            self._following[profile_id] = set(following)

    def _register_profile(self, profile: Dict[str, Any]) -> None:
        self._profiles[profile["id"]] = profile
        self._profiles_by_username[profile["username"]] = profile
        self._followers.setdefault(profile["id"], set())
        self._following.setdefault(profile["id"], set())

    def _seed_demo_profiles(self) -> None:
        amelia = {
            "id": "user_amelia",
            "username": "amelia-damayanti",
            "full_name": "Amelia Damayanti",
            "bio": (
                "Perfumer independen yang gemar mengeksplorasi aroma rempah Nusantara. "
                "Percaya bahwa setiap wewangian punya cerita manis untuk dibagikan."
            ),
            "preferred_aroma": "Rempah hangat & floral gourmand",
            "avatar_url": "https://images.unsplash.com/photo-1542293787938-4d2226c3d9f1?auto=format&fit=crop&w=300&q=80",
            "location": "Bandung, Indonesia",
            "tagline": "Meracik cerita wangi untuk komunitas.",
            "activities": [
                {
                    "title": "Merilis batch perdana Langit Sepia",
                    "timestamp": "2 hari lalu",
                    "description": "Batch pertama ludes dalam 36 jam setelah teaser di komunitas PerfumeLoka.",
                },
                {
                    "title": "Sesi live blending dengan komunitas",
                    "timestamp": "1 minggu lalu",
                    "description": "Berbagi proses layering rempah manis dan musk yang bisa dicoba di rumah.",
                },
            ],
            "favorites": [
                "Aroma Senopati – Rumah Wangi",
                "Kopi Sore – SukaSuara",
                "Damar Biru – Cahaya Laut",
            ],
            "sambatan_updates": [
                "Mengkurasi 12 peserta untuk Sambatan Hujan Pagi batch 2.",
                "Membantu brand Arunika memilih packaging eco friendly.",
            ],
        }

        bintang = {
            "id": "user_bintang",
            "username": "bintang-waskita",
            "full_name": "Bintang Waskita",
            "bio": "Founder Arunika Fragrance. Fokus mengangkat aroma kopi dan cokelat Indonesia.",
            "preferred_aroma": "Gourmand & woody",
            "avatar_url": "https://images.unsplash.com/photo-1502323777036-f29e3972d82f?auto=format&fit=crop&w=300&q=80",
            "location": "Yogyakarta, Indonesia",
            "tagline": "Menguatkan rasa lokal lewat aroma.",
            "activities": [
                {
                    "title": "Memenangkan penghargaan UKM Aroma 2024",
                    "timestamp": "5 hari lalu",
                    "description": "Arunika terpilih sebagai brand parfum terinovatif kategori bahan lokal.",
                },
            ],
            "favorites": [
                "Langit Sepia – Langit Senja",
                "Rimba Malam – Cahaya Laut",
            ],
            "sambatan_updates": [
                "Mengajak 20 anggota komunitas mencoba eksperimen Macchiato Accord.",
            ],
        }

        chandra = {
            "id": "user_chandra",
            "username": "chandra-pratama",
            "full_name": "Chandra Pratama",
            "bio": "Collector fragrance niche dan reviewer tetap di Nusantarum.",
            "preferred_aroma": "Citrus aromatic",
            "avatar_url": "https://images.unsplash.com/photo-1544723795-3fb6469f5b39?auto=format&fit=crop&w=300&q=80",
            "location": "Jakarta, Indonesia",
            "tagline": "Berbagi insight wewangian buat pemula.",
            "activities": [
                {
                    "title": "Mengulas Langit Sepia",
                    "timestamp": "3 hari lalu",
                    "description": "Memberi rating 4.5/5 dan highlight pada dry-down manisnya yang tahan lama.",
                },
                {
                    "title": "Membuka diskusi komunitas tentang teknik layering",
                    "timestamp": "2 minggu lalu",
                    "description": "Mengulas cara memadukan citrus segar dengan gourmand berat.",
                },
            ],
            "favorites": [
                "Hujan Pagi – Langit Senja",
                "Macchiato Drift – Arunika",
                "Teh Senja – Rumah Wangi",
            ],
            "sambatan_updates": [
                "Mengikuti Sambatan Macchiato Drift batch 1.",
            ],
        }

        self._perfumer_products = {
            "user_amelia": [
                {
                    "id": "prod_langitsepia",
                    "name": "Langit Sepia",
                    "brand_name": "Langit Senja",
                    "brand_slug": "langit-senja",
                    "aroma_notes": "Bergamot • Tonka Bean • Patchouli",
                    "highlight": "Racikan signature bertema golden hour dengan nuansa cozy.",
                },
                {
                    "id": "prod_hujanpagi",
                    "name": "Hujan Pagi",
                    "brand_name": "Langit Senja",
                    "brand_slug": "langit-senja",
                    "aroma_notes": "Rain Accord • Vetiver • White Musk",
                    "highlight": "Aroma petrichor lembut yang menenangkan suasana pagi.",
                },
            ],
        }

        self._owned_brands = {
            "user_amelia": [
                {
                    "id": "brand_langitsenja",
                    "name": "Langit Senja",
                    "slug": "langit-senja",
                    "logo_url": "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=120&q=80",
                    "status": "active",
                    "tagline": "Cerita aroma hangat untuk nostalgia senja.",
                },
            ],
            "user_bintang": [
                {
                    "id": "brand_arunika",
                    "name": "Arunika",
                    "slug": "arunika",
                    "logo_url": "https://images.unsplash.com/photo-1545239351-1141bd82e8a6?auto=format&fit=crop&w=120&q=80",
                    "status": "active",
                    "tagline": "Eksperimen rasa kopi dan cokelat premium.",
                },
            ],
            "user_chandra": [],
        }

        for profile in (amelia, bintang, chandra):
            self._register_profile(profile)

        self._followers = {
            "user_amelia": {"user_bintang", "user_chandra"},
            "user_bintang": {"user_chandra"},
            "user_chandra": set(),
        }
        self._following = {
            "user_amelia": {"user_bintang"},
            "user_bintang": {"user_amelia"},
            "user_chandra": {"user_amelia", "user_bintang"},
        }

        self._initial_relationships = {
            profile_id: (set(followers), set(self._following.get(profile_id, set())))
            for profile_id, followers in self._followers.items()
        }


class ProfileService:
    """Profile orchestration layer backed by a Supabase gateway."""

    def __init__(self, gateway: Optional[ProfileGateway] = None) -> None:
        self._gateway = gateway or InMemoryProfileGateway()

    async def get_profile(self, profile_identifier: str, *, viewer_id: Optional[str] = None) -> ProfileView:
        profile_data = await self._resolve_profile_data(profile_identifier)
        profile_id = profile_data["id"]

        stats_data = await self._gateway.fetch_profile_stats(profile_id)
        follow_graph = await self._gateway.fetch_follow_graph(profile_id)
        perfumer_products = await self._gateway.fetch_perfumer_products(profile_id)
        owned_brands = await self._gateway.fetch_owned_brands(profile_id)

        profile = self._build_profile_record(
            profile_data,
            followers=follow_graph.get("followers", []),
            following=follow_graph.get("following", []),
            perfumer_products=perfumer_products,
            owned_brands=owned_brands,
        )

        stats = self._build_profile_stats(stats_data, profile)

        viewer = ProfileViewerState(
            id=viewer_id,
            is_owner=viewer_id == profile.id if viewer_id else False,
            is_following=(viewer_id in profile.followers) if viewer_id else False,
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

        return ProfileView(profile=profile, stats=stats, badges=badges, viewer=viewer)

    async def follow_profile(self, target_identifier: str, *, follower_id: str) -> ProfileView:
        follower = await self._resolve_profile_data(follower_id)
        target = await self._resolve_profile_data(target_identifier)

        if follower["id"] == target["id"]:
            raise ProfileError("Tidak dapat mengikuti profil sendiri.")

        is_following = await self._gateway.check_following(
            follower_id=follower["id"], following_id=target["id"]
        )
        if not is_following:
            await self._gateway.create_follow(follower_id=follower["id"], following_id=target["id"])

        return await self.get_profile(target["id"], viewer_id=follower["id"])

    async def unfollow_profile(self, target_identifier: str, *, follower_id: str) -> ProfileView:
        follower = await self._resolve_profile_data(follower_id)
        target = await self._resolve_profile_data(target_identifier)

        if follower["id"] == target["id"]:
            raise ProfileError("Tidak dapat berhenti mengikuti profil sendiri.")

        is_following = await self._gateway.check_following(
            follower_id=follower["id"], following_id=target["id"]
        )
        if is_following:
            await self._gateway.delete_follow(follower_id=follower["id"], following_id=target["id"])

        return await self.get_profile(target["id"], viewer_id=follower["id"])

    async def update_profile(
        self, profile_identifier: str, *, viewer_id: str, payload: ProfileUpdate
    ) -> tuple[ProfileView, bool]:
        profile_data = await self._resolve_profile_data(profile_identifier)
        viewer_data = await self._resolve_profile_data(viewer_id)

        if profile_data["id"] != viewer_data["id"]:
            raise ProfileError("Tidak memiliki akses untuk memperbarui profil ini.")

        update_payload = payload.to_payload()
        if not update_payload:
            profile_view = await self.get_profile(
                profile_data["id"], viewer_id=viewer_data["id"]
            )
            return profile_view, False

        def _normalize(value: Any) -> Any:
            if value is None:
                return None
            if isinstance(value, str):
                trimmed = value.strip()
                return trimmed or None
            return value

        changes = {
            key: value
            for key, value in update_payload.items()
            if _normalize(profile_data.get(key)) != _normalize(value)
        }

        if changes:
            await self._gateway.update_profile(profile_data["id"], changes)

        profile_view = await self.get_profile(
            profile_data["id"], viewer_id=viewer_data["id"]
        )
        return profile_view, bool(changes)

    async def list_followers(self, profile_identifier: str) -> List[ProfileRecord]:
        profile_data = await self._resolve_profile_data(profile_identifier)
        followers = await self._gateway.fetch_followers(profile_data["id"])
        return [self._build_profile_record(item) for item in followers]

    async def list_following(self, profile_identifier: str) -> List[ProfileRecord]:
        profile_data = await self._resolve_profile_data(profile_identifier)
        following = await self._gateway.fetch_following(profile_data["id"])
        return [self._build_profile_record(item) for item in following]

    async def list_perfumer_products(self, profile_identifier: str) -> List[PerfumerProduct]:
        profile_data = await self._resolve_profile_data(profile_identifier)
        products = await self._gateway.fetch_perfumer_products(profile_data["id"])
        return [self._build_perfumer_product(item) for item in products]

    async def list_owned_brands(self, profile_identifier: str) -> List[OwnedBrand]:
        profile_data = await self._resolve_profile_data(profile_identifier)
        brands = await self._gateway.fetch_owned_brands(profile_data["id"])
        return [self._build_owned_brand(item) for item in brands]

    async def reset_relationships(self) -> None:
        reset = getattr(self._gateway, "reset_relationships", None)
        if reset is None:
            return
        result = reset()
        if hasattr(result, "__await__"):
            await result  # type: ignore[func-returns-value]

    async def _resolve_profile_data(self, identifier: str) -> Dict[str, Any]:
        profile_data = await self._gateway.fetch_profile(identifier)
        if not profile_data:
            raise ProfileNotFound("Profil tidak ditemukan.")
        return profile_data

    def _build_profile_record(
        self,
        data: Dict[str, Any],
        *,
        followers: Iterable[str] | None = None,
        following: Iterable[str] | None = None,
        perfumer_products: Iterable[Dict[str, Any]] | Iterable[PerfumerProduct] | None = None,
        owned_brands: Iterable[Dict[str, Any]] | Iterable[OwnedBrand] | None = None,
    ) -> ProfileRecord:
        return ProfileRecord(
            id=data.get("id", ""),
            username=data.get("username", ""),
            full_name=data.get("full_name", ""),
            bio=data.get("bio", ""),
            preferred_aroma=data.get("preferred_aroma"),
            avatar_url=data.get("avatar_url"),
            location=data.get("location"),
            tagline=data.get("tagline"),
            followers=set(followers or []),
            following=set(following or []),
            perfumer_products=[self._build_perfumer_product(item) for item in perfumer_products or []],
            owned_brands=[self._build_owned_brand(item) for item in owned_brands or []],
            activities=[self._build_timeline_entry(item) for item in data.get("activities", [])],
            favorites=list(data.get("favorites", [])),
            sambatan_updates=list(data.get("sambatan_updates", [])),
        )

    def _build_profile_stats(self, stats: Optional[Dict[str, Any]], profile: ProfileRecord) -> ProfileStats:
        if not stats:
            return ProfileStats(
                follower_count=len(profile.followers),
                following_count=len(profile.following),
                perfumer_product_count=len(profile.perfumer_products),
                owned_brand_count=len(profile.owned_brands),
            )
        return ProfileStats(
            follower_count=stats.get("follower_count", len(profile.followers)),
            following_count=stats.get("following_count", len(profile.following)),
            perfumer_product_count=stats.get("perfumer_product_count", len(profile.perfumer_products)),
            owned_brand_count=stats.get("owned_brand_count", len(profile.owned_brands)),
        )

    def _build_perfumer_product(self, data: Dict[str, Any] | PerfumerProduct) -> PerfumerProduct:
        if isinstance(data, PerfumerProduct):
            return data
        return PerfumerProduct(
            id=data.get("id", ""),
            name=data.get("name", ""),
            brand_name=data.get("brand_name", ""),
            brand_slug=data.get("brand_slug", ""),
            aroma_notes=data.get("aroma_notes", ""),
            highlight=data.get("highlight", ""),
        )

    def _build_owned_brand(self, data: Dict[str, Any] | OwnedBrand) -> OwnedBrand:
        if isinstance(data, OwnedBrand):
            return data
        return OwnedBrand(
            id=data.get("id", ""),
            name=data.get("name", ""),
            slug=data.get("slug", ""),
            logo_url=data.get("logo_url", ""),
            status=data.get("status", ""),
            tagline=data.get("tagline", ""),
        )

    def _build_timeline_entry(self, data: Dict[str, Any] | TimelineEntry) -> TimelineEntry:
        if isinstance(data, TimelineEntry):
            return data
        return TimelineEntry(
            title=data.get("title", ""),
            timestamp=data.get("timestamp", ""),
            description=data.get("description", ""),
        )


profile_service = ProfileService()
"""Singleton profile service instance shared across routers and tests."""
