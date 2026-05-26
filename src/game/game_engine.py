"""游戏核心逻辑。"""

from __future__ import annotations

from src.boss.boss_branch_bound import solve_boss_battle
from src.game.game_state import GameState
from src.game.player_state import PlayerState
from src.game.scoring import compute_score
from src.maze.maze import Maze
from src.maze.maze_validator import find_start_end
from src.utils.constants import WALL, COIN, TRAP, BOSS, END, ROAD, MOVE_DELTAS


class MazeGameEngine:
    """迷宫游戏引擎，支持人工/AI 移动、资源触发与 BOSS 战。"""

    def __init__(self, maze: Maze | dict | list[list[str]], boss_config: dict | None = None):
        if isinstance(maze, Maze):
            grid = maze.copy_grid()
        elif isinstance(maze, dict):
            grid = Maze.from_dict(maze).copy_grid()
        else:
            grid = [row[:] for row in maze]
        start, _end = find_start_end(grid)
        if start is None:
            raise ValueError("迷宫缺少起点 S")
        self.state = GameState(grid=grid)
        self.player_state = PlayerState(position=start, path=[start])
        self.boss_config = boss_config or {
            "B": [11],
            "PlayerSkills": [
                {"name": "普通攻击", "damage": 2, "cooldown": 0, "cost": 0},
                {"name": "火球术", "damage": 8, "cooldown": 4, "cost": 2},
            ],
            "minRouds": 20,
            "CoinConsumption": 5,
        }
        self.history: list[dict] = []

    @property
    def grid(self):
        return self.state.grid

    def log(self, message: str) -> None:
        """添加游戏日志。"""
        self.state.logs.append(message)
        self.state.logs = self.state.logs[-8:]

    def move_player(self, action: str) -> dict:
        """执行一个玩家动作。"""
        if self.state.paused or self.state.game_over:
            return {"moved": False, "event": "paused_or_over"}

        if action == "USE_SKILL":
            if self.player_state.in_boss_battle:
                result = solve_boss_battle(self.boss_config)
                self.player_state.in_boss_battle = False
                self.player_state.coin -= result.get("coin_consumption", 0)
                self.log(f"BOSS 战结束：{result.get('min_rounds')} 回合")
                return {"moved": False, "event": "boss_battle", "boss_result": result}
            return {"moved": False, "event": "no_boss"}

        dr, dc = MOVE_DELTAS.get(action, (0, 0))
        if action in MOVE_DELTAS and action != "WAIT":
            self.player_state.direction = action
        r, c = self.player_state.position
        nr, nc = r + dr, c + dc
        if not (0 <= nr < len(self.grid) and 0 <= nc < len(self.grid[0])):
            return {"moved": False, "event": "out_of_bounds"}
        if self.grid[nr][nc] == WALL:
            self.player_state.steps += 1
            self.log("撞墙")
            return {"moved": False, "event": "wall"}

        self.player_state.position = (nr, nc)
        self.player_state.path.append((nr, nc))
        self.player_state.steps += 1
        event = "move"
        cell = self.grid[nr][nc]

        if cell == COIN:
            self.player_state.coin += 50
            self.player_state.collected_coins += 1
            self.grid[nr][nc] = ROAD
            self.log("收集金币 +50")
            event = "coin"
        elif cell == TRAP:
            self.player_state.hp -= 30
            self.player_state.triggered_traps += 1
            self.grid[nr][nc] = ROAD
            self.log("触发陷阱 -30 HP")
            event = "trap"
            if self.player_state.hp <= 0:
                self.state.game_over = True
                self.log("玩家失败")
        elif cell == BOSS:
            self.player_state.in_boss_battle = True
            self.grid[nr][nc] = ROAD
            self.log("遭遇 BOSS")
            event = "boss"
        elif cell == END:
            self.state.game_over = True
            self.state.victory = True
            self.log("到达终点，游戏胜利")
            event = "end"

        self.player_state.score = compute_score(
            self.player_state.coin,
            self.player_state.hp,
            self.player_state.steps,
            self.state.victory,
        )
        info = {
            "moved": event not in {"wall", "out_of_bounds"},
            "event": event,
            "position": list(self.player_state.position),
            "hp": self.player_state.hp,
            "coin": self.player_state.coin,
            "score": self.player_state.score,
        }
        self.history.append({"action": action, **info})
        return info

    def step(self, action: str) -> dict:
        """执行一步。"""
        return self.move_player(action)

    def run_ai(self, strategy, max_steps: int = 500) -> dict:
        """使用 AI 策略自动运行。"""
        strategy.reset(self.grid, self.player_state)
        for _ in range(max_steps):
            if self.state.game_over:
                break
            action = strategy.choose_action(self, self.player_state)
            info = self.step(action)
            if info.get("event") == "boss":
                self.step("USE_SKILL")
        return {
            "strategy": getattr(strategy, "name", strategy.__class__.__name__),
            "victory": self.state.victory,
            "steps": self.player_state.steps,
            "score": self.player_state.score,
            "coin": self.player_state.coin,
            "hp": self.player_state.hp,
            "path": [[r, c] for r, c in self.player_state.path],
            "history": self.history,
            "logs": self.state.logs,
        }

    def pause(self) -> None:
        self.state.paused = True

    def resume(self) -> None:
        self.state.paused = False

    def restart(self, maze: Maze | dict | list[list[str]]) -> None:
        """重新加载迷宫。"""
        self.__init__(maze, boss_config=self.boss_config)
