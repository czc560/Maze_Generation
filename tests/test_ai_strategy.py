from src.ai.greedy_strategy import GreedyStrategy
from src.ai.ppo_strategy import PPOStrategy
from src.ai.qlearning_strategy import QLearningStrategy
from src.game.player_state import PlayerState
from src.maze.maze_factory import generate_maze
from src.utils.constants import ACTIONS


def test_ai_strategies_choose_action():
    maze = generate_maze(15, "dfs", 42)
    player = PlayerState(position=(1, 1))
    for strategy in [GreedyStrategy(), PPOStrategy(seed=1), QLearningStrategy(seed=1)]:
        action = strategy.choose_action(maze, player)
        assert action in ACTIONS
