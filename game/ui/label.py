"""Label: simple text rendering widget."""

from __future__ import annotations

import pygame


class Label:
    """A non-interactive text label."""

    def __init__(
        self,
        text: str,
        font: pygame.font.Font,
        color: tuple[int, int, int] = (220, 220, 230),
        antialias: bool = True,
    ) -> None:
        self.text = text
        self.font = font
        self.color = color
        self.antialias = antialias
        self._surface: pygame.Surface | None = None
        self._dirty = True

    def set_text(self, text: str) -> None:
        if text != self.text:
            self.text = text
            self._dirty = True

    def set_color(self, color: tuple[int, int, int]) -> None:
        if color != self.color:
            self.color = color
            self._dirty = True

    def _rebuild(self) -> None:
        self._surface = self.font.render(self.text, self.antialias, self.color)
        self._dirty = False

    @property
    def surface(self) -> pygame.Surface:
        if self._dirty or self._surface is None:
            self._rebuild()
        return self._surface  # type: ignore[return-value]

    @property
    def rect(self) -> pygame.Rect:
        return self.surface.get_rect()

    def render(self, surface: pygame.Surface, x: int, y: int) -> None:
        surface.blit(self.surface, (x, y))

    def render_centered(self, surface: pygame.Surface, center_x: int, center_y: int) -> None:
        r = self.surface.get_rect(center=(center_x, center_y))
        surface.blit(self.surface, r)
