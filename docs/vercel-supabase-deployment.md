# Vercel Deployment Guide (FastAPI + Supabase)

Panduan ini menjelaskan cara men-deploy backend FastAPI Sensasiwangi.id ke Vercel
serta menghubungkannya dengan proyek Supabase yang telah disediakan. Langkah-langkah
ini melanjutkan ringkasan integrasi yang pernah dibagikan sebelumnya.

## 1. Menjalankan Migrasi Supabase

1. Instal Supabase CLI minimal v1.153 di mesin lokal:
   ```bash
   npm install -g supabase
   # atau ikuti https://supabase.com/docs/guides/cli
   ```
2. Login ke Supabase CLI dan hubungkan ke project ID yang relevan:
   ```bash
   supabase login
   supabase link --project-ref yguckgrnvzvbxtygbzke
   ```
3. Dorong seluruh skema yang tersedia di folder `supabase/migrations`:
   ```bash
   supabase db push
   ```
   Perintah ini akan membuat tabel marketplace, Nusantarum, onboarding, dan
   relasi yang sudah diatur pada migrasi SQL.

> **Catatan**: Bila prefer menggunakan `psql`, jalankan masing-masing file SQL
> secara berurutan terhadap database Supabase produksi/staging Anda.

## 2. Menyiapkan Variabel Lingkungan

1. Gandakan `.env.example` menjadi `.env` untuk pengembangan lokal:
   ```bash
   cp .env.example .env
   ```
2. Isi variabel yang diberikan:
   ```bash
   SUPABASE_URL=https://yguckgrnvzvbxtygbzke.supabase.co
   SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlndWNrZ3Judnp2Ynh0eWdiemtlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTg5Mzg0NTIsImV4cCI6MjA3NDUxNDQ1Mn0.psMSy6vys-6rEKzJbUmX87j9zmB6dE94zc1_nVakuLU
   SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlndWNrZ3Judnp2Ynh0eWdiemtlIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1ODkzODQ1MiwiZXhwIjoyMDc0NTE0NDUyfQ.QYhkQk59D3Y_GBEhNz8amto-RP_WHL-2_tQtGnE8Ia0
   SESSION_SECRET=ganti-dengan-string-acak
   ```
   Pastikan `SESSION_SECRET` berisi string acak minimal 32 karakter pada
   lingkungan produksi.
3. Untuk pengembangan lokal, jalankan Uvicorn seperti biasa dan backend akan
   otomatis membaca variabel tersebut melalui `pydantic-settings`.

## 3. Konfigurasi Deployment Vercel

1. Import repositori GitHub ke Vercel dan pilih framework **Other**.
2. Pada tab **Environment Variables**, tambahkan tiga key Supabase di atas.
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY` (gunakan **Encrypted**/Production scope saja)
3. Tambahkan variabel `SESSION_SECRET` terpisah untuk keamanan.
4. Di tab **Build & Development Settings**, set:
   - **Build Command**: `pip install -r requirements.txt`
   - **Output Directory**: kosongkan (karena FastAPI dijalankan sebagai serverless)
   - **Install Command**: biarkan default
5. Pastikan Vercel mendeteksi file `main.py` yang mengekspos objek `app`. Bila
   perlu, buat file `vercel.json` dengan isi berikut di root repo:
   ```json
   {
     "builds": [
       { "src": "main.py", "use": "@vercel/python" }
     ],
     "routes": [
       { "src": "/(.*)", "dest": "main.py" }
     ]
   }
   ```
6. Deploy project. Vercel akan menjalankan FastAPI menggunakan adapter Python
   bawaan, sementara `NusantarumService` akan memanggil PostgREST Supabase dengan
   kredensial yang sudah dikonfigurasi.

## 4. Verifikasi Integrasi

- Gunakan endpoint Nusantarum (`/nusantarum` pada router web) untuk memastikan
  data berhasil diambil dari Supabase.
- Periksa log Vercel jika terjadi error 500; pesan `Supabase credentials belum
  dikonfigurasi` menandakan variabel lingkungan belum terset dengan benar.

Selamat! Dengan langkah di atas, pipeline Codex × Vercel × Supabase sudah siap.
