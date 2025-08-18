# app/worker/sync.py
from __future__ import annotations

import os

from app.core.db import SessionLocal, init_db
from app.db import crud
from app.repositories.skkni_repository import (  # type: ignore[attr-defined]
    DEFAULT_SEED_UUIDS,
    fetch_documents_and_units_by_uuids,
)


def _read_seed_file(path: str) -> list[str]:
    if not path:
        return []
    if not os.path.exists(path):
        return []
    uuids: list[str] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            uuids.append(s)
    return uuids


def _read_seed_env() -> list[str]:
    raw = os.getenv("SEED_UUIDS", "").strip()
    if not raw:
        return []
    return [s.strip() for s in raw.split(",") if s.strip()]


def _unique_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def main() -> None:
    """
    Worker sekali jalan untuk mengisi DB lokal:
    1) Baca UUID dari ENV SEED_UUIDS (comma-separated) dan/atau file /data/seed_uuids.txt.
    2) Jika keduanya kosong, gunakan DEFAULT_SEED_UUIDS (5 UUID valid yang sudah kamu pakai).
    3) Ambil detail tiap dokumen + unit, lalu upsert ke DB.
    """
    seed_file_path = os.getenv("SEED_FILE", "/data/seed_uuids.txt")
    env_uuids = _read_seed_env()
    file_uuids = _read_seed_file(seed_file_path)

    combined = _unique_preserve_order(env_uuids + file_uuids)
    if not combined:
        combined = DEFAULT_SEED_UUIDS[:]

    print(f"[sync] total UUID yang akan diproses: {len(combined)}")

    # siapkan DB (buat tabel bila belum ada)
    init_db()
    db = SessionLocal()
    try:
        docs, units = fetch_documents_and_units_by_uuids(combined)

        print(f"[sync] dokumen siap upsert: {len(docs)}, unit siap upsert: {len(units)}")
        if docs:
            crud.upsert_documents(db, docs)
        if units:
            crud.upsert_units(db, units)

        print("[sync] selesai. Data tersimpan di DB.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
