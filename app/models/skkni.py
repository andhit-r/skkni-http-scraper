from pydantic import BaseModel, Field
from typing import Optional, List

class SearchParams(BaseModel):
    q: Optional[str] = Field(default=None, description="Cari di kode/judul unit")
    kode_unit: Optional[str] = None
    judul_unit: Optional[str] = None
    nomor_skkni: Optional[str] = None
    tahun: Optional[str] = None
    sektor: Optional[str] = None
    bidang: Optional[str] = None
    sub_bidang: Optional[str] = None
    page_from: int = 1
    page_to: int = 2
    limit: int = 100
    include_merged: bool = True

class UnitCompetency(BaseModel):
    id: Optional[str]
    kode_unit: Optional[str]
    kode: Optional[str]
    judul_unit: Optional[str]
    nomor_skkni: Optional[str]
    judul_skkni: Optional[str]
    sektor: Optional[str]
    bidang: Optional[str]
    sub_bidang: Optional[str]
    tahun: Optional[str]
    nomor_kepmen: Optional[str]
    unduh_url: Optional[str]
    listing_url: Optional[str]

class DocumentMetadata(BaseModel):
    id: Optional[str]
    nomor_skkni: Optional[str]
    judul_skkni: Optional[str]
    sektor: Optional[str]
    bidang: Optional[str]
    sub_bidang: Optional[str]
    tahun: Optional[str]
    nomor_kepmen: Optional[str]
    listing_url: Optional[str]

class UnitsResponse(BaseModel):
    count: int
    items: List[UnitCompetency] = []

class DocumentsResponse(BaseModel):
    count: int
    items: List[DocumentMetadata] = []
