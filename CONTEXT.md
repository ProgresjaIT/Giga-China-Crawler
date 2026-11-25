# Giga China Crawler

Narzędzie, które dla szukanego towaru znajduje chińskich dostawców z najniższą ceną i najniższym MOQ, przeszukując chińskie serwisy z towarami.

## Language

**Query**:
To, czego szuka użytkownik: tytuł towaru, zdjęcie towaru albo oba naraz. Gdy jest samo zdjęcie, tytuł jest tworzony na podstawie zdjęcia i musi przejść sprawdzenie, czy pasuje do zdjęcia.
_Avoid_: zapytanie, search, szukajka

**Source**:
Serwis internetowy z chińskimi towarami, który przeszukujemy (np. Alibaba.com).
_Avoid_: strona, platforma, marketplace

**Offer**:
Jedno ogłoszenie produktu w jednym Source, wystawione przez jednego Suppliera.
_Avoid_: produkt, listing, aukcja

**Supplier**:
Firma, która wystawia Offer w Source.
_Avoid_: sprzedawca, Chińczyk, fabryka, vendor

**MOQ**:
Minimum Order Quantity: najmniejsza liczba jednostek, którą Supplier sprzeda w jednym zamówieniu (np. "Min. order" na Alibabie).
_Avoid_: MQU, minimalne zamówienie

**Price Tier**:
Cena za jednostkę obowiązująca od danej ilości w górę, np. "100+ szt. po 6,00 zł". Offer ma jeden lub więcej Price Tierów.
_Avoid_: przedział cenowy, widełki

**Match**:
Ocena, czy Offer to naprawdę ten sam towar, co Query. Offer przechodzi Match przy pewności co najmniej 0,7.

**Price**:
Każda cena w wynikach jest przeliczona na złotówki (PLN); cena w oryginalnej walucie Source jest pokazana obok.

**Minimum Order Value**:
Najmniejsza kwota, za jaką da się złożyć pierwsze zamówienie u Suppliera: MOQ razy cena z Price Tieru obowiązującego przy MOQ.
_Avoid_: wartość zamówienia, koszt startowy

**Cheapest List**:
Wynik wyszukiwania posortowany po najniższej możliwej cenie za jednostkę (z najwyższego Price Tieru), z ilością potrzebną do tej ceny.

**Lowest MOQ List**:
Wynik wyszukiwania posortowany po najniższym MOQ. Jednostka MOQ (szt., kg, komplety) jest zawsze pokazana, bo różnych jednostek nie da się porównać.

**Lowest Order Value List**:
Wynik wyszukiwania posortowany po najniższym Minimum Order Value.

**Search Term**:
Konkretne słowa wpisane do wyszukiwarki Source. Jedno Query może dać kilka Search Termów (np. różne nazwy handlowe tego samego towaru).
_Avoid_: fraza, keyword

**Search Run**:
Jedno wykonanie Query: użyte Search Termy i Sources oraz otrzymane listy wyników.

**Super Result**:
Search Run oznaczony przez człowieka przyciskiem "Super wynik. Zapisz w pamięci." jako wart powtórzenia.

**Memory**:
Zapis Search Runów i ich wyników, z którego program korzysta, żeby kolejne wyszukiwania dawały lepsze wyniki.

## Relationships

- **Supplier** wystawia jedną lub wiele **Offers** w jednym lub wielu **Sources**
- **Offer** ma jedno **MOQ** i jeden lub więcej **Price Tierów**
- Jedno **Query** daje jeden lub więcej **Search Termów**
- Jedno **Query** daje trzy osobne listy: **Cheapest List**, **Lowest MOQ List** i **Lowest Order Value List**
- Do list trafiają tylko **Offers**, które przeszły **Match**
- Gdy ten sam **Supplier** wystawia ten sam towar w kilku **Sources**, każda **Offer** zostaje na listach osobno; sortowanie po cenie samo pokaże tańszą wyżej
- **Search Run** jest zapisywany w **Memory**; **Super Result** waży w niej więcej niż zwykły **Search Run**

## Flagged ambiguities

- "MQU" oznaczało **MOQ**.
- "Chińczyk" oznaczało **Supplier**.
