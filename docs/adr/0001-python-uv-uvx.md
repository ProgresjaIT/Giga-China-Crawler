# Python z uv, jeden serwer dostępny przez sieć

Narzędzie piszemy w Pythonie, bo w Pythonie są wszystkie potrzebne biblioteki: Scrapling, Patchright, klient Google Gemini i oficjalne SDK MCP. Zależnościami zarządza uv: jedna komenda (`uv sync`) pobiera właściwą wersję Pythona i bibliotek do osobnego katalogu projektu, a plik `uv.lock` zapewnia, że na każdym komputerze instalują się dokładnie te same wersje. Dzięki temu przeniesienie programu z komputera dewelopera na docelowy komputer firmowy to `git clone` i `uv sync`, bez ręcznego tworzenia środowiska.

Program działa w jednym miejscu (na razie na komputerze dewelopera, docelowo na komputerze firmowym) i pod jednym adresem udostępnia serwer MCP oraz dashboard. Klienci MCP (Claude, Cursor) nie instalują niczego, tylko podają adres serwera, np. `http://komputer-firmowy:8000/mcp`.

## Considered Options

- **pip + venv**: ręczne tworzenie środowiska i brak pliku blokującego wersje; łatwo o różnice między komputerami.
- **Docker**: izoluje najlepiej, ale utrudnia uruchomienie widocznej przeglądarki, w której człowiek loguje się i rozwiązuje testy na człowieka.
- **Każdy uruchamia serwer u siebie przez `uvx` (stdio)**: odrzucone, bo Memory ma być jedna i wspólna, a przeglądarka jest ciężka i potrzebuje zalogowanej sesji.

## Consequences

- Na komputerze z programem musi być zainstalowany uv (jedna komenda).
- Przeglądarkę dla Patchright trzeba pobrać osobno przy pierwszym uruchomieniu (`patchright install chromium`).
- Serwer jest dostępny w sieci, więc nie wystawiamy go poza sieć firmową.
