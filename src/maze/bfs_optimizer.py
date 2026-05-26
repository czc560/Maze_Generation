"""BFS / 分支限界思想迷宫优化器。"""

from __future__ import annotations

import random
import time

from src.maze.maze import Maze
from src.maze.maze_metrics import compute_metrics, shortest_path
from src.maze.maze_validator import validate_maze
from src.utils.constants import WALL, ROAD


def optimize_maze_by_bfs_branch_bound(maze: Maze, seed: int | None = None) -> Maze:
    """尝试打开局部墙体增加分支，同时通过验证器保证迷宫合法。"""
    start_time = time.perf_counter()
    rng = random.Random(seed)
    grid = maze.copy_grid()
    n = len(grid)
    before = compute_metrics(grid)
    steps = list(maze.generation_steps[-50:])
    process: list[dict] = []
    candidates: list[tuple[int, int, str]] = []

    for r in range(1, n - 1):
        for c in range(1, n - 1):
            if grid[r][c] != WALL:
                continue
            vertical = grid[r - 1][c] != WALL and grid[r + 1][c] != WALL
            horizontal = grid[r][c - 1] != WALL and grid[r][c + 1] != WALL
            if vertical:
                candidates.append((r, c, "vertical"))
            if horizontal:
                candidates.append((r, c, "horizontal"))

    rng.shuffle(candidates)
    opened = 0
    max_open = max(1, min(8, n // 3))

    for r, c, kind in candidates:
        if opened >= max_open:
            break
        trial = [row[:] for row in grid]
        trial[r][c] = ROAD
        val = validate_maze(trial)
        if not val["valid"]:
            continue
        trial_metrics = compute_metrics(trial)
        score_before = before["branches"] * 4 + before["dead_ends"] + before["shortest_path_length"]
        score_after = trial_metrics["branches"] * 4 + trial_metrics["dead_ends"] + trial_metrics["shortest_path_length"]
        if score_after >= score_before - 2:
            grid = trial
            opened += 1
            before = trial_metrics
            steps.append([row[:] for row in grid])
            process.append({"open_wall": [r, c], "kind": kind, "score_after": score_after})

    result = Maze(
        grid=grid,
        size=n,
        algorithm="bfs_optimize",
        seed=seed if seed is not None else maze.seed,
        generation_steps=steps,
        metadata={
            "base_algorithm": maze.algorithm,
            "runtime_seconds": round(time.perf_counter() - start_time, 6),
            "opened_walls": opened,
            "process": process,
            "bfs_shortest_path": [[r, c] for r, c in shortest_path(grid)],
        },
    )
    result.validation = validate_maze(grid)
    result.metrics = compute_metrics(grid)
    result.metadata["before_metrics"] = maze.metrics or compute_metrics(maze.grid)
    result.metadata["after_metrics"] = result.metrics
    return result
