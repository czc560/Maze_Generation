"""加载与开始动画。"""

from __future__ import annotations

import time


def _draw_grid(screen, grid, cell_size=24, highlight=None):
    try:
        import pygame
    except Exception:
        return
    colors = {
        "#": (40, 40, 48),
        ".": (220, 220, 220),
        "S": (60, 200, 120),
        "E": (80, 140, 230),
        "G": (240, 210, 70),
        "T": (220, 70, 70),
        "B": (150, 70, 180),
    }
    highlight = set(highlight or [])
    for r, row in enumerate(grid):
        for c, ch in enumerate(row):
            rect = pygame.Rect(c * cell_size, r * cell_size, cell_size, cell_size)
            pygame.draw.rect(screen, colors.get(ch, (200, 200, 200)), rect)
            if (r, c) in highlight:
                pygame.draw.rect(screen, (255, 255, 255), rect, 3)


def show_algorithm_generation_replay(screen, generation_steps, algorithm: str, seed: int | None, size: int, fps: int = 30, skippable: bool = True):
    """播放迷宫生成过程回放。"""
    try:
        import pygame
    except Exception:
        return
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 26)
    steps = generation_steps or []
    if not steps:
        return
    for i, grid in enumerate(steps):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if skippable and event.type == pygame.KEYDOWN:
                return
        screen.fill((20, 20, 28))
        _draw_grid(screen, grid, max(8, min(32, 560 // size)))
        text = f"Algorithm: {algorithm.upper()}  Seed: {seed}  Size: {size}x{size}  {i+1}/{len(steps)}"
        screen.blit(font.render(text, True, (255, 255, 255)), (10, size * max(8, min(32, 560 // size)) + 12))
        pygame.display.flip()
        clock.tick(fps)


def show_start_path_flash_animation(screen, grid, path, start_pos, end_pos, flash_count: int = 3, path_speed: int = 30, skippable: bool = True):
    """点击开始游戏后的 S/E 与路径闪烁动画。"""
    try:
        import pygame
    except Exception:
        return
    clock = pygame.time.Clock()
    cell_size = max(8, min(32, 560 // len(grid)))
    for _ in range(flash_count):
        for highlight in ([start_pos, end_pos], []):
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (skippable and event.type == pygame.KEYDOWN):
                    return
            screen.fill((20, 20, 28))
            _draw_grid(screen, grid, cell_size, highlight)
            pygame.display.flip()
            time.sleep(0.12)
    shown = []
    for pos in path:
        shown.append(tuple(pos))
        screen.fill((20, 20, 28))
        _draw_grid(screen, grid, cell_size, shown)
        pygame.display.flip()
        clock.tick(path_speed)


def play_coin_collect_animation(position, amount):
    """金币动画接口。"""
    return {"type": "coin", "position": position, "amount": amount}


def play_trap_trigger_animation(position, damage):
    """陷阱动画接口。"""
    return {"type": "trap", "position": position, "damage": damage}
