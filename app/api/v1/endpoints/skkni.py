from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.db import crud

router = APIRouter(prefix="/skkni", tags=["skkni"])


@router.get("/search-documents")
def search_documents(
    page_from: int = Query(1, ge=1),
    page_to: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    q: str | None = None,
    sektor: str | None = None,
    bidang: str | None = None,
    tahun: str | None = None,
    force_refresh: bool = False,  # disimpan untuk kompatibilitas; saat ini baca dari cache/DB
    db: Session = Depends(get_db),
):
    """
    Saat ini endpoint membaca dari DB (cache). force_refresh diabaikan di v1 (sinkronisasi dilakukan via worker terpisah).
    """
    try:
        total, items = crud.get_documents(
            db=db,
            limit=limit,
            q=q,
            sektor=sektor,
            bidang=bidang,
            tahun=tahun,
        )
        return {"source": "cache", "count": total, "items": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"search-documents failed: {type(e).__name__}") from e


@router.get("/search-units")
def search_units(
    page_from: int = Query(1, ge=1),
    page_to: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    q: str | None = None,
    sektor: str | None = None,
    bidang: str | None = None,
    tahun: str | None = None,
    doc_uuid: str | None = None,
    force_refresh: bool = False,  # diabaikan, sinkronisasi via worker
    db: Session = Depends(get_db),
):
    """
    Baca units dari DB (hasil sinkronisasi worker). Jika tidak ada filter, tetap kembalikan data terbatas oleh 'limit'.
    """
    try:
        total, items = crud.get_units(
            db=db,
            limit=limit,
            q=q,
            sektor=sektor,
            bidang=bidang,
            tahun=tahun,
            doc_uuid=doc_uuid,
        )
        return {"source": "cache", "count": total, "items": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"search-units failed: {type(e).__name__}") from e


@router.get("/sectors")
def list_sectors(
    db: Session = Depends(get_db),
):
    try:
        rows = crud.get_distinct_sectors(db)
        return {"count": len(rows), "items": [{"name": name, "count": cnt} for name, cnt in rows]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"sectors failed: {type(e).__name__}") from e


@router.get("/bidang")
def list_bidang(
    db: Session = Depends(get_db),
):
    try:
        rows = crud.get_distinct_bidang(db)
        return {"count": len(rows), "items": [{"name": name, "count": cnt} for name, cnt in rows]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"bidang failed: {type(e).__name__}") from e


@router.get("/sub-bidang")
def list_sub_bidang(
    db: Session = Depends(get_db),
):
    try:
        rows = crud.get_distinct_sub_bidang(db)
        return {"count": len(rows), "items": [{"name": name, "count": cnt} for name, cnt in rows]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"sub-bidang failed: {type(e).__name__}") from e
