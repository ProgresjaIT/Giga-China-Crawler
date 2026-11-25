"""Made-in-China.com: wyszukiwanie tytułem i odczyt ceny oraz MOQ z oferty."""

from urllib.parse import quote

from lxml import html

from giga_china_crawler.browser import wait_for

NAME = "Made-in-China.com"
CARD = ".prod-list .products-item, .prod-list .list-node"
SEARCH_URL = ("https://www.made-in-china.com/productdirectory.do?subaction=hunt&style=b&mode=and&code=0"
              "&comProvince=nolimit&order=0&isOpenCorrection=1&org=top&searchType=0&word=")


def search_url(term: str) -> str:
    return SEARCH_URL + quote(term, safe="")


def _first_text(node, *selectors) -> str | None:
    for selector in selectors:
        found = node.cssselect(selector)
        if found:
            return " ".join(found[0].text_content().split()) or None
    return None


def _first_image(node) -> str | None:
    for selector, attribute in (("img[data-original]", "data-original"),
                                ("img[data-src]", "data-src"), ("img.img-shadow", "src")):
        found = node.cssselect(".prod-img .img-list .img-wrap " + selector)
        if found:
            return found[0].get(attribute)
    return None


def extract_offers(markup: str) -> list[dict]:
    offers = []
    for card in html.fromstring(markup).cssselect(CARD):
        links = card.cssselect("h2.product-name a")
        title = _first_text(card, "h2.product-name a")
        if not links or not title:
            continue
        moq = _first_text(card, ".product-property .moq-new .attribute",
                          ".product-property > div.info:not(.price-info)")
        offers.append({
            "source": NAME,
            "title": title,
            "url": links[0].get("href"),
            "image_url": _first_image(card),
            "price_text": _first_text(card, ".product-property .price-new .attribute",
                                      ".product-property .price-info strong.price"),
            "moq_text": moq.replace("(MOQ)", "").strip() if moq else None,
            "supplier": _first_text(card, ".company-info > .company-name > a.compnay-name",
                                    ".company-name-txt > a.compnay-name"),
        })
    return offers


async def _collect(session, url: str, notify, selector: str) -> str | None:
    markup = {}

    async def action(page):
        if await wait_for(page, selector, notify):
            await page.wait_for_timeout(800)
            markup["html"] = await page.content()

    await session.fetch(url, page_action=action, google_search=False, timeout=60000)
    return markup.get("html")


async def search(session, term: str, notify) -> list[dict]:
    markup = await _collect(session, search_url(term), notify, CARD)
    return extract_offers(markup) if markup else []


async def details(session, url: str, notify) -> dict:
    markup = await _collect(session, url, notify, ".only-one-priceNum-td-left")
    if not markup:
        return {}
    doc = html.fromstring(markup)

    def text(*selectors):
        for selector in selectors:
            nodes = doc.cssselect(selector)
            if nodes:
                return " ".join(nodes[0].text_content().split()) or None
        return None

    return {
        "title": text("h1.sr-proMainInfo-baseInfoH1"),
        "price_text": text(".only-one-priceNum-td-left"),
        "moq_text": (text(".only-one-priceNum-price") or "").replace("(MOQ)", "").strip() or None,
        "supplier": text("a.sr-comInfo-title-review", "a.sr-comInfo-title", ".sr-com-info a"),
    }
