from typing import List, Dict, Iterable, Tuple, Optional
from sqlalchemy import select, or_
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.db.models import (
    Document, Unit,
    Sector, Field, SubField,
    DocumentTaxonomy, UnitTaxonomy
)

CACHE_TTL_DAYS = 30

# ------------- Helpers -------------

def _uuid_from_unduh(unduh_url: str) -> str:
    import re
    m = re.search(r"/documents/([^/]+)/", unduh_url or "")
    return (m.group(1) if m else "").lower()

def needs_refresh(ts: datetime) -> bool:
    return (not ts) or ((datetime.utcnow() - ts) > timedelta(days=CACHE_TTL_DAYS))

def _norm_name(x: str | None) -> str:
    return (x or "").strip()

# ------------- Taxonomy upsert -------------

def get_or_create_sector(db: Session, name: str | None, code: str | None = None) -> Sector | None:
    name = _norm_name(name)
    if not name:
        return None
    q = select(Sector).where(Sector.name == name)
    obj = db.execute(q).scalar_one_or_none()
    if obj:
        return obj
    obj = Sector(name=name, code=code or None)
    db.add(obj)
    db.flush()
    return obj

def get_or_create_field(db: Session, sector: Sector | None, name: str | None, code: str | None = None) -> Field | None:
    name = _norm_name(name)
    if not sector or not name:
        return None
    q = select(Field).where(Field.sector_id == sector.id, Field.name == name)
    obj = db.execute(q).scalar_one_or_none()
    if obj:
        return obj
    obj = Field(sector_id=sector.id, name=name, code=code or None)
    db.add(obj)
    db.flush()
    return obj

def get_or_create_subfield(db: Session, field: Field | None, name: str | None, code: str | None = None) -> SubField | None:
    name = _norm_name(name)
    if not field or not name:
        return None
    q = select(SubField).where(SubField.field_id == field.id, SubField.name == name)
    obj = db.execute(q).scalar_one_or_none()
    if obj:
        return obj
    obj = SubField(field_id=field.id, name=name, code=code or None)
    db.add(obj)
    db.flush()
    return obj

def _link_document_taxonomy(db: Session, doc_uuid: str, sektor: str | None, bidang: str | None, sub_bidang: str | None):
    sector_obj = get_or_create_sector(db, sektor)
    field_obj = get_or_create_field(db, sector_obj, bidang) if bidang else None
    subfield_obj = get_or_create_subfield(db, field_obj, sub_bidang) if sub_bidang else None

    tx = db.get(DocumentTaxonomy, doc_uuid)
    if tx:
        tx.sector_id = sector_obj.id if sector_obj else None
        tx.field_id = field_obj.id if field_obj else None
        tx.subfield_id = subfield_obj.id if subfield_obj else None
    else:
        tx = DocumentTaxonomy(
            document_uuid=doc_uuid,
            sector_id=sector_obj.id if sector_obj else None,
            field_id=field_obj.id if field_obj else None,
            subfield_id=subfield_obj.id if subfield_obj else None,
        )
        db.add(tx)

def _link_unit_taxonomy(db: Session, unit_id: int, sektor: str | None, bidang: str | None, sub_bidang: str | None):
    sector_obj = get_or_create_sector(db, sektor)
    field_obj = get_or_create_field(db, sector_obj, bidang) if bidang else None
    subfield_obj = get_or_create_subfield(db, field_obj, sub_bidang) if sub_bidang else None

    tx = db.get(UnitTaxonomy, unit_id)
    if tx:
        tx.sector_id = sector_obj.id if sector_obj else None
        tx.field_id = field_obj.id if field_obj else None
        tx.subfield_id = subfield_obj.id if subfield_obj else None
    else:
        tx = UnitTaxonomy(
            unit_id=unit_id,
            sector_id=sector_obj.id if sector_obj else None,
            field_id=field_obj.id if field_obj else None,
            subfield_id=subfield_obj.id if subfield_obj else None,
        )
        db.add(tx)

# ------------- Upserts -------------

