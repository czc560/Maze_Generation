"""玩家状态。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PlayerState:
    """玩家状态结构。"""

    position: tuple[int, int]
    hp: int = 100
    coin: int = 0
    collected_coins: int = 0
    triggered_traps: int = 0
    skill_cooldowns: dict[str, int] = field(default_factory=dict)
    in_boss_battle: bool = False
    path: list[tuple[int, int]] = field(default_factory=list)
    score: int = 0
    steps: int = 0
    direction: str = "DOWN"
