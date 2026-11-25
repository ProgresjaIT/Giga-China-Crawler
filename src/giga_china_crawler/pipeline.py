"""Jeden Search Run: tytuł -> Search Termy -> Sources -> Match -> szczegóły -> trzy listy -> wnioski -> pamięć."""

import asyncio
import uuid
from datetime import datetime, timezone

from giga_china_crawler import ai, browser, memory
from giga_china_crawler.ranking import price_offer, three_lists
from giga_china_crawler.sources import alibaba

# shortcut: na razie tylko Alibaba.com; 1688, Made-in-China, Global Sources i DHgate dochodzą po kolei.
SOURCES = [alibaba]
RUNS: dict[str, dict] = {}
_tasks: set[asyncio.Task] = set()


def start(title: str, image: tuple[bytes, str] | None) -> str:
    if not title.strip() and not image:
        raise ValueError("Podaj tytuł albo zdjęcie towaru.")
    run = {"id": uuid.uuid4().hex[:12], "title": title.strip(), "has_image": bool(image), "status": "running",
           "progress": [], "started_at": datetime.now(timezone.utc).isoformat(), "errors": []}
    RUNS[run["id"]] = run
    task = asyncio.create_task(_run(run, image))
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)
    return run["id"]


def get(run_id: str) -> dict | None:
    return RUNS.get(run_id) or next((r for r in memory.load() if r["id"] == run_id), None)


async def _run(run: dict, image) -> None:
    def note(text: str):
        run["progress"].append(text)

    try:
        if not run["title"]:
            run["title"] = await _title_from_image(image, note)
        history = memory.recent()
        run["search_terms"] = await ai.search_terms(run["title"], history)
        note(f"Search Termy: {', '.join(run['search_terms'])}")

        offers, run["per_term"], run["per_source"] = {}, {}, {}
        async with browser.session() as session:
            for source in SOURCES:
                found = []
                for term in run["search_terms"]:
                    note(f"{source.NAME}: szukam „{term}”")
                    try:
                        batch = await source.search(session, term, note)
                    except Exception as exc:
                        run["errors"].append(f"{source.NAME} / {term}: {exc}")
                        batch = []
                    for offer in batch:
                        offer["search_term"] = term
                    run["per_term"][term] = run["per_term"].get(term, 0) + len(batch)
                    found += batch
                if image and hasattr(source, "search_image"):
                    note(f"{source.NAME}: szukam zdjęciem")
                    try:
                        batch = await source.search_image(session, image, note)
                    except Exception as exc:
                        run["errors"].append(f"{source.NAME} / zdjęcie: {exc}")
                        batch = []
                    for offer in batch:
                        offer["search_term"] = "(zdjęcie)"
                    found += batch
                run["per_source"][source.NAME] = {"found": len(found)}
                for offer in found:
                    offers.setdefault(offer["url"], offer)

            note(f"Sprawdzam dopasowanie {len(offers)} ofert (Gemini Decision 1)")
            candidates = list(offers.values())
            scores = await asyncio.gather(*(ai.match(run["title"], image, o) for o in candidates),
                                          return_exceptions=True)
            matched = []
            for offer, score in zip(candidates, scores):
                if isinstance(score, Exception):
                    run["errors"].append(f"Match {offer['url']}: {score}")
                    continue
                offer["match"] = round(score, 2)
                if score >= ai.MATCH_THRESHOLD:
                    matched.append(offer)
            run["matched_count"] = len(matched)

            by_name = {s.NAME: s for s in SOURCES}
            for i, offer in enumerate(matched, 1):
                note(f"Szczegóły oferty {i}/{len(matched)}")
                try:
                    offer |= await by_name[offer["source"]].details(session, offer["url"], note)
                except Exception as exc:
                    run["errors"].append(f"Szczegóły {offer['url']}: {exc}")

        for offer in matched:
            price_offer(offer)
        run["lists"] = three_lists(matched)
        cheapest, lowest = run["lists"]["cheapest"], run["lists"]["lowest_moq"]
        run["best_unit_price_pln"] = cheapest[0]["unit_price_pln"] if cheapest else None
        run["lowest_moq"] = f"{lowest[0]['moq']} {lowest[0]['moq_unit']}" if lowest else None
        run["status"] = "done"
        note("Gotowe")
        try:
            run["lessons"] = await ai.lessons(run, history)
        except Exception as exc:
            run["errors"].append(f"Wnioski: {exc}")
    except Exception as exc:
        run["status"] = "error"
        run["errors"].append(f"{type(exc).__name__}: {exc}")
    finally:
        run["finished_at"] = datetime.now(timezone.utc).isoformat()
        memory.save_run(run)


async def _title_from_image(image, note) -> str:
    """OpenAI pisze tytuł, Decision 1 sprawdza, czy pasuje do zdjęcia; do 3 prób."""
    rejected = []
    for _ in range(3):
        title = await ai.title_from_image(image, rejected)
        score = await ai.title_fits_image(title, image)
        note(f"Tytuł ze zdjęcia: „{title}” (pasuje na {score:.2f})")
        if score >= ai.MATCH_THRESHOLD:
            return title
        rejected.append(title)
    raise RuntimeError("Nie udało się opisać zdjęcia tytułem, który pasuje. Dodaj tytuł ręcznie.")
