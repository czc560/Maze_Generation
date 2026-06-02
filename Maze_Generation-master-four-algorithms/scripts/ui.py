from __future__ import annotations

import statistics
import tkinter as tk
from typing import Any, Optional

from .ai_player import ProbeAI
from .config import ASSETS
from .game_rules import generate_game_rules, simulate_boss_gauntlet
from .maze import COIN_VALUE, Maze, SYMBOLS, normalize_generation_method
from .strategies import evaluate_distribution, generate_normalized_maze, optimal_path_max_coins


COLORS = ASSETS["colors"]

METHOD_LABELS: dict[str, str] = {
    "分治法": "divide_conquer",
    "回溯法": "backtracking",
    "分支限界法": "branch_bound",
    "最小生成树算法": "mst",
}
METHOD_NAMES = {value: key for key, value in METHOD_LABELS.items()}


class MazeUI:
    def __init__(
        self,
        rows: int,
        cols: int,
        seed: int = 42,
        k: float = 4.0,
        generation_method: str = "mst",
        cell_size: int = 24,
    ) -> None:
        self.rows = rows
        self.cols = cols
        self.seed = seed
        self.k = k
        self.generation_method = normalize_generation_method(generation_method)
        self.cell_size = cell_size

        self.root = tk.Tk()
        self.root.title("K-Centered Maze Viewer")
        self.canvas = tk.Canvas(
            self.root,
            width=self.cols * self.cell_size,
            height=self.rows * self.cell_size,
            highlightthickness=0,
        )
        self.canvas.pack()

        controls = tk.Frame(self.root)
        controls.pack(fill=tk.X)

        tk.Label(controls, text="Seed:").pack(side=tk.LEFT, padx=4)
        self.seed_var = tk.StringVar(value=str(self.seed))
        self.seed_entry = tk.Entry(controls, textvariable=self.seed_var, width=10)
        self.seed_entry.pack(side=tk.LEFT)

        tk.Label(controls, text="k:").pack(side=tk.LEFT, padx=4)
        self.k_var = tk.StringVar(value=str(self.k))
        self.k_entry = tk.Entry(controls, textvariable=self.k_var, width=8)
        self.k_entry.pack(side=tk.LEFT)

        tk.Label(controls, text="算法:").pack(side=tk.LEFT, padx=4)
        self.method_var = tk.StringVar(value=METHOD_NAMES.get(self.generation_method, "最小生成树算法"))
        self.method_menu = tk.OptionMenu(controls, self.method_var, *METHOD_LABELS.keys())
        self.method_menu.pack(side=tk.LEFT)

        tk.Button(controls, text="Regenerate", command=self.regenerate).pack(side=tk.LEFT, padx=6)
        tk.Button(controls, text="Evaluate", command=self.evaluate).pack(side=tk.LEFT, padx=6)
        tk.Button(controls, text="Run AI", command=self.run_ai).pack(side=tk.LEFT, padx=6)
        tk.Button(controls, text="Step AI", command=self.step_ai).pack(side=tk.LEFT, padx=6)
        tk.Button(controls, text="Reset AI", command=self.reset_ai).pack(side=tk.LEFT, padx=6)

        self.status_var = tk.StringVar(value="Ready")
        self.status_label = tk.Label(self.root, textvariable=self.status_var, anchor="w")
        self.status_label.pack(fill=tk.X)

        self.cells: list[list[int]] = []
        self.initial_contents: list[list[str]] = []
        self.optimal_path: list[tuple[int, int]] = []
        self.optimal_overlay: list[int] = []
        self.ai_route: list[tuple[int, int]] = []
        self.comparison_shown = False
        self.comparison_pending = False
        self.boss_battle_active = False
        self.ai_marker: Optional[int] = None
        self.ai: Optional[ProbeAI] = None
        self.ai_running = False
        self.ai_delay_ms = 120

        self.maze, self.report, self.game_rules = self._build_maze()
        self.initial_contents = [
            [node.content for node in row] for row in self.maze.grid
        ]
        self.optimal_path = optimal_path_max_coins(self.maze)
        self._draw_grid()
        self._draw_optimal_path()
        self.canvas.bind("<Button-1>", self._on_click)

    def _build_maze(self) -> tuple[Maze, dict[str, float], dict[str, Any]]:
        maze, report = generate_normalized_maze(
            self.rows,
            self.cols,
            seed=self.seed,
            target_mean=self.k,
            generation_method=self.generation_method,
        )
        rules = generate_game_rules(maze)
        return maze, report, rules

    def _draw_grid(self) -> None:
        self.canvas.delete("all")
        self.cells = []
        for row in range(self.rows):
            row_cells: list[int] = []
            for col in range(self.cols):
                x1 = col * self.cell_size
                y1 = row * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size
                fill = self._cell_color(self.maze.grid[row][col].content)
                rect_id = self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill=fill, outline="#2e2e2e"
                )
                row_cells.append(rect_id)
            self.cells.append(row_cells)

    def _draw_optimal_path(self) -> None:
        for item in self.optimal_overlay:
            self.canvas.delete(item)
        self.optimal_overlay = []

        if not self.optimal_path:
            return

        for row, col in self.optimal_path:
            x1 = col * self.cell_size + self.cell_size * 0.35
            y1 = row * self.cell_size + self.cell_size * 0.35
            x2 = col * self.cell_size + self.cell_size * 0.65
            y2 = row * self.cell_size + self.cell_size * 0.65
            dot = self.canvas.create_oval(
                x1,
                y1,
                x2,
                y2,
                fill="#6dd3ce",
                outline="",
            )
            self.optimal_overlay.append(dot)


    def _cell_color(self, content: str) -> str:
        palette = {
            SYMBOLS["wall"]: COLORS["wall"],
            SYMBOLS["floor"]: COLORS["floor"],
            SYMBOLS["start"]: COLORS["start"],
            SYMBOLS["end"]: COLORS["end"],
            SYMBOLS["boss"]: COLORS["boss"],
            SYMBOLS["coin"]: COLORS["coin"],
            SYMBOLS["trap"]: COLORS["trap"],
        }
        return palette.get(content, "#ffffff")

    def _paint_cell(self, row: int, col: int, color: str) -> None:
        rect_id = self.cells[row][col]
        self.canvas.itemconfigure(rect_id, fill=color)

    def regenerate(self) -> None:
        try:
            self.seed = int(self.seed_var.get())
            self.k = float(self.k_var.get())
            self.generation_method = METHOD_LABELS[self.method_var.get()]
        except ValueError:
            self.status_var.set("Seed must be an integer and k must be a number")
            return
        except KeyError:
            self.status_var.set("请选择有效的迷宫生成算法")
            return

        self.maze, self.report, self.game_rules = self._build_maze()
        self.initial_contents = [
            [node.content for node in row] for row in self.maze.grid
        ]
        self.optimal_path = optimal_path_max_coins(self.maze)
        self._draw_grid()
        self._draw_optimal_path()
        self.reset_ai()
        self.status_var.set(
            f"Regenerated method={self.method_var.get()} seed={self.seed} k={self.k:.2f} "
            f"mean={self.report['mean']:.2f} std={self.report['std']:.2f}"
        )

    def evaluate(self) -> None:
        results = evaluate_distribution(self.maze)
        scores = [r.score for r in results]
        reached = sum(1 for r in results if r.reached_end)
        mean_score = statistics.mean(scores) if scores else 0.0
        stdev_score = statistics.pstdev(scores) if len(scores) > 1 else 0.0
        self.status_var.set(
            f"Reached {reached}/{len(results)} | mean={mean_score:.2f} | std={stdev_score:.2f} | target k={self.k:.2f}"
        )

    def _on_click(self, event: tk.Event) -> None:
        col = int(event.x // self.cell_size)
        row = int(event.y // self.cell_size)
        if not (0 <= row < self.rows and 0 <= col < self.cols):
            return
        content = self.maze.grid[row][col].content
        self.status_var.set(f"Cell ({row}, {col}) = {content}")

    def _ensure_ai(self) -> ProbeAI:
        if self.ai is None:
            self.ai = ProbeAI(self.maze, aggression=0.55, probe_depth=6, rollouts=6, seed=self.seed)
        return self.ai

    def _content_at(self, row: int, col: int) -> str:
        if 0 <= row < len(self.initial_contents) and 0 <= col < len(self.initial_contents[row]):
            return self.initial_contents[row][col]
        return self.maze.grid[row][col].content

    def _current_coin_total(self) -> int:
        if self.ai is not None:
            return len(self.ai.collected_coins) * COIN_VALUE
        return 0

    def _draw_ai_marker(self, pos: tuple[int, int]) -> None:
        row, col = pos
        x1 = col * self.cell_size + 4
        y1 = row * self.cell_size + 4
        x2 = x1 + self.cell_size - 8
        y2 = y1 + self.cell_size - 8
        if self.ai_marker is None:
            self.ai_marker = self.canvas.create_oval(x1, y1, x2, y2, fill=COLORS["ai"], outline="")
        else:
            self.canvas.coords(self.ai_marker, x1, y1, x2, y2)

    def _mark_visited(self, pos: tuple[int, int]) -> None:
        row, col = pos
        content = self.maze.grid[row][col].content
        if content in {SYMBOLS["floor"], SYMBOLS["start"]}:
            self._paint_cell(row, col, COLORS["visited"])

    def step_ai(self) -> None:
        ai = self._ensure_ai()
        if ai.is_finished():
            self.status_var.set("AI finished")
            return

        state = ai.step()
        if not self.ai_route:
            if self.maze.start is not None:
                self.ai_route = [self.maze.start]
        self.ai_route.append(state.position)
        cell_content = self.maze.grid[state.position[0]][state.position[1]].content
        if cell_content == SYMBOLS["boss"]:
            self._run_boss_battle()
            self.maze.grid[state.position[0]][state.position[1]].content = SYMBOLS["floor"]
            self._paint_cell(state.position[0], state.position[1], COLORS["visited"])
        elif cell_content in {SYMBOLS["coin"], SYMBOLS["trap"]}:
            self.maze.grid[state.position[0]][state.position[1]].content = SYMBOLS["floor"]
            self._paint_cell(state.position[0], state.position[1], COLORS["visited"])
        else:
            self._mark_visited(state.position)

        self._draw_ai_marker(state.position)
        score = state.resources / state.steps if state.steps else 0.0
        self.status_var.set(
            f"AI steps={state.steps} resources={state.resources} score={score:.2f}"
        )
        if ai.is_finished() and not self.comparison_shown:
            self.comparison_pending = True
            if not self.boss_battle_active:
                self._show_route_comparison()

    def _ai_tick(self) -> None:
        if not self.ai_running:
            return
        self.step_ai()
        if self.ai is not None and not self.ai.is_finished():
            self.root.after(self.ai_delay_ms, self._ai_tick)
        else:
            self.ai_running = False
            if not self.comparison_shown:
                self.comparison_pending = True
                if not self.boss_battle_active:
                    self._show_route_comparison()

    def run_ai(self) -> None:
        if self.ai_running:
            return
        self.ai_running = True
        self._ai_tick()

    def reset_ai(self) -> None:
        self.ai_running = False
        if self.ai_marker is not None:
            self.canvas.delete(self.ai_marker)
            self.ai_marker = None
        self.ai = None
        self.ai_route = [self.maze.start] if self.maze.start is not None else []
        self.comparison_shown = False
        self.comparison_pending = False
        self.boss_battle_active = False

    def _route_stats(self, path: list[tuple[int, int]]) -> dict[str, Any]:
        coins: set[tuple[int, int]] = set()
        for row, col in path:
            content = self._content_at(row, col)
            if content == SYMBOLS["coin"]:
                coins.add((row, col))

        boss_hp_list = self.game_rules.get("boss_hp", [])
        coin_total = len(coins) * COIN_VALUE
        battle = simulate_boss_gauntlet(
            boss_hp_list,
            self.game_rules.get("player_skills", []),
            self.game_rules.get("min_rounds", 0),
            coin_total,
            self.game_rules.get("coin_consumption", 1),
        )

        boss_index = battle["boss_index"]
        remaining_list: list[int] = []
        if boss_index < len(boss_hp_list):
            remaining_list.append(battle["boss_remaining"])
            remaining_list.extend(boss_hp_list[boss_index + 1 :])

        return {
            "steps": max(0, len(path) - 1),
            "coins": len(coins),
            "coin_value": coin_total,
            "coins_left": battle["coins_left"],
            "boss_remaining": remaining_list,
        }

    def _show_route_comparison(self) -> None:
        if self.comparison_shown:
            return
        self.comparison_shown = True

        ai_path = self.ai_route
        optimal_path = self.optimal_path
        if not ai_path or not optimal_path:
            return

        ai_stats = self._route_stats(ai_path)
        opt_stats = self._route_stats(optimal_path)

        window = tk.Toplevel(self.root)
        window.title("Route Comparison")

        header = tk.Frame(window)
        header.pack(fill=tk.X, padx=10, pady=6)
        tk.Label(header, text="Route", width=12, anchor="w").grid(row=0, column=0)
        tk.Label(header, text="Steps", width=10, anchor="w").grid(row=0, column=1)
        tk.Label(header, text="Coins", width=10, anchor="w").grid(row=0, column=2)
        tk.Label(header, text="Coins Left", width=12, anchor="w").grid(row=0, column=3)
        tk.Label(header, text="Boss HP Left", width=18, anchor="w").grid(row=0, column=4)

        def add_row(row: int, name: str, stats: dict[str, Any]) -> None:
            tk.Label(header, text=name, width=12, anchor="w").grid(row=row, column=0)
            tk.Label(header, text=str(stats["steps"]), width=10, anchor="w").grid(row=row, column=1)
            tk.Label(header, text=str(stats["coins"]), width=10, anchor="w").grid(row=row, column=2)
            tk.Label(header, text=str(stats["coins_left"]), width=12, anchor="w").grid(row=row, column=3)
            remaining = stats["boss_remaining"]
            remaining_text = "[]" if not remaining else str(remaining)
            tk.Label(header, text=remaining_text, width=18, anchor="w").grid(row=row, column=4)

        add_row(1, "AI", ai_stats)
        add_row(2, "Optimal", opt_stats)

    def _run_boss_battle(self) -> None:
        self.boss_battle_active = True
        boss_hp_list = self.game_rules.get("boss_hp", [])
        skills = self.game_rules.get("player_skills", [])
        player_hp = self.game_rules.get("player_hp", 100)
        round_limit = self.game_rules.get("min_rounds", 0)
        coin_consumption = self.game_rules.get("coin_consumption", 1)
        if not boss_hp_list or not skills:
            return

        coin_total = self._current_coin_total()
        battle = simulate_boss_gauntlet(
            boss_hp_list,
            skills,
            round_limit,
            coin_total,
            coin_consumption,
        )
        battle_log = battle["log"]
        if not battle_log:
            return

        window = tk.Toplevel(self.root)
        window.title("Boss Battle")
        window.resizable(False, False)

        def finalize_battle() -> None:
            if not window.winfo_exists():
                return
            window.destroy()
            self.boss_battle_active = False
            if self.comparison_pending and not self.comparison_shown:
                self._show_route_comparison()

        window.protocol("WM_DELETE_WINDOW", finalize_battle)

        header = tk.Frame(window)
        header.pack(fill=tk.X, padx=10, pady=6)

        player_var = tk.StringVar(value=f"Player HP: {player_hp}")
        boss_var = tk.StringVar(value="Boss HP: ???")
        round_var = tk.StringVar(value=f"Round: 0/{round_limit}")
        boss_index_var = tk.StringVar(value="Boss: 1")
        coins_var = tk.StringVar(value=f"Coins: {coin_total}")

        tk.Label(header, textvariable=player_var).pack(side=tk.LEFT, padx=6)
        tk.Label(header, textvariable=boss_var).pack(side=tk.LEFT, padx=6)
        tk.Label(header, textvariable=round_var).pack(side=tk.LEFT, padx=6)
        tk.Label(header, textvariable=boss_index_var).pack(side=tk.LEFT, padx=6)
        tk.Label(header, textvariable=coins_var).pack(side=tk.LEFT, padx=6)

        scene = tk.Canvas(window, width=520, height=300, highlightthickness=0)
        scene.pack(padx=10, pady=4)

        for i in range(0, 300, 24):
            color = "#2b2d42" if (i // 24) % 2 == 0 else "#24263a"
            scene.create_rectangle(0, i, 520, i + 24, fill=color, outline=color)

        for i in range(0, 520, 26):
            scene.create_rectangle(i, 0, i + 14, 300, fill="#1c1d2b", outline="", stipple="gray12")

        vignette = []
        vignette.append(scene.create_rectangle(0, 0, 520, 18, fill="#11121a", outline=""))
        vignette.append(scene.create_rectangle(0, 282, 520, 300, fill="#11121a", outline=""))
        vignette.append(scene.create_rectangle(0, 0, 18, 300, fill="#11121a", outline=""))
        vignette.append(scene.create_rectangle(502, 0, 520, 300, fill="#11121a", outline=""))

        particles: list[tuple[int, float]] = []
        for i in range(18):
            x = 30 + i * 26
            y = 40 + (i % 6) * 36
            radius = 3 + (i % 3)
            pid = scene.create_oval(x, y, x + radius, y + radius, fill="#3b3f5c", outline="")
            particles.append((pid, 0.4 + (i % 4) * 0.2))

        player_x, player_y = 120, 190
        boss_x, boss_y = 400, 140

        player_body = scene.create_oval(
            player_x - 28, player_y - 28, player_x + 28, player_y + 28, fill="#6c5ce7", outline=""
        )
        player_name = scene.create_text(player_x, player_y + 44, text="Player", fill="#e0e0e0")

        boss_body = scene.create_oval(
            boss_x - 46, boss_y - 46, boss_x + 46, boss_y + 46, fill="#e76f51", outline=""
        )
        boss_eye_left = scene.create_oval(boss_x - 18, boss_y - 12, boss_x - 8, boss_y - 2, fill="#1d1d1d", outline="")
        boss_eye_right = scene.create_oval(boss_x + 8, boss_y - 12, boss_x + 18, boss_y - 2, fill="#1d1d1d", outline="")
        boss_name = scene.create_text(boss_x, boss_y + 60, text="Boss", fill="#e0e0e0")
        boss_items = [boss_body, boss_eye_left, boss_eye_right, boss_name]

        player_max = max(1, player_hp)
        boss_max = max(1, max(boss_hp_list))

        player_bar_bg = scene.create_rectangle(30, 16, 220, 30, fill="#1f1f1f", outline="")
        boss_bar_bg = scene.create_rectangle(300, 16, 490, 30, fill="#1f1f1f", outline="")
        player_bar = scene.create_rectangle(30, 16, 220, 30, fill="#6c5ce7", outline="")
        boss_bar = scene.create_rectangle(300, 16, 490, 30, fill="#e76f51", outline="")

        skill_frame = tk.Frame(window)
        skill_frame.pack(fill=tk.X, padx=10, pady=4)
        skill_labels: list[tk.Label] = []
        for idx, (damage, cooldown) in enumerate(skills):
            label = tk.Label(
                skill_frame,
                text=f"Skill {idx + 1}: dmg={damage} cd={cooldown} cur=0",
                relief=tk.RIDGE,
                padx=6,
                pady=2,
            )
            label.pack(side=tk.LEFT, padx=4)
            skill_labels.append(label)

        log_box = tk.Text(window, height=8, width=60, state=tk.DISABLED)
        log_box.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        delay_ms = 800

        def append_log(text: str) -> None:
            log_box.configure(state=tk.NORMAL)
            log_box.insert(tk.END, text + "\n")
            log_box.see(tk.END)
            log_box.configure(state=tk.DISABLED)

        def update_bars(current_boss: int) -> None:
            player_width = 190 * max(0.0, player_hp / player_max)
            boss_width = 190 * max(0.0, current_boss / boss_max)
            scene.coords(player_bar, 30, 16, 30 + player_width, 30)
            scene.coords(boss_bar, 300, 16, 300 + boss_width, 30)

        def play_attack_effect(entry: dict[str, Any]) -> None:
            skill_index = entry["skill_index"]
            if skill_index is None:
                return

            card = scene.create_rectangle(
                player_x - 16, player_y - 22, player_x + 16, player_y + 22, fill="#f4d35e", outline="#1f1f1f", width=2
            )
            card_text = scene.create_text(player_x, player_y, text="ATK", fill="#1f1f1f", font=("Helvetica", 10, "bold"))

            damage_text = scene.create_text(
                boss_x, boss_y - 60, text=f"-{entry['damage']}", fill="#ff6b6b", font=("Helvetica", 14, "bold")
            )

            shake_offsets = [0, -6, 6, -4, 4, 0]

            def fly(step: int, steps: int = 8) -> None:
                dx = (boss_x - player_x) / steps
                dy = (boss_y - player_y) / steps
                scene.move(card, dx, dy)
                scene.move(card_text, dx, dy)
                if step + 1 < steps:
                    window.after(40, lambda: fly(step + 1, steps))
                else:
                    scene.delete(card)
                    scene.delete(card_text)

            def shake(step: int, prev: int) -> None:
                dx = shake_offsets[step] - prev
                for item in boss_items:
                    scene.move(item, dx, 0)
                if step + 1 < len(shake_offsets):
                    window.after(30, lambda: shake(step + 1, shake_offsets[step]))

            def float_text(step: int) -> None:
                scene.move(damage_text, 0, -4)
                if step < 6:
                    window.after(30, lambda: float_text(step + 1))
                else:
                    scene.delete(damage_text)

            window.after(0, lambda: fly(0))
            window.after(140, lambda: shake(0, 0))
            window.after(140, lambda: float_text(0))

        def drift_particles() -> None:
            for pid, speed in particles:
                scene.move(pid, speed, 0)
                x1, _, x2, _ = scene.coords(pid)
                if x1 > 520:
                    scene.move(pid, -540, 0)
            window.after(60, drift_particles)

        def show_end_panel(won: bool) -> None:
            panel = tk.Frame(window, bg="#11121a", bd=2, relief=tk.RIDGE)
            panel.place(relx=0.5, rely=0.5, anchor="center", width=240, height=120)
            title = "Victory" if won else "Defeat"
            subtitle = "Boss defeated" if won else "Player fell"
            tk.Label(panel, text=title, bg="#11121a", fg="#f4d35e", font=("Helvetica", 16, "bold")).pack(pady=(16, 4))
            tk.Label(panel, text=subtitle, bg="#11121a", fg="#d0d0d0").pack()
            if self.ai_running:
                window.after(600, finalize_battle)

        def render_step(index: int) -> None:
            entry = battle_log[index]
            event = entry.get("event")

            if event == "revive":
                coins_var.set(f"Coins: {entry['coins_left']}")
                append_log("Revive: restarting from Boss 1")
                window.after(delay_ms, lambda: render_step(index + 1))
                return
            if event == "fail":
                append_log("Battle failed: coins exhausted")
                window.after(300, lambda: show_end_panel(False))
                return

            boss_idx = entry.get("boss_index", 0)
            boss_index_var.set(f"Boss: {boss_idx + 1}")
            known_hp = entry.get("known_hp", [])
            display_hp = "???"
            if boss_idx < len(known_hp) and known_hp[boss_idx] is not None:
                display_hp = str(known_hp[boss_idx])
            boss_var.set(f"Boss HP: {display_hp}")

            if event in {"attack", "wait"}:
                round_var.set(f"Round: {entry['round']}/{round_limit}")
                if "boss_hp" in entry:
                    update_bars(entry["boss_hp"])

                if "cooldowns" in entry:
                    for i, label in enumerate(skill_labels):
                        damage, cooldown = skills[i]
                        cur_cd = entry["cooldowns"][i]
                        label.configure(text=f"Skill {i + 1}: dmg={damage} cd={cooldown} cur={cur_cd}")

            if event == "wait":
                append_log(f"Turn {entry['round']}: wait (no skill ready)")
            elif event == "attack":
                skill_index = entry["skill_index"]
                append_log(
                    f"Turn {entry['round']}: skill {skill_index + 1} damage={entry['damage']} boss_hp={entry['boss_hp']}"
                )
                play_attack_effect(entry)
            elif event == "defeat":
                append_log(f"Boss {boss_idx + 1} defeated")

            if index + 1 < len(battle_log):
                window.after(delay_ms, lambda: render_step(index + 1))
            else:
                window.after(300, lambda: show_end_panel(True))

        drift_particles()
        render_step(0)

    def run(self) -> None:
        self.root.mainloop()


def run_tkinter_ui(rows: int, cols: int, seed: int, k: float, generation_method: str = "mst") -> None:
    ui = MazeUI(rows=rows, cols=cols, seed=seed, k=k, generation_method=generation_method)
    ui.run()
