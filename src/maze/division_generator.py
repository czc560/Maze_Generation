"""递归分割法迷宫生成器。"""

from __future__ import annotations

import random
import time

from src.maze.generator_base import road_grid, record_step, finalize_maze
from src.utils.constants import WALL, ROAD, normalize_size


def generate_division_maze(size: int, seed: int | None = None):
    """使用递归分割法生成连通迷宫。"""
    start_time = time.perf_counter()
    rng = random.Random(seed)
    size = normalize_size(size)
    grid = road_grid(size)
    steps: list[list[list[str]]] = []
    record_step(steps, grid)

    def divide(r1: int, c1: int, r2: int, c2: int) -> None:
        height = r2 - r1 + 1
        width = c2 - c1 + 1
        if height < 3 or width < 3:
            return

        horizontal_candidates = [r for r in range(r1 + 1, r2) if r % 2 == 0]
        vertical_candidates = [c for c in range(c1 + 1, c2) if c % 2 == 0]
        if not horizontal_candidates and not vertical_candidates:
            return

        if horizontal_candidates and vertical_candidates:
            horizontal = height >= width if height != width else rng.choice([True, False])
        else:
            horizontal = bool(horizontal_candidates)

        if horizontal:
            wall_r = rng.choice(horizontal_candidates)
            door_candidates = [c for c in range(c1, c2 + 1) if c % 2 == 1]
            door_c = rng.choice(door_candidates)
            for c in range(c1, c2 + 1):
                grid[wall_r][c] = WALL
            grid[wall_r][door_c] = ROAD
            record_step(steps, grid)
            divide(r1, c1, wall_r - 1, c2)
            divide(wall_r + 1, c1, r2, c2)
        else:
            wall_c = rng.choice(vertical_candidates)
            door_candidates = [r for r in range(r1, r2 + 1) if r % 2 == 1]
            door_r = rng.choice(door_candidates)
            for r in range(r1, r2 + 1):
                grid[r][wall_c] = WALL
            grid[door_r][wall_c] = ROAD
            record_step(steps, grid)
            divide(r1, c1, r2, wall_c - 1)
            divide(r1, wall_c + 1, r2, c2)

    divide(1, 1, size - 2, size - 2)
    return finalize_maze(grid, "division", seed, steps, start_time, {"note": "递归分割法不强制完美迷宫性质"})
