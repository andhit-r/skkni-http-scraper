from app.models.skkni import DocumentMetadata, SearchParams, UnitCompetency  # type: ignore[attr-defined]
from app.repositories.skkni_repository import SkkniRepository  # type: ignore[attr-defined]
from app.utils.parsing import (
    build_join_key_judul,
    build_join_key_nomor,
    make_unit_id,
    pdf_doc_key,
)


class SkkniService:
    def __init__(self):
        self.repo = SkkniRepository()

    async def search_units(self, params: SearchParams) -> list[UnitCompetency]:
        # 1) ambil unit sesuai paging/filter dasar
        units = await self.repo.fetch_units(
            q=params.q,
            kode_unit=params.kode_unit,
            judul_unit=params.judul_unit,
            nomor_skkni=params.nomor_skkni,
            page_from=params.page_from,
            page_to=params.page_to,
            limit=params.limit,
        )

        # siapkan id walau tanpa merge
        for u in units:
            u["id"] = make_unit_id(u.get("kode_unit", ""), u.get("judul_unit", ""), u.get("nomor_skkni", ""))

        if not params.include_merged:
            return [UnitCompetency(**u) for u in units]

        # 2) ambil metadata dokumen (secukupnya)
        docs = await self.repo.fetch_documents(q=None, page_from=1, page_to=300, limit=100)

        # 3) index dokumen: PDF key (utama), nomor (sekunder), judul (fallback)
        idx_pdf, idx_nomor, idx_judul = {}, {}, {}
        for d in docs:
            pdfk = pdf_doc_key(d.get("unduh_url", ""))
            if pdfk and pdfk not in idx_pdf:
                idx_pdf[pdfk] = d
            jn = build_join_key_nomor(d.get("nomor_skkni", ""))
            if jn and jn not in idx_nomor:
                idx_nomor[jn] = d
            jj = build_join_key_judul(d.get("judul_skkni", ""))
            if jj and jj not in idx_judul:
                idx_judul[jj] = d

        merged: list[dict] = []
        for u in units:
            row = dict(u)

            # PRIORITAS 1: join via PDF key
            hit = idx_pdf.get(pdf_doc_key(u.get("unduh_url", "")))

            # PRIORITAS 2: via nomor
            if not hit:
                hit = idx_nomor.get(build_join_key_nomor(u.get("nomor_skkni", "")))

            # PRIORITAS 3: via judul
            if not hit:
                hit = idx_judul.get(build_join_key_judul(u.get("judul_skkni", "")))

            if hit:
                for k in ("sektor", "bidang", "sub_bidang", "tahun", "nomor_kepmen"):
                    val = row.get(k)
                    if not val:
                        row[k] = hit.get(k, "")

            merged.append(row)

        # 4) filter lanjutan (sektor/bidang/sub_bidang/tahun)
        def ok(x: dict) -> bool:
            if params.sektor and params.sektor.lower() not in (x.get("sektor", "").lower()):
                return False
            if params.bidang and params.bidang.lower() not in (x.get("bidang", "").lower()):
                return False
            if params.sub_bidang and params.sub_bidang.lower() not in (x.get("sub_bidang", "").lower()):
                return False
            if params.tahun and params.tahun.lower() not in (x.get("tahun", "").lower()):
                return False
            return True

        merged = [m for m in merged if ok(m)]
        return [UnitCompetency(**m) for m in merged]

    async def search_documents(self, params: SearchParams) -> list[DocumentMetadata]:
        docs = await self.repo.fetch_documents(
            q=params.q,
            page_from=params.page_from,
            page_to=params.page_to,
            limit=params.limit,
        )
        return [DocumentMetadata(**d) for d in docs]
