"""Optimal resource-collection path via tree-DP on perfect mazes.

A perfect maze is a tree — no cycles. The optimal S→E walk that maximises
resource collection is equivalent to finding the maximum-weight connected
subtree that contains both S and E. This module solves that in O(V) using
a single bottom-up DP pass over the BFS tree rooted at S.

Usage::

    from game.maze.optimal_path import compute_optimal_path
    result = compute_optimal_path(maze)
    print(result.max_resource, result.path)
"""

from __future__ import annotations

import collections
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from game.maze.symbols import SYMBOLS, COIN_VALUE, TRAP_VALUE

if TYPE_CHECKING:
    from game.maze.generator import Maze

_DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))


# ============================================================================
#  Result types
# ============================================================================


@dataclass
class OptimalPathResult:
    """Result of optimal resource-collection path computation."""

    max_resource: int          # maximum net resource (excluding S, E)
    path: list[tuple[int, int]]  # S→E walk (may revisit cells)
    visited_cells: set[tuple[int, int]]  # deduplicated cells in the subtree
    coins_in_path: int         # number of coins collected
    traps_in_path: int         # number of traps triggered
    is_optimal: bool           # guaranteed global-optimal? (True for trees)
    note: str = ""


# ============================================================================
#  Maze helpers (adapt the game Maze to the solver's needs)
# ============================================================================


def _walkable(maze: Maze, r: int, c: int) -> bool:
    return 0 <= r < maze.rows and 0 <= c < maze.cols and maze.grid[r][c].walkable


def _neighbors(maze: Maze, r: int, c: int) -> list[tuple[int, int]]:
    return maze._neighbors(r, c)


def _cell_value(maze, cell: tuple[int, int]) -> int:
    """Return the resource value of *cell* (excluding S/E)."""
    ch = maze.grid[cell[0]][cell[1]].content
    # Support JSONMaze coin/trap charsets, fall back to game SYMBOLS
    if hasattr(maze, "_coin_chars"):
        if ch in maze._coin_chars:   # type: ignore[union-attr]
            return COIN_VALUE
        if ch in maze._trap_chars:   # type: ignore[union-attr]
            return TRAP_VALUE
    else:
        if ch == SYMBOLS["coin"]:
            return COIN_VALUE
        if ch == SYMBOLS["trap"]:
            return TRAP_VALUE
    return 0


def _is_coin(maze, cell: tuple[int, int]) -> bool:
    ch = maze.grid[cell[0]][cell[1]].content
    if hasattr(maze, "_coin_chars"):
        return ch in maze._coin_chars  # type: ignore[union-attr]
    return ch == SYMBOLS["coin"]


def _is_trap(maze, cell: tuple[int, int]) -> bool:
    ch = maze.grid[cell[0]][cell[1]].content
    if hasattr(maze, "_trap_chars"):
        return ch in maze._trap_chars  # type: ignore[union-attr]
    return ch == SYMBOLS["trap"]


# ============================================================================
#  BFS tree builder
# ============================================================================


def _bfs_tree(maze: Maze):
    """BFS from S, returning parent/children/order and tree-ness check.

    Returns:
        parent: dict mapping cell → parent (None for S)
        children: defaultdict(list) mapping cell → list of child cells
        order: top-down BFS order (root=S first)
        is_tree: True if the walkable cells form a tree (no cycles, fully connected)
        reachable: number of cells reachable from S
        total_walkable: total walkable cells in the maze
    """
    s = maze.start
    parent: dict[tuple[int, int], tuple[int, int] | None] = {s: None}
    order: list[tuple[int, int]] = [s]
    q = collections.deque([s])
    edge_count = 0

    while q:
        u = q.popleft()
        for v in _neighbors(maze, *u):
            edge_count += 1
            if v not in parent:
                parent[v] = u
                order.append(v)
                q.append(v)

    edge_count //= 2  # each undirected edge counted twice
    children = collections.defaultdict(list)
    for v, p in parent.items():
        if p is not None:
            children[p].append(v)

    reachable = len(parent)
    total_walkable = sum(
        1 for r in range(maze.rows) for c in range(maze.cols)
        if maze.grid[r][c].walkable
    )
    is_tree = (edge_count == reachable - 1) and (reachable == total_walkable)

    return parent, children, order, is_tree, reachable, total_walkable


# ============================================================================
#  Tree DP
# ============================================================================


