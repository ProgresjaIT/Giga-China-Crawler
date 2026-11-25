"""Kaskada solverów CAPTCHA: klasyfikacja, kolejka z rankingu, próby po kolei."""

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from giga_china_crawler.browser import CHALLENGE_WORDS
from giga_china_crawler.solvers import ADAPTERS

ALL_TYPES = ("ocr", "slider", "token", "behaviour")
SOLVERS = (
    {"name": "profile", "types": ALL_TYPES, "env": None},
    {"name": "alibaba-slider", "types": ("slider",), "env": None},
    {"name": "ddddocr", "types": ("ocr", "slider"), "env": None},
    {"name": "geetest-solver", "types": ("slider",), "env": None},
    {"name": "cf-solver", "types": ALL_TYPES, "env": "CF_SOLVER_URL"},
    {"name": "cipher-solver", "types": ("token", "behaviour"), "env": "CIPHER_SOLVER_URL"},
    {"name": "nopecha", "types": ("token", "slider"), "env": "NOPECHA_API_KEY"},
    {"name": "extension-solver", "types": ("token", "ocr"), "env": "EXTENSION_SOLVER_URL"},
    {"name": "2captcha", "types": ("ocr", "slider", "token"), "env": "TWO_CAPTCHA_API_KEY"},
    {"name": "human", "types": ALL_TYPES, "env": None},
)
SKILL = "captcha-cascade"
REPOS = {
    "profile": "Giga-China-Crawler/.local/browser-profile",
    "alibaba-slider": "MCP_Alibaba/src/alibaba_mcp/browser/actions.py",
    "ddddocr": "sml2h3/ddddocr",
    "geetest-solver": "Evil-Bane/Geetest-Solver",
    "cf-solver": "VeyraAgent/cf-solver",
    "cipher-solver": "cipher-x-sudo/captcha-solver",
    "nopecha": "NopeCHALLC/nopecha-python",
    "extension-solver": "icemellow-me/captcha-solver-extension",
    "2captcha": "2captcha/2captcha-python",
    "human": "człowiek",
}
SITEKEY = re.compile(r'(?:data-sitekey|sitekey)["\']?\s*[:=]\s*["\']([^"\']+)', re.I)
LOG_PATH = Path("logs/captcha_wyniki.json")


def record(found: dict, result: dict) -> None:
    """Jeden wpis na parę URL + typ challenge'u; kolejne użycia aktualizują wpis."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        entries = json.loads(LOG_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        entries = []
    now = datetime.now(timezone.utc).isoformat()
    detail = result["attempts"][-1]["detail"] if result["attempts"] else None
    solver = result["solver"]
    fields = {"skill": SKILL, "solver": solver, "repo": REPOS.get(solver) if solver else None,
              "success": result["status"] == "solved", "status": result["status"],
              "sitekey": found["sitekey"], "detail": detail,
              "attempted": list(dict.fromkeys(a["solver"] for a in result["attempts"])),
               "attempted_repos": list(dict.fromkeys(REPOS.get(a["solver"], a["solver"])
                                                     for a in result["attempts"])),
               "attempt_log": [{"solver": a["solver"], "detail": a.get("detail"), "solved": a.get("solved")}
                               for a in result["attempts"]],
               "last_seen": now}

    for entry in entries:
        if entry.get("url") == found["url"] and entry.get("type") == found["type"]:
            entry.update(fields)
            entry["count"] = entry.get("count", 1) + 1
            break
    else:
        entries.append({"url": found["url"], "type": found["type"], **fields,
                        "first_seen": now, "count": 1})
    LOG_PATH.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def candidates(kind: str, env: dict | None = None) -> list[dict]:
    """Solverzy dla typu challenge'u: lokalni, skonfigurowani, reszta, człowiek."""
    env = os.environ if env is None else env
    matches = [s for s in SOLVERS if kind in s["types"]]

    def rank(spec):
        name = spec["name"]
        if name == "profile":
            return (0, 0)
        if name == "human":
            return (3, 0)
        configured = spec["env"] is None or bool(env.get(spec["env"]))
        return (1 if configured else 2, SOLVERS.index(spec))

    return sorted(matches, key=rank)


