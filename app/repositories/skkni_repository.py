"""Repository layer to interact with SKKNI site (scraping with Playwright & API)."""

from typing import List, Dict, Optional, Tuple
import re
import json

from app.core.config import settings
from app.utils.playwright_helper import chromium_page
from app.utils.parsing import norm, strip_status_tokens

BASE = settings.BASE_URL.rstrip("/")


# ----------------------------- UTIL UMUM -----------------------------

def _std_key(h: str) -> str:
    """Pemetaan header -> kunci standar dict."""
    m = {
        "kode unit": "kode_unit",
        "kode": "kode",
        "judul unit": "judul_unit",
        "judul": "judul",
        "judul skkni": "judul_skkni",
        "nomor skkni": "nomor_skkni",
        "keterangan": "keterangan",
        "unduh": "unduh_url",
        "status": "status",
        "sektor": "sektor",
        "bidang": "bidang",
        "sub-bidang": "sub_bidang",
        "sub bidang": "sub_bidang",
        "tahun": "tahun",
        "nomor kepmen": "nomor_kepmen",
        "no kepmen": "nomor_kepmen",
        "aksi": "aksi",
        "action": "aksi",
        "detail": "detail",
    }
    key = m.get(h.lower())
    if key:
        return key
    return re.sub(r"[^a-z0-9]+", "_", h.lower()).strip("_")


def _clean_placeholder(v: str) -> str:
    """Hilangkan placeholder seperti 'Pilih ...', '-'."""
    if not v:
        return ""
    vv = v.strip()
    if not vv or vv == "-" or vv.lower().startswith("pilih "):
        return ""
    return vv


def _uuid_from_unduh(unduh_url: str) -> str:
    m = re.search(r"/documents/([^/]+)/", unduh_url or "")
    return (m.group(1) if m else "").lower()


def _pick(d: Dict, *names: str) -> str:
    for n in names:
        v = d.get(n)
        if v is not None and str(v).strip():
            return norm(str(v))
    return ""


# ----------------------------- PLAYWRIGHT HELPERS -----------------------------

async def _goto_listing(page, url: str) -> None:
    last_err = None
    for _ in range(3):
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=settings.TIMEOUT * 1000)
            for _ in range(8):
                await page.mouse.wheel(0, 2200)
                await page.wait_for_timeout(150)
            await page.wait_for_load_state("networkidle", timeout=15_000)
            return
        except Exception as e:
            last_err = e
            await page.wait_for_timeout(600)
    if last_err:
        raise last_err


async def _extract_biggest_table(page):
    """Ambil tabel dengan jumlah baris terbesar (umumnya tabel utama)."""
    tables = page.locator("table")
    best = None
    best_rows = 0
    for i in range(await tables.count()):
        rc = await tables.nth(i).locator("tbody tr").count()
        if rc > best_rows:
            best = tables.nth(i)
            best_rows = rc
    if not best or best_rows == 0:
        return [], [], None

    ths = best.locator("thead tr th")
    if await ths.count() == 0:
        ths = best.locator("tr").first.locator("th, td")
    headers = [norm(await ths.nth(i).inner_text()) for i in range(await ths.count())]

    rows = []
    body = best.locator("tbody tr")
    for r in range(await body.count()):
        cells = body.nth(r).locator("td, th")
        row = [norm(await cells.nth(c).inner_text()) for c in range(await cells.count())]
        rows.append(row)

    return headers, rows, best


