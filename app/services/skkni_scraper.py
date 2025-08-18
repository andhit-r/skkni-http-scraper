import re
from typing import cast

from bs4 import BeautifulSoup
import httpx

from app.core.config import settings

LIST_URL = settings.BASE_URL.rstrip("/") + "/dokumen"
API_DOC_URL = settings.API_BASE.rstrip("/") + "/v1/public/documents/{uuid}"


_uuid_re = re.compile(r"/documents/([0-9a-fA-F-]+)/download")


def _extract_uuid(href: str) -> str | None:
    m = _uuid_re.search(href or "")
    return m.group(1) if m else None


def scrape_document_listing(page_from: int, page_to: int, limit: int) -> list[dict]:
    """
    Scrape halaman listing dokumen SKKNI.
    Hasil mentah: hanya judul & unduh_url + uuid + listing_url.
    Detail (sektor/bidang/tahun/nomor) akan diisi di langkah enrich.
    """
    items: list[dict] = []
    with httpx.Client(timeout=30.0) as client:
        for page in range(page_from, page_to + 1):
            url = f"{LIST_URL}?limit={limit}&page={page}"
            resp = client.get(url)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            # heuristik: cari tautan unduh (href mengandung '/v1/public/documents/<uuid>/download')
            for a in soup.find_all("a", href=True):
                href = a["href"]
                uuid = _extract_uuid(href)
                if not uuid:
                    continue

                # naik ke parent card untuk ambil judul (heuristik, bisa berubah)
                title = None
                card = a.find_parent(["div", "article", "li"])
                if card:
                    # cari elemen text besar
                    h = card.find(["h1", "h2", "h3", "h4"])
                    if h and h.get_text(strip=True):
                        title = h.get_text(strip=True)
                if not title:
                    # fallback: text link
                    title = a.get_text(strip=True) or f"Dokumen {uuid}"

                items.append(
                    {
                        "uuid": uuid,
                        "judul_skkni": title,
                        "unduh_url": href if href.startswith("http") else settings.API_BASE.rstrip("/") + href,
                        "listing_url": url,
                    }
                )
    # de-dupe by uuid (ambil pertama)
    seen = set()
    deduped = []
    for it in items:
        if it["uuid"] in seen:
            continue
        seen.add(it["uuid"])
        deduped.append(it)
    return deduped


def enrich_documents_from_api(docs: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    Enrich setiap dokumen via API publik: /v1/public/documents/{uuid}
    Menghasilkan:
      - daftar dokumen lengkap (dengan sektor/bidang/tahun/nomor_kepmen)
      - daftar unit yang ditarik dari 'units' pada response API
    """
    full_docs: list[dict] = []
    units: list[dict] = []

    with httpx.Client(timeout=30.0) as client:
        for d in docs:
            uuid = d["uuid"]
            url = API_DOC_URL.format(uuid=uuid)
            r = client.get(url)
            if r.status_code != 200:
                # tetap push data minimal, biar tidak blank total
                full_docs.append(d | {"nomor_skkni": None, "tahun": None})
                continue

            js = r.json().get("data", {})

            # ambil taxonomy
            sektor = None
            bidang = None
            sub_bidang = None

            core = js.get("core_category") or {}
            cat = core.get("category") or {}
            if cat.get("name"):
                sektor = cat["name"]
            if core.get("name"):
                bidang = core["name"]

            # meta dokumen
            nomor_kepmen = js.get("number_kepmen")
            number = js.get("number")
            title = js.get("title") or d.get("judul_skkni")
            published_at = js.get("published_at") or js.get("created_at")
            # tahun dari nomor/ published_at (fallback sederhana)
            tahun = None
            if number:
                m = re.search(r"(\d{4})", str(number))
                if m:
                    tahun = m.group(1)
            if not tahun and published_at:
                m = re.search(r"(\d{4})", str(published_at))
                if m:
                    tahun = m.group(1)

            full_docs.append(
                {
                    "uuid": uuid,
                    "judul_skkni": title,
                    "nomor_skkni": f"Nomor {number} Tahun {tahun}" if number and tahun else (number or None),
                    "sektor": sektor,
                    "bidang": bidang,
                    "sub_bidang": sub_bidang,
                    "tahun": tahun,
                    "nomor_kepmen": nomor_kepmen,
                    "unduh_url": d.get("unduh_url"),
                    "listing_url": d.get("listing_url"),
                }
            )

            # units
            for u in js.get("units") or []:
                units.append(
                    {
                        "doc_uuid": uuid,
                        "kode_unit": u.get("code"),
                        "judul_unit": (u.get("title") or "").strip(),
                        "nomor_skkni": f"Nomor {number} Tahun {tahun}" if number and tahun else (number or None),
                        "sektor": sektor,
                        "bidang": bidang,
                        "sub_bidang": sub_bidang,
                        "tahun": tahun,
                        "nomor_kepmen": nomor_kepmen,
                        "unduh_url": d.get("unduh_url"),
                        "listing_url": cast(str, d.get("listing_url")).replace("/dokumen", "/dokumen-unit")
                        if d.get("listing_url")
                        else None,
                    }
                )

    return full_docs, units


def scrape_documents_and_units(page_from: int, page_to: int, limit: int) -> tuple[list[dict], list[dict]]:
    """
    Kombinasi: scrape listing -> enrich ke API -> return (docs, units)
    """
    base_docs = scrape_document_listing(page_from, page_to, limit)
    full_docs, units = enrich_documents_from_api(base_docs)
    return full_docs, units
