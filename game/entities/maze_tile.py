"""MazeTile: one cell of the maze grid. Content-immutable after creation."""

from __future__ import annotations

import pygame

from game.assets.manager import AssetManager
from game.constants import (
    ASSET_WALL, ASSET_FLOOR, ASSET_START, ASSET_END,
    ASSET_BOSS, ASSET_COIN, ASSET_TRAP,
)


# Map maze content characters → asset keys
CONTENT_TO_ASSET: dict[str, str] = {}

_initialized = False


def _init_mapping() -> None:
    """Lazy-init the content→asset mapping from core config."""
    global _initialized, CONTENT_TO_ASSET
    if _initialized:
        return
    from game.maze import SYMBOLS
    CONTENT_TO_ASSET = {
        SYMBOLS["wall"]:  ASSET_WALL,
        SYMBOLS["floor"]: ASSET_FLOOR,
        SYMBOLS["start"]: ASSET_START,
        SYMBOLS["end"]:   ASSET_END,
        SYMBOLS["boss"]:  ASSET_BOSS,
        SYMBOLS["coin"]:  ASSET_COIN,
        SYMBOLS["trap"]:  ASSET_TRAP,
    }
    _initialized = True


class MazeTile(pygame.sprite.Sprite):
    """One cell of the maze grid. Not interactive — pure visual.

    This is NOT an Entity subclass because tiles don't move or animate.
    They are organized in a static sprite group for efficient drawing.
    """

    def __init__(
        self,
        content: str,
        grid_pos: tuple[int, int],
        cell_size: int,
        asset_manager: AssetManager,
    ) -> None:
        super().__init__()
        _init_mapping()

        self.content = content
        self.grid_pos = grid_pos
        self.cell_size = cell_size

        asset_key = CONTENT_TO_ASSET.get(content, ASSET_WALL)
        self.image = asset_manager.get_image(asset_key, (cell_size, cell_size))
        self.rect = self.image.get_rect()
        self.rect.topleft = (grid_pos[1] * cell_size, grid_pos[0] * cell_size)

    def set_cell_size(self, size: int) -> None:
        """Re-render at a new cell size (used when maze is regenerated)."""
        self.cell_size = size
        # Re-trigger image loading — handled by whoever regenerates