async def _text_or_selected(page, root_selector: str) -> str:
    """Ambil value dari elemen (select -> option selected; selain itu inner_text)."""
    el = page.locator(root_selector)
    if await el.count() == 0:
        return ""
    tag = (await el.first.evaluate("el => el.tagName")).lower()
    if tag == "select":
        opt = el.first.locator("option[selected]")
        if await opt.count() > 0:
            return norm(await opt.first.inner_text())
        try:
            val = await el.first.evaluate("el => el.value")
            if val:
                opt2 = el.first.locator(f"option[value='{val}']")
                if await opt2.count() > 0:
                    return norm(await opt2.first.inner_text())
        except Exception:
            pass
        # fallback pertama yang bukan placeholder
        all_opts = el.first.locator("option")
        for i in range(await all_opts.count()):
            txt = norm(await all_opts.nth(i).inner_text())
            if txt and not txt.lower().startswith("pilih "):
                return txt
        return ""
    return norm(await el.first.inner_text())


# ----------------------------- LISTING SCRAPER -----------------------------

async def _scrape_listing(index_path: str, page_from: int, page_to: int, limit: int, want_detail_link: bool = False) -> List[Dict]:
    """
    Scrape listing tabel per halaman (?limit=&page=) dan hasilkan list of dict.
    Jika want_detail_link=True, ambil juga href detail dari kolom judul/aksi (kalau ada).
    """
    out: List[Dict] = []
    base = f"{BASE}/{index_path.strip('/')}"
    async with chromium_page() as page:
        for pn in range(page_from, page_to + 1):
            url = f"{base}?limit={limit}&page={pn}"
            await _goto_listing(page, url)

            headers, rows, best = await _extract_biggest_table(page)
            if not rows:
                break

            keys = [_std_key(h) for h in headers]
            body = best.locator("tbody tr")

            for r_idx, row_values in enumerate(rows):
                d: Dict = {}
                cells = body.nth(r_idx).locator("td, th")
                C = await cells.count()

                # simpan href detail dari kolom 0 (judul) atau kolom 'aksi'
                detail_url = None
                if want_detail_link:
                    if C > 0:
                        a0 = cells.nth(0).locator("a[href]")
                        if await a0.count() > 0:
                            href = await a0.first.get_attribute("href")
                            if href:
                                detail_url = href if href.startswith("http") else BASE + href
                    if not detail_url and C > 0:
                        a_last = cells.nth(C - 1).locator("a[href]")
                        if await a_last.count() > 0:
                            href = await a_last.first.get_attribute("href")
                            if href:
                                detail_url = href if href.startswith("http") else BASE + href

                for c in range(min(C, len(keys))):
                    key = keys[c]
                    if key == "unduh_url":
                        a = cells.nth(c).locator("a[href]")
                        href = None
                        if await a.count() > 0:
                            href = await a.first.get_attribute("href")
                        if href and href.startswith("/"):
                            href = BASE + href
                        d[key] = norm(href or (row_values[c] if c < len(row_values) else ""))
                    else:
                        d[key] = norm(row_values[c] if c < len(row_values) else "")

                    # bersihkan placeholder di kolom target
                    if key in ("sektor", "bidang", "sub_bidang", "tahun", "nomor_kepmen"):
                        d[key] = _clean_placeholder(d[key])

                # Fallback: scan seluruh sel untuk link unduh dokumen
                if not d.get("unduh_url"):
                    try:
                        links = cells.locator("a[href*='/documents/'][href$='/download']")
                        if await links.count() > 0:
                            href = await links.first.get_attribute("href")
                            if href and href.startswith("/"):
                                href = BASE + href
                            if href:
                                d["unduh_url"] = norm(href)
                    except Exception:
                        pass

                d["listing_url"] = url
                if want_detail_link and detail_url:
                    d["detail_url"] = detail_url

                # normalisasi ringan pada unit/dokumen
                raw_kode = d.get("kode_unit") or d.get("kode") or ""
                raw_nomor = d.get("nomor_skkni") or ""
                if raw_kode:
                    d["kode_unit"] = strip_status_tokens(raw_kode)
                if raw_nomor:
                    d["nomor_skkni"] = strip_status_tokens(raw_nomor)

                out.append(d)
    return out


# ----------------------------- DETAIL ENRICHMENT -----------------------------

