# Ranking solverów

Kolejność to domyślna kolejka prób dla crawlera chińskich Source'ów. Zmiana kolejności wymaga dowodu z kroku 1 kaskady.

| # | Solver | Typy | Koszt | Uwaga |
| --- | --- | --- | --- | --- |
| 1 | Zapamiętany profil `.local/browser-profile` | sesja | 0 | `browser.py:9`. Stare cookie często wystarcza — spróbuj przed solverami. |
| 1b | `MCP_Alibaba/src/alibaba_mcp/browser/actions.py` | suwak Alibaby | 0 | Ludzki gest `#nc_1_n1z` → `#nc_1_n1t`, przed OCR. |
| 2 | `ddddocr` | tekst, chińskie znaki, suwak | 0, offline | MIT, szybki. Nie daje tokenu dla widgetów. |
| 3 | `Evil-Bane/Geetest-Solver` | GeeTest v4: slide, icon, ai, gobang | 0 | ddddocr + OpenCV ORB; >95% na demo. Najczęstszy blok chińskich Source'ów. |
| 4 | `VeyraAgent/cf-solver` | ~55 typów: GeeTest v3/v4, TCaptcha, Aliyun, Shumei, Turnstile, reCAPTCHA, hCaptcha | 0, self-hosted | FastAPI. Część typów potrzebuje sitekey lub czystego IP; oznaczone jako educational use. |
| 5 | `cipher-x-sudo/captcha-solver` | 11 typów: Turnstile, reCAPTCHA, hCaptcha, Cloudflare, AWS WAF, BotGuard, DataDome, PerimeterX, Akamai, Aliyun, Arkose | 0, self-hosted | CloakBrowser, `:8877`, headful/Xvfb. Mocny w WAF, słabszy w chińskich puzzle'ach. |
| 6 | `NopeCHA` | reCAPTCHA v2/v3, Turnstile, FunCaptcha, AWS WAF, tekst, PerimeterX | 100 zapytań/dzień | Rozszerzenie/API, kod zamknięty. Endpoint hCaptcha wycofany w październiku 2026. |
| 7 | `AlibabaResearch/captcha-mind` | 8 zadań: connect_icon, coordinates, dart_count, dice_count, rotation_match, image_select, click_order, slide_puzzle | GPU + vLLM | Na końcu. Quadro P2000 4 GB nie wystarcza dla 7B fp16 (~15 GB). Nie podłączony. |
| 8 | `icemellow-me/captcha-solver-extension` | reCAPTCHA v2, Turnstile, hCaptcha, obraz/canvas | 0, ale trzy backendy | Wymaga serwerów na portach 8844, 8833, 8822. Najwięcej infrastruktury. |
| 9 | `2captcha` / `Anti-Captcha` | około 40 typów | płatne | Otwarte klienty, rozwiązuje usługa. Ostateczny fallback. |
| 10 | Człowiek w oknie przeglądarki | dowolny | czas | Ostatnia deska ratunku, 60 s i przerywalne. |
| 11 | Płatny dostawca danych | brak challenge'u | płatne | Oxylabs, Apify, Decodo, 1688 Cloud Hub. Gdy zablokowano konto lub IP. |

## Nie solverzy

| Repo | Zastosowanie |
| --- | --- |
| `MetaAgentX/OpenCaptchaWorld` | 463 puzzle'y, środowisko testowe agentów. Porównuj modele, nie rozwiązuj na żywo. |
| `kronenflex/llm-captcha-benchmark` | 28 rodzin na lokalnych fixture'ach + metryki ruchu myszy. Pomiar, nie produkcja. |

## Heurystyka

| Dowód z kroku 1 | Kolejka |
| --- | --- |
| chiński tekst albo canvas | 1 → 2 → 4 |
| suwak / GeeTest | 1 → 3 → 4 → 7 |
| widget z sitekey | 1 → 6 → 5 → 4 → 9 |
| cookie WAF | 1 → 5 → 4 → 9 |
| brak łamigłówki, ocena ruchu | 1 → 5 → residential proxy → 10 |

Wybór Jeva (krok 2 kaskady) ma sens tylko wtedy, gdy masz klucz TypeSafe JEV i endpoint, który przyjmuje obraz. W repozytorium Jev występuje jako `jev-ultrafast` — agent do naprawy instrukcji, nie klasyfikator CAPTCHA.

## Konfiguracja

Kolejka w kodzie to `captcha.py:SOLVERS`. Dostęp do niej daje narzędzie MCP `solve_captcha(url, challenge_type)`; `browser.py` wywołuje ją sam, gdy wykryje test.

`ddddocr` i `geetest-solver` działają lokalnie z kodu w `vendor/`, bez kluczy. `cf-solver` i `cipher-solver` czytają `CF_SOLVER_URL` / `CIPHER_SOLVER_URL` (własne `POST /solve`, opcjonalny `CAPTCHA_SOLVER_TOKEN`). `nopecha` i `2captcha` używają klientów z `vendor/` i kluczy `NOPECHA_API_KEY` / `TWO_CAPTCHA_API_KEY`. `extension-solver` wymaga `EXTENSION_SOLVER_URL` i opcjonalnie `EXTENSION_SOLVER_KEY`; protokół `in.php`/`res.php` zgodny z `vendor/captcha-solver-extension/background.js`. `captchamind` jest wyłączony do końca. Każda próba ląduje w `logs/captcha_wyniki.json` z `skill`, `solver`, `repo`, `success`.
