"""项目常量。"""

from __future__ import annotations

WALL = "#"
ROAD = "."
START = "S"
END = "E"
COIN = "G"
TRAP = "T"
BOSS = "B"

WALKABLE = {ROAD, START, END, COIN, TRAP, BOSS}
RESOURCE_VALUES = {
    ROAD: 0,
    START: 0,
    END: 0,
    BOSS: 0,
    COIN: 50,
    TRAP: -30,
}

ACTIONS = ["UP", "DOWN", "LEFT", "RIGHT", "WAIT", "USE_SKILL"]
MOVE_DELTAS = {
    "UP": (-1, 0),
    "DOWN": (1, 0),
    "LEFT": (0, -1),
    "RIGHT": (0, 1),
    "WAIT": (0, 0),
}

CARDINAL_DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]
CARVE_DIRS_2 = [(-2, 0), (2, 0), (0, -2), (0, 2)]


def normalize_size(size: int) -> int:
    """将迷宫尺寸规范化：不小于 5，且必须为奇数。"""
    size = max(5, int(size))
    if size % 2 == 0:
        size += 1
    return size
