"""Jeden proces: serwer MCP (/mcp) i dashboard (/) pod tym samym adresem."""

import base64
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse

from giga_china_crawler import memory, pipeline

MAX_IMAGE_BYTES = 10 * 1024 * 1024
IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}

mcp = MCPServer("giga-china-crawler", instructions=(
    "Szuka chińskich dostawców towaru i zwraca trzy listy w PLN: najniższa cena za sztukę, najniższe MOQ "
    "i najniższy koszt pierwszego zamówienia. Wyszukiwanie trwa minuty: wywołaj search, potem co jakiś czas "
    "get_results, aż status przestanie być 'running'."))


def _check_image(data: bytes, mime: str) -> tuple[bytes, str]:
    mime = mime.split(";")[0].strip().lower()
    if mime not in IMAGE_TYPES or not data or len(data) > MAX_IMAGE_BYTES:
        raise ValueError("Zdjęcie musi być JPG, PNG albo WEBP i mieć do 10 MB.")
    return data, mime


async def _download_image(url: str) -> tuple[bytes, str]:
    if not url.startswith(("https://", "http://")):
        raise ValueError("Adres zdjęcia musi zaczynać się od http:// albo https://")
    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        response = await client.get(url)
    response.raise_for_status()
    return _check_image(response.content, response.headers.get("content-type", ""))


@mcp.tool()
async def search(title: str = "", image_url: str = "") -> dict:
    """Rozpocznij wyszukiwanie dostawców. Podaj tytuł towaru, adres zdjęcia albo oba. Zwraca run_id."""
    image = await _download_image(image_url) if image_url else None
    return {"run_id": pipeline.start(title, image), "status": "running"}


@mcp.tool()
async def get_results(run_id: str) -> dict:
    """Postęp albo wynik wyszukiwania: trzy listy ofert (ceny w PLN), błędy i wnioski."""
    run = pipeline.get(run_id)
    return run or {"error": "Nie ma wyszukiwania o takim run_id."}


@mcp.tool()
async def solve_captcha(url: str, challenge_type: str = "") -> dict:
    """Uruchom kaskadę solverów CAPTCHA na stronie. Zwraca status, użyty solver i próby."""
    from giga_china_crawler import browser, captcha
    if challenge_type and challenge_type not in captcha.ALL_TYPES:
        raise ValueError(f"Typ challenge'u musi być jednym z: {', '.join(captcha.ALL_TYPES)}")
    result = {}

    async def action(page):
        result.update(await captcha.solve(page, forced_type=challenge_type or None))

    async with browser.session() as session:
        await session.fetch(url, page_action=action, google_search=False, timeout=60000)
    return result or {"error": "Nie udało się otworzyć strony."}


@mcp.custom_route("/", methods=["GET"])
async def dashboard(request: Request) -> HTMLResponse:
    return HTMLResponse((Path(__file__).parent / "dashboard.html").read_text(encoding="utf-8"))


@mcp.custom_route("/api/search", methods=["POST"])
async def api_search(request: Request) -> JSONResponse:
    body = await request.json()
    try:
        image = None
        if body.get("image_base64"):
            image = _check_image(base64.b64decode(body["image_base64"]), body.get("image_type", ""))
        return JSONResponse({"run_id": pipeline.start(body.get("title", ""), image)})
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)


@mcp.custom_route("/api/runs", methods=["GET"])
async def api_runs(request: Request) -> JSONResponse:
    runs = [{k: r.get(k) for k in ("id", "title", "status", "started_at", "super", "matched_count")}
            for r in memory.load()[-30:]]
    return JSONResponse(runs[::-1])


@mcp.custom_route("/api/runs/{run_id}", methods=["GET"])
async def api_run(request: Request) -> JSONResponse:
    run = pipeline.get(request.path_params["run_id"])
    return JSONResponse(run) if run else JSONResponse({"error": "Nie znaleziono"}, status_code=404)


@mcp.custom_route("/api/runs/{run_id}/super", methods=["POST"])
async def api_super(request: Request) -> JSONResponse:
    run_id = request.path_params["run_id"]
    if run_id in pipeline.RUNS:
        pipeline.RUNS[run_id]["super"] = True
    return JSONResponse({"ok": memory.mark_super(run_id)})


def main() -> None:
    load_dotenv()
    mcp.run("streamable-http", host=os.environ.get("HOST", "0.0.0.0"), port=int(os.environ.get("PORT", "8000")))


if __name__ == "__main__":
    main()
