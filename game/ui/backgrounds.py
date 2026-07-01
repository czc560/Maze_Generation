"""Theme background render helpers for game scenes."""

from __future__ import annotations

import math
import random
import pygame


_BG_CACHE: dict[tuple[str, int, int], pygame.Surface] = {}


def get_background(name: str, size: tuple[int, int]) -> pygame.Surface:
    key = (name, size[0], size[1])
    cached = _BG_CACHE.get(key)
    if cached is not None:
        return cached
    surface = pygame.Surface(size).convert()
    if name == "config":
        _draw_config(surface)
    elif name == "strategy":
        _draw_strategy(surface)
    elif name == "boss":
        _draw_boss(surface)
    elif name == "results":
        _draw_results(surface)
    elif name == "gameplay":
        _draw_gameplay(surface)
    else:
        _draw_base(surface, (12, 14, 20), (22, 25, 32))
    _BG_CACHE[key] = surface
    return surface


def draw_background(target: pygame.Surface, name: str) -> None:
    bg = get_background(name, target.get_size())
    target.blit(bg, (0, 0))


def _draw_base(surface: pygame.Surface, top: tuple[int, int, int], bottom: tuple[int, int, int]) -> None:
    w, h = surface.get_size()
    for y in range(h):
        t = y / max(1, h - 1)
        color = tuple(round(a + (b - a) * t) for a, b in zip(top, bottom))
        pygame.draw.line(surface, color, (0, y), (w, y))


def _draw_vignette(surface: pygame.Surface, strength: int = 120) -> None:
    w, h = surface.get_size()
    overlay = pygame.Surface((w, h), pygame.SRCALPHA)
    center = (w * 0.5, h * 0.46)
    max_d = math.hypot(center[0], center[1])
    step = 10
    for y in range(0, h, step):
        for x in range(0, w, step):
            d = math.hypot(x - center[0], y - center[1]) / max_d
            alpha = max(0, min(strength, int((d ** 1.7) * strength)))
            pygame.draw.rect(overlay, (0, 0, 0, alpha), (x, y, step, step))
    surface.blit(overlay, (0, 0))


def _draw_config(surface: pygame.Surface) -> None:
    w, h = surface.get_size()
    _draw_base(surface, (18, 22, 28), (29, 25, 22))
    grid = 32
    for x in range(0, w, grid):
        color = (72, 90, 104) if x % (grid * 4) == 0 else (45, 56, 66)
        pygame.draw.line(surface, color, (x, 0), (x, h), 1)
    for y in range(0, h, grid):
        color = (72, 90, 104) if y % (grid * 4) == 0 else (45, 56, 66)
        pygame.draw.line(surface, color, (0, y), (w, y), 1)

    blueprint = pygame.Surface((w, h), pygame.SRCALPHA)
    rng = random.Random(7)
    for i in range(11):
        x = 70 + i * 82
        y = 130 + (i % 3) * 54
        rect = pygame.Rect(x, y, rng.choice((84, 116, 148)), rng.choice((44, 76, 108)))
        pygame.draw.rect(blueprint, (122, 202, 255, 74), rect, width=2, border_radius=3)
        if i % 2 == 0:
            pygame.draw.line(blueprint, (255, 210, 102, 82), rect.midleft, rect.midright, 2)
    pygame.draw.arc(blueprint, (122, 202, 255, 62), (w - 330, 120, 230, 230), 0.2, 5.4, 3)
    pygame.draw.line(blueprint, (255, 210, 102, 70), (w - 320, 420), (w - 90, 210), 3)
    surface.blit(blueprint, (0, 0))
    _draw_vignette(surface, 110)


def _draw_strategy(surface: pygame.Surface) -> None:
    w, h = surface.get_size()
    _draw_base(surface, (10, 14, 20), (18, 24, 31))
    rng = random.Random(12)
    for x in range(0, w, 28):
        pygame.draw.line(surface, (26, 44, 52), (x, 0), (x, h), 1)
    for y in range(0, h, 28):
        pygame.draw.line(surface, (22, 36, 44), (0, y), (w, y), 1)

    code = pygame.Surface((w, h), pygame.SRCALPHA)
    for row in range(16):
        y = 96 + row * 30
        x = 88 + (row % 4) * 18
        pygame.draw.rect(code, (47, 214, 156, 58), (x, y, rng.randrange(130, 360), 5), border_radius=3)
        pygame.draw.rect(code, (97, 142, 255, 42), (x + 28, y + 12, rng.randrange(90, 280), 4), border_radius=2)
    for i in range(7):
        cx = w - 260 + int(math.cos(i * 1.7) * 130)
        cy = 160 + i * 62
        pygame.draw.circle(code, (255, 210, 104, 86), (cx, cy), 6)
        if i:
            px = w - 260 + int(math.cos((i - 1) * 1.7) * 130)
            py = 160 + (i - 1) * 62
            pygame.draw.line(code, (91, 174, 255, 46), (px, py), (cx, cy), 2)
    surface.blit(code, (0, 0))
    _draw_vignette(surface, 120)


