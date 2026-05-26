"""贪婪 AI 策略。"""

from __future__ import annotations

from collections import deque

from src.ai.base_strategy import BaseAIStrategy
from src.maze.maze_metrics import normalize_grid, neighbors4
from src.utils.constants import COIN, END, BOSS


class GreedyStrategy(BaseAIStrategy):
    """优先寻找最近金币，没有金币则前往终点/BOSS。"""

    name = "greedy"

    def _find_targets(self, grid, symbols: set[str]) -> list[tuple[int, int]]:
        return [(r, c) for r, row in enumerate(grid) for c, ch in enumerate(row) if ch in symbols]

    def _bfs_to_targets(self, grid, start, targets: set[tuple[int, int]], avoid_traps: bool = True):
        q = deque([start])
        parent = {start: None}
        while q:
            cur = q.popleft()
            if cur in targets:
                path = []
                while cur is not None:
                    path.append(cur)
                    cur = parent[cur]
                return list(reversed(path))
            for nxt in neighbors4(grid, *cur, avoid_traps=avoid_traps):
                if nxt not in parent:
                    parent[nxt] = cur
                    q.append(nxt)
        if avoid_traps:
            return self._bfs_to_targets(grid, start, targets, avoid_traps=False)
        return []

    def choose_action(self, maze, player_state) -> str:
        """根据当前位置规划到最近目标的下一步动作。"""
        grid = normalize_grid(maze.grid if hasattr(maze, "grid") else maze)
        pos = tuple(player_state.position)
        if player_state.in_boss_battle:
            return "USE_SKILL"

        coins = set(self._find_targets(grid, {COIN}))
        end_or_boss = set(self._find_targets(grid, {END, BOSS}))
        if coins:
            path = self._bfs_to_targets(grid, pos, coins, avoid_traps=True)
        else:
            path = self._bfs_to_targets(grid, pos, end_or_boss, avoid_traps=False)

        if len(path) < 2:
            return "WAIT"
        nr, nc = path[1]
        r, c = pos
        if nr < r:
            return "UP"
        if nr > r:
            return "DOWN"
        if nc < c:
            return "LEFT"
        if nc > c:
            return "RIGHT"
        return "WAIT"
