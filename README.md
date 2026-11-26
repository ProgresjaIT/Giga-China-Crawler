# Giga China Crawler

Szuka chińskich dostawców towaru (tytułem, zdjęciem albo jednym i drugim) na Alibaba.com i Made-in-China.com i daje trzy listy w złotówkach: najniższa cena za sztukę, najniższe MOQ i najniższy koszt pierwszego zamówienia. Jeden program udostępnia serwer MCP (dla agentów: OpenHands, Claude, Cursor) oraz dashboard dla ludzi. Słownik pojęć: [CONTEXT.md](CONTEXT.md). Decyzje: [docs/adr](docs/adr). Plany: [docs/TODO.md](docs/TODO.md).

## Co jest w repo

| Ścieżka | Co robi |
|---|---|
| `src/giga_china_crawler/server.py` | Serwer MCP i dashboard pod jednym adresem. Narzędzia: `search`, `get_results`, `solve_captcha`. |
| `src/giga_china_crawler/pipeline.py` | Przebieg wyszukiwania: hasła z AI, przeszukanie źródeł, ocena dopasowania, ceny, trzy listy. |
| `src/giga_china_crawler/sources/` | Źródła ofert: `alibaba.py`, `made_in_china.py`. |
| `src/giga_china_crawler/browser.py` | Jedna przeglądarka (Scrapling + Patchright) ze stałym profilem. |
| `src/giga_china_crawler/ai.py` | OpenAI wymyśla hasła i tytuł ze zdjęcia, Gemini ocenia, czy oferta pasuje. |
| `src/giga_china_crawler/captcha.py`, `solvers.py` | Rozpoznanie captchy i automatyczny gest suwaka Alibaby. |
| `src/giga_china_crawler/memory.py` | Pamięć wyszukiwań w jednym pliku JSON. |
| `Dockerfile` | Obraz dla serwera bez ekranu: Python, zależności i Chromium z bibliotekami. |
| `docs/wdrozenie-agent-dashboard.md` | Jak działa klocek w agent-dashboard i dlaczego potrzebuje `Dockerfile`. |

## Sekrety

W `.env` (lokalnie) albo w sekretach klocka (agent-dashboard):

- `OPENAI_API_KEY`: hasła wyszukiwania i tytuł ze zdjęcia.
- `GEMINI_API_KEY`: ocena, czy oferta to ten sam towar.

Opcjonalne zmienne: `HOST` (domyślnie `0.0.0.0`), `PORT` (domyślnie `8000`), `DATA_DIR` (folder na profil przeglądarki, pamięć i log captchy; domyślnie bieżący folder, a gdy jest tylko do odczytu, `/tmp/giga-china-crawler`), `OPENAI_MODEL`.

## Uruchomienie na komputerze

Wymaga [uv](https://docs.astral.sh/uv/) i Google Chrome.

```bash
uv sync
cp .env.example .env   # wpisz klucze
uv run giga-china-crawler
```

- Dashboard: http://127.0.0.1:8000/
- MCP: http://127.0.0.1:8000/mcp

Na komputerze z ekranem program otwiera widoczne okno Chrome. Gdy serwis pokaże test na człowieka, w dashboardzie pojawi się prośba o rozwiązanie go w tym oknie (program czeka do 5 minut).

## Uruchomienie w Dockerze (serwer bez ekranu)

```bash
docker build -t giga-china-crawler .
docker run --rm -p 8000:8000 --env-file .env giga-china-crawler
```

Bez ekranu przeglądarka działa bez okna (Chromium w trybie `headless`). Test na człowieka rozwiązuje tylko automatyczny gest suwaka Alibaby; innych testów nikt nie rozwiąże. Kontener potrzebuje co najmniej 2 GB pamięci RAM (w teście: 1,5 GB po 6 ofertach i dalej rosło).

## Agent-dashboard (OpenHands)

Loader agent-dashboard buduje obraz z `Dockerfile` w tym repo. Przy pierwszej instalacji podaj transport `http`. Przebudowa istniejącego klocka zachowuje szablon z pierwszej instalacji, więc klocek zainstalowany wcześniej jako `python-uv` trzeba usunąć i zainstalować ponownie. Szczegóły i znane problemy: [docs/wdrozenie-agent-dashboard.md](docs/wdrozenie-agent-dashboard.md).

## Podłączenie w kliencie MCP

```json
{ "mcpServers": { "giga-china-crawler": { "type": "http", "url": "http://ADRES-SERWERA:8000/mcp" } } }
```

Wyszukiwanie trwa minuty: agent wywołuje `search`, a potem co jakiś czas `get_results`, aż status przestanie być `running`.

Serwer nie ma logowania. Nie wystawiaj go poza sieć firmową.

## Testy

```bash
uv run python -m unittest discover -s tests
```
