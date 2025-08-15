from sqlalchemy import (
    String, Integer, DateTime, Text, UniqueConstraint, ForeignKey
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.core.db import Base

# =======================
# Master Taxonomy Tables
# =======================

class Sector(Base):
    __tablename__ = "sectors"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    name: Mapped[str] = mapped_column(String(256), unique=True, index=True)

    fields: Mapped[list["Field"]] = relationship("Field", back_populates="sector", cascade="all, delete-orphan")

class Field(Base):
    __tablename__ = "fields"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sector_id: Mapped[int] = mapped_column(ForeignKey("sectors.id", ondelete="RESTRICT"), index=True)
    code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    name: Mapped[str] = mapped_column(String(256))

    sector: Mapped["Sector"] = relationship("Sector", back_populates="fields")
    sub_fields: Mapped[list["SubField"]] = relationship("SubField", back_populates="field", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("sector_id", "name", name="uq_field_sector_name"),
    )

class SubField(Base):
    __tablename__ = "sub_fields"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    field_id: Mapped[int] = mapped_column(ForeignKey("fields.id", ondelete="RESTRICT"), index=True)
    code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    name: Mapped[str] = mapped_column(String(256))

    field: Mapped["Field"] = relationship("Field", back_populates="sub_fields")

    __table_args__ = (
        UniqueConstraint("field_id", "name", name="uq_subfield_field_name"),
    )

# =======================
# Existing Entities
# =======================

class Document(Base):
    __tablename__ = "documents"
    uuid: Mapped[str] = mapped_column(String(64), primary_key=True)
    judul_skkni: Mapped[str] = mapped_column(Text)
    nomor_skkni: Mapped[str] = mapped_column(String(128), default="")
    # String snapshots (legacy, tetap dipertahankan)
    sektor: Mapped[str] = mapped_column(String(256), default="")
    bidang: Mapped[str] = mapped_column(String(256), default="")
    sub_bidang: Mapped[str] = mapped_column(String(256), default="")
    tahun: Mapped[str] = mapped_column(String(8), default="")
    nomor_kepmen: Mapped[str] = mapped_column(String(128), default="")
    unduh_url: Mapped[str] = mapped_column(Text, default="")
    listing_url: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    raw_json: Mapped[str] = mapped_column(Text, default="")  # optional

    taxonomy: Mapped["DocumentTaxonomy"] = relationship(
        "DocumentTaxonomy", back_populates="document", uselist=False, cascade="all, delete-orphan"
    )

class Unit(Base):
    __tablename__ = "units"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    doc_uuid: Mapped[str] = mapped_column(String(64), index=True)
    kode_unit: Mapped[str] = mapped_column(String(64), index=True)
    judul_unit: Mapped[str] = mapped_column(Text, default="")
    nomor_skkni: Mapped[str] = mapped_column(String(128), default="")
    # String snapshots (legacy, tetap dipertahankan)
    sektor: Mapped[str] = mapped_column(String(256), default="")
    bidang: Mapped[str] = mapped_column(String(256), default="")
    sub_bidang: Mapped[str] = mapped_column(String(256), default="")
    tahun: Mapped[str] = mapped_column(String(8), default="")
    nomor_kepmen: Mapped[str] = mapped_column(String(128), default="")
    unduh_url: Mapped[str] = mapped_column(Text, default="")
    listing_url: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    taxonomy: Mapped["UnitTaxonomy"] = relationship(
        "UnitTaxonomy", back_populates="unit", uselist=False, cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("doc_uuid", "kode_unit", name="uq_unit_doc_kode"),
    )

# =======================
# Link Tables (Associations)
# =======================

class DocumentTaxonomy(Base):
    __tablename__ = "document_taxonomies"
    document_uuid: Mapped[str] = mapped_column(
        ForeignKey("documents.uuid", ondelete="CASCADE"),
        primary_key=True
    )
    sector_id: Mapped[int | None] = mapped_column(ForeignKey("sectors.id", ondelete="RESTRICT"), nullable=True, index=True)
    field_id: Mapped[int | None] = mapped_column(ForeignKey("fields.id", ondelete="RESTRICT"), nullable=True, index=True)
    subfield_id: Mapped[int | None] = mapped_column(ForeignKey("sub_fields.id", ondelete="RESTRICT"), nullable=True, index=True)

    document: Mapped["Document"] = relationship("Document", back_populates="taxonomy")
    sector: Mapped["Sector"] = relationship("Sector")
    field: Mapped["Field"] = relationship("Field")
    subfield: Mapped["SubField"] = relationship("SubField")

class UnitTaxonomy(Base):
    __tablename__ = "unit_taxonomies"
    unit_id: Mapped[int] = mapped_column(
        ForeignKey("units.id", ondelete="CASCADE"),
        primary_key=True
    )
    sector_id: Mapped[int | None] = mapped_column(ForeignKey("sectors.id", ondelete="RESTRICT"), nullable=True, index=True)
    field_id: Mapped[int | None] = mapped_column(ForeignKey("fields.id", ondelete="RESTRICT"), nullable=True, index=True)
    subfield_id: Mapped[int | None] = mapped_column(ForeignKey("sub_fields.id", ondelete="RESTRICT"), nullable=True, index=True)

    unit: Mapped["Unit"] = relationship("Unit", back_populates="taxonomy")
    sector: Mapped["Sector"] = relationship("Sector")
    field: Mapped["Field"] = relationship("Field")
    subfield: Mapped["SubField"] = relationship("SubField")
