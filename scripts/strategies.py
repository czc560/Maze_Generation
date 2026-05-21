from __future__ import annotations

import math
import random
import statistics
from collections import deque
from dataclasses import dataclass
from typing import Callable

from .maze import COIN_VALUE, TRAP_VALUE, Maze, SYMBOLS


@dataclass
class SimulationResult:
    aggression: float
    reached_end: bool
    steps: int
    resources: int
    score: float
    collected_coins: int
    triggered_traps: int


def bfs_path(maze: Maze, start: tuple[int, int], end: tuple[int, int]) -> list[tuple[int, int]]:
    q: deque[tuple[int, int]] = deque([start])
    parent: dict[tuple[int, int], tuple[int, int] | None] = {start: None}

    while q:
        cell = q.popleft()
        if cell == end:
            break
        for nxt in maze._neighbors(*cell):
            if nxt not in parent:
                parent[nxt] = cell
                q.append(nxt)

    if end not in parent:
        return []

    path: list[tuple[int, int]] = []
    cur: tuple[int, int] | None = end
    while cur is not None:
        path.append(cur)
        cur = parent[cur]
    path.reverse()
    return path


def get_main_path(maze: Maze) -> list[tuple[int, int]]:
    if maze.start is None or maze.end is None:
        return []
    return bfs_path(maze, maze.start, maze.end)


def distance_to_end_map(maze: Maze) -> dict[tuple[int, int], int]:
    if maze.end is None:
        return {}

    q: deque[tuple[int, int]] = deque([maze.end])
    dist: dict[tuple[int, int], int] = {maze.end: 0}

    while q:
        cell = q.popleft()
        for nxt in maze._neighbors(*cell):
            if nxt not in dist:
                dist[nxt] = dist[cell] + 1
                q.append(nxt)

    return dist


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _distance_to_path_map(maze: Maze, path: list[tuple[int, int]]) -> dict[tuple[int, int], int]:
    if not path:
        return {}

    q: deque[tuple[int, int]] = deque(path)
    dist: dict[tuple[int, int], int] = {cell: 0 for cell in path}

    while q:
        cell = q.popleft()
        for nxt in maze._neighbors(*cell):
            if nxt not in dist:
                dist[nxt] = dist[cell] + 1
                q.append(nxt)

    return dist


def _difficulty_map(maze: Maze) -> dict[tuple[int, int], float]:
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
            path_score = dist_to_path.get(cell, max_path) / max_path
            end_score = dist_to_end.get(cell, max_end) / max_end
            difficulty[cell] = clamp(0.6 * path_score + 0.4 * end_score, 0.0, 1.0)
    return difficulty


def _gaussian_weight(x: float, mu: float, sigma: float) -> float:
    sigma = max(0.05, sigma)
    return math.exp(-((x - mu) ** 2) / (2 * sigma * sigma))


def _weighted_sample(cells: list[tuple[int, int]], weights: list[float], k: int, rng: random.Random) -> list[tuple[int, int]]:
    if k <= 0 or not cells:
        return []

    scored: list[tuple[float, tuple[int, int]]] = []
    for cell, weight in zip(cells, weights):
        w = max(weight, 1e-6)
        key = -math.log(rng.random()) / w
        scored.append((key, cell))

    scored.sort(key=lambda item: item[0])
    return [cell for _, cell in scored[:k]]


