"""Playwright helpers (init browser/context/page, navigation utilities)."""
from contextlib import asynccontextmanager
from typing import AsyncIterator
from playwright.async_api import async_playwright
from app.core.config import settings

@asynccontextmanager
async def chromium_page() -> AsyncIterator:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=settings.HEADLESS)
        context = await browser.new_context()
        page = await context.new_page()
        try:
            yield page
        finally:
            await context.close()
            await browser.close()