async def _extract_from_embedded_json(page) -> Dict[str, str]:
    """
    Cari metadata di <script> yang berisi JSON state (Next.js/Nuxt/SPA).
    Mengembalikan sektor/bidang/sub_bidang/tahun/nomor_kepmen jika ditemukan.
    """
    out = {"sektor": "", "bidang": "", "sub_bidang": "", "tahun": "", "nomor_kepmen": ""}

    scripts = page.locator("script")
    count = await scripts.count()
    if count == 0:
        return out

    def pick_any(d: Dict, keys: List[str]) -> str:
        for k in keys:
            if not isinstance(d, dict):
                continue
            v = d.get(k)
            if isinstance(v, str) and v.strip():
                return norm(v)
            if isinstance(v, dict):
                vv = v.get("name") or v.get("nama")
                if isinstance(vv, str) and vv.strip():
                    return norm(vv)
        return ""

    for i in range(count):
        try:
            txt = await scripts.nth(i).inner_text()
        except Exception:
            continue
        if not txt or len(txt) < 20:
            continue

        js_obj = None
        try:
            js_obj = json.loads(txt)
        except Exception:
            m = re.search(r"=\s*(\{.*\})\s*;?\s*$", txt, flags=re.DOTALL)
            if m:
                blob = m.group(1)
                try:
                    js_obj = json.loads(blob)
                except Exception:
                    pass

        if not isinstance(js_obj, dict):
            continue

        candidates = []
        if "__NEXT_DATA__" in js_obj and isinstance(js_obj["__NEXT_DATA__"], dict):
            root = js_obj["__NEXT_DATA__"].get("props", {}).get("pageProps", {})
            candidates.append(root)
        if "__NUXT__" in js_obj and isinstance(js_obj["__NUXT__"], dict):
            root = js_obj["__NUXT__"].get("state") or js_obj["__NUXT__"].get("data")
            if isinstance(root, (list, dict)):
                candidates.append(root)
        candidates.append(js_obj)

        found = {}

        def traverse(node):
            nonlocal found
            if isinstance(node, dict):
                if not found.get("sektor"):
                    found["sektor"] = pick_any(node, ["sektor", "sector", "sektor_name", "sector_name"])
                if not found.get("bidang"):
                    found["bidang"] = pick_any(node, ["bidang", "field", "bidang_name", "field_name"])
                if not found.get("sub_bidang"):
                    found["sub_bidang"] = pick_any(node, ["sub_bidang", "subField", "sub_field", "sub_bidang_name", "sub_field_name"])
                if not found.get("tahun"):
                    found["tahun"] = pick_any(node, ["tahun", "year"])
                if not found.get("nomor_kepmen"):
                    found["nomor_kepmen"] = pick_any(node, ["nomor_kepmen", "no_kepmen", "kepmen", "kepmen_number", "kepmenNumber"])
                for v in node.values():
                    traverse(v)
            elif isinstance(node, list):
                for v in node:
                    traverse(v)

        for cand in candidates:
            traverse(cand)
            if any(found.get(k) for k in ("sektor", "bidang", "sub_bidang", "tahun", "nomor_kepmen")):
                break

        for k in out.keys():
            if found.get(k) and not out.get(k):
                out[k] = found[k]

        if any(out.values()):
            break

    # bersihkan placeholder
    for k, v in list(out.items()):
        out[k] = _clean_placeholder(v)
    return out


