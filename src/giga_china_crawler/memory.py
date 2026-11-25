"""Pamięć: jeden plik JSON z Search Runami, wnioskami i oznaczeniami "Super wynik"."""

import json
import os
import threading
from pathlib import Path

PATH = Path(os.environ.get("MEMORY_PATH", "memory.json"))
_lock = threading.Lock()


def load() -> list[dict]:
    return json.loads(PATH.read_text(encoding="utf-8")) if PATH.exists() else []


def _write(runs: list[dict]) -> None:
    # Zapis do pliku tymczasowego i podmiana: awaria w trakcie nie niszczy historii.
    tmp = PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(runs, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(PATH)


def save_run(run: dict) -> None:
    with _lock:
        runs = [r for r in load() if r["id"] != run["id"]]
        _write(runs + [run])


def mark_super(run_id: str) -> bool:
    with _lock:
        runs = load()
        for run in runs:
            if run["id"] == run_id:
                run["super"] = True
                _write(runs)
                return True
        return False


def recent(limit: int = 50) -> list[dict]:
    """Skrót ostatnich wyszukiwań dla AI; Super Results na początku."""
    runs = load()[-limit:]
    runs.sort(key=lambda r: not r.get("super"))
    return [{"query": r.get("title"), "super": r.get("super", False), "search_terms": r.get("search_terms"),
             "matched": r.get("matched_count"), "best_unit_price_pln": r.get("best_unit_price_pln"),
             "lessons": r.get("lessons", [])} for r in runs]
