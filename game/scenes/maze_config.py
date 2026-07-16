"""MazeConfigScene: maze parameters before starting a new game."""

from __future__ import annotations

import random
import pygame

from game.scenes.base import Scene
from game.constants import (COLOR_TEXT, COLOR_TEXT_DIM, DEFAULT_ROWS, DEFAULT_COLS,
                             DEFAULT_SEED, DEFAULT_K, DEFAULT_METHOD)
from game.ui.button import Button
from game.ui.label import Label
from game.ui.slider import Slider
from game.ui.dropdown import Dropdown
from game.ui.text_input import TextInput
from game.ui.panel import Panel
from game.ui.backgrounds import draw_background
from game.ui.theme import FONT_UI_BOLD, FONT_UI_LIGHT, FONT_UI_REGULAR

ALGORITHM_OPTIONS = ["mst", "backtracking", "divide_conquer", "branch_bound"]
ALGORITHM_LABELS = {"mst": "最小生成树 Prim", "backtracking": "回溯法 DFS",
                     "divide_conquer": "分治法", "branch_bound": "分支限界法"}
ALGORITHM_HELP = {
    "mst": "路径更均衡，适合稳定探索。",
    "backtracking": "通道更曲折，死路更多。",
    "divide_conquer": "结构规整，房间感更强。",
    "branch_bound": "偏策略规划，挑战更集中。",
}