async def _extract_detail_fields_from_page(page) -> Dict[str, str]:
    """
    Ekstrak Sektor, Bidang, Sub Bidang, Tahun, Nomor Kepmen dari halaman detail.
    Urutan:
      A) embedded JSON di <script>
      B) tabel th/td
      C) definition list dt/dd
      D) label/value di form/grid
    """
    # A) embedded JSON
    from_script = await _extract_from_embedded_json(page)
    out = {
        "sektor": from_script.get("sektor", ""),
        "bidang": from_script.get("bidang", ""),
        "sub_bidang": from_script.get("sub_bidang", ""),
        "tahun": from_script.get("tahun", ""),
        "nomor_kepmen": from_script.get("nomor_kepmen", ""),
    }
    if any(out.values()):
        return out

    # B) tabel th/td
    try:
        rows = page.locator("table tr")
        for i in range(await rows.count()):
            th = rows.nth(i).locator("th, td").first
            td = rows.nth(i).locator("td").last
            if await th.count() == 0 or await td.count() == 0:
                continue
            label = norm(await th.inner_text()).lower()
            value = norm(await td.inner_text())
            if "sektor" == label:
                out["sektor"] = _clean_placeholder(value)
            elif "bidang" == label and "sub" not in label:
                out["bidang"] = _clean_placeholder(value)
            elif "sub" in label and "bidang" in label:
                out["sub_bidang"] = _clean_placeholder(value)
            elif "tahun" == label:
                out["tahun"] = _clean_placeholder(value)
            elif "nomor kepmen" in label or "no kepmen" in label:
                out["nomor_kepmen"] = _clean_placeholder(value)
    except Exception:
        pass

    # C) definition list
    try:
        dts = page.locator("dl dt")
        for i in range(await dts.count()):
            dt = dts.nth(i)
            dd = dt.locator("xpath=following-sibling::dd[1]")
            if await dd.count() == 0:
                continue
            label = norm(await dt.inner_text()).lower()
            value = norm(await dd.first.inner_text())
            if "sektor" == label:
                out["sektor"] = out["sektor"] or _clean_placeholder(value)
            elif "bidang" == label and "sub" not in label:
                out["bidang"] = out["bidang"] or _clean_placeholder(value)
            elif "sub" in label and "bidang" in label:
                out["sub_bidang"] = out["sub_bidang"] or _clean_placeholder(value)
            elif "tahun" == label:
                out["tahun"] = out["tahun"] or _clean_placeholder(value)
            elif "nomor kepmen" in label or "no kepmen" in label:
                out["nomor_kepmen"] = out["nomor_kepmen"] or _clean_placeholder(value)
    except Exception:
        pass

    # D) form/grid
    async def pick_form(lbl: str) -> str:
        lab = page.locator(f"xpath=//label[normalize-space(text())='{lbl}']")
        if await lab.count() == 0:
            lab = page.locator(f"xpath=//*[normalize-space(text())='{lbl}']")
            if await lab.count() == 0:
                return ""
        node = lab.first
        for sel in ("xpath=following::*[self::select or self::input or self::div][1]",
                    "xpath=parent::*/following-sibling::*[self::select or self::input or self::div][1]"):
            try:
                cand = node.locator(sel)
                if await cand.count() > 0:
                    v = await _text_or_selected(page, cand._selector)
                    return _clean_placeholder(v)
            except Exception:
                continue
        return ""

    for key, label in [
        ("sektor", "Sektor"),
        ("bidang", "Bidang"),
        ("sub_bidang", "Sub Bidang"),
        ("tahun", "Tahun"),
        ("nomor_kepmen", "Nomor Kepmen"),
    ]:
        if not out[key]:
            val = await pick_form(label)
            if val:
                out[key] = val

    return out


