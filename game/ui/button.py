"""Button: clickable rectangle with text label."""

from __future__ import annotations

from typing import Callable

import pygame

from game.ui.label import Label

# Button state constants
STATE_NORMAL = 0
STATE_HOVER = 1
STATE_ACTIVE = 2


class Button:
    """A clickable button with hover and active states."""

    def __init__(
        self,
        rect: pygame.Rect,
        text: str,
        font: pygame.font.Font,
        callback: Callable[[], None] | None = None,
        color_normal: tuple[int, int, int] = (60, 60, 80),
        color_hover: tuple[int, int, int] = (80, 80, 110),
        color_active: tuple[int, int, int] = (100, 100, 140),
        text_color: tuple[int, int, int] = (220, 220, 230),
        border_radius: int = 6,
    ) -> None:
        self.rect = rect
        self.callback = callback
        self._color_normal = color_normal
        self._color_hover = color_hover
        self._color_active = color_active
        self._text_color = text_color
        self._border_radius = border_radius
        self._state = STATE_NORMAL
        self._pressed = False

        self.label = Label(text, font, text_color)

    # ---- State -------------------------------------------------------------

    @property
    def state(self) -> int:
        return self._state

    def _update_state(self, mouse_pos: tuple[int, int], mouse_pressed: bool) -> None:
        if not self.rect.collidepoint(mouse_pos):
            self._state = STATE_NORMAL
            self._pressed = False
            return

        if mouse_pressed:
            self._state = STATE_ACTIVE
            self._pressed = True
        elif self._pressed:
            # Released while hovering → click
            self._state = STATE_HOVER
            self._pressed = False
            if self.callback is not None:
                self.callback()
        else:
            self._state = STATE_HOVER

    @property
    def _current_color(self) -> tuple[int, int, int]:
        if self._state == STATE_ACTIVE:
            return self._color_active
        if self._state == STATE_HOVER:
            return self._color_hover
        return self._color_normal

    # ---- Event handling ----------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Return True if the event was consumed by this button."""
        if event.type == pygame.MOUSEMOTION:
            self._update_state(event.pos, bool(event.buttons[0]))
            return self._state != STATE_NORMAL
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._update_state(event.pos, True)
            return self._state == STATE_ACTIVE
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._update_state(event.pos, False)
            return True
        return False

    # ---- Render ------------------------------------------------------------

    def render(self, surface: pygame.Surface) -> None:
        color = self._current_color
        pygame.draw.rect(surface, color, self.rect, border_radius=self._border_radius)
        # Border
        pygame.draw.rect(surface, _lighten(color, 30), self.rect, width=1, border_radius=self._border_radius)
        # Text centered
        self.label.render_centered(surface, self.rect.centerx, self.rect.centery)


def _lighten(color: tuple[int, int, int], amount: int) -> tuple[int, int, int]:
    return tuple(min(255, c + amount) for c in color)  # type: ignore[return-value]