def _draw_boss(surface: pygame.Surface) -> None:
    w, h = surface.get_size()
    # Bright pastoral pixel-art arena: sky, hills, meadow, flowers, and tile plaza.
    for y in range(h):
        t = y / max(1, h - 1)
        if y < h * 0.58:
            sky_t = y / (h * 0.58)
            color = (
                round(104 + 64 * sky_t),
                round(190 + 34 * sky_t),
                round(255 - 35 * sky_t),
            )
        else:
            grass_t = (y - h * 0.58) / (h * 0.42)
            color = (
                round(82 - 18 * grass_t),
                round(184 - 38 * grass_t),
                round(74 - 20 * grass_t),
            )
        pygame.draw.line(surface, color, (0, y), (w, y))

    # Pixel sun and clouds.
    pygame.draw.rect(surface, (255, 226, 90), (92, 62, 82, 82))
    pygame.draw.rect(surface, (255, 240, 138), (108, 78, 50, 50))
    for cloud in ((310, 78), (840, 92), (1050, 56)):
        cx, cy = cloud
        for rect in ((0, 18, 84, 24), (22, 0, 52, 42), (62, 10, 64, 32), (-38, 14, 54, 28)):
            pygame.draw.rect(surface, (245, 253, 255), (cx + rect[0], cy + rect[1], rect[2], rect[3]))
            pygame.draw.rect(surface, (205, 231, 237), (cx + rect[0], cy + rect[1] + rect[3] - 5, rect[2], 5))

    # Blocky far hills.
    for base_y, color, step in ((390, (87, 176, 91), 70), (438, (64, 151, 82), 90)):
        points = [(-80, base_y)]
        for x in range(-80, w + 160, step):
            points.append((x + step // 2, base_y - (36 if (x // step) % 2 == 0 else 58)))
            points.append((x + step, base_y))
        points.extend([(w + 120, h), (-120, h)])
        pygame.draw.polygon(surface, color, points)

    # Meadow checker tiles around the arena.
    tile = 34
    for y in range(430, h, tile):
        for x in range(0, w, tile):
            c = (92, 178, 78) if ((x // tile + y // tile) % 2 == 0) else (105, 195, 84)
            pygame.draw.rect(surface, c, (x, y, tile, tile))
            pygame.draw.rect(surface, (69, 142, 66), (x, y, tile, tile), width=1)

    # Flowers and shrubs, deterministic.
    rng = random.Random(41)
    flower_colors = [(255, 116, 148), (255, 218, 92), (132, 106, 255), (255, 255, 255)]
    for _ in range(90):
        x = rng.randrange(18, w - 18)
        y = rng.randrange(468, h - 16)
        pygame.draw.rect(surface, (45, 124, 55), (x, y + 5, 3, 8))
        color = rng.choice(flower_colors)
        pygame.draw.rect(surface, color, (x - 4, y, 5, 5))
        pygame.draw.rect(surface, color, (x + 2, y, 5, 5))
        pygame.draw.rect(surface, (255, 235, 95), (x, y + 2, 3, 3))

    plaza = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.ellipse(plaza, (233, 207, 142, 210), (w // 2 - 420, 304, 840, 236))
    pygame.draw.ellipse(plaza, (160, 118, 76, 80), (w // 2 - 420, 304, 840, 236), width=4)
    pygame.draw.ellipse(plaza, (255, 250, 204, 92), (w // 2 - 310, 330, 620, 156), width=3)
    surface.blit(plaza, (0, 0))

    # Gentle readable edge shading.
    shade = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(shade, (255, 255, 255, 34), (0, 0, w, 118))
    pygame.draw.rect(shade, (35, 73, 45, 58), (0, h - 120, w, 120))
    surface.blit(shade, (0, 0))


def _draw_results(surface: pygame.Surface) -> None:
    w, h = surface.get_size()
    _draw_base(surface, (13, 19, 22), (24, 24, 20))
    glow = pygame.Surface((w, h), pygame.SRCALPHA)
    for i in range(9):
        alpha = max(8, 70 - i * 7)
        pygame.draw.ellipse(glow, (255, 213, 98, alpha), (w // 2 - 130 - i * 46, 18 - i * 22, 260 + i * 92, 150 + i * 44), width=3)
    for x in range(100, w, 140):
        pygame.draw.line(glow, (118, 146, 120, 40), (x, 100), (x - 80, h), 2)
    for y in range(170, h, 72):
        pygame.draw.line(glow, (255, 255, 255, 18), (0, y), (w, y), 1)
    surface.blit(glow, (0, 0))
    _draw_vignette(surface, 120)


def _draw_gameplay(surface: pygame.Surface) -> None:
    w, h = surface.get_size()
    _draw_base(surface, (13, 15, 20), (22, 21, 22))
    rng = random.Random(22)
    for y in range(0, h, 34):
        offset = 0 if (y // 34) % 2 == 0 else 42
        for x in range(-offset, w, 84):
            color = 28 + rng.randrange(10)
            pygame.draw.rect(surface, (color, color + 3, color + 7), (x, y, 82, 32), border_radius=2)
            pygame.draw.rect(surface, (8, 10, 14), (x, y, 82, 32), width=1, border_radius=2)
    haze = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.ellipse(haze, (75, 126, 148, 32), (-160, 70, 760, 520))
    pygame.draw.ellipse(haze, (210, 170, 78, 24), (760, 20, 620, 440))
    surface.blit(haze, (0, 0))
    _draw_vignette(surface, 96)
