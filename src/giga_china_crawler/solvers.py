"""Jedyny solver w kontenerze: gest suwaka Alibaby (bez zewnętrznych usług i katalogu vendor/)."""

from giga_china_crawler.actions import SLIDER_HANDLE, drag_slider_once


async def slider_gesture(found: dict, page, env: dict) -> dict:
    for frame in list(getattr(page, "frames", ()) or ()) + [page]:
        try:
            handle = frame.locator(SLIDER_HANDLE)
            if not await handle.is_visible():
                continue
            if await drag_slider_once(page, frame):
                return {"solved": True, "detail": "gest suwaka Alibaba"}
        except Exception:
            continue
    return {"solved": False, "detail": "brak widocznego suwaka #nc_1_n1z"}


ADAPTERS = {"alibaba-slider": slider_gesture}
