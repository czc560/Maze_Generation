#!/usr/bin/env python3
"""最优资源收集路径 — 验收用 CLI 工具

用法::

    # 求解迷宫
    python solve_maze.py maze.json
    python solve_maze.py maze.json --out result.json
    python solve_maze.py test1.json test2.json --out-dir results/

    # 生成迷宫
    python solve_maze.py --generate 15 15 --seed 42 --out maze.json

    # 检查 Boss 战技能序列最优性
    python solve_maze.py --check-sequence input.json
    python solve_maze.py --check-sequence input.json --out result.json

    # 给定 B + PlayerSkills, 输出最优 SkillSequence
    python solve_maze.py --optimal-sequence input.json
    python solve_maze.py --optimal-sequence input.json --out output.json
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
from game.battle.rules import check_sequence_optimality, _optimal_skill_dp_continuous


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


def cmd_check_sequence(args) -> int:
    """Check whether a skill sequence is the minimum-turn optimal sequence.

    Input JSON format::

        {"B":[20,35],"PlayerSkills":[[5,0],[10,2]],"SkillSequence":[1,0,0,1,0,0]}

    Returns 0 if optimal, 1 if not optimal or illegal.
    """
    path: str = args.check_sequence
    print(f"── 检查序列最优性: {path} ──")

    # Load
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"  ❌ 加载失败: {e}")
        return 1

    # Validate required fields
    for key in ("B", "PlayerSkills", "SkillSequence"):
        if key not in data:
            print(f"  ❌ 缺少字段: {key}")
            return 1

    B: list[int] = data["B"]
    PlayerSkills: list[list[int]] = data["PlayerSkills"]
    SkillSequence: list[int] = data["SkillSequence"]

    # Run check
    result = check_sequence_optimality(B, PlayerSkills, SkillSequence)

    # Print
    print(f"  Boss数: {result['bosses_total']}  击败: {result['bosses_defeated']}")
    print(f"  使用回合: {result['turns_used']}  理论最优: {result['optimal_turns']}")
    print(f"  合法: {'✅' if result['legal'] else '❌'}  "
          f"最优: {'✅' if result['is_optimal'] else '❌'}")
    if result["errors"]:
        for err in result["errors"]:
            print(f"    ⚠ {err}")

    for d in result.get("boss_details", []):
        status = "✅ 击败" if d["defeated"] else "❌ 未击败"
        opt = d.get("optimal_turns", "?")
        opt_seq = d.get("optimal_sequence", [])
        print(f"  Boss#{d['boss_index']+1} HP={d['hp']}  "
              f"实际={d['turns']}回合  最优={opt}回合  {status}")
        if opt_seq:
            print(f"    最优序列: {opt_seq}")

    if result.get("optimal_sequence"):
        print(f"  参考最优序列 (全部): {result['optimal_sequence']}")

    # Export
    if args.out:
        out_path = args.out
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"  → 已写入: {os.path.abspath(out_path)}")

    return 0 if result["is_optimal"] else 1


def cmd_optimal_sequence(args) -> int:
    """Given B and PlayerSkills, compute and output the optimal SkillSequence.

    Input JSON format::

        {"B":[20,35],"PlayerSkills":[[5,0],[10,2]]}

    Output: the same dict with ``SkillSequence`` inserted.
    """
    path: str = args.optimal_sequence
    print(f"── 计算最优序列: {path} ──")

    # Load
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"  ❌ 加载失败: {e}")
        return 1

    # Validate
    for key in ("B", "PlayerSkills"):
        if key not in data:
            print(f"  ❌ 缺少字段: {key}")
            return 1

    B: list[int] = data["B"]
    PlayerSkills: list[list[int]] = data["PlayerSkills"]

    # Compute optimal
    opt_seq = _optimal_skill_dp_continuous(B, PlayerSkills)

    # Build output
    out_data = {"B": B, "PlayerSkills": PlayerSkills, "SkillSequence": opt_seq}

    print(f"  Boss数: {len(B)}  最优回合: {len(opt_seq)}")
    print(f"  序列: {opt_seq}")

    # Validate legality
    from game.battle.rules import simulate_skill_sequence
    sim = simulate_skill_sequence(B, PlayerSkills, opt_seq)
    print(f"  自检: legal={sim['legal']}  damage={sim['total_damage_dealt']}  "
          f"击败={sim['bosses_defeated']}/{sim['bosses_total']}")

    # Export
    out_path = args.out
    if out_path is None:
        out_path = os.path.splitext(path)[0] + "_optimal.json"

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_data, f, ensure_ascii=False, indent=2)
    print(f"  → 已写入: {os.path.abspath(out_path)}")

    # Also print raw JSON to stdout for piping
    print(json.dumps(out_data, ensure_ascii=False))

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

    # Sequence check mode
    ap.add_argument("--check-sequence", default=None, metavar="FILE",
                    help="检查技能序列是否为最优 (BOSS 战)")

    # Optimal sequence compute mode
    ap.add_argument("--optimal-sequence", default=None, metavar="FILE",
                    help="输入 B + PlayerSkills, 输出最优 SkillSequence")

    args = ap.parse_args()

    # ---- Generate mode ----
    if args.generate is not None:
        args.generate_rows, args.generate_cols = args.generate
        rc = cmd_generate(args)
        sys.exit(rc)

    # ---- Sequence check mode ----
    if args.check_sequence is not None:
        rc = cmd_check_sequence(args)
        sys.exit(rc)

    # ---- Optimal sequence compute mode ----
    if args.optimal_sequence is not None:
        rc = cmd_optimal_sequence(args)
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
