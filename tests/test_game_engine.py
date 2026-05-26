from src.game.game_engine import MazeGameEngine
from src.maze.maze_factory import generate_maze
from src.maze.maze_metrics import neighbors4


def test_game_engine_loads_and_moves():
    maze = generate_maze(15, "dfs", 42)
    engine = MazeGameEngine(maze)
    start = engine.player_state.position
    nxt = neighbors4(engine.grid, *start)[0]
    dr = nxt[0] - start[0]
    dc = nxt[1] - start[1]
    action = "DOWN" if dr == 1 else "UP" if dr == -1 else "RIGHT" if dc == 1 else "LEFT"
    info = engine.step(action)
    assert info["moved"]
    assert tuple(info["position"]) == nxt
