from __future__ import annotations

import json
from pathlib import Path

import pytest

from game.maze.generator import Maze
from game.maze.optimal_path import (
    compute_optimal_path,
    export_game_maze_json,
    game_maze_to_grid,
    load_maze_from_json,
    verify_path,
)
from game.maze.strategies import make_normalized_strategies


ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "tests" / "golden"


@pytest.mark.parametrize(
    ("method", "golden_name"),
    (
        ("mst", "generate_mst_utf8.json.bin"),
        ("backtracking", "generate_backtracking_utf8.json.bin"),
        ("divide_conquer", "generate_divide_conquer_utf8.json.bin"),
        ("branch_bound", "generate_branch_bound_utf8.json.bin"),
    ),
)
def test_fixed_seed_generation_matches_golden_json(
    tmp_path: Path, method: str, golden_name: str
) -> None:
    coin_strategy, trap_strategy = make_normalized_strategies(4.0, spread=1.2)
    maze = Maze.generate(
        15,
        15,
        seed=42,
        generation_method=method,
        coin_strategy=coin_strategy,
        trap_strategy=trap_strategy,
    )
    output = tmp_path / f"{method}.json"
    export_game_maze_json(maze, str(output))
    assert output.read_bytes() == (GOLDEN / golden_name).read_bytes()


def test_submitted_maze_full_path_and_replay_match_golden() -> None:
    maze = load_maze_from_json(str(ROOT / "best_maze_design_林士清.json"))
    result = compute_optimal_path(maze, require_end=True)
    report = verify_path(maze, result.path, require_end=True)
    golden = json.loads(
        (GOLDEN / "solve_require_end_out_utf8.json.bin").read_text(encoding="utf-8")
    )

    assert [[row, col] for row, col in result.path] == golden["path_rc"]
    assert result.max_resource == 430
    assert result.coins_in_path == 11
    assert result.traps_in_path == 4
    assert len(result.path) == 103
    assert result.is_optimal is True
    assert report["legal"] is True
    assert report["resource"] == result.max_resource
    assert report["steps"] == 102


def test_game_maze_json_conversion_round_trip(tmp_path: Path) -> None:
    maze = Maze.generate(15, 15, seed=42, generation_method="mst")
    output = tmp_path / "maze.json"
    export_game_maze_json(maze, str(output))
    loaded = load_maze_from_json(str(output))

    assert ["".join(row) for row in game_maze_to_grid(maze)] == [
        "".join(cell.content for cell in row) for row in loaded.grid
    ]
