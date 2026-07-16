"""MainMenuScene: title screen."""

from __future__ import annotations

import pygame

from game.scenes.base import Scene
from game.constants import COLOR_TEXT, COLOR_TEXT_DIM
from game.ui.button import Button
from game.ui.label import Label
from game.ui.theme import FONT_UI_LIGHT, FONT_UI_REGULAR


class MainMenuScene(Scene):
    """Title screen."""

    def __init__(self, manager) -> None:
        super().__init__(manager)
        am = self.engine.asset_manager
        self._title_font = am.get_font(FONT_UI_LIGHT, 70)
        self._subtitle_font = am.get_font(FONT_UI_REGULAR, 24)
        self._btn_font = am.get_font(FONT_UI_REGULAR, 28)
        self._meta_font = am.get_font(FONT_UI_LIGHT, 17)
        self._title = Label("Maze Explorer", self._title_font, COLOR_TEXT)
        self._subtitle = Label("迷宫探险者", self._subtitle_font, (229, 238, 245))
        self._buttons: list[Button] = []
        self._needs_layout = True

    def enter(self) -> None:
        self._needs_layout = True
        if not hasattr(self.engine, "strategy_config") or not self.engine.strategy_config:
            self.engine.strategy_config = {
                "ai_strategy": "memory_greedy",
                "coin_weight": 1.2, "trap_weight": 0.8, "end_weight": 1.6,
                "visited_penalty": 2.0, "unvisited_bonus": 0.5,
                "auto_battle": False,
                "skills": [[8, 4], [2, 0], [4, 2], [6, 3]],
            }

    def _layout(self, surface: pygame.Surface) -> None:
        sw, sh = surface.get_size()
        btn_w, btn_h = 260, 54
        cx = min(sw - btn_w - 90, max(720, sw // 2 + 150))
        by = sh // 2 + 60
        self._buttons.clear()
        from game.scenes.maze_config import MazeConfigScene
        self._buttons.append(Button(
            pygame.Rect(cx, by, btn_w, btn_h),
            "新游戏", self._btn_font,
            callback=lambda: self.manager.replace(MazeConfigScene(self.manager)),
            color_normal=(35, 89, 124),
            color_hover=(47, 125, 170),
            color_active=(68, 152, 196),
            text_color=(242, 249, 255),
        ))
        self._buttons.append(Button(
            pygame.Rect(cx, by + 72, btn_w, btn_h),
            "退出", self._btn_font,
            callback=lambda: setattr(self.engine, "running", False),
            color_normal=(52, 53, 67),
            color_hover=(72, 74, 92),
            color_active=(94, 96, 118),
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
        if self._needs_layout:
            self._layout(surface)
        sw, sh = surface.get_size()
        backdrop = self.engine.asset_manager.get_image("menu_backdrop", (sw, sh))
        surface.blit(backdrop, (0, 0))

        shade = pygame.Surface((sw, sh), pygame.SRCALPHA)
        pygame.draw.rect(shade, (2, 5, 10, 78), (0, 0, 520, sh))
        pygame.draw.rect(shade, (0, 0, 0, 62), (0, sh - 130, sw, 130))
        surface.blit(shade, (0, 0))

        title_x = 116
        title_y = sh // 2 - 95
        pygame.draw.line(surface, (255, 205, 92), (title_x, title_y - 24), (title_x + 172, title_y - 24), 3)
        self._title.render(surface, title_x, title_y)
        self._subtitle.render(surface, title_x + 4, title_y + 82)
        Label("探索迷宫 / 收集金币 / 挑战 Boss", self._meta_font, (184, 198, 210)).render(
            surface, title_x + 4, title_y + 122
        )

        btn_anchor = self._buttons[0].rect.left
        panel = pygame.Rect(btn_anchor - 28, self._buttons[0].rect.top - 30, 316, 184)
        pygame.draw.rect(surface, (8, 12, 18, 184), panel, border_radius=8)
        pygame.draw.rect(surface, (255, 209, 112, 108), panel, width=1, border_radius=8)
        for btn in self._buttons:
            btn.render(surface)
        Label("v0.2", self._meta_font, COLOR_TEXT_DIM).render_centered(surface, sw - 52, sh - 28)