def make_normalized_strategies(
    target_mean: float = 4.0,
    spread: float = 1.2,
) -> tuple[
    Callable[[Maze, list[tuple[int, int]], random.Random], list[tuple[int, int]]],
    Callable[[Maze, list[tuple[int, int]], random.Random], list[tuple[int, int]]],
]:
    """Generate coin/trap strategies tuned for roughly normal score distributions."""

    def coin_strategy(maze: Maze, remaining: list[tuple[int, int]], rng: random.Random) -> list[tuple[int, int]]:
        main_path = get_main_path(maze)
        main_set = set(main_path)
        difficulty = _difficulty_map(maze)

        base_ratio = 0.16
        mean_bonus = clamp((target_mean - 4.0) * 0.02, -0.05, 0.08)
        coin_count = max(1, int((base_ratio + mean_bonus) * len(remaining)))

        path_cells = [
            c for c in remaining
            if c in main_set and c not in {maze.start, maze.end, maze.boss}
        ]
        branch_cells = [c for c in remaining if c not in main_set]

        path_coin_count = min(len(path_cells), max(1, int(coin_count * 0.25)))
        branch_coin_count = coin_count - path_coin_count

        coins: list[tuple[int, int]] = []
        if path_coin_count > 0:
            path_weights = [
                _gaussian_weight(difficulty.get(c, 0.4), 0.35, 0.25)
                for c in path_cells
            ]
            coins.extend(_weighted_sample(path_cells, path_weights, path_coin_count, rng))

        if branch_coin_count > 0 and branch_cells:
            branch_weights = [
                _gaussian_weight(difficulty.get(c, 0.5), 0.55, 0.25 + spread * 0.05)
                for c in branch_cells
            ]
            coins.extend(_weighted_sample(branch_cells, branch_weights, branch_coin_count, rng))

        return coins

    def trap_strategy(maze: Maze, remaining: list[tuple[int, int]], rng: random.Random) -> list[tuple[int, int]]:
        main_path = get_main_path(maze)
        main_set = set(main_path)
        difficulty = _difficulty_map(maze)

        base_ratio = 0.10
        mean_penalty = clamp((4.0 - target_mean) * 0.015, -0.03, 0.06)
        trap_count = max(1, int((base_ratio + mean_penalty) * len(remaining)))

        safe_path_cells = set(main_path[:3] + main_path[-4:])
        path_cells = [
            c for c in remaining
            if c in main_set
            and c not in safe_path_cells
            and c not in {maze.start, maze.end, maze.boss}
        ]
        branch_cells = [c for c in remaining if c not in main_set]

        path_trap_count = min(len(path_cells), max(1, int(trap_count * 0.15)))
        branch_trap_count = trap_count - path_trap_count

        traps: list[tuple[int, int]] = []
        if path_trap_count > 0:
            path_weights = [
                _gaussian_weight(difficulty.get(c, 0.6), 0.6, 0.22)
                for c in path_cells
            ]
            traps.extend(_weighted_sample(path_cells, path_weights, path_trap_count, rng))

        if branch_trap_count > 0 and branch_cells:
            branch_weights = [
                _gaussian_weight(difficulty.get(c, 0.7), 0.7, 0.20 + spread * 0.04)
                for c in branch_cells
            ]
            traps.extend(_weighted_sample(branch_cells, branch_weights, branch_trap_count, rng))

        return traps

    return coin_strategy, trap_strategy


def visible_cells(maze: Maze, pos: tuple[int, int]) -> list[tuple[int, int]]:
    row, col = pos
    cells: list[tuple[int, int]] = []
    for r in range(row - 1, row + 2):
        for c in range(col - 1, col + 2):
            if 0 <= r < maze.rows and 0 <= c < maze.cols:
                if maze.grid[r][c].walkable:
                    cells.append((r, c))
    return cells


def shortest_visible_value(
    maze: Maze,
    start: tuple[int, int],
    targets: set[tuple[int, int]],
    max_depth: int = 4,
) -> float:
    if not targets:
        return 0.0

    q: deque[tuple[tuple[int, int], int]] = deque([(start, 0)])
    seen = {start}
    best = 0.0

    while q:
        cell, depth = q.popleft()
        if depth > max_depth:
            continue

        content = maze.grid[cell[0]][cell[1]].content
        if cell in targets and depth > 0:
            if content == SYMBOLS["coin"]:
                best += COIN_VALUE / depth
            elif content == SYMBOLS["trap"]:
                best += TRAP_VALUE / depth

        if depth == max_depth:
            continue

        for nxt in maze._neighbors(*cell):
            if nxt not in seen:
                seen.add(nxt)
                q.append((nxt, depth + 1))

    return best


