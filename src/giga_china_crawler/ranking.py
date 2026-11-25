"""Trzy listy wyników: najniższa cena, najniższe MOQ, najniższy koszt pierwszego zamówienia."""

from giga_china_crawler.money import parse_moq, parse_price_range, pln_rate


def price_offer(offer: dict) -> dict:
    """Dopisuje do oferty ceny w PLN. Progi ze strony oferty mają pierwszeństwo przed widełkami z listy."""
    tiers = offer.get("tiers") or []
    if tiers:
        rate = pln_rate(tiers[0]["currency"])
        cheapest, first = min(tiers, key=lambda t: t["price"]), tiers[0]
        moq = offer.get("moq") or (first["min_qty"], first["unit"])
        offer |= {"original_currency": first["currency"],
                  "unit_price_pln": round(cheapest["price"] * rate, 4), "qty_for_unit_price": cheapest["min_qty"],
                  "price_at_moq_pln": round(first["price"] * rate, 4)}
    else:
        price = parse_price_range(offer.get("price_text"))
        moq = offer.get("moq") or parse_moq(offer.get("moq_text"))
        if price:
            low, high, currency = price
            rate = pln_rate(currency)
            # Bez progów najwyższa cena z widełek dotyczy najmniejszej ilości, najniższa największej.
            offer |= {"original_currency": currency, "unit_price_pln": round(low * rate, 4),
                      "qty_for_unit_price": None, "price_at_moq_pln": round(high * rate, 4)}
    if moq:
        offer["moq"], offer["moq_unit"] = moq[0], moq[1]
        if offer.get("price_at_moq_pln") is not None:
            offer["order_value_pln"] = round(moq[0] * offer["price_at_moq_pln"], 2)
    return offer


def three_lists(offers: list[dict]) -> dict[str, list[dict]]:
    def by(key):
        return sorted((o for o in offers if o.get(key) is not None), key=lambda o: o[key])
    return {"cheapest": by("unit_price_pln"), "lowest_moq": by("moq"), "lowest_order_value": by("order_value_pln")}
