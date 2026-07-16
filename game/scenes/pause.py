"""PauseScene: overlay with Resume, Strategy Settings, and Main Menu."""

from __future__ import annotations

import pygame
from game.scenes.base import Scene
from game.constants import COLOR_ACCENT
from game.ui.label import Label
from game.ui.button import Button
from game.ui.theme import FONT_UI_BOLD, FONT_UI_REGULAR


class PauseScene(Scene):
    """Overlay during gameplay."""

    def __init__(self, manager) -> None:
        super().__init__(manager)
        am = self.engine.asset_manager
        self._font = am.get_font(FONT_UI_BOLD, 36)
        self._font_btn = am.get_font(FONT_UI_REGULAR, 24)
        self._buttons: list[Button] = []
        self._needs_layout = True

    def enter(self) -> None:
        self._needs_layout = True

    def _layout(self, surface: pygame.Surface) -> None:
        sw, sh = surface.get_size()
        self._buttons.clear()
        btn_w, btn_h = 250, 50
        cx = sw // 2 - btn_w // 2
        base_y = sh // 2 - 75

        self._buttons.append(Button(
            pygame.Rect(cx, base_y, btn_w, btn_h),
            "继续游戏", self._font_btn,
            callback=lambda: self.manager.pop(),
        ))
        self._buttons.append(Button(
            pygame.Rect(cx, base_y + 70, btn_w, btn_h),
            "策略设置", self._font_btn,
            callback=self._open_strategy_settings,
        ))
        self._buttons.append(Button(
            pygame.Rect(cx, base_y + 140, btn_w, btn_h),
            "返回主菜单", self._font_btn,
            callback=self._go_to_menu,
        ))
        self._needs_layout = False

    def _open_strategy_settings(self) -> None:
        from game.scenes.strategy_settings import StrategySettingsScene
        self.manager.push(StrategySettingsScene(self.manager))

    def _go_to_menu(self) -> None:
        from game.scenes.menu import MainMenuScene
        while self.manager.depth > 0:
            self.manager.pop()
        self.manager.push(MainMenuScene(self.manager))

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.manager.pop(); return
        for btn in self._buttons:
            btn.handle_event(event)

    def update(self, dt: float) -> None:
        pass

    def render(self, surface: pygame.Surface) -> None:
        if self._needs_layout: self._layout(surface)
        sw, sh = surface.get_size()
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 155))
        surface.blit(overlay, (0, 0))
        panel = pygame.Rect(sw // 2 - 185, sh // 2 - 155, 370, 330)
        pygame.draw.rect(surface, (12, 16, 23, 220), panel, border_radius=10)
        pygame.draw.rect(surface, (116, 142, 164, 140), panel, width=1, border_radius=10)
        pygame.draw.line(surface, (255, 209, 112), (panel.left + 86, panel.top + 50), (panel.right - 86, panel.top + 50), 2)
        Label("游 戏 暂 停", self._font, COLOR_ACCENT).render_centered(surface, sw // 2, sh // 2 - 130)
        for btn in self._buttons: btn.render(surface)
