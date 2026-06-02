from __future__ import annotations

import json
import os
from typing import Any

from .game_rules import generate_game_rules
from .maze import Maze, SYMBOLS


def maze_to_dict(maze: Maze, include_grid: bool = True) -> dict[str, Any]:
    del include_grid
    rules = generate_game_rules(maze)
    symbol_map = {
        SYMBOLS["wall"]: "#",
        SYMBOLS["floor"]: " ",
        SYMBOLS["start"]: "S",
        SYMBOLS["end"]: "E",
        SYMBOLS["boss"]: "B",
        SYMBOLS["coin"]: "G",
        SYMBOLS["trap"]: "T",
    }

    maze_grid: list[list[str]] = []
    for row in range(maze.rows):
        row_cells: list[str] = []
        for col in range(maze.cols):
            content = maze.grid[row][col].content
            row_cells.append(symbol_map.get(content, content))
        maze_grid.append(row_cells)

    return {
        "maze": maze_grid,
        "B": list(rules["boss_hp"]),
        "PlayerSkills": [list(skill) for skill in rules["player_skills"]],
        "minRouds": rules["min_rounds"],
        "CoinConsumption": rules["coin_consumption"],
    }


def export_maze_json(maze: Maze, path: str, include_grid: bool = True) -> str:
    data = maze_to_dict(maze, include_grid=include_grid)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("{\n")
        handle.write('  "maze": [\n')
        for idx, row in enumerate(data["maze"]):
            row_text = json.dumps(row, ensure_ascii=True)
            suffix = "," if idx < len(data["maze"]) - 1 else ""
            handle.write(f"    {row_text}{suffix}\n")
        handle.write("  ],\n")

        handle.write(f"  \"B\": {json.dumps(data['B'], ensure_ascii=True)},\n")
        handle.write(
            f"  \"PlayerSkills\": {json.dumps(data['PlayerSkills'], ensure_ascii=True)},\n"
        )
        handle.write(f"  \"minRouds\": {data['minRouds']},\n")
        handle.write(f"  \"CoinConsumption\": {data['CoinConsumption']}\n")
        handle.write("}\n")
    return os.path.abspath(path)
