"""MazeConfigScene: simple maze parameters before starting a new game."""

from __future__ import annotations

import random
import pygame

from game.scenes.base import Scene
from game.constants import (COLOR_BG, COLOR_TEXT, COLOR_TEXT_DIM, COLOR_ACCENT,
                             DEFAULT_ROWS, DEFAULT_COLS, DEFAULT_SEED, DEFAULT_K, DEFAULT_METHOD)
from game.ui.button import Button
from game.ui.label import Label
from game.ui.slider import Slider
from game.ui.dropdown import Dropdown
from game.ui.text_input import TextInput
from game.ui.panel import Panel

ALGORITHM_OPTIONS = ["mst", "backtracking", "divide_conquer", "branch_bound"]
ALGORITHM_LABELS = {"mst": "最小生成树 Prim", "backtracking": "回溯法 DFS",
                     "divide_conquer": "分治法", "branch_bound": "分支限界法"}


class MazeConfigScene(Scene):
    """Clean maze configuration screen."""

    def __init__(self, manager) -> None:
        super().__init__(manager)
        am = self.engine.asset_manager
        self._font = am.get_font(None, 28)
        self._font_small = am.get_font(None, 20)
        self._font_title = am.get_font(None, 38)

        self._rows = DEFAULT_ROWS
        self._cols = DEFAULT_COLS
        self._seed = DEFAULT_SEED
        self._k = DEFAULT_K
        self._method = DEFAULT_METHOD

        self._sliders: list[Slider] = []
        self._widgets: list = []
        self._buttons: list[Button] = []
        self._needs_layout = True

    def enter(self) -> None:
        self._needs_layout = True

    def _layout(self, surface: pygame.Surface) -> None:
        sw, sh = surface.get_size()
        self._sliders.clear()
        self._widgets.clear()
        self._buttons.clear()

        panel_w, panel_h = 420, 450
        px = (sw - panel_w) // 2
        py = 80
        col_w = panel_w - 40

        self._panel = Panel(pygame.Rect(px, py, panel_w, panel_h),
                            color=(28, 28, 42), border_color=(50, 50, 70))
        lx = px + 20
        ly = py + 25

        # Rows
        self._sliders.append(Slider(pygame.Rect(lx, ly, col_w, 18), "行数", self._font_small,
                                     5, 51, 2, self._rows,
                                     on_change=lambda v: setattr(self, '_rows', int(v))))
        ly += 52
        # Cols
        self._sliders.append(Slider(pygame.Rect(lx, ly, col_w, 18), "列数", self._font_small,
                                     5, 51, 2, self._cols,
                                     on_change=lambda v: setattr(self, '_cols', int(v))))
        ly += 60
        # Algorithm
        Label("生成算法", self._font_small, COLOR_TEXT_DIM).render(
            surface, lx, ly)  # just for layout reference
        algo_names = [ALGORITHM_LABELS[a] for a in ALGORITHM_OPTIONS]
        self._algo = Dropdown(pygame.Rect(lx, ly + 22, col_w, 32), algo_names, self._font_small,
                              default_index=ALGORITHM_OPTIONS.index(self._method),
                              on_change=lambda i, _: setattr(self, '_method', ALGORITHM_OPTIONS[i]))
        self._widgets.append(self._algo)
        self._algo_label_y = ly
        self._algo_y = ly + 22
        ly += 95

        # Seed
        Label("随机种子 (留空=随机)", self._font_small, COLOR_TEXT_DIM).render(surface, lx, ly)
        ly += 22
        self._seed_input = TextInput(pygame.Rect(lx, ly, col_w - 90, 32), self._font_small,
                                     placeholder="留空=随机", default_text=str(self._seed))
        self._widgets.append(self._seed_input)
        self._buttons.append(Button(pygame.Rect(lx + col_w - 80, ly, 80, 32), "随机",
                                    self._font_small, callback=self._randomize_seed))
        ly += 55

        # k-value
        self._sliders.append(Slider(pygame.Rect(lx, ly, col_w, 18), "目标分数 k", self._font_small,
                                     0.5, 8.0, 0.1, self._k,
                                     on_change=lambda v: setattr(self, '_k', v)))
        ly += 70

        # Start button
        btn_w = 180
        self._start_btn = Button(pygame.Rect(px + (panel_w - btn_w) // 2, py + panel_h - 65, btn_w, 44),
                                 "开始游戏", self._font,
                                 color_normal=(40, 120, 60), color_hover=(55, 150, 80),
                                 callback=self._start_game)
        self._buttons.append(self._start_btn)

        # Back button at bottom of screen
        self._buttons.append(Button(pygame.Rect(sw // 2 - 80, sh - 55, 160, 40),
                                    "返回主菜单", self._font_small,
                                    color_normal=(120, 40, 40), color_hover=(150, 55, 55),
                                    callback=lambda: self.manager.pop()))
        self._needs_layout = False

    def _randomize_seed(self):
        self._seed = random.randint(0, 2**31 - 1)
        if hasattr(self, '_seed_input'):
            self._seed_input.text = str(self._seed)

    def _start_game(self):
        seed_text = self._seed_input.text.strip() if hasattr(self, '_seed_input') else ""
        try:
            seed = int(seed_text) if seed_text else random.randint(0, 2**31 - 1)
        except ValueError:
            seed = random.randint(0, 2**31 - 1)

        strategy = getattr(self.engine, 'strategy_config', {})
        config = {
            "rows": self._rows, "cols": self._cols, "seed": seed,
            "k": self._k, "method": self._method,
            **strategy,
        }
        from game.scenes.gameplay import GameplayScene
        self.manager.replace(GameplayScene(self.manager, config=config))

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.manager.pop(); return
        for s in self._sliders: s.handle_event(event)
        for w in self._widgets:
            if hasattr(w, 'handle_event'): w.handle_event(event)
        for btn in self._buttons: btn.handle_event(event)

    def update(self, dt: float) -> None:
        if hasattr(self, '_seed_input'): self._seed_input.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        if self._needs_layout: self._layout(surface)
        surface.fill(COLOR_BG)
        sw = surface.get_width()
        Label("新 游 戏", self._font_title, COLOR_ACCENT).render_centered(surface, sw // 2, 30)
        self._panel.render(surface)
        for s in self._sliders: s.render(surface)
        for w in self._widgets:
            if hasattr(w, 'render'): w.render(surface)
        for btn in self._buttons: btn.render(surface)