async def _api_fetch_doc_fields(page, uuid: str) -> Dict[str, str]:
    """
    Ambil detail dokumen dari API publik berdasarkan UUID.
    - Tidak memakai /taxonomy (404 HTML).
    - Support wrapper 'data'.
    - Mapping:
        sektor  <- core_category.category.name (DIVISION)
        bidang  <- core_category.name (GROUP)
        sub_bidang <- core_category.class/subclass/name jika ada
        nomor_kepmen <- number_kepmen atau variasinya
        tahun  <- 'year' atau regex dari nomor_kepmen / nomor_skkni / published_at
    """
    if not uuid:
        return {}

    candidates = [
        f"https://skkni-api.kemnaker.go.id/v1/public/documents/{uuid}",
        f"https://skkni-api.kemnaker.go.id/v1/public/documents/{uuid}/meta",
        f"https://skkni-api.kemnaker.go.id/v1/public/documents/{uuid}?include=sector,field,sub_field",
    ]

    merged: Dict = {}
    for url in candidates:
        try:
            resp = await page.request.get(url, timeout=settings.TIMEOUT * 1000)
            ct = (resp.headers.get("content-type") or "").lower()
            if not resp.ok or "application/json" not in ct:
                continue
            js = await resp.json()
            if isinstance(js, list) and js:
                js = js[0]
            if isinstance(js, dict):
                core = js.get("data", js)
                for k, v in core.items():
                    if k not in merged:
                        merged[k] = v
        except Exception:
            continue

    if not merged:
        return {}

    def normtxt(x) -> str:
        if isinstance(x, str):
            return norm(x)
        if isinstance(x, (int, float)):
            return norm(str(x))
        if isinstance(x, dict):
            for kk in ("name", "nama", "label", "title"):
                if isinstance(x.get(kk), (str, int, float)) and str(x.get(kk)).strip():
                    return norm(str(x.get(kk)))
        return ""

    sektor = ""
    bidang = ""
    sub_bidang = ""

    try:
        cc = merged.get("core_category") or {}
        sektor = sektor or normtxt((cc.get("category") or {}).get("name"))
        bidang = bidang or normtxt(cc.get("name"))
        cls = cc.get("class") or cc.get("klass") or cc.get("subclass") or {}
        if isinstance(cls, dict):
            sub_bidang = sub_bidang or normtxt(cls.get("name"))
        elif isinstance(cls, str):
            sub_bidang = sub_bidang or normtxt(cls)
    except Exception:
        pass

    # deep scan untuk variasi lain
    want = {
        "sektor":     ["sektor", "sector", "sector_name", "sektor_name", "kategori", "category", "industry_division", "division"],
        "bidang":     ["bidang", "field", "field_name", "bidang_name", "industry_group", "group", "golongan"],
        "sub_bidang": ["sub_bidang", "subField", "sub_field", "sub_bidang_name", "sub_field_name", "industry_class", "class", "subkategori", "subcategory", "sub_golongan"],
        "tahun":      ["tahun", "year", "published_year", "issued_year", "tahun_penetapan", "tahun_terbit"],
        "nomor_kepmen": ["number_kepmen", "nomor_kepmen", "no_kepmen", "kepmen", "kepmen_number", "kepmenNumber", "decision_number"],
        "nomor_skkni": ["nomor_skkni", "no_skkni", "skkni_number", "number_skkni", "number"],
        "published_at": ["published_at"],
    }
    found = {k: "" for k in want}

    def match_key(k: str, targets: list) -> bool:
        kl = (k or "").lower()
        return any(kl == t.lower() or t.lower() in kl for t in targets)

    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                for cat, keys in want.items():
                    if not found[cat] and match_key(k, keys):
                        txt = normtxt(v)
                        if not txt and isinstance(v, (list, dict)):
                            if isinstance(v, dict):
                                txt = normtxt(v)
                            elif isinstance(v, list) and v:
                                txt = normtxt(v[0])
                        if txt and not txt.lower().startswith("pilih "):
                            found[cat] = txt
                walk(v)
        elif isinstance(node, list):
            for it in node:
                walk(it)

    walk(merged)

    sektor = sektor or found["sektor"]
    bidang = bidang or found["bidang"]
    sub_bidang = sub_bidang or found["sub_bidang"]
    nomor_kep = found["nomor_kepmen"]
    nomor_skkni = found["nomor_skkni"]
    published_at = found["published_at"]

    # derive tahun
    import re as _re
    def extract_year(*texts: str) -> str:
        for t in texts:
            if not t:
                continue
            m = _re.search(r"(?:tahun|year)\s*(\d{4})", t, flags=_re.IGNORECASE)
            if m:
                return m.group(1)
            m2 = _re.findall(r"(\d{4})", t)
            if m2:
                for y in reversed(m2):
                    try:
                        if 1990 <= int(y) <= 2100:
                            return y
                    except Exception:
                        continue
        return ""

    tahun = found["tahun"] or extract_year(nomor_kep, nomor_skkni, published_at)
    if not nomor_kep and nomor_skkni:
        nomor_kep = nomor_skkni

    def clean(v: str) -> str:
        return _clean_placeholder(v)

    return {
        "sektor": clean(sektor),
        "bidang": clean(bidang),
        "sub_bidang": clean(sub_bidang),
        "tahun": clean(tahun),
        "nomor_kepmen": clean(nomor_kep),
    }


