# Giga China Crawler

Szuka chińskich dostawców towaru (tytułem, zdjęciem albo jednym i drugim) i daje trzy listy w złotówkach: najniższa cena za sztukę, najniższe MOQ i najniższy koszt pierwszego zamówienia. Jeden program udostępnia serwer MCP (dla Claude, Cursora i innych) oraz dashboard dla ludzi. Słownik pojęć: [CONTEXT.md](CONTEXT.md). Decyzje: [docs/adr](docs/adr). Plany: [docs/TODO.md](docs/TODO.md).

## Uruchomienie

```bash
uv sync
cp .env.example .env   # wpisz OPENAI_API_KEY i GEMINI_API_KEY
uv run giga-china-crawler
```

- Dashboard: http://127.0.0.1:8000/
- MCP: http://127.0.0.1:8000/mcp (narzędzia `search` i `get_results`)

Program otwiera widoczne okno Chrome (wymagany zainstalowany Google Chrome). Gdy serwis pokaże test na człowieka, w dashboardzie pojawi się prośba o rozwiązanie go w tym oknie; program czeka do 5 minut ([ADR 0002](docs/adr/0002-czlowiek-rozwiazuje-testy-na-czlowieka.md)). Profil przeglądarki z sesją jest w `.local/browser-profile`, pamięć wyszukiwań w `memory.json`.

Żeby inni w sieci firmowej mogli się podłączyć, ustaw w `.env` `HOST=0.0.0.0`. Nie wystawiaj serwera poza sieć firmową: nie ma logowania.

## Podłączenie w kliencie MCP

```json
{ "mcpServers": { "giga-china-crawler": { "type": "http", "url": "http://ADRES-KOMPUTERA:8000/mcp" } } }
```

## Testy

```bash
uv run python -m unittest discover -s tests
```
