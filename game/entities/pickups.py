"""Pickup entities: Coin and Trap collectibles."""

from __future__ import annotations

import pygame

from game.assets.manager import AssetManager
from game.constants import ASSET_COIN, ASSET_TRAP
from game.entities.base import Entity


class Coin(Entity):
    """A collectible coin on the maze. Kills itself when collected."""

    def __init__(
        self,
        grid_pos: tuple[int, int],
        cell_size: int,
        asset_manager: AssetManager,
        *groups: pygame.sprite.Group,
    ) -> None:
        super().__init__(ASSET_COIN, grid_pos, cell_size, asset_manager, *groups)

    def collect(self) -> None:
        """Remove from all sprite groups."""
        self.kill()


class Trap(Entity):
    """A trap on the maze. Triggers on step, kills itself."""

    def __init__(
        self,
        grid_pos: tuple[int, int],
        cell_size: int,
        asset_manager: AssetManager,
        *groups: pygame.sprite.Group,
    ) -> None:
        super().__init__(ASSET_TRAP, grid_pos, cell_size, asset_manager, *groups)

    def trigger(self) -> None:
        """Remove from all sprite groups."""
        self.kill()
