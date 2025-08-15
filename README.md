# 📚 SKKNI HTTP Scraper

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688?logo=fastapi)
![Playwright](https://img.shields.io/badge/Playwright-Testing-2EAD33?logo=playwright)
![SQLite](https://img.shields.io/badge/SQLite-DB-003B57?logo=sqlite)
![License](https://img.shields.io/badge/License-MIT-green)
[![CI](https://github.com/andhit-r/skkni-http-scraper/actions/workflows/ci.yml/badge.svg)](https://github.com/andhit-r/skkni-http-scraper/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/andhit-t/skkni-http-scraper/branch/main/graph/badge.svg)](https://codecov.io/gh/andhit-r/skkni-http-scraper)


> **SKKNI HTTP Scraper** adalah layanan HTTP berbasis [FastAPI](https://fastapi.tiangolo.com/) untuk mengambil data **dokumen** dan **unit kompetensi** dari portal resmi SKKNI (Kemnaker), lengkap dengan caching lokal menggunakan SQLite.

---

## ✨ Fitur Utama

- 🚀 **Scraping langsung** dari portal SKKNI (dokumen & unit kompetensi).
- 💾 **Cache otomatis** ke database lokal (SQLite) untuk menghindari scraping berulang.
- 🏷 **Normalisasi** sektor, bidang, sub-bidang ke tabel master terpisah.
- 📄 **Swagger UI** & **ReDoc** untuk dokumentasi API interaktif.
- 🌐 **CORS support** untuk integrasi dengan Odoo, n8n, dan front-end lain.
- ⚡ **Limit paralel scraping** & konfigurasi TTL cache.
- 🔍 Filter `force_refresh`, `include_merged`, `sektor`, dan pagination.

---

## 📦 Instalasi

### 1. Clone Repository
```bash
git clone https://github.com/username/skkni-http-scraper.git
cd skkni-http-scraper
```

### 2. Buat Virtual Environment & Install Dependencies
```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Jalankan Server
```bash
uvicorn app.main:app --reload
```

---

## ⚙️ Konfigurasi Environment

Buat file `.env` di root proyek:

```env
DATABASE_URL=sqlite:///./skkni_cache.db
HEADLESS=true
CACHE_TTL_DAYS=30
MAX_CONCURRENCY=2
ALLOWED_ORIGINS=http://localhost:5678,https://yapi.simetri-sinergi.id
```

---

## 📚 API Documentation

Setelah server berjalan, dokumentasi API tersedia di:

- 📖 Swagger UI → [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- 📖 ReDoc → [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 🔍 Contoh Request

Ambil 2 dokumen pertama:
```bash
curl "http://127.0.0.1:8000/skkni/search-documents?page_from=1&page_to=1&limit=2"
```

Ambil unit kompetensi dengan filter sektor:
```bash
curl "http://127.0.0.1:8000/skkni/search-units?sektor=industri&page_from=1&page_to=1&limit=2"
```

---

## 🛠 Struktur Direktori

```
skkni-http-scraper/
├── app/
│   ├── api/v1/endpoints/   # Endpoint API
│   ├── core/               # Config & settings
│   ├── db/                 # Model & session DB
│   ├── repositories/       # Logika akses data
│   ├── utils/              # Helper (Playwright, dll)
│   └── main.py              # Entry FastAPI
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 🧪 Development Tips

- Gunakan `--reload` saat development.
- Untuk debug scraping, set `HEADLESS=false` di `.env`.
- Gunakan `CACHE_TTL_DAYS` lebih panjang jika scraping lambat.

---

## 🏆 Atribusi

- Data diambil dari **[SKKNI Kemnaker](https://skkni.kemnaker.go.id)**.
- Proyek ini dibantu pengembangannya dengan **ChatGPT (OpenAI GPT-5)**.

> 💡 *"Dokumentasi yang baik adalah separuh dari software yang baik"* – dibuat dengan ❤️ dan bantuan ChatGPT.

---

## 📜 Lisensi

Proyek ini berlisensi **MIT** – bebas digunakan dan dimodifikasi.
