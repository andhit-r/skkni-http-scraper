import os

import pytest

# Set env before imports so Settings picks them up
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_unit.db")
os.environ.setdefault("HEADLESS", "true")
os.environ.setdefault("CACHE_TTL_DAYS", "30")
os.environ.setdefault("MAX_CONCURRENCY", "2")

from fastapi.testclient import TestClient

from app.core.db import Base, SessionLocal, engine

# Import after env is set
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    # fresh schema for tests
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def client():
    return TestClient(app)


@pytest.fixture()
def db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def mock_repo(monkeypatch):
    """
    Monkeypatch SkkniRepository methods used by endpoints to avoid real scraping.
    Returns canned data for documents and units.
    """
    from app.api.v1.endpoints import skkni as skkni_ep

    docs = [
        {
            "uuid": "e0d07068-3da5-4e1d-9c75-cc69e0f6b1ee",
            "judul_skkni": "SKKNI Industri Bahan Bangunan Dari Semen",
            "nomor_skkni": "Nomor 166 Tahun 2025",
            "sektor": "INDUSTRI PENGOLAHAN",
            "bidang": "INDUSTRI BARANG GALIAN BUKAN LOGAM",
            "sub_bidang": "",
            "tahun": "2025",
            "nomor_kepmen": "Nomor 166 Tahun 2025",
            "unduh_url": "https://skkni-api.kemnaker.go.id/v1/public/documents/e0d07068-3da5-4e1d-9c75-cc69e0f6b1ee/download",
            "listing_url": "https://skkni.kemnaker.go.id/dokumen?limit=5&page=1",
        },
        {
            "uuid": "0e99cd86-c937-46ad-9bb2-8b50b2be4d08",
            "judul_skkni": "SKKNI Perdagangan Barang Secara Eceran Melalui Pemesanan Online",
            "nomor_skkni": "Nomor 257 Tahun 2025",
            "sektor": "PERDAGANGAN BESAR DAN ECERAN; REPARASI DAN PERAWATAN MOBIL DAN SEPEDA MOTOR",
            "bidang": "PERDAGANGAN BESAR, BUKAN MOBIL DAN SEPEDA MOTOR",
            "sub_bidang": "",
            "tahun": "2025",
            "nomor_kepmen": "Nomor 257 Tahun 2025",
            "unduh_url": "https://skkni-api.kemnaker.go.id/v1/public/documents/0e99cd86-c937-46ad-9bb2-8b50b2be4d08/download",
            "listing_url": "https://skkni.kemnaker.go.id/dokumen?limit=5&page=1",
        },
    ]

    units = [
        {
            "doc_uuid": "0e99cd86-c937-46ad-9bb2-8b50b2be4d08",
            "kode_unit": "G.47PEI00.001.1",
            "judul_unit": "Melakukan Identifikasi terhadap Perilaku Konsumen",
            "nomor_skkni": "Nomor 257 Tahun 2025",
            "sektor": "PERDAGANGAN BESAR DAN ECERAN; REPARASI DAN PERAWATAN MOBIL DAN SEPEDA MOTOR",
            "bidang": "PERDAGANGAN BESAR, BUKAN MOBIL DAN SEPEDA MOTOR",
            "unduh_url": "https://skkni-api.kemnaker.go.id/v1/public/documents/0e99cd86-c937-46ad-9bb2-8b50b2be4d08/download",
            "listing_url": "https://skkni.kemnaker.go.id/dokumen-unit?limit=5&page=1",
        },
        {
            "doc_uuid": "0e99cd86-c937-46ad-9bb2-8b50b2be4d08",
            "kode_unit": "G.47PEI00.003.1",
            "judul_unit": "Menentukan Target Pasar",
            "nomor_skkni": "Nomor 257 Tahun 2025",
            "sektor": "PERDAGANGAN BESAR DAN ECERAN; REPARASI DAN PERAWATAN MOBIL DAN SEPEDA MOTOR",
            "bidang": "PERDAGANGAN BESAR, BUKAN MOBIL DAN SEPEDA MOTOR",
            "unduh_url": "https://skkni-api.kemnaker.go.id/v1/public/documents/0e99cd86-c937-46ad-9bb2-8b50b2be4d08/download",
            "listing_url": "https://skkni.kemnaker.go.id/dokumen-unit?limit=5&page=1",
        },
    ]

    async def fake_fetch_documents(*args, **kwargs):
        return docs

    async def fake_fetch_units(*args, **kwargs):
        return units

    monkeypatch.setattr(skkni_ep.repo, "fetch_documents", fake_fetch_documents)
    monkeypatch.setattr(skkni_ep.repo, "fetch_units", fake_fetch_units)

    return {"docs": docs, "units": units}
