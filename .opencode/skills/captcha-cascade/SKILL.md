---
name: captcha-cascade
description: Kaskada solverów CAPTCHA — rozpoznaj typ challenge'u, ułóż kolejkę solverów z RANKING.md i próbuj po kolei, aż token zadziała w przeglądarce. Użyj gdy w Source pojawi się CAPTCHA, suwak "przesuń, aby zweryfikować", GeeTest, Turnstile, hCaptcha albo gdy użytkownik prosi o obejście testu na człowieka.
---

# Kaskada CAPTCHA

Jeden challenge, jedna kolejka, jeden solver naraz. Kolejka jest tania na początku, droga na końcu.

## 1. Rozpoznaj typ

Zrób zrzut ekranu i sprawdź DOM: iframe, `data-sitekey`, `sitekey`, tekst z `CHALLENGE_WORDS` (`browser.py:10`). Wpisz challenge do jednej grupy:

- `ocr` — tekst, chińskie znaki, canvas.
- `slider` — GeeTest, TCaptcha, Aliyun, przesuń/kliknij w kolejności.
- `token` — reCAPTCHA, Turnstile, hCaptcha: widget z sitekey.
- `behaviour` — brak łamigłówki, ocena ruchu i IP (Turnstile invisible, DataDome, Akamai).

Gotowe, gdy: masz typ, zrzut ekranu i dowód — selektor, URL iframe'u, sitekey albo plik obrazu. Bez dowodu nie ruszaj dalej.

## 2. Ułóż kolejkę

Otwórz [RANKING.md](RANKING.md). Wybierz trzy pierwsze pozycje pasujące do typu i Source. Zapisz argumenty wejściowe (sitekey, URL, obraz) oraz szacowany koszt.

Gdy dostępny jest endpoint wizyjny TypeSafe JEV, wyślij mu zrzut i listę kandydatów, żeby zwrócił `{"type": ..., "solver": ..., "confidence": ...}`. W przeciwnym razie zastosuj heurystykę z rankingu. `jev-ultrafast` z `docs/TODO.md:4` to naprawiacz instrukcji, nie solver — nie zakładaj, że sam rozwiąże challenge.

Gotowe, gdy: kolejka ma nazwy solverów, dane wejściowe i powód wyboru.

## 3. Idź po kolei

Uruchamiaj po jednym solverze. Nie zmieniaj kolejności po porażce bez zapisania dlaczego. Na jeden challenge przejdź przez wszystkie pasujące solvery z RANKING.md z wyłączeniem `captchamind` (GPU na końcu). Po każdej próbie zapisz nazwę, `solved`, czas i błąd.

Gotowe, gdy: masz token/cookie albo kolejka jest wyczerpana.

## 4. Sprawdź replay

Tokeny WAF są związane z IP, JA3/TLS i User-Agent; `cf_clearance` żyje około 15–30 minut. Odtwórz z tego samego profilu `.local/browser-profile`, tego samego UA i tego samego proxy, którym rozwiązano challenge. Powtórz żądanie i sprawdź, czy `wait_for()` (`browser.py:30`) znów nie widzi `CHALLENGE_WORDS`.

Gotowe, gdy: drugie żądanie przechodzi bez nowego challenge'u.

## 5. Zapisz i eskaluj

Zapisz do `logs/captcha_wyniki.json`: URL, typ challenge'u, `skill`, `solver`, `repo`, `success`, czas i koszt. Jeden wpis na parę URL + typ; kolejne próby zwiększają `count`. Gdy kolejka się wyczerpie, przekaż challenge człowiekowi albo przejdź na płatnego dostawcę danych (Oxylabs, Apify, Decodo, 1688 Cloud Hub) — nie uruchamiaj tej samej kolejki bez zmiany IP, profilu albo solvera.

Gotowe, gdy: wynik zapisany i żadna kolejka nie została powtórzona w tych samych warunkach.

## Zasady

- Klucze trzymaj w `.env`; wzór jest w `.env.example`.
- Równoległe próby palą IP i budują telemetrię — kolejka jest sekwencyjna.
- Projekty z sekcji „Nie solverzy" w `RANKING.md` służą do pomiaru, nie do rozwiązywania na żywo.
