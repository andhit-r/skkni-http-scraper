from fastapi import APIRouter, Depends
from app.api.deps import get_skkni_service
from app.models.skkni import SearchParams, UnitsResponse, DocumentsResponse
from app.services.skkni_service import SkkniService

router = APIRouter()

@router.get("/search-units", response_model=UnitsResponse, summary="Cari unit kompetensi dari /dokumen-unit")
async def search_units(
    params: SearchParams = Depends(),
    service: SkkniService = Depends(get_skkni_service),
):
    items = await service.search_units(params)
    return {"count": len(items), "items": items}

@router.get("/search-documents", response_model=DocumentsResponse, summary="Cari dokumen SKKNI dari /dokumen")
async def search_documents(
    params: SearchParams = Depends(),
    service: SkkniService = Depends(get_skkni_service),
):
    items = await service.search_documents(params)
    return {"count": len(items), "items": items}
