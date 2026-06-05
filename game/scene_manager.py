"""SceneManager: stack-based scene container.

Only the top scene receives events, updates, and renders.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from game.engine import GameEngine
    from game.scenes.base import Scene


class SceneManager:
    """Manages a stack of Scene objects."""

    def __init__(self, engine: GameEngine) -> None:
        self.engine = engine
        self._stack: list[Scene] = []

    @property
    def current(self) -> Scene | None:
        return self._stack[-1] if self._stack else None

    @property
    def depth(self) -> int:
        return len(self._stack)

    # ---- Stack operations --------------------------------------------------

    def push(self, scene: Scene) -> None:
        """Pause the current top scene (if any), push *scene*, and call enter()."""
        if self._stack:
            self._stack[-1].pause()
        self._stack.append(scene)
        scene.enter()

    def pop(self) -> Scene | None:
        """Pop the top scene, call exit() on it, and resume the new top."""
        if not self._stack:
            return None
        popped = self._stack.pop()
        popped.exit()
        if self._stack:
            self._stack[-1].resume()
        return popped

    def replace(self, scene: Scene) -> None:
        """Pop the current scene and push *scene* (no resume on the old one)."""
        if self._stack:
            self._stack.pop().exit()
        self._stack.append(scene)
        scene.enter()

    def pop_to(self, scene_class: type[Scene]) -> None:
        """Pop scenes until one of type *scene_class* is on top."""
        while self._stack and not isinstance(self._stack[-1], scene_class):
            self._stack.pop().exit()
        if self._stack:
            self._stack[-1].resume()

    # ---- Per-frame ---------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        """Forward event to top scene. Handle global quit here."""
        if event.type == pygame.QUIT:
            self.engine.running = False
            return
        if self._stack:
            self._stack[-1].handle_event(event)

    def update(self, dt: float) -> None:
        if self._stack:
            self._stack[-1].update(dt)

    def render(self, surface: pygame.Surface) -> None:
        if self._stack:
            self._stack[-1].render(surface)
