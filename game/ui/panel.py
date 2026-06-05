"""Panel: a bordered background container widget."""

from __future__ import annotations

import pygame


class Panel:
    """A rectangular panel with background and optional border."""

    def __init__(
        self,
        rect: pygame.Rect,
        color: tuple[int, int, int] = (35, 35, 50),
        border_color: tuple[int, int, int] | None = (60, 60, 80),
        border_width: int = 1,
        border_radius: int = 8,
    ) -> None:
        self.rect = rect
        self.color = color
        self.border_color = border_color
        self.border_width = border_width
        self.border_radius = border_radius

    def render(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, self.color, self.rect, border_radius=self.border_radius)
        if self.border_color is not None and self.border_width > 0:
            pygame.draw.rect(
                surface,
                self.border_color,
                self.rect,
                width=self.border_width,
                border_radius=self.border_radius,
            )
