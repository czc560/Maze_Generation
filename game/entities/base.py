"""Entity: base sprite class for all visible game objects on the maze grid."""

from __future__ import annotations

import pygame

from game.assets.manager import AssetManager
from game.entities.animation import MoveAnimation
from game.constants import ASSET_BOSS, ASSET_COIN, ASSET_END, ASSET_FLOOR, ASSET_START


_FLOOR_BACKED_KEYS = {ASSET_COIN, ASSET_START, ASSET_END, ASSET_BOSS}


class Entity(pygame.sprite.Sprite):
    """A sprite anchored to a grid position that can animate between cells.

    Subclasses should call ``_load_image()`` in their ``__init__`` after
    setting ``self.asset_key``, or override the image loading entirely.
    """

    def __init__(
        self,
        asset_key: str,
        grid_pos: tuple[int, int],
        cell_size: int,
        asset_manager: AssetManager,
        *groups: pygame.sprite.Group,
    ) -> None:
        super().__init__(*groups)
        self.asset_key = asset_key
        self._grid_pos = grid_pos
        self.cell_size = cell_size
        self._asset_manager = asset_manager
        self._anim: MoveAnimation | None = None
        self._load_image()

    # ---- Grid position -----------------------------------------------------

    @property
    def grid_pos(self) -> tuple[int, int]:
        return self._grid_pos

    @grid_pos.setter
    def grid_pos(self, pos: tuple[int, int]) -> None:
        """Instant teleport — no animation."""
        self._grid_pos = pos
        self._anim = None
        self._sync_rect()

    def move_to(self, target: tuple[int, int], duration: float = 0.12) -> None:
        """Start an animation from current position to *target*."""
        self._anim = MoveAnimation(self._grid_pos, target, duration)

    @property
    def is_moving(self) -> bool:
        return self._anim is not None and not self._anim.finished

    # ---- Sprite lifecycle --------------------------------------------------

    def update(self, dt: float) -> None:
        """Advance movement animation and sync rect."""
        if self._anim is not None:
            finished = self._anim.update(dt)
            if finished:
                self._grid_pos = self._anim.to_pos
                self._anim = None
                self.on_arrive()
            self._sync_rect()

    def on_arrive(self) -> None:
        """Override to react when a move animation completes."""

    # ---- Image loading -----------------------------------------------------

    def _load_image(self) -> None:
        size = (self.cell_size, self.cell_size)
        if self.asset_key in _FLOOR_BACKED_KEYS:
            floor = self._asset_manager.get_image(ASSET_FLOOR, size)
            icon_size = max(4, int(self.cell_size * 0.78))
            icon = self._asset_manager.get_image(self.asset_key, (icon_size, icon_size))
            self.image = floor.copy()
            self.image.blit(icon, icon.get_rect(center=self.image.get_rect().center))
        else:
            self.image = self._asset_manager.get_image(self.asset_key, size)
        self.rect = self.image.get_rect()
        self._sync_rect()

    def set_cell_size(self, size: int) -> None:
        """Update cell size and reload the image."""
        self.cell_size = size
        self._load_image()
        self._sync_rect()

    def refresh_image(self) -> None:
        """Force reload the image (e.g. after asset change)."""
        self._load_image()
        self._sync_rect()

    # ---- Rect sync ---------------------------------------------------------

    def _sync_rect(self) -> None:
        """Position self.rect at the screen pixel for the current (possibly animated) grid pos."""
        if self._anim is not None and not self._anim.finished:
            gpos = self._anim.current_pos()
        else:
            gpos = self._grid_pos

        self.rect.topleft = (
            int(gpos[1] * self.cell_size),
            int(gpos[0] * self.cell_size),
        )

    @property
    def pixel_pos(self) -> tuple[int, int]:
        """Top-left pixel position of this sprite."""
        return self.rect.topleft
