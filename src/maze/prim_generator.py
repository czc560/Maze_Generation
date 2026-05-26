"""随机 Prim 迷宫生成器。"""

from __future__ import annotations

import random
import time

from src.maze.generator_base import wall_grid, record_step, finalize_maze
from src.utils.constants import ROAD, CARVE_DIRS_2, normalize_size


def generate_prim_maze(size: int, seed: int | None = None):
    """使用随机 Prim 算法生成完美迷宫。"""
    start_time = time.perf_counter()
    rng = random.Random(seed)
    size = normalize_size(size)
    grid = wall_grid(size)
    steps: list[list[list[str]]] = []

    start = (1, 1)
    grid[1][1] = ROAD
    visited = {start}
    frontiers: list[tuple[int, int]] = []

    def add_frontiers(cell: tuple[int, int]) -> None:
        r, c = cell
        for dr, dc in CARVE_DIRS_2:
            nr, nc = r + dr, c + dc
            if 1 <= nr < size - 1 and 1 <= nc < size - 1 and (nr, nc) not in visited:
                if (nr, nc) not in frontiers:
                    frontiers.append((nr, nc))

    add_frontiers(start)
    record_step(steps, grid)

    while frontiers:
        idx = rng.randrange(len(frontiers))
        cell = frontiers.pop(idx)
        if cell in visited:
            continue
        r, c = cell
        connected = []
        for dr, dc in CARVE_DIRS_2:
            nr, nc = r + dr, c + dc
            if (nr, nc) in visited:
                connected.append((nr, nc))
        if not connected:
            continue
        pr, pc = rng.choice(connected)
        grid[(r + pr) // 2][(c + pc) // 2] = ROAD
        grid[r][c] = ROAD
        visited.add(cell)
        add_frontiers(cell)
        record_step(steps, grid)

    return finalize_maze(grid, "prim", seed, steps, start_time, {"visited_cells": len(visited)})
