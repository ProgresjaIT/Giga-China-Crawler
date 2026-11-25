"""Adaptery do realnego kodu solverów z katalogu vendor/."""

import asyncio
import base64
import os
import re
import sys
from pathlib import Path

import httpx

from giga_china_crawler.actions import SLIDER_HANDLE, drag_slider_once

VENDOR = Path(__file__).resolve().parents[2] / "vendor"
PATHS = {
    "ddddocr": VENDOR / "ddddocr",
    "geetest": VENDOR / "geetest-solver",
    "nopecha": VENDOR / "nopecha-python" / "src",
    "twocaptcha": VENDOR / "2captcha-python",
}
for path in PATHS.values():
    if path.is_dir() and str(path) not in sys.path:
        sys.path.insert(0, str(path))

CAPTCHA_ID = re.compile(r'captcha[_-]?id["\']?\s*[:=]\s*["\']([^"\']+)', re.I)


def _missing(what: str) -> dict:
    return {"solved": False, "detail": f"brak {what}", "skipped": True}


async def slider_gesture(found: dict, page, env: dict) -> dict:
    for frame in list(getattr(page, "frames", ()) or ()) + [page]:
        try:
            handle = frame.locator(SLIDER_HANDLE)
            if not await handle.is_visible():
                continue
            if await drag_slider_once(page, frame):
                return {"solved": True, "detail": "gest suwaka Alibaba"}
        except Exception as exc:
            continue
    return {"solved": False, "detail": "brak widocznego suwaka #nc_1_n1z"}


async def ddddocr(found: dict, page, env: dict) -> dict:
    try:
        import ddddocr as lib
    except ImportError:
        return _missing("ddddocr z vendor/ddddocr")
    try:
        image = await page.screenshot()
        answer = await asyncio.to_thread(lambda: lib.DdddOcr(show_ad=False).classification(image))
    except Exception as exc:
        return {"solved": False, "detail": f"ddddocr: {type(exc).__name__}: {exc}"}
    inputs = page.locator("input[type=text], input:not([type])")
    if await inputs.count():
        await inputs.first.fill(answer)
        await inputs.first.press("Enter")
    return {"solved": bool(answer), "detail": f"ddddocr: {answer[:60]}", "answer": answer}


async def geetest(found: dict, page, env: dict) -> dict:
    try:
        from geetest_solver import GeetestSolver
    except ImportError:
        return _missing("geetest-solver z vendor/geetest-solver")
    match = CAPTCHA_ID.search(await page.content())
    captcha_id = match.group(1) if match else found.get("sitekey")
    if not captcha_id:
        return {"solved": False, "detail": "geetest: brak captcha_id"}
    try:
        result = await asyncio.to_thread(lambda: GeetestSolver(captcha_id, "slide").solve())
    except Exception as exc:
        return {"solved": False, "detail": f"geetest: {type(exc).__name__}: {exc}"}
    return {"solved": bool(result), "detail": f"geetest: {str(result)[:120]}", "token": str(result)}


async def _sidecar(found: dict, env: dict, url_env: str, payload: dict) -> dict:
    url = env.get(url_env)
    if not url:
        return _missing(url_env)
    headers = {}
    if env.get("CAPTCHA_SOLVER_TOKEN"):
        headers["Authorization"] = f"Bearer {env['CAPTCHA_SOLVER_TOKEN']}"
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(url.rstrip("/") + "/solve", json=payload, headers=headers)
            data = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        return {"solved": False, "detail": f"{url_env}: {type(exc).__name__}: {exc}"}
    return {"solved": bool(data.get("solved")), "detail": str(data.get("error") or data.get("method") or "")[:200],
            "token": data.get("token"), "cookies": data.get("cookies") or []}


async def cf_solver(found: dict, page, env: dict) -> dict:
    kind = found["type"]
    payload = {"url": found["url"], "sitekey": found["sitekey"], "type": "auto"}
    if kind == "slider" and found["sitekey"]:
        payload.update({"type": "geetest", "captcha_id": found["sitekey"], "risk_type": "slide"})
    elif kind == "token":
        payload["type"] = "recaptcha"
    elif kind == "behaviour":
        payload["type"] = "cloudflare"
    return await _sidecar(found, env, "CF_SOLVER_URL", payload)


