"""游戏全局状态。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GameState:
    """游戏状态。"""

    grid: list[list[str]]
    running: bool = True
    paused: bool = False
    game_over: bool = False
    victory: bool = False
    logs: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
