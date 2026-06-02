from __future__ import annotations

import heapq
import random
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from .config import ASSETS


SYMBOLS = ASSETS["symbols"]
COIN_VALUE = ASSETS["values"]["coin"]
TRAP_VALUE = ASSETS["values"]["trap"]


GENERATION_METHODS: dict[str, str] = {
    "mst": "最小生成树算法",
    "prim": "最小生成树算法",
    "minimum_spanning_tree": "最小生成树算法",
    "backtracking": "回溯法",
    "dfs": "回溯法",
    "divide_conquer": "分治法",
    "recursive_division": "分治法",
    "division": "分治法",
    "branch_bound": "分支限界法",
    "branch_and_bound": "分支限界法",
}


def normalize_generation_method(method: str | None) -> str:
    """Return the canonical key used by the maze builder."""
    if method is None:
        return "mst"
    key = method.strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "最小生成树": "mst",
        "最小生成树算法": "mst",
        "mst": "mst",
        "prim": "mst",
        "minimum_spanning_tree": "mst",
        "回溯": "backtracking",
        "回溯法": "backtracking",
        "dfs": "backtracking",
        "depth_first_search": "backtracking",
        "backtracking": "backtracking",
        "分治": "divide_conquer",
        "分治法": "divide_conquer",
        "recursive_division": "divide_conquer",
        "division": "divide_conquer",
        "divide_conquer": "divide_conquer",
        "分支限界": "branch_bound",
        "分支限界法": "branch_bound",
        "branch_bound": "branch_bound",
        "branch_and_bound": "branch_bound",
    }
    if key not in aliases:
        valid = ", ".join(sorted({"mst", "backtracking", "divide_conquer", "branch_bound"}))
        raise ValueError(f"Unknown maze generation method: {method!r}. Valid methods: {valid}")
    return aliases[key]


@dataclass
class MazeNode:
    """A single maze cell."""

    content: str = SYMBOLS["wall"]
    row: int = 0
    col: int = 0
    extra: Any = None
    params: dict[str, Any] = field(default_factory=dict)

    @property
    def walkable(self) -> bool:
        return self.content != SYMBOLS["wall"]

    def __str__(self) -> str:
        return self.content


