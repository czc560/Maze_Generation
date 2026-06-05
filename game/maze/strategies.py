"""Coin/trap placement strategies, distribution calibration, greedy-player simulation."""

from __future__ import annotations

import math
import random
import statistics
from dataclasses import dataclass
from typing import Callable

from game.maze.symbols import SYMBOLS, COIN_VALUE, TRAP_VALUE
from game.maze.pathfinding import (
    bfs_path, get_main_path, distance_to_end_map, distance_map,
    clamp, visible_cells, shortest_visible_value, _distance_to_path_map,
)


@dataclass
class SimulationResult:
    aggression: float
    reached_end: bool
    steps: int
    resources: int
    score: float
    collected_coins: int
    triggered_traps: int


# ============================================================================
#  Difficulty & weighted sampling
# ============================================================================

def _difficulty_map(maze) -> dict[tuple[int, int], float]:
    main_path = get_main_path(maze)
    dist_to_path = _distance_to_path_map(maze, main_path)
    dist_to_end = distance_to_end_map(maze)
    max_path = max(dist_to_path.values(), default=1)
    max_end = max(dist_to_end.values(), default=1)
    difficulty: dict[tuple[int, int], float] = {}
    for row in range(maze.rows):
        for col in range(maze.cols):
            if not maze.grid[row][col].walkable:
                continue
            cell = (row, col)
            ps = dist_to_path.get(cell, max_path) / max_path
            es = dist_to_end.get(cell, max_end) / max_end
            difficulty[cell] = clamp(0.6 * ps + 0.4 * es, 0.0, 1.0)
    return difficulty


def _gaussian_weight(x: float, mu: float, sigma: float) -> float:
    sigma = max(0.05, sigma)
    return math.exp(-((x - mu) ** 2) / (2 * sigma * sigma))


def _weighted_sample(cells, weights, k, rng):
    if k <= 0 or not cells:
        return []
    scored = []
    for cell, w in zip(cells, weights):
        key = -math.log(rng.random()) / max(w, 1e-6)
        scored.append((key, cell))
    scored.sort(key=lambda item: item[0])
    return [cell for _, cell in scored[:k]]


# ============================================================================
#  Normalized coin/trap strategies
# ============================================================================

def make_normalized_strategies(
    target_mean: float = 4.0, spread: float = 1.2,
) -> tuple[Callable, Callable]:
    """Return (coin_strategy, trap_strategy) closures tuned for roughly normal score distributions."""

    def coin_strategy(maze, remaining, rng):
        main_path = get_main_path(maze)
        main_set = set(main_path)
        difficulty = _difficulty_map(maze)
        base_ratio = 0.16
        mean_bonus = clamp((target_mean - 4.0) * 0.02, -0.05, 0.08)
        coin_count = max(1, int((base_ratio + mean_bonus) * len(remaining)))
        path_cells = [c for c in remaining if c in main_set
                      and c not in {maze.start, maze.end, *(maze.bosses or [])}]
        branch_cells = [c for c in remaining if c not in main_set]
        path_coin_count = min(len(path_cells), max(1, int(coin_count * 0.25)))
        branch_coin_count = coin_count - path_coin_count
        coins = []
        if path_coin_count > 0:
            w = [_gaussian_weight(difficulty.get(c, 0.4), 0.35, 0.25) for c in path_cells]
            coins.extend(_weighted_sample(path_cells, w, path_coin_count, rng))
        if branch_coin_count > 0 and branch_cells:
            w = [_gaussian_weight(difficulty.get(c, 0.5), 0.55, 0.25 + spread * 0.05) for c in branch_cells]
            coins.extend(_weighted_sample(branch_cells, w, branch_coin_count, rng))
        return coins

    def trap_strategy(maze, remaining, rng):
        main_path = get_main_path(maze)
        main_set = set(main_path)
        difficulty = _difficulty_map(maze)
        base_ratio = 0.10
        mean_penalty = clamp((4.0 - target_mean) * 0.015, -0.03, 0.06)
        trap_count = max(1, int((base_ratio + mean_penalty) * len(remaining)))
        safe_set = set(main_path[:3] + main_path[-4:])
        path_cells = [c for c in remaining if c in main_set
                      and c not in safe_set
                      and c not in {maze.start, maze.end, *(maze.bosses or [])}]
        branch_cells = [c for c in remaining if c not in main_set]
        path_trap_count = min(len(path_cells), max(1, int(trap_count * 0.15)))
        branch_trap_count = trap_count - path_trap_count
        traps = []
        if path_trap_count > 0:
            w = [_gaussian_weight(difficulty.get(c, 0.6), 0.6, 0.22) for c in path_cells]
            traps.extend(_weighted_sample(path_cells, w, path_trap_count, rng))
        if branch_trap_count > 0 and branch_cells:
            w = [_gaussian_weight(difficulty.get(c, 0.7), 0.7, 0.20 + spread * 0.04) for c in branch_cells]
            traps.extend(_weighted_sample(branch_cells, w, branch_trap_count, rng))
        return traps

    return coin_strategy, trap_strategy


# ============================================================================
#  Greedy player simulation (for distribution evaluation)
# ============================================================================

