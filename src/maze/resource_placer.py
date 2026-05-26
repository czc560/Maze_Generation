"""金币、陷阱与 BOSS 放置。"""

from __future__ import annotations

import random

from src.maze.maze import Maze
from src.maze.maze_metrics import shortest_path, compute_metrics
from src.maze.maze_validator import validate_maze
from src.utils.constants import ROAD, COIN, TRAP, BOSS, START, END


def _available_roads(grid: list[list[str]]) -> list[tuple[int, int]]:
    return [(r, c) for r, row in enumerate(grid) for c, ch in enumerate(row) if ch == ROAD]


def place_resources(
    maze: Maze,
    coin_count: int = 10,
    trap_count: int = 8,
    place_boss: bool = True,
    seed: int | None = None,
) -> Maze:
    """在可达道路上放置金币、陷阱、BOSS。"""
    rng = random.Random(seed)
    grid = maze.copy_grid()
    n = len(grid)

    for r in range(n):
        for c in range(n):
            if grid[r][c] in {COIN, TRAP, BOSS}:
                grid[r][c] = ROAD

    grid[1][1] = START
    grid[n - 2][n - 2] = END
    path = shortest_path(grid)
    boss_pos: tuple[int, int] | None = None

    if place_boss:
        candidates = path[len(path) // 2 :] if len(path) > 4 else _available_roads(grid)
        candidates = [p for p in candidates if grid[p[0]][p[1]] == ROAD]
        if candidates:
            boss_pos = candidates[min(len(candidates) - 1, max(0, int(len(candidates) * 0.65)))]
        else:
            roads = _available_roads(grid)
            boss_pos = roads[-1] if roads else None
        if boss_pos:
            grid[boss_pos[0]][boss_pos[1]] = BOSS

    roads = _available_roads(grid)
    rng.shuffle(roads)
    coin_count = min(coin_count, len(roads))
    for r, c in roads[:coin_count]:
        grid[r][c] = COIN

    roads = _available_roads(grid)
    rng.shuffle(roads)
    trap_count = min(trap_count, len(roads))
    for r, c in roads[:trap_count]:
        grid[r][c] = TRAP

    result = Maze(
        grid=grid,
        size=maze.size,
        algorithm=maze.algorithm,
        seed=maze.seed,
        generation_steps=maze.generation_steps,
        metadata={
            **maze.metadata,
            "coin_count": coin_count,
            "trap_count": trap_count,
            "boss_position": list(boss_pos) if boss_pos else None,
            "resource_seed": seed,
        },
    )
    result.validation = validate_maze(grid, require_boss=place_boss)
    result.metrics = compute_metrics(grid)
    return result