def _solve_tree_dp(maze: Maze, require_end: bool) -> OptimalPathResult:
    """Core tree-DP solver. Assumes the maze is a tree.

    When require_end=True:  walk must start at S and end at E.
    When require_end=False: walk may start/end anywhere — finds the
        globally optimal connected subtree and produces a covering walk.
    """
    parent, children, order, _, _, _ = _bfs_tree(maze)
    s, e = maze.start, maze.end

    # ---- Bottom-up DP: best[u] = value(u) + Σ max(0, best[c]) ----
    best: dict[tuple[int, int], int] = {}
    for u in reversed(order):
        val = _cell_value(maze, u)
        for c in children[u]:
            val += max(0, best[c])
        best[u] = val

    # ---- Select included cells -----------------------------------------
    if not require_end:
        # Free start/end: find the globally optimal subtree.
        max_node = max(best, key=best.get)  # type: ignore[arg-type]

        included: set[tuple[int, int]] = set()

        def collect(u: tuple[int, int]) -> None:
            included.add(u)
            for c in children[u]:
                if best[c] > 0:
                    collect(c)

        collect(max_node)

        # Total resource = sum of all cell values in the subtree
        total = sum(_cell_value(maze, u) for u in included)

        # Walk: DFS from max_node, each child branch entered and returned from
        walk: list[tuple[int, int]] = []

        def dfs_walk(u: tuple[int, int]) -> None:
            walk.append(u)
            for c in children[u]:
                if c in included:
                    dfs_walk(c)
                    walk.append(u)  # return to u

        dfs_walk(max_node)

        coins = sum(1 for u in included if _is_coin(maze, u))
        traps = sum(1 for u in included if _is_trap(maze, u))

        return OptimalPathResult(
            max_resource=total,
            path=walk,
            visited_cells=included,
            coins_in_path=coins,
            traps_in_path=traps,
            is_optimal=True,
            note=f"完美迷宫(树): 树形DP, 全局最优。起点={max_node}",
        )

    # ---- require_end=True: walk must start at S, end at E --------------

    # Backbone S → E
    backbone: list[tuple[int, int]] = []
    cur = e
    while cur is not None:
        backbone.append(cur)
        cur = parent.get(cur)  # type: ignore[arg-type]
    backbone.reverse()

    # Map each backbone cell to its next-toward-E child
    nxt_toward_e: dict[tuple[int, int], tuple[int, int] | None] = {}
    for i in range(len(backbone) - 1):
        nxt_toward_e[backbone[i]] = backbone[i + 1]
    nxt_toward_e[backbone[-1]] = None

    included = set(backbone)

    def grow(u: tuple[int, int]) -> None:
        included.add(u)
        for c in children[u]:
            if best[c] > 0:
                grow(c)

    for u in backbone:
        for c in children[u]:
            if c == nxt_toward_e.get(u):
                continue  # backbone child handled separately
            if best[c] > 0:
                grow(c)

    # Total resource (excluding S, E)
    total = sum(_cell_value(maze, u) for u in included if u not in (s, e))

    # Build actual S→E walk
    walk: list[tuple[int, int]] = []

    def dfs(u: tuple[int, int]) -> None:
        walk.append(u)
        exit_child = nxt_toward_e.get(u)
        kids = [c for c in children[u] if c in included]
        # Visit non-exit children first (go & return)
        for c in kids:
            if c == exit_child:
                continue
            dfs(c)
            walk.append(u)  # backtrack to u
        # Visit exit child last (no return)
        if exit_child is not None and exit_child in kids:
            dfs(exit_child)

    dfs(s)

    coins = sum(1 for u in included if _is_coin(maze, u))
    traps = sum(1 for u in included if _is_trap(maze, u))

    return OptimalPathResult(
        max_resource=total,
        path=walk,
        visited_cells=included,
        coins_in_path=coins,
        traps_in_path=traps,
        is_optimal=True,
        note="完美迷宫(树): 树形DP, 结果为全局最优。",
    )


# ============================================================================
#  Public API
# ============================================================================


