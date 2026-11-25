Logowanie i computer use dopisałem do [docs/TODO.md](docs/TODO.md). Poniżej odpowiedzi na pytania szefa.

**1. Czemu tylko dwa narzędzia, skoro Scrapling ma własne MCP?** Scrapling działa w środku naszego programu jako biblioteka: to on otwiera serwisy i wyciąga ceny. Jego własny serwer MCP daje AI ogólne narzędzia typu "pobierz dowolną stronę" ([Scrapling MCP](https://scrapling.readthedocs.io/en/latest/ai/mcp-server/)). Nie dokładamy ich do naszego serwera, bo każde narzędzie zjada tokeny, a stary projekt miał przez to 34,6 tys. tokenów na sam start (`poprawki.md`). Kto chce, może podłączyć serwer MCP Scraplinga osobno obok naszego, bez pisania żadnego kodu.

**2. Jak wygląda pętla uczenia ("reverse thinking", czyli myślenie od wyniku wstecz)?**

```
Zapytanie (tytuł / zdjęcie)
   │
   ▼
[1] OpenAI czyta pamięć: wnioski + Super Results z 50 ostatnich wyszukiwań
   │  wychodzi: Search Termy (PL/EN/CN)
   ▼
[2] Instrukcje na sztywno przeszukują 5 serwisów ──► błąd na serwisie? zapis "serwis X: zepsuta instrukcja / test na człowieka"
   │  wychodzi: oferty
   ▼
[3] Decision 1: pasuje ≥ 0,7?  ── nie ──► odrzucona (zapis: ile odrzuconych na Search Term)
   │ tak
   ▼
[4] Trzy listy w złotówkach ──► dashboard ──► człowiek: "Super wynik. Zapisz w pamięci."
   │
   ▼
[5] Element samonaprawczy: OpenAI porównuje wynik z poprzednimi i dopisuje 1–3 wnioski,
    np. "słowo 'LED strip 5050' dało 3x więcej dopasowań niż 'taśma LED'",
    "DHgate nic nie dał dla elektroniki", "1688 pokazał test, pominięty"
   │
   ▼
Plik pamięci JSON ──► wraca do kroku [1] przy następnym wyszukiwaniu
```

Program uczy się więc z dwóch rzeczy: z liczb (cena, liczba dopasowań, kliknięte "Super wynik") i z wniosków dopisywanych po każdym wyszukiwaniu. Zepsute instrukcje są widoczne w dashboardzie. W wersji 1 naprawia je człowiek, a w wersji 2 jev.

**Computer use, gdy nie działa nic innego:** dopisane do TODO jako ostatnia deska ratunku, dopiero po jev. To najdroższa i najwolniejsza opcja, bo AI patrzy na zrzuty ekranu.

**Podsumowanie**, które razem z powyższą pętlą jest podstawą kodu:
- Zapytanie to tytuł, zdjęcie albo oba. Przy samym zdjęciu OpenAI pisze tytuł, a Decision 1 sprawdza, czy pasuje do zdjęcia.
- 5 serwisów przeszukiwanych w tle instrukcjami na sztywno (Scrapling i Patchright), z widocznym postępem.
- Decision 1 sprawdza każdą ofertę, a szczegóły pobieramy dla wszystkich z pewnością co najmniej 0,7.
- Ceny w złotówkach po kursie NBP i trzy listy: najniższa cena, najniższe MOQ, najniższy koszt pierwszego zamówienia.
- Jeden serwer pod jednym adresem: MCP z narzędziami `search` i `get_results` oraz dashboard z przyciskiem "Super wynik".
- Pamięć to jeden plik JSON z wynikami i wnioskami. Testy na człowieka rozwiązuje człowiek.

Nie sprawdziłem, czy 1688 i pozostałe serwisy wpuszczają gości ani które mają wyszukiwanie zdjęciem. To wyjdzie przy pisaniu pierwszych instrukcji. Ryzyko: 5 serwisów to 5 osobnych instrukcji do napisania i utrzymania, więc pierwsze działające wyniki będą z Alibaby, a reszta dojdzie po kolei.