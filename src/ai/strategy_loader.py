"""AI 策略加载器。"""

from __future__ import annotations

import importlib.util
from pathlib import Path

from src.ai.base_strategy import BaseAIStrategy
from src.ai.greedy_strategy import GreedyStrategy
from src.ai.ppo_strategy import PPOStrategy
from src.ai.qlearning_strategy import QLearningStrategy


def load_strategy(name: str, custom_strategy: str | None = None) -> BaseAIStrategy:
    """按名称或路径加载策略。"""
    name = (name or "greedy").lower()
    if name == "greedy":
        return GreedyStrategy()
    if name == "ppo":
        return PPOStrategy()
    if name in {"qlearning", "ql", "rl"}:
        return QLearningStrategy()
    if name == "custom":
        if not custom_strategy:
            raise ValueError("custom 策略需要 --custom-strategy 路径")
        path = Path(custom_strategy)
        spec = importlib.util.spec_from_file_location("custom_strategy_module", path)
        if spec is None or spec.loader is None:
            raise ValueError(f"无法加载自定义策略: {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if hasattr(module, "create_strategy"):
            return module.create_strategy()
        for obj in module.__dict__.values():
            try:
                if isinstance(obj, type) and issubclass(obj, BaseAIStrategy) and obj is not BaseAIStrategy:
                    return obj()
            except TypeError:
                continue
        raise ValueError("自定义策略文件中没有 BaseAIStrategy 子类或 create_strategy")
    raise ValueError(f"未知 AI 策略: {name}")
