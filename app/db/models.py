# app/db/models.py
from __future__ import annotations

from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, UniqueConstraint, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Document(Base):
    __tablename__ = "documents"

    # UUID dokumen dari API Kemnaker
    uuid = Column(String, primary_key=True, index=True)

    # Metadata dasar
    judul_skkni = Column(Text, nullable=False)
    nomor_skkni = Column(String, nullable=True)

    # Catatan penting: biarkan nullable karena API sering mengembalikan null
    sektor = Column(String, nullable=True, index=True)
    bidang = Column(String, nullable=True, index=True)
    sub_bidang = Column(String, nullable=True, index=True)

    tahun = Column(String, nullable=True)
    nomor_kepmen = Column(String, nullable=True)

    # Link
    unduh_url = Column(Text, nullable=True)
    listing_url = Column(Text, nullable=True)

    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # relasi ke units
    units = relationship("Unit", back_populates="document", cascade="all, delete-orphan")


class Unit(Base):
    __tablename__ = "units"

    id = Column(Integer, primary_key=True, autoincrement=True)
    doc_uuid = Column(String, ForeignKey("documents.uuid"), index=True, nullable=False)

    kode_unit = Column(String, nullable=False, index=True)
    judul_unit = Column(Text, nullable=False)

    nomor_skkni = Column(String, nullable=True)
    sektor = Column(String, nullable=True, index=True)
    bidang = Column(String, nullable=True, index=True)
    sub_bidang = Column(String, nullable=True, index=True)

    tahun = Column(String, nullable=True)
    nomor_kepmen = Column(String, nullable=True)

    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    document = relationship("Document", back_populates="units")

    __table_args__ = (
        # Tiap dokumen bisa punya kode unit unik
        UniqueConstraint("doc_uuid", "kode_unit", name="uq_doc_unit_code"),
    )


class Sector(Base):
    __tablename__ = "sectors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False, index=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Bidang(Base):
    __tablename__ = "bidang"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False, index=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class SubBidang(Base):
    __tablename__ = "sub_bidang"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False, index=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
