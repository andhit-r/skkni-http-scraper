from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable, List, Optional, Tuple

from sqlalchemy import func, select, or_, and_
from sqlalchemy.orm import Session

from app.db import models

# TTL cache hanya dipakai untuk logika lama (kalau masih ada)
CACHE_TTL_DAYS = 30


def is_expired(ts: Optional[datetime]) -> bool:
    return (not ts) or ((datetime.utcnow() - ts) > timedelta(days=CACHE_TTL_DAYS))


def _coerce_dt(val) -> Optional[datetime]:
    """
    Terima datetime/str/None → kembalikan datetime (atau None).
    - String yang didukung:
      * ISO 8601 (datetime.fromisoformat)
      * 'YYYY-MM-DD HH:MM:SS'
    """
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    if isinstance(val, str):
        # coba ISO 8601 dulu
        try:
            return datetime.fromisoformat(val)
        except Exception:
            pass
        # coba format 'YYYY-MM-DD HH:MM:SS'
        try:
            return datetime.strptime(val, "%Y-%m-%d %H:%M:%S")
        except Exception:
            pass
    # fallback: None (biar gak meledak)
    return None


# --------------------------
# Documents
# --------------------------

def upsert_documents(db: Session, docs: Iterable[dict]) -> None:
    """
    Upsert daftar dokumen ke tabel documents.
    Field wajib: uuid, judul_skkni, nomor_skkni, sektor, bidang, tahun, unduh_url, listing_url
    sub_bidang boleh None. updated_at akan di-coerce ke datetime jika string.
    """
    for d in docs:
        uuid = d["uuid"]
        obj: models.Document | None = db.get(models.Document, uuid)
        upd_at = _coerce_dt(d.get("updated_at"))

        if obj is None:
            obj = models.Document(
                uuid=uuid,
                judul_skkni=d.get("judul_skkni"),
                nomor_skkni=d.get("nomor_skkni"),
                sektor=d.get("sektor"),
                bidang=d.get("bidang"),
                sub_bidang=d.get("sub_bidang"),  # boleh None
                tahun=d.get("tahun"),
                nomor_kepmen=d.get("nomor_kepmen"),
                unduh_url=d.get("unduh_url"),
                listing_url=d.get("listing_url"),
                updated_at=upd_at,
            )
            db.add(obj)
        else:
            obj.judul_skkni = d.get("judul_skkni")
            obj.nomor_skkni = d.get("nomor_skkni")
            obj.sektor = d.get("sektor")
            obj.bidang = d.get("bidang")
            obj.sub_bidang = d.get("sub_bidang")
            obj.tahun = d.get("tahun")
            obj.nomor_kepmen = d.get("nomor_kepmen")
            obj.unduh_url = d.get("unduh_url")
            obj.listing_url = d.get("listing_url")
            obj.updated_at = upd_at
    db.commit()


def get_documents(
    db: Session,
    limit: int = 20,
    q: Optional[str] = None,
    sektor: Optional[str] = None,
    bidang: Optional[str] = None,
    tahun: Optional[str] = None,
) -> Tuple[int, List[dict]]:
    """
    Ambil dokumen dari DB dengan optional filter.
    """
    stmt = select(models.Document)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(
                models.Document.judul_skkni.ilike(like),
                models.Document.nomor_skkni.ilike(like),
                models.Document.sektor.ilike(like),
                models.Document.bidang.ilike(like),
                models.Document.sub_bidang.ilike(like),
            )
        )
    if sektor:
        stmt = stmt.where(models.Document.sektor == sektor)
    if bidang:
        stmt = stmt.where(models.Document.bidang == bidang)
    if tahun:
        stmt = stmt.where(models.Document.tahun == tahun)

    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.execute(stmt.order_by(models.Document.updated_at.desc().nullslast()).limit(limit)).scalars().all()

    items = []
    for r in rows:
        items.append(
            {
                "uuid": r.uuid,
                "judul_skkni": r.judul_skkni,
                "nomor_skkni": r.nomor_skkni,
                "sektor": r.sektor,
                "bidang": r.bidang,
                "sub_bidang": r.sub_bidang,
                "tahun": r.tahun,
                "nomor_kepmen": r.nomor_kepmen,
                "unduh_url": r.unduh_url,
                "listing_url": r.listing_url,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            }
        )
    return total or 0, items


