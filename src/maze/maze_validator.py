"""迷宫合法性验证。"""

from __future__ import annotations

from collections import deque

from src.maze.maze_metrics import normalize_grid, neighbors4, walkable_positions, compute_metrics
from src.utils.constants import START, END, BOSS, COIN, TRAP


def find_cells(grid: list[str] | list[list[str]], target: str) -> list[tuple[int, int]]:
    """查找所有指定符号格子。"""
    g = normalize_grid(grid)
    return [(r, c) for r, row in enumerate(g) for c, ch in enumerate(row) if ch == target]


def find_start_end(grid: list[str] | list[list[str]]) -> tuple[tuple[int, int] | None, tuple[int, int] | None]:
    """返回起点与终点。"""
    starts = find_cells(grid, START)
    ends = find_cells(grid, END)
    return (starts[0] if starts else None, ends[0] if ends else None)


def get_neighbors(grid: list[str] | list[list[str]], row: int, col: int) -> list[tuple[int, int]]:
    """返回可通行邻居。"""
    return neighbors4(normalize_grid(grid), row, col)


def is_reachable(
    grid: list[str] | list[list[str]],
    start: tuple[int, int] | None,
    end: tuple[int, int] | None,
) -> bool:
    """判断两个坐标是否可达。"""
    g = normalize_grid(grid)
    if start is None or end is None:
        return False
    q: deque[tuple[int, int]] = deque([start])
    seen = {start}
    while q:
        cur = q.popleft()
        if cur == end:
            return True
        for nxt in neighbors4(g, *cur):
            if nxt not in seen:
                seen.add(nxt)
                q.append(nxt)
    return False


def is_connected(grid: list[str] | list[list[str]]) -> bool:
    """判断所有非墙格子是否连通。"""
    g = normalize_grid(grid)
    cells = walkable_positions(g)
    if not cells:
        return False
    q: deque[tuple[int, int]] = deque([cells[0]])
    seen = {cells[0]}
    while q:
        cur = q.popleft()
        for nxt in neighbors4(g, *cur):
            if nxt not in seen:
                seen.add(nxt)
                q.append(nxt)
    return len(seen) == len(cells)


def is_perfect_maze(grid: list[str] | list[list[str]]) -> bool:
    """完美迷宫：非墙图连通且无环，即边数 = 点数 - 1。"""
    g = normalize_grid(grid)
    cells = walkable_positions(g)
    if not cells or not is_connected(g):
        return False
    edge_count = 0
    for r, c in cells:
        for nr, nc in neighbors4(g, r, c):
            if (nr, nc) > (r, c):
                edge_count += 1
    return edge_count == len(cells) - 1


def validate_maze(grid: list[str] | list[list[str]], require_boss: bool = False) -> dict:
    """综合验证迷宫合法性，并返回详细报告。"""
    g = normalize_grid(grid)
    n = len(g)
    size_ok = n >= 5 and all(len(row) == n for row in g)
    starts = find_cells(g, START)
    ends = find_cells(g, END)
    bosses = find_cells(g, BOSS)

    single_start = len(starts) == 1
    single_end = len(ends) == 1
    single_boss = len(bosses) == 1 if require_boss else len(bosses) <= 1

    start = starts[0] if starts else None
    end = ends[0] if ends else None

    start_to_end_reachable = is_reachable(g, start, end)
    all_paths_connected = is_connected(g)

    all_special_cells_reachable = True
    if start is None:
        all_special_cells_reachable = False
    else:
        for symbol in (COIN, TRAP, BOSS):
            for cell in find_cells(g, symbol):
                if not is_reachable(g, start, cell):
                    all_special_cells_reachable = False
                    break

    perfect = is_perfect_maze(g)
    metrics = compute_metrics(g)
    valid = all(
        [
            size_ok,
            single_start,
            single_end,
            single_boss,
            start_to_end_reachable,
            all_paths_connected,
            all_special_cells_reachable,
        ]
    )
    errors: list[str] = []
    if not size_ok:
        errors.append("尺寸必须为 n×n 且不小于 5")
    if not single_start:
        errors.append("起点 S 必须唯一")
    if not single_end:
        errors.append("终点 E 必须唯一")
    if not single_boss:
        errors.append("BOSS B 数量不符合要求")
    if not start_to_end_reachable:
        errors.append("S 到 E 不可达")
    if not all_paths_connected:
        errors.append("存在非墙格子不连通")
    if not all_special_cells_reachable:
        errors.append("存在金币/陷阱/BOSS 不可达")

    return {
        "valid": valid,
        "size_ok": size_ok,
        "single_start": single_start,
        "single_end": single_end,
        "single_boss": single_boss,
        "start_to_end_reachable": start_to_end_reachable,
        "all_paths_connected": all_paths_connected,
        "all_special_cells_reachable": all_special_cells_reachable,
        "is_perfect_maze": perfect,
        "path_cells": metrics["path_cells"],
        "wall_cells": metrics["wall_cells"],
        "dead_ends": metrics["dead_ends"],
        "branches": metrics["branches"],
        "message": "迷宫合法" if valid else "；".join(errors),
    }
