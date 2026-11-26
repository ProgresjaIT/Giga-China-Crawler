"""OpenAI pisze (tytuł ze zdjęcia, Search Termy, wnioski); Gemini Decision 1 ocenia (Match)."""

import asyncio
import base64
import json
import os

from google import genai
from openai import AsyncOpenAI

MATCH_THRESHOLD = 0.7
_openai: AsyncOpenAI | None = None
_gemini: genai.Client | None = None
_decisions_limit = asyncio.Semaphore(10)


def openai_client() -> AsyncOpenAI:
    global _openai
    _openai = _openai or AsyncOpenAI()
    return _openai


def gemini_client() -> genai.Client:
    global _gemini
    _gemini = _gemini or genai.Client(http_options={"api_version": "v1beta"})
    return _gemini


async def _ask(prompt: str, image: tuple[bytes, str] | None = None) -> str:
    content = [{"type": "input_text", "text": prompt}]
    if image:
        data, mime = image
        content.append({"type": "input_image", "image_url": f"data:{mime};base64,{base64.b64encode(data).decode()}"})
    response = await openai_client().responses.create(
        model=os.environ.get("OPENAI_MODEL", "gpt-5-mini"), input=[{"role": "user", "content": content}])
    return response.output_text.strip()


def _json(text: str):
    return json.loads(text[text.find("["):text.rfind("]") + 1])


async def title_from_image(image: tuple[bytes, str], rejected: list[str]) -> str:
    hint = f" Te tytuły zostały odrzucone jako niepasujące: {rejected}." if rejected else ""
    return await _ask("Napisz po angielsku krótki tytuł produktu ze zdjęcia, taki jak w ogłoszeniu hurtowym "
                      f"na Alibaba.com (3-8 słów, bez marki, jeśli nie jest pewna). Zwróć tylko tytuł.{hint}", image)


async def search_terms(title: str, memory: list[dict]) -> list[str]:
    if not os.environ.get("OPENAI_API_KEY"):
        return [title]  # shortcut: bez klucza szukamy dokładnie wpisanym tytułem, więc najlepiej po angielsku
    text = await _ask(
        "Szukamy chińskich dostawców tego towaru: " + json.dumps(title, ensure_ascii=False) + ".\n"
        "Zaproponuj 3 Search Termy po angielsku do wyszukiwarki Alibaba.com: nazwy handlowe, pod którymi "
        "chińscy dostawcy wystawiają ten towar. Pierwszy ma być najbardziej oczywisty.\n"
        "Historia wcześniejszych wyszukiwań z wnioskami (super=true oznacza wynik oceniony przez człowieka "
        "jako bardzo dobry); wykorzystaj to, co zadziałało:\n" + json.dumps(memory, ensure_ascii=False) +
        "\nZwróć tylko tablicę JSON z napisami.")
    try:
        terms = [t for t in _json(text) if isinstance(t, str) and t.strip()]
    except ValueError:
        terms = []
    return list(dict.fromkeys(terms or [title]))[:3]


async def lessons(run: dict, memory: list[dict]) -> list[str]:
    summary = {k: run.get(k) for k in ("title", "search_terms", "per_term", "per_source", "matched_count",
                                       "best_unit_price_pln", "lowest_moq", "errors")}
    if not os.environ.get("OPENAI_API_KEY"):
        return []
    text = await _ask(
        "Oto wynik wyszukiwania chińskich dostawców:\n" + json.dumps(summary, ensure_ascii=False) +
        "\nOto wcześniejsze wyszukiwania:\n" + json.dumps(memory, ensure_ascii=False) +
        "\nNapisz 1-3 krótkie wnioski po polsku, które pomogą następnym wyszukiwaniom dać tańsze oferty "
        "albo więcej dopasowań (np. które słowa zadziałały, które serwisy zawiodły). Zwróć tablicę JSON z napisami.")
    try:
        return [t for t in _json(text) if isinstance(t, str)][:3]
    except ValueError:
        return []


async def _yes_probability(blocks: list[dict], instructions: str) -> float:
    async with _decisions_limit:
        result = await gemini_client().aio.decisions.create(
            model="gemini-decision-1", input=blocks,
            questions={"yes": {"type": "noul", "instructions": instructions}})
    answer = result.answers["yes"]
    return float(answer["noul"] if isinstance(answer, dict) else answer.noul)


def _image_block(image: tuple[bytes, str]) -> dict:
    return {"type": "image", "data": base64.b64encode(image[0]).decode(), "mime_type": image[1], "resolution": "low"}


async def title_fits_image(title: str, image: tuple[bytes, str]) -> float:
    return await _yes_probability(
        [{"type": "text", "text": f"Tytuł: {title}\nZdjęcie:\n"}, _image_block(image)],
        "Czy tytuł poprawnie opisuje produkt widoczny na zdjęciu?")


async def match(title: str, image: tuple[bytes, str] | None, offer: dict) -> float:
    if not (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")):
        return 1.0  # shortcut: bez klucza Gemini każda oferta przechodzi, wyniki mogą zawierać śmieci
    blocks = [{"type": "text", "text": f"SZUKANY TOWAR\nTytuł: {title}\n"}]
    if image:
        blocks += [{"type": "text", "text": "Zdjęcie szukanego towaru:\n"}, _image_block(image)]
    blocks.append({"type": "text", "text": f"\nOFERTA DOSTAWCY\nTytuł: {offer['title']}\n"})
    if offer.get("image_url"):
        blocks += [{"type": "text", "text": "Zdjęcie oferty:\n"},
                   {"type": "image", "uri": offer["image_url"], "mime_type": "image/jpeg", "resolution": "low"}]
    return await _yes_probability(blocks, "Czy OFERTA DOSTAWCY to ten sam rodzaj towaru co SZUKANY TOWAR "
                                          "(ten sam produkt, ewentualnie inny kolor, rozmiar lub wariant)?")
