"""Q-learning 强化学习策略。"""

from __future__ import annotations

import json
import random
from pathlib import Path

from src.ai.base_strategy import BaseAIStrategy
from src.utils.constants import ACTIONS


class QLearningStrategy(BaseAIStrategy):
    """轻量 Q-learning 策略，可训练、保存和加载 Q 表。"""

    name = "qlearning"

    def __init__(self, epsilon: float = 0.15, alpha: float = 0.2, gamma: float = 0.95, seed: int | None = None):
        self.epsilon = epsilon
        self.alpha = alpha
        self.gamma = gamma
        self.rng = random.Random(seed)
        self.q: dict[str, dict[str, float]] = {}

    def _state_key(self, maze, player_state) -> str:
        pos = tuple(player_state.position)
        return f"{pos[0]},{pos[1]}|hp={player_state.hp//10}|coin={min(player_state.coin, 20)//5}"

    def _ensure(self, key: str) -> dict[str, float]:
        if key not in self.q:
            self.q[key] = {a: 0.0 for a in ACTIONS}
        return self.q[key]

    def choose_action(self, maze, player_state) -> str:
        """epsilon-greedy 选择动作。"""
        key = self._state_key(maze, player_state)
        values = self._ensure(key)
        if self.rng.random() < self.epsilon:
            return self.rng.choice(ACTIONS)
        return max(values, key=values.get)

    def update(self, transition: dict) -> None:
        """Q-learning 更新。"""
        s = str(transition.get("state"))
        a = transition.get("action", "WAIT")
        r = float(transition.get("reward", 0.0))
        ns = str(transition.get("next_state"))
        done = bool(transition.get("done", False))
        values = self._ensure(s)
        next_values = self._ensure(ns)
        target = r if done else r + self.gamma * max(next_values.values())
        values[a] = values.get(a, 0.0) + self.alpha * (target - values.get(a, 0.0))

    def save_model(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.q, ensure_ascii=False, indent=2), encoding="utf-8")

    def load_model(self, path: str | Path) -> None:
        path = Path(path)
        if path.exists():
            self.q = json.loads(path.read_text(encoding="utf-8"))
