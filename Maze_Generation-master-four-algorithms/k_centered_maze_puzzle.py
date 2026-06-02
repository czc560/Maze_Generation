from __future__ import annotations

import argparse
import os
import random
import sys

ROOT = os.path.dirname(__file__)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from scripts.exporter import export_maze_json
from scripts.maze import Maze, normalize_generation_method
from scripts.strategies import evaluate_distribution, generate_normalized_maze, make_normalized_strategies
from scripts.ui import run_tkinter_ui


METHOD_HELP = "mst, backtracking, divide_conquer, branch_bound，也支持中文：最小生成树算法、回溯法、分治法、分支限界法"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="K-centered maze generator")
    parser.add_argument("rows", nargs="?", type=int, default=15, help="迷宫行数，默认 15")
    parser.add_argument("cols", nargs="?", type=int, default=None, help="迷宫列数，默认等于 rows")
    parser.add_argument("--seed", type=int, default=None, help="随机种子（不填则随机）")
    parser.add_argument("--k", type=float, default=4.0, help="目标分数中心")
    parser.add_argument("--method", default="mst", help=METHOD_HELP)
    parser.add_argument("--ui", action="store_true", help="启动 Tkinter 可视化界面")
    parser.add_argument("--eval", action="store_true", help="评估一组玩家的平均分")
    parser.add_argument("--export", default=None, help="导出 JSON 到指定路径")
    parser.add_argument("--no-calibrate", action="store_true", help="跳过分数分布校准，生成更快")
    args = parser.parse_args(argv)
    if args.cols is None:
        args.cols = args.rows
    args.method = normalize_generation_method(args.method)
    return args


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    if args.seed is None:
        args.seed = random.randint(0, 2**31 - 1)

    if args.ui:
        run_tkinter_ui(args.rows, args.cols, args.seed, args.k, generation_method=args.method)
        return

    if not args.no_calibrate:
        maze, report = generate_normalized_maze(
            args.rows,
            args.cols,
            seed=args.seed,
            target_mean=args.k,
            generation_method=args.method,
        )
        print(
            f"Calibrated method={args.method} mean={report['mean']:.2f} std={report['std']:.2f} "
            f"reach={report['reach_rate']:.2f} skew={report['skew']:.2f}"
        )
    else:
        coin_strategy, trap_strategy = make_normalized_strategies(args.k, spread=1.2)
        maze = Maze.generate(
            rows=args.rows,
            cols=args.cols,
            seed=args.seed,
            generation_method=args.method,
            coin_strategy=coin_strategy,
            trap_strategy=trap_strategy,
        )

    maze.print()

    if args.export:
        out_path = export_maze_json(maze, args.export)
        print(f"Exported JSON to {out_path}")

    if args.eval:
        results = evaluate_distribution(maze)
        mean_score = sum(r.score for r in results) / len(results)
        print(f"Mean score: {mean_score:.3f}")


if __name__ == "__main__":
    main()
