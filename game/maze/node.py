"""MazeNode — a single maze cell."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from game.maze.symbols import SYMBOLS


@dataclass
class MazeNode:
    """A single maze cell."""

    content: str = SYMBOLS["wall"]
    row: int = 0
    col: int = 0
    extra: Any = None
    params: dict[str, Any] = field(default_factory=dict)

    @property
    def walkable(self) -> bool:
        return self.content != SYMBOLS["wall"]

    def __str__(self) -> str:
        return self.content
