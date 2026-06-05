"""Player: keyboard-controlled character entity."""

from __future__ import annotations

import pygame

from game.assets.manager import AssetManager
from game.constants import ASSET_PLAYER
from game.entities.base import Entity

# Direction vectors
DIRECTIONS: dict[int, tuple[int, int]] = {
    pygame.K_UP:    (-1, 0),
    pygame.K_w:     (-1, 0),
    pygame.K_DOWN:  (1, 0),
    pygame.K_s:     (1, 0),
    pygame.K_LEFT:  (0, -1),
    pygame.K_a:     (0, -1),
    pygame.K_RIGHT: (0, 1),
    pygame.K_d:     (0, 1),
}


class Player(Entity):
    """Player character controlled via keyboard (arrows or WASD)."""

    def __init__(
        self,
        grid_pos: tuple[int, int],
        cell_size: int,
        asset_manager: AssetManager,
        *groups: pygame.sprite.Group,
    ) -> None:
        super().__init__(ASSET_PLAYER, grid_pos, cell_size, asset_manager, *groups)

        # Stats
        self.steps_taken: int = 0
        self.resources: int = 0
        self.coins_collected: list[tuple[int, int]] = []
        self.traps_triggered: list[tuple[int, int]] = []
        self.bosses_encountered: int = 0
        self.finished: bool = False
        self.route: list[tuple[int, int]] = [grid_pos]

        # Pending action after animation completes
        self._pending_arrival_action: str | None = None

    # ---- Movement ----------------------------------------------------------

    def try_move(self, direction: tuple[int, int], maze) -> bool:
        """Attempt to move one cell in *direction*. Returns True if accepted."""
        if self.is_moving or self.finished:
            return False

        tr = self.grid_pos[0] + direction[0]
        tc = self.grid_pos[1] + direction[1]

        if not (0 <= tr < maze.rows and 0 <= tc < maze.cols):
            return False
        if not maze.grid[tr][tc].walkable:
            return False

        self.move_to((tr, tc), duration=0.10)
        return True

    def handle_keydown(self, key: int, maze) -> bool:
        """Process a keyboard input. Returns True if a move was started."""
        direction = DIRECTIONS.get(key)
        if direction is None:
            return False
        return self.try_move(direction, maze)

    # ---- Arrival handling --------------------------------------------------

    def on_arrive(self) -> None:
        """Called when movement animation finishes. Record position."""
        self.steps_taken += 1
        self.route.append(self._grid_pos)

    def check_cell(self, maze) -> str | None:
        """Check the current cell's content and handle pickups.

        Returns one of: 'coin', 'trap', 'boss', 'end', None.
        """
        from game.maze import SYMBOLS, COIN_VALUE, TRAP_VALUE

        content = maze.grid[self.grid_pos[0]][self.grid_pos[1]].content
        pos = self.grid_pos

        if content == SYMBOLS["coin"]:
            self.resources += COIN_VALUE
            self.coins_collected.append(pos)
            maze._set_content(pos[0], pos[1], SYMBOLS["floor"])
            return "coin"

        if content == SYMBOLS["trap"]:
            self.resources += TRAP_VALUE  # negative value
            self.traps_triggered.append(pos)
            maze._set_content(pos[0], pos[1], SYMBOLS["floor"])
            return "trap"

        if content == SYMBOLS["boss"]:
            self.bosses_encountered += 1
            maze._set_content(pos[0], pos[1], SYMBOLS["floor"])
            return "boss"

        if content == SYMBOLS["end"]:
            self.finished = True
            return "end"

        return None

    @property
    def score(self) -> float:
        return self.resources / max(1, self.steps_taken)

    @property
    def coin_count(self) -> int:
        return len(self.coins_collected)

    @property
    def trap_count(self) -> int:
        return len(self.traps_triggered)

    # ---- Reset -------------------------------------------------------------

    def reset(self, start_pos: tuple[int, int]) -> None:
        """Reset player state for a new game."""
        self.grid_pos = start_pos
        self._anim = None
        self.steps_taken = 0
        self.resources = 0
        self.coins_collected.clear()
        self.traps_triggered.clear()
        self.bosses_encountered = 0
        self.finished = False
        self.route = [start_pos]