async def classify(page) -> dict:
    """Typ challenge'u i dowód z DOM: sitekey, iframe, słowa na stronie."""
    html = await page.content()
    body = (await page.locator("body").inner_text()).lower() if await page.locator("body").count() else ""
    title = (await page.title()).lower()
    words = [word for word in CHALLENGE_WORDS if word in body or word in title]
    kind = "behaviour"
    if words:
        kind = "ocr"
        if re.search(r"slide|przesuń|drag|geetest|tcaptcha", html + body, re.I):
            kind = "slider"
        elif re.search(r"recaptcha|turnstile|hcaptcha", html, re.I):
            kind = "token"
    key = SITEKEY.search(html)
    return {"type": kind, "sitekey": key.group(1) if key else None, "url": page.url,
            "evidence": words, "iframe": bool(re.search(r"captcha|challenge", html, re.I))}


async def challenge_present(page) -> bool:
    """Sprawdza, czy po próbie nadal widać test na człowieka."""
    body = (await page.locator("body").inner_text()).lower() if await page.locator("body").count() else ""
    title = (await page.title()).lower()
    return any(word in body or word in title for word in CHALLENGE_WORDS)


async def _settle(page) -> bool:
    await page.wait_for_timeout(1000)
    return not await challenge_present(page)


async def _attempt(spec: dict, found: dict, env: dict, page, notify) -> dict:
    name = spec["name"]
    if name == "profile":
        await page.reload()
        solved = await _settle(page)
        return {"solver": name, "solved": solved, "detail": "ponowny wczyt profilu"}
    if name == "human":
        notify("Rozwiąż test w oknie przeglądarki.")
        await page.bring_to_front()
        for _ in range(60):
            if await _settle(page):
                return {"solver": name, "solved": True, "detail": "rozwiązał człowiek"}
        return {"solver": name, "solved": False, "detail": "brak rozwiązania w 60 s"}
    adapter = ADAPTERS.get(name)
    if adapter is None:
        return {"solver": name, "solved": False, "detail": "brak adaptera"}
    try:
        outcome = await adapter(found, page, env)
    except Exception as exc:
        return {"solver": name, "solved": False, "detail": f"{type(exc).__name__}: {exc}"}
    detail = outcome.get("detail") or ""
    if not outcome.get("solved"):
        return {"solver": name, "solved": False, "detail": detail or "nie rozwiązał"}
    cookies = outcome.get("cookies") or []
    if cookies:
        try:
            await page.context.add_cookies(cookies)
        except Exception as exc:
            return {"solver": name, "solved": False, "detail": f"cookies: {exc}"}
    await page.reload()
    solved = await _settle(page)
    return {"solver": name, "solved": solved,
            "detail": detail or ("token zaakceptowany" if solved else "token odrzucony"),
            "token": outcome.get("token")}


async def solve(page, notify=lambda _: None, *, forced_type: str | None = None,
                env: dict | None = None, max_solvers: int = 10, attempts: int = 1) -> dict:
    """Próbuje solverów po kolei aż do działającego tokena lub wyczerpania kolejki."""
    env = os.environ if env is None else env
    found = await classify(page) if not forced_type else {
        "type": forced_type, "sitekey": None, "url": page.url, "evidence": [], "iframe": False}
    log = []
    for spec in candidates(found["type"], env)[:max_solvers]:
        for _ in range(attempts):
            result = await _attempt(spec, found, env, page, notify)
            log.append(result)
            if result["solved"]:
                final = {"status": "solved", "solver": result["solver"], "challenge": found, "attempts": log}
                record(found, final)
                return final
    final = {"status": "escalate", "solver": None, "challenge": found, "attempts": log}
    record(found, final)
    return final
