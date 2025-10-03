# Codebase Audit - Sensasiwangi.id MVP

## Ringkasan Eksekusi
- Seluruh pengujian automatis proyek berhasil dijalankan menggunakan `pytest` untuk memverifikasi alur utama seperti autentikasi, onboarding, Nusantarum, profil komunitas, dashboard brand, pelaporan, dan Sambatan.【9418c7†L1-L13】【1786bd†L94-L158】【e8f8b8†L17-L193】【16daa8†L33-L133】【bc0c16†L94-L190】

## Observasi Utama per Fitur

### 1. Autentikasi & Sesi
- `AuthService` menyimpan akun dan registrasi verifikasi email sepenuhnya di memori serta melakukan hash password dengan SHA-256 tanpa salt, sehingga lemah terhadap serangan kebocoran hash dan tidak siap produksi.【e3b6c8†L5-L187】
- Middleware sesi saat ini menyimpan payload di dictionary in-memory tanpa kunci thread-safe atau backend terdistribusi; pada deployment multi-proses sesi akan hilang atau balapan tulis bisa terjadi.【9112f0†L56-L105】
- Layanan email hanya melakukan logging ketika pengiriman gagal sehingga route registrasi mengira verifikasi terkirim meskipun provider bermasalah.【29c468†L162-L185】

**Rekomendasi**
- Gunakan library hashing adaptif seperti `bcrypt`/`argon2` dengan salt unik dan pindahkan penyimpanan akun ke Supabase Auth atau database permanen.
- Ganti middleware sesi dengan backend yang mendukung multi-instance (mis. Signed cookies, Redis) dan tambahkan locking bila tetap menggunakan memori lokal.
- Propagasi kegagalan pengiriman email ke lapisan layanan agar UI bisa menampilkan error dan lakukan retry/backoff.

### 2. Onboarding
- Endpoint onboarding mengembalikan `verification_token` secara langsung ke klien dan layanan tidak pernah memanggil utilitas pengiriman email; hal ini membuka risiko token dibocorkan dan membuat pengalaman verifikasi manual.【09fe88†L94-L179】【f6f302†L334-L345】
- Rate limit berbasis dictionary `_rate_limit` tidak membersihkan entri lama sehingga pada volume tinggi akan menambah penggunaan memori.【e01ffb†L141-L169】

**Rekomendasi**
- Hilangkan token dari respons publik dan gunakan channel email via `send_verification_email` dengan audit delivery.
- Tambahkan mekanisme garbage collection atau gunakan struktur TTL (mis. `cachetools.TTLCache`) untuk rate limit.

### 3. Sambatan
- `run_lifecycle` memodifikasi status kampanye tanpa memegang `self._lock`, sehingga bisa balapan dengan `join_campaign`/`cancel_participation` yang memakai lock dan menyebabkan status akhir tidak konsisten.【bc2e9c†L298-L341】
- `confirm_participation` juga tidak memanfaatkan lock sehingga status partisipan bisa bertabrakan dengan pembatalan yang terjadi bersamaan.【bc2e9c†L270-L290】

**Rekomendasi**
- Gunakan lock yang sama di seluruh operasi tulis (konfirmasi, lifecycle) atau beralih ke model penyimpanan transaksional (database) dengan constraint.

### 4. Nusantarum Directory
- `HttpSupabaseGateway` membuat `httpx.AsyncClient` baru di setiap permintaan sehingga tidak memanfaatkan koneksi keep-alive; ini akan memperlambat dan meningkatkan overhead ketika trafik tinggi.【24dc48†L200-L245】
- Cache Nusantarum hanya menyimpan TTL pendek tanpa invalidasi manual sehingga update penting (mis. perubahan status kurasi) bisa tertunda.【24dc48†L274-L346】【9f3093†L1-L72】

**Rekomendasi**
- Kelola `AsyncClient` sebagai instance tunggal/pool dan injeksikan melalui dependency.
- Tambahkan endpoint untuk cache purge atau gunakan layer caching eksternal yang mendukung invalidasi berdasarkan event Supabase.

### 5. Profil Komunitas
- Implementasi default menggunakan gateway in-memory; tanpa konfigurasi Supabase sebenarnya data tidak persisten dan follow/unfollow hanya memodifikasi koleksi lokal, sehingga hasil berbeda antar instance.【9f4c1a†L33-L120】【d85413†L6-L120】

**Rekomendasi**
- Konfigurasikan gateway Supabase pada runtime production dan tambahkan validasi fallback agar deployment menolak berjalan tanpa kredensial.

### 6. Pelaporan
- Generator XLSX menulis file OpenXML manual tanpa stylesheet kompleks; aman untuk dataset kecil tetapi belum menangani format angka/locale khusus.【4d4439†L1-L90】

**Rekomendasi**
- Jika kebutuhan ekspor bertambah, pertimbangkan integrasi `openpyxl`/`xlsxwriter` agar mudah menambahkan format, filter, dan formula.

## Saran Prioritas Perbaikan
1. **Keamanan autentikasi & pengiriman verifikasi** – Terapkan hashing kuat, simpan akun di penyimpanan permanen, dan pastikan notifikasi email gagal dapat terdeteksi.【e3b6c8†L5-L187】【29c468†L162-L185】
2. **Konsistensi Sambatan** – Lindungi seluruh operasi dengan locking atau transaksi sebelum menjalankan kampanye di lingkungan multi-worker.【bc2e9c†L270-L341】
3. **Stabilitas integrasi Supabase** – Reuse koneksi HTTP dan validasi konfigurasi sebelum enabling fitur Nusantarum/profil.【24dc48†L200-L300】【9f4c1a†L33-L120】
4. **Manajemen sesi & cache** – Migrasikan sesi ke backend bersama dan sediakan invalidasi cache eksplisit untuk data penting.【9112f0†L56-L105】【9f3093†L1-L72】

Dengan penerapan rekomendasi di atas, workflow yang sudah diverifikasi oleh test suite akan lebih siap untuk lingkungan produksi bertrafik tinggi sekaligus menjaga keamanan data pengguna.
