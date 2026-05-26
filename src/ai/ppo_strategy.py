"""轻量 PPO 策略框架。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from src.ai.base_strategy import BaseAIStrategy
from src.utils.constants import ACTIONS


class PPOStrategy(BaseAIStrategy):
    """不依赖深度学习库的简化 PPO 风格策略。"""

    name = "ppo"

    def __init__(self, obs_dim: int = 8, seed: int | None = None):
        self.rng = np.random.default_rng(seed)
        self.obs_dim = obs_dim
        self.action_dim = len(ACTIONS)
        self.weights = self.rng.normal(0, 0.05, size=(obs_dim, self.action_dim))
        self.bias = np.zeros(self.action_dim)
        self.buffer: list[dict[str, Any]] = []

    def _obs(self, maze, player_state) -> np.ndarray:
        n = len(maze.grid if hasattr(maze, "grid") else maze)
        r, c = player_state.position
        return np.array(
            [
                r / max(n, 1),
                c / max(n, 1),
                player_state.hp / 100.0,
                player_state.coin / 50.0,
                player_state.collected_coins / 20.0,
                player_state.triggered_traps / 20.0,
                player_state.steps / 500.0,
                1.0 if player_state.in_boss_battle else 0.0,
            ],
            dtype=float,
        )

    def _policy(self, obs: np.ndarray) -> np.ndarray:
        logits = obs @ self.weights + self.bias
        logits = logits - np.max(logits)
        probs = np.exp(logits)
        return probs / np.sum(probs)

    def choose_action(self, maze, player_state) -> str:
        """根据线性策略网络采样动作。"""
        obs = self._obs(maze, player_state)
        probs = self._policy(obs)
        idx = int(self.rng.choice(np.arange(self.action_dim), p=probs))
        return ACTIONS[idx]

    def store_transition(self, transition: dict) -> None:
        """保存经验。"""
        self.buffer.append(transition)

    def update(self, transition: dict) -> None:
        self.store_transition(transition)

    def train(self, learning_rate: float = 0.01, clip_eps: float = 0.2, epochs: int = 2) -> dict:
        """执行简化 PPO 风格策略梯度更新。"""
        if not self.buffer:
            return {"loss": 0.0, "samples": 0}
        losses = []
        for _ in range(epochs):
            for item in self.buffer:
                obs = np.asarray(item.get("obs", np.zeros(self.obs_dim)), dtype=float)
                if obs.shape[0] != self.obs_dim:
                    continue
                action = int(item.get("action_index", 0))
                advantage = float(item.get("advantage", item.get("reward", 0.0)))
                old_prob = float(item.get("old_prob", 1.0 / self.action_dim))
                probs = self._policy(obs)
                ratio = probs[action] / max(old_prob, 1e-8)
                clipped = np.clip(ratio, 1 - clip_eps, 1 + clip_eps)
                scale = -min(ratio * advantage, clipped * advantage)
                grad = probs.copy()
                grad[action] -= 1
                self.weights -= learning_rate * scale * np.outer(obs, grad)
                self.bias -= learning_rate * scale * grad
                losses.append(float(scale))
        self.buffer.clear()
        return {"loss": float(np.mean(losses)) if losses else 0.0, "samples": len(losses)}

    def save_model(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez(path, weights=self.weights, bias=self.bias)

    def load_model(self, path: str | Path) -> None:
        path = Path(path)
        if path.exists():
            data = np.load(path)
            self.weights = data["weights"]
            self.bias = data["bias"]
