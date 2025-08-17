"""Parsing helpers & normalizers."""

import re

# --- String cleaners (untuk tampilan) ---


def norm(s: str) -> str:
    """
    Rapikan whitespace (termasuk newline) dan pertahankan case asli.
    Contoh: "ABC \n DEF " -> "ABC DEF"
    """
    return re.sub(r"\s+", " ", (s or "").strip())


def slug(s: str) -> str:
    """Slug alfanumerik lowercase (untuk ID)."""
    return re.sub(r"[^a-z0-9]+", "_", (s or "").lower()).strip("_")


# --- Join-key builders (selalu normalized lowercase) ---

STOPWORDS_NOMOR = (
    "skkni",
    "nomor",
    "no",
    "no.",
    "thn",
    "tahun",
    "kepmen",
    "keputusan",
    "menteri",
    "tenaga",
    "kerja",
    "kemnaker",
    "kementerian",
)

PHRASES_JUDUL = (
    "standar kompetensi kerja nasional indonesia",
    "standar kompetensi kerja",
    "skkni",
)


def build_join_key_nomor(nomor: str) -> str:
    """
    Normalisasi nomor SKKNI untuk join:
    - lowercase
    - hapus kata umum: nomor/no/thn/tahun/kepmen/...
    - hapus semua non-alnum
    """
    s = (nomor or "").lower()
    for w in STOPWORDS_NOMOR:
        s = s.replace(w, "")
    s = re.sub(r"[^\w]+", "", s)
    return s


def build_join_key_judul(judul: str) -> str:
    """
    Normalisasi judul SKKNI untuk join (buang frasa umum dan non-alnum).
    """
    s = (judul or "").lower()
    for p in PHRASES_JUDUL:
        s = s.replace(p, "")
    s = re.sub(r"[^\w]+", "", s)
    return s


def pdf_doc_key(url: str) -> str:
    """
    Ambil 'kunci PDF' dari unduh_url.
    Contoh:
    https://skkni-api.kemnaker.go.id/v1/public/documents/<UUID>/download
    -> ekstrak <UUID>
    """
    u = (url or "").strip()
    m = re.search(r"/documents/([^/]+)/download", u)
    if m:
        return m.group(1).lower()
    # fallback: pakai keseluruhan path huruf/angka saja
    return re.sub(r"[^a-z0-9]+", "", u.lower())


# --- Status cleaner & deterministic ID ---

STATUS_TOKENS = ("BERLAKU", "DICABUT", "DIUBAH", "TIDAK BERLAKU")


def strip_status_tokens(s: str) -> str:
    """
    Hilangkan embel-embel status di ujung/mid string seperti ' BERLAKU' dsb.
    Case-insensitive dan tetap mempertahankan case asli selain tokennya.
    """
    t = s or ""
    for tok in STATUS_TOKENS:
        # hilangkan varian " XXX" dan "-XXX"
        t = t.replace(f" {tok}", "").replace(f"-{tok}", "")
        t = re.sub(rf"\b{tok}\b", "", t, flags=re.IGNORECASE)
    return norm(t)


def make_unit_id(kode_unit: str = "", judul_unit: str = "", nomor_skkni: str = "") -> str:
    """
    Buat ID deterministik untuk unit (stabil dipakai di downstream, mis. Odoo XML ID).
    """
    base = "_".join([slug(kode_unit), slug(judul_unit), slug(nomor_skkni)]).strip("_")[:120]
    return f"__export__.skkni_unit_{base or 'row'}"