def simulate_greedy_player(
    maze: Maze,
    aggression: float,
    max_steps_factor: int = 8,
) -> SimulationResult:
    if maze.start is None or maze.end is None:
        return SimulationResult(aggression, False, 0, 0, 0.0, 0, 0)

    aggression = clamp(aggression, 0.0, 1.0)
    dist = distance_to_end_map(maze)

    pos = maze.start
    visited_count: dict[tuple[int, int], int] = {}
    triggered_traps: set[tuple[int, int]] = set()
    collected_coins: set[tuple[int, int]] = set()

    resources = 0
    steps = 0
    max_steps = max(maze.rows * maze.cols * max_steps_factor, 1)

    while pos != maze.end and steps < max_steps:
        visited_count[pos] = visited_count.get(pos, 0) + 1
        candidates = maze._neighbors(*pos)

        if not candidates:
            break

        visible = set(visible_cells(maze, pos))
        visible_uncollected = {
            c for c in visible
            if maze.grid[c[0]][c[1]].content == SYMBOLS["coin"] and c not in collected_coins
        }
        visible_untriggered_traps = {
            c for c in visible
            if maze.grid[c[0]][c[1]].content == SYMBOLS["trap"] and c not in triggered_traps
        }

        best_cell = None
        best_score = -10**18

        for nxt in candidates:
            cell_content = maze.grid[nxt[0]][nxt[1]].content

            end_distance = dist.get(nxt, maze.rows * maze.cols)
            progress_score = -end_distance * (1.8 - aggression)

            local_value = shortest_visible_value(maze, nxt, visible_uncollected, max_depth=4)
            local_trap_value = shortest_visible_value(maze, nxt, visible_untriggered_traps, max_depth=3)

            coin_score = local_value * (0.6 + aggression)
            trap_score = local_trap_value * (1.4 - aggression)

            direct_score = 0.0
            if cell_content == SYMBOLS["coin"] and nxt not in collected_coins:
                direct_score += COIN_VALUE * (0.8 + aggression)
            elif cell_content == SYMBOLS["trap"] and nxt not in triggered_traps:
                direct_score += TRAP_VALUE * (1.6 - aggression)

            exploration_score = 2.5 * aggression / (1 + visited_count.get(nxt, 0))
            revisit_penalty = 4.0 * visited_count.get(nxt, 0)

            total = progress_score + coin_score + trap_score + direct_score + exploration_score - revisit_penalty

            if total > best_score:
                best_score = total
                best_cell = nxt

        if best_cell is None:
            break

        pos = best_cell
        steps += 1

        content = maze.grid[pos[0]][pos[1]].content
        if content == SYMBOLS["coin"] and pos not in collected_coins:
            resources += COIN_VALUE
            collected_coins.add(pos)
        elif content == SYMBOLS["trap"] and pos not in triggered_traps:
            resources += TRAP_VALUE
            triggered_traps.add(pos)

    reached = pos == maze.end
    score = resources / steps if steps > 0 else 0.0

    return SimulationResult(
        aggression=aggression,
        reached_end=reached,
        steps=steps,
        resources=resources,
        score=score,
        collected_coins=len(collected_coins),
        triggered_traps=len(triggered_traps),
    )


def evaluate_distribution(maze: Maze, player_count: int = 19) -> list[SimulationResult]:
    if player_count <= 1:
        aggressions = [0.5]
    else:
        aggressions = [i / (player_count - 1) for i in range(player_count)]
    return [simulate_greedy_player(maze, a) for a in aggressions]


def _skewness(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = statistics.mean(values)
    stdev = statistics.pstdev(values)
    if stdev == 0:
        return 0.0
    return sum((v - mean) ** 3 for v in values) / len(values) / (stdev ** 3)


def _kurtosis(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = statistics.mean(values)
    stdev = statistics.pstdev(values)
    if stdev == 0:
        return 0.0
    return sum((v - mean) ** 4 for v in values) / len(values) / (stdev ** 4) - 3.0


def normality_score(results: list[SimulationResult], target_mean: float, target_std: float) -> float:
    scores = [r.score for r in results]
    if not scores:
        return 1e9
    mean_score = statistics.mean(scores)
    stdev_score = statistics.pstdev(scores) if len(scores) > 1 else 0.0
    skew = _skewness(scores)
    kurt = _kurtosis(scores)
    reach_rate = sum(1 for r in results if r.reached_end) / len(results)

    return (
        abs(mean_score - target_mean)
        + 0.7 * abs(stdev_score - target_std)
        + 0.5 * abs(skew)
        + 0.2 * abs(kurt)
        + 0.6 * abs(reach_rate - 0.7)
    )


def generate_normalized_maze(
    rows: int,
    cols: int,
    seed: int,
    target_mean: float = 4.0,
    target_std: float = 1.2,
    attempts: int = 6,
) -> tuple[Maze, dict[str, float]]:
    rng = random.Random(seed)
    best: Maze | None = None
    best_report: dict[str, float] | None = None
    best_score = float("inf")

    for attempt in range(max(1, attempts)):
        k = target_mean + rng.uniform(-0.6, 0.6)
        spread = clamp(target_std + rng.uniform(-0.4, 0.4), 0.6, 2.2)
        coin_strategy, trap_strategy = make_normalized_strategies(k, spread)
        maze = Maze.generate(
            rows=rows,
            cols=cols,
            seed=seed + attempt,
            coin_strategy=coin_strategy,
            trap_strategy=trap_strategy,
        )
        results = evaluate_distribution(maze)
        score = normality_score(results, target_mean=target_mean, target_std=target_std)

        if score < best_score:
            scores = [r.score for r in results]
            best_score = score
            best = maze
            best_report = {
                "mean": statistics.mean(scores) if scores else 0.0,
                "std": statistics.pstdev(scores) if len(scores) > 1 else 0.0,
                "reach_rate": sum(1 for r in results if r.reached_end) / len(results),
                "skew": _skewness(scores),
                "kurtosis": _kurtosis(scores),
                "score": score,
            }

    if best is None:
        best = Maze.generate(rows=rows, cols=cols, seed=seed)
        best_report = {
            "mean": 0.0,
            "std": 0.0,
            "reach_rate": 0.0,
            "skew": 0.0,
            "kurtosis": 0.0,
            "score": 0.0,
        }

    return best, best_report
