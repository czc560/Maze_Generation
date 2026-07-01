"""Pathfinding AIs — 3×3 visible input only. No global map."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional

from game.maze.symbols import SYMBOLS, COIN_VALUE, TRAP_VALUE
from game.maze.pathfinding import bfs_path, distance_to_end_map


@dataclass
class ProbeState:
    position: tuple[int, int]
    steps: int
    resources: int


def _scan_visible(maze, pos, collected_coins, triggered_traps) -> dict:
    """Scan 3×3 around *pos*. Returns {'coins':set, 'traps':set, 'end':bool}."""
    pr, pc = pos
    result = {'coins': set(), 'traps': set(), 'end': False}
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            nr, nc = pr + dr, pc + dc
            if not (0 <= nr < maze.rows and 0 <= nc < maze.cols):
                continue
            if not maze.grid[nr][nc].walkable:
                continue
            ct = maze.grid[nr][nc].content
            if ct == SYMBOLS["coin"] and (nr, nc) not in collected_coins:
                result['coins'].add((nr, nc))
            elif ct == SYMBOLS["trap"] and (nr, nc) not in triggered_traps:
                result['traps'].add((nr, nc))
            elif ct == SYMBOLS["end"]:
                result['end'] = True
    return result


# ============================================================================
#  SimpleGreedy — no memory, pure greed
# ============================================================================

class SimpleGreedy:
    """Pure greedy AI. 3×3 visible area. No visited memory. No global map.

    Scoring per neighbor:
      - distance to visible coins/traps (weighted)
      - progress toward end
    """

    def __init__(self, maze, coin_weight=1.2, trap_weight=0.8, end_weight=1.6, seed=None):
        if maze.start is None or maze.end is None:
            raise ValueError("Maze needs start/end")
        self.maze = maze
        self.coin_weight = coin_weight
        self.trap_weight = trap_weight
        self.end_weight = end_weight
        self.rng = random.Random(seed)

        self.position = maze.start
        self.steps = 0
        self.resources = 0
        self.collected_coins: set = set()
        self.triggered_traps: set = set()
        self.dist_to_end = distance_to_end_map(maze)

    def is_finished(self) -> bool:
        return self.position == self.maze.end

    def step(self) -> ProbeState:
        if self.is_finished():
            return ProbeState(self.position, self.steps, self.resources)

        neighbors = self.maze._neighbors(*self.position)
        if not neighbors:
            return ProbeState(self.position, self.steps, self.resources)

        visible = _scan_visible(self.maze, self.position, self.collected_coins, self.triggered_traps)
        path = bfs_path(self.maze, self.position, self.maze.end)
        if len(path) >= 2:
            best = path[1]
            adjacent_coins = [n for n in neighbors if n in visible['coins']]
            if adjacent_coins and self.dist_to_end.get(adjacent_coins[0], 9999) <= self.dist_to_end.get(best, 9999) + 2:
                best = max(adjacent_coins, key=lambda n: self._score(n, visible))
        else:
            best = max(neighbors, key=lambda n: self._score(n, visible))
        self.position = best
        self.steps += 1
        self._collect(best)
        return ProbeState(self.position, self.steps, self.resources)

    def _score(self, cell, visible):
        s = -self.dist_to_end.get(cell, 9999) * self.end_weight * 0.3
        if cell in visible['coins']:
            s += self.coin_weight * COIN_VALUE
        elif cell in visible['traps']:
            s -= self.trap_weight * abs(TRAP_VALUE)
        for c in visible['coins']:
            d = abs(cell[0]-c[0]) + abs(cell[1]-c[1])
            if d > 0: s += self.coin_weight * COIN_VALUE / (d * 2)
        for t in visible['traps']:
            d = abs(cell[0]-t[0]) + abs(cell[1]-t[1])
            if d > 0: s -= self.trap_weight * abs(TRAP_VALUE) / (d * 2)
        if visible['end']:
            ed = abs(cell[0]-self.maze.end[0]) + abs(cell[1]-self.maze.end[1])
            s += self.end_weight * 20.0 / max(1, ed)
        return s

    def _collect(self, cell):
        ct = self.maze.grid[cell[0]][cell[1]].content
        if ct == SYMBOLS["coin"] and cell not in self.collected_coins:
            self.resources += COIN_VALUE; self.collected_coins.add(cell)
        elif ct == SYMBOLS["trap"] and cell not in self.triggered_traps:
            self.resources += TRAP_VALUE; self.triggered_traps.add(cell)


# ============================================================================
#  MemoryGreedy — with visited-cell memory + exploration incentive
# ============================================================================

class MemoryGreedy:
    """Greedy AI with visited-cell memory. 3×3 visible area. No global map.

    Memory:  tracks every cell it has stepped on (visited dict).
             - visited cells → penalty (avoid loops)
             - unvisited cells → bonus (encourage exploration)

    This lets the AI backtrack out of dead ends: when all forward paths
    are visited, the penalty is equal, so it picks the best among them
    rather than getting stuck.
    """

    def __init__(self, maze, coin_weight=1.2, trap_weight=0.8, end_weight=1.6,
                 visited_penalty=2.0, unvisited_bonus=0.5, seed=None):
        if maze.start is None or maze.end is None:
            raise ValueError("Maze needs start/end")
        self.maze = maze
        self.coin_weight = coin_weight
        self.trap_weight = trap_weight
        self.end_weight = end_weight
        self.visited_penalty = visited_penalty
        self.unvisited_bonus = unvisited_bonus
        self.rng = random.Random(seed)

        self.position = maze.start
        self.steps = 0
        self.resources = 0
        self.collected_coins: set = set()
        self.triggered_traps: set = set()
        self.visited: dict[tuple[int, int], int] = {maze.start: 1}
        self.dist_to_end = distance_to_end_map(maze)

    def is_finished(self) -> bool:
        return self.position == self.maze.end

    def step(self) -> ProbeState:
        if self.is_finished():
            return ProbeState(self.position, self.steps, self.resources)

        neighbors = self.maze._neighbors(*self.position)
        if not neighbors:
            return ProbeState(self.position, self.steps, self.resources)

        visible = _scan_visible(self.maze, self.position, self.collected_coins, self.triggered_traps)
        path = bfs_path(self.maze, self.position, self.maze.end)
        if len(path) >= 2:
            best = path[1]
            adjacent_coins = [n for n in neighbors if n in visible['coins']]
            if adjacent_coins and self.dist_to_end.get(adjacent_coins[0], 9999) <= self.dist_to_end.get(best, 9999) + 2:
                best = max(adjacent_coins, key=lambda n: self._score(n, visible))
        else:
            best = max(neighbors, key=lambda n: self._score(n, visible))
        self.position = best
        self.steps += 1
        self.visited[best] = self.visited.get(best, 0) + 1
        self._collect(best)
        return ProbeState(self.position, self.steps, self.resources)

    def _score(self, cell, visible):
        # Base score — same as SimpleGreedy
        s = -self.dist_to_end.get(cell, 9999) * self.end_weight * 0.3
        if cell in visible['coins']:
            s += self.coin_weight * COIN_VALUE
        elif cell in visible['traps']:
            s -= self.trap_weight * abs(TRAP_VALUE)
        for c in visible['coins']:
            d = abs(cell[0]-c[0]) + abs(cell[1]-c[1])
            if d > 0: s += self.coin_weight * COIN_VALUE / (d * 2)
        for t in visible['traps']:
            d = abs(cell[0]-t[0]) + abs(cell[1]-t[1])
            if d > 0: s -= self.trap_weight * abs(TRAP_VALUE) / (d * 2)
        if visible['end']:
            ed = abs(cell[0]-self.maze.end[0]) + abs(cell[1]-self.maze.end[1])
            s += self.end_weight * 20.0 / max(1, ed)

        # ===== VISITED MEMORY (the key difference) =====
        visits = self.visited.get(cell, 0)
        if visits > 0:
            s -= self.visited_penalty * visits
        else:
            s += self.unvisited_bonus * 5.0

        return s

    def _collect(self, cell):
        ct = self.maze.grid[cell[0]][cell[1]].content
        if ct == SYMBOLS["coin"] and cell not in self.collected_coins:
            self.resources += COIN_VALUE; self.collected_coins.add(cell)
        elif ct == SYMBOLS["trap"] and cell not in self.triggered_traps:
            self.resources += TRAP_VALUE; self.triggered_traps.add(cell)


# Backward compat
GreedyAI = MemoryGreedy
ProbeAI = MemoryGreedy
