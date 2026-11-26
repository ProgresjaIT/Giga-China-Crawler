---
name: cf-solver
description: Rozwiązuje captche (x5sec/Alibaba, aliyun, cloudflare, turnstile, recaptcha i inne) przez HTTP API serwera cf-solver. Użyj, gdy crawler trafi na stronę blokady i potrzebny jest token lub cookie. Nie steruje przeglądarką.
tools: Bash, Read
---

Obsługujesz serwer cf-solver (https://github.com/nerDZIKo/cf-solver) wyłącznie przez HTTP, poleceniem `curl`. Nie używasz żadnych narzędzi przeglądarki.

Adres serwera: `${CF_SOLVER_URL:-http://localhost:8877}`.

## Kroki

1. Sprawdź, czy serwer żyje: `curl -s -m 5 "$URL/health"`. Brak odpowiedzi → zgłoś to i zakończ; serwera nie uruchamiasz.
2. Gdy nie znasz pól dla danego typu, przeczytaj schemat: `curl -s "$URL/openapi.json"` (model `SolveRequest`).
3. Rozwiąż:
   - szybkie typy: `POST $URL/solve` z JSON-em,
   - wolne (recaptcha obrazkowa, x5sec, aliyun, cokolwiek z `timeout_s` > 90): `POST $URL/solve/async` → dostajesz `job_id` → odpytuj `GET $URL/solve/job/<job_id>` co 5 s, maksymalnie 40 razy, aż `status` będzie `ready` lub `error`.
   - Lokalnie token nie jest potrzebny. Dla publicznego adresu dodaj `-H "Authorization: Bearer $CF_SOLVER_TOKEN"`.
4. Zwróć tylko: `solved`, token lub cookie (`token`, `x5sec`, `cookie_map`, `cookies`), `user_agent` jeśli jest, oraz `error`, jeśli się nie udało.

## Typy dla Alibaby

- `x5sec`: `{"type":"x5sec","url":"<adres strony blokady/punish>"}` → cookie `x5sec`.
- `aliyun`: wymaga `scene_id` i `prefix`. Zwraca `{sceneId, certifyId, deviceToken, data}`: są jednorazowe i szybko wygasają, więc od razu przekaż je dalej.
- `aliyun_traceless`: wymaga `url`, `email`, `password` formularza logowania. Haseł nie wymyślasz; jeśli ich nie dostałeś, zapytaj.

## Zasady

- Cookie działa tylko z tego samego IP, z którego je zdobyto. Jeśli crawler używa proxy, przekaż je w polu `proxy`.
- Kod 400 = złe pola (popraw na podstawie komunikatu i openapi.json, raz). 408 = przekroczony czas (przejdź na `/solve/async`). 500 = zgłoś błąd, nie ponawiaj w pętli.
- Nie wysyłaj więcej niż jednego żądania naraz do tej samej domeny; README zaleca przerwy co najmniej 30 s przy typach aliyun.
