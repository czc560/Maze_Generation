"""GameplayScene: main maze exploration.

Player: arrow keys / WASD.  AI: press TAB to toggle auto-run (greedy or DQN).
"""

from __future__ import annotations

import random
import pygame

from game.scenes.base import Scene
from game.constants import (
    COLOR_TEXT, COLOR_TEXT_DIM,
    COLOR_GOLD, COLOR_RED, COLOR_GREEN,
    COLOR_OPTIMAL_HIGHLIGHT, COLOR_OPTIMAL_DIM, COLOR_OPTIMAL_BORDER,
    MAZE_AREA_LEFT, MAZE_AREA_TOP, MAZE_AREA_WIDTH, MAZE_AREA_HEIGHT,
    HUD_PANEL_X, HUD_PANEL_WIDTH,
    GameEvent,
)
from game.entities.maze_tile import MazeTile
from game.entities.player import Player
from game.entities.pickups import Coin, Trap
from game.entities.markers import StartPortal, EndPortal, BossMarker
from game.visibility import VisibilityManager
from game.ui.label import Label
from game.ui.panel import Panel
from game.ui.backgrounds import draw_background
from game.ui.theme import FONT_UI_BOLD, FONT_UI_LIGHT, FONT_UI_REGULAR


class GameplayScene(Scene):
    """Main gameplay — explore the maze, collect coins, fight bosses."""

    def __init__(self, manager, config: dict | None = None) -> None:
        super().__init__(manager)
        self._config = config or {}
        self._am = self.engine.asset_manager

        # Maze params
        self._rows = self._config.get("rows", 15)
        self._cols = self._config.get("cols", 15)
        self._seed = self._config.get("seed", random.randint(0, 2**31 - 1))
        self._k = self._config.get("k", 4.0)
        self._method = self._config.get("method", "mst")

        # AI config
        self._ai_strategy = self._config.get("ai_strategy", "heuristic_greedy")
        self._dqn_model_path = self._config.get("dqn_model_path", "")

        # Boss skills
        self._skills = self._config.get("skills", [[8, 4], [2, 0], [4, 2], [6, 3]])

        # Runtime
        self._maze = None
        self._game_rules = None
        self._cell_size = 32
        self._max_resources = 1

        self._tile_group = pygame.sprite.Group()
        self._pickup_group = pygame.sprite.Group()
        self._marker_group = pygame.sprite.Group()
        self._entity_group = pygame.sprite.Group()

        # Tile lookup by (row, col) — for updating tile images after pickup
        self._tile_map: dict[tuple[int, int], MazeTile] = {}

        self._player: Player | None = None
        self._visibility: VisibilityManager | None = None

        # AI
        self._ai_agent = None   # GreedyAI or DQNAI instance
        self._ai_active = False
        self._ai_step_timer = 0.0
        self._ai_step_interval = 0.25  # seconds between AI steps

        self._maze_surface: pygame.Surface | None = None
        self._maze_render_offset = (MAZE_AREA_LEFT, MAZE_AREA_TOP)

        # HUD
        self._hud_font = self._am.get_font(FONT_UI_REGULAR, 20)
        self._hud_font_small = self._am.get_font(FONT_UI_LIGHT, 15)
        self._hud_font_large = self._am.get_font(FONT_UI_BOLD, 26)
        self._hud_panel = Panel(
            pygame.Rect(HUD_PANEL_X, MAZE_AREA_TOP, HUD_PANEL_WIDTH, MAZE_AREA_HEIGHT),
            color=(17, 21, 31), border_color=(82, 94, 118),
        )

        self._boss_battle_result: dict | None = None
        self._needs_rebuild = True

        # Optimal path — two modes computed, 0=off, 1=free, 2=S→E
        self._optimal_free = None
        self._optimal_se = None
        self._show_optimal = 0
        self._optimal_overlay_cache_key = None
        self._optimal_overlay_surface: pygame.Surface | None = None

    # ========================================================================
    #  Lifecycle
    # ========================================================================

    def enter(self) -> None:
        if self._needs_rebuild:
            self._build_maze()
            self._needs_rebuild = False

    def resume(self) -> None:
        if self._boss_battle_result is not None:
            result = self._boss_battle_result

            # Sync resource changes from the boss battle before showing results.
            if self._player is not None:
                self._player.resources = int(
                    result.get("coins_remaining", self._player.resources)
                )

            if not result.get("victory"):
                self._goto_results(player_lost=True)
                return
            self._boss_battle_result = None

    # ========================================================================
    #  Maze generation
    # ========================================================================

    def _build_maze(self) -> None:
        from game.maze.generator import Maze
        from game.maze import SYMBOLS, COIN_VALUE
        from game.maze.strategies import make_normalized_strategies
        from game.battle import generate_game_rules

        coin_strategy, trap_strategy = make_normalized_strategies(self._k, spread=1.2)
        self._maze = Maze.generate(
            rows=self._rows, cols=self._cols, seed=self._seed,
            generation_method=self._method,
            coin_strategy=coin_strategy, trap_strategy=trap_strategy,
        )
        self._game_rules = generate_game_rules(self._maze, player_skills=self._skills)
        coin_total = sum(
            1
            for r in range(self._maze.rows)
            for c in range(self._maze.cols)
            if self._maze.grid[r][c].content == SYMBOLS["coin"]
        ) * COIN_VALUE
        self._max_resources = max(1, coin_total)

        # Cell size
        self._cell_size = min(
            MAZE_AREA_WIDTH // self._maze.cols,
            MAZE_AREA_HEIGHT // self._maze.rows,
        )
        self._am.clear_image_cache()
        self._am.preload_all(self._cell_size)

        mw = self._maze.cols * self._cell_size
        mh = self._maze.rows * self._cell_size
        self._maze_surface = pygame.Surface((mw, mh))

        for g in (self._tile_group, self._pickup_group, self._marker_group, self._entity_group):
            g.empty()
        self._tile_map.clear()

        # Tiles (build lookup map)
        for r in range(self._maze.rows):
            for c in range(self._maze.cols):
                tile = MazeTile(self._maze.grid[r][c].content, (r, c), self._cell_size, self._am)
                self._tile_group.add(tile)
                self._tile_map[(r, c)] = tile

        # Pickups & markers
        for r in range(self._maze.rows):
            for c in range(self._maze.cols):
                ct, pos = self._maze.grid[r][c].content, (r, c)
                if ct == SYMBOLS["coin"]:
                    Coin(pos, self._cell_size, self._am, self._pickup_group)
                elif ct == SYMBOLS["trap"]:
                    Trap(pos, self._cell_size, self._am, self._pickup_group)
                elif ct == SYMBOLS["start"]:
                    StartPortal(pos, self._cell_size, self._am, self._marker_group)
                elif ct == SYMBOLS["end"]:
                    EndPortal(pos, self._cell_size, self._am, self._marker_group)
                elif ct == SYMBOLS["boss"]:
                    BossMarker(pos, self._cell_size, self._am, self._marker_group)

        # Player
        self._player = Player(self._maze.start, self._cell_size, self._am, self._entity_group)

        # AI agent
        self._init_ai()
        self._ai_active = False

        # Visibility
        self._visibility = VisibilityManager(self._maze.rows, self._maze.cols, self._am)
        self._visibility.update_visibility(self._player.grid_pos)

        self._boss_battle_result = None

        # Compute optimal resource-collection path — both free and S→E modes
        from game.maze.optimal_path import compute_optimal_path
        self._optimal_free = compute_optimal_path(self._maze, require_end=False)
        self._optimal_se = compute_optimal_path(self._maze, require_end=True)
        self._show_optimal = 0
        self._optimal_overlay_cache_key = None
        self._optimal_overlay_surface = None

    def _init_ai(self) -> None:
        """Create the AI agent based on config."""
        algo = self._ai_strategy  # "simple_greedy" | "memory_greedy" | "dqn"
        if algo == "dqn":
            from game.ai.dqn import DQNAI
            self._ai_agent = DQNAI(self._maze, model_path=self._dqn_model_path,
                                   epsilon=float(self._config.get("dqn_epsilon", 0.05)))
        elif algo == "simple_greedy":
            from game.ai.greedy import SimpleGreedy
            self._ai_agent = SimpleGreedy(
                self._maze,
                coin_weight=float(self._config.get("coin_weight", 1.2)),
                trap_weight=float(self._config.get("trap_weight", 0.8)),
                end_weight=float(self._config.get("end_weight", 1.6)),
            )
        else:  # memory_greedy (default)
            from game.ai.greedy import MemoryGreedy
            self._ai_agent = MemoryGreedy(
                self._maze,
                coin_weight=float(self._config.get("coin_weight", 1.2)),
                trap_weight=float(self._config.get("trap_weight", 0.8)),
                end_weight=float(self._config.get("end_weight", 1.6)),
                visited_penalty=float(self._config.get("visited_penalty", 2.0)),
                unvisited_bonus=float(self._config.get("unvisited_bonus", 0.5)),
            )

    # ========================================================================
    #  Events
    # ========================================================================

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            self._handle_keydown(event)
        if event.type == GameEvent.BOSS_BATTLE_OVER:
            self._boss_battle_result = getattr(event, 'result', None)

    def _handle_keydown(self, event: pygame.event.Event) -> None:
        if self._player is None:
            return
        key = event.key
        if key in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT,
                    pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d):
            self._player.handle_keydown(key, self._maze)
            self._ai_active = False  # manual input disables AI
        elif key == pygame.K_TAB:
            self._ai_active = not self._ai_active
        elif key == pygame.K_o:
            self._show_optimal = (self._show_optimal + 1) % 3
        elif key == pygame.K_ESCAPE:
            from game.scenes.pause import PauseScene
            self.manager.push(PauseScene(self.manager))

    # ========================================================================
    #  Boss / Results
    # ========================================================================

    def _trigger_boss_battle(self) -> None:
        from game.scenes.boss_battle import BossBattleScene
        coin_total = self._player.resources if self._player else 0
        auto_battle = bool(self._ai_active or self._config.get("auto_battle", False))
        self.manager.push(BossBattleScene(
            self.manager, game_rules=self._game_rules,
            player_skills=[list(s) for s in self._skills],
            coin_total=coin_total,
            battle_mode=auto_battle,
            auto_speed=0.6,
        ))

    def _goto_results(self, player_lost: bool = False) -> None:
        from game.scenes.results import ResultsScene
        self.manager.replace(ResultsScene(
            self.manager, maze=self._maze, player=self._player,
            game_rules=self._game_rules, player_lost=player_lost,
            optimal_result=(self._optimal_free if self._show_optimal == 1
                            else self._optimal_se if self._show_optimal == 2
                            else self._optimal_free),
        ))

    # ========================================================================
    #  Update
    # ========================================================================

    def update(self, dt: float) -> None:
        if self._player is None:
            return

        self._entity_group.update(dt)

        # AI auto-run
        if self._ai_active and self._ai_agent and not self._player.is_moving:
            if not self._ai_agent.is_finished() and not self._player.finished:
                self._ai_step_timer += dt
                if self._ai_step_timer >= self._ai_step_interval:
                    self._ai_step_timer = 0.0
                    self._ai_step()

        # Player arrival
        if not self._player.is_moving and not self._player.finished:
            result = self._player.check_cell(self._maze)
            if result == "boss":
                self._trigger_boss_battle()
            elif result == "end":
                self._goto_results()
                return
            elif result in ("coin", "trap"):
                pos = self._player.grid_pos
                self._on_pickup(pos, result)

        if self._visibility and self._player:
            self._visibility.update_visibility(self._player.grid_pos)

    def _ai_step(self) -> None:
        """Have the AI move the player one step."""
        if self._ai_agent is None or self._player is None:
            return
        state = self._ai_agent.step()
        target = state.position
        # Move player sprite toward AI's new position
        dr = target[0] - self._player.grid_pos[0]
        dc = target[1] - self._player.grid_pos[1]
        if (dr, dc) in ((0, 0),):
            return
        direction = (dr, dc)
        self._player.try_move(direction, self._maze)

    def _on_pickup(self, pos: tuple[int, int], kind: str) -> None:
        """Remove pickup sprite AND update the tile to floor."""
        # Kill pickup sprite
        for sprite in list(self._pickup_group):
            if sprite.grid_pos == pos:
                sprite.kill()
        # Update tile to floor
        tile = self._tile_map.get(pos)
        if tile:
            from game.maze import SYMBOLS
            from game.constants import ASSET_FLOOR
            tile.image = self._am.get_image(ASSET_FLOOR, (self._cell_size, self._cell_size))
            # Also update marker if relevant
            for sprite in list(self._marker_group):
                if sprite.grid_pos == pos and kind == "boss":
                    sprite.kill()

        self._am.play_sound(kind, 0.6)

    # ========================================================================
    #  Render
    # ========================================================================

    def render(self, surface: pygame.Surface) -> None:
        draw_background(surface, "gameplay")
        self._render_maze(surface)
        self._render_hud(surface)

    def _render_optimal_overlay(self, surface: pygame.Surface) -> None:
        """Draw cached gold highlights and path lines for the optimal walk."""
        if self._show_optimal == 0 or self._visibility is None or self._maze is None:
            return

        result = self._optimal_free if self._show_optimal == 1 else self._optimal_se
        if result is None:
            return

        cs = self._cell_size
        cache_key = (
            self._show_optimal,
            id(result),
            cs,
            self._maze.rows,
            self._maze.cols,
            self._visibility.version,
        )

        if self._optimal_overlay_cache_key != cache_key or self._optimal_overlay_surface is None:
            mw = self._maze.cols * cs
            mh = self._maze.rows * cs
            overlay = pygame.Surface((mw, mh), pygame.SRCALPHA)
            line_width = max(3, cs // 6)
            half = cs // 2

            for r, c in result.visited_cells:
                if self._visibility.is_visible(r, c):
                    alpha_fill, alpha_border = 70, 120
                    color = COLOR_OPTIMAL_HIGHLIGHT
                elif self._visibility.is_explored(r, c):
                    alpha_fill, alpha_border = 40, 75
                    color = COLOR_OPTIMAL_DIM
                else:
                    alpha_fill, alpha_border = 18, 42
                    color = COLOR_OPTIMAL_DIM

                rect = pygame.Rect(c * cs, r * cs, cs, cs)
                pygame.draw.rect(overlay, (*color, alpha_fill), rect)
                pygame.draw.rect(overlay, (*COLOR_OPTIMAL_BORDER, alpha_border), rect, 1)

            path = result.path
            for i in range(len(path) - 1):
                (r1, c1), (r2, c2) = path[i], path[i + 1]
                visible = self._visibility.is_visible(r1, c1) or self._visibility.is_visible(r2, c2)
                explored = self._visibility.is_explored(r1, c1) or self._visibility.is_explored(r2, c2)
                if visible:
                    alpha = 200
                elif explored:
                    alpha = 120
                else:
                    alpha = 60

                x1, y1 = c1 * cs + half, r1 * cs + half
                x2, y2 = c2 * cs + half, r2 * cs + half
                pygame.draw.line(overlay, (255, 240, 180, alpha), (x1, y1), (x2, y2), line_width)

            self._optimal_overlay_surface = overlay
            self._optimal_overlay_cache_key = cache_key

        surface.blit(self._optimal_overlay_surface, (0, 0))

    def _render_maze(self, surface: pygame.Surface) -> None:
        if self._maze_surface is None or self._player is None:
            return
        ms = self._maze_surface
        ms.fill((18, 18, 24))
        ox, oy = self._maze_render_offset

        self._tile_group.draw(ms)
        self._marker_group.draw(ms)
        self._pickup_group.draw(ms)

        self._player.render(ms)

        self._visibility.render_fog(ms, self._cell_size)
        self._render_optimal_overlay(ms)

        frame = pygame.Rect(ox - 10, oy - 10, ms.get_width() + 20, ms.get_height() + 20)
        shadow = pygame.Surface((frame.width + 14, frame.height + 14), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 96), shadow.get_rect(), border_radius=10)
        surface.blit(shadow, (frame.x + 7, frame.y + 9))
        pygame.draw.rect(surface, (21, 27, 37), frame, border_radius=8)
        pygame.draw.rect(surface, (88, 125, 148), frame, width=2, border_radius=8)
        pygame.draw.rect(surface, (188, 224, 255), frame.inflate(-8, -8), width=1, border_radius=6)
        surface.blit(ms, (ox, oy))

    def _draw_hud_bar(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        ratio: float,
        fill: tuple[int, int, int],
        bg: tuple[int, int, int] = (30, 35, 46),
    ) -> None:
        ratio = max(0.0, min(1.0, ratio))
        pygame.draw.rect(surface, bg, rect, border_radius=5)
        if ratio > 0:
            fill_rect = rect.copy()
            fill_rect.width = max(4, int(rect.width * ratio))
            pygame.draw.rect(surface, fill, fill_rect, border_radius=5)
        pygame.draw.rect(surface, (82, 91, 111), rect, width=1, border_radius=5)

    def _render_hud_icon(self, surface: pygame.Surface, key: str, center: tuple[int, int], size: int) -> None:
        icon = self._am.get_image(key, (size, size))
        rect = icon.get_rect(center=center)
        surface.blit(icon, rect)

    def _draw_stat_row(
        self,
        surface: pygame.Surface,
        y: int,
        label: str,
        value: str,
        color: tuple[int, int, int],
    ) -> int:
        x = HUD_PANEL_X + 18
        pygame.draw.circle(surface, color, (x + 6, y + 11), 5)
        Label(label, self._hud_font_small, COLOR_TEXT_DIM).render(surface, x + 18, y)
        value_surf = self._hud_font_small.render(value, True, COLOR_TEXT)
        surface.blit(value_surf, (HUD_PANEL_X + HUD_PANEL_WIDTH - 18 - value_surf.get_width(), y))
        return y + 23

    def _render_hud(self, surface: pygame.Surface) -> None:
        if self._player is None:
            return
        self._hud_panel.render(surface)
        p = self._player
        x = HUD_PANEL_X + 16
        y = MAZE_AREA_TOP + 16
        panel_right = HUD_PANEL_X + HUD_PANEL_WIDTH - 16

        header = pygame.Rect(HUD_PANEL_X + 8, MAZE_AREA_TOP + 8, HUD_PANEL_WIDTH - 16, 112)
        pygame.draw.rect(surface, (24, 34, 48), header, border_radius=8)
        pygame.draw.rect(surface, (88, 137, 168), header, width=1, border_radius=8)
        self._render_hud_icon(surface, "player", (x + 38, y + 42), 68)
        Label("探索状态", self._hud_font_large, (190, 226, 255)).render(surface, x + 82, y + 10)
        ai_label = "AI 自动" if self._ai_active else "手动探索"
        ai_color = COLOR_GREEN if self._ai_active else COLOR_TEXT_DIM
        Label(ai_label, self._hud_font_small, ai_color).render(surface, x + 84, y + 44)
        mode_names = {0: "最优: 关", 1: "最优: 自由", 2: "最优: S-E"}
        Label(mode_names[self._show_optimal], self._hud_font_small, COLOR_GOLD if self._show_optimal else COLOR_TEXT_DIM).render(
            surface, x + 84, y + 68
        )

        y = MAZE_AREA_TOP + 138
        Label("资源", self._hud_font, COLOR_TEXT).render(surface, x, y)
        coin_ratio = min(1.0, max(0.0, p.resources / max(1, self._max_resources)))
        self._render_hud_icon(surface, "coin", (panel_right - 22, y + 12), 28)
        y += 29
        self._draw_hud_bar(surface, pygame.Rect(x, y, HUD_PANEL_WIDTH - 32, 12), coin_ratio, (238, 180, 57))
        y += 22
        y = self._draw_stat_row(surface, y, "金币", f"{p.resources}/{self._max_resources}", COLOR_GOLD)
        y = self._draw_stat_row(surface, y, "收集", str(p.coin_count), (88, 202, 255))
        y = self._draw_stat_row(surface, y, "陷阱", str(p.trap_count), COLOR_RED)
        y = self._draw_stat_row(surface, y, "步数", str(p.steps_taken), (154, 169, 196))
        y = self._draw_stat_row(surface, y, "效率", f"{p.score:.1f}", COLOR_GREEN)

        y += 8
        pygame.draw.line(surface, (71, 78, 96), (x, y), (panel_right, y), 1)
        y += 16
        Label("Boss", self._hud_font, COLOR_TEXT).render(surface, x, y)
        self._render_hud_icon(surface, "boss", (panel_right - 22, y + 12), 28)
        y += 30
        if self._game_rules:
            bh = self._game_rules.get("boss_hp", [])
            y = self._draw_stat_row(surface, y, "数量", str(len(bh)), (217, 94, 102))
            y = self._draw_stat_row(surface, y, "回合限制", str(self._game_rules.get("min_rounds", "?")), (235, 190, 91))
            y = self._draw_stat_row(surface, y, "重试消耗", f"{self._game_rules.get('coin_consumption', '?')}G", COLOR_GOLD)

        y += 8
        pygame.draw.line(surface, (71, 78, 96), (x, y), (panel_right, y), 1)
        y += 16
        mode_name = {0: "OFF", 1: "自由", 2: "S-E"}[self._show_optimal]
        result = self._optimal_free if self._show_optimal == 1 else self._optimal_se
        Label("最优参考", self._hud_font, COLOR_TEXT).render(surface, x, y)
        Label(mode_name, self._hud_font_small, COLOR_GOLD if self._show_optimal else COLOR_TEXT_DIM).render(
            surface, panel_right - 42, y + 4
        )
        y += 30
        if self._show_optimal > 0 and result is not None:
            y = self._draw_stat_row(surface, y, "理论最优", str(result.max_resource), COLOR_GOLD)
            y = self._draw_stat_row(
                surface, y, "硬币/陷阱", f"{result.coins_in_path}/{result.traps_in_path}", (88, 202, 255)
            )
        else:
            Label("按 O 循环显示", self._hud_font_small, COLOR_TEXT_DIM).render(surface, x, y)
            y += 23

        controls = pygame.Rect(HUD_PANEL_X + 10, MAZE_AREA_TOP + MAZE_AREA_HEIGHT - 118, HUD_PANEL_WIDTH - 20, 106)
        pygame.draw.rect(surface, (22, 25, 34), controls, border_radius=8)
        pygame.draw.rect(surface, (72, 82, 102), controls, width=1, border_radius=8)
        Label("操作", self._hud_font, COLOR_TEXT_DIM).render(surface, controls.x + 12, controls.y + 10)
        cy = controls.y + 38
        for ctrl in ("WASD / 方向键  移动", "TAB  AI 自动", "O  最优路径", "Esc  暂停"):
            Label(ctrl, self._hud_font_small, COLOR_TEXT_DIM).render(surface, controls.x + 12, cy)
            cy += 16
