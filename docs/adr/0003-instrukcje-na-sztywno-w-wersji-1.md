# Wersja 1 czyta serwisy instrukcjami na sztywno, nie agentem AI

Każdy z pięciu Sources (Alibaba.com, 1688.com, Made-in-China.com, Global Sources, DHgate) ma w wersji 1 własną, ręcznie napisaną instrukcję w Scraplingu z przeglądarką Patchright: gdzie jest pole wyszukiwania, gdzie wgrać zdjęcie, gdzie stoi cena, MOQ i dostawca. Wybraliśmy to, bo najszybciej daje działające wyniki, nie kosztuje nic przy każdym kroku i obsługuje wgrywanie zdjęć, czego wymaga wyszukiwanie zdjęciem.

## Considered Options

- **Agent jev-ultrafast na wszystkich serwisach**: sam znajduje drogę po nowych stronach, ale każdy krok to zapytanie do AI, nie wgrywa plików (odpada wyszukiwanie zdjęciem) i łączy się z Chrome przez port debugowania, więc nie wiadomo, czy zadziała z Patchright.
- **Dwa lub trzy sposoby naraz** (instrukcje dla dużych serwisów, agent dla reszty): odrzucone, bo jeden sposób jest prostszy w utrzymaniu.

## Consequences

- Gdy serwis zmieni wygląd, instrukcję trzeba poprawić ręcznie.
- Nowy Source wymaga napisania nowej instrukcji.
- Wersja 2 (docs/TODO.md) ma dodać jev, który sam znajduje drogę i zapamiętuje kliknięcia, najpierw jako naprawiacz zepsutych instrukcji.
