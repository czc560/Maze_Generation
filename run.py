"""命令行入口。"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ai.ai_player import run_ai_on_maze
from src.boss.boss_branch_bound import solve_boss_battle
from src.maze.best_maze_generator import generate_best_maze
from src.maze.maze import Maze
from src.maze.maze_factory import generate_maze
from src.maze.resource_placer import place_resources
from src.resource.resource_optimizer import optimize_resource_path
from src.utils.json_io import load_json, save_json
from src.utils.path_utils import ensure_project_dirs
from src.visualization.maze_visualizer import (
    draw_maze,
    draw_maze_comparison,
    draw_metric_comparison,
    draw_runtime_comparison,
)
from src.visualization.resource_visualizer import draw_resource_path
from src.visualization.boss_visualizer import draw_boss_timeline
from src.visualization.ai_visualizer import draw_ai_path


ALGORITHMS = ["dfs", "prim", "kruskal", "division", "bfs_optimize"]


def load_maze(path: str | Path) -> Maze:
    """读取迷宫 JSON。"""
    data = load_json(path)
    if "best_maze" in data:
        data = data["best_maze"]
    return Maze.from_dict(data)


def boss_config_default() -> dict:
    """默认 BOSS 配置。"""
    return {
        "B": [11, 13, 9, 15],
        "BossAbilities": [
            {"name": "重击", "damage": 8, "cooldown": 3},
            {"name": "护盾", "shield": 5, "cooldown": 4},
        ],
        "PlayerSkills": [
            {"name": "普通攻击", "damage": 2, "cooldown": 0, "cost": 0},
            {"name": "火球术", "damage": 8, "cooldown": 4, "cost": 2},
            {"name": "连击", "damage": 4, "cooldown": 2, "cost": 1},
            {"name": "斩击", "damage": 6, "cooldown": 3, "cost": 1},
        ],
        "minRouds": 20,
        "CoinConsumption": 5,
        "PlayerCoin": 30,
        "PlayerHP": 100,
    }


def generate_and_save(args) -> dict:
    """生成指定算法迷宫并保存。"""
    paths = ensure_project_dirs(PROJECT_ROOT)
    maze = generate_maze(args.size, args.algorithm, args.seed)
    maze = place_resources(maze, args.coins, args.traps, True, args.seed)
    out = paths["generated_mazes"] / f"maze_{args.algorithm}_{maze.size}_seed{args.seed}.json"
    maze.save_json(out)
    fig = paths["figures"] / f"maze_{args.algorithm}_{maze.size}_seed{args.seed}.png"
    draw_maze(maze.grid, f"{args.algorithm.upper()} Maze", fig)
    print(f"已生成: {out}")
    print(f"已保存图片: {fig}")
    print("验证:", maze.validation["message"])
    return maze.to_dict()


def compare_algorithms(args) -> list[dict]:
    """生成并比较五种算法。"""
    paths = ensure_project_dirs(PROJECT_ROOT)
    results = []
    metrics = []
    for algorithm in ALGORITHMS:
        maze = generate_maze(args.size, algorithm, args.seed)
        maze = place_resources(maze, args.coins, args.traps, True, args.seed)
        out = paths["generated_mazes"] / f"maze_{algorithm}_{maze.size}_seed{args.seed}.json"
        maze.save_json(out)
        metric = {
            "algorithm": algorithm,
            **maze.metrics,
            "runtime_seconds": maze.metadata.get("runtime_seconds", 0),
            "valid": maze.validation.get("valid", False),
            "perfect": maze.validation.get("is_perfect_maze", False),
        }
        metrics.append(metric)
        results.append({"algorithm": algorithm, "score": metric["shortest_path_length"] + metric["branches"] * 3, "metrics": metric})
    draw_maze_comparison(results, paths["figures"] / "maze_algorithm_comparison.png")
    draw_runtime_comparison(metrics, paths["figures"] / "runtime_comparison.png")
    draw_metric_comparison(metrics, paths["figures"] / "metric_comparison.png")
    save_json(metrics, paths["logs"] / "algorithm_comparison.json")
    print("算法对比:")
    for m in metrics:
        print(f"{m['algorithm']:12s} valid={m['valid']} perfect={m['perfect']} path={m['shortest_path_length']} branches={m['branches']} dead_ends={m['dead_ends']}")
    return metrics


def run_resource(path: str | Path) -> dict:
    """执行资源路径优化。"""
    paths = ensure_project_dirs(PROJECT_ROOT)
    maze = load_maze(path)
    result = optimize_resource_path(maze.grid)
    save_json(result, paths["logs"] / "resource_result.json")
    draw_resource_path(maze.grid, result["path"], "Optimal Resource Path", paths["figures"] / "resource_path.png")
    print("最大资源值:", result["max_resource"])
    print("路径长度:", result["path_length"])
    return result


def run_boss(path: str | Path | None = None) -> dict:
    """求解 BOSS 战。"""
    paths = ensure_project_dirs(PROJECT_ROOT)
    config = load_json(path) if path else boss_config_default()
    result = solve_boss_battle(config)
    save_json(result, paths["logs"] / "boss_result.json")
    draw_boss_timeline(result, paths["figures"] / "boss_timeline.png")
    print("BOSS 最少回合:", result.get("min_rounds"))
    print("是否满足限制:", result.get("success_within_limit"))
    return result


def run_ai(args) -> dict:
    """运行 AI 玩家。"""
    paths = ensure_project_dirs(PROJECT_ROOT)
    maze_path = args.maze or (PROJECT_ROOT / "data" / "best_maze.json")
    maze = load_maze(maze_path)
    result = run_ai_on_maze(maze, ai=args.ai, custom_strategy=args.custom_strategy, max_steps=args.size * args.size * 4)
    out = paths["ai_runs"] / f"ai_{args.ai}_result.json"
    save_json(result, out)
    draw_ai_path(maze.grid, result["path"], paths["figures"] / f"ai_{args.ai}_path.png")
    print(f"AI 结果已保存: {out}")
    print(f"胜利={result['victory']} 步数={result['steps']} 分数={result['score']}")
    return result


def run_all(args) -> dict:
    """一键完成课程展示流程。"""
    paths = ensure_project_dirs(PROJECT_ROOT)
    comparison = compare_algorithms(args)
    best = generate_best_maze(args.size, args.seed, candidates_per_algorithm=2)
    best_maze = Maze.from_dict(best["best_maze"])
    resource_result = optimize_resource_path(best_maze.grid)
    save_json(resource_result, paths["logs"] / "resource_result.json")
    draw_resource_path(best_maze.grid, resource_result["path"], "Best Maze Resource Path", paths["figures"] / "best_resource_path.png")

    boss_cfg_path = PROJECT_ROOT / "data" / "boss_config.json"
    boss_cfg = load_json(boss_cfg_path) if boss_cfg_path.exists() else boss_config_default()
    boss_result = solve_boss_battle(boss_cfg)
    save_json(boss_result, paths["logs"] / "boss_result.json")
    draw_boss_timeline(boss_result, paths["figures"] / "boss_timeline.png")

    ai_results = {}
    for ai in ["greedy", "ppo", "qlearning"]:
        try:
            result = run_ai_on_maze(best_maze, ai=ai, max_steps=args.size * args.size * 4, boss_config=boss_cfg)
            ai_results[ai] = result
            save_json(result, paths["ai_runs"] / f"ai_{ai}_result.json")
        except Exception as exc:
            ai_results[ai] = {"error": str(exc)}

    summary = {
        "comparison": comparison,
        "best": best,
        "resource_result": resource_result,
        "boss_result": boss_result,
        "ai_results": ai_results,
    }
    save_json(summary, paths["logs"] / "result_summary.json")
    print("一键流程完成，摘要已保存到 outputs/logs/result_summary.json")
    return summary


def parse_args():
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(description="AI 竞技迷宫设计与 AI 玩家挑战系统")
    parser.add_argument("--algorithm", choices=ALGORITHMS, help="生成迷宫算法")
    parser.add_argument("--size", type=int, default=15, help="迷宫尺寸")
    parser.add_argument("--seed", type=int, default=42, help="随机种子")
    parser.add_argument("--coins", type=int, default=10, help="金币数量")
    parser.add_argument("--traps", type=int, default=8, help="陷阱数量")
    parser.add_argument("--compare", action="store_true", help="比较五种算法")
    parser.add_argument("--resource", help="资源路径优化：传入迷宫 JSON")
    parser.add_argument("--boss", nargs="?", const=str(PROJECT_ROOT / "data" / "boss_config.json"), help="BOSS 战求解：可传入配置 JSON")
    parser.add_argument("--best", action="store_true", help="生成最佳迷宫")
    parser.add_argument("--ai", default=None, help="运行 AI：greedy/ppo/qlearning/custom")
    parser.add_argument("--maze", help="AI 或资源模式使用的迷宫 JSON")
    parser.add_argument("--play", action="store_true", help="启动 pygame，并使用指定 AI 自动游玩")
    parser.add_argument("--custom-strategy", help="自定义策略 Python 文件")
    parser.add_argument("--game", action="store_true", help="启动 pygame 游戏界面")
    parser.add_argument("--all", action="store_true", help="一键完成全部流程")
    return parser.parse_args()


def main():
    args = parse_args()
    ensure_project_dirs(PROJECT_ROOT)

    if args.all:
        run_all(args)
        return

    if args.game or args.play:
        from src.ui.game_app import MazeGameApp
        MazeGameApp(size=args.size, algorithm=args.algorithm or "dfs", seed=args.seed, ai=args.ai or "greedy").run()
        return

    if args.compare:
        compare_algorithms(args)

    if args.algorithm:
        generate_and_save(args)

    if args.best:
        result = generate_best_maze(args.size, args.seed)
        print("最佳迷宫得分:", result["best_score"])

    if args.resource:
        run_resource(args.resource)

    if args.boss:
        run_boss(args.boss)

    if args.ai:
        run_ai(args)

    if not any([args.compare, args.algorithm, args.best, args.resource, args.boss, args.ai]):
        print("未指定任务。示例: python run.py --all --size 15 --seed 42")


if __name__ == "__main__":
    main()
