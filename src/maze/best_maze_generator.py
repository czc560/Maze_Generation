"""最佳迷宫生成器。"""

from __future__ import annotations

from pathlib import Path

from src.maze.maze_factory import generate_maze
from src.maze.resource_placer import place_resources
from src.maze.maze_metrics import compute_metrics
from src.resource.resource_optimizer import optimize_resource_path
from src.utils.json_io import save_json
from src.utils.path_utils import project_root


def _score_maze(maze, resource_result: dict, ai_result: dict | None = None) -> float:
    """综合路径长度、分支、死胡同、资源与 AI 表现进行评分。"""
    metrics = maze.metrics or compute_metrics(maze.grid)
    score = 0.0
    score += metrics.get("shortest_path_length", 0) * 2.0
    score += metrics.get("dead_ends", 0) * 2.5
    score += metrics.get("branches", 0) * 4.0
    score += resource_result.get("max_resource", 0) * 0.6
    score += metrics.get("coins", 0) * 5.0
    score += metrics.get("traps", 0) * 3.0
    if maze.validation.get("valid"):
        score += 100
    if ai_result:
        score += ai_result.get("score", 0) * 0.2
        if ai_result.get("victory"):
            score += 40
    if maze.algorithm in {"dfs", "prim", "kruskal"} and maze.validation.get("is_perfect_maze"):
        score += 20
    return score


def generate_best_maze(
    size: int = 15,
    seed: int | None = 42,
    candidates_per_algorithm: int = 3,
) -> dict:
    """生成多个候选迷宫，选择评分最高者并保存 JSON。"""
    algorithms = ["dfs", "prim", "kruskal", "division", "bfs_optimize"]
    best_record: dict | None = None
    candidates: list[dict] = []

    for alg_index, algorithm in enumerate(algorithms):
        for i in range(candidates_per_algorithm):
            candidate_seed = None if seed is None else seed + alg_index * 100 + i
            maze = generate_maze(size, algorithm, candidate_seed)
            maze = place_resources(maze, coin_count=8, trap_count=6, place_boss=True, seed=candidate_seed)
            if not maze.validation.get("valid"):
                continue
            resource_result = optimize_resource_path(maze.grid)
            ai_result = None
            try:
                from src.ai.ai_player import run_ai_on_maze
                ai_result = run_ai_on_maze(maze, ai="greedy", max_steps=size * size * 3)
            except Exception as exc:
                ai_result = {"error": str(exc), "score": 0, "victory": False}
            score = _score_maze(maze, resource_result, ai_result)
            record = {
                "score": score,
                "maze": maze.to_dict(),
                "resource_result": resource_result,
                "ai_result": ai_result,
                "algorithm": algorithm,
                "seed": candidate_seed,
            }
            candidates.append(record)
            if best_record is None or score > best_record["score"]:
                best_record = record

    if best_record is None:
        raise RuntimeError("未能生成合法候选迷宫")

    result = {
        "best_score": best_record["score"],
        "best_maze": best_record["maze"],
        "resource_result": best_record["resource_result"],
        "ai_result": best_record["ai_result"],
        "candidate_count": len(candidates),
        "candidates": [
            {
                "score": round(c["score"], 3),
                "algorithm": c["algorithm"],
                "seed": c["seed"],
                "metrics": c["maze"].get("metrics", {}),
            }
            for c in candidates
        ],
    }

    base = project_root()
    save_json(best_record["maze"], base / "data" / "best_maze.json")
    save_json(best_record["maze"], base / "outputs" / "generated_mazes" / "best_maze.json")
    save_json(result, base / "outputs" / "logs" / "best_maze_selection.json")
    return result
