"""BOSS 战状态对象。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BossBattleState:
    """BOSS 战斗状态。"""

    boss_hps: list[int]
    player_hp: int = 100
    player_coin: int = 20
    round_index: int = 0
    boss_index: int = 0
    cooldowns: list[int] = field(default_factory=list)
    finished: bool = False