def upsert_documents(db: Session, docs: Iterable[Dict]) -> None:
    for d in docs:
        uuid = _uuid_from_unduh(d.get("unduh_url", "")) or d.get("uuid") or ""
        if not uuid:
            continue
        obj = db.get(Document, uuid)
        payload = {
            "uuid": uuid,
            "judul_skkni": d.get("judul_skkni", ""),
            "nomor_skkni": d.get("nomor_skkni", "") or "",
            "sektor": d.get("sektor", "") or "",
            "bidang": d.get("bidang", "") or "",
            "sub_bidang": d.get("sub_bidang", "") or "",
            "tahun": d.get("tahun", "") or "",
            "nomor_kepmen": d.get("nomor_kepmen", "") or "",
            "unduh_url": d.get("unduh_url", "") or "",
            "listing_url": d.get("listing_url", "") or "",
            "raw_json": d.get("__raw_json__", "") or "",
            "updated_at": datetime.utcnow(),
        }
        if obj:
            for k, v in payload.items():
                setattr(obj, k, v)
        else:
            obj = Document(**payload)
            db.add(obj)
            db.flush()

        _link_document_taxonomy(db, uuid, payload["sektor"], payload["bidang"], payload["sub_bidang"])

def upsert_units(db: Session, units: Iterable[Dict]) -> None:
    for u in units:
        uuid = _uuid_from_unduh(u.get("unduh_url", "")) or u.get("doc_uuid") or ""
        kode = (u.get("kode_unit") or u.get("kode") or "").strip()
        if not uuid or not kode:
            continue

        q = select(Unit).where(Unit.doc_uuid == uuid, Unit.kode_unit == kode)
        obj = db.execute(q).scalar_one_or_none()

        payload = {
            "doc_uuid": uuid,
            "kode_unit": kode,
            "judul_unit": u.get("judul_unit", "") or "",
            "nomor_skkni": u.get("nomor_skkni", "") or "",
            "sektor": u.get("sektor", "") or "",
            "bidang": u.get("bidang", "") or "",
            "sub_bidang": u.get("sub_bidang", "") or "",
            "tahun": u.get("tahun", "") or "",
            "nomor_kepmen": u.get("nomor_kepmen", "") or "",
            "unduh_url": u.get("unduh_url", "") or "",
            "listing_url": u.get("listing_url", "") or "",
            "updated_at": datetime.utcnow(),
        }

        if obj:
            for k, v in payload.items():
                setattr(obj, k, v)
            unit_id = obj.id
        else:
            obj = Unit(**payload)
            db.add(obj)
            db.flush()
            unit_id = obj.id

        _link_unit_taxonomy(db, unit_id, payload["sektor"], payload["bidang"], payload["sub_bidang"])

# ------------- Readers (cache-first with taxonomy names) -------------

def get_documents_cached(db: Session, limit: int, offset: int = 0) -> List[Document]:
    q = select(Document).order_by(Document.updated_at.desc()).offset(offset).limit(limit)
    return list(db.execute(q).scalars())

def get_units_cached(db: Session, limit: int, offset: int = 0) -> List[Unit]:
    q = select(Unit).order_by(Unit.updated_at.desc()).offset(offset).limit(limit)
    return list(db.execute(q).scalars())

def get_documents_cached_with_taxo(db: Session, limit: int, offset: int = 0):
    docs = get_documents_cached(db, limit=limit, offset=offset)
    out = []
    for d in docs:
        tx = db.get(DocumentTaxonomy, d.uuid)
        if tx:
            sektor = db.get(Sector, tx.sector_id).name if tx.sector_id else None
            bidang = db.get(Field, tx.field_id).name if tx.field_id else None
            subf  = db.get(SubField, tx.subfield_id).name if tx.subfield_id else None
        else:
            sektor = bidang = subf = None
        out.append((d, sektor or (d.sektor or None), bidang or (d.bidang or None), subf or (d.sub_bidang or None)))
    return out

def get_units_cached_with_taxo(db: Session, limit: int, offset: int = 0):
    units = get_units_cached(db, limit=limit, offset=offset)
    out = []
    for u in units:
        tx = db.get(UnitTaxonomy, u.id)
        if tx:
            sektor = db.get(Sector, tx.sector_id).name if tx.sector_id else None
            bidang = db.get(Field, tx.field_id).name if tx.field_id else None
            subf  = db.get(SubField, tx.subfield_id).name if tx.subfield_id else None
        else:
            sektor = bidang = subf = None
        out.append((u, sektor or (u.sektor or None), bidang or (u.bidang or None), subf or (u.sub_bidang or None)))
    return out

# ---------- Browsing taxonomy ----------

