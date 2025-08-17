# Deployment dengan Docker Compose

Dokumen ini menjelaskan cara menjalankan **SKKNI HTTP Scraper** menggunakan Docker Compose untuk lingkungan **development** maupun **production** (opsional di balik Traefik).

> Catatan:
> - Perintah di bawah menggunakan `sudo` sesuai preferensi Anda.
> - Gunakan `docker compose` (bukan `docker-compose`).

---

## 1) Prasyarat

- Linux host dengan Docker Engine & Docker Compose plugin.
- Port 8000 bebas atau sesuaikan publikasi port di Compose.
- (Opsional Production) Traefik sudah berjalan sebagai reverse proxy dan memiliki external network.

Cek versi:
```bash
sudo docker --version
sudo docker compose version
```

---

## 2) Konfigurasi Lingkungan

Buat file `.env` di root project (sesuaikan nilai):

```env
# Database lokal (default SQLite)
DATABASE_URL=sqlite:///./skkni_cache.db

# Playwright / Scraper
HEADLESS=true
CACHE_TTL_DAYS=30
MAX_CONCURRENCY=2

# CORS (pisahkan dengan koma)
ALLOWED_ORIGINS=http://localhost:5678,https://yapi.simetri-sinergi.id

# Aplikasi
APP_PORT=8000

# (Opsional) Traefik
TRAEFIK_ENABLE=false
TRAEFIK_ENTRYPOINT=websecure
TRAEFIK_DOMAIN=skkni.simetri-sinergi.id
TRAEFIK_TLS=true
```

---

## 3) File `docker-compose.yml`

### 3.1 Versi Minimal (Tanpa Traefik)

```yaml
version: "3.9"

services:
  scraper:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: skkni_http_scraper
    env_file:
      - .env
    ports:
      - "8000:${APP_PORT}"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://127.0.0.1:${APP_PORT}/docs"]
      interval: 30s
      timeout: 5s
      retries: 5
      start_period: 20s
    volumes:
      - ./data:/app/data
    working_dir: /app
```

### 3.2 Versi Production (Di Balik Traefik)

```yaml
version: "3.9"

networks:
  traefik_proxy:
    external: true

services:
  scraper:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: skkni_http_scraper
    env_file:
      - .env
    networks:
      - traefik_proxy
    expose:
      - "${APP_PORT}"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://127.0.0.1:${APP_PORT}/docs"]
      interval: 30s
      timeout: 5s
      retries: 5
      start_period: 20s
    volumes:
      - ./data:/app/data
    labels:
      - "traefik.enable=${TRAEFIK_ENABLE}"
      - "traefik.http.routers.skkni.rule=Host(`${TRAEFIK_DOMAIN}`)"
      - "traefik.http.routers.skkni.entrypoints=${TRAEFIK_ENTRYPOINT}"
      - "traefik.http.routers.skkni.tls=${TRAEFIK_TLS}"
      - "traefik.http.services.skkni.loadbalancer.server.port=${APP_PORT}"
```

---

## 4) Menjalankan Stack

```bash
sudo docker compose down --remove-orphans -v
sudo docker compose pull || true
sudo docker compose build --no-cache
sudo docker compose up -d
```

---

## 5) Verifikasi

```bash
sudo docker compose ps
sudo docker compose logs -f
```

---

## 6) Perintah Harian

```bash
sudo docker compose logs --tail=200 scraper
sudo docker compose restart scraper
sudo docker compose pull && sudo docker compose up -d
sudo docker system prune -f
```

---

## 7) Troubleshooting

- **YAML error**: gunakan `sudo docker compose config`
- **Traefik error**: cek network & label
- **DB error**: sesuaikan `DATABASE_URL` jika pakai PostgreSQL/MySQL
- **Playwright**: untuk debug, set `HEADLESS=false`

---

## 8) Rollback

```bash
sudo docker compose down --remove-orphans
# ubah tag image jika perlu
sudo docker compose up -d
```

---

## 9) Keamanan Production

- Simpan `.env` di luar repo publik.
- Minimalkan port publik (gunakan Traefik + TLS).
- Batasi `ALLOWED_ORIGINS` hanya domain/klien tepercaya.
- Gunakan storage persisten untuk database.
