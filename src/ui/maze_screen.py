"""游戏内迷宫画面。"""

from __future__ import annotations


class MazeScreen:
    """绘制迷宫、玩家和 HUD。"""

    def __init__(self, cell_size: int = 28):
        self.cell_size = cell_size

    def draw(self, screen, engine, strategy_name: str = "manual"):
        try:
            import pygame
        except Exception:
            return
        grid = engine.grid
        colors = {
            "#": (35, 35, 45),
            ".": (215, 215, 215),
            "S": (60, 200, 120),
            "E": (80, 140, 230),
            "G": (240, 210, 70),
            "T": (220, 70, 70),
            "B": (150, 70, 180),
        }
        for r, row in enumerate(grid):
            for c, ch in enumerate(row):
                rect = pygame.Rect(c * self.cell_size, r * self.cell_size, self.cell_size, self.cell_size)
                pygame.draw.rect(screen, colors.get(ch, (200, 200, 200)), rect)
                pygame.draw.rect(screen, (80, 80, 90), rect, 1)
        pr, pc = engine.player_state.position
        pygame.draw.circle(
            screen,
            (30, 30, 250),
            (pc * self.cell_size + self.cell_size // 2, pr * self.cell_size + self.cell_size // 2),
            max(4, self.cell_size // 3),
        )
        font = pygame.font.SysFont(None, 24)
        y = len(grid) * self.cell_size + 8
        ps = engine.player_state
        hud = f"HP:{ps.hp}  Coin:{ps.coin}  Steps:{ps.steps}  Score:{ps.score}  AI:{strategy_name}"
        screen.blit(font.render(hud, True, (255, 255, 255)), (8, y))
        for i, line in enumerate(engine.state.logs[-5:]):
            screen.blit(font.render(line, True, (230, 230, 230)), (8, y + 24 + i * 20))