# ----------------------------- KANDIDAT DETAIL URL -----------------------------

def _candidate_detail_urls(uuid: str, nomor_skkni: str, judul: str) -> List[str]:
    """Buat kemungkinan URL halaman detail di situs utama."""
    cands = []
    if uuid:
        cands += [
            f"{BASE}/dokumen/{uuid}",
            f"{BASE}/dokumen?uuid={uuid}",
            f"{BASE}/dokumen-detail/{uuid}",
        ]

    def _slug(s: str) -> str:
        return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")

    if nomor_skkni:
        cands += [f"{BASE}/dokumen/{_slug(nomor_skkni)}"]
    if judul:
        cands += [f"{BASE}/dokumen/{_slug(judul)}"]

    # unik
    seen = set()
    out = []
    for u in cands:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


async def _enrich_documents_with_detail(docs: List[Dict]) -> List[Dict]:
    """
    Lengkapi dokumen yang belum punya sektor/bidang/sub_bidang/tahun/nomor_kepmen.
    Urutan:
      1) API berdasarkan UUID dari unduh_url
      2) Jika masih kosong & ada detail_url → embedded JSON / DOM detail
      3) Jika masih kosong & tidak ada detail_url → coba kandidat URL terkontruksi
    Dibatasi agar ringan saat uji awal (MAX_DETAIL).
    """
    targets = [d for d in docs if not any(d.get(k) for k in ("sektor", "bidang", "sub_bidang", "tahun", "nomor_kepmen"))]
    if not targets:
        return docs

    MAX_DETAIL = 10  # naikkan setelah stabil
    targets = targets[:MAX_DETAIL]

    async with chromium_page() as page:
        for d in targets:
            uuid = _uuid_from_unduh(d.get("unduh_url", ""))

            # 1) API by UUID
            if uuid:
                fields = await _api_fetch_doc_fields(page, uuid)
                for k, v in fields.items():
                    if v and not d.get(k):
                        d[k] = v

            # 2) Halaman detail (jika ada link)
            if not any(d.get(k) for k in ("sektor", "bidang", "sub_bidang", "tahun", "nomor_kepmen")) and d.get("detail_url"):
                try:
                    await _goto_listing(page, d["detail_url"])
                    fields2 = await _extract_detail_fields_from_page(page)
                    for k, v in fields2.items():
                        if v and not d.get(k):
                            d[k] = v
                except Exception:
                    pass

            # 3) Kandidat URL (UUID/slug) jika masih kosong
            if not any(d.get(k) for k in ("sektor", "bidang", "sub_bidang", "tahun", "nomor_kepmen")):
                for cand in _candidate_detail_urls(uuid, d.get("nomor_skkni", ""), d.get("judul_skkni", "")):
                    try:
                        await _goto_listing(page, cand)
                        fields3 = await _extract_detail_fields_from_page(page)
                        for k, v in fields3.items():
                            if v and not d.get(k):
                                d[k] = v
                        if any(d.get(k) for k in ("sektor", "bidang", "sub_bidang", "tahun", "nomor_kepmen")):
                            break
                    except Exception:
                        continue

    return docs