def compute_optimal_path(
    maze: Maze,
    require_end: bool = False,
) -> OptimalPathResult:
    """Compute the optimal resource-collection path.

    For perfect mazes (trees) the result is guaranteed globally optimal.
    For non-tree mazes a warning is included and the result uses the BFS
    spanning tree — still legal but not guaranteed optimal.

    Args:
        maze: A game ``Maze`` instance with start/end set.
        require_end: If True, the walk must start at S and end at E.
            If False (default), start/end can be anywhere — finds the
            globally optimal connected subtree.

    Returns:
        OptimalPathResult with max_resource, path, visited_cells, etc.
    """
    if maze.start is None or maze.end is None:
        raise ValueError("Maze must have both start and end cells")

    parent, _children, _order, is_tree, _reachable, total = _bfs_tree(maze)

    if maze.end not in parent and require_end:
        raise ValueError("终点 E 不可从起点 S 到达, 迷宫不连通。")

    if not is_tree:
        # Non-tree: solve on BFS spanning tree (legal but sub-optimal possible)
        result = _solve_tree_dp(maze, require_end)
        result.is_optimal = False
        result.note = (
            f"警告: 该迷宫不是完美迷宫(可走格 {total}, 但存在环)。"
            "已在 BFS 生成树上求解, 结果合法但不保证全局最优; "
            "请与助教确认迷宫是否应为完美迷宫。"
        )
        return result

    return _solve_tree_dp(maze, require_end)


def verify_path(
    maze: Maze,
    path: list[tuple[int, int]],
    require_end: bool = False,
) -> dict:
    """Replay a walk and validate legality + recompute resource value.

    Useful as a self-check before submitting to an evaluation system.

    Returns a dict with keys:
        legal (bool), resource (int), coins (int), traps (int),
        steps (int), errors (list[str]),
        starts_at_S (bool), ends_at_E (bool)
    """
    errors: list[str] = []
    path = [tuple(p) for p in path]

    if not path:
        return {
            "legal": False, "resource": 0, "coins": 0, "traps": 0,
            "steps": 0, "errors": ["路径为空"],
            "starts_at_S": False, "ends_at_E": False,
        }

    s, e = maze.start, maze.end
    starts_at_s = (path[0] == s)
    ends_at_e = (path[-1] == e)

    if require_end:
        if not starts_at_s:
            errors.append(f"起点不是 S{s}, 而是 {path[0]}")
        if not ends_at_e:
            errors.append(f"终点不是 E{e}, 而是 {path[-1]}")

    for i, (r, c) in enumerate(path):
        if not _walkable(maze, r, c):
            errors.append(f"第{i}步 {(r, c)} 不可走(越界/墙)")

    for i in range(len(path) - 1):
        (r1, c1), (r2, c2) = path[i], path[i + 1]
        if abs(r1 - r2) + abs(c1 - c2) != 1:
            errors.append(
                f"第{i}→{i + 1}步 {path[i]}→{path[i + 1]} 非四邻相邻移动"
            )

    seen: set[tuple[int, int]] = set()
    resource, coins, traps = 0, 0, 0
    for cell in path:
        if cell in seen:
            continue
        seen.add(cell)
        if cell in (s, e):
            continue
        ch = maze.grid[cell[0]][cell[1]].content
        if _is_coin(maze, cell):
            resource += COIN_VALUE
            coins += 1
        elif _is_trap(maze, cell):
            resource += TRAP_VALUE
            traps += 1

    return {
        "legal": len(errors) == 0,
        "resource": resource,
        "coins": coins,
        "traps": traps,
        "steps": len(path) - 1,
        "errors": errors,
        "starts_at_S": starts_at_s,
        "ends_at_E": ends_at_e,
    }


# ============================================================================
#  JSON maze support — lightweight maze from a 2D char array
# ============================================================================


class _JSONCell:
    """A single cell in a JSON-loaded maze, duck-types MazeNode."""
    __slots__ = ("content", "_walkable")

    def __init__(self, ch: str, walkable: bool) -> None:
        self.content = ch
        self._walkable = walkable

    @property
    def walkable(self) -> bool:
        return self._walkable


class JSONMaze:
    """Lightweight maze loaded from a JSON file (2D char array).

    Duck-types ``game.maze.generator.Maze`` so that all solver functions
    (``compute_optimal_path``, ``verify_path``) work without imports
    from the game layer or pygame.
    """

    def __init__(
        self,
        grid: list[list[str]],
        coin_chars: frozenset | None = None,
        trap_chars: frozenset | None = None,
        wall_char: str = "#",
    ) -> None:
        self.rows = len(grid)
        self.cols = max(len(r) for r in grid) if grid else 0
        self._coin_chars = coin_chars or frozenset({"C", "G"})
        self._trap_chars = trap_chars or frozenset({"T"})
        self._wall_char = wall_char
        self.start: tuple[int, int] | None = None
        self.end: tuple[int, int] | None = None
        self.bosses: list[tuple[int, int]] = []

        self.grid: list[list[_JSONCell]] = []
        for r in range(self.rows):
            row: list[_JSONCell] = []
            for c in range(self.cols):
                ch = grid[r][c] if c < len(grid[r]) else wall_char
                w = ch != wall_char
                row.append(_JSONCell(ch, w))
                if ch == "S":
                    self.start = (r, c)
                elif ch == "E":
                    self.end = (r, c)
                elif ch == "B":
                    self.bosses.append((r, c))
            self.grid.append(row)

    def _neighbors(self, row: int, col: int) -> list[tuple[int, int]]:
        result: list[tuple[int, int]] = []
        for dr, dc in _DIRS:
            nr, nc = row + dr, col + dc
            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                if self.grid[nr][nc].walkable:
                    result.append((nr, nc))
        return result


