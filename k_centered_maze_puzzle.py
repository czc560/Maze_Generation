from __future__ import annotations

import heapq
import math
import random
import statistics
import sys
import tkinter as tk
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


COIN_VALUE = 50
TRAP_VALUE = -30


@dataclass
class MazeNode:
    """A single maze cell."""

    content: str = "#"
    row: int = 0
    col: int = 0
    extra: Any = None
    params: dict[str, Any] = field(default_factory=dict)

    from __future__ import annotations

    import os
    import sys
    from typing import Optional

    ROOT = os.path.dirname(__file__)
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)

    from scripts.exporter import export_maze_json
    from scripts.maze import Maze
    from scripts.strategies import evaluate_distribution, generate_normalized_maze, make_normalized_strategies
    from scripts.ui import run_tkinter_ui


    def parse_args(argv: list[str]) -> tuple[int, int, int, float, bool, bool, Optional[str], bool]:
        """Very small CLI parser.

        Usage examples:
          python k_centered_maze_puzzle.py
          python k_centered_maze_puzzle.py 21 21
          python k_centered_maze_puzzle.py 21 21 --k 4.0 --seed 42 --eval
          python k_centered_maze_puzzle.py 21 21 --k 4.0 --ui
          python k_centered_maze_puzzle.py 21 21 --export out.json
        """
        ui = "--ui" in argv
        do_eval = "--eval" in argv
        no_calibrate = "--no-calibrate" in argv

        seed = 42
        k = 4.0
        export_path: Optional[str] = None

        if "--seed" in argv:
            idx = argv.index("--seed")
            if idx + 1 >= len(argv):
                raise ValueError("--seed requires an integer value")
            seed = int(argv[idx + 1])

        if "--k" in argv:
            idx = argv.index("--k")
            if idx + 1 >= len(argv):
                raise ValueError("--k requires a numeric value")
            k = float(argv[idx + 1])

        if "--export" in argv:
            idx = argv.index("--export")
            if idx + 1 >= len(argv):
                raise ValueError("--export requires a path")
            export_path = argv[idx + 1]

        positional: list[str] = []
        skip_next = False
        for item in argv:
            if skip_next:
                skip_next = False
                continue
            if item in {"--seed", "--k", "--export"}:
                skip_next = True
                continue
            if item in {"--ui", "--eval", "--no-calibrate"}:
                continue
            positional.append(item)

        if len(positional) >= 2:
            rows = int(positional[0])
            cols = int(positional[1])
        elif len(positional) == 1:
            rows = int(positional[0])
            cols = rows
        else:
            rows, cols = 15, 15

        return rows, cols, seed, k, ui, do_eval, export_path, not no_calibrate


    def main() -> None:
        rows, cols, seed, k, ui, do_eval, export_path, calibrate = parse_args(sys.argv[1:])

        if ui:
            run_tkinter_ui(rows, cols, seed, k)
            return

        if calibrate:
            maze, report = generate_normalized_maze(rows, cols, seed=seed, target_mean=k)
            if report:
                print(
                    f"Calibrated mean={report['mean']:.2f} std={report['std']:.2f} "
                    f"reach={report['reach_rate']:.2f} skew={report['skew']:.2f}"
                )
        else:
            coin_strategy, trap_strategy = make_normalized_strategies(k, spread=1.2)
            maze = Maze.generate(
                rows=rows,
                cols=cols,
                seed=seed,
                coin_strategy=coin_strategy,
                trap_strategy=trap_strategy,
            )

        maze.print()

        if export_path:
            out_path = export_maze_json(maze, export_path)
            print(f"Exported JSON to {out_path}")

        if do_eval:
            results = evaluate_distribution(maze)
            mean_score = sum(r.score for r in results) / len(results)
            print(f"Mean score: {mean_score:.3f}")


    if __name__ == "__main__":
        main()
            for nr, nc in self._room_neighbors(to_row, to_col):
