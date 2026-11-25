# Na przyszłość

- Kontakt z dostawcami (wysyłanie zapytań, czytanie odpowiedzi). Poza zakresem pierwszej wersji, bo w starym projekcie MCP_Alibaba działało to słabo, a wysyła wiadomości w imieniu firmy.
- Wersja 2: jev-ultrafast, który sam znajduje drogę po serwisie, a program zapamiętuje jego kliknięcia i odtwarza je bez AI. Najpierw jako naprawiacz, gdy instrukcja na sztywno przestanie działać. Przed startem sprawdzić, czy jev da się podłączyć do przeglądarki Patchright (port debugowania), i pamiętać, że jev nie wgrywa plików (krok ze zdjęciem robi Patchright). Wymaga klucza TypeSafe JEV.
- Serwisy proponowane przez AI: zapisywane w pamięci i pokazywane w dashboardzie jako "proponowane serwisy"; człowiek decyduje, czy je dodać.
- DeepSeek do podpowiadania nowych serwisów (życzenie szefa). W wersji 1 wszystko robi OpenAI; DeepSeek ma być dodatkiem, bez którego program działa normalnie.
- Logowanie: człowiek loguje się raz, ręcznie, kontem firmowym w oknie przeglądarki programu, a przeglądarka zapamiętuje sesję. Bez logowania próbujemy tylko na serwisach, które wpuszczają gości. Ustalić, czy firma ma konta na Alibabie i 1688.
- Computer use (AI sterujące przeglądarką na podstawie zrzutów ekranu) jako ostatnia deska ratunku, gdy zawiodą i instrukcja, i jev. Najdroższe i najwolniejsze, więc tylko po jev. Też nie rozwiązuje testów na człowieka (docs/adr/0002).
