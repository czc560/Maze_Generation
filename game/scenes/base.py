"""Abstract Scene base class for the scene stack."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from game.scene_manager import SceneManager


class Scene(ABC):
    """A single screen / overlay in the game.

    Lifecycle (called by SceneManager):
        push:    __init__() -> enter()
        overlay: pause() on the scene below, then __init__() -> enter()
        pop:     exit() on this scene, resume() on the scene below
        replace: exit() on this scene, enter() on the replacement
    """

    def __init__(self, manager: SceneManager) -> None:
        self.manager = manager
        self.engine = manager.engine

    # ---- Lifecycle hooks (override as needed) ------------------------------

    def enter(self) -> None:
        """Called when this scene becomes the active (top) scene."""

    def exit(self) -> None:
        """Called when this scene is popped from the stack."""

    def pause(self) -> None:
        """Called when another scene is pushed on top of this one."""

    def resume(self) -> None:
        """Called when the scene above this one is popped."""

    # ---- Per-frame hooks ---------------------------------------------------

    @abstractmethod
    def handle_event(self, event: pygame.event.Event) -> None:
        """Process a single pygame event."""

    @abstractmethod
    def update(self, dt: float) -> None:
        """Update game logic. *dt* is seconds since last frame."""

    @abstractmethod
    def render(self, surface: pygame.Surface) -> None:
        """Draw the scene to *surface*."""
