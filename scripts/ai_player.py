from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional

from .maze import COIN_VALUE, TRAP_VALUE, Maze, SYMBOLS
from .strategies import distance_to_end_map, shortest_visible_value, visible_cells, clamp


@dataclass
class ProbeState:
    position: tuple[int, int]
    steps: int
    resources: int


class ProbeAI:
    """A greedy agent that probes short rollouts before moving."""

    def __init__(
        self,
        maze: Maze,
        aggression: float = 0.55,
        probe_depth: int = 6,
        rollouts: int = 6,
        seed: Optional[int] = None,
    ) -> None:
        if maze.start is None or maze.end is None:
            raise ValueError("Maze must have start and end")

        self.maze = maze
        self.aggression = clamp(aggression, 0.0, 1.0)
        self.probe_depth = max(1, probe_depth)
        self.rollouts = max(1, rollouts)
        self.rng = random.Random(seed)

        self.position = maze.start
        self.steps = 0
        self.resources = 0
        self.collected_coins: set[tuple[int, int]] = set()
        self.triggered_traps: set[tuple[int, int]] = set()

        self.dist_to_end = distance_to_end_map(maze)

    def is_finished(self) -> bool:
        return self.position == self.maze.end

    def step(self) -> ProbeState:
        if self.is_finished():
            return ProbeState(self.position, self.steps, self.resources)

        candidates = self.maze._neighbors(*self.position)
        if not candidates:
            return ProbeState(self.position, self.steps, self.resources)

        best_cell = None
        best_score = -10**18
        for nxt in candidates:
            score = self._evaluate_move(nxt)
            if score > best_score:
                best_score = score
                best_cell = nxt

        if best_cell is None:
            return ProbeState(self.position, self.steps, self.resources)

        self.position = best_cell
        self.steps += 1
        self._collect_cell(self.position)
        return ProbeState(self.position, self.steps, self.resources)

    def _collect_cell(self, cell: tuple[int, int]) -> None:
        content = self.maze.grid[cell[0]][cell[1]].content
        if content == SYMBOLS["coin"] and cell not in self.collected_coins:
            self.resources += COIN_VALUE
            self.collected_coins.add(cell)
        elif content == SYMBOLS["trap"] and cell not in self.triggered_traps:
            self.resources += TRAP_VALUE
            self.triggered_traps.add(cell)

    def _evaluate_move(self, nxt: tuple[int, int]) -> float:
        immediate = self._immediate_score(nxt)
        rollout = self._probe_rollout(nxt)
        return immediate + rollout

    def _immediate_score(self, nxt: tuple[int, int]) -> float:
        end_distance = self.dist_to_end.get(nxt, self.maze.rows * self.maze.cols)
        progress_score = -end_distance * (1.6 - self.aggression)

        visible = set(visible_cells(self.maze, self.position))
        visible_coins = {
            c for c in visible
            if self.maze.grid[c[0]][c[1]].content == SYMBOLS["coin"] and c not in self.collected_coins
        }
        visible_traps = {
            c for c in visible
            if self.maze.grid[c[0]][c[1]].content == SYMBOLS["trap"] and c not in self.triggered_traps
        }

        coin_score = shortest_visible_value(self.maze, nxt, visible_coins, max_depth=4) * (0.6 + self.aggression)
        trap_score = shortest_visible_value(self.maze, nxt, visible_traps, max_depth=3) * (1.4 - self.aggression)

        direct = 0.0
        cell_content = self.maze.grid[nxt[0]][nxt[1]].content
        if cell_content == SYMBOLS["coin"] and nxt not in self.collected_coins:
            direct += COIN_VALUE * (0.9 + self.aggression)
        elif cell_content == SYMBOLS["trap"] and nxt not in self.triggered_traps:
            direct += TRAP_VALUE * (1.7 - self.aggression)

        return progress_score + coin_score + trap_score + direct

    def _probe_rollout(self, nxt: tuple[int, int]) -> float:
        total = 0.0
        for _ in range(self.rollouts):
            total += self._rollout_from(nxt)
        return total / self.rollouts

    def _rollout_from(self, nxt: tuple[int, int]) -> float:
        pos = nxt
        collected = set(self.collected_coins)
        triggered = set(self.triggered_traps)
        resources = 0.0

        for _ in range(self.probe_depth):
            if pos == self.maze.end:
                break
            candidates = self.maze._neighbors(*pos)
            if not candidates:
                break

            best_cell = None
            best_score = -10**18
            for cand in candidates:
                score = self._rollout_score(cand, collected, triggered)
                if score > best_score:
                    best_score = score
                    best_cell = cand

            if best_cell is None:
                break

            pos = best_cell
            content = self.maze.grid[pos[0]][pos[1]].content
            if content == SYMBOLS["coin"] and pos not in collected:
                resources += COIN_VALUE
                collected.add(pos)
            elif content == SYMBOLS["trap"] and pos not in triggered:
                resources += TRAP_VALUE
                triggered.add(pos)

        return resources / max(1, self.probe_depth)

    def _rollout_score(
        self,
        cell: tuple[int, int],
        collected: set[tuple[int, int]],
        triggered: set[tuple[int, int]],
    ) -> float:
        score = 0.0
        end_distance = self.dist_to_end.get(cell, self.maze.rows * self.maze.cols)
        score -= end_distance * (1.2 - self.aggression)

        content = self.maze.grid[cell[0]][cell[1]].content
        if content == SYMBOLS["coin"] and cell not in collected:
            score += COIN_VALUE * (0.7 + self.aggression)
        elif content == SYMBOLS["trap"] and cell not in triggered:
            score += TRAP_VALUE * (1.4 - self.aggression)

        return score
