# 0002 – Runtime Base
Tanggal: 2025-08-17
Status: Disetujui

## Konteks
Performa build dan kecocokan pustaka C-ext lebih stabil di image Debian slim dibanding Alpine untuk stack saat ini.

## Keputusan
- Docker base image: **`python:3.12.11-slim`**.
- Menetapkan versi patch spesifik untuk repeatability (dapat ditingkatkan patch berikutnya bila rilis keamanan tersedia).
- Menambahkan env default: `PIP_DISABLE_PIP_VERSION_CHECK=1`, `PIP_NO_CACHE_DIR=1`, `PYTHONDONTWRITEBYTECODE=1`.

## Konsekuensi
- Build lebih konsisten lintas mesin.
- Ukuran image tetap efisien namun kompatibel dengan C-ext.
- Kenaikan patch perlu pembaruan `Dockerfile` + dokumentasi.
