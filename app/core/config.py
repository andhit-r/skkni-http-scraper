from pydantic import BaseSettings

class Settings(BaseSettings):
    BASE_URL: str = "https://skkni.kemnaker.go.id"
    TIMEOUT: int = 20
    DATABASE_URL: str = "sqlite:///./skkni_cache.db"
    HEADLESS: bool = True  # ← TAMBAHKAN INI (default: headless)

settings = Settings()
