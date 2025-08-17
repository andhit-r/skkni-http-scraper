from pydantic import BaseModel


class DocumentItem(BaseModel):
    uuid: str
    judul_skkni: str
    nomor_skkni: str | None = None
    sektor: str | None = None
    bidang: str | None = None
    sub_bidang: str | None = None
    tahun: str | None = None
    nomor_kepmen: str | None = None
    unduh_url: str | None = None
    listing_url: str | None = None
    updated_at: str | None = None


class UnitItem(BaseModel):
    doc_uuid: str
    kode_unit: str
    judul_unit: str
    nomor_skkni: str | None = None
    sektor: str | None = None
    bidang: str | None = None
    sub_bidang: str | None = None
    tahun: str | None = None
    nomor_kepmen: str | None = None
    unduh_url: str | None = None
    listing_url: str | None = None
    updated_at: str | None = None


class SearchDocumentsResponse(BaseModel):
    count: int
    items: list[DocumentItem]
    source: str  # "fresh" | "cache"


class SearchUnitsResponse(BaseModel):
    count: int
    items: list[UnitItem]
    source: str
