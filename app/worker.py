# app/worker.py
from __future__ import annotations

from datetime import UTC, datetime
import os

from app.core.db import get_session, init_db
from app.db import crud
from app.repositories.skkni_repository import (
    fetch_document_detail,
    fetch_units_for_document,
    normalize_document,
)


def read_seed_uuids() -> list[str]:
    """
    Baca daftar UUID dari SEED_FILE (satu UUID per baris).
    Default path: /data/seed_uuids.txt
    """
    seed_path = os.environ.get("SEED_FILE", "/data/seed_uuids.txt")
    uuids: list[str] = []
    if os.path.exists(seed_path):
        with open(seed_path, encoding="utf-8") as f:
            for line in f:
                s = line.strip()
                if s:
                    uuids.append(s)
    return uuids


def main() -> None:
    uuids = read_seed_uuids()
    print(f"[worker] total UUID yang akan diproses: {len(uuids)}")

    docs_payload: list[dict] = []
    units_payload: list[dict] = []

    for idx, uuid in enumerate(uuids, start=1):
        try:
            # Ambil detail mentah dari API Kemnaker.
            raw_detail = fetch_document_detail(uuid)

            # Normalisasi sekali di worker; listing_url kita kosongkan (tidak wajib).
            doc_row = normalize_document(raw_detail, listing_url="")

            # Guard: pastikan listing_url selalu string
            if not isinstance(doc_row.get("listing_url", ""), str):
                doc_row["listing_url"] = ""

            # updated_at harus timezone-aware datetime (menghindari DeprecationWarning)
            doc_row["updated_at"] = datetime.now(UTC)
            docs_payload.append(doc_row)

            # Ambil & normalisasi units; tambahkan updated_at timezone-aware
            ulist = fetch_units_for_document(uuid)
            for r in ulist:
                r["updated_at"] = datetime.now(UTC)
            units_payload.extend(ulist)

            print(f"[worker] {idx}/{len(uuids)} OK: {uuid} (units: {len(ulist)})")
        except Exception as e:
            print(f"[worker] {idx}/{len(uuids)} SKIP {uuid}: {e}")

    print(f"[worker] dokumen siap upsert: {len(docs_payload)}, unit siap upsert: {len(units_payload)}")

    # Init DB & upsert
    init_db()
    with get_session() as db:
        if docs_payload:
            crud.upsert_documents(db, docs_payload)
        if units_payload:
            crud.upsert_units(db, units_payload)

    print("[worker] upsert selesai.")


if __name__ == "__main__":
    main()