def load_maze_from_json(source) -> JSONMaze:
    """Load a maze from a JSON file path, dict, or 2D list.

    Handles both ``G`` and ``C`` as coin, ``T`` as trap,
    `` `` and ``.`` as floor.

    Returns a ``JSONMaze`` ready for ``compute_optimal_path``.
    """
    import json

    if isinstance(source, str):
        with open(source, "r", encoding="utf-8") as f:
            data = json.load(f)
    elif isinstance(source, dict):
        data = source
    elif isinstance(source, list):
        data = {"maze": source}
    else:
        raise TypeError(f"Expected path, dict, or list; got {type(source)}")

    maze_field = data["maze"] if isinstance(data, dict) and "maze" in data else data
    grid = _as_char_grid(maze_field)
    return JSONMaze(grid)


def _as_char_grid(maze_field) -> list[list[str]]:
    grid: list[list[str]] = []
    for row in maze_field:
        grid.append(list(row) if isinstance(row, str) else [str(c) for c in row])
    return grid


def export_result(
    maze: JSONMaze,
    result: OptimalPathResult,
    out_path: str | None = None,
) -> dict:
    """Build structured output dict and optionally write to *out_path* as JSON.

    Keys: max_resource, coins_collected, traps_triggered,
          path_length_steps, path_rc, visited_cells_rc,
          is_global_optimal, note, annotated_maze
    """
    ann = [[" "] * maze.cols for _ in range(maze.rows)]
    for r in range(maze.rows):
        for c in range(maze.cols):
            ann[r][c] = maze.grid[r][c].content
    for r, c in result.visited_cells:
        if ann[r][c] not in ("#", "S", "E", "B", "C", "G", "T"):
            ann[r][c] = "*"

    out = {
        "max_resource": result.max_resource,
        "coins_collected": result.coins_in_path,
        "traps_triggered": result.traps_in_path,
        "path_length_steps": len(result.path) - 1,
        "path_rc": [[r, c] for r, c in result.path],
        "visited_cells_rc": sorted([r, c] for r, c in result.visited_cells),
        "is_global_optimal": result.is_optimal,
        "note": result.note,
        "annotated_maze": ["".join(row) for row in ann],
    }

    if out_path:
        import json, os
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)

    return out


# ============================================================================
#  Maze JSON export (game Maze → 2D array JSON matching maze_15_15.json)
# ============================================================================


def game_maze_to_grid(maze) -> list[list[str]]:
    """Convert a game ``Maze`` to a 2D char array.

    Uses ``G`` for coin, ``T`` for trap, space for floor
    (matching the evaluation format from ``maze_15_15.json``).
    """
    from game.maze.symbols import SYMBOLS as GS

    COIN_CH = "G"
    TRAP_CH = "T"
    FLOOR_CH = " "

    grid: list[list[str]] = []
    for r in range(maze.rows):
        row: list[str] = []
        for c in range(maze.cols):
            ch = maze.grid[r][c].content
            if ch == GS["floor"]:
                row.append(FLOOR_CH)
            elif ch == GS["coin"]:
                row.append(COIN_CH)
            elif ch == GS["trap"]:
                row.append(TRAP_CH)
            else:
                row.append(ch)
        grid.append(row)
    return grid


def export_game_maze_json(maze, out_path: str) -> str:
    """Export a game ``Maze`` as JSON in the evaluation format.

    Produces string-row format (no internal JSON commas/quoting in the grid)::

        {"maze": ["###########S###", "#  G T G#    ...", ...]}

    This matches the ``maze_15_15.json`` sample format interpreted as
    string-per-row, which avoids the testing system picking up ``"``
    and ``,`` as maze characters.
    """
    import json, os
    grid = game_maze_to_grid(maze)
    data = {"maze": ["".join(row) for row in grid]}
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return os.path.abspath(out_path)
