"""Visibility system: 3×3 fog-of-war around the player.

Cells within Manhattan distance ≤ VISIBILITY_RANGE from the player are "visible"
and rendered at full brightness. Cells the player has previously visited are
"explored" and shown dimmed. Never-visited cells are fully covered by fog.
"""

from __future__ import annotations

import pygame

from game.constants import (
    ASSET_FOG, ASSET_FOG_DIM, VISIBILITY_RANGE,
    COLOR_FOG, COLOR_FOG_DIM,
)

# A per-game state object (not a sprite — we overlay fog surfaces)
from game.assets.manager import AssetManager


class VisibilityManager:
    """Tracks which cells have been explored and produces fog overlays.

    Usage per frame::

        vismgr.update_visibility(player_pos)
        vismgr.render_fog(surface, camera, cell_size)
    """

    def __init__(self, rows: int, cols: int, asset_manager: AssetManager) -> None:
        self.rows = rows
        self.cols = cols
        self._asset_manager = asset_manager
        self._version = 0
        # explored[r][c] = True if the player has ever seen this cell
        self._explored: list[list[bool]] = [
            [False for _ in range(cols)] for _ in range(rows)
        ]
        # Currently visible cells (recomputed each frame)
        self._visible: set[tuple[int, int]] = set()

    # ---- Update ------------------------------------------------------------

    def update_visibility(self, center: tuple[int, int]) -> None:
        """Recompute visible cells from *center* and mark them as explored."""
        cr, cc = center
        old_visible = set(self._visible)
        changed = False
        self._visible.clear()
        for dr in range(-VISIBILITY_RANGE, VISIBILITY_RANGE + 1):
            for dc in range(-VISIBILITY_RANGE, VISIBILITY_RANGE + 1):
                if abs(dr) + abs(dc) <= VISIBILITY_RANGE:
                    r, c = cr + dr, cc + dc
                    if 0 <= r < self.rows and 0 <= c < self.cols:
                        self._visible.add((r, c))
                        if not self._explored[r][c]:
                            changed = True
                        self._explored[r][c] = True
        if changed or self._visible != old_visible:
            self._version += 1

    def is_visible(self, row: int, col: int) -> bool:
        return (row, col) in self._visible

    def is_explored(self, row: int, col: int) -> bool:
        return self._explored[row][col]

    @property
    def version(self) -> int:
        return self._version

    # ---- Fog rendering -----------------------------------------------------

    def render_fog(
        self,
        surface: pygame.Surface,
        cell_size: int,
        offset_x: int = 0,
        offset_y: int = 0,
    ) -> None:
        """Draw fog-of-war overlays on top of the maze area.

        - Cells that are visible: no overlay (clear).
        - Cells that are explored but not currently visible: dim fog overlay.
        - Cells that are never explored: opaque fog overlay.
        """
        for r in range(self.rows):
            for c in range(self.cols):
                if (r, c) in self._visible:
                    continue  # fully visible, no overlay

                px = offset_x + c * cell_size
                py = offset_y + r * cell_size

                if self._explored[r][c]:
                    # Dim overlay for explored-but-out-of-sight
                    fog = self._asset_manager.get_image(ASSET_FOG_DIM, (cell_size, cell_size))
                else:
                    # Full fog for unexplored
                    fog = self._asset_manager.get_image(ASSET_FOG, (cell_size, cell_size))

                surface.blit(fog, (px, py))

    # ---- Reset -------------------------------------------------------------

    def reset(self, rows: int, cols: int) -> None:
        self.rows = rows
        self.cols = cols
        self._explored = [
            [False for _ in range(self.cols)] for _ in range(self.rows)
        ]
        self._visible.clear()
        self._version += 1