def list_sectors(db: Session, q: str | None = None, limit: int = 100, offset: int = 0) -> List[Sector]:
    query = select(Sector).order_by(Sector.name).offset(offset).limit(limit)
    if q:
        query = select(Sector).where(Sector.name.ilike(f"%{q}%")).order_by(Sector.name).offset(offset).limit(limit)
    return list(db.execute(query).scalars())

def list_fields(db: Session, sector_id: int, limit: int = 200, offset: int = 0) -> List[Field]:
    query = select(Field).where(Field.sector_id == sector_id).order_by(Field.name).offset(offset).limit(limit)
    return list(db.execute(query).scalars())

def list_subfields(db: Session, field_id: int, limit: int = 200, offset: int = 0) -> List[SubField]:
    query = select(SubField).where(SubField.field_id == field_id).order_by(SubField.name).offset(offset).limit(limit)
    return list(db.execute(query).scalars())

# ---------- SEARCH with taxonomy filters ----------

def search_documents_by_taxo(
    db: Session,
    sector_id: Optional[int] = None,
    field_id: Optional[int] = None,
    subfield_id: Optional[int] = None,
    qtext: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
):
    """
    Cari dokumen berdasarkan taxonomy id dan/atau teks (judul / nomor).
    Return list of (Document, sektor_name, bidang_name, sub_bidang_name).
    """
    stmt = (
        select(
            Document,
            Sector.name,
            Field.name,
            SubField.name,
        )
        .select_from(Document)
        .outerjoin(DocumentTaxonomy, DocumentTaxonomy.document_uuid == Document.uuid)
        .outerjoin(Sector, Sector.id == DocumentTaxonomy.sector_id)
        .outerjoin(Field, Field.id == DocumentTaxonomy.field_id)
        .outerjoin(SubField, SubField.id == DocumentTaxonomy.subfield_id)
    )

    if sector_id:
        stmt = stmt.where(DocumentTaxonomy.sector_id == sector_id)
    if field_id:
        stmt = stmt.where(DocumentTaxonomy.field_id == field_id)
    if subfield_id:
        stmt = stmt.where(DocumentTaxonomy.subfield_id == subfield_id)
    if qtext:
        like = f"%{qtext}%"
        stmt = stmt.where(or_(Document.judul_skkni.ilike(like), Document.nomor_skkni.ilike(like)))

    stmt = stmt.order_by(Document.updated_at.desc()).offset(offset).limit(limit)

    rows = db.execute(stmt).all()
    out = []
    for d, sektor, bidang, subf in rows:
        out.append((d, sektor or (d.sektor or None), bidang or (d.bidang or None), subf or (d.sub_bidang or None)))
    return out

def search_units_by_taxo(
    db: Session,
    sector_id: Optional[int] = None,
    field_id: Optional[int] = None,
    subfield_id: Optional[int] = None,
    qtext: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
):
    """
    Cari unit berdasarkan taxonomy id dan/atau teks (judul_unit / kode_unit / nomor_skkni).
    Return list of (Unit, sektor_name, bidang_name, sub_bidang_name).
    """
    stmt = (
        select(
            Unit,
            Sector.name,
            Field.name,
            SubField.name,
        )
        .select_from(Unit)
        .outerjoin(UnitTaxonomy, UnitTaxonomy.unit_id == Unit.id)
        .outerjoin(Sector, Sector.id == UnitTaxonomy.sector_id)
        .outerjoin(Field, Field.id == UnitTaxonomy.field_id)
        .outerjoin(SubField, SubField.id == UnitTaxonomy.subfield_id)
    )

    if sector_id:
        stmt = stmt.where(UnitTaxonomy.sector_id == sector_id)
    if field_id:
        stmt = stmt.where(UnitTaxonomy.field_id == field_id)
    if subfield_id:
        stmt = stmt.where(UnitTaxonomy.subfield_id == subfield_id)
    if qtext:
        like = f"%{qtext}%"
        stmt = stmt.where(
            or_(
                Unit.judul_unit.ilike(like),
                Unit.kode_unit.ilike(like),
                Unit.nomor_skkni.ilike(like),
            )
        )

    stmt = stmt.order_by(Unit.updated_at.desc()).offset(offset).limit(limit)

    rows = db.execute(stmt).all()
    out = []
    for u, sektor, bidang, subf in rows:
        out.append((u, sektor or (u.sektor or None), bidang or (u.bidang or None), subf or (u.sub_bidang or None)))
    return out
