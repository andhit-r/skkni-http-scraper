from fastapi import APIRouter, Query, Depends
from typing import Optional
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.db import crud
from app.repositories.skkni_repository import SkkniRepository

router = APIRouter()
repo = SkkniRepository()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------- Search: Documents --------------------

@router.get("/search-documents")
async def search_documents(
    page_from: int = Query(1, ge=1),
    page_to: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    force_refresh: bool = Query(False),
    # NEW filters
    sector_id: Optional[int] = Query(None),
    field_id: Optional[int] = Query(None),
    subfield_id: Optional[int] = Query(None),
    q: Optional[str] = Query(None, description="Cari judul/nomor SKKNI"),
    db: Session = Depends(get_db),
):
    # Jika ada filter/q -> langsung query dari DB (tanpa scrape)
    if sector_id or field_id or subfield_id or q:
        rows = crud.search_documents_by_taxo(
            db,
            sector_id=sector_id,
            field_id=field_id,
            subfield_id=subfield_id,
            qtext=q,
            limit=limit,
            offset=0,
        )
        items = [_doc_to_dict_with_taxo(d, sektor, bidang, sub_bidang) for d, sektor, bidang, sub_bidang in rows]
        return {"count": len(items), "items": items, "source": "cache"}

    # Mode lama: cache-first lalu fallback fresh scrape
    cached = crud.get_documents_cached(db, limit=limit)
    if cached and not force_refresh and not any(crud.needs_refresh(d.updated_at) for d in cached):
        items = []
        for d, sektor, bidang, sub_bidang in crud.get_documents_cached_with_taxo(db, limit=limit):
            items.append(_doc_to_dict_with_taxo(d, sektor, bidang, sub_bidang))
        return {"count": len(items), "items": items, "source": "cache"}

    docs = await repo.fetch_documents(page_from=page_from, page_to=page_to, limit=limit)
    for d in docs:
        d.setdefault("__raw_json__", "")
    crud.upsert_documents(db, docs)
    db.commit()

    items = []
    for d, sektor, bidang, sub_bidang in crud.get_documents_cached_with_taxo(db, limit=limit):
        items.append(_doc_to_dict_with_taxo(d, sektor, bidang, sub_bidang))
    return {"count": len(items), "items": items, "source": "fresh"}


# -------------------- Search: Units --------------------

@router.get("/search-units")
async def search_units(
    include_merged: bool = Query(False),
    page_from: int = Query(1, ge=1),
    page_to: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    force_refresh: bool = Query(False),
    # NEW filters
    sector_id: Optional[int] = Query(None),
    field_id: Optional[int] = Query(None),
    subfield_id: Optional[int] = Query(None),
    q: Optional[str] = Query(None, description="Cari judul/kode unit/nomor SKKNI"),
    db: Session = Depends(get_db),
):
    # Jika ada filter/q -> langsung query DB
    if sector_id or field_id or subfield_id or q:
        rows = crud.search_units_by_taxo(
            db,
            sector_id=sector_id,
            field_id=field_id,
            subfield_id=subfield_id,
            qtext=q,
            limit=limit,
            offset=0,
        )
        items = [_unit_to_dict_with_taxo(u, sektor, bidang, sub_bidang) for u, sektor, bidang, sub_bidang in rows]
        return {"count": len(items), "items": items, "source": "cache"}

    # Mode lama: cache-first lalu fresh
    cached = crud.get_units_cached(db, limit=limit)
    if cached and not force_refresh and not any(crud.needs_refresh(u.updated_at) for u in cached):
        items = []
        for u, sektor, bidang, sub_bidang in crud.get_units_cached_with_taxo(db, limit=limit):
            items.append(_unit_to_dict_with_taxo(u, sektor, bidang, sub_bidang))
        return {"count": len(items), "items": items, "source": "cache"}

    units = await repo.fetch_units(page_from=page_from, page_to=page_to, limit=limit)
    crud.upsert_units(db, units)
    db.commit()

    items = []
    for u, sektor, bidang, sub_bidang in crud.get_units_cached_with_taxo(db, limit=limit):
        items.append(_unit_to_dict_with_taxo(u, sektor, bidang, sub_bidang))
    return {"count": len(items), "items": items, "source": "fresh"}


# -------------------- Taxonomy Browsing --------------------

@router.get("/sectors")
def list_sectors(
    q: Optional[str] = Query(None, description="Cari nama sektor (like)"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    rows = crud.list_sectors(db, q=q, limit=limit, offset=offset)
    return {"count": len(rows), "items": [{"id": r.id, "name": r.name, "code": r.code} for r in rows]}

@router.get("/sectors/{sector_id}/fields")
def list_fields(
    sector_id: int,
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    rows = crud.list_fields(db, sector_id=sector_id, limit=limit, offset=offset)
    return {"count": len(rows), "items": [{"id": r.id, "name": r.name, "code": r.code, "sector_id": r.sector_id} for r in rows]}

@router.get("/fields/{field_id}/sub-fields")
def list_sub_fields(
    field_id: int,
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    rows = crud.list_subfields(db, field_id=field_id, limit=limit, offset=offset)
    return {"count": len(rows), "items": [{"id": r.id, "name": r.name, "code": r.code, "field_id": r.field_id} for r in rows]}


# -------------------- Serializers --------------------

def _doc_to_dict_with_taxo(d, sektor, bidang, sub_bidang) -> dict:
    return {
        "uuid": d.uuid,
        "judul_skkni": d.judul_skkni,
        "nomor_skkni": d.nomor_skkni or None,
        "sektor": sektor,
        "bidang": bidang,
        "sub_bidang": sub_bidang,
        "tahun": d.tahun or None,
        "nomor_kepmen": d.nomor_kepmen or None,
        "unduh_url": d.unduh_url or None,
        "listing_url": d.listing_url or None,
        "updated_at": d.updated_at.isoformat(),
    }

def _unit_to_dict_with_taxo(u, sektor, bidang, sub_bidang) -> dict:
    return {
        "doc_uuid": u.doc_uuid,
        "kode_unit": u.kode_unit,
        "judul_unit": u.judul_unit or None,
        "nomor_skkni": u.nomor_skkni or None,
        "sektor": sektor,
        "bidang": bidang,
        "sub_bidang": sub_bidang,
        "tahun": u.tahun or None,
        "nomor_kepmen": u.nomor_kepmen or None,
        "unduh_url": u.unduh_url or None,
        "listing_url": u.listing_url or None,
        "updated_at": u.updated_at.isoformat(),
    }
