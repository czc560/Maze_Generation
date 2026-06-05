"""Dropdown: expandable option selector."""

from __future__ import annotations

from typing import Callable

import pygame

from game.ui.button import Button
from game.ui.label import Label

OPTION_HEIGHT = 32


class Dropdown:
    """A dropdown selector that expands/collapses a list of options."""

    def __init__(
        self,
        rect: pygame.Rect,
        options: list[str],
        font: pygame.font.Font,
        default_index: int = 0,
        on_change: Callable[[int, str], None] | None = None,
        color_bg: tuple[int, int, int] = (50, 50, 70),
        color_hover: tuple[int, int, int] = (70, 70, 100),
        color_selected: tuple[int, int, int] = (90, 90, 130),
        text_color: tuple[int, int, int] = (220, 220, 230),
    ) -> None:
        self.rect = rect
        self.options = options
        self.font = font
        self._selected_index = default_index
        self.on_change = on_change
        self._expanded = False
        self._hovered_index = -1

        self._color_bg = color_bg
        self._color_hover = color_hover
        self._color_selected = color_selected
        self._text_color = text_color

    # ---- Properties --------------------------------------------------------

    @property
    def selected_index(self) -> int:
        return self._selected_index

    @property
    def selected_value(self) -> str:
        if 0 <= self._selected_index < len(self.options):
            return self.options[self._selected_index]
        return ""

    def select(self, index: int) -> None:
        if 0 <= index < len(self.options) and index != self._selected_index:
            self._selected_index = index
            if self.on_change:
                self.on_change(index, self.options[index])

    # ---- Event handling ----------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Return True if event consumed."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos

            # Click on collapsed header → expand
            if not self._expanded and self.rect.collidepoint(mx, my):
                self._expanded = True
                return True

            # Click on expanded header → collapse
            if self._expanded and self.rect.collidepoint(mx, my):
                self._expanded = False
                return True

            # Click on an option in the expanded list
            if self._expanded:
                for i in range(len(self.options)):
                    opt_rect = self._option_rect(i)
                    if opt_rect.collidepoint(mx, my):
                        self.select(i)
                        self._expanded = False
                        return True

            # Click elsewhere → collapse
            if self._expanded:
                self._expanded = False
                return True

        if event.type == pygame.MOUSEMOTION and self._expanded:
            mx, my = event.pos
            self._hovered_index = -1
            for i in range(len(self.options)):
                if self._option_rect(i).collidepoint(mx, my):
                    self._hovered_index = i
                    break
            return True

        return False

    def _option_rect(self, index: int) -> pygame.Rect:
        return pygame.Rect(
            self.rect.x,
            self.rect.y + (index + 1) * OPTION_HEIGHT,
            self.rect.width,
            OPTION_HEIGHT,
        )

    # ---- Render ------------------------------------------------------------

    def render(self, surface: pygame.Surface) -> None:
        # Header
        header_color = self._color_hover if self._expanded else self._color_bg
        pygame.draw.rect(surface, header_color, self.rect, border_radius=4)
        pygame.draw.rect(surface, _lighten(header_color, 30), self.rect, width=1, border_radius=4)

        # Header text
        label = Label(self.selected_value, self.font, self._text_color)
        label.render_centered(surface, self.rect.centerx, self.rect.centery)

        # Arrow indicator
        arrow = "▲" if self._expanded else "▼"
        arrow_lbl = Label(arrow, self.font, self._text_color)
        arrow_lbl.render(surface, self.rect.right - 30, self.rect.y + 5)

        # Expanded options
        if self._expanded:
            for i, opt in enumerate(self.options):
                opt_rect = self._option_rect(i)
                if i == self._selected_index:
                    c = self._color_selected
                elif i == self._hovered_index:
                    c = self._color_hover
                else:
                    c = self._color_bg
                pygame.draw.rect(surface, c, opt_rect)
                pygame.draw.rect(surface, _lighten(c, 20), opt_rect, width=1)

                opt_label = Label(opt, self.font, self._text_color)
                opt_label.render_centered(surface, opt_rect.centerx, opt_rect.centery)


def _lighten(color: tuple[int, int, int], amount: int) -> tuple[int, int, int]:
    return tuple(min(255, c + amount) for c in color)  # type: ignore[return-value]
