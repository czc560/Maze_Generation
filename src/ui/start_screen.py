"""游戏开始画面。"""

from __future__ import annotations


class StartScreen:
    """开始界面：标题、按钮、算法/AI/尺寸/种子选择入口。"""

    def __init__(self, default_algorithm="dfs", default_ai="greedy", size=15, seed=42):
        self.algorithm = default_algorithm
        self.ai = default_ai
        self.size = size
        self.seed = seed

    def run(self, screen=None):
        """返回当前设置；pygame 版本可在此基础上继续扩展。"""
        if screen is None:
            return {"algorithm": self.algorithm, "ai": self.ai, "size": self.size, "seed": self.seed}
        try:
            import pygame
        except Exception:
            return {"algorithm": self.algorithm, "ai": self.ai, "size": self.size, "seed": self.seed}
        font = pygame.font.SysFont(None, 36)
        small = pygame.font.SysFont(None, 24)
        clock = pygame.time.Clock()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return {"quit": True}
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        return {"algorithm": self.algorithm, "ai": self.ai, "size": self.size, "seed": self.seed}
                    if event.key == pygame.K_ESCAPE:
                        return {"quit": True}
            screen.fill((25, 25, 35))
            screen.blit(font.render("AI Competitive Maze", True, (255, 255, 255)), (80, 80))
            lines = [
                "Press ENTER to start",
                f"Algorithm: {self.algorithm}",
                f"AI Strategy: {self.ai}",
                f"Size: {self.size}",
                f"Seed: {self.seed}",
                "Assets/audio can be replaced under assets/.",
            ]
            for i, line in enumerate(lines):
                screen.blit(small.render(line, True, (230, 230, 230)), (80, 150 + i * 30))
            pygame.display.flip()
            clock.tick(30)
