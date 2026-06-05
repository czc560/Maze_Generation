"""StrategySettingsScene — code-like AI parameter editor."""

from __future__ import annotations

import pygame

from game.scenes.base import Scene
from game.constants import COLOR_BG, COLOR_TEXT, COLOR_TEXT_DIM, COLOR_ACCENT
from game.ui.button import Button
from game.ui.label import Label
from game.ui.text_input import TextInput
from game.ui.panel import Panel

ALGO_OPTIONS = ["simple_greedy", "memory_greedy", "dqn"]
ALGO_LABELS = {"simple_greedy": "SimpleGreedy", "memory_greedy": "MemoryGreedy", "dqn": "DQN"}

ALGO_PARAMS = {
    "simple_greedy": [
        ("coin_weight", "金币吸引力"),
        ("trap_weight", "陷阱避开度"),
        ("end_weight",  "终点吸引力"),
    ],
    "memory_greedy": [
        ("coin_weight",     "金币吸引力"),
        ("trap_weight",     "陷阱避开度"),
        ("end_weight",      "终点吸引力"),
        ("visited_penalty", "已访问惩罚"),
        ("unvisited_bonus", "未访问奖励"),
    ],
    "dqn": [
        ("dqn_model_path", "模型路径"),
        ("dqn_epsilon",    "epsilon"),
    ],
}


