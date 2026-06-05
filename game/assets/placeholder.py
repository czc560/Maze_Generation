"""PlaceholderGenerator: generates colored rectangles with text labels
as fallback sprites when real PNG assets are missing."""

from __future__ import annotations

import pygame

from game.constants import (
    ASSET_WALL, ASSET_FLOOR, ASSET_PLAYER, ASSET_COIN, ASSET_TRAP,
    ASSET_BOSS, ASSET_START, ASSET_END, ASSET_AI_MARKER,
    ASSET_FOG, ASSET_FOG_DIM,
)


# (fill_color_hex, border_color_hex, label_text)
PLACEHOLDER_DEFS: dict[str, tuple[str, str, str]] = {
    ASSET_WALL:      ("#2b2b2b", "#1a1a1a", "##"),
    ASSET_FLOOR:     ("#e3e3e3", "#c8c8c8", ""),
    ASSET_PLAYER:    ("#009dff", "#0070c0", "P"),
    ASSET_COIN:      ("#fdae6b", "#e08a30", "C"),
    ASSET_TRAP:      ("#920000", "#600000", "T"),
    ASSET_BOSS:      ("#756bb1", "#504090", "B"),
    ASSET_START:     ("#009dff", "#0070c0", "S"),
    ASSET_END:       ("#2fff00", "#20b000", "E"),
    ASSET_AI_MARKER: ("#ffd43b", "#c0a020", "AI"),
    ASSET_FOG:       ("#0a0a14a0", "#00000000", ""),   # translucent dark
    ASSET_FOG_DIM:   ("#0a0a1446", "#00000000", ""),   # very translucent dim
}

# Below this cell size, skip text labels (they won't fit)
MIN_CELL_SIZE_FOR_LABEL = 16


class PlaceholderGenerator:
    """Generates placeholder sprite surfaces on demand."""

    @staticmethod
    def generate(key: str, width: int, height: int) -> pygame.Surface:
        """Create a placeholder Surface for *key* at the given size.

        Returns a new Surface every call (no caching here — AssetManager handles that).
        """
        surface = pygame.Surface((width, height), pygame.SRCALPHA)

        fill_hex, border_hex, label = PLACEHOLDER_DEFS.get(
            key, ("#ff00ff", "#cc00cc", "?")
        )

        fill_color = _hex_to_rgba(fill_hex)
        border_color = _hex_to_rgba(border_hex)

        # Fill background
        surface.fill(fill_color)

        # 1px border
        pygame.draw.rect(surface, border_color, (0, 0, width, height), 1)

        # Text label (skip if too small)
        if label and width >= MIN_CELL_SIZE_FOR_LABEL and height >= MIN_CELL_SIZE_FOR_LABEL:
            font_size = max(10, min(width, height) // 2)
            try:
                font = pygame.font.SysFont("simhei, arial", font_size, bold=True)
            except Exception:
                font = pygame.font.Font(None, font_size)

            text_surf = font.render(label, True, (255, 255, 255))
            text_rect = text_surf.get_rect(center=(width // 2, height // 2))
            surface.blit(text_surf, text_rect)

        return surface

    @staticmethod
    def generate_all(cell_size: int) -> dict[str, pygame.Surface]:
        """Pre-generate all known sprites at the given cell size."""
        result: dict[str, pygame.Surface] = {}
        for key in PLACEHOLDER_DEFS:
            result[key] = PlaceholderGenerator.generate(key, cell_size, cell_size)
        return result


def _hex_to_rgba(hex_str: str) -> tuple[int, int, int, int]:
    """Convert '#rrggbb' or '#rrggbbaa' to (r, g, b, a)."""
    h = hex_str.lstrip("#")
    if len(h) == 6:
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)
    elif len(h) == 8:
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), int(h[6:8], 16))
    return (255, 0, 255, 255)