async def cipher_solver(found: dict, page, env: dict) -> dict:
    kind = found["type"]
    payload = {"url": found["url"], "sitekey": found["sitekey"],
               "type": "recaptcha" if kind == "token" else "cloudflare" if kind == "behaviour" else "hcaptcha"}
    return await _sidecar(found, env, "CIPHER_SOLVER_URL", payload)


async def nopecha(found: dict, page, env: dict) -> dict:
    key = env.get("NOPECHA_API_KEY")
    if not key:
        return _missing("NOPECHA_API_KEY")
    try:
        from nopecha.api.requests import RequestsAPIClient
    except ImportError:
        return _missing("nopecha-python z vendor/nopecha-python")
    api = RequestsAPIClient(key)
    try:
        if found["type"] == "token":
            if "turnstile" in (await page.content()).lower():
                answer = await asyncio.to_thread(api.solve_cloudflare_turnstile, found["sitekey"], found["url"])
            else:
                answer = await asyncio.to_thread(api.solve_recaptcha_v2, found["sitekey"], found["url"])
        elif found["type"] == "ocr":
            image = base64.b64encode(await page.screenshot()).decode()
            answer = await asyncio.to_thread(api.recognize_textcaptcha, image)
        else:
            return {"solved": False, "detail": "nopecha: typ nieobsługiwany"}
    except Exception as exc:
        return {"solved": False, "detail": f"nopecha: {type(exc).__name__}: {exc}"}
    token = getattr(answer, "data", answer)
    return {"solved": bool(token), "detail": f"nopecha: {str(token)[:60]}", "token": str(token)}


async def twocaptcha(found: dict, page, env: dict) -> dict:
    key = env.get("TWO_CAPTCHA_API_KEY")
    if not key:
        return _missing("TWO_CAPTCHA_API_KEY")
    try:
        from twocaptcha import TwoCaptcha
    except ImportError:
        return _missing("2captcha-python z vendor/2captcha-python")
    solver = TwoCaptcha(key)
    try:
        if found["type"] == "ocr":
            answer = await asyncio.to_thread(solver.normal, await page.screenshot())
        elif found["type"] == "slider" and found["sitekey"]:
            answer = await asyncio.to_thread(solver.geetest_v4, found["sitekey"], found["url"])
        elif found["sitekey"]:
            answer = await asyncio.to_thread(solver.recaptcha, found["sitekey"], found["url"])
        else:
            return {"solved": False, "detail": "2captcha: brak danych"}
    except Exception as exc:
        return {"solved": False, "detail": f"2captcha: {type(exc).__name__}: {exc}"}
    return {"solved": bool(answer), "detail": f"2captcha: {str(answer)[:60]}", "token": str(answer)}


async def extension(found: dict, page, env: dict) -> dict:
    url = env.get("EXTENSION_SOLVER_URL")
    if not url:
        return _missing("EXTENSION_SOLVER_URL")
    method = {"token": "userrecaptcha", "ocr": "base64", "slider": "geetest"}.get(found["type"], "userrecaptcha")
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            submitted = (await client.post(url.rstrip("/") + "/in.php", data={
                "key": env.get("EXTENSION_SOLVER_KEY", ""), "method": method,
                "sitekey": found["sitekey"] or "", "pageurl": found["url"], "json": "1"})).json()
            task = submitted.get("request")
            if not task:
                return {"solved": False, "detail": f"extension: {submitted}"}
            for _ in range(60):
                await asyncio.sleep(2)
                polled = (await client.get(url.rstrip("/") + "/res.php", params={
                    "key": env.get("EXTENSION_SOLVER_KEY", ""), "id": task, "json": "1"})).json()
                if polled.get("request") != "CAPCHA_NOT_READY":
                    token = polled.get("request")
                    return {"solved": bool(token), "detail": f"extension: {str(token)[:60]}", "token": str(token)}
    except (httpx.HTTPError, ValueError) as exc:
        return {"solved": False, "detail": f"extension: {type(exc).__name__}: {exc}"}
    return {"solved": False, "detail": "extension: timeout"}


ADAPTERS = {
    "alibaba-slider": slider_gesture,
    "ddddocr": ddddocr,
    "geetest-solver": geetest,
    "cf-solver": cf_solver,
    "cipher-solver": cipher_solver,
    "nopecha": nopecha,
    "2captcha": twocaptcha,
    "extension-solver": extension,
}
