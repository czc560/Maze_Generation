"""Slider: draggable numeric range selector."""

from __future__ import annotations

from typing import Callable

import pygame

from game.ui.label import Label


class Slider:
    """A horizontal slider for selecting a numeric value within a range."""

    def __init__(
        self,
        rect: pygame.Rect,
        label_text: str,
        font: pygame.font.Font,
        min_value: float = 0.0,
        max_value: float = 1.0,
        step: float = 0.1,
        default_value: float | None = None,
        on_change: Callable[[float], None] | None = None,
        track_color: tuple[int, int, int] = (50, 50, 70),
        fill_color: tuple[int, int, int] = (100, 140, 255),
        handle_color: tuple[int, int, int] = (180, 200, 255),
        text_color: tuple[int, int, int] = (220, 220, 230),
    ) -> None:
        self.track_rect = rect
        self.label_text = label_text
        self.font = font
        self.min = min_value
        self.max = max_value
        self.step = step
        self._value = default_value if default_value is not None else min_value
        self.on_change = on_change

        self._track_color = track_color
        self._fill_color = fill_color
        self._handle_color = handle_color
        self._text_color = text_color

        self._dragging = False
        self._handle_radius = rect.height // 2 + 2
        self._label = Label(f"{label_text}: {self._value:.1f}", font, text_color)

    # ---- Properties --------------------------------------------------------

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, v: float) -> None:
        v = self._clamp(v)
        if v != self._value:
            self._value = v
            self._update_label()
            if self.on_change:
                self.on_change(self._value)

    def _clamp(self, v: float) -> float:
        v = max(self.min, min(self.max, v))
        if self.step > 0:
            v = round(v / self.step) * self.step
            v = round(v, 6)  # kill floating noise
        return v

    def _update_label(self) -> None:
        # Format: show int when step >= 1, else 1 decimal
        if self.step >= 1:
            self._label.set_text(f"{self.label_text}: {int(self._value)}")
        elif self.step >= 0.1:
            self._label.set_text(f"{self.label_text}: {self._value:.1f}")
        else:
            self._label.set_text(f"{self.label_text}: {self._value:.2f}")

    @property
    def handle_x(self) -> int:
        frac = (self._value - self.min) / (self.max - self.min) if self.max > self.min else 0
        return self.track_rect.left + int(frac * self.track_rect.width)

    # ---- Event handling ----------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Return True if event consumed."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            hx = self.handle_x
            hy = self.track_rect.centery
            # Check if click is near the handle
            dx = event.pos[0] - hx
            dy = event.pos[1] - hy
            if dx * dx + dy * dy <= (self._handle_radius + 5) ** 2:
                self._dragging = True
                return True
            # Check if click is on the track
            if self.track_rect.collidepoint(event.pos):
                self._dragging = True
                self._update_from_mouse(event.pos[0])
                return True

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._dragging = False
            return True

        if event.type == pygame.MOUSEMOTION and self._dragging:
            self._update_from_mouse(event.pos[0])
            return True

        return False

    def _update_from_mouse(self, mx: int) -> None:
        frac = (mx - self.track_rect.left) / self.track_rect.width
        frac = max(0.0, min(1.0, frac))
        self.value = self.min + frac * (self.max - self.min)

    # ---- Render ------------------------------------------------------------

    def render(self, surface: pygame.Surface) -> None:
        # Label above the track
        self._label.render(surface, self.track_rect.left, self.track_rect.top - 22)

        # Track background
        pygame.draw.rect(surface, self._track_color, self.track_rect, border_radius=4)

        # Filled portion
        fill_rect = pygame.Rect(
            self.track_rect.left,
            self.track_rect.top,
            self.handle_x - self.track_rect.left,
            self.track_rect.height,
        )
        if fill_rect.width > 0:
            pygame.draw.rect(surface, self._fill_color, fill_rect, border_radius=4)

        # Track border
        pygame.draw.rect(surface, _lighten(self._track_color, 30), self.track_rect, width=1, border_radius=4)

        # Handle
        hx = self.handle_x
        hy = self.track_rect.centery
        pygame.draw.circle(surface, self._handle_color, (hx, hy), self._handle_radius)
        pygame.draw.circle(surface, (255, 255, 255), (hx, hy), self._handle_radius, width=1)


def _lighten(color: tuple[int, int, int], amount: int) -> tuple[int, int, int]:
    return tuple(min(255, c + amount) for c in color)  # type: ignore[return-value]
