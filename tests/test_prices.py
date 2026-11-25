import unittest
from unittest import mock

from giga_china_crawler import money
from giga_china_crawler.money import parse_moq, parse_number, parse_price_range, parse_tiers
from giga_china_crawler.ranking import price_offer, three_lists

PRICE_SECTION = "1.132,63 PLN\n2-9 pieces\n1.053,15 PLN\n10-99 pieces\n973,67 PLN\n100-499 pieces\n794,83 PLN\n≥500 pieces\nEdit selections\nPackage / Case\nPC"


class Prices(unittest.TestCase):
    def test_numbers(self):
        for text, value in [("1.132,63", 1132.63), ("1,132.63", 1132.63), ("0,0381", 0.0381), ("42.582", 42582),
                            ("1.50", 1.5), ("1,00", 1.0), ("0.125", 0.125), ("1,000", 1000), ("12", 12),
                            ("42.582,74", 42582.74), ("1.234.567", 1234567)]:
            self.assertEqual(parse_number(text), value, text)

    def test_range_and_moq(self):
        self.assertEqual(parse_price_range("0,0381-0,0623 PLN"), (0.0381, 0.0623, "PLN"))
        self.assertEqual(parse_price_range("US$1.20-3.50"), (1.2, 3.5, "USD"))
        self.assertIsNone(parse_price_range("Contact supplier"))
        self.assertEqual(parse_moq("Min. order: 5 pieces"), (5, "pieces"))
        self.assertEqual(parse_moq("Min. order: 1,000 sets"), (1000, "sets"))

    def test_tiers(self):
        tiers = parse_tiers(PRICE_SECTION)
        self.assertEqual([(t["min_qty"], t["price"], t["unit"]) for t in tiers],
                         [(2, 1132.63, "pieces"), (10, 1053.15, "pieces"), (100, 973.67, "pieces"), (500, 794.83, "pieces")])

    def test_three_lists(self):
        with mock.patch.object(money, "pln_rate", return_value=4.0), \
             mock.patch("giga_china_crawler.ranking.pln_rate", return_value=4.0):
            a = price_offer({"tiers": parse_tiers("1,00 USD\n100-999 pieces\n0,50 USD\n≥1000 pieces")})
            b = price_offer({"price_text": "US$0.80-1.20", "moq_text": "Min. order: 10 pieces"})
        self.assertEqual((a["unit_price_pln"], a["qty_for_unit_price"], a["moq"], a["order_value_pln"]), (2.0, 1000, 100, 400.0))
        self.assertEqual((b["unit_price_pln"], b["moq"], b["order_value_pln"]), (3.2, 10, 48.0))
        lists = three_lists([a, b, {"title": "bez ceny"}])
        self.assertEqual(lists["cheapest"], [a, b])
        self.assertEqual(lists["lowest_moq"], [b, a])
        self.assertEqual(lists["lowest_order_value"], [b, a])


if __name__ == "__main__":
    unittest.main()
