"""Maze class with four generation algorithms."""

from __future__ import annotations

import heapq
import random
from collections import deque
from typing import Any, Callable, Optional

from game.maze.node import MazeNode
from game.maze.symbols import SYMBOLS, COIN_VALUE, TRAP_VALUE, normalize_generation_method
from game.maze.pathfinding import bfs_path, distance_to_end_map


class Maze:
    """Rectangular maze with selectable generation algorithms.

    Supported methods: mst (Prim), backtracking (DFS), divide_conquer, branch_bound.
    """

    def __init__(
        self,
        rows: int,
        cols: Optional[int] = None,
        seed: Optional[int] = None,
        generation_method: str = "mst",
        boss_battle: Optional[Callable] = None,
        coin_strategy: Optional[Callable] = None,
        trap_strategy: Optional[Callable] = None,
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
        self.bosses: list[tuple[int, int]] = []
        self.boss_battle = boss_battle
        self.coin_strategy = coin_strategy
        self.trap_strategy = trap_strategy

    @classmethod
    def generate(cls, rows: int, cols: Optional[int] = None, seed: Optional[int] = None,
                 generation_method: str = "mst", boss_battle=None,
                 coin_strategy=None, trap_strategy=None) -> "Maze":
        maze = cls(rows=rows, cols=cols, seed=seed, generation_method=generation_method,
                   boss_battle=boss_battle, coin_strategy=coin_strategy, trap_strategy=trap_strategy)
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

    # ========================================================================
    #  Build pipeline
    # ========================================================================

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
        self.grid = [[MazeNode(SYMBOLS["wall"], row, col) for col in range(self.cols)] for row in range(self.rows)]
        self.start = self.end = self.boss = None
        self.bosses.clear()

    # ========================================================================
    #  1) MST / Randomized Prim
    # ========================================================================

    def _carve_mst_maze(self) -> None:
        room_rows = list(range(1, self.rows - 1, 2))
        room_cols = list(range(1, self.cols - 1, 2))
        if not room_rows or not room_cols:
            self._carve_fallback_path(); return
        sr = self.random.choice(room_rows)
        sc = self.random.choice(room_cols)
        visited: set[tuple[int, int]] = {(sr, sc)}
        self._open_cell(sr, sc)
        frontier: list[tuple[int, int, int, int, int]] = []
        for nr, nc in self._room_neighbors(sr, sc):
            heapq.heappush(frontier, (self.random.randint(1, 1_000_000), sr, sc, nr, nc))
        while frontier:
            _, fr, fc, tr, tc = heapq.heappop(frontier)
            if (tr, tc) in visited:
                continue
            self._open_between((fr, fc), (tr, tc))
            visited.add((tr, tc))
            for nr, nc in self._room_neighbors(tr, tc):
                if (nr, nc) not in visited:
                    heapq.heappush(frontier, (self.random.randint(1, 1_000_000), tr, tc, nr, nc))

    def _carve_prim_maze(self) -> None:
        self._carve_mst_maze()

    # ========================================================================
    #  2) Backtracking / Randomized DFS
    # ========================================================================

    def _carve_backtracking_maze(self) -> None:
        room_rows = list(range(1, self.rows - 1, 2))
        room_cols = list(range(1, self.cols - 1, 2))
        if not room_rows or not room_cols:
            self._carve_fallback_path(); return
        start = (self.random.choice(room_rows), self.random.choice(room_cols))
        visited: set[tuple[int, int]] = {start}
        stack: list[tuple[int, int]] = [start]
        self._open_cell(*start)
        while stack:
            current = stack[-1]
            candidates = [c for c in self._room_neighbors(*current) if c not in visited]
            if not candidates:
                stack.pop(); continue
            nxt = self.random.choice(candidates)
            self._open_between(current, nxt)
            visited.add(nxt); stack.append(nxt)

    # ========================================================================
    #  3) Divide & Conquer / Recursive Division
    # ========================================================================

    def _carve_divide_conquer_maze(self) -> None:
        if self.rows < 3 or self.cols < 3:
            self._carve_fallback_path(); return
        for row in range(1, self.rows - 1):
            for col in range(1, self.cols - 1):
                self._open_cell(row, col)
        self._divide_area(1, 1, self.rows - 2, self.cols - 2)

    def _divide_area(self, top: int, left: int, bottom: int, right: int) -> None:
        height, width = bottom - top + 1, right - left + 1
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

    # ========================================================================
    #  4) Branch & Bound
    # ========================================================================

    def _carve_branch_bound_maze(self) -> None:
        room_rows = list(range(1, self.rows - 1, 2))
        room_cols = list(range(1, self.cols - 1, 2))
        if not room_rows or not room_cols:
            self._carve_fallback_path(); return
        start = (room_rows[0], room_cols[0])
        goal = (room_rows[-1], room_cols[-1])
        room_count = len(room_rows) * len(room_cols)
        min_path_len = max(self._room_distance(start, goal) + 1, int(room_count * 0.45))
        main_path = self._branch_bound_room_path(start, goal, min_path_len, room_count)
        if not main_path:
            self._carve_backtracking_maze(); return
        visited: set[tuple[int, int]] = set()
        for cell in main_path:
            self._open_cell(*cell); visited.add(cell)
        for a, b in zip(main_path, main_path[1:]):
            self._open_between(a, b)
        branch_budget = max(0, int(room_count * 0.42))
        frontier = list(main_path)
        self.random.shuffle(frontier)
        while frontier and branch_budget > 0:
            base = frontier.pop()
            candidates = [c for c in self._room_neighbors(*base) if c not in visited]
            if not candidates:
                continue
            candidates.sort(key=lambda c: (self._room_distance(c, goal), self.random.random()), reverse=True)
            nxt = candidates[0]
            self._open_between(base, nxt)
            visited.add(nxt); frontier.append(nxt)
            if self.random.random() < 0.45:
                frontier.append(base)
            branch_budget -= 1

    def _branch_bound_room_path(self, start, goal, min_path_len, room_count):
        if start == goal:
            return [start]
        state_limit = max(1_500, min(55_000, room_count * 260))
        counter = 0
        best_goal_path = None; best_goal_score = float("-inf")
        heap: list = []
        heapq.heappush(heap, (0.0, counter, start, (start,), frozenset({start}), None, 0))
        states_seen = 0
        while heap and states_seen < state_limit:
            _, _, current, path, visited, last_dir, turns = heapq.heappop(heap)
            states_seen += 1
            if current == goal:
                score = len(path) + 0.18 * turns
                if len(path) >= min_path_len:
                    return list(path)
                if score > best_goal_score:
                    best_goal_score = score; best_goal_path = path
                continue
            if len(path) + (room_count - len(visited)) < min_path_len:
                continue
            neighbors = [c for c in self._room_neighbors(*current) if c not in visited]
            self.random.shuffle(neighbors)
            for nxt in neighbors:
                direction = (nxt[0] - current[0], nxt[1] - current[1])
                next_turns = turns + (1 if last_dir is not None and direction != last_dir else 0)
                next_path = path + (nxt,)
                next_visited = frozenset(set(visited) | {nxt})
                dist_to_goal = self._room_distance(nxt, goal)
                shortage = max(0, min_path_len - len(next_path))
                priority = (dist_to_goal + 0.30 * shortage - 0.10 * next_turns
                            - 0.03 * len(next_path) + self.random.random() * 0.25)
                counter += 1
                heapq.heappush(heap, (priority, counter, nxt, next_path, next_visited, direction, next_turns))
        return list(best_goal_path) if best_goal_path is not None else []

    def _room_distance(self, a, b):
        return (abs(a[0] - b[0]) + abs(a[1] - b[1])) // 2

    def _open_between(self, a, b):
        self._open_cell(*a)
        self._open_cell((a[0] + b[0]) // 2, (a[1] + b[1]) // 2)
        self._open_cell(*b)

    def _room_neighbors(self, row, col):
        result = []
        for dr, dc in ((-2, 0), (2, 0), (0, -2), (0, 2)):
            nr, nc = row + dr, col + dc
            if 0 < nr < self.rows - 1 and 0 < nc < self.cols - 1:
                result.append((nr, nc))
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
                self._open_cell(row + 1, self.cols - 1 if row % 2 == 0 else 0)

    # ========================================================================
    #  Special cell placement
    # ========================================================================

    def _place_special_cells(self) -> None:
        open_cells = self._collect_open_cells()
        if not open_cells:
            return
        if len(open_cells) == 1:
            row, col = open_cells[0]
            self._set_content(row, col, SYMBOLS["start"])
            self.start = (row, col); return

        start, end, path = self._find_farthest_pair(open_cells)
        self._set_content(*start, SYMBOLS["start"])
        self._set_content(*end, SYMBOLS["end"])
        self.start, self.end = start, end

        # Place ONE boss on the critical path (second-to-last cell)
        if len(path) >= 2:
            boss = path[-2]
            if boss not in {start, end}:
                self._set_content(*boss, SYMBOLS["boss"])
                self.bosses.append(boss)
                self.boss = boss

        reserved = {start, end}
        reserved.update(self.bosses)
        remaining = [c for c in open_cells if c not in reserved]
        if not remaining:
            return

        if self.coin_strategy is not None:
            coin_cells = self._apply_strategy(self.coin_strategy, remaining, SYMBOLS["coin"])
            remaining = [c for c in remaining if c not in set(coin_cells)]
        else:
            remaining = self._place_default_coins(remaining, reserve_traps=self.trap_strategy is None)

        if self.trap_strategy is not None and remaining:
            self._apply_strategy(self.trap_strategy, remaining, SYMBOLS["trap"])
        elif remaining:
            self._place_default_traps(remaining)

    def _apply_strategy(self, strategy, remaining, marker):
        suggested = strategy(self, list(remaining), self.random)
        if not suggested:
            return []
        remaining_set = set(remaining)
        filtered = [c for c in suggested if c in remaining_set and c not in
                    ([] if not hasattr(self, '_apply_cache') else [])]
        result = []
        seen = set()
        for cell in suggested:
            if cell in remaining_set and cell not in seen:
                seen.add(cell); result.append(cell)
                self._set_content(cell[0], cell[1], marker)
        return result

    def _place_default_coins(self, remaining, reserve_traps):
        min_coins = 5 if self.rows >= 15 and self.cols >= 15 else 1
        min_traps = 3 if (reserve_traps and self.rows >= 15 and self.cols >= 15) else (1 if reserve_traps else 0)
        rc = len(remaining)
        if rc < min_coins + min_traps:
            if rc >= 2 and reserve_traps:
                min_coins = min(min_coins, rc - 1); min_traps = min(min_traps, rc - min_coins)
            else:
                min_coins = min(min_coins, rc); min_traps = 0
        max_cc = max(min_coins, rc // 5)
        coin_count = self.random.randint(min_coins, max(min_coins, min(rc - min_traps, max_cc)))
        if coin_count > 0:
            cells = self.random.sample(remaining, coin_count)
            for row, col in cells:
                self._set_content(row, col, SYMBOLS["coin"])
            return [c for c in remaining if c not in set(cells)]
        return remaining

    def _place_default_traps(self, remaining):
        min_traps = 3 if self.rows >= 15 and self.cols >= 15 else 1
        rc = len(remaining)
        if rc <= 0:
            return
        trap_min = min(min_traps, rc)
        trap_max = min(rc, max(min_traps, rc // 8))
        trap_count = self.random.randint(trap_min, trap_max)
        if trap_count > 0:
            for row, col in self.random.sample(remaining, trap_count):
                self._set_content(row, col, SYMBOLS["trap"])

    def _find_farthest_pair(self, open_cells):
        start = open_cells[0]
        farthest, _ = self._bfs_farthest(start)
        other, parent = self._bfs_farthest(farthest)
        path = self._reconstruct_path(parent, farthest, other)
        return farthest, other, path

    def _bfs_farthest(self, source):
        queue = deque([source])
        parent: dict = {source: None}
        farthest = source
        while queue:
            row, col = queue.popleft()
            farthest = (row, col)
            for nr, nc in self._neighbors(row, col):
                if (nr, nc) not in parent:
                    parent[(nr, nc)] = (row, col)
                    queue.append((nr, nc))
        return farthest, parent

    def _reconstruct_path(self, parent, start, end):
        path = [end]
        cur = end
        while cur != start:
            prev = parent.get(cur)
            if prev is None:
                break
            path.append(prev); cur = prev
        path.reverse()
        return path

    # ========================================================================
    #  Grid helpers
    # ========================================================================

    def _neighbors(self, row, col):
        result = []
        for nr, nc in ((row-1, col), (row+1, col), (row, col-1), (row, col+1)):
            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                if self.grid[nr][nc].walkable:
                    result.append((nr, nc))
        return result

    def _collect_open_cells(self):
        return [(r, c) for r in range(self.rows) for c in range(self.cols)
                if self.grid[r][c].walkable]

    def _set_content(self, row, col, content):
        if 0 <= row < self.rows and 0 <= col < self.cols:
            self.grid[row][col].content = content

    def _open_cell(self, row, col):
        self._set_content(row, col, SYMBOLS["floor"])

    @property
    def boss_count(self) -> int:
        return len(self.bosses)
