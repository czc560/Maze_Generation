"""迷宫统一生成入口。"""

from __future__ import annotations

from src.maze.dfs_generator import generate_dfs_maze
from src.maze.prim_generator import generate_prim_maze
from src.maze.kruskal_generator import generate_kruskal_maze
from src.maze.division_generator import generate_division_maze
from src.maze.bfs_optimizer import optimize_maze_by_bfs_branch_bound
from src.utils.constants import normalize_size


def generate_maze(size: int, algorithm: str, seed: int | None = None):
    """统一迷宫生成接口。"""
    size = normalize_size(size)
    algorithm = algorithm.lower()
    if algorithm == "dfs":
        return generate_dfs_maze(size, seed)
    if algorithm == "prim":
        return generate_prim_maze(size, seed)
    if algorithm == "kruskal":
        return generate_kruskal_maze(size, seed)
    if algorithm == "division":
        return generate_division_maze(size, seed)
    if algorithm == "bfs_optimize":
        base = generate_dfs_maze(size, seed)
        return optimize_maze_by_bfs_branch_bound(base, seed)
    raise ValueError(f"不支持的迷宫算法: {algorithm}")
