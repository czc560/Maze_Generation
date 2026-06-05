"""BFS pathfinding, distance maps, and visibility helpers for maze navigation."""

from __future__ import annotations

from collections import deque

from game.maze.symbols import SYMBOLS, COIN_VALUE, TRAP_VALUE


def bfs_path(maze, start: tuple[int, int], end: tuple[int, int]) -> list[tuple[int, int]]:
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


def get_main_path(maze) -> list[tuple[int, int]]:
    if maze.start is None or maze.end is None:
        return []
    return bfs_path(maze, maze.start, maze.end)


def distance_map(maze, start: tuple[int, int]) -> dict[tuple[int, int], int]:
    q: deque[tuple[int, int]] = deque([start])
    dist: dict[tuple[int, int], int] = {start: 0}
    while q:
        cell = q.popleft()
        for nxt in maze._neighbors(*cell):
            if nxt not in dist:
                dist[nxt] = dist[cell] + 1
                q.append(nxt)
    return dist


def distance_to_end_map(maze) -> dict[tuple[int, int], int]:
    if maze.end is None:
        return {}
    return distance_map(maze, maze.end)


def optimal_path_max_coins(maze, detour_limit: int = 12, coin_mask_limit: int = 16) -> list[tuple[int, int]]:
    if maze.start is None or maze.end is None:
        return []
    start, end = maze.start, maze.end
    start_dist = distance_map(maze, start)
    if end not in start_dist:
        return []
    end_dist = distance_to_end_map(maze)
    shortest_len = start_dist[end]

    coins: list[tuple[int, int]] = []
    for row in range(maze.rows):
        for col in range(maze.cols):
            if maze.grid[row][col].content == SYMBOLS["coin"]:
                cell = (row, col)
                if cell in start_dist and cell in end_dist:
                    detour = start_dist[cell] + end_dist[cell] - shortest_len
                    if detour <= detour_limit:
                        coins.append(cell)
    coins.sort(key=lambda c: start_dist[c] + end_dist[c] - shortest_len)
    if len(coins) > coin_mask_limit:
        coins = coins[:coin_mask_limit]

    coin_index = {cell: idx for idx, cell in enumerate(coins)}

    def coin_mask_for(cell):
        idx = coin_index.get(cell)
        return 0 if idx is None else 1 << idx

    max_steps = shortest_len + detour_limit
    start_mask = coin_mask_for(start)
    start_state = (start, start_mask)

    queue: deque = deque([start_state])
    steps_map: dict = {start_state: 0}
    parent: dict = {}
    best_state = None
    best_coins = -1

    while queue:
        pos, mask = queue.popleft()
        steps = steps_map[(pos, mask)]
        if steps > max_steps:
            continue
        if pos == end:
            coins_collected = mask.bit_count()
            if coins_collected > best_coins:
                best_state = (pos, mask)
                best_coins = coins_collected
        if steps == max_steps:
            continue
        for nxt in maze._neighbors(*pos):
            next_mask = mask | coin_mask_for(nxt)
            state = (nxt, next_mask)
            if state in steps_map:
                continue
            steps_map[state] = steps + 1
            parent[state] = (pos, mask)
            queue.append(state)

    if best_state is None:
        return bfs_path(maze, start, end)

    path = []
    cur_state = best_state
    while cur_state != start_state:
        path.append(cur_state[0])
        cur_state = parent[cur_state]
    path.append(start)
    path.reverse()
    return path


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def visible_cells(maze, pos: tuple[int, int]) -> list[tuple[int, int]]:
    row, col = pos
    cells: list[tuple[int, int]] = []
    for r in range(row - 1, row + 2):
        for c in range(col - 1, col + 2):
            if 0 <= r < maze.rows and 0 <= c < maze.cols:
                if maze.grid[r][c].walkable:
                    cells.append((r, c))
    return cells


def shortest_visible_value(maze, start: tuple[int, int], targets: set, max_depth: int = 4) -> float:
    if not targets:
        return 0.0
    q: deque = deque([(start, 0)])
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


def _distance_to_path_map(maze, path: list[tuple[int, int]]) -> dict[tuple[int, int], int]:
    if not path:
        return {}
    q: deque = deque(path)
    dist: dict[tuple[int, int], int] = {cell: 0 for cell in path}
    while q:
        cell = q.popleft()
        for nxt in maze._neighbors(*cell):
            if nxt not in dist:
                dist[nxt] = dist[cell] + 1
                q.append(nxt)
    return dist
