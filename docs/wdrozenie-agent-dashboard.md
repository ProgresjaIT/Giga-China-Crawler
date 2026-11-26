# Wdrożenie w agent-dashboard (mcp_loader)

Jak crawler działa jako klocek MCP w agent-dashboard (`ad.leadprogressai.app`) i dlaczego potrzebuje własnego `Dockerfile`. Źródło faktów: kod loadera w repo `ProgresjaIT/mcp_loader` (stan z 2026-11-26).

## Jak loader buduje obraz

Loader sprawdza repo w tej kolejności: `Dockerfile`, `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod` (`mcp_loader/builder/detect.py`). Pierwszy pasujący plik wybiera szablon.

```
repo z GitHuba
      │
      ▼
jest Dockerfile? ──tak──> szablon "dockerfile": obraz z naszego Dockerfile
      │ nie
      ▼
jest pyproject.toml? ──tak──> szablon "python-uv": python:3.12-slim + uv sync
```

Szablon `python-uv` instaluje tylko pakiety Pythona. Nie ma w nim Chrome ani Chromium, a crawler bez przeglądarki nie pobierze ofert. Stąd błąd `Chromium distribution 'chrome' is not found`. Własny `Dockerfile` z Patchright i Chromium rozwiązuje to w jednym repo.

## W jakich warunkach działa kontener

Loader generuje `compose.yaml` (`mcp_loader/builder/compose.py`) z takimi ustawieniami:

| Ustawienie | Wartość | Co to znaczy dla crawlera |
|---|---|---|
| `read_only` | `true` | Folder z kodem jest tylko do odczytu. Dane idą do `/tmp/giga-china-crawler` (`DATA_DIR`). |
| `tmpfs` | `/tmp` | `/tmp` siedzi w pamięci RAM, więc liczy się do limitu pamięci i znika przy restarcie. |
| `HOME` | `/tmp` | Narzędzia, które piszą do katalogu domowego, piszą do `/tmp`. |
| `user` | `10010:10010` | Zwykły użytkownik, nie root. Pliki w obrazie muszą być dla niego czytelne. |
| `cap_drop` | `ALL` | Brak uprawnień specjalnych. Chromium musi działać bez piaskownicy (Patchright tak robi domyślnie). |
| `mem_limit` | `512m` (domyślnie) | Ustawia zmienna `DEFAULT_MEM_LIMIT` loadera. Chromium, onnxruntime i opencv mogą się nie zmieścić. |
| `cpus` | `1.0` | Jeden rdzeń. |
| ekran | brak | Przeglądarka musi działać bez okna (`headless`). |

Serwer musi słuchać na `0.0.0.0:8000`, bo loader łączy się z nim spoza kontenera (`http://mcp-<nazwa>:8000/mcp`). Crawler ma to ustawione domyślnie (`HOST`, `PORT`).

## Dlaczego Chromium w obrazie, a nie pobierany przy starcie

Pobieranie przy starcie zapisywałoby około 150 MB do `/tmp`, czyli do pamięci RAM, i powtarzałoby się po każdym restarcie. Chromium wbudowany w obraz leży na dysku, jest gotowy od razu i ma komplet bibliotek systemowych (`patchright install --with-deps chromium`).

## Instalacja i przebudowa

- **Pierwsza instalacja** wykrywa szablon od nowa, więc po dodaniu `Dockerfile` wybierze `dockerfile`. Przy instalacji trzeba podać transport `http`, bo dla szablonu `dockerfile` loader domyślnie zakłada `stdio`.
- **Przebudowa** istniejącego serwera używa szablonu zapisanego przy pierwszej instalacji (`mcp_loader/rebuild.py`, `template=old['template']`). Serwer zainstalowany jako `python-uv` zostanie `python-uv` mimo nowego `Dockerfile`. Żeby przejść na `dockerfile`, usuń klocek w agent-dashboard i zainstaluj go ponownie.
- **Sekrety** (`OPENAI_API_KEY`, `GEMINI_API_KEY` i inne z `.env.example`) wpisuje się na stronie klocka w agent-dashboard. Loader zapisuje je do `.env` serwera, a zapis restartuje kontener.

## Znane problemy

- `Conflict. The container name "/mcp-giga-china-crawler" is already in use`: stary kontener nie został usunięty przed utworzeniem nowego. Usuwa go osoba z dostępem do serwera loadera: `docker rm -f mcp-giga-china-crawler`.
- `Read-only file system` przy `.local`: naprawione, dane idą do `DATA_DIR`.
- Captcha: bez okna nikt nie rozwiąże testu ręcznie. Działa tylko automatyczny gest suwaka Alibaby.
- Brak logowania: każdy, kto zna adres serwera, może uruchamiać wyszukiwania.
