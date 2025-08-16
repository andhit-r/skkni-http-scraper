from typing import List, Optional
from pydantic import BaseModel


class DocumentItem(BaseModel):
    uuid: str
    judul_skkni: str
    nomor_skkni: Optional[str] = None
    sektor: Optional[str] = None
    bidang: Optional[str] = None
    sub_bidang: Optional[str] = None
    tahun: Optional[str] = None
    nomor_kepmen: Optional[str] = None
    unduh_url: Optional[str] = None
    listing_url: Optional[str] = None
    updated_at: Optional[str] = None


class UnitItem(BaseModel):
    doc_uuid: str
    kode_unit: str
    judul_unit: str
    nomor_skkni: Optional[str] = None
    sektor: Optional[str] = None
    bidang: Optional[str] = None
    sub_bidang: Optional[str] = None
    tahun: Optional[str] = None
    nomor_kepmen: Optional[str] = None
    unduh_url: Optional[str] = None
    listing_url: Optional[str] = None
    updated_at: Optional[str] = None


class SearchDocumentsResponse(BaseModel):
    count: int
    items: List[DocumentItem]
    source: str  # "fresh" | "cache"


class SearchUnitsResponse(BaseModel):
    count: int
    items: List[UnitItem]
    source: str
