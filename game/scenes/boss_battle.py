"""BossBattleScene - animated boss gauntlet with optional auto-battle."""

from __future__ import annotations

import math
import random
from functools import lru_cache

import pygame

from game.scenes.base import Scene
from game.constants import (COLOR_TEXT, COLOR_TEXT_DIM, COLOR_ACCENT, COLOR_GOLD,
                             COLOR_RED, COLOR_GREEN, SCREEN_WIDTH, SCREEN_HEIGHT, GameEvent)
from game.ui.label import Label
from game.ui.button import Button
from game.ui.skill_card import SkillCard
from game.ui.backgrounds import draw_background
from game.ui.theme import FONT_UI_BOLD, FONT_UI_LIGHT, FONT_UI_REGULAR


SKILL_COLORS = [
    (92, 204, 255),
    (255, 204, 78),
    (255, 94, 118),
    (126, 232, 142),
    (182, 132, 255),
    (255, 150, 82),
    (96, 236, 208),
    (235, 235, 245),
]


class BossBattleScene(Scene):
    """Animated boss gauntlet overlay."""

    def __init__(self, manager, game_rules=None, player_skills=None, coin_total=0,
                 battle_mode=False, auto_speed=0.6):
        super().__init__(manager)
        self._game_rules = game_rules or {}
        self._skills_data = player_skills or [[8, 4], [2, 0], [4, 2], [6, 3]]
        self._coin_total = coin_total
        self._auto_battle = battle_mode
        self._auto_speed = auto_speed
        self._auto_timer = 0.0

        self._boss_hp_list = list(self._game_rules.get("boss_hp", [11, 13, 9, 15]))
        self._round_limit = self._game_rules.get("min_rounds", 20)
        self._coin_consumption = self._game_rules.get("coin_consumption", 5)

        self._phase = "battle" if self._auto_battle else "choose"
        self._battle_started = False
        self._current_boss_idx = 0
        self._rounds_used = 0
        self._boss_round = 0
        self._bosses_killed = [False] * len(self._boss_hp_list)
        self._bosses_revealed = [True] * len(self._boss_hp_list)
        self._coins_spent = 0
        self._current_boss_hp_left = self._boss_hp_list[0] if self._boss_hp_list else 0
        self._boss_start_hp = self._current_boss_hp_left

        self._skill_cards: list[SkillCard] = []
        self._am = self.engine.asset_manager
        self._font = self._am.get_font(FONT_UI_REGULAR, 24)
        self._font_small = self._am.get_font(FONT_UI_LIGHT, 18)
        self._font_card = self._am.get_font(FONT_UI_LIGHT, 16)
        self._font_large = self._am.get_font(FONT_UI_BOLD, 36)

        self._anim_state = "intro"
        self._anim_timer = 1.5
        self._anim_particles: list[dict] = []
        self._skill_effects: list[dict] = []
        self._battle_log: list[str] = ["Boss战准备中"]
        self._result: dict | None = None
        self._needs_layout = True
        self._buttons: list[Button] = []
        self._time = 0.0
        self._player_lunge = 0.0
        self._boss_shake = 0.0
        self._impact_flash = 0.0
        self._last_skill_idx: int | None = None

        self._spawn_particles(40)

    # ======================================================================
    # Lifecycle
    # ======================================================================

    def enter(self) -> None:
        self._needs_layout = True
        if self._auto_battle:
            self._init_battle(reset_known=True)
        else:
            self._phase = "choose"
            self._battle_started = False
            self._battle_log = ["Boss战准备中"]

    def _init_battle(self, reset_known: bool = False) -> None:
        self._battle_started = True
        self._phase = "battle"
        self._rounds_used = 0
        self._boss_round = 0
        self._current_boss_idx = 0
        self._bosses_killed = [False] * len(self._boss_hp_list)
        if reset_known:
            self._bosses_revealed = [True] * len(self._boss_hp_list)
        self._battle_log = ["Boss战开始！"]
        self._skill_cards = [
            SkillCard(i, dmg, cd, self._font, self._font_card)
            for i, (dmg, cd) in enumerate(self._skills_data)
        ]
        for card in self._skill_cards:
            card.reset()
        if self._boss_hp_list:
            self._start_boss(0, reset_cooldowns=True, intro=True)
        else:
            self._on_victory()

    def _start_boss(self, idx: int, reset_cooldowns: bool = True, intro: bool = True) -> None:
        self._current_boss_idx = idx
        self._boss_round = 0
        self._boss_start_hp = self._boss_hp_list[idx]
        self._current_boss_hp_left = self._boss_start_hp
        if reset_cooldowns:
            for card in self._skill_cards:
                card.reset()
        hp_text = str(self._boss_start_hp)
        self._battle_log.append(f"--- Boss #{idx + 1}  HP: {hp_text} ---")
        self._anim_state = "intro" if intro else "player_turn"
        self._anim_timer = 0.9 if intro else 0.0
        self._last_skill_idx = None

    def _reset_gauntlet_for_retry(self) -> None:
        self._rounds_used = 0
        self._bosses_killed = [False] * len(self._boss_hp_list)
        self._skill_effects.clear()
        if self._boss_hp_list:
            self._start_boss(0, reset_cooldowns=True, intro=True)

    # ======================================================================
    # Events
    # ======================================================================

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            self._handle_key(event.key)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self._handle_click(event.pos)

    def _handle_key(self, key: int) -> None:
        if self._phase == "choose":
            if key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_a):
                self._auto_battle = True
                self._init_battle(reset_known=True)
            elif key == pygame.K_m:
                self._auto_battle = False
                self._init_battle(reset_known=True)
            return

        if self._anim_state == "retry":
            if key in (pygame.K_r, pygame.K_SPACE, pygame.K_RETURN):
                self._retry_with_coins()
            elif key == pygame.K_ESCAPE:
                self._on_defeat("放弃复活")
            return

        if self._anim_state != "player_turn":
            return

        if key == pygame.K_ESCAPE:
            self._forfeit_current()
            return
        if key == pygame.K_SPACE and not any(card.is_ready for card in self._skill_cards):
            self._advance_wait_turn()
            return
        if self._auto_battle:
            return
        if pygame.K_1 <= key <= pygame.K_8:
            idx = key - pygame.K_1
            if 0 <= idx < len(self._skill_cards):
                self._use_skill(idx)

    def _handle_click(self, pos: tuple[int, int]) -> None:
        if self._phase == "choose" or self._anim_state == "retry":
            for btn in self._buttons:
                if btn.rect.collidepoint(pos) and btn.callback is not None:
                    btn.callback()
                    return
        if self._anim_state != "player_turn" or self._auto_battle:
            return
        for card in self._skill_cards:
            if card.rect.collidepoint(pos) and card.is_ready:
                self._use_skill(card.index)
                return

    # ======================================================================
    # Skill use and cooldowns
    # ======================================================================

    def _use_skill(self, idx: int) -> None:
        if idx < 0 or idx >= len(self._skill_cards):
            return
        card = self._skill_cards[idx]
        if not card.is_ready:
            return
        if self._rounds_used >= self._round_limit:
            self._on_round_limit()
            return

        dmg = max(0, card.damage)
        self._last_skill_idx = idx
        card.use()
        self._current_boss_hp_left = max(0, self._current_boss_hp_left - dmg)
        self._rounds_used += 1
        self._boss_round += 1
        hp_show = str(self._current_boss_hp_left)
        self._battle_log.append(
            f"总回合{self._rounds_used}: 技能#{idx + 1}(-{dmg}) -> Boss HP:{hp_show}"
        )
        self._spawn_skill_effect(idx, dmg)
        self._tick_cooldowns()

        if self._current_boss_hp_left <= 0:
            self._on_boss_killed()
        elif self._rounds_used >= self._round_limit:
            self._on_round_limit()

    def _advance_wait_turn(self) -> None:
        if self._rounds_used >= self._round_limit:
            self._on_round_limit()
            return
        self._rounds_used += 1
        self._boss_round += 1
        self._battle_log.append(f"总回合{self._rounds_used}: 等待技能冷却")
        self._tick_cooldowns()
        if self._rounds_used >= self._round_limit:
            self._on_round_limit()

    def _tick_cooldowns(self) -> None:
        for card in self._skill_cards:
            card.tick_cooldown()

    def _auto_use_skill(self) -> None:
        available = [i for i, card in enumerate(self._skill_cards) if card.is_ready]
        if not available:
            self._advance_wait_turn()
            return

        idx = self._optimal_skill_index_for_current_state(available)
        if idx is None:
            idx = max(available, key=lambda i: (self._skills_data[i][0], -self._skills_data[i][1]))
        self._use_skill(idx)

    def _optimal_skill_index_for_current_state(self, available: list[int]) -> int | None:
        skills = tuple((int(d), int(cd)) for d, cd in self._skills_data)
        start_cds = tuple(card.cooldown_remaining for card in self._skill_cards)
        hp_left = self._current_boss_hp_left

        @lru_cache(maxsize=None)
        def solve(hp: int, cds: tuple[int, ...]) -> tuple[int, int | None]:
            if hp <= 0:
                return 0, None
            ready = [i for i, cd in enumerate(cds) if cd <= 0]
            if not ready:
                next_cds = tuple(max(0, cd - 1) for cd in cds)
                turns, _ = solve(hp, next_cds)
                return turns + 1, -1

            best = (10**9, None)
            for i in ready:
                next_cds = list(cds)
                next_cds[i] = skills[i][1] + 1
                next_cds = [max(0, cd - 1) for cd in next_cds]
                turns, _ = solve(hp - skills[i][0], tuple(next_cds))
                candidate = (turns + 1, i)
                if candidate[0] < best[0]:
                    best = candidate
            return best

        _, idx = solve(hp_left, start_cds)
        return idx if idx in available else None

    # ======================================================================
    # Boss lifecycle
    # ======================================================================

    def _on_boss_killed(self) -> None:
        idx = self._current_boss_idx
        self._bosses_revealed[idx] = True
        self._bosses_killed[idx] = True
        self._battle_log.append(f">>> Boss #{idx + 1} 击杀! HP={self._boss_start_hp}")
        self._spawn_particles(36, near_boss=True)
        if idx + 1 < len(self._boss_hp_list):
            if self._rounds_used >= self._round_limit:
                self._on_round_limit()
                return
            self._start_boss(idx + 1, reset_cooldowns=True, intro=True)
        else:
            self._on_victory()

    def _retry_cost(self) -> int:
        return min(max(1, self._coin_consumption), max(0, self._coin_total))

    def _can_retry(self) -> bool:
        return self._coin_total > 0

    def _on_round_limit(self) -> None:
        if self._can_retry():
            if self._auto_battle:
                self._retry_with_coins()
            else:
                self._anim_state = "retry"
                self._needs_layout = True
                cost = self._retry_cost()
                self._battle_log.append(
                    f"回合耗尽，可消耗{cost}资源复活重打"
                )
        else:
            self._anim_state = "retry"
            self._needs_layout = True
            self._battle_log.append("回合耗尽，金币不足，无法复活")

    def _retry_with_coins(self) -> None:
        if not self._can_retry():
            self._on_defeat("金币不足!")
            return
        cost = self._retry_cost()
        self._coin_total -= cost
        self._coins_spent += cost
        self._battle_log.append(
            f"消耗{cost}资源复活重打(剩余:{self._coin_total})"
        )
        self._reset_gauntlet_for_retry()

    def _forfeit_current(self) -> None:
        self._on_round_limit()

    def _on_victory(self) -> None:
        self._anim_state = "victory"
        self._anim_timer = 1.5
        self._battle_log.append("全部击杀!")
        self._result = {"victory": True, "coins_spent": self._coins_spent,
                         "coins_remaining": self._coin_total,
                         "bosses_killed": sum(self._bosses_killed),
                         "total_bosses": len(self._boss_hp_list),
                         "rounds_used": self._rounds_used}
        self._spawn_particles(70)

    def _on_defeat(self, reason=""):
        self._anim_state = "defeat"
        self._anim_timer = 3.0
        self._battle_log.append(f"失败: {reason}")
        self._result = {"victory": False, "coins_spent": self._coins_spent,
                         "coins_remaining": self._coin_total,
                         "bosses_killed": sum(self._bosses_killed),
                         "total_bosses": len(self._boss_hp_list),
                         "rounds_used": self._rounds_used}
        self._spawn_particles(32)

    def _done(self):
        evt = pygame.event.Event(GameEvent.BOSS_BATTLE_OVER, result=self._result)
        pygame.event.post(evt)
        self.manager.pop()

    # ======================================================================
    # Update and effects
    # ======================================================================

    def update(self, dt: float) -> None:
        self._time += dt
        self._player_lunge = max(0.0, self._player_lunge - dt)
        self._boss_shake = max(0.0, self._boss_shake - dt)
        self._impact_flash = max(0.0, self._impact_flash - dt)

        if self._phase == "choose" or self._anim_state == "retry":
            self._update_particles(dt)
            return

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
                    self._done()
                    return

        self._update_particles(dt)
        self._update_skill_effects(dt)

    def _update_particles(self, dt: float) -> None:
        for p in self._anim_particles:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["life"] -= dt
            p["vy"] += 20 * dt
        self._anim_particles = [p for p in self._anim_particles if p["life"] > 0]

    def _update_skill_effects(self, dt: float) -> None:
        for effect in self._skill_effects:
            effect["age"] += dt
            if effect["kind"] == "text":
                effect["y"] -= 34 * dt
        self._skill_effects = [e for e in self._skill_effects if e["age"] < e["duration"]]

    def _spawn_particles(self, count: int, near_boss: bool = False) -> None:
        for _ in range(count):
            if near_boss:
                x = random.randint(SCREEN_WIDTH // 2 + 210, SCREEN_WIDTH // 2 + 360)
                y = random.randint(130, 290)
            else:
                x = random.randint(100, SCREEN_WIDTH - 100)
                y = random.randint(100, SCREEN_HEIGHT - 100)
            self._anim_particles.append({
                "x": x,
                "y": y,
                "vx": random.uniform(-90, 90),
                "vy": random.uniform(-100, 35),
                "life": random.uniform(1.0, 3.0),
                "color": random.choice(SKILL_COLORS[:6]),
                "size": random.randint(2, 5),
            })

    def _spawn_skill_effect(self, idx: int, damage: int) -> None:
        color = SKILL_COLORS[idx % len(SKILL_COLORS)]
        self._player_lunge = 0.22
        self._boss_shake = 0.32
        self._impact_flash = 0.22
        start = (315, 215)
        end = (900, 185)
        kind = "slash" if idx % 3 == 1 else "projectile"
        self._skill_effects.append({
            "kind": kind,
            "age": 0.0,
            "duration": 0.34,
            "start": start,
            "end": end,
            "color": color,
            "idx": idx,
        })
        self._skill_effects.append({
            "kind": "text",
            "age": 0.0,
            "duration": 0.75,
            "x": end[0] + 24,
            "y": end[1] - 36,
            "text": f"-{damage}",
            "color": color,
        })
        for _ in range(16):
            self._anim_particles.append({
                "x": end[0] + random.uniform(-28, 28),
                "y": end[1] + random.uniform(-28, 28),
                "vx": random.uniform(-120, 140),
                "vy": random.uniform(-130, 80),
                "life": random.uniform(0.45, 1.0),
                "color": color,
                "size": random.randint(2, 5),
            })

    # ======================================================================
    # Render
    # ======================================================================

    def render(self, surface: pygame.Surface) -> None:
        sw, sh = surface.get_size()
        draw_background(surface, "boss")

        for p in self._anim_particles:
            alpha = int(255 * min(1.0, p["life"] / 1.2))
            ps = pygame.Surface((p["size"] * 2, p["size"] * 2), pygame.SRCALPHA)
            pygame.draw.circle(ps, (*p["color"][:3], alpha), (p["size"], p["size"]), p["size"])
            surface.blit(ps, (int(p["x"]), int(p["y"])))

        if self._phase == "choose":
            self._render_choose(surface, sw, sh)
            return

        boss_area = pygame.Rect(80, 52, sw - 160, sh // 3)
        pygame.draw.rect(surface, (255, 246, 220), boss_area, border_radius=12)
        pygame.draw.rect(surface, (113, 153, 76), boss_area, width=2, border_radius=12)
        self._render_combatants(surface, boss_area)
        self._render_boss_status(surface, boss_area)
        self._render_skill_effects(surface)

        round_panel = pygame.Rect(boss_area.left + 120, boss_area.bottom + 10,
                                  boss_area.width - 240, 54)
        pygame.draw.rect(surface, (45, 54, 43), round_panel, border_radius=10)
        pygame.draw.rect(surface, (126, 156, 91), round_panel, width=2, border_radius=10)
        bar_rect = pygame.Rect(round_panel.left + 18, round_panel.top + 10,
                               round_panel.width - 36, 10)
        self._render_round_bar(surface, bar_rect)

        cards_y = round_panel.bottom + 16
        card_gap = 14
        total_cw = len(self._skill_cards) * SkillCard.CARD_WIDTH + (len(self._skill_cards) - 1) * card_gap
        cards_x = (sw - total_cw) // 2
        for i, card in enumerate(self._skill_cards):
            card.render(surface, cards_x + i * (SkillCard.CARD_WIDTH + card_gap), cards_y)
            if self._last_skill_idx == i and self._impact_flash > 0:
                pygame.draw.rect(surface, SKILL_COLORS[i % len(SKILL_COLORS)], card.rect.inflate(6, 6), width=2, border_radius=8)

        action_y = cards_y + SkillCard.CARD_HEIGHT + 18
        action_panel = pygame.Rect(sw // 2 - 380, action_y, 760, 44)
        pygame.draw.rect(surface, (255, 248, 214), action_panel, border_radius=8)
        pygame.draw.rect(surface, (108, 143, 76), action_panel, width=2, border_radius=8)
        latest = self._battle_log[-1] if self._battle_log else "准备战斗"
        Label(latest, self._font_small, (42, 63, 42)).render_centered(surface, action_panel.centerx, action_panel.centery)

        if self._anim_state == "intro":
            self._render_overlay(surface, f"准备挑战 Boss #{self._current_boss_idx + 1}", COLOR_ACCENT)
        elif self._anim_state == "victory":
            self._render_overlay(surface, "胜 利", COLOR_GREEN)
        elif self._anim_state == "retry":
            self._render_retry_overlay(surface)
        elif self._anim_state == "defeat":
            self._render_overlay(surface, "失 败", COLOR_RED)


    def _render_retry_overlay(self, surface: pygame.Surface) -> None:
        sw, sh = surface.get_size()
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((24, 18, 12, 150))
        surface.blit(overlay, (0, 0))
        panel = pygame.Rect(sw // 2 - 285, sh // 2 - 150, 570, 278)
        pygame.draw.rect(surface, (255, 246, 220), panel, border_radius=14)
        pygame.draw.rect(surface, (142, 104, 56), panel, width=3, border_radius=14)
        pygame.draw.line(surface, (255, 218, 105), (panel.left + 44, panel.top + 66), (panel.right - 44, panel.top + 66), 3)
        Label("回合耗尽", self._font_large, COLOR_RED).render_centered(surface, panel.centerx, panel.top + 42)
        cost = self._retry_cost()
        if self._can_retry():
            detail = f"消耗 {cost} 资源复活并从第一个 Boss 重打"
        else:
            detail = "当前资源不足，无法复活"
        Label(detail, self._font, (62, 74, 45)).render_centered(surface, panel.centerx, panel.top + 100)
        Label(f"当前资源: {self._coin_total}", self._font, COLOR_GOLD).render_centered(surface, panel.centerx, panel.top + 136)

        if self._needs_layout:
            self._buttons.clear()
            if self._can_retry():
                self._buttons.append(Button(
                    pygame.Rect(panel.centerx - 205, panel.bottom - 78, 190, 46),
                    "复活重打 (R)", self._font_small,
                    color_normal=(62, 150, 86), color_hover=(78, 181, 106),
                    callback=self._retry_with_coins,
                ))
                quit_x = panel.centerx + 15
            else:
                quit_x = panel.centerx - 95
            self._buttons.append(Button(
                pygame.Rect(quit_x, panel.bottom - 78, 190, 46),
                "放弃", self._font_small,
                color_normal=(142, 70, 70), color_hover=(173, 86, 86),
                callback=lambda: self._on_defeat("放弃复活"),
            ))
            self._needs_layout = False
        for btn in self._buttons:
            btn.render(surface)

    def _render_choose(self, surface: pygame.Surface, sw: int, sh: int) -> None:
        panel = pygame.Rect(sw // 2 - 250, sh // 2 - 145, 500, 250)
        pygame.draw.rect(surface, (19, 16, 24, 220), panel, border_radius=12)
        pygame.draw.rect(surface, (157, 69, 76, 180), panel, width=1, border_radius=12)
        Label("Boss 战即将开始", self._font_large, COLOR_ACCENT).render_centered(surface, sw // 2, panel.top + 48)
        Label("请选择战斗模式", self._font, COLOR_TEXT).render_centered(surface, sw // 2, panel.top + 96)

        if self._needs_layout:
            self._buttons.clear()
            self._buttons.append(Button(pygame.Rect(sw // 2 - 185, panel.top + 145, 170, 50),
                                        "自动战斗 (A)", self._font, color_normal=(40, 120, 60),
                                        callback=lambda: (setattr(self, '_auto_battle', True),
                                                          self._init_battle(reset_known=True))))
            self._buttons.append(Button(pygame.Rect(sw // 2 + 15, panel.top + 145, 170, 50),
                                        "手动战斗 (M)", self._font, color_normal=(120, 100, 40),
                                        callback=lambda: (setattr(self, '_auto_battle', False),
                                                          self._init_battle(reset_known=True))))
            self._needs_layout = False
        for btn in self._buttons:
            btn.render(surface)

    def _render_combatants(self, surface: pygame.Surface, boss_area: pygame.Rect) -> None:
        bob = math.sin(self._time * 4.0) * 5
        player_x = boss_area.left + 220 + int(self._player_lunge * 160)
        player_y = boss_area.centery + 22 + int(bob)
        shake_x = random.randint(-7, 7) if self._boss_shake > 0 else 0
        shake_y = random.randint(-5, 5) if self._boss_shake > 0 else 0
        boss_x = boss_area.right - 260 + shake_x
        boss_y = boss_area.centery + 4 + int(math.sin(self._time * 3.0) * 4) + shake_y

        for cx, cy, w in ((player_x, player_y + 61, 118), (boss_x, boss_y + 78, 150)):
            shadow = pygame.Surface((w, 28), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow, (0, 0, 0, 110), shadow.get_rect())
            surface.blit(shadow, shadow.get_rect(center=(cx, cy)))

        player_img = self._am.get_image("player", (108, 108))
        boss_img = self._am.get_image("boss", (138, 138))
        surface.blit(player_img, player_img.get_rect(center=(player_x, player_y)))
        surface.blit(boss_img, boss_img.get_rect(center=(boss_x, boss_y)))

        if self._impact_flash > 0:
            flash = pygame.Surface((190, 190), pygame.SRCALPHA)
            alpha = int(150 * min(1.0, self._impact_flash / 0.22))
            pygame.draw.circle(flash, (255, 220, 145, alpha), (95, 95), 92, width=8)
            pygame.draw.circle(flash, (255, 90, 90, alpha), (95, 95), 58, width=4)
            surface.blit(flash, flash.get_rect(center=(boss_x, boss_y)))

    def _render_boss_status(self, surface: pygame.Surface, boss_area: pygame.Rect) -> None:
        Label(f"Boss #{self._current_boss_idx + 1}/{len(self._boss_hp_list)}", self._font_large,
              COLOR_RED).render_centered(surface, boss_area.centerx, boss_area.top + 25)
        hp_text = f"HP: {self._current_boss_hp_left}/{self._boss_start_hp}"
        hp_color = COLOR_GREEN
        Label(hp_text, self._font, hp_color).render_centered(surface, boss_area.centerx, boss_area.bottom - 28)

        hp_bar = pygame.Rect(boss_area.centerx - 150, boss_area.bottom - 52, 300, 10)
        pygame.draw.rect(surface, (56, 38, 45), hp_bar, border_radius=5)
        frac = max(0.0, min(1.0, self._current_boss_hp_left / max(1, self._boss_start_hp)))
        pygame.draw.rect(surface, (210, 68, 82), (hp_bar.left, hp_bar.top, int(hp_bar.width * frac), hp_bar.height), border_radius=5)
        pygame.draw.rect(surface, (255, 232, 182), hp_bar, width=1, border_radius=5)

    def _render_round_bar(self, surface: pygame.Surface, bar_rect: pygame.Rect) -> None:
        pygame.draw.rect(surface, (60, 45, 55), bar_rect, border_radius=6)
        frac = min(1.0, self._rounds_used / self._round_limit) if self._round_limit else 0
        fill_c = COLOR_GREEN if frac < 0.7 else (COLOR_GOLD if frac < 0.9 else COLOR_RED)
        if frac > 0:
            pygame.draw.rect(surface, fill_c, pygame.Rect(bar_rect.left, bar_rect.top,
                             int(bar_rect.width * frac), bar_rect.height), border_radius=6)
        mode = "自动" if self._auto_battle else "手动"
        Label(f"总回合: {self._rounds_used}/{self._round_limit}  |  当前Boss: {self._boss_round}  |  "
              f"金币: {self._coin_total}  |  {mode}模式",
              self._font_small, (242, 239, 210)).render_centered(
                  surface, bar_rect.centerx, bar_rect.bottom + 15)

    def _render_skill_effects(self, surface: pygame.Surface) -> None:
        for effect in self._skill_effects:
            t = min(1.0, effect["age"] / max(0.001, effect["duration"]))
            alpha = int(255 * (1.0 - max(0.0, t - 0.65) / 0.35))
            if effect["kind"] in ("projectile", "slash"):
                sx, sy = effect["start"]
                ex, ey = effect["end"]
                x = sx + (ex - sx) * t
                y = sy + (ey - sy) * t
                color = effect["color"]
                if effect["kind"] == "projectile":
                    pygame.draw.line(surface, (*color, max(60, alpha // 2)), (sx, sy), (x, y), 4)
                    pygame.draw.circle(surface, color, (int(x), int(y)), 13)
                    pygame.draw.circle(surface, (255, 255, 255), (int(x), int(y)), 5)
                else:
                    length = 80
                    pygame.draw.line(surface, color, (x - length * 0.45, y + 32), (x + length * 0.45, y - 32), 8)
                    pygame.draw.line(surface, (255, 245, 210), (x - length * 0.25, y + 18), (x + length * 0.25, y - 18), 3)
            elif effect["kind"] == "text":
                surf = self._font_large.render(effect["text"], True, effect["color"])
                surf.set_alpha(alpha)
                surface.blit(surf, surf.get_rect(center=(effect["x"], effect["y"])))

    def _render_overlay(self, surface: pygame.Surface, text: str, color: tuple[int, int, int]) -> None:
        sw, sh = surface.get_size()
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))
        panel = pygame.Rect(sw // 2 - 235, sh // 2 - 62, 470, 124)
        pygame.draw.rect(surface, (35, 31, 38), panel, border_radius=14)
        pygame.draw.rect(surface, color, panel, width=2, border_radius=14)
        pygame.draw.line(surface, (115, 105, 104),
                         (panel.left + 70, panel.centery + 29),
                         (panel.right - 70, panel.centery + 29), 1)
        Label(text, self._font_large, color).render_centered(
            surface, panel.centerx, panel.centery - 5)
