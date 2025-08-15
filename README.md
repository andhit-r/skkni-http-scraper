# SKKNI HTTP Scraper

HTTP service (FastAPI) untuk scraping data SKKNI. Arsitektur mengikuti pola API/Core/Models/Repositories/Services/Utils.

## Run (local)
```bash
pip install -r requirements.txt
python -m playwright install
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Docker
```bash
docker build -t skkni-http-scraper:dev .
docker run --rm -p 8000:8000 -e API_KEY=dev skkni-http-scraper:dev
curl -H "x-api-key: dev" http://localhost:8000/health
```

## Endpoints
- `GET /` → info
- `GET /health` → health check
- `GET /skkni/search-units` → (stub) cari unit dari /dokumen-unit
- `GET /skkni/search-documents` → (stub) cari dokumen dari /dokumen
