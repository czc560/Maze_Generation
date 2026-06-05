"""Marker entities: StartPortal, EndPortal, BossMarker."""

from __future__ import annotations

import pygame

from game.assets.manager import AssetManager
from game.constants import ASSET_START, ASSET_END, ASSET_BOSS
from game.entities.base import Entity


class StartPortal(Entity):
    """Visual marker for the maze start position."""

    def __init__(
        self,
        grid_pos: tuple[int, int],
        cell_size: int,
        asset_manager: AssetManager,
        *groups: pygame.sprite.Group,
    ) -> None:
        super().__init__(ASSET_START, grid_pos, cell_size, asset_manager, *groups)


class EndPortal(Entity):
    """Visual marker for the maze end position."""

    def __init__(
        self,
        grid_pos: tuple[int, int],
        cell_size: int,
        asset_manager: AssetManager,
        *groups: pygame.sprite.Group,
    ) -> None:
        super().__init__(ASSET_END, grid_pos, cell_size, asset_manager, *groups)


class BossMarker(Entity):
    """Visual marker on a boss cell. Removed when boss is encountered."""

    def __init__(
        self,
        grid_pos: tuple[int, int],
        cell_size: int,
        asset_manager: AssetManager,
        *groups: pygame.sprite.Group,
    ) -> None:
        super().__init__(ASSET_BOSS, grid_pos, cell_size, asset_manager, *groups)