class Maze:
    """Rectangular maze with selectable generation algorithms.

    Supported generation methods:
    - divide_conquer: recursive division / 分治法
    - backtracking: randomized DFS / 回溯法
    - branch_bound: branch-and-bound guided main path / 分支限界法
    - mst: randomized Prim minimum spanning tree / 最小生成树算法
    """

    def __init__(
        self,
        rows: int,
        cols: Optional[int] = None,
        seed: Optional[int] = None,
        generation_method: str = "mst",
        boss_battle: Optional[Callable[["Maze", tuple[int, int]], Any]] = None,
        coin_strategy: Optional[
            Callable[["Maze", list[tuple[int, int]], random.Random], list[tuple[int, int]]]
        ] = None,
        trap_strategy: Optional[
            Callable[["Maze", list[tuple[int, int]], random.Random], list[tuple[int, int]]]
        ] = None,
    ) -> None:
        if cols is None:
            cols = rows
        if rows < 1 or cols < 1:
            raise ValueError("Maze dimensions must be positive")

        self.rows = rows
        self.cols = cols
        self.seed = seed
        self.generation_method = normalize_generation_method(generation_method)
        self.random = random.Random(seed)
        self.grid: list[list[MazeNode]] = [
            [MazeNode(SYMBOLS["wall"], row, col) for col in range(cols)] for row in range(rows)
        ]
        self.start: Optional[tuple[int, int]] = None
        self.end: Optional[tuple[int, int]] = None
        self.boss: Optional[tuple[int, int]] = None
        self.boss_battle = boss_battle
        self.coin_strategy = coin_strategy
        self.trap_strategy = trap_strategy

    @classmethod
    def generate(
        cls,
        rows: int,
        cols: Optional[int] = None,
        seed: Optional[int] = None,
        generation_method: str = "mst",
        boss_battle: Optional[Callable[["Maze", tuple[int, int]], Any]] = None,
        coin_strategy: Optional[
            Callable[["Maze", list[tuple[int, int]], random.Random], list[tuple[int, int]]]
        ] = None,
        trap_strategy: Optional[
            Callable[["Maze", list[tuple[int, int]], random.Random], list[tuple[int, int]]]
        ] = None,
    ) -> "Maze":
        maze = cls(
            rows=rows,
            cols=cols,
            seed=seed,
            generation_method=generation_method,
            boss_battle=boss_battle,
            coin_strategy=coin_strategy,
            trap_strategy=trap_strategy,
        )
        maze._build()
        return maze

    def trigger_boss_battle(self) -> Any:
        if self.boss is None or self.boss_battle is None:
            return None
        return self.boss_battle(self, self.boss)

    def print(self) -> None:
        for row in self.grid:
            print("".join(node.content for node in row))

    def __str__(self) -> str:
        return "\n".join("".join(node.content for node in row) for row in self.grid)

    def _build(self) -> None:
        self._reset_grid()
        if self.generation_method == "divide_conquer":
            self._carve_divide_conquer_maze()
        elif self.generation_method == "backtracking":
            self._carve_backtracking_maze()
        elif self.generation_method == "branch_bound":
            self._carve_branch_bound_maze()
        else:
            self._carve_mst_maze()
        self._place_special_cells()

    def _reset_grid(self) -> None:
        self.grid = [
            [MazeNode(SYMBOLS["wall"], row, col) for col in range(self.cols)]
            for row in range(self.rows)
        ]
        self.start = None
        self.end = None
        self.boss = None

    # ------------------------------------------------------------------
    # 1) 最小生成树算法：随机 Prim。每个奇数坐标格是图节点，边是相邻节点之间的墙。
    # ------------------------------------------------------------------
    def _carve_mst_maze(self) -> None:
        """Generate a perfect maze by randomized Prim minimum spanning tree."""
        room_rows = list(range(1, self.rows - 1, 2))
        room_cols = list(range(1, self.cols - 1, 2))
        if not room_rows or not room_cols:
            self._carve_fallback_path()
            return

        start_row = self.random.choice(room_rows)
        start_col = self.random.choice(room_cols)

        visited: set[tuple[int, int]] = {(start_row, start_col)}
        self._open_cell(start_row, start_col)

        frontier: list[tuple[int, int, int, int, int]] = []
        for nr, nc in self._room_neighbors(start_row, start_col):
            weight = self.random.randint(1, 1_000_000)
            heapq.heappush(frontier, (weight, start_row, start_col, nr, nc))

        while frontier:
            _, from_row, from_col, to_row, to_col = heapq.heappop(frontier)
            if (to_row, to_col) in visited:
                continue

            self._open_between((from_row, from_col), (to_row, to_col))
            visited.add((to_row, to_col))

            for nr, nc in self._room_neighbors(to_row, to_col):
                if (nr, nc) not in visited:
                    weight = self.random.randint(1, 1_000_000)
                    heapq.heappush(frontier, (weight, to_row, to_col, nr, nc))

    # Keep the previous private name for compatibility with any external code.
    def _carve_prim_maze(self) -> None:
        self._carve_mst_maze()

    # ------------------------------------------------------------------
    # 2) 回溯法：随机 DFS。走不动时回退，因此天然生成单连通“完美迷宫”。
    # ------------------------------------------------------------------
    def _carve_backtracking_maze(self) -> None:
        """Generate a perfect maze by randomized depth-first backtracking."""
        room_rows = list(range(1, self.rows - 1, 2))
        room_cols = list(range(1, self.cols - 1, 2))
        if not room_rows or not room_cols:
            self._carve_fallback_path()
            return

        start = (self.random.choice(room_rows), self.random.choice(room_cols))
        visited: set[tuple[int, int]] = {start}
        stack: list[tuple[int, int]] = [start]
        self._open_cell(*start)

        while stack:
            current = stack[-1]
            candidates = [cell for cell in self._room_neighbors(*current) if cell not in visited]
            if not candidates:
                stack.pop()
                continue
            nxt = self.random.choice(candidates)
            self._open_between(current, nxt)
            visited.add(nxt)
            stack.append(nxt)

    # ------------------------------------------------------------------
    # 3) 分治法：递归分割。先打开房间，再不断加墙，并在墙上留一个门。
    # ------------------------------------------------------------------
    def _carve_divide_conquer_maze(self) -> None:
        """Generate a room-like maze by recursive division."""
        if self.rows < 3 or self.cols < 3:
            self._carve_fallback_path()
            return

        for row in range(1, self.rows - 1):
            for col in range(1, self.cols - 1):
                self._open_cell(row, col)

        self._divide_area(1, 1, self.rows - 2, self.cols - 2)

    def _divide_area(self, top: int, left: int, bottom: int, right: int) -> None:
        height = bottom - top + 1
        width = right - left + 1
        if height < 3 or width < 3:
            return

        horizontal = height > width if height != width else bool(self.random.getrandbits(1))

        if horizontal:
            possible_walls = [r for r in range(top + 1, bottom) if r % 2 == 0]
            possible_doors = [c for c in range(left, right + 1) if c % 2 == 1]
            if not possible_walls or not possible_doors:
                return
            wall_row = self.random.choice(possible_walls)
            door_col = self.random.choice(possible_doors)
            for col in range(left, right + 1):
                self._set_content(wall_row, col, SYMBOLS["wall"])
            self._open_cell(wall_row, door_col)
            self._divide_area(top, left, wall_row - 1, right)
            self._divide_area(wall_row + 1, left, bottom, right)
        else:
            possible_walls = [c for c in range(left + 1, right) if c % 2 == 0]
            possible_doors = [r for r in range(top, bottom + 1) if r % 2 == 1]
            if not possible_walls or not possible_doors:
                return
            wall_col = self.random.choice(possible_walls)
            door_row = self.random.choice(possible_doors)
            for row in range(top, bottom + 1):
                self._set_content(row, wall_col, SYMBOLS["wall"])
            self._open_cell(door_row, wall_col)
            self._divide_area(top, left, bottom, wall_col - 1)
            self._divide_area(top, wall_col + 1, bottom, right)

    # ------------------------------------------------------------------
    # 4) 分支限界法：用优先队列搜索一条满足长度下界的主路径，再按预算扩展分支。
    # ------------------------------------------------------------------
    def _carve_branch_bound_maze(self) -> None:
        """Generate a maze using a branch-and-bound guided main path."""
        room_rows = list(range(1, self.rows - 1, 2))
        room_cols = list(range(1, self.cols - 1, 2))
        if not room_rows or not room_cols:
            self._carve_fallback_path()
            return

        start = (room_rows[0], room_cols[0])
        goal = (room_rows[-1], room_cols[-1])
        room_count = len(room_rows) * len(room_cols)
        min_path_len = max(self._room_distance(start, goal) + 1, int(room_count * 0.45))

        main_path = self._branch_bound_room_path(start, goal, min_path_len, room_count)
        if not main_path:
            # When the bounded search cannot find a good path quickly, fall back to a safe DFS maze.
            self._carve_backtracking_maze()
            return

        visited: set[tuple[int, int]] = set()
        for cell in main_path:
            self._open_cell(*cell)
            visited.add(cell)
        for a, b in zip(main_path, main_path[1:]):
            self._open_between(a, b)

        branch_budget = max(0, int(room_count * 0.42))
        frontier = list(main_path)
        self.random.shuffle(frontier)

        while frontier and branch_budget > 0:
            base = frontier.pop()
            candidates = [cell for cell in self._room_neighbors(*base) if cell not in visited]
            if not candidates:
                continue
            # Limit rule: prefer candidates farther from the goal, producing side branches and dead ends.
            candidates.sort(key=lambda c: (self._room_distance(c, goal), self.random.random()), reverse=True)
            nxt = candidates[0]
            self._open_between(base, nxt)
            visited.add(nxt)
            frontier.append(nxt)
            if self.random.random() < 0.45:
                frontier.append(base)
            branch_budget -= 1

    def _branch_bound_room_path(
        self,
        start: tuple[int, int],
        goal: tuple[int, int],
        min_path_len: int,
        room_count: int,
    ) -> list[tuple[int, int]]:
        if start == goal:
            return [start]

        state_limit = max(1_500, min(55_000, room_count * 260))
        counter = 0
        best_goal_path: tuple[tuple[int, int], ...] | None = None
        best_goal_score = -10**18

        # priority, counter, current, path, visited, last_direction, turns
        heap: list[
            tuple[
                float,
                int,
                tuple[int, int],
                tuple[tuple[int, int], ...],
                frozenset[tuple[int, int]],
                tuple[int, int] | None,
                int,
            ]
        ] = []
        start_path = (start,)
        heapq.heappush(heap, (0.0, counter, start, start_path, frozenset({start}), None, 0))

        states_seen = 0
        while heap and states_seen < state_limit:
            _, _, current, path, visited, last_dir, turns = heapq.heappop(heap)
            states_seen += 1

            if current == goal:
                score = len(path) + 0.18 * turns
                if len(path) >= min_path_len:
                    return list(path)
                if score > best_goal_score:
                    best_goal_score = score
                    best_goal_path = path
                continue

            # Bound: even if all remaining rooms were used, this branch cannot satisfy the lower bound.
            if len(path) + (room_count - len(visited)) < min_path_len:
                continue

            neighbors = [cell for cell in self._room_neighbors(*current) if cell not in visited]
            self.random.shuffle(neighbors)
            for nxt in neighbors:
                direction = (nxt[0] - current[0], nxt[1] - current[1])
                next_turns = turns + (1 if last_dir is not None and direction != last_dir else 0)
                next_path = path + (nxt,)
                next_visited = frozenset(set(visited) | {nxt})

                dist_to_goal = self._room_distance(nxt, goal)
                shortage = max(0, min_path_len - len(next_path))
                # Lower priority is expanded first. This is the “bound” used to prune/guide branches.
                priority = (
                    dist_to_goal
                    + 0.30 * shortage
                    - 0.10 * next_turns
                    - 0.03 * len(next_path)
                    + self.random.random() * 0.25
                )
                counter += 1
                heapq.heappush(
                    heap,
                    (priority, counter, nxt, next_path, next_visited, direction, next_turns),
                )

        return list(best_goal_path) if best_goal_path is not None else []

    def _room_distance(self, a: tuple[int, int], b: tuple[int, int]) -> int:
        return (abs(a[0] - b[0]) + abs(a[1] - b[1])) // 2

    def _open_between(self, a: tuple[int, int], b: tuple[int, int]) -> None:
        self._open_cell(*a)
        self._open_cell((a[0] + b[0]) // 2, (a[1] + b[1]) // 2)
        self._open_cell(*b)

    def _room_neighbors(self, row: int, col: int) -> list[tuple[int, int]]:
        result: list[tuple[int, int]] = []
        for dr, dc in ((-2, 0), (2, 0), (0, -2), (0, 2)):
            next_row = row + dr
            next_col = col + dc
            if 0 < next_row < self.rows - 1 and 0 < next_col < self.cols - 1:
                result.append((next_row, next_col))
        return result

    def _carve_fallback_path(self) -> None:
        for row in range(self.rows):
            if row % 2 == 0:
                for col in range(self.cols):
                    self._open_cell(row, col)
            else:
                for col in range(self.cols - 1, -1, -1):
                    self._open_cell(row, col)
            if row + 1 < self.rows:
                bridge_col = self.cols - 1 if row % 2 == 0 else 0
                self._open_cell(row + 1, bridge_col)

    def _place_special_cells(self) -> None:
        open_cells = self._collect_open_cells()
        if not open_cells:
            return

        if len(open_cells) == 1:
            row, col = open_cells[0]
            self._set_content(row, col, SYMBOLS["start"])
            self.start = (row, col)
            return

        start, end, path = self._find_farthest_pair(open_cells)
        self._set_content(*start, SYMBOLS["start"])
        self._set_content(*end, SYMBOLS["end"])
        self.start = start
        self.end = end

        if len(path) >= 2:
            boss = path[-2]
            if boss not in {start, end}:
                self._set_content(*boss, SYMBOLS["boss"])
                self.boss = boss

        reserved = {start, end}
        if self.boss is not None:
            reserved.add(self.boss)

        remaining = [cell for cell in open_cells if cell not in reserved]
        if not remaining:
            return

        if self.coin_strategy is not None:
            coin_cells = self._apply_strategy(self.coin_strategy, remaining, SYMBOLS["coin"])
            remaining = [cell for cell in remaining if cell not in set(coin_cells)]
        else:
            reserve_traps = self.trap_strategy is None
            remaining = self._place_default_coins(remaining, reserve_traps=reserve_traps)

        if self.trap_strategy is not None and remaining:
            self._apply_strategy(self.trap_strategy, remaining, SYMBOLS["trap"])
        elif remaining:
            self._place_default_traps(remaining)

    def _apply_strategy(
        self,
        strategy: Callable[["Maze", list[tuple[int, int]], random.Random], list[tuple[int, int]]],
        remaining: list[tuple[int, int]],
        marker: str,
    ) -> list[tuple[int, int]]:
        suggested = strategy(self, list(remaining), self.random)
        if not suggested:
            return []
        filtered: list[tuple[int, int]] = []
        remaining_set = set(remaining)
        for cell in suggested:
            if cell in remaining_set and cell not in filtered:
                filtered.append(cell)
        for row, col in filtered:
            self._set_content(row, col, marker)
        return filtered

    def _place_default_coins(
        self, remaining: list[tuple[int, int]], reserve_traps: bool
    ) -> list[tuple[int, int]]:
        min_coins = 1
        min_traps = 1 if reserve_traps else 0
        if self.rows >= 15 and self.cols >= 15:
            min_coins = 5
            min_traps = 3 if reserve_traps else 0

        remaining_count = len(remaining)
        if remaining_count <= 0:
            return remaining

        if remaining_count < min_coins + min_traps:
            if remaining_count >= 2 and reserve_traps:
                min_coins = min(min_coins, remaining_count - 1)
                min_traps = min(min_traps, remaining_count - min_coins)
            else:
                min_coins = min(min_coins, remaining_count)
                min_traps = 0

        max_coin_cap = max(min_coins, remaining_count // 5)
        max_coin_count = max(min_coins, min(remaining_count - min_traps, max_coin_cap))
        coin_count = self.random.randint(min_coins, max_coin_count)

        if coin_count > 0:
            coin_cells = self.random.sample(remaining, coin_count)
            for row, col in coin_cells:
                self._set_content(row, col, SYMBOLS["coin"])
            return [cell for cell in remaining if cell not in set(coin_cells)]
        return remaining

    def _place_default_traps(self, remaining: list[tuple[int, int]]) -> None:
        min_traps = 1
        if self.rows >= 15 and self.cols >= 15:
            min_traps = 3

        remaining_count = len(remaining)
        if remaining_count <= 0:
            return

        trap_min = min(min_traps, remaining_count)
        max_trap_cap = max(min_traps, remaining_count // 8)
        trap_max = min(remaining_count, max_trap_cap)
        trap_count = self.random.randint(trap_min, trap_max)
        if trap_count > 0:
            trap_cells = self.random.sample(remaining, trap_count)
            for row, col in trap_cells:
                self._set_content(row, col, SYMBOLS["trap"])

    def _find_farthest_pair(
        self, open_cells: list[tuple[int, int]]
    ) -> tuple[tuple[int, int], tuple[int, int], list[tuple[int, int]]]:
        start = open_cells[0]
        farthest, _ = self._bfs_farthest(start)
        other, parent = self._bfs_farthest(farthest)
        path = self._reconstruct_path(parent, farthest, other)
        return farthest, other, path

    def _bfs_farthest(
        self, source: tuple[int, int]
    ) -> tuple[tuple[int, int], dict[tuple[int, int], tuple[int, int] | None]]:
        queue: deque[tuple[int, int]] = deque([source])
        parent: dict[tuple[int, int], tuple[int, int] | None] = {source: None}
        farthest = source

        while queue:
            row, col = queue.popleft()
            farthest = (row, col)
            for next_row, next_col in self._neighbors(row, col):
                if (next_row, next_col) not in parent:
                    parent[(next_row, next_col)] = (row, col)
                    queue.append((next_row, next_col))

        return farthest, parent

    def _reconstruct_path(
        self,
        parent: dict[tuple[int, int], tuple[int, int] | None],
        start: tuple[int, int],
        end: tuple[int, int],
    ) -> list[tuple[int, int]]:
        path: list[tuple[int, int]] = [end]
        current = end
        while current != start:
            previous = parent.get(current)
            if previous is None:
                break
            path.append(previous)
            current = previous
        path.reverse()
        return path

    def _neighbors(self, row: int, col: int) -> list[tuple[int, int]]:
        result: list[tuple[int, int]] = []
        for next_row, next_col in (
            (row - 1, col),
            (row + 1, col),
            (row, col - 1),
            (row, col + 1),
        ):
            if 0 <= next_row < self.rows and 0 <= next_col < self.cols:
                if self.grid[next_row][next_col].walkable:
                    result.append((next_row, next_col))
        return result

    def _collect_open_cells(self) -> list[tuple[int, int]]:
        cells: list[tuple[int, int]] = []
        for row in range(self.rows):
            for col in range(self.cols):
                if self.grid[row][col].walkable:
                    cells.append((row, col))
        return cells

    def _set_content(self, row: int, col: int, content: str) -> None:
        if 0 <= row < self.rows and 0 <= col < self.cols:
            self.grid[row][col].content = content

    def _open_cell(self, row: int, col: int) -> None:
        self._set_content(row, col, SYMBOLS["floor"])
