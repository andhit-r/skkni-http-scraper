# app/core/db.py
from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db import models


def _build_engine():
    url = settings.DATABASE_URL
    connect_args = {}
    # SQLite perlu connect_args khusus
    if url.startswith("sqlite:"):
        connect_args = {"check_same_thread": False}
    return create_engine(url, echo=False, future=True, connect_args=connect_args)


engine = _build_engine()

# Session factory
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    class_=Session,
    future=True,
)


def init_db() -> None:
    """Pastikan semua tabel ada."""
    models.Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency FastAPI: yield session, lalu tutup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Context manager biasa (dipakai oleh worker/skrip)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
