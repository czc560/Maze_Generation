"""SkillCard: displays a skill's damage, cooldown, and readiness state."""

from __future__ import annotations

import pygame


class SkillCard:
    """Visual representation of a single boss-battle skill.

    Shows:
    - Skill name / index
    - Damage value
    - Cooldown status (ready / turns remaining)
    """

    CARD_WIDTH = 120
    CARD_HEIGHT = 80

    def __init__(
        self,
        index: int,
        damage: int,
        cooldown_max: int,
        font: pygame.font.Font,
        small_font: pygame.font.Font,
        color_bg: tuple[int, int, int] = (50, 50, 75),
        color_ready: tuple[int, int, int] = (80, 200, 80),
        color_cooldown: tuple[int, int, int] = (200, 80, 80),
        color_text: tuple[int, int, int] = (220, 220, 230),
        color_highlight: tuple[int, int, int] = (255, 220, 60),
    ) -> None:
        self.index = index
        self.damage = damage
        self.cooldown_max = cooldown_max
        self._cooldown_remaining = 0  # 0 = ready to use
        self.used_this_turn = False

        self.font = font
        self.small_font = small_font
        self._color_bg = color_bg
        self._color_ready = color_ready
        self._color_cooldown = color_cooldown
        self._color_text = color_text
        self._color_highlight = color_highlight

        self.rect = pygame.Rect(0, 0, self.CARD_WIDTH, self.CARD_HEIGHT)

    # ---- State -------------------------------------------------------------

    @property
    def is_ready(self) -> bool:
        return self._cooldown_remaining <= 0 and not self.used_this_turn

    @property
    def cooldown_remaining(self) -> int:
        return self._cooldown_remaining

    def use(self) -> None:
        """Mark this skill as used; it goes on cooldown."""
        self.used_this_turn = True
        self._cooldown_remaining = self.cooldown_max

    def tick_cooldown(self) -> None:
        """Advance one turn: reduce cooldown by 1."""
        self.used_this_turn = False
        if self._cooldown_remaining > 0:
            self._cooldown_remaining -= 1

    def reset(self) -> None:
        self._cooldown_remaining = 0
        self.used_this_turn = False

    # ---- Render ------------------------------------------------------------

    def render(self, surface: pygame.Surface, x: int, y: int) -> None:
        self.rect.topleft = (x, y)

        # Background
        if self.is_ready:
            bg = self._color_ready
        elif self._cooldown_remaining > 0:
            bg = self._color_cooldown
        else:
            bg = self._color_bg

        pygame.draw.rect(surface, bg, self.rect, border_radius=6)
        pygame.draw.rect(surface, _lighten(bg, 30), self.rect, width=1, border_radius=6)

        # Skill label
        name_surf = self.font.render(f"Skill {self.index + 1}", True, self._color_text)
        name_rect = name_surf.get_rect(midtop=(self.rect.centerx, self.rect.top + 6))
        surface.blit(name_surf, name_rect)

        # Damage
        dmg_surf = self.small_font.render(f"DMG: {self.damage}", True, self._color_text)
        dmg_rect = dmg_surf.get_rect(midtop=(self.rect.centerx, name_rect.bottom + 4))
        surface.blit(dmg_surf, dmg_rect)

        # Cooldown / Ready
        if self._cooldown_remaining > 0:
            cd_text = f"CD: {self._cooldown_remaining}"
            cd_color = self._color_cooldown
        elif self.used_this_turn:
            cd_text = "Used"
            cd_color = (180, 180, 100)
        else:
            cd_text = "READY"
            cd_color = self._color_highlight

        cd_surf = self.small_font.render(cd_text, True, cd_color)
        cd_rect = cd_surf.get_rect(midbottom=(self.rect.centerx, self.rect.bottom - 6))
        surface.blit(cd_surf, cd_rect)


def _lighten(color: tuple[int, int, int], amount: int) -> tuple[int, int, int]:
    return tuple(min(255, c + amount) for c in color)  # type: ignore[return-value]
