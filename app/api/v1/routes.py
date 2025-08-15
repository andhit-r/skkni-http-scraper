from fastapi import APIRouter
from app.api.v1.endpoints.skkni import router as skkni_router

# Router utama untuk v1
api_router = APIRouter()

# Mount semua endpoint SKKNI langsung di root router v1
# (path dasar endpoint-nya sudah seperti /search-documents, /search-units, dll)
api_router.include_router(skkni_router, prefix="", tags=["skkni"])
