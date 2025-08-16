# app/core/config.py
from __future__ import annotations

import json
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # .env didukung; abaikan key tak dikenal
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    BASE_URL: str = "https://skkni-api.kemnaker.go.id"
    DATABASE_URL: str = "sqlite:////data/skkni_cache.db"

    # Simpan sebagai STRING agar tidak diparse JSON oleh pydantic-settings.
    # Contoh yang diterima:
    #  - "*"                      (default)
    #  - "http://a:3000"         (single)
    #  - "http://a:3000,http://b" (koma)
    #  - JSON list: '["http://a","http://b"]'
    ALLOWED_ORIGINS: str = "*"

    CACHE_TTL_DAYS: int = 30
    HEADLESS: bool = True
    MAX_CONCURRENCY: int = 2

    # ---- helper ----
    def allowed_origins_list(self) -> List[str]:
        s = (self.ALLOWED_ORIGINS or "").strip()
        if not s or s == "*":
            return ["*"]

        # Jika JSON list valid -> pakai
        if s.startswith("["):
            try:
                arr = json.loads(s)
                if isinstance(arr, list):
                    return [str(x).strip() for x in arr if str(x).strip()]
            except Exception:
                pass

        # Fallback: split koma
        parts = [p.strip() for p in s.split(",") if p.strip()]
        return parts if parts else ["*"]


settings = Settings()
