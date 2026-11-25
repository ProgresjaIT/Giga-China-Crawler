Piszę teraz szkielet nowego projektu w Giga-China-Crawler. Potem sprawdzę na żywo, jak działa wyszukiwanie zdjęciem na Alibabie.

Sprawdzam w przeglądarce, jak Alibaba przyjmuje zdjęcie do wyszukiwania.

Alibaba od razu pokazała mi test CAPTCHA w przeglądarce podglądu. Nie rozwiązuję go, więc dalej sprawdzę selektory w samym programie, na Patchright i prawdziwym Chrome.

Testy cen wyłapały błąd w czytaniu formatu "1,00 USD". Poprawiam to, żeby rozpoznawanie formatu nie zależało od waluty.

Pierwsza wersja jest w [Giga-China-Crawler](README.md). Jeden program uruchamia serwer MCP z narzędziami `search` i `get_results` oraz dashboard z polem na tytuł, zdjęciem i przyciskiem "Super wynik". Na razie przeszukuje tylko Alibabę. Główna logika jest w [pipeline.py](src/giga_china_crawler/pipeline.py), a dopasowanie przez Decision 1 i teksty z OpenAI w [ai.py](src/giga_china_crawler/ai.py). Sprawdziłem, że serwer startuje, dashboard się otwiera, MCP odpowiada, a 4 testy cen i list przechodzą.

Prawdziwe wyszukiwanie na Alibabie nie przeszło, bo w nowym profilu przeglądarki od razu pojawił się test CAPTCHA. Przez to nie sprawdziłem jeszcze pobierania ofert, progów cenowych, wyszukiwania zdjęciem ani wywołań Gemini i OpenAI.

To zderza się z notatką w `plan_do_zatwierdzenia.md`, że szef nie chce ręcznie logować się ani rozwiązywać CAPTCHA. Automatycznego rozwiązywania nie zrobię. Zostają dwie drogi. Pierwsza: ktoś rozwiązuje test raz, a my sprawdzamy, czy zapamiętany profil przeglądarki potem działa przez kilka dni bez kolejnych testów. Druga: płatny dostawca danych z notatki w starym projekcie (Oxylabs, Apify, Decodo albo oficjalny 1688 Cloud Hub), który daje ceny bez przeglądarki po naszej stronie.

Żeby odpalić program u siebie, wpisz klucze OpenAI i Gemini do `.env` (wzór jest w `.env.example`):

```bash
cd /home/jakub/Dokumenty/Repozytoria/Giga-China-Crawler && cp .env.example .env
```

```bash
cd /home/jakub/Dokumenty/Repozytoria/Giga-China-Crawler && uv run giga-china-crawler
```

Pominąłem 4 pozostałe serwisy (oznaczone w kodzie jako `shortcut`). Domyślny model OpenAI `gpt-5-mini` to moje założenie, więc zmień go w `.env`, jeśli używacie innego. Zrobiłem też `git init` w repo, ale nic nie jest zacommitowane, a serwer nie ma logowania, więc nie może być wystawiony poza sieć firmową.