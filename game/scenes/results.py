"""ResultsScene: post-game score, then return to maze config."""

from __future__ import annotations

import pygame
from game.scenes.base import Scene
from game.constants import (COLOR_BG, COLOR_TEXT, COLOR_TEXT_DIM, COLOR_ACCENT,
                             COLOR_GOLD, COLOR_RED, COLOR_GREEN)
from game.ui.label import Label
from game.ui.button import Button
from game.ui.panel import Panel


class ResultsScene(Scene):
    """End-of-game results."""

    def __init__(self, manager, maze=None, player=None, game_rules=None, player_lost=False) -> None:
        super().__init__(manager)
        self._maze = maze
        self._player = player
        self._game_rules = game_rules or {}
        self._player_lost = player_lost
        am = self.engine.asset_manager
        self._font_title = am.get_font(None, 42)
        self._font = am.get_font(None, 24)
        self._font_small = am.get_font(None, 19)
        self._buttons: list[Button] = []
        self._needs_layout = True

    def enter(self) -> None:
        self._needs_layout = True

    def _layout(self, surface: pygame.Surface) -> None:
        sw, sh = surface.get_size()
        self._buttons.clear()
        btn_w, btn_h = 200, 48
        bottom_y = sh - btn_h - 40

        self._buttons.append(Button(
            pygame.Rect(sw // 2 - btn_w - 20, bottom_y, btn_w, btn_h),
            "再来一局", self._font_small,
            color_normal=(40, 120, 60), color_hover=(55, 150, 80),
            callback=self._play_again,
        ))
        self._buttons.append(Button(
            pygame.Rect(sw // 2 + 20, bottom_y, btn_w, btn_h),
            "返回主菜单", self._font_small,
            color_normal=(120, 40, 40), color_hover=(150, 55, 55),
            callback=self._go_to_menu,
        ))
        self._needs_layout = False

    def _play_again(self):
        from game.scenes.maze_config import MazeConfigScene
        self.manager.replace(MazeConfigScene(self.manager))

    def _go_to_menu(self):
        from game.scenes.menu import MainMenuScene
        while self.manager.depth > 0:
            self.manager.pop()
        self.manager.push(MainMenuScene(self.manager))

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_SPACE, pygame.K_ESCAPE, pygame.K_RETURN):
                self._play_again(); return
        for btn in self._buttons:
            btn.handle_event(event)

    def update(self, dt: float) -> None:
        pass

    def render(self, surface: pygame.Surface) -> None:
        if self._needs_layout: self._layout(surface)
        sw, sh = surface.get_size()
        surface.fill(COLOR_BG)

        title = "Boss战失败!" if self._player_lost else "迷宫探索完成!"
        tcolor = COLOR_RED if self._player_lost else COLOR_GREEN
        Label(title, self._font_title, tcolor).render_centered(surface, sw // 2, 50)

        p = self._player
        if p is not None:
            panel_rect = pygame.Rect(sw // 2 - 200, 110, 400, 280)
            Panel(panel_rect, color=(28, 28, 42), border_color=(55, 55, 75)).render(surface)
            stats = [("总步数", str(p.steps_taken)), ("金币", str(p.resources)),
                      ("收集金币", str(p.coin_count)), ("触发陷阱", str(p.trap_count)),
                      ("最终得分", f"{p.score:.1f}")]
            y = 130
            for label, value in stats:
                Label(f"{label}:", self._font, COLOR_TEXT_DIM).render(surface, panel_rect.left + 30, y)
                Label(value, self._font, COLOR_GOLD).render(surface, panel_rect.right - 120, y)
                y += 36
            if self._game_rules:
                y += 10
                bh = self._game_rules.get("boss_hp", [])
                Label(f"Boss: {len(bh)} | 回合限制: {self._game_rules.get('min_rounds','?')} | 重试: {self._game_rules.get('coin_consumption','?')}G",
                      self._font_small, COLOR_TEXT_DIM).render_centered(surface, sw // 2, y)

        Label("空格/ESC/回车 → 再来一局", self._font_small, COLOR_TEXT_DIM).render_centered(
            surface, sw // 2, sh - 90)
        for btn in self._buttons: btn.render(surface)
