from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.routes import api_router

# Ambil origins dari settings kalau ada, fallback ke default lokal
try:
    from app.core.config import settings
    _origins_csv = getattr(settings, "ALLOWED_ORIGINS", "")
    ALLOWED_ORIGINS = [o.strip() for o in _origins_csv.split(",") if o.strip()] or [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5678",  # n8n default
    ]
except Exception:
    ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5678",
    ]

app = FastAPI(
    title="SKKNI HTTP Scraper",
    version="1.0.0",
    description="HTTP service untuk scraping & cache SKKNI",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Healthcheck (dipakai di test)
@app.get("/healthz", tags=["_internal"])
def healthz():
    return {"status": "ok"}

# MOUNT ROUTER V1 DI PREFIX /skkni
# -> hasil: /skkni/search-documents, /skkni/search-units, /skkni/sectors, dst.
app.include_router(api_router, prefix="/skkni")
