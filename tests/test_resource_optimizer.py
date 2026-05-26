from src.maze.maze_factory import generate_maze
from src.maze.resource_placer import place_resources
from src.resource.resource_optimizer import optimize_resource_path


def test_resource_optimizer_returns_path():
    maze = generate_maze(15, "dfs", 42)
    maze = place_resources(maze, coin_count=3, trap_count=2, place_boss=True, seed=1)
    result = optimize_resource_path(maze.grid)
    path = result["path"]
    assert path
    assert path[0] == [1, 1]
    assert path[-1] == [maze.size - 2, maze.size - 2]
    for a, b in zip(path, path[1:]):
        assert abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1
    assert "max_resource" in result
