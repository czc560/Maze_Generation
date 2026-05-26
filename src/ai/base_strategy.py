"""AI 策略基础接口。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from src.utils.constants import ACTIONS


class BaseAIStrategy(ABC):
    """AI 策略基类。"""

    name = "base"

    def reset(self, maze, player_state) -> None:
        """重置策略内部状态。"""

    @abstractmethod
    def choose_action(self, maze, player_state) -> str:
        """选择一个动作。"""

    def update(self, transition: dict[str, Any]) -> None:
        """接收环境转移，用于学习型策略。"""

    def available_actions(self) -> list[str]:
        """返回动作空间。"""
        return ACTIONS[:]
