# Testy na człowieka rozwiązuje człowiek, nie program

Gdy Source pokaże test na człowieka (np. suwak "przesuń, aby zweryfikować" albo CAPTCHA), program nie próbuje go obejść. Pokazuje okno przeglądarki, czeka, aż człowiek sam rozwiąże test, i dopiero potem kontynuuje. Jeśli nikt tego nie zrobi w wyznaczonym czasie, dany Source jest w tym Search Run pomijany, a wynik mówi wprost, że został pominięty i dlaczego.

Poprzedni projekt (MCP_Alibaba, `src/alibaba_mcp/browser/actions.py`, `drag_slider_once`) miał kod, który udawał ruch ręki człowieka po suwaku, żeby oszukać zabezpieczenie. Świadomie go nie przenosimy: obchodzenie zabezpieczeń przeciw botom łamie zasady serwisów, grozi zablokowaniem firmowego konta i adresu IP, a do tego jest zawodne (w starym projekcie zadziałało raz).

## Consequences

- Przeglądarka działa w trybie z widocznym oknem albo da się ją w każdej chwili pokazać.
- Przy wyszukiwaniu musi być ktoś, kto w razie potrzeby rozwiąże test; inaczej część Sources wypadnie z wyników.
