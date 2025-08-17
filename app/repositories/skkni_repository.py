# app/repositories/skkni_repository.py
from __future__ import annotations

import logging
import re
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

BASE = settings.BASE_URL.rstrip("/")


# ---------- HTTP helpers ----------


def _client() -> httpx.Client:
    return httpx.Client(
        timeout=httpx.Timeout(20.0),
        headers={
            "Accept": "application/json, */*;q=0.1",
            "User-Agent": "skkni-http-scraper/1.0",
        },
        follow_redirects=True,
    )


def _json_or_raise(r: httpx.Response) -> Any:
    ctype = r.headers.get("content-type", "")
    if "application/json" in ctype:
        return r.json()
    snippet = r.text[:200].replace("\n", "")
    raise ValueError(f"Non-JSON response for {r.request.url}. content-type={ctype} body~200='{snippet}'")


# ---------- Normalizers ----------


def _safe_get(d: dict[str, Any], *keys: str, default: Any = "") -> Any:
    cur: Any = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def _extract_year(text: str) -> str:
    if not text:
        return ""
    m = re.search(r"(19|20)\d{2}", text)
    return m.group(0) if m else ""


def _pick(v: dict[str, Any], candidates: list[str], default: str = "") -> str:
    for k in candidates:
        if k in v and isinstance(v[k], str) and v[k].strip():
            return v[k]
    return default


def normalize_document(
    raw: dict[str, Any],
    listing_url: str | None = None,
    **_: Any,  # serap argumen tak terpakai agar backward-compatible
) -> dict[str, Any]:
    """
    Normalisasi detail dokumen.
    Kompatibel dengan panggilan lama: normalize_document(raw, listing_url).
    """
    uuid = _safe_get(raw, "uuid", default=_safe_get(raw, "id", default=""))
    judul = _safe_get(raw, "judul_skkni") or _safe_get(raw, "judul") or _safe_get(raw, "title") or ""
    nomor_skkni = _safe_get(raw, "nomor_skkni") or _safe_get(raw, "nomor") or _safe_get(raw, "number") or ""
    nomor_kepmen = _safe_get(raw, "nomor_kepmen", default=nomor_skkni)

    # Catatan: banyak payload detail tidak menyertakan taxonomy lengkap.
    sektor = _safe_get(raw, "sektor") or _safe_get(raw, "taxonomy", "sektor") or _safe_get(raw, "sector") or ""
    bidang = _safe_get(raw, "bidang") or _safe_get(raw, "taxonomy", "bidang") or _safe_get(raw, "field") or ""
    sub_bidang = (
        _safe_get(raw, "sub_bidang") or _safe_get(raw, "taxonomy", "sub_bidang") or _safe_get(raw, "subfield") or None
    )

    tahun = _safe_get(raw, "tahun") or _extract_year(nomor_skkni) or _extract_year(nomor_kepmen) or ""
    unduh_url = _safe_get(raw, "unduh_url") or _safe_get(raw, "download_url") or ""

    return {
        "uuid": uuid,
        "judul_skkni": judul,
        "nomor_skkni": nomor_skkni,
        "sektor": sektor,
        "bidang": bidang,
        "sub_bidang": sub_bidang,  # boleh None di DB
        "tahun": tahun,
        "nomor_kepmen": nomor_kepmen,
        "unduh_url": unduh_url,
        "listing_url": listing_url or _safe_get(raw, "listing_url", default=""),
    }


def normalize_units(doc_uuid: str, raw_units: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Konversi list unit mentah => {doc_uuid,kode_unit,judul_unit}.
    Kunci fleksibel: kode_unit/unitCode/code/kode dan judul_unit/nama/title/name.
    """
    items: list[dict[str, Any]] = []
    for u in raw_units:
        kode = _pick(u, ["kode_unit", "unitCode", "code", "kode"], default="")
        judul = _pick(u, ["judul_unit", "nama", "title", "name"], default="")
        if not kode and not judul:
            continue
        items.append({"doc_uuid": doc_uuid, "kode_unit": kode, "judul_unit": judul})
    return items


# ---------- Fetchers ----------


def fetch_document_detail(uuid: str) -> dict[str, Any]:
    """
    Ambil **RAW** detail dokumen (TIDAK dinormalisasi).
    Worker yang akan memanggil normalize_document(raw, listing_url=...).
    """
    url = f"{BASE}/v1/public/documents/{uuid}"
    with _client() as c:
        r = c.get(url)
        r.raise_for_status()
        raw = _json_or_raise(r)

    # Banyak API membungkus di "data"
    if isinstance(raw, dict) and "data" in raw and isinstance(raw["data"], dict):
        raw = raw["data"]

    if not isinstance(raw, dict):
        raise ValueError(f"Unexpected document payload for {uuid}: {type(raw)}")

    return raw  # <-- kembalikan RAW, bukan hasil normalize_document()


def _extract_list_from_payload(payload: Any, uuid: str, url: str) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("data", "items", "result", "rows"):
            v = payload.get(key)
            if isinstance(v, list):
                return v
        data = payload.get("data")
        if isinstance(data, dict):
            for key in ("items", "result", "rows"):
                v = data.get(key)
                if isinstance(v, list):
                    return v
    logger.warning("Unexpected units payload for %s: %s (url=%s)", uuid, type(payload), url)
    return []


def fetch_units_for_document(uuid: str) -> list[dict[str, Any]]:
    url = f"{BASE}/v1/public/documents/{uuid}/units?limit=1000"
    with _client() as c:
        r = c.get(url)
        r.raise_for_status()
        payload = _json_or_raise(r)

    units_raw = _extract_list_from_payload(payload, uuid, url)
    units = normalize_units(uuid, units_raw)
    logger.info("[repo] units %s: %d", uuid, len(units))
    return units
