"""TextInput: single-line text input widget."""

from __future__ import annotations

import pygame

from game.ui.label import Label

CURSOR_BLINK_INTERVAL = 0.5


class TextInput:
    """A single-line text input field."""

    def __init__(
        self,
        rect: pygame.Rect,
        font: pygame.font.Font,
        placeholder: str = "",
        default_text: str = "",
        max_chars: int = 32,
        color_bg: tuple[int, int, int] = (50, 50, 70),
        color_active_bg: tuple[int, int, int] = (60, 60, 85),
        color_text: tuple[int, int, int] = (220, 220, 230),
        color_cursor: tuple[int, int, int] = (180, 200, 255),
    ) -> None:
        self.rect = rect
        self.font = font
        self.placeholder = placeholder
        self._text = default_text
        self.max_chars = max_chars
        self._focused = False
        self._cursor_visible = True
        self._cursor_timer = 0.0

        self._color_bg = color_bg
        self._color_active_bg = color_active_bg
        self._color_text = color_text
        self._color_cursor = color_cursor

    # ---- Properties --------------------------------------------------------

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        self._text = value[:self.max_chars]

    @property
    def focused(self) -> bool:
        return self._focused

    # ---- Event handling ----------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Return True if event consumed."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self._focused = True
                self._cursor_visible = True
                self._cursor_timer = 0.0
                return True
            else:
                self._focused = False
                return False

        if not self._focused:
            return False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self._text = self._text[:-1]
                return True
            if event.key == pygame.K_RETURN or event.key == pygame.K_TAB:
                self._focused = False
                return True
            if event.unicode and event.unicode.isprintable() and len(self._text) < self.max_chars:
                self._text += event.unicode
                return True
            return True  # consume all keys when focused

        return False

    # ---- Update & Render ---------------------------------------------------

    def update(self, dt: float) -> None:
        if self._focused:
            self._cursor_timer += dt
            if self._cursor_timer >= CURSOR_BLINK_INTERVAL:
                self._cursor_timer -= CURSOR_BLINK_INTERVAL
                self._cursor_visible = not self._cursor_visible

    def render(self, surface: pygame.Surface) -> None:
        bg = self._color_active_bg if self._focused else self._color_bg
        pygame.draw.rect(surface, bg, self.rect, border_radius=4)
        pygame.draw.rect(surface, _lighten(bg, 30), self.rect, width=1, border_radius=4)

        # Text or placeholder
        display_text = self._text if self._text else self.placeholder
        text_color = self._color_text if self._text else _dim(self._color_text)
        lbl = Label(display_text, self.font, text_color)
        lbl.render(surface, self.rect.x + 8, self.rect.y + (self.rect.height - lbl.rect.height) // 2)

        # Cursor
        if self._focused and self._cursor_visible:
            text_w = lbl.rect.width if self._text else 0
            cx = self.rect.x + 8 + text_w + 2
            cy1 = self.rect.y + 6
            cy2 = self.rect.bottom - 6
            pygame.draw.line(surface, self._color_cursor, (cx, cy1), (cx, cy2), width=2)


def _lighten(color: tuple[int, int, int], amount: int) -> tuple[int, int, int]:
    return tuple(min(255, c + amount) for c in color)  # type: ignore[return-value]


def _dim(color: tuple[int, int, int]) -> tuple[int, int, int]:
    return tuple(c // 2 for c in color)  # type: ignore[return-value]
