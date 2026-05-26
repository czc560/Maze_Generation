"""Kruskal 迷宫生成器。"""

from __future__ import annotations

import random
import time

from src.maze.generator_base import wall_grid, record_step, finalize_maze
from src.utils.constants import ROAD, normalize_size


class UnionFind:
    """并查集，用于 Kruskal 迷宫生成。"""

    def __init__(self, items):
        self.parent = {item: item for item in items}
        self.rank = {item: 0 for item in items}

    def find(self, item):
        """查找根节点。"""
        if self.parent[item] != item:
            self.parent[item] = self.find(self.parent[item])
        return self.parent[item]

    def union(self, a, b) -> bool:
        """合并两个集合，成功合并返回 True。"""
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1
        return True


def generate_kruskal_maze(size: int, seed: int | None = None):
    """使用 Kruskal 算法生成树型完美迷宫。"""
    start_time = time.perf_counter()
    rng = random.Random(seed)
    size = normalize_size(size)
    grid = wall_grid(size)
    steps: list[list[list[str]]] = []

    nodes = [(r, c) for r in range(1, size - 1, 2) for c in range(1, size - 1, 2)]
    for r, c in nodes:
        grid[r][c] = ROAD

    edges: list[tuple[tuple[int, int], tuple[int, int], tuple[int, int]]] = []
    node_set = set(nodes)
    for r, c in nodes:
        for dr, dc in [(2, 0), (0, 2)]:
            nr, nc = r + dr, c + dc
            if (nr, nc) in node_set:
                edges.append(((r, c), (nr, nc), ((r + nr) // 2, (c + nc) // 2)))
    rng.shuffle(edges)
    uf = UnionFind(nodes)
    record_step(steps, grid)

    carved_edges = 0
    for a, b, wall in edges:
        if uf.union(a, b):
            wr, wc = wall
            grid[wr][wc] = ROAD
            carved_edges += 1
            record_step(steps, grid)

    return finalize_maze(grid, "kruskal", seed, steps, start_time, {"carved_edges": carved_edges})