def simulate_greedy_player(maze, aggression: float, max_steps_factor: int = 8) -> SimulationResult:
    if maze.start is None or maze.end is None:
        return SimulationResult(aggression, False, 0, 0, 0.0, 0, 0)
    aggression = clamp(aggression, 0.0, 1.0)
    dist = distance_to_end_map(maze)
    pos = maze.start
    visited_count: dict = {}
    triggered_traps: set = set()
    collected_coins: set = set()
    resources, steps = 0, 0
    max_steps = max(maze.rows * maze.cols * max_steps_factor, 1)

    while pos != maze.end and steps < max_steps:
        visited_count[pos] = visited_count.get(pos, 0) + 1
        candidates = maze._neighbors(*pos)
        if not candidates:
            break
        vis = set(visible_cells(maze, pos))
        vis_coins = {c for c in vis
                     if maze.grid[c[0]][c[1]].content == SYMBOLS["coin"] and c not in collected_coins}
        vis_traps = {c for c in vis
                     if maze.grid[c[0]][c[1]].content == SYMBOLS["trap"] and c not in triggered_traps}

        best_cell = None
        best_score = float("-inf")
        for nxt in candidates:
            ct = maze.grid[nxt[0]][nxt[1]].content
            end_dist = dist.get(nxt, maze.rows * maze.cols)
            progress = -end_dist * (1.8 - aggression)
            coin_s = shortest_visible_value(maze, nxt, vis_coins, 4) * (0.6 + aggression)
            trap_s = shortest_visible_value(maze, nxt, vis_traps, 3) * (1.4 - aggression)
            direct = 0.0
            if ct == SYMBOLS["coin"] and nxt not in collected_coins:
                direct += COIN_VALUE * (0.8 + aggression)
            elif ct == SYMBOLS["trap"] and nxt not in triggered_traps:
                direct += TRAP_VALUE * (1.6 - aggression)
            explore = 2.5 * aggression / (1 + visited_count.get(nxt, 0))
            revisit = 4.0 * visited_count.get(nxt, 0)
            total = progress + coin_s + trap_s + direct + explore - revisit
            if total > best_score:
                best_score = total; best_cell = nxt

        if best_cell is None:
            break
        pos = best_cell; steps += 1
        ct = maze.grid[pos[0]][pos[1]].content
        if ct == SYMBOLS["coin"] and pos not in collected_coins:
            resources += COIN_VALUE; collected_coins.add(pos)
        elif ct == SYMBOLS["trap"] and pos not in triggered_traps:
            resources += TRAP_VALUE; triggered_traps.add(pos)

    reached = pos == maze.end
    score = resources / steps if steps > 0 else 0.0
    return SimulationResult(aggression, reached, steps, resources, score,
                            len(collected_coins), len(triggered_traps))


def evaluate_distribution(maze, player_count: int = 19) -> list[SimulationResult]:
    if player_count <= 1:
        aggressions = [0.5]
    else:
        aggressions = [i / (player_count - 1) for i in range(player_count)]
    return [simulate_greedy_player(maze, a) for a in aggressions]


# ============================================================================
#  Normality scoring & calibration
# ============================================================================

def _skewness(values):
    if len(values) < 2:
        return 0.0
    m = statistics.mean(values)
    s = statistics.pstdev(values)
    if s == 0:
        return 0.0
    return sum((v - m) ** 3 for v in values) / len(values) / (s ** 3)


def _kurtosis(values):
    if len(values) < 2:
        return 0.0
    m = statistics.mean(values)
    s = statistics.pstdev(values)
    if s == 0:
        return 0.0
    return sum((v - m) ** 4 for v in values) / len(values) / (s ** 4) - 3.0


def normality_score(results, target_mean, target_std):
    scores = [r.score for r in results]
    if not scores:
        return 1e9
    ms = statistics.mean(scores)
    ss = statistics.pstdev(scores) if len(scores) > 1 else 0.0
    sk = _skewness(scores)
    ku = _kurtosis(scores)
    rr = sum(1 for r in results if r.reached_end) / len(results)
    return (abs(ms - target_mean) + 0.7 * abs(ss - target_std)
            + 0.5 * abs(sk) + 0.2 * abs(ku) + 0.6 * abs(rr - 0.7))


def generate_normalized_maze(rows, cols, seed, target_mean=4.0, target_std=1.2,
                             attempts=6, generation_method="mst"):
    from game.maze.generator import Maze
    rng = random.Random(seed)
    best, best_report, best_score = None, None, float("inf")
    for attempt in range(max(1, attempts)):
        k = target_mean + rng.uniform(-0.6, 0.6)
        spread = clamp(target_std + rng.uniform(-0.4, 0.4), 0.6, 2.2)
        cs, ts = make_normalized_strategies(k, spread)
        maze = Maze.generate(rows=rows, cols=cols, seed=seed + attempt,
                             generation_method=generation_method,
                             coin_strategy=cs, trap_strategy=ts)
        results = evaluate_distribution(maze)
        score = normality_score(results, target_mean, target_std)
        if score < best_score:
            scores = [r.score for r in results]
            best_score = score; best = maze
            best_report = {
                "mean": statistics.mean(scores) if scores else 0.0,
                "std": statistics.pstdev(scores) if len(scores) > 1 else 0.0,
                "reach_rate": sum(1 for r in results if r.reached_end) / len(results),
                "skew": _skewness(scores), "kurtosis": _kurtosis(scores), "score": score,
            }
    if best is None:
        from game.maze.generator import Maze
        best = Maze.generate(rows=rows, cols=cols, seed=seed, generation_method=generation_method)
        best_report = {"mean": 0.0, "std": 0.0, "reach_rate": 0.0, "skew": 0.0, "kurtosis": 0.0, "score": 0.0}
    return best, best_report
