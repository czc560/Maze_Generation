"""AI 玩家运行入口。"""

from __future__ import annotations

from src.ai.strategy_loader import load_strategy
from src.game.game_engine import MazeGameEngine
from src.maze.maze import Maze


def run_ai_on_maze(
    maze_data,
    ai: str = "greedy",
    custom_strategy: str | None = None,
    max_steps: int = 500,
    boss_config: dict | None = None,
) -> dict:
    """加载指定 AI 在迷宫上运行。"""
    if isinstance(maze_data, Maze):
        maze = maze_data
    elif isinstance(maze_data, dict):
        maze = Maze.from_dict(maze_data)
    else:
        maze = Maze(maze_data)
    strategy = load_strategy(ai, custom_strategy)
    engine = MazeGameEngine(maze, boss_config=boss_config)
    return engine.run_ai(strategy, max_steps=max_steps)
