from src.maze.maze_factory import generate_maze
from src.utils.json_io import load_json


def test_maze_json_save_load(tmp_path):
    maze = generate_maze(15, "dfs", 42)
    path = tmp_path / "maze.json"
    maze.save_json(path)
    data = load_json(path)
    assert data["size"] == 15
    assert data["algorithm"] == "dfs"
    assert len(data["maze"]) == 15
