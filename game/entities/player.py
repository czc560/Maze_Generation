"""Player: keyboard-controlled character entity."""

from __future__ import annotations

import math

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

        # Visual movement state
        self._facing: tuple[int, int] = (0, 1)
        self._walk_phase: float = 0.0
        self._trail_timer: float = 0.0
        self._trail: list[dict] = []

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

        self._facing = direction
        self.move_to((tr, tc), duration=0.12)
        return True

    def handle_keydown(self, key: int, maze) -> bool:
        """Process a keyboard input. Returns True if a move was started."""
        direction = DIRECTIONS.get(key)
        if direction is None:
            return False
        return self.try_move(direction, maze)


    def update(self, dt: float) -> None:
        moving_before = self.is_moving
        super().update(dt)

        if self.is_moving or moving_before:
            self._walk_phase += dt * 18.0
            self._trail_timer += dt
            if self._trail_timer >= 0.025:
                self._trail_timer = 0.0
                self._trail.append({"center": self.rect.center, "age": 0.0, "life": 0.18})
        else:
            self._walk_phase *= max(0.0, 1.0 - dt * 10.0)

        for item in self._trail:
            item["age"] += dt
        self._trail = [item for item in self._trail if item["age"] < item["life"]]

    def render(self, surface: pygame.Surface) -> None:
        """Draw the player with walk squash, bob, shadow, and short motion trail."""
        if self.image is None:
            return

        for item in self._trail:
            life = max(0.001, item["life"])
            alpha = int(76 * (1.0 - item["age"] / life))
            ghost = pygame.transform.smoothscale(
                self.image,
                (max(1, int(self.cell_size * 0.86)), max(1, int(self.cell_size * 0.86))),
            ).convert_alpha()
            ghost.fill((120, 210, 255, alpha), special_flags=pygame.BLEND_RGBA_MULT)
            surface.blit(ghost, ghost.get_rect(center=item["center"]))

        cx, cy = self.rect.center
        progress = 0.0
        if self._anim is not None and self._anim.duration > 0:
            progress = max(0.0, min(1.0, self._anim.elapsed / self._anim.duration))
        step = abs(math.sin(progress * math.pi)) if self.is_moving else 0.0

        shadow_w = int(self.cell_size * (0.72 + 0.12 * (1.0 - step)))
        shadow_h = max(4, int(self.cell_size * 0.18))
        shadow = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 92), shadow.get_rect())
        surface.blit(shadow, shadow.get_rect(center=(cx, self.rect.bottom - max(2, self.cell_size // 14))))

        bob = int(-self.cell_size * 0.16 * step)
        lean_x = int(self._facing[1] * self.cell_size * 0.06 * step)
        lean_y = int(self._facing[0] * self.cell_size * 0.04 * step)
        scale_x = 1.0 + 0.08 * step
        scale_y = 1.0 - 0.05 * step
        draw_w = max(1, int(self.cell_size * scale_x))
        draw_h = max(1, int(self.cell_size * scale_y))

        sprite = pygame.transform.smoothscale(self.image, (draw_w, draw_h)).convert_alpha()
        if self._facing[1] < 0:
            sprite = pygame.transform.flip(sprite, True, False)
        if self.is_moving:
            angle = -self._facing[1] * 6.0 * step + self._facing[0] * 3.0 * step
            sprite = pygame.transform.rotate(sprite, angle)

        glow_size = max(8, int(self.cell_size * (0.78 + 0.18 * step)))
        glow = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
        pygame.draw.circle(glow, (95, 205, 255, int(28 + 34 * step)), (glow_size // 2, glow_size // 2), glow_size // 2)
        surface.blit(glow, glow.get_rect(center=(cx + lean_x, cy + bob + lean_y)))
        surface.blit(sprite, sprite.get_rect(center=(cx + lean_x, cy + bob + lean_y)))

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