class StrategySettingsScene(Scene):
    """Code-like parameter editing for AI strategies."""

    def __init__(self, manager) -> None:
        super().__init__(manager)
        am = self.engine.asset_manager
        self._font = am.get_font(None, 22)
        self._font_mono = am.get_font(None, 19)
        self._font_title = am.get_font(None, 32)

        cfg = getattr(self.engine, 'strategy_config', {})
        self._algo = cfg.get("ai_strategy", "memory_greedy")
        self._params = {
            "coin_weight":     str(cfg.get("coin_weight", 1.2)),
            "trap_weight":     str(cfg.get("trap_weight", 0.8)),
            "end_weight":      str(cfg.get("end_weight", 1.6)),
            "visited_penalty": str(cfg.get("visited_penalty", 2.0)),
            "unvisited_bonus": str(cfg.get("unvisited_bonus", 0.5)),
            "dqn_model_path":  str(cfg.get("dqn_model_path", "")),
            "dqn_epsilon":     str(cfg.get("dqn_epsilon", 0.05)),
        }
        self._skills = [list(s) for s in cfg.get("skills", [[8, 4], [2, 0], [4, 2], [6, 3]])]
        self._auto_battle = cfg.get("auto_battle", False)

        self._inputs: list[tuple[str, TextInput]] = []
        self._buttons: list[Button] = []
        self._needs_layout = True

    def enter(self) -> None:
        self._needs_layout = True

    def _layout(self, surface: pygame.Surface) -> None:
        sw, sh = surface.get_size()
        self._inputs.clear()
        self._buttons.clear()
        margin = 60
        panel_w = sw - 2 * margin
        lx = margin + 20

        # ---- AI section ----
        fields = ALGO_PARAMS[self._algo]
        ai_h = 100 + len(fields) * 34 + 40
        ai_y = 70
        self._ai_panel = Panel(pygame.Rect(margin, ai_y, panel_w, ai_h),
                               color=(28, 28, 42), border_color=(50, 50, 70))
        self._ai_rect = self._ai_panel.rect

        # ---- Boss skills section ----
        skill_y = ai_y + ai_h + 15
        skill_h = 130
        self._skill_panel = Panel(pygame.Rect(margin, skill_y, panel_w, skill_h),
                                  color=(28, 28, 42), border_color=(50, 50, 70))
        self._skill_rect = self._skill_panel.rect

        # ---- Inputs for AI params ----
        ly = ai_y + 55
        for key, label_text in fields:
            lbl = f"  {key:18s} = "
            inp = TextInput(pygame.Rect(lx + 250, ly - 2, 90, 26), self._font_mono,
                            default_text=self._params.get(key, ""))
            self._inputs.append((key, inp))
            ly += 34

        # ---- Toggle algo button ----
        next_idx = (ALGO_OPTIONS.index(self._algo) + 1) % len(ALGO_OPTIONS)
        next_name = ALGO_LABELS[ALGO_OPTIONS[next_idx]]
        self._buttons.append(Button(pygame.Rect(lx, ai_y + ai_h - 50, 200, 30),
                                    f"切换为 {next_name}", self._font_mono,
                                    callback=self._toggle_algo))

        # ---- Auto-battle toggle ----
        auto_text = "自动战斗: [✓] ON" if self._auto_battle else "自动战斗: [ ] OFF"
        self._auto_btn = Button(pygame.Rect(lx + 220, ai_y + ai_h - 50, 200, 30),
                                auto_text, self._font_mono,
                                callback=self._toggle_auto_battle)
        self._buttons.append(self._auto_btn)

        # ---- Save / Cancel ----
        save_y = skill_y + skill_h + 20
        self._save_btn = Button(pygame.Rect(sw // 2 - 100, save_y, 200, 44),
                                "保存并返回", self._font,
                                color_normal=(40, 120, 60), color_hover=(55, 150, 80),
                                callback=self._save_and_close)
        self._buttons.append(self._save_btn)
        self._buttons.append(Button(pygame.Rect(sw // 2 - 100, save_y + 54, 200, 44),
                                    "取消返回", self._font,
                                    color_normal=(120, 40, 40), color_hover=(150, 55, 55),
                                    callback=lambda: self.manager.pop()))
        self._needs_layout = False

    def _toggle_algo(self):
        idx = (ALGO_OPTIONS.index(self._algo) + 1) % len(ALGO_OPTIONS)
        self._algo = ALGO_OPTIONS[idx]
        self._needs_layout = True

    def _toggle_auto_battle(self):
        self._auto_battle = not self._auto_battle
        self._needs_layout = True

    def _save_and_close(self):
        cfg = {"ai_strategy": self._algo, "auto_battle": self._auto_battle,
               "skills": [list(s) for s in self._skills]}
        for key, inp in self._inputs:
            val = inp.text.strip()
            try:
                cfg[key] = float(val) if '.' in val else val
            except ValueError:
                cfg[key] = val
        for k in ALGO_PARAMS["memory_greedy"] + ALGO_PARAMS["simple_greedy"] + ALGO_PARAMS["dqn"]:
            if k[0] in cfg and k[0] not in ("dqn_model_path",):
                try: cfg[k[0]] = float(cfg[k[0]])
                except (ValueError, TypeError): pass
        self.engine.strategy_config = cfg
        self.manager.pop()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.manager.pop(); return
        for _, inp in self._inputs: inp.handle_event(event)
        for btn in self._buttons: btn.handle_event(event)

    def update(self, dt: float) -> None:
        for _, inp in self._inputs: inp.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        if self._needs_layout: self._layout(surface)
        surface.fill(COLOR_BG)
        sw = surface.get_width()

        Label("策 略 设 置", self._font_title, COLOR_ACCENT).render_centered(surface, sw // 2, 25)

        self._ai_panel.render(surface)
        self._skill_panel.render(surface)

        # AI section content
        lx = self._ai_rect.x + 20
        algo = self._algo
        fields = ALGO_PARAMS[algo]

        Label(f"── 寻路 AI: {ALGO_LABELS[algo]} ──", self._font, COLOR_ACCENT).render(surface, lx, self._ai_rect.y + 15)

        ly = self._ai_rect.y + 55
        for key, label_text in fields:
            Label(f"  {key:18s} = ", self._font_mono, COLOR_TEXT).render(surface, lx, ly)
            Label(f"# {label_text}", self._font_mono, COLOR_TEXT_DIM).render(surface, lx + 355, ly)
            ly += 34

        for _, inp in self._inputs: inp.render(surface)

        # Boss skills section
        ly = self._skill_rect.y + 20
        Label("── Boss 技能配置 ──", self._font, COLOR_ACCENT).render(surface, lx, ly)
        ly += 32
        skill_text = "skills = [" + ", ".join(f"[{d},{c}]" for d, c in self._skills) + "]"
        Label(skill_text, self._font_mono, COLOR_TEXT).render(surface, lx, ly)
        ly += 35
        # Add/remove buttons
        add_btn = Button(pygame.Rect(lx, ly, 100, 28), "+ 添加", self._font_mono,
                         callback=lambda: (self._skills.append([5, 2]) if len(self._skills) < 8 else None,
                                          setattr(self, '_needs_layout', True)))
        del_btn = Button(pygame.Rect(lx + 115, ly, 100, 28), "× 删除最后", self._font_mono,
                         callback=lambda: (self._skills.pop() if len(self._skills) > 1 else None,
                                          setattr(self, '_needs_layout', True)))
        add_btn.render(surface)
        del_btn.render(surface)

        for btn in self._buttons:
            if btn not in (add_btn, del_btn):
                btn.render(surface)
