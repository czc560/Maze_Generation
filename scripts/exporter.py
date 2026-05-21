from __future__ import annotations

import json
import os
from typing import Any

from .config import ASSETS
from .maze import Maze, SYMBOLS


def maze_to_dict(maze: Maze, include_grid: bool = True) -> dict[str, Any]:
    coins: list[tuple[int, int]] = []
    traps: list[tuple[int, int]] = []

    grid_lines: list[str] = []
    for row in range(maze.rows):
        line_chars: list[str] = []
        for col in range(maze.cols):
            content = maze.grid[row][col].content
            line_chars.append(content)
            if content == SYMBOLS["coin"]:
                coins.append((row, col))
            elif content == SYMBOLS["trap"]:
                traps.append((row, col))
        if include_grid:
            grid_lines.append("".join(line_chars))

    return {
        "rows": maze.rows,
        "cols": maze.cols,
        "seed": maze.seed,
        "symbols": dict(ASSETS["symbols"]),
        "values": dict(ASSETS["values"]),
        "start": maze.start,
        "end": maze.end,
        "boss": maze.boss,
        "coins": coins,
        "traps": traps,
        "grid": grid_lines if include_grid else None,
    }


def export_maze_json(maze: Maze, path: str, include_grid: bool = True) -> str:
    data = maze_to_dict(maze, include_grid=include_grid)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)
    return os.path.abspath(path)
