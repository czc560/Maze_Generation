"""GameplayScene: main maze exploration.

Player: arrow keys / WASD.  AI: press TAB to toggle auto-run (greedy or DQN).
"""

from __future__ import annotations

import random
import pygame

from game.scenes.base import Scene
from game.constants import (
    COLOR_BG, COLOR_TEXT, COLOR_TEXT_DIM, COLOR_ACCENT,
    COLOR_GOLD, COLOR_RED, COLOR_GREEN,
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
        self._hud_font = self._am.get_font(None, 20)
        self._hud_font_small = self._am.get_font(None, 16)
        self._hud_font_large = self._am.get_font(None, 26)
        self._hud_panel = Panel(
            pygame.Rect(HUD_PANEL_X, MAZE_AREA_TOP, HUD_PANEL_WIDTH, MAZE_AREA_HEIGHT),
            color=(30, 30, 42), border_color=(55, 55, 75),
        )

        self._boss_battle_result: dict | None = None
        self._needs_rebuild = True

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
            if not result.get("victory"):
                self._goto_results(player_lost=True)
                return
            self._boss_battle_result = None

    # ========================================================================
    #  Maze generation
    # ========================================================================

    def _build_maze(self) -> None:
        from game.maze.generator import Maze
        from game.maze import SYMBOLS
        from game.maze.strategies import make_normalized_strategies
        from game.battle import generate_game_rules

        coin_strategy, trap_strategy = make_normalized_strategies(self._k, spread=1.2)
        self._maze = Maze.generate(
            rows=self._rows, cols=self._cols, seed=self._seed,
            generation_method=self._method,
            coin_strategy=coin_strategy, trap_strategy=trap_strategy,
        )
        self._game_rules = generate_game_rules(self._maze)

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
        elif key == pygame.K_ESCAPE:
            from game.scenes.pause import PauseScene
            self.manager.push(PauseScene(self.manager))

    # ========================================================================
    #  Boss / Results
    # ========================================================================

    def _trigger_boss_battle(self) -> None:
        from game.scenes.boss_battle import BossBattleScene
        coin_total = self._player.resources if self._player else 0
        auto_battle = self._config.get("auto_battle", False)
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
        surface.fill(COLOR_BG)
        self._render_maze(surface)
        self._render_hud(surface)

    def _render_maze(self, surface: pygame.Surface) -> None:
        if self._maze_surface is None or self._player is None:
            return
        ms = self._maze_surface
        ms.fill((18, 18, 24))
        ox, oy = self._maze_render_offset

        self._tile_group.draw(ms)
        self._marker_group.draw(ms)
        self._pickup_group.draw(ms)

        if self._player.image:
            ms.blit(self._player.image, self._player.rect)

        self._visibility.render_fog(ms, self._cell_size)
        surface.blit(ms, (ox, oy))
        pygame.draw.rect(surface, (70, 70, 90),
                         (ox - 1, oy - 1, ms.get_width() + 2, ms.get_height() + 2), 1)

    def _render_hud(self, surface: pygame.Surface) -> None:
        if self._player is None:
            return
        self._hud_panel.render(surface)
        p = self._player
        x = HUD_PANEL_X + 15
        y = MAZE_AREA_TOP + 15

        Label("— 状态面板 —", self._hud_font_large, COLOR_ACCENT).render(surface, x, y)
        y += 40

        for label, value in [
            ("步数", str(p.steps_taken)), ("金币", str(p.resources)),
            ("收集", str(p.coin_count)), ("陷阱", str(p.trap_count)),
            ("得分", f"{p.score:.1f}"),
        ]:
            Label(f"{label}:  {value}", self._hud_font_small, COLOR_TEXT).render(surface, x + 10, y)
            y += 24

        # AI status
        y += 6
        ai_text = "AI: ON  (TAB切换)" if self._ai_active else "AI: OFF (TAB切换)"
        ai_color = COLOR_GREEN if self._ai_active else COLOR_TEXT_DIM
        Label(ai_text, self._hud_font_small, ai_color).render(surface, x, y)
        y += 26

        # Boss info
        if self._game_rules:
            y += 8
            bh = self._game_rules.get("boss_hp", [])
            Label(f"Boss: {len(bh)}  |  回合限制: {self._game_rules.get('min_rounds','?')}  |  重试: {self._game_rules.get('coin_consumption','?')}G",
                  self._hud_font_small, COLOR_TEXT).render(surface, x, y)

        # Controls
        y = MAZE_AREA_TOP + MAZE_AREA_HEIGHT - 130
        Label("— 操作 —", self._hud_font, COLOR_TEXT_DIM).render(surface, x, y)
        y += 26
        for ctrl in ("↑↓←→/WASD  移动", "TAB  切换AI自动", "Esc  暂停"):
            Label(ctrl, self._hud_font_small, COLOR_TEXT_DIM).render(surface, x + 5, y)
            y += 22
