"""Jedna widoczna przeglądarka (Scrapling + Patchright, systemowy Chrome) z trwałym profilem."""

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from scrapling.fetchers import AsyncStealthySession

from giga_china_crawler import DATA_DIR

PROFILE = DATA_DIR / ".local/browser-profile"
CHALLENGE_WORDS = ("slide to verify", "drag the slider", "captcha", "przesuń", "weryfikacja", "unusual traffic")
HUMAN_WAIT_SECONDS = 300
_lock = asyncio.Lock()
_session: AsyncStealthySession | None = None


@asynccontextmanager
async def session():
    """Przeglądarka jest jedna, więc wyszukiwania idą po kolei."""
    global _session
    async with _lock:
        if _session is None:
            PROFILE.mkdir(parents=True, exist_ok=True, mode=0o700)
            # real_chrome: Chromium z Patchright potrafi paść przy starcie w profilu z MCP (stary projekt).
            _session = AsyncStealthySession(headless=False, real_chrome=True, user_data_dir=str(PROFILE),
                                            extra_flags=["--window-size=1280,900", "--disable-notifications"])
            await _session.start()
        yield _session


async def wait_for(page, selector: str, notify) -> bool:
    """Czeka na wyniki. Gdy serwis pokaże test na człowieka, uruchamia kaskadę solverów."""
    asked = False
    for _ in range(HUMAN_WAIT_SECONDS * 2):
        if await page.locator(selector).count():
            return True
        if not asked:
            body = (await page.locator("body").inner_text()).lower() if await page.locator("body").count() else ""
            title = (await page.title()).lower()
            if any(word in body or word in title for word in CHALLENGE_WORDS):
                notify("Serwis pokazał test na człowieka. Rozwiąż go w oknie przeglądarki.")
                await page.bring_to_front()
                asked = True
                from giga_china_crawler import captcha
                result = await captcha.solve(page, notify)
                status = result["status"] + (f" ({result['solver']})" if result["solver"] else "")
                notify(f"Kaskada CAPTCHA: {status}")
        await asyncio.sleep(0.5)
    return False
