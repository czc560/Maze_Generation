"""BossBattleScene — animated boss gauntlet with optional auto-battle.

- Before battle: player chooses manual or auto-battle (cannot switch during).
- Unknown HP → always max-damage skill.
- Known HP   → DP-optimal skill sequence.
- Fail → spend coins to revive; coins exhausted = game over.
"""

from __future__ import annotations

import random
import pygame

from game.scenes.base import Scene
from game.constants import (COLOR_BG, COLOR_TEXT, COLOR_TEXT_DIM, COLOR_ACCENT,
                             COLOR_GOLD, COLOR_RED, COLOR_GREEN, SCREEN_WIDTH, SCREEN_HEIGHT, GameEvent)
from game.ui.label import Label
from game.ui.button import Button
from game.ui.skill_card import SkillCard


class BossBattleScene(Scene):
    """Animated boss gauntlet overlay."""

    def __init__(self, manager, game_rules=None, player_skills=None, coin_total=0,
                 battle_mode=False, auto_speed=0.6):
        super().__init__(manager)
        self._game_rules = game_rules or {}
        self._skills_data = player_skills or [[8, 4], [2, 0], [4, 2], [6, 3]]
        self._coin_total = coin_total
        self._auto_battle = battle_mode  # pre-chosen, immutable during battle
        self._auto_speed = auto_speed
        self._auto_timer = 0.0

        self._boss_hp_list = list(self._game_rules.get("boss_hp", [11, 13, 9, 15]))
        self._round_limit = self._game_rules.get("min_rounds", 20)
        self._coin_consumption = self._game_rules.get("coin_consumption", 5)

        self._phase = "choose" if not self._auto_battle else "battle"  # choose | battle
        self._current_boss_idx = 0
        self._current_round = 0
        self._bosses_killed = [False] * len(self._boss_hp_list)
        self._bosses_revealed = [False] * len(self._boss_hp_list)
        self._coins_spent = 0
        self._current_boss_hp_left = self._boss_hp_list[0] if self._boss_hp_list else 0
        self._boss_start_hp = self._current_boss_hp_left

        self._skill_cards: list[SkillCard] = []
        self._am = self.engine.asset_manager
        self._font = self._am.get_font(None, 24)
        self._font_small = self._am.get_font(None, 18)
        self._font_large = self._am.get_font(None, 36)

        self._anim_state = "intro"
        self._anim_timer = 1.5
        self._anim_particles: list[dict] = []
        self._battle_log: list[str] = ["Boss战开始！"]
        self._result: dict | None = None
        self._needs_layout = True
        self._buttons: list[Button] = []

        self._spawn_particles(40)

    # ========================================================================
    #  Lifecycle
    # ========================================================================

    def enter(self) -> None:
        self._init_battle()
        self._anim_timer = 1.5

    def _init_battle(self) -> None:
        self._current_boss_idx = 0
        self._current_round = 0
        self._battle_log = ["Boss战开始！"]
        self._skill_cards = [
            SkillCard(i, dmg, cd, self._font, self._font_small)
            for i, (dmg, cd) in enumerate(self._skills_data)
        ]
        for c in self._skill_cards:
            c.reset()
        if self._boss_hp_list:
            self._start_boss(0)
        self._phase = "battle"

    def _start_boss(self, idx: int) -> None:
        self._current_boss_idx = idx
        self._current_round = 0
        self._boss_start_hp = self._boss_hp_list[idx]
        self._current_boss_hp_left = self._boss_start_hp
        for c in self._skill_cards:
            c.reset()
        hp_text = "???" if not self._bosses_revealed[idx] else str(self._boss_start_hp)
        self._battle_log.append(f"--- Boss #{idx + 1}  HP: {hp_text} ---")
        self._anim_state = "player_turn"

    # ========================================================================
    #  Events
    # ========================================================================

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            self._handle_key(event.key)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self._handle_click(event.pos)

    def _handle_key(self, key: int) -> None:
        # In "choose" phase: space=auto, enter=manual
        if self._phase == "choose":
            if key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_a):
                self._auto_battle = True
                self._init_battle()
            elif key == pygame.K_m:
                self._auto_battle = False
                self._phase = "battle"
            return

        if self._anim_state != "player_turn":
            return

        if key == pygame.K_ESCAPE:
            self._forfeit_current(); return

        if self._auto_battle:
            return

        if pygame.K_1 <= key <= pygame.K_8:
            idx = key - pygame.K_1
            if 0 <= idx < len(self._skill_cards):
                self._use_skill(idx)

    def _handle_click(self, pos: tuple[int, int]) -> None:
        if self._phase == "choose":
            for btn in self._buttons:
                btn.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": pos, "button": 1}))
            return
        for card in self._skill_cards:
            if card.rect.collidepoint(pos) and card.is_ready and not self._auto_battle:
                self._use_skill(card.index); return

    # ========================================================================
    #  Skill use
    # ========================================================================

    def _use_skill(self, idx: int) -> None:
        if idx < 0 or idx >= len(self._skill_cards):
            return
        card = self._skill_cards[idx]
        if not card.is_ready:
            return
        dmg = card.damage
        card.use()
        self._current_boss_hp_left = max(0, self._current_boss_hp_left - dmg)
        self._current_round += 1
        hp_show = "???" if not self._bosses_revealed[self._current_boss_idx] else str(self._current_boss_hp_left)
        self._battle_log.append(f"回合{self._current_round}: 技能#{idx+1}(-{dmg}) → Boss HP:{hp_show}")
        for c in self._skill_cards:
            c.tick_cooldown()

        if self._current_boss_hp_left <= 0:
            self._on_boss_killed()
        elif self._current_round >= self._round_limit:
            self._on_round_limit()

    def _auto_use_skill(self) -> None:
        """AI picks skill: unknown HP → max dmg; known HP → DP optimal."""
        from game.battle.rules import optimal_skill_index_for

        available = [i for i, card in enumerate(self._skill_cards) if card.is_ready]
        if not available:
            self._current_round += 1
            for c in self._skill_cards:
                c.tick_cooldown()
            if self._current_round >= self._round_limit:
                self._on_round_limit()
            return

        if not self._bosses_revealed[self._current_boss_idx]:
            # Unknown HP → max damage
            idx = max(available, key=lambda i: self._skills_data[i][0])
        else:
            # Known HP → DP optimal
            idx = optimal_skill_index_for(available, self._skills_data, self._current_boss_hp_left)
            if idx is None:
                idx = max(available, key=lambda i: self._skills_data[i][0])

        self._use_skill(idx)

    # ========================================================================
    #  Boss lifecycle
    # ========================================================================

    def _on_boss_killed(self) -> None:
        idx = self._current_boss_idx
        self._bosses_revealed[idx] = True
        self._bosses_killed[idx] = True
        self._battle_log.append(f">>> Boss #{idx+1} 击杀! HP={self._boss_start_hp}")
        if idx + 1 < len(self._boss_hp_list):
            self._anim_state = "intro"
            self._anim_timer = 1.5
            self._start_boss(idx + 1)
        else:
            self._on_victory()

    def _on_round_limit(self) -> None:
        if self._coin_total >= self._coin_consumption:
            self._coin_total -= self._coin_consumption
            self._coins_spent += self._coin_consumption
            self._battle_log.append(f"!!! 回合超限！花费{self._coin_consumption}金币重试(剩余:{self._coin_total})")
            self._start_boss(self._current_boss_idx)
        else:
            self._on_defeat("金币不足!")

    def _forfeit_current(self) -> None:
        self._on_round_limit()

    def _on_victory(self) -> None:
        self._anim_state = "victory"
        self._battle_log.append("★★★ 全部击杀! ★★★")
        self._result = {"victory": True, "coins_spent": self._coins_spent,
                         "coins_remaining": self._coin_total,
                         "bosses_killed": sum(self._bosses_killed),
                         "total_bosses": len(self._boss_hp_list)}
        self._spawn_particles(60)

    def _on_defeat(self, reason=""):
        self._anim_state = "defeat"
        self._battle_log.append(f"失败: {reason}")
        self._result = {"victory": False, "coins_spent": self._coins_spent,
                         "coins_remaining": 0,
                         "bosses_killed": sum(self._bosses_killed),
                         "total_bosses": len(self._boss_hp_list)}
        self._spawn_particles(30)

    def _done(self):
        evt = pygame.event.Event(GameEvent.BOSS_BATTLE_OVER, result=self._result)
        pygame.event.post(evt)
        self.manager.pop()

    # ========================================================================
    #  Update
    # ========================================================================

    def update(self, dt: float) -> None:
        if self._phase == "choose":
            return  # wait for user choice

        if self._auto_battle and self._anim_state == "player_turn":
            self._auto_timer += dt
            if self._auto_timer >= self._auto_speed:
                self._auto_timer = 0.0
                self._auto_use_skill()

        if self._anim_state in ("intro", "victory", "defeat"):
            self._anim_timer -= dt
            if self._anim_timer <= 0:
                if self._anim_state == "intro":
                    self._anim_state = "player_turn"
                elif self._anim_state in ("victory", "defeat"):
                    self._done(); return

        for p in self._anim_particles:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["life"] -= dt
            p["vy"] += 20 * dt
        self._anim_particles = [p for p in self._anim_particles if p["life"] > 0]

    def _spawn_particles(self, count):
        for _ in range(count):
            self._anim_particles.append({
                "x": random.randint(100, SCREEN_WIDTH - 100),
                "y": random.randint(100, SCREEN_HEIGHT - 100),
                "vx": random.uniform(-80, 80), "vy": random.uniform(-80, 40),
                "life": random.uniform(1.5, 4.0),
                "color": random.choice(
                    [(100, 140, 255), (255, 200, 60), (200, 80, 80), (80, 220, 80)]),
                "size": random.randint(2, 5),
            })

    # ========================================================================
    #  Render
    # ========================================================================

    def render(self, surface: pygame.Surface) -> None:
        sw, sh = surface.get_size()
        bg = pygame.Surface((sw, sh)); bg.fill((18, 18, 28)); surface.blit(bg, (0, 0))

        for p in self._anim_particles:
            alpha = int(255 * min(1.0, p["life"] / 2.0))
            color = (*p["color"][:3], alpha)
            ps = pygame.Surface((p["size"] * 2, p["size"] * 2), pygame.SRCALPHA)
            pygame.draw.circle(ps, color, (p["size"], p["size"]), p["size"])
            surface.blit(ps, (int(p["x"]), int(p["y"])))

        # ---- Choose phase ----
        if self._phase == "choose":
            Label("Boss 战即将开始", self._font_large, COLOR_ACCENT).render_centered(surface, sw // 2, sh // 2 - 80)
            Label("请选择战斗模式:", self._font, COLOR_TEXT).render_centered(surface, sw // 2, sh // 2 - 20)

            if self._needs_layout:
                self._buttons.clear()
                self._buttons.append(Button(pygame.Rect(sw // 2 - 180, sh // 2 + 30, 170, 50),
                                            "自动战斗 (A)", self._font, color_normal=(40, 120, 60),
                                            callback=lambda: (setattr(self, '_auto_battle', True),
                                                              self._init_battle())))
                self._buttons.append(Button(pygame.Rect(sw // 2 + 10, sh // 2 + 30, 170, 50),
                                            "手动战斗 (M)", self._font, color_normal=(120, 100, 40),
                                            callback=lambda: (setattr(self, '_phase', 'battle'),
                                                              setattr(self, '_auto_battle', False))))
                self._needs_layout = False
            for btn in self._buttons:
                btn.render(surface)
            return

        # ---- Battle phase ----
        boss_area = pygame.Rect(80, 60, sw - 160, sh // 3)
        pygame.draw.rect(surface, (35, 35, 50), boss_area, border_radius=12)
        pygame.draw.rect(surface, (70, 70, 100), boss_area, width=1, border_radius=12)
        boss_img = self._am.get_image("boss", (64, 64))
        surface.blit(boss_img, boss_img.get_rect(center=(boss_area.centerx, boss_area.centery)))
        Label(f"Boss #{self._current_boss_idx + 1}/{len(self._boss_hp_list)}", self._font_large,
              COLOR_RED).render_centered(surface, boss_area.centerx, boss_area.top + 25)
        hp_text = (f"HP: {self._current_boss_hp_left}/{self._boss_start_hp}"
                   if self._bosses_revealed[self._current_boss_idx] else "HP: ???")
        hp_color = COLOR_GREEN if self._bosses_revealed[self._current_boss_idx] else COLOR_GOLD
        Label(hp_text, self._font, hp_color).render_centered(surface, boss_area.centerx, boss_area.bottom - 25)

        # Round bar
        bar_rect = pygame.Rect(boss_area.left + 20, boss_area.bottom + 10, boss_area.width - 40, 12)
        pygame.draw.rect(surface, (60, 60, 80), bar_rect, border_radius=6)
        frac = min(1.0, self._current_round / self._round_limit) if self._round_limit else 0
        fill_c = COLOR_GREEN if frac < 0.7 else (COLOR_GOLD if frac < 0.9 else COLOR_RED)
        if frac > 0:
            pygame.draw.rect(surface, fill_c, pygame.Rect(bar_rect.left, bar_rect.top,
                                int(bar_rect.width * frac), bar_rect.height), border_radius=6)
        Label(f"回合: {self._current_round}/{self._round_limit}  |  "
              f"金币: {self._coin_total}  |  "
              f"{'自动' if self._auto_battle else '手动'}模式",
              self._font_small, COLOR_TEXT).render_centered(surface, bar_rect.centerx, bar_rect.bottom + 12)

        # Skills
        cards_y = bar_rect.bottom + 35
        total_cw = len(self._skill_cards) * SkillCard.CARD_WIDTH + (len(self._skill_cards) - 1) * 10
        cards_x = (sw - total_cw) // 2
        for i, card in enumerate(self._skill_cards):
            card.render(surface, cards_x + i * (SkillCard.CARD_WIDTH + 10), cards_y)

        # Log
        log_y = cards_y + SkillCard.CARD_HEIGHT + 20
        log_panel = pygame.Rect(80, log_y, sw - 160, sh - log_y - 30)
        pygame.draw.rect(surface, (30, 30, 45), log_panel, border_radius=8)
        pygame.draw.rect(surface, (55, 55, 75), log_panel, width=1, border_radius=8)
        for i, line in enumerate(self._battle_log[-10:]):
            Label(line, self._font_small, COLOR_TEXT_DIM).render(
                surface, log_panel.left + 10, log_panel.top + 8 + i * 20)

        # State overlays
        if self._anim_state == "intro":
            self._render_overlay(surface, f"准备挑战 Boss #{self._current_boss_idx + 1}", COLOR_ACCENT)
        elif self._anim_state == "victory":
            self._render_overlay(surface, "★★★ 胜利！★★★", COLOR_GREEN)
        elif self._anim_state == "defeat":
            self._render_overlay(surface, "失 败", COLOR_RED)

    def _render_overlay(self, surface, text, color):
        sw, sh = surface.get_size()
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))
        Label(text, self._font_large, color).render_centered(surface, sw // 2, sh // 2)
