"""Build pygame UI assets."""

from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
SPRITES = ROOT / "game" / "assets" / "sprites"

CUSTOM_SPRITES = {
    "玩家.png": "player.png",
    "金币.png": "coin.png",
    "陷阱.png": "trap.png",
    "墙.png": "wall.png",
    "地板.png": "floor.png",
    "boss.png": "boss.png",
}


def _lerp(a: int, b: int, t: float) -> int:
    return round(a + (b - a) * t)


def _blend(c1: tuple[int, int, int], c2: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return tuple(_lerp(a, b, t) for a, b in zip(c1, c2))


def _make_maze(cols: int, rows: int, seed: int = 17) -> tuple[list[list[int]], list[tuple[int, int]]]:
    rng = random.Random(seed)
    grid_w, grid_h = cols * 2 + 1, rows * 2 + 1
    grid = [[1 for _ in range(grid_w)] for _ in range(grid_h)]
    stack = [(0, 0)]
    seen = {(0, 0)}
    grid[1][1] = 0
    parent: dict[tuple[int, int], tuple[int, int]] = {}

    while stack:
        cx, cy = stack[-1]
        choices = []
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < cols and 0 <= ny < rows and (nx, ny) not in seen:
                choices.append((nx, ny, dx, dy))
        if not choices:
            stack.pop()
            continue
        nx, ny, dx, dy = rng.choice(choices)
        seen.add((nx, ny))
        parent[(nx, ny)] = (cx, cy)
        grid[cy * 2 + 1 + dy][cx * 2 + 1 + dx] = 0
        grid[ny * 2 + 1][nx * 2 + 1] = 0
        stack.append((nx, ny))

    end = (cols - 1, rows - 1)
    route_cells = [end]
    while route_cells[-1] != (0, 0):
        route_cells.append(parent[route_cells[-1]])
    route_cells.reverse()
    route = [(x * 2 + 1, y * 2 + 1) for x, y in route_cells]
    return grid, route


def build_menu_backdrop(width: int = 1280, height: int = 720) -> Image.Image:
    img = Image.new("RGB", (width, height), (9, 12, 18))
    px = img.load()
    top = (9, 13, 20)
    bottom = (20, 24, 30)
    for y in range(height):
        t = y / max(1, height - 1)
        row = _blend(top, bottom, t)
        for x in range(width):
            glow = max(0.0, 1.0 - math.hypot((x - 980) / 700, (y - 340) / 420))
            cool = int(24 * glow)
            px[x, y] = (row[0] + cool // 4, row[1] + cool // 2, row[2] + cool)

    draw = ImageDraw.Draw(img, "RGBA")
    rng = random.Random(29)
    for _ in range(700):
        x = rng.randrange(width)
        y = rng.randrange(height)
        alpha = rng.randrange(10, 36)
        draw.point((x, y), fill=(150, 185, 210, alpha))

    grid, route = _make_maze(22, 13)
    cell = 28
    ox, oy = 520, 98
    wall = (38, 46, 58, 210)
    wall_hi = (88, 103, 121, 82)
    floor = (25, 33, 43, 170)
    for gy, row in enumerate(grid):
        for gx, value in enumerate(row):
            x0 = ox + gx * cell
            y0 = oy + gy * cell
            if x0 > width or y0 > height:
                continue
            jitter = (gx * 13 + gy * 7) % 12
            if value:
                draw.rounded_rectangle(
                    (x0 + 2, y0 + 2, x0 + cell - 3, y0 + cell - 3),
                    radius=4,
                    fill=(wall[0] + jitter, wall[1] + jitter, wall[2] + jitter, wall[3]),
                    outline=wall_hi,
                    width=1,
                )
            else:
                draw.rectangle((x0 + 3, y0 + 3, x0 + cell - 4, y0 + cell - 4), fill=floor)

    points = [(ox + gx * cell + cell // 2, oy + gy * cell + cell // 2) for gx, gy in route]
    if len(points) > 1:
        glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow, "RGBA")
        gd.line(points, fill=(66, 205, 255, 120), width=13, joint="curve")
        glow = glow.filter(ImageFilter.GaussianBlur(8))
        img = Image.alpha_composite(img.convert("RGBA"), glow)
        draw = ImageDraw.Draw(img, "RGBA")
        draw.line(points, fill=(255, 207, 92, 230), width=4, joint="curve")
        for p in (points[0], points[-1]):
            draw.ellipse((p[0] - 9, p[1] - 9, p[0] + 9, p[1] + 9), fill=(255, 231, 146, 235))

    vignette = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    vd = ImageDraw.Draw(vignette, "RGBA")
    for i in range(180):
        alpha = int(i * 0.72)
        vd.rectangle((i, i, width - i, height - i), outline=(0, 0, 0, max(0, 130 - alpha // 2)))
    vd.rectangle((0, 0, 500, height), fill=(2, 5, 10, 118))
    vd.rectangle((0, 0, width, 90), fill=(0, 0, 0, 44))
    vd.rectangle((0, height - 120, width, height), fill=(0, 0, 0, 58))
    img = Image.alpha_composite(img.convert("RGBA"), vignette)
    return img.convert("RGBA")


def make_portal(size: int, color: tuple[int, int, int]) -> Image.Image:
    icon = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(icon, "RGBA")
    center = size // 2
    for i in range(7, 0, -1):
        pad = size // 2 - i * size // 16
        alpha = 28 + i * 22
        draw.ellipse((pad, pad, size - pad, size - pad), outline=color + (alpha,), width=max(2, size // 30))
    draw.ellipse((size * 3 // 8, size * 3 // 8, size * 5 // 8, size * 5 // 8), fill=color + (230,))
    draw.ellipse((center - 5, center - 5, center + 5, center + 5), fill=(255, 255, 255, 220))
    return icon


def copy_custom_sprites() -> None:
    for source_name, target_name in CUSTOM_SPRITES.items():
        source_path = ROOT / source_name
        if source_path.exists():
            Image.open(source_path).save(SPRITES / target_name)


def main() -> None:
    SPRITES.mkdir(parents=True, exist_ok=True)
    build_menu_backdrop().save(SPRITES / "menu_backdrop.png")
    make_portal(192, (83, 210, 255)).save(SPRITES / "start_portal.png")
    make_portal(192, (92, 230, 139)).save(SPRITES / "end_portal.png")
    Image.new("RGBA", (64, 64), (6, 8, 14, 174)).save(SPRITES / "fog.png")
    Image.new("RGBA", (64, 64), (7, 9, 15, 82)).save(SPRITES / "fog_dim.png")
    copy_custom_sprites()


if __name__ == "__main__":
    main()
