from contextlib import asynccontextmanager
from playwright.async_api import async_playwright
from app.core.config import settings
import os

def _candidate_executables() -> list[str]:
    # Urutan kandidat path chromium di Debian/Ubuntu
    cands = []
    env_path = os.getenv("CHROMIUM_PATH")
    if env_path:
        cands.append(env_path)
    # fallback umum
    cands += ["/usr/bin/chromium", "/usr/bin/chromium-browser", "/snap/bin/chromium"]
    # filter yang eksis
    return [p for p in cands if os.path.exists(p)]

@asynccontextmanager
async def chromium_page():
    """
    Membuka Playwright Chromium menggunakan:
    - executable_path -> Chromium sistem (jika tersedia)
    - fallback -> bundling Playwright (jika kebetulan image punya, tapi kita tidak mengandalkannya)
    """
    p = await async_playwright().start()
    launch_kwargs = {
        "headless": settings.HEADLESS,
        "args": [
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-setuid-sandbox",
        ],
    }

    # Pakai Chromium sistem bila ada
    exes = _candidate_executables()
    if exes:
        launch_kwargs["executable_path"] = exes[0]

    browser = await p.chromium.launch(**launch_kwargs)
    page = await browser.new_page()
    try:
        yield page
    finally:
        await browser.close()
        await p.stop()