# ----------------------------- REPOSITORY PUBLIK -----------------------------

class SkkniRepository:
    """Fasad repository untuk operasi SKKNI."""

    async def fetch_documents(self, page_from: int = 1, page_to: int = 1, limit: int = 20) -> List[Dict]:
        """
        Ambil metadata dokumen dari listing /dokumen lalu enrich via API/Detail.
        """
        docs = await _scrape_listing(
            index_path="dokumen",
            page_from=page_from,
            page_to=page_to,
            limit=limit,
            want_detail_link=True,
        )

        # normalisasi nama kolom umum untuk dokumen
        normed: List[Dict] = []
        for d in docs:
            item = {
                "uuid": _uuid_from_unduh(d.get("unduh_url", "")) or "",
                "judul_skkni": d.get("judul_skkni") or d.get("judul") or "",
                "nomor_skkni": d.get("nomor_skkni") or "",
                "sektor": d.get("sektor") or "",
                "bidang": d.get("bidang") or "",
                "sub_bidang": d.get("sub_bidang") or "",
                "tahun": d.get("tahun") or "",
                "nomor_kepmen": d.get("nomor_kepmen") or "",
                "unduh_url": d.get("unduh_url") or "",
                "listing_url": d.get("listing_url") or "",
                "detail_url": d.get("detail_url") or "",
            }
            # strip placeholder
            for k in ("sektor", "bidang", "sub_bidang", "tahun", "nomor_kepmen"):
                item[k] = _clean_placeholder(item[k])
            normed.append(item)

        # enrich
        normed = await _enrich_documents_with_detail(normed)
        return normed

    async def fetch_units(self, page_from: int = 1, page_to: int = 1, limit: int = 20) -> List[Dict]:
        """
        Ambil listing unit kompetensi dari /dokumen-unit.
        Kemudian, map metadata dari dokumen via API berdasarkan UUID di unduh_url.
        """
        units = await _scrape_listing(
            index_path="dokumen-unit",
            page_from=page_from,
            page_to=page_to,
            limit=limit,
            want_detail_link=False,
        )

        # normalisasi
        normed: List[Dict] = []
        for u in units:
            item = {
                "id": u.get("id") or None,
                "kode_unit": (u.get("kode_unit") or u.get("kode") or "").strip(),
                "kode": u.get("kode") or None,
                "judul_unit": u.get("judul_unit") or u.get("judul") or "",
                "nomor_skkni": u.get("nomor_skkni") or "",
                "judul_skkni": u.get("judul_skkni") or "",
                "sektor": u.get("sektor") or "",
                "bidang": u.get("bidang") or "",
                "sub_bidang": u.get("sub_bidang") or "",
                "tahun": u.get("tahun") or "",
                "nomor_kepmen": u.get("nomor_kepmen") or "",
                "unduh_url": u.get("unduh_url") or "",
                "listing_url": u.get("listing_url") or "",
            }
            # strip status tokens & placeholder
            if item["kode_unit"]:
                item["kode_unit"] = strip_status_tokens(item["kode_unit"])
            for k in ("sektor", "bidang", "sub_bidang", "tahun", "nomor_kepmen"):
                item[k] = _clean_placeholder(item[k])
            normed.append(item)

        # Enrich per unit dari API dokumen (pakai UUID dari unduh_url)
        async with chromium_page() as page:
            for it in normed:
                uuid = _uuid_from_unduh(it.get("unduh_url", ""))
                if not uuid:
                    continue
                fields = await _api_fetch_doc_fields(page, uuid)
                for k in ("sektor", "bidang", "sub_bidang", "tahun", "nomor_kepmen"):
                    if (not it.get(k)) and fields.get(k):
                        it[k] = fields[k]

        return normed
