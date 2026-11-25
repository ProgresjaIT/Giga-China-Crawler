import unittest
from unittest.mock import patch

from giga_china_crawler import pipeline, ranking
from giga_china_crawler.ranking import price_offer
from giga_china_crawler.sources import made_in_china

MARKUP = """
<div class="prod-list"><div class="list-img"><div class="list-img-wrap">
  <div class="products-item">
    <div class="prod-img"><div class="img-list"><div class="img-wrap">
      <img data-original="https://image.made-in-china.com/hammer.webp">
    </div></div></div>
    <h2 class="product-name"><a href="https://x.en.made-in-china.com/product/abc/China-Hammer.html">Claw <strong>Hammer</strong></a></h2>
    <div class="product-property">
      <div class="price-new"><span class="attribute">US$1.12-1.46</span></div>
      <div class="moq-new"><span class="attribute">500 Pieces</span></div>
    </div>
    <div class="company-info"><div class="company-name"><a class="compnay-name">Tuopu Hardware</a></div></div>
  </div>
</div></div></div>
"""


DYNAMIC_MARKUP = """
<div class="prod-list"><div class="list-node">
  <div class="prod-img"><div class="img-list"><div class="img-wrap">
    <img class="img-shadow" src="https://image.made-in-china.com/hammer.jpg">
  </div></div></div>
  <h2 class="product-name"><a href="https://x.en.made-in-china.com/product/abc/China-Hammer.html">Claw <strong>Hammer</strong></a></h2>
  <div class="product-property">
    <div class="price-info"><strong class="price">US$50.00-200.00</strong></div>
    <div class="info">1 Piece (MOQ)</div>
  </div>
  <div class="company-name-txt"><a class="compnay-name">Chaojingang Machinery</a></div>
</div></div>
"""


class MadeInChinaTests(unittest.TestCase):
    def test_search_url_encodes_polish_term(self):
        self.assertIn("word=m%C5%82otki", made_in_china.search_url("młotki"))

    def test_extract_offers(self):
        offers = made_in_china.extract_offers(MARKUP)
        self.assertEqual(len(offers), 1)
        self.assertEqual(offers[0]["title"], "Claw Hammer")
        self.assertEqual(offers[0]["price_text"], "US$1.12-1.46")
        self.assertEqual(offers[0]["moq_text"], "500 Pieces")
        self.assertEqual(offers[0]["supplier"], "Tuopu Hardware")
        with patch.object(ranking, "pln_rate", return_value=4.0):
            price_offer(offers[0])
        self.assertEqual(offers[0]["moq"], 500)
        self.assertEqual(offers[0]["moq_unit"], "Pieces")

    def test_extract_dynamic_search_offers(self):
        offers = made_in_china.extract_offers(DYNAMIC_MARKUP)
        self.assertEqual(len(offers), 1)
        self.assertEqual(offers[0]["title"], "Claw Hammer")
        self.assertEqual(offers[0]["price_text"], "US$50.00-200.00")
        self.assertEqual(offers[0]["moq_text"], "1 Piece")
        self.assertEqual(offers[0]["supplier"], "Chaojingang Machinery")
        self.assertEqual(offers[0]["image_url"], "https://image.made-in-china.com/hammer.jpg")

    def test_source_registered(self):
        self.assertIn(made_in_china, pipeline.SOURCES)


if __name__ == "__main__":
    unittest.main()
