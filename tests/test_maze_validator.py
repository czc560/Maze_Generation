from src.maze.maze_factory import generate_maze
from src.maze.maze_validator import validate_maze, find_cells


def test_validator_basic_dfs():
    maze = generate_maze(15, "dfs", 42)
    result = validate_maze(maze.grid)
    assert result["valid"]
    assert result["single_start"]
    assert result["single_end"]
    assert len(find_cells(maze.grid, "S")) == 1
    assert len(find_cells(maze.grid, "E")) == 1
