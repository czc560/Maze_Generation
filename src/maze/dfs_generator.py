"""DFS 回溯法迷宫生成器。"""

from __future__ import annotations

import random
import time

from src.maze.generator_base import wall_grid, record_step, finalize_maze
from src.utils.constants import ROAD, CARVE_DIRS_2, normalize_size


def generate_dfs_maze(size: int, seed: int | None = None):
    """使用随机 DFS 回溯法生成完美迷宫。"""
    start_time = time.perf_counter()
    rng = random.Random(seed)
    size = normalize_size(size)
    grid = wall_grid(size)
    steps: list[list[list[str]]] = []

    start = (1, 1)
    grid[1][1] = ROAD
    stack = [start]
    visited = {start}
    record_step(steps, grid)

    while stack:
        r, c = stack[-1]
        dirs = CARVE_DIRS_2[:]
        rng.shuffle(dirs)
        next_cell = None
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if 1 <= nr < size - 1 and 1 <= nc < size - 1 and (nr, nc) not in visited:
                next_cell = (nr, nc, dr, dc)
                break
        if next_cell is None:
            stack.pop()
            continue
        nr, nc, dr, dc = next_cell
        grid[r + dr // 2][c + dc // 2] = ROAD
        grid[nr][nc] = ROAD
        visited.add((nr, nc))
        stack.append((nr, nc))
        record_step(steps, grid)

    return finalize_maze(grid, "dfs", seed, steps, start_time, {"visited_cells": len(visited)})
