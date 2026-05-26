"""迷宫指标与路径工具。"""

from __future__ import annotations

from collections import deque
from typing import Iterable

from src.utils.constants import WALL, CARDINAL_DIRS, COIN, TRAP, BOSS


def normalize_grid(grid: list[str] | list[list[str]]) -> list[list[str]]:
    """统一迷宫矩阵格式。"""
    if not grid:
        return []
    if isinstance(grid[0], str):
        return [list(row) for row in grid]  # type: ignore[arg-type]
    return [list(row) for row in grid]  # type: ignore[arg-type]


def in_bounds(grid: list[list[str]], r: int, c: int) -> bool:
    return 0 <= r < len(grid) and 0 <= c < len(grid[0])


def is_walkable_cell(ch: str) -> bool:
    return ch != WALL


def walkable_positions(grid: list[list[str]]) -> list[tuple[int, int]]:
    """返回所有非墙格子坐标。"""
    return [(r, c) for r, row in enumerate(grid) for c, ch in enumerate(row) if is_walkable_cell(ch)]


def neighbors4(grid: list[list[str]], r: int, c: int, avoid_traps: bool = False) -> list[tuple[int, int]]:
    """返回四邻接可通行坐标。"""
    out: list[tuple[int, int]] = []
    for dr, dc in CARDINAL_DIRS:
        nr, nc = r + dr, c + dc
        if in_bounds(grid, nr, nc) and grid[nr][nc] != WALL:
            if avoid_traps and grid[nr][nc] == TRAP:
                continue
            out.append((nr, nc))
    return out


def find_first(grid: list[list[str]], targets: Iterable[str]) -> tuple[int, int] | None:
    """查找第一个目标格子。"""
    targets = set(targets)
    for r, row in enumerate(grid):
        for c, ch in enumerate(row):
            if ch in targets:
                return (r, c)
    return None


def shortest_path(
    grid: list[str] | list[list[str]],
    start: tuple[int, int] | None = None,
    end: tuple[int, int] | None = None,
    avoid_traps: bool = False,
) -> list[tuple[int, int]]:
    """BFS 最短路径；找不到时返回空列表。"""
    g = normalize_grid(grid)
    if not g:
        return []
    start = start or find_first(g, {"S"})
    end = end or find_first(g, {"E"})
    if start is None or end is None:
        return []

    q: deque[tuple[int, int]] = deque([start])
    parent: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    while q:
        cur = q.popleft()
        if cur == end:
            break
        for nxt in neighbors4(g, *cur, avoid_traps=avoid_traps):
            if nxt not in parent:
                parent[nxt] = cur
                q.append(nxt)

    if end not in parent:
        if avoid_traps:
            return shortest_path(g, start, end, avoid_traps=False)
        return []

    path: list[tuple[int, int]] = []
    cur: tuple[int, int] | None = end
    while cur is not None:
        path.append(cur)
        cur = parent[cur]
    path.reverse()
    return path


def cell_degrees(grid: list[str] | list[list[str]]) -> dict[tuple[int, int], int]:
    """统计每个非墙格子的图度数。"""
    g = normalize_grid(grid)
    return {pos: len(neighbors4(g, *pos)) for pos in walkable_positions(g)}


def compute_metrics(grid: list[str] | list[list[str]]) -> dict:
    """计算墙数、通路数、死胡同数、分支数、资源数等指标。"""
    g = normalize_grid(grid)
    degrees = cell_degrees(g)
    path_cells = sum(1 for row in g for ch in row if ch != WALL)
    wall_cells = sum(1 for row in g for ch in row if ch == WALL)
    dead_ends = sum(1 for d in degrees.values() if d == 1)
    branches = sum(1 for d in degrees.values() if d >= 3)
    sp = shortest_path(g)
    return {
        "path_cells": path_cells,
        "wall_cells": wall_cells,
        "dead_ends": dead_ends,
        "branches": branches,
        "coins": sum(row.count(COIN) for row in g),
        "traps": sum(row.count(TRAP) for row in g),
        "bosses": sum(row.count(BOSS) for row in g),
        "shortest_path_length": max(0, len(sp) - 1),
        "grid_size": len(g),
    }
