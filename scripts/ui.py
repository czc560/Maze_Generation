from __future__ import annotations

import statistics
import tkinter as tk
from typing import Optional

from .ai_player import ProbeAI
from .config import ASSETS
from .maze import Maze, SYMBOLS
from .strategies import evaluate_distribution, generate_normalized_maze


COLORS = ASSETS["colors"]


class MazeUI:
    def __init__(
        self,
        rows: int,
        cols: int,
        seed: int = 42,
        k: float = 4.0,
        cell_size: int = 24,
    ) -> None:
        self.rows = rows
        self.cols = cols
        self.seed = seed
        self.k = k
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

        tk.Button(controls, text="Regenerate", command=self.regenerate).pack(side=tk.LEFT, padx=6)
        tk.Button(controls, text="Evaluate", command=self.evaluate).pack(side=tk.LEFT, padx=6)
        tk.Button(controls, text="Run AI", command=self.run_ai).pack(side=tk.LEFT, padx=6)
        tk.Button(controls, text="Step AI", command=self.step_ai).pack(side=tk.LEFT, padx=6)
        tk.Button(controls, text="Reset AI", command=self.reset_ai).pack(side=tk.LEFT, padx=6)

        self.status_var = tk.StringVar(value="Ready")
        self.status_label = tk.Label(self.root, textvariable=self.status_var, anchor="w")
        self.status_label.pack(fill=tk.X)

        self.cells: list[list[int]] = []
        self.ai_marker: Optional[int] = None
        self.ai: Optional[ProbeAI] = None
        self.ai_running = False
        self.ai_delay_ms = 120

        self.maze, self.report = self._build_maze()
        self._draw_grid()
        self.canvas.bind("<Button-1>", self._on_click)

    def _build_maze(self) -> tuple[Maze, dict[str, float]]:
        return generate_normalized_maze(self.rows, self.cols, seed=self.seed, target_mean=self.k)

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
        except ValueError:
            self.status_var.set("Seed must be an integer and k must be a number")
            return

        self.maze, self.report = self._build_maze()
        self._draw_grid()
        self.reset_ai()
        self.status_var.set(
            f"Regenerated seed={self.seed} k={self.k:.2f} mean={self.report['mean']:.2f} std={self.report['std']:.2f}"
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
        cell_content = self.maze.grid[state.position[0]][state.position[1]].content
        if cell_content in {SYMBOLS["coin"], SYMBOLS["trap"]}:
            self.maze.grid[state.position[0]][state.position[1]].content = SYMBOLS["floor"]
            self._paint_cell(state.position[0], state.position[1], COLORS["visited"])
        else:
            self._mark_visited(state.position)

        self._draw_ai_marker(state.position)
        score = state.resources / state.steps if state.steps else 0.0
        self.status_var.set(
            f"AI steps={state.steps} resources={state.resources} score={score:.2f}"
        )

    def _ai_tick(self) -> None:
        if not self.ai_running:
            return
        self.step_ai()
        if self.ai is not None and not self.ai.is_finished():
            self.root.after(self.ai_delay_ms, self._ai_tick)
        else:
            self.ai_running = False

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

    def run(self) -> None:
        self.root.mainloop()


def run_tkinter_ui(rows: int, cols: int, seed: int, k: float) -> None:
    ui = MazeUI(rows=rows, cols=cols, seed=seed, k=k)
    ui.run()
