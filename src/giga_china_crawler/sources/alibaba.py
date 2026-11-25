"""Alibaba.com: wyszukiwanie tytułem i zdjęciem, progi cenowe ze strony oferty."""

import tempfile
from urllib.parse import urlencode, urljoin, urlsplit, urlunsplit

from lxml import html

from giga_china_crawler.browser import wait_for
from giga_china_crawler.money import parse_tiers

NAME = "Alibaba.com"
CARD = ".fy26-product-card"
IMAGE_SEARCH_BUTTON = ".header-tab-switch-image-upload-multi"


def extract_offers(markup: str) -> list[dict]:
    """Karty z listy wyników; brakujące pola zostają puste."""
    offers = []
    for card in html.fromstring(markup).cssselect(CARD):
        def text(selector):
            nodes = card.cssselect(selector)
            return " ".join(nodes[0].text_content().split()) if nodes else None
        links, title = card.cssselect('a[href*="/product-detail/"]'), text("h2.searchx-product-e-title")
        if not links or not title:
            continue
        url = urlsplit(urljoin("https://www.alibaba.com", links[0].get("href")))
        if url.hostname != "www.alibaba.com":
            continue
        images = card.cssselect("img.searchx-product-e-slider__img")
        image = urljoin("https:", images[0].get("src") or images[0].get("data-src") or "") if images else None
        offers.append({
            "source": NAME, "title": title, "url": urlunsplit(("https", url.netloc, url.path, "", "")),
            "image_url": image if image and image.startswith("https://") else None,
            "price_text": text(".searchx-product-price-price-main"), "moq_text": text(".searchx-moq"),
            "supplier": text(".searchx-product-e-company"), "supplier_years": text(".searchx-product-e-supplier__year"),
            "rating": text(".searchx-review-score"),
        })
    return offers


async def _collect(session, url: str, notify, before=None) -> list[dict]:
    markup = {}

    async def action(page):
        if before:
            await before(page)
        if await wait_for(page, CARD, notify):
            await page.wait_for_timeout(1500)  # karty doładowują ceny chwilę po pojawieniu się
            markup["html"] = await page.content()

    await session.fetch(url, page_action=action, google_search=False, timeout=60000)
    return extract_offers(markup["html"]) if "html" in markup else []


async def search(session, term: str, notify) -> list[dict]:
    return await _collect(session, "https://www.alibaba.com/trade/search?" + urlencode({"SearchText": term}), notify)


async def search_image(session, image: tuple[bytes, str], notify) -> list[dict]:
    suffix = "." + image[1].split("/")[-1].replace("jpeg", "jpg")
    with tempfile.NamedTemporaryFile(suffix=suffix) as file:
        file.write(image[0])
        file.flush()

        async def upload(page):
            await page.locator(IMAGE_SEARCH_BUTTON).first.wait_for(timeout=20000)
            async with page.expect_file_chooser() as chooser:
                await page.locator(IMAGE_SEARCH_BUTTON).first.click()
            await (await chooser.value).set_files(file.name)

        return await _collect(session, "https://www.alibaba.com/", notify, before=upload)


async def details(session, url: str, notify) -> dict:
    """Progi cenowe i MOQ ze strony oferty."""
    found = {}

    async def action(page):
        if await wait_for(page, ".module_price", notify):
            found["price"] = await page.locator(".module_price").first.inner_text()

    await session.fetch(url, page_action=action, google_search=False, timeout=60000)
    tiers = parse_tiers(found.get("price"))
    if not tiers:
        return {}
    return {"tiers": tiers, "moq": (tiers[0]["min_qty"], tiers[0]["unit"])}
