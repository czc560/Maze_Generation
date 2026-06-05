"""MainMenuScene: title screen."""

from __future__ import annotations

import pygame

from game.scenes.base import Scene
from game.constants import COLOR_BG, COLOR_TEXT, COLOR_TEXT_DIM, COLOR_ACCENT
from game.ui.button import Button
from game.ui.label import Label


class MainMenuScene(Scene):
    """Title screen."""

    def __init__(self, manager) -> None:
        super().__init__(manager)
        am = self.engine.asset_manager
        self._title_font = am.get_font(None, 56)
        self._subtitle_font = am.get_font(None, 22)
        self._btn_font = am.get_font(None, 28)
        self._title = Label("Maze Explorer", self._title_font, COLOR_TEXT)
        self._subtitle = Label("迷宫探险者", self._subtitle_font, COLOR_TEXT_DIM)
        self._buttons: list[Button] = []
        self._needs_layout = True

    def enter(self) -> None:
        self._needs_layout = True
        # Init strategy defaults
        if not hasattr(self.engine, 'strategy_config') or not self.engine.strategy_config:
            self.engine.strategy_config = {
                "ai_strategy": "memory_greedy",
                "coin_weight": 1.2, "trap_weight": 0.8, "end_weight": 1.6,
                "visited_penalty": 2.0, "unvisited_bonus": 0.5,
                "auto_battle": False,
                "skills": [[8, 4], [2, 0], [4, 2], [6, 3]],
            }

    def _layout(self, surface: pygame.Surface) -> None:
        sw, sh = surface.get_size()
        btn_w, btn_h = 240, 50
        cx = sw // 2 - btn_w // 2
        self._buttons.clear()
        from game.scenes.maze_config import MazeConfigScene
        self._buttons.append(Button(
            pygame.Rect(cx, sh // 2 + 40, btn_w, btn_h),
            "新游戏", self._btn_font,
            callback=lambda: self.manager.replace(MazeConfigScene(self.manager)),
        ))
        self._buttons.append(Button(
            pygame.Rect(cx, sh // 2 + 105, btn_w, btn_h),
            "退出", self._btn_font,
            callback=lambda: setattr(self.engine, "running", False),
        ))
        self._needs_layout = False

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.engine.running = False
        for btn in self._buttons:
            btn.handle_event(event)

    def update(self, dt: float) -> None:
        pass

    def render(self, surface: pygame.Surface) -> None:
        if self._needs_layout: self._layout(surface)
        sw, sh = surface.get_size()
        surface.fill(COLOR_BG)
        for x in range(0, sw, 40):
            for y in range(0, sh, 40):
                if (x // 40 + y // 40) % 3 == 0:
                    alpha_surf = pygame.Surface((38, 38), pygame.SRCALPHA)
                    alpha_surf.fill((255, 255, 255, 6))
                    surface.blit(alpha_surf, (x + 1, y + 1))
        self._title.render_centered(surface, sw // 2, sh // 2 - 60)
        self._subtitle.render_centered(surface, sw // 2, sh // 2 - 10)
        for btn in self._buttons: btn.render(surface)
        Label("v0.2", self.engine.asset_manager.get_font(None, 16),
              COLOR_TEXT_DIM).render_centered(surface, sw // 2, sh - 25)