class MazeConfigScene(Scene):
    """Maze configuration screen."""

    def __init__(self, manager) -> None:
        super().__init__(manager)
        am = self.engine.asset_manager
        self._font = am.get_font(FONT_UI_REGULAR, 26)
        self._font_small = am.get_font(FONT_UI_REGULAR, 18)
        self._font_tiny = am.get_font(FONT_UI_LIGHT, 12)
        self._font_title = am.get_font(FONT_UI_BOLD, 36)

        self._rows = DEFAULT_ROWS
        self._cols = DEFAULT_COLS
        self._seed = DEFAULT_SEED
        self._k = DEFAULT_K
        self._method = DEFAULT_METHOD

        self._sliders: list[Slider] = []
        self._widgets: list = []
        self._buttons: list[Button] = []
        self._needs_layout = True
        self._panel = Panel(pygame.Rect(0, 0, 1, 1))
        self._preview_panel = Panel(pygame.Rect(0, 0, 1, 1))
        self._algo_label_pos = (0, 0)
        self._seed_label_pos = (0, 0)
        self._content_x = 0
        self._preview_cache_key = None
        self._preview_maze = None

    def enter(self) -> None:
        self._needs_layout = True

    def _layout(self, surface: pygame.Surface) -> None:
        sw, sh = surface.get_size()
        self._sliders.clear()
        self._widgets.clear()
        self._buttons.clear()

        gap = 34
        panel_w = 470
        panel_h = min(560, sh - 132)
        px = 72
        py = 96
        preview_x = px + panel_w + gap
        preview_w = sw - preview_x - 72
        preview_h = panel_h
        col_w = panel_w - 54

        self._panel = Panel(pygame.Rect(px, py, panel_w, panel_h),
                            color=(18, 31, 40), border_color=(101, 159, 178), border_width=2)
        self._preview_panel = Panel(pygame.Rect(preview_x, py, preview_w, preview_h),
                                    color=(20, 32, 30), border_color=(130, 169, 94), border_width=2)
        lx = px + 28
        ly = py + 106
        self._content_x = lx

        self._sliders.append(Slider(pygame.Rect(lx, ly, col_w, 18), "行数", self._font_small,
                                     5, 51, 2, self._rows,
                                     on_change=lambda v: setattr(self, '_rows', int(v)),
                                     track_color=(42, 69, 78), fill_color=(255, 206, 92),
                                     handle_color=(255, 244, 197), text_color=(226, 244, 239)))
        ly += 54
        self._sliders.append(Slider(pygame.Rect(lx, ly, col_w, 18), "列数", self._font_small,
                                     5, 51, 2, self._cols,
                                     on_change=lambda v: setattr(self, '_cols', int(v)),
                                     track_color=(42, 69, 78), fill_color=(136, 222, 160),
                                     handle_color=(232, 255, 226), text_color=(226, 244, 239)))
        ly += 66

        self._algo_label_pos = (lx, ly)
        algo_names = [ALGORITHM_LABELS[a] for a in ALGORITHM_OPTIONS]
        self._algo = Dropdown(pygame.Rect(lx, ly + 26, col_w, 34), algo_names, self._font_small,
                              default_index=ALGORITHM_OPTIONS.index(self._method),
                              on_change=lambda i, _: setattr(self, '_method', ALGORITHM_OPTIONS[i]),
                              color_bg=(32, 58, 64), color_hover=(48, 86, 92),
                              color_selected=(83, 122, 92), text_color=(238, 250, 223))
        self._widgets.append(self._algo)
        ly += 86

        self._seed_label_pos = (lx, ly)
        self._seed_input = TextInput(pygame.Rect(lx, ly + 26, col_w - 96, 34), self._font_small,
                                     placeholder="留空=随机", default_text=str(self._seed),
                                     color_bg=(32, 58, 64), color_active_bg=(44, 78, 86),
                                     color_text=(238, 250, 223), color_cursor=(255, 218, 105))
        self._widgets.append(self._seed_input)
        self._buttons.append(Button(pygame.Rect(lx + col_w - 86, ly + 26, 86, 34), "随机",
                                    self._font_small, callback=self._randomize_seed,
                                    color_normal=(79, 105, 128), color_hover=(96, 128, 156)))
        ly += 102

        self._sliders.append(Slider(pygame.Rect(lx, ly, col_w, 18), "目标分数 k", self._font_small,
                                     0.5, 8.0, 0.1, self._k,
                                     on_change=lambda v: setattr(self, '_k', v),
                                     track_color=(42, 69, 78), fill_color=(169, 206, 255),
                                     handle_color=(235, 246, 255), text_color=(226, 244, 239)))

        btn_y = py + panel_h - 68
        self._start_btn = Button(pygame.Rect(lx, btn_y, 196, 46), "开始游戏", self._font,
                                 color_normal=(50, 142, 84), color_hover=(68, 171, 104),
                                 callback=self._start_game)
        self._buttons.append(self._start_btn)
        self._buttons.append(Button(pygame.Rect(lx + 218, btn_y, 196, 46), "返回主菜单",
                                    self._font_small, color_normal=(130, 62, 62),
                                    color_hover=(160, 76, 76), callback=lambda: self.manager.pop()))
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
        config = {"rows": self._rows, "cols": self._cols, "seed": seed,
                  "k": self._k, "method": self._method, **strategy}
        from game.scenes.gameplay import GameplayScene
        self.manager.replace(GameplayScene(self.manager, config=config))

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.manager.pop()
            return

        # Expanded dropdowns get first chance so lower inputs/buttons do not steal clicks.
        for w in self._widgets:
            if getattr(w, '_expanded', False) and hasattr(w, 'handle_event'):
                if w.handle_event(event):
                    return

        for s in self._sliders:
            if s.handle_event(event):
                return
        for w in self._widgets:
            if hasattr(w, 'handle_event'):
                if w.handle_event(event):
                    return
        for btn in self._buttons:
            if btn.handle_event(event):
                return

    def update(self, dt: float) -> None:
        if hasattr(self, '_seed_input'):
            self._seed_input.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        if self._needs_layout:
            self._layout(surface)
        draw_background(surface, "config")
        sw = surface.get_width()

        self._render_header(surface, sw)
        self._panel.render(surface)
        self._preview_panel.render(surface)
        self._render_config_panel(surface)
        self._render_preview(surface)

        for s in self._sliders:
            s.render(surface)
        expanded_widgets = []
        for w in self._widgets:
            if getattr(w, '_expanded', False):
                expanded_widgets.append(w)
            elif hasattr(w, 'render'):
                w.render(surface)
        for btn in self._buttons:
            btn.render(surface)
        for w in expanded_widgets:
            w.render(surface)

    def _render_header(self, surface: pygame.Surface, sw: int) -> None:
        header = pygame.Rect(72, 26, sw - 144, 52)
        pygame.draw.rect(surface, (10, 18, 25, 172), header, border_radius=10)
        pygame.draw.rect(surface, (255, 217, 114, 132), header, width=1, border_radius=10)
        Label("新 游 戏", self._font_title, (255, 218, 105)).render(surface, header.x + 24, header.y + 6)
        Label("配置迷宫规模、生成算法和资源压力", self._font_small, (210, 225, 225)).render(
            surface, header.x + 210, header.y + 17
        )

    def _render_config_panel(self, surface: pygame.Surface) -> None:
        rect = self._panel.rect
        Label("迷宫参数", self._font, (226, 244, 239)).render(surface, rect.x + 28, rect.y + 24)
        Label("生成前设置", self._font_tiny, (152, 185, 188)).render(surface, rect.x + 30, rect.y + 58)
        pygame.draw.line(surface, (93, 142, 154), (rect.x + 28, rect.y + 78), (rect.right - 28, rect.y + 78), 1)

        Label("生成算法", self._font_small, (216, 232, 229)).render(surface, *self._algo_label_pos)
        Label(ALGORITHM_HELP.get(self._method, ""), self._font_tiny, (150, 180, 178)).render(
            surface, self._algo_label_pos[0], self._algo_label_pos[1] + 64
        )
        Label("随机种子", self._font_small, (216, 232, 229)).render(surface, *self._seed_label_pos)
        Label("相同种子会生成相同迷宫", self._font_tiny, (150, 180, 178)).render(
            surface, self._seed_label_pos[0], self._seed_label_pos[1] + 64
        )

        summary_y = rect.bottom - 122
        summary = pygame.Rect(rect.x + 28, summary_y, rect.width - 56, 42)
        pygame.draw.rect(surface, (12, 24, 31), summary, border_radius=8)
        pygame.draw.rect(surface, (78, 130, 145), summary, width=1, border_radius=8)
        Label(f"{self._rows} x {self._cols}", self._font_small, (255, 218, 105)).render(surface, summary.x + 14, summary.y + 10)
        Label(f"k = {self._k:.1f}", self._font_small, (136, 222, 160)).render(surface, summary.x + 142, summary.y + 10)
        Label(self._method, self._font_small, (169, 206, 255)).render(surface, summary.x + 256, summary.y + 10)

    def _preview_seed(self) -> int:
        if hasattr(self, '_seed_input'):
            value = self._seed_input.text.strip()
            if value:
                try:
                    return int(value)
                except ValueError:
                    return DEFAULT_SEED
        return int(self._seed)

    def _get_preview_maze(self):
        seed = self._preview_seed()
        rows = max(5, min(31, int(self._rows)))
        cols = max(5, min(31, int(self._cols)))
        key = (rows, cols, seed, self._method)
        if key == self._preview_cache_key and self._preview_maze is not None:
            return self._preview_maze
        try:
            from game.maze.generator import Maze
            maze = Maze.generate(rows=rows, cols=cols, seed=seed, generation_method=self._method)
        except Exception:
            maze = None
        self._preview_cache_key = key
        self._preview_maze = maze
        return maze

    def _render_preview(self, surface: pygame.Surface) -> None:
        rect = self._preview_panel.rect
        Label("实时预览", self._font, (238, 250, 223)).render(surface, rect.x + 26, rect.y + 24)
        Label("按当前行列和种子生成的结构预览", self._font_tiny, (180, 206, 168)).render(
            surface, rect.x + 28, rect.y + 58
        )
        pygame.draw.line(surface, (127, 166, 97), (rect.x + 26, rect.y + 78), (rect.right - 26, rect.y + 78), 1)

        area = pygame.Rect(rect.x + 34, rect.y + 100, rect.width - 68, rect.height - 180)
        pygame.draw.rect(surface, (15, 33, 27), area, border_radius=10)
        pygame.draw.rect(surface, (123, 166, 91), area, width=2, border_radius=10)

        maze = self._get_preview_maze()
        rows = maze.rows if maze is not None else max(5, min(31, int(self._rows)))
        cols = maze.cols if maze is not None else max(5, min(31, int(self._cols)))
        cell = max(6, min(area.width // cols, area.height // rows))
        maze_w = cell * cols
        maze_h = cell * rows
        ox = area.centerx - maze_w // 2
        oy = area.centery - maze_h // 2
        from game.maze import SYMBOLS
        for r in range(rows):
            for c in range(cols):
                content = maze.grid[r][c].content if maze is not None else SYMBOLS["wall"]
                if content == SYMBOLS["wall"]:
                    color = (76, 94, 70)
                elif content == SYMBOLS["start"]:
                    color = (80, 220, 130)
                elif content == SYMBOLS["end"]:
                    color = (88, 165, 255)
                elif content == SYMBOLS["coin"]:
                    color = (238, 196, 68)
                elif content == SYMBOLS["trap"]:
                    color = (218, 88, 84)
                elif content == SYMBOLS["boss"]:
                    color = (178, 100, 226)
                else:
                    color = (220, 201, 139)
                pygame.draw.rect(surface, color, (ox + c * cell, oy + r * cell, max(1, cell - 1), max(1, cell - 1)))

        info_y = rect.bottom - 62
        for i, (label, value, color) in enumerate((
            ("规模", f"{self._rows} x {self._cols}", (255, 218, 105)),
            ("算法", ALGORITHM_LABELS.get(self._method, self._method), (178, 216, 255)),
            ("压力", f"k {self._k:.1f}", (148, 232, 164)),
        )):
            chip = pygame.Rect(rect.x + 34 + i * ((rect.width - 82) // 3), info_y, (rect.width - 100) // 3, 34)
            pygame.draw.rect(surface, (14, 31, 27), chip, border_radius=7)
            pygame.draw.rect(surface, color, chip, width=1, border_radius=7)
            Label(label, self._font_tiny, (190, 205, 190)).render(surface, chip.x + 10, chip.y + 9)
            Label(value, self._font_tiny, color).render(surface, chip.x + 58, chip.y + 9)