# --------------------------
# Units
# --------------------------

def upsert_units(db: Session, units: Iterable[dict]) -> None:
    """
    Upsert daftar unit ke tabel units.
    Field wajib: doc_uuid, kode_unit, judul_unit
    Field tambahan (opsional): sektor, bidang, sub_bidang, nomor_skkni, tahun, updated_at
    """
    for u in units:
        key = (u["doc_uuid"], u["kode_unit"])
        obj: models.Unit | None = (
            db.execute(
                select(models.Unit).where(
                    and_(models.Unit.doc_uuid == key[0], models.Unit.kode_unit == key[1])
                )
            )
            .scalars()
            .first()
        )
        upd_at = _coerce_dt(u.get("updated_at"))

        if obj is None:
            obj = models.Unit(
                doc_uuid=u["doc_uuid"],
                kode_unit=u["kode_unit"],
                judul_unit=u.get("judul_unit"),
                sektor=u.get("sektor"),
                bidang=u.get("bidang"),
                sub_bidang=u.get("sub_bidang"),
                nomor_skkni=u.get("nomor_skkni"),
                tahun=u.get("tahun"),
                updated_at=upd_at,
            )
            db.add(obj)
        else:
            obj.judul_unit = u.get("judul_unit")
            obj.sektor = u.get("sektor")
            obj.bidang = u.get("bidang")
            obj.sub_bidang = u.get("sub_bidang")
            obj.nomor_skkni = u.get("nomor_skkni")
            obj.tahun = u.get("tahun")
            obj.updated_at = upd_at
    db.commit()


def get_units(
    db: Session,
    limit: int = 50,
    q: Optional[str] = None,
    sektor: Optional[str] = None,
    bidang: Optional[str] = None,
    tahun: Optional[str] = None,
    doc_uuid: Optional[str] = None,
) -> Tuple[int, List[dict]]:
    """
    Ambil units dari DB. Jika tanpa filter sekalipun, harus tetap return data (dibatasi 'limit').
    """
    stmt = select(models.Unit)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(
                models.Unit.judul_unit.ilike(like),
                models.Unit.kode_unit.ilike(like),
            )
        )
    if sektor:
        stmt = stmt.where(models.Unit.sektor == sektor)
    if bidang:
        stmt = stmt.where(models.Unit.bidang == bidang)
    if tahun:
        stmt = stmt.where(models.Unit.tahun == tahun)
    if doc_uuid:
        stmt = stmt.where(models.Unit.doc_uuid == doc_uuid)

    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.execute(stmt.order_by(models.Unit.updated_at.desc().nullslast()).limit(limit)).scalars().all()

    items = []
    for r in rows:
        items.append(
            {
                "doc_uuid": r.doc_uuid,
                "kode_unit": r.kode_unit,
                "judul_unit": r.judul_unit,
                "sektor": r.sektor,
                "bidang": r.bidang,
                "sub_bidang": r.sub_bidang,
                "nomor_skkni": r.nomor_skkni,
                "tahun": r.tahun,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            }
        )
    return total or 0, items


# --------------------------
# Taxonomy (distinct)
# --------------------------

def get_distinct_sectors(db: Session) -> List[Tuple[str, int]]:
    stmt = (
        select(models.Document.sektor, func.count(models.Document.uuid))
        .group_by(models.Document.sektor)
        .order_by(func.count(models.Document.uuid).desc())
    )
    return [(name, cnt) for name, cnt in db.execute(stmt).all() if name]


def get_distinct_bidang(db: Session) -> List[Tuple[str, int]]:
    stmt = (
        select(models.Document.bidang, func.count(models.Document.uuid))
        .group_by(models.Document.bidang)
        .order_by(func.count(models.Document.uuid).desc())
    )
    return [(name, cnt) for name, cnt in db.execute(stmt).all() if name]


def get_distinct_sub_bidang(db: Session) -> List[Tuple[str, int]]:
    # Banyak dokumen tidak punya sub_bidang → wajar hasil 0 jika memang tidak tersedia
    stmt = (
        select(models.Document.sub_bidang, func.count(models.Document.uuid))
        .where(models.Document.sub_bidang.is_not(None))
        .group_by(models.Document.sub_bidang)
        .order_by(func.count(models.Document.uuid).desc())
    )
    return [(name, cnt) for name, cnt in db.execute(stmt).all() if name]
