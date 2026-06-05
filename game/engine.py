"""GameEngine: owns the display, clock, event pump, and SceneManager."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from game.assets.manager import AssetManager
from game.scene_manager import SceneManager
from game.constants import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, COLOR_BG

if TYPE_CHECKING:
    from game.scenes.base import Scene


class GameEngine:
    """Top-level game runner.

    Usage::

        engine = GameEngine("My Game", 1280, 720)
        engine.run(MyInitialScene)
    """

    def __init__(
        self,
        title: str = "Maze Explorer",
        width: int = SCREEN_WIDTH,
        height: int = SCREEN_HEIGHT,
        fps: int = FPS,
    ) -> None:
        pygame.init()
        pygame.display.set_caption(title)
        self.screen = pygame.display.set_mode((width, height))
        self.clock = pygame.time.Clock()
        self.fps = fps
        self.running = False
        self.asset_manager = AssetManager()
        self.scene_manager = SceneManager(self)

    def run(self, initial_scene: type[Scene], **scene_kwargs) -> None:
        """Start the main loop. Pushes *initial_scene* and loops until quit."""
        self.running = True
        self.scene_manager.push(initial_scene(self.scene_manager, **scene_kwargs))

        while self.running:
            dt = self.clock.tick(self.fps) / 1000.0

            # Process events
            for event in pygame.event.get():
                self.scene_manager.handle_event(event)

            # Update
            self.scene_manager.update(dt)

            # Render
            self.screen.fill(COLOR_BG)
            self.scene_manager.render(self.screen)
            pygame.display.flip()

        pygame.quit()

    @property
    def width(self) -> int:
        return self.screen.get_width()

    @property
    def height(self) -> int:
        return self.screen.get_height()
