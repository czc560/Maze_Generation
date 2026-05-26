"""pygame 游戏应用入口。"""

from __future__ import annotations

from src.ai.strategy_loader import load_strategy
from src.game.game_engine import MazeGameEngine
from src.maze.maze_factory import generate_maze
from src.maze.resource_placer import place_resources
from src.maze.maze_metrics import shortest_path
from src.ui.loading_screen import show_algorithm_generation_replay, show_start_path_flash_animation
from src.ui.maze_screen import MazeScreen
from src.ui.start_screen import StartScreen
from src.game.input_handler import pygame_key_to_action


class MazeGameApp:
    """封装开始画面、加载动画、游戏内画面与 AI 自动运行。"""

    def __init__(self, size=15, algorithm="dfs", seed=42, ai="greedy"):
        self.size = size
        self.algorithm = algorithm
        self.seed = seed
        self.ai = ai

    def run(self):
        """启动 pygame 游戏。"""
        try:
            import pygame
        except Exception as exc:
            print(f"pygame 不可用，无法启动图形界面: {exc}")
            return
        pygame.init()
        screen = pygame.display.set_mode((760, 680))
        pygame.display.set_caption("AI Competitive Maze")
        settings = StartScreen(self.algorithm, self.ai, self.size, self.seed).run(screen)
        if settings.get("quit"):
            pygame.quit()
            return
        maze = generate_maze(settings["size"], settings["algorithm"], settings["seed"])
        show_algorithm_generation_replay(screen, maze.generation_steps, maze.algorithm, maze.seed, maze.size)
        maze = place_resources(maze, 8, 6, True, settings["seed"])
        path = shortest_path(maze.grid)
        show_start_path_flash_animation(screen, maze.grid, path, path[0], path[-1])
        engine = MazeGameEngine(maze)
        strategy = load_strategy(settings["ai"])
        maze_screen = MazeScreen(cell_size=max(12, min(30, 560 // maze.size)))
        clock = pygame.time.Clock()
        auto_ai = settings["ai"] != "manual"

        running = True
        while running:
            dt = clock.tick(30) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    action = pygame_key_to_action(event.key)
                    if action:
                        engine.step(action)
                    if event.key == pygame.K_p:
                        engine.pause() if not engine.state.paused else engine.resume()
            if auto_ai and not engine.state.game_over:
                action = strategy.choose_action(engine, engine.player_state)
                info = engine.step(action)
                if info.get("event") == "boss":
                    engine.step("USE_SKILL")
            screen.fill((20, 20, 28))
            maze_screen.draw(screen, engine, strategy_name=settings["ai"])
            pygame.display.flip()
        pygame.quit()
