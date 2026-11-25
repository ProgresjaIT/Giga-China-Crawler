"""Ludzki gest przeciągnięcia suwaka Alibaby."""

import asyncio
import math
import random

_CURSOR = None

SLIDER_HANDLE = "#nc_1_n1z"
SLIDER_TRACK = "#nc_1_n1t"


def _min_jerk(pos: float) -> float:
    """Profil o zerowej prędkości i zerowym przyspieszeniu na krańcach."""
    return pos * pos * pos * (pos * (pos * 6.0 - 15.0) + 10.0)


async def _rest(rng: random.Random, lo: float, hi: float) -> None:
    await asyncio.sleep(rng.uniform(lo, hi))


async def _approach(page, rng: random.Random, x: float, y: float) -> None:
    """Dojdź do uchwytu łukiem i zawieś nad nim palec zanim chwyci."""
    global _CURSOR
    if _CURSOR is None:
        sx, sy = x + rng.uniform(-180, -50), y + rng.uniform(30, 200)
    else:
        sx, sy = _CURSOR
    dist = math.hypot(x - sx, y - sy)
    if dist < 8.0:
        sx, sy = x - rng.uniform(40, 120), y + rng.uniform(30, 140)
        dist = math.hypot(x - sx, y - sy)

    bow = rng.uniform(-0.3, 0.3)
    cx = (sx + x) / 2 - (y - sy) * bow
    cy = (sy + y) / 2 + (x - sx) * bow

    steps = int(max(8, min(42, dist / rng.uniform(8.0, 16.0))))
    for i in range(1, steps + 1):
        u = _min_jerk(i / steps)
        v = 1.0 - u
        px = v * v * sx + 2.0 * v * u * cx + u * u * x
        py = v * v * sy + 2.0 * v * u * cy + u * u * y
        await page.mouse.move(px + rng.gauss(0, 0.6), py + rng.gauss(0, 0.6))
        _CURSOR = (px, py)
        await asyncio.sleep(rng.uniform(0.008, 0.026))

    await _rest(rng, 0.05, 0.15)
    for _ in range(rng.randint(2, 4)):
        await page.mouse.move(x + rng.gauss(0, 1.3), y + rng.gauss(0, 1.3))
        await _rest(rng, 0.02, 0.07)
    await page.mouse.move(x, y)
    _CURSOR = (x, y)
    await _rest(rng, 0.08, 0.22)


async def _drag(page, rng: random.Random, x: float, y: float, travel: float) -> None:
    """Prowadź uchwyt jednym ciągłym ruchem w prawo; prędkość zmienia się, kierunek nie."""
    global _CURSOR
    steps = int(max(28, min(110, travel / rng.uniform(3.5, 6.5))))

    vf1 = rng.uniform(1.2, 2.4)
    af1 = rng.uniform(0.12, 0.28)
    vf2 = rng.uniform(3.0, 6.0)
    af2 = rng.uniform(0.04, 0.12)
    ph1 = rng.random() * math.tau
    ph2 = rng.random() * math.tau

    vel = []
    for i in range(steps):
        u = (i + 1) / steps
        base = 0.3 + 0.7 * math.sin(math.pi * u)
        mod = 1.0 + af1 * math.sin(u * math.tau * vf1 + ph1) \
                  + af2 * math.sin(u * math.tau * vf2 + ph2)
        vel.append(max(0.05, base * mod))
    total = sum(vel)

    positions = []
    cum = 0.0
    for v in vel:
        cum += v
        positions.append(travel * cum / total)

    wave_f = rng.uniform(0.7, 1.6)
    wave_a = rng.uniform(0.8, 2.2)
    wave_p = rng.random() * math.tau
    drift = rng.uniform(-1.5, 1.5)

    pauses = {rng.randint(int(steps * 0.3), int(steps * 0.6))}
    if rng.random() < 0.5:
        pauses.add(rng.randint(int(steps * 0.65), int(steps * 0.85)))

    for i, pos in enumerate(positions):
        u = (i + 1) / steps
        cy = y + math.sin(u * math.tau * wave_f + wave_p) * wave_a + u * drift \
             + rng.gauss(0, 0.3)
        cx = x + pos + rng.gauss(0, 0.35)
        await page.mouse.move(cx, cy)
        _CURSOR = (cx, cy)
        if i in pauses:
            await _rest(rng, 0.06, 0.2)
            await page.mouse.move(cx, cy + rng.gauss(0, 0.8))
            _CURSOR = (cx, cy)
            await _rest(rng, 0.03, 0.1)
        else:
            await asyncio.sleep(rng.uniform(0.007, 0.022))

    settle = x + travel
    await _rest(rng, 0.05, 0.14)
    await page.mouse.move(settle, y)
    _CURSOR = (settle, y)
    await _rest(rng, 0.09, 0.28)


async def _release(page, rng: random.Random, x: float, y: float) -> None:
    """Puść uchwyt i oddal kursor tak, jak robi to dłoń po geście."""
    global _CURSOR
    tx = x + rng.uniform(-50, 50)
    ty = y + rng.uniform(-35, 55)
    steps = rng.randint(3, 7)
    for i in range(1, steps + 1):
        u = _min_jerk(i / steps)
        await page.mouse.move(
            x + (tx - x) * u + rng.gauss(0, 0.7),
            y + (ty - y) * u + rng.gauss(0, 0.7),
        )
        _CURSOR = (tx, ty)
        await asyncio.sleep(rng.uniform(0.01, 0.032))


async def drag_slider_once(page, frame, handle_selector=SLIDER_HANDLE,
                           track_selector=SLIDER_TRACK) -> bool:
    handle, track = frame.locator(handle_selector), frame.locator(track_selector)
    if not await handle.is_visible() or not await track.is_visible():
        return False
    h, t = await handle.bounding_box(), await track.bounding_box()
    if not h or not t:
        return False
    x, y = h["x"] + h["width"] / 2, h["y"] + h["height"] / 2
    travel = t["x"] + t["width"] - h["width"] / 2 - x
    if travel <= 0:
        return False

    rng = random.Random()
    await _approach(page, rng, x, y)
    await page.mouse.down()
    try:
        await _drag(page, rng, x, y, travel)
    finally:
        await page.mouse.up()
    await _rest(rng, 0.06, 0.2)
    await _release(page, rng, _CURSOR[0], _CURSOR[1])
    return True
