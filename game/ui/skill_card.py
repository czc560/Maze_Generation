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

    CARD_WIDTH = 128
    CARD_HEIGHT = 92

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
        self._cooldown_remaining = self.cooldown_max + 1

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
        accent = _skill_accent(self.index)
        ready = self.is_ready

        shadow = self.rect.move(4, 6)
        pygame.draw.rect(surface, (0, 0, 0), shadow, border_radius=10)
        base = (246, 222, 158) if ready else (146, 117, 89)
        pygame.draw.rect(surface, base, self.rect, border_radius=10)
        pygame.draw.rect(surface, (117, 82, 48), self.rect, width=3, border_radius=10)
        pygame.draw.rect(surface, (255, 246, 203), self.rect.inflate(-10, -10), width=1, border_radius=7)

        top_band = pygame.Rect(self.rect.x + 6, self.rect.y + 6, self.rect.width - 12, 18)
        pygame.draw.rect(surface, accent, top_band, border_radius=6)
        pygame.draw.rect(surface, (255, 255, 255), (top_band.x + 6, top_band.y + 3, top_band.width - 12, 2), border_radius=1)

        badge = pygame.Rect(self.rect.x + 10, self.rect.y + 30, 34, 34)
        pygame.draw.ellipse(surface, (80, 59, 42), badge.inflate(4, 4))
        pygame.draw.ellipse(surface, accent, badge)
        pygame.draw.ellipse(surface, (255, 246, 214), badge.inflate(-10, -10))
        idx_surf = self.small_font.render(str(self.index + 1), True, (56, 48, 36))
        surface.blit(idx_surf, idx_surf.get_rect(center=badge.center))

        name_surf = self.small_font.render(f"技能 {self.index + 1}", True, (54, 49, 38))
        surface.blit(name_surf, (self.rect.x + 52, self.rect.y + 31))
        dmg_surf = self.font.render(str(self.damage), True, (132, 50, 42))
        surface.blit(dmg_surf, (self.rect.x + 52, self.rect.y + 49))
        dmg_label = self.small_font.render("伤害", True, (93, 78, 58))
        surface.blit(dmg_label, (self.rect.x + 84, self.rect.y + 53))

        if self._cooldown_remaining > 0:
            cd_text = f"冷却 {self._cooldown_remaining}"
            cd_color = (255, 245, 226)
            overlay = pygame.Surface(self.rect.size, pygame.SRCALPHA)
            overlay.fill((48, 37, 42, 118))
            surface.blit(overlay, self.rect.topleft)
        elif self.used_this_turn:
            cd_text = "已释放"
            cd_color = (255, 244, 186)
        else:
            cd_text = "可释放"
            cd_color = (38, 116, 63)

        status_rect = pygame.Rect(self.rect.x + 10, self.rect.bottom - 24, self.rect.width - 20, 18)
        pygame.draw.rect(surface, (255, 250, 221) if ready else (94, 72, 62), status_rect, border_radius=6)
        pygame.draw.rect(surface, accent if ready else (129, 95, 82), status_rect, width=1, border_radius=6)
        cd_surf = self.small_font.render(cd_text, True, cd_color)
        surface.blit(cd_surf, cd_surf.get_rect(center=status_rect.center))


def _skill_accent(index: int) -> tuple[int, int, int]:
    palette = [
        (87, 181, 238),
        (244, 184, 60),
        (224, 87, 102),
        (96, 184, 96),
        (166, 117, 226),
        (238, 133, 72),
        (72, 196, 178),
        (205, 205, 220),
    ]
    return palette[index % len(palette)]


def _lighten(color: tuple[int, int, int], amount: int) -> tuple[int, int, int]:
    return tuple(min(255, c + amount) for c in color)  # type: ignore[return-value]
