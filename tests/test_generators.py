import pytest

from src.maze.maze_factory import generate_maze
from src.maze.resource_placer import place_resources
from src.maze.maze_validator import validate_maze


@pytest.mark.parametrize("algorithm", ["dfs", "prim", "kruskal", "division", "bfs_optimize"])
def test_generators_create_valid_maze(algorithm):
    maze = generate_maze(15, algorithm, 42)
    assert maze.size == 15
    result = validate_maze(maze.grid)
    assert result["valid"]
    assert result["single_start"]
    assert result["single_end"]
    if algorithm in {"dfs", "prim", "kruskal"}:
        assert result["is_perfect_maze"]


def test_resource_placement_has_single_boss():
    maze = generate_maze(15, "dfs", 42)
    maze = place_resources(maze, coin_count=5, trap_count=3, place_boss=True, seed=42)
    result = validate_maze(maze.grid, require_boss=True)
    assert result["valid"]
    assert result["single_boss"]
    assert sum(row.count("G") for row in maze.grid) == 5
    assert sum(row.count("T") for row in maze.grid) == 3
    assert sum(row.count("B") for row in maze.grid) == 1
