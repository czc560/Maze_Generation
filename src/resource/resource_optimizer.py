"""最优资源收集路径搜索。"""

from __future__ import annotations

from collections import deque
from math import inf

from src.maze.maze_metrics import normalize_grid, neighbors4, shortest_path
from src.maze.maze_validator import find_start_end
from src.utils.constants import COIN, TRAP, RESOURCE_VALUES


def _resource_positions(grid: list[list[str]]) -> list[tuple[int, int]]:
    """返回所有资源坐标，金币优先、陷阱按需纳入。"""
    coins = [(r, c) for r, row in enumerate(grid) for c, ch in enumerate(row) if ch == COIN]
    traps = [(r, c) for r, row in enumerate(grid) for c, ch in enumerate(row) if ch == TRAP]
    return coins + traps


def _compress_resources(resources: list[tuple[int, int]], limit: int = 16) -> list[tuple[int, int]]:
    """限制精确状态空间规模，保证课程演示可运行。"""
    return resources[:limit]


def optimize_resource_path(grid: list[str] | list[list[str]]) -> dict:
    """从 S 到 E 搜索最大资源收益路径。"""
    g = normalize_grid(grid)
    start, end = find_start_end(g)
    if start is None or end is None:
        return {
            "max_resource": 0,
            "path": [],
            "coins_collected": 0,
            "traps_triggered": 0,
            "path_length": 0,
            "visited_states": 0,
            "process": [{"error": "缺少 S 或 E"}],
        }

    resources_all = _resource_positions(g)
    resources = _compress_resources(resources_all)
    res_index = {pos: i for i, pos in enumerate(resources)}
    res_value = {pos: RESOURCE_VALUES.get(g[pos[0]][pos[1]], 0) for pos in resources}

    start_key = (start, 0)
    best: dict[tuple[tuple[int, int], int], tuple[int, int]] = {start_key: (0, 0)}
    parent: dict[tuple[tuple[int, int], int], tuple[tuple[tuple[int, int], int], tuple[int, int]]] = {}
    q: deque[tuple[tuple[int, int], int]] = deque([start_key])
    best_end_key: tuple[tuple[int, int], int] | None = None
    best_end_score = -inf
    best_end_len = inf
    visited_states = 0
    max_states = 240000
    process: list[dict] = []

    while q and visited_states < max_states:
        pos, mask = q.popleft()
        score, length = best[(pos, mask)]
        visited_states += 1

        if pos == end and (score > best_end_score or (score == best_end_score and length < best_end_len)):
            best_end_key = (pos, mask)
            best_end_score = score
            best_end_len = length
            if len(process) < 80:
                process.append({"reach_E": [pos[0], pos[1]], "score": score, "length": length})

        for nxt in neighbors4(g, *pos):
            nmask = mask
            nscore = score
            if nxt in res_index:
                bit = 1 << res_index[nxt]
                if not (mask & bit):
                    nmask |= bit
                    nscore += res_value[nxt]
            nlen = length + 1
            key = (nxt, nmask)
            old = best.get(key)
            if old is None or nscore > old[0] or (nscore == old[0] and nlen < old[1]):
                best[key] = (nscore, nlen)
                parent[key] = ((pos, mask), nxt)
                q.append(key)

    if best_end_key is None:
        path = shortest_path(g, start, end)
    else:
        rev: list[tuple[int, int]] = []
        cur = best_end_key
        rev.append(cur[0])
        while cur != start_key:
            prev, _step = parent[cur]
            cur = prev
            rev.append(cur[0])
        path = list(reversed(rev))

    seen_coin: set[tuple[int, int]] = set()
    seen_trap: set[tuple[int, int]] = set()
    for pos in path:
        ch = g[pos[0]][pos[1]]
        if ch == COIN:
            seen_coin.add(pos)
        elif ch == TRAP:
            seen_trap.add(pos)

    max_resource = len(seen_coin) * 50 - len(seen_trap) * 30
    return {
        "max_resource": max_resource,
        "path": [[r, c] for r, c in path],
        "coins_collected": len(seen_coin),
        "traps_triggered": len(seen_trap),
        "path_length": max(0, len(path) - 1),
        "visited_states": visited_states,
        "resource_state_limit": len(resources),
        "total_resource_cells": len(resources_all),
        "process": process,
        "visualization": {
            "path_cells": [[r, c] for r, c in path],
            "coins": [[r, c] for r, c in seen_coin],
            "traps": [[r, c] for r, c in seen_trap],
        },
    }
