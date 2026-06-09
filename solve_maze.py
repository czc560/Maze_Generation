#!/usr/bin/env python3
"""最优资源收集路径 — 验收用 CLI 工具

用法::

    # 求解迷宫
    python solve_maze.py maze.json
    python solve_maze.py maze.json --out result.json
    python solve_maze.py test1.json test2.json --out-dir results/

    # 生成迷宫
    python solve_maze.py --generate 15 15 --seed 42 --out maze.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from game.maze.optimal_path import (
    compute_optimal_path,
    verify_path,
    load_maze_from_json,
    export_result,
    export_game_maze_json,
    game_maze_to_grid,
)


def solve_one(path: str, out_path: str | None = None, require_end: bool = False) -> int:
    """Solve a single maze JSON file.  Returns 0 on success, 1 on failure."""
    print(f"── 求解: {path} ──")

    try:
        maze = load_maze_from_json(path)
    except Exception as e:
        print(f"  ❌ 加载失败: {e}")
        return 1

    print(f"  迷宫: {maze.rows}×{maze.cols}  "
          f"可走格={sum(1 for r in range(maze.rows) for c in range(maze.cols) if maze.grid[r][c].walkable)}")

    try:
        result = compute_optimal_path(maze, require_end=require_end)  # type: ignore[arg-type]
    except Exception as e:
        print(f"  ❌ 求解失败: {e}")
        return 1

    report = verify_path(maze, result.path, require_end=require_end)  # type: ignore[arg-type]

    if not report["legal"]:
        print("  ❌ 路径不合法!")
        for err in report["errors"]:
            print(f"      - {err}")
        return 1

    if report["resource"] != result.max_resource:
        print(f"  ⚠  回放资源 ({report['resource']}) ≠ DP结果 ({result.max_resource})")
        return 1

    print(f"  最优资源: {result.max_resource}")
    print(f"  金币: {result.coins_in_path}  陷阱: {result.traps_in_path}  "
          f"步数: {len(result.path)-1}")
    print(f"  自检: ✅ 合法  回放={report['resource']}  DP={result.max_resource}  "
          f"最优={result.is_optimal}")
    if result.note:
        print(f"  备注: {result.note}")

    # Path output
    path_json = json.dumps([[r, c] for r, c in result.path], ensure_ascii=False)
    print(f"  路径 path_rc ({len(result.path)} 步, 含 S→E):")
    print(f"  {path_json}")

    if out_path:
        export_result(maze, result, out_path)  # type: ignore[arg-type]
        print(f"  → 已写入: {os.path.abspath(out_path)}")

    return 0


def cmd_generate(args) -> int:
    """Generate a random maze and export as JSON."""
    from game.maze.generator import Maze
    from game.maze.strategies import make_normalized_strategies
    from game.maze import SYMBOLS

    rows, cols = args.generate_rows, args.generate_cols
    seed = args.seed
    k = args.k

    cs, ts = make_normalized_strategies(k, spread=1.2)
    maze = Maze.generate(
        rows=rows, cols=cols, seed=seed,
        generation_method=args.method,
        coin_strategy=cs, trap_strategy=ts,
    )

    out = args.out
    if out is None:
        out = f"maze_{rows}_{cols}_seed{seed}.json"

    path = export_game_maze_json(maze, out)
    print(f"迷宫已生成: {rows}×{cols}  seed={seed}  k={k}  算法={args.method}")
    print(f"  起点: {list(maze.start)}  终点: {list(maze.end)}")
    print(f"  Boss: {list(maze.boss) if maze.boss else None}")
    coins = sum(1 for r in range(rows) for c in range(cols)
                if maze.grid[r][c].content == SYMBOLS["coin"])
    traps = sum(1 for r in range(rows) for c in range(cols)
                if maze.grid[r][c].content == SYMBOLS["trap"])
    print(f"  金币: {coins}  陷阱: {traps}")
    print(f"  → {path}")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(
        description="最优资源收集路径求解器 — 迷宫设计任务 ② 验收用"
    )
    ap.add_argument("maze_files", nargs="*", help="迷宫 JSON 文件（求解模式）")
    ap.add_argument("--out", default=None, metavar="PATH", help="输出 JSON 路径")
    ap.add_argument("--out-dir", default=None, metavar="DIR", help="批量输出目录")
    ap.add_argument("--require-end", action="store_true", help="要求路径从 S 出发、在 E 结束")

    # Generate mode
    ap.add_argument("--generate", nargs=2, metavar=("ROWS", "COLS"), type=int,
                    help="生成随机迷宫并导出 JSON（不求解）")
    ap.add_argument("--seed", type=int, default=42, help="随机种子 (default: 42)")
    ap.add_argument("--k", type=float, default=4.0, help="目标分数均值 (default: 4.0)")
    ap.add_argument("--method", default="mst",
                    choices=["mst", "backtracking", "divide_conquer", "branch_bound"],
                    help="生成算法 (default: mst)")

    args = ap.parse_args()

    # ---- Generate mode ----
    if args.generate is not None:
        args.generate_rows, args.generate_cols = args.generate
        rc = cmd_generate(args)
        sys.exit(rc)

    # ---- Solve mode ----
    if not args.maze_files:
        ap.print_help()
        sys.exit(1)

    require_end = args.require_end
    files = args.maze_files
    failed = 0

    for i, fp in enumerate(files):
        if args.out and len(files) == 1:
            out = args.out
        elif args.out_dir:
            base = os.path.splitext(os.path.basename(fp))[0]
            out = os.path.join(args.out_dir, f"{base}_solution.json")
        else:
            out = None
        if failed > 0:
            print()
        rc = solve_one(fp, out, require_end)
        if rc != 0:
            failed += 1

    print(f"\n{'='*50}")
    print(f"完成: {len(files)} 个, {len(files)-failed} 成功, {failed} 失败")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
