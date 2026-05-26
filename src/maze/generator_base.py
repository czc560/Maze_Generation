"""迷宫生成器基础工具。"""

from __future__ import annotations

import time
from typing import Any

from src.maze.maze import Maze
from src.maze.maze_metrics import compute_metrics
from src.maze.maze_validator import validate_maze
from src.utils.constants import WALL, ROAD, START, END, normalize_size


def wall_grid(size: int) -> list[list[str]]:
    """创建全墙矩阵。"""
    size = normalize_size(size)
    return [[WALL for _ in range(size)] for _ in range(size)]


def road_grid(size: int) -> list[list[str]]:
    """创建边界为墙、内部为路的矩阵。"""
    size = normalize_size(size)
    grid = [[ROAD for _ in range(size)] for _ in range(size)]
    for i in range(size):
        grid[0][i] = WALL
        grid[size - 1][i] = WALL
        grid[i][0] = WALL
        grid[i][size - 1] = WALL
    return grid


def record_step(steps: list[list[list[str]]], grid: list[list[str]], max_steps: int = 1200) -> None:
    """记录生成过程；过多时按间隔降采样。"""
    if len(steps) < max_steps:
        steps.append([row[:] for row in grid])


def finalize_maze(
    grid: list[list[str]],
    algorithm: str,
    seed: int | None,
    generation_steps: list[list[list[str]]],
    start_time: float,
    metadata: dict[str, Any] | None = None,
) -> Maze:
    """设置 S/E、计算验证与指标，返回 Maze。"""
    n = len(grid)
    grid[1][1] = START
    grid[n - 2][n - 2] = END
    maze = Maze(grid=grid, size=n, algorithm=algorithm, seed=seed, generation_steps=generation_steps)
    meta = metadata.copy() if metadata else {}
    meta.update(
        {
            "runtime_seconds": round(time.perf_counter() - start_time, 6),
            "space_estimate_cells": n * n,
            "generation_steps": len(generation_steps),
        }
    )
    maze.metadata = meta
    maze.validation = validate_maze(grid)
    maze.metrics = compute_metrics(grid)
    return maze
