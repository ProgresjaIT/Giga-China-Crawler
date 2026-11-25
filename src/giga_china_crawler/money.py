"""Ceny, progi cenowe, MOQ i przeliczanie na złotówki po kursie NBP."""

import re
import time

import httpx

CURRENCIES = (("PLN", "PLN"), ("zł", "PLN"), ("US$", "USD"), ("USD", "USD"), ("$", "USD"),
              ("CNY", "CNY"), ("RMB", "CNY"), ("¥", "CNY"), ("￥", "CNY"), ("EUR", "EUR"), ("€", "EUR"))
NUMBER = r"\d[\d.,]*"


def currency_of(text: str) -> str | None:
    return next((code for mark, code in CURRENCIES if mark in text), None)


def parse_number(text: str) -> float:
    """"1.132,63" (PL) i "1,132.63" (EN). Przy jednym separatorze: dokładnie 3 cyfry po nim i część
    całkowita różna od 0 oznaczają tysiące ("42.582", "1,000"), w innym razie to część dziesiętna."""
    # shortcut: "1,500" zawsze czytamy jako 1500, nie 1,5; jeśli Source poda 3 miejsca po przecinku, poprawić per Source.
    text = text.rstrip(".,")
    seps = [c for c in text if c in ",."]
    if not seps:
        return float(text)
    last = max(text.rfind(","), text.rfind("."))
    head, tail = re.sub(r"[.,]", "", text[:last]), text[last + 1:]
    if len(set(seps)) == 1 and (len(seps) > 1 or (len(tail) == 3 and head.strip("0"))):
        return float(head + tail)
    return float(f"{head}.{tail}")


def parse_price_range(text: str | None) -> tuple[float, float, str] | None:
    """"0,0381-0,0623 PLN" -> (0.0381, 0.0623, "PLN")."""
    if not text or not (currency := currency_of(text)):
        return None
    values = [parse_number(n) for n in re.findall(NUMBER, text)]
    return (min(values), max(values), currency) if values else None


def parse_moq(text: str | None) -> tuple[int, str] | None:
    """"Min. order: 5 pieces" -> (5, "pieces")."""
    if not text or not (m := re.search(r"(\d[\d.,]*)\s*([^\d\s][^\n]*)?", text.split(":")[-1])):
        return None
    return int(re.sub(r"[.,\s]", "", m.group(1))), (m.group(2) or "").strip()


def parse_tiers(text: str | None) -> list[dict]:
    """Sekcja ceny ze strony oferty: na zmianę linia z ceną i linia z ilością."""
    tiers, lines = [], [line.strip() for line in (text or "").splitlines() if line.strip()]
    for price_line, qty_line in zip(lines, lines[1:]):
        currency = currency_of(price_line)
        qty = re.match(r"^(?:≥|>=)?\s*(\d[\d.,]*)", qty_line)
        if not currency or not qty or currency_of(qty_line):
            continue
        number = re.search(NUMBER, price_line)
        if number:
            tiers.append({"min_qty": int(re.sub(r"[.,]", "", qty.group(1))),
                          "price": parse_number(number.group()),
                          "currency": currency,
                          "unit": re.sub(r"^\s*[-–]\s*\d[\d.,]*", "", qty_line[qty.end():]).strip()})
    return sorted(tiers, key=lambda t: t["min_qty"])


_rates: dict[str, tuple[float, float]] = {}


def pln_rate(currency: str) -> float:
    """Średni kurs NBP (tabela A), odświeżany raz na dobę."""
    if currency == "PLN":
        return 1.0
    cached = _rates.get(currency)
    if cached and time.time() - cached[1] < 86400:
        return cached[0]
    response = httpx.get(f"https://api.nbp.pl/api/exchangerates/rates/a/{currency.lower()}/?format=json", timeout=15)
    response.raise_for_status()
    rate = float(response.json()["rates"][0]["mid"])
    _rates[currency] = (rate, time.time())
    return rate
