"""Maze 数据结构。"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.utils.json_io import save_json


def _to_grid(raw: list[str] | list[list[str]]) -> list[list[str]]:
    """兼容 list[str] 与 list[list[str]] 两种迷宫表达。"""
    if not raw:
        return []
    if isinstance(raw[0], str):
        return [list(row) for row in raw]  # type: ignore[arg-type]
    return [list(row) for row in raw]  # type: ignore[arg-type]


@dataclass
class Maze:
    """迷宫对象，保存矩阵、算法、随机种子、生成步骤与指标。"""

    grid: list[list[str]]
    size: int | None = None
    algorithm: str = "unknown"
    seed: int | None = None
    generation_steps: list[list[list[str]]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    validation: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.grid = _to_grid(self.grid)
        self.size = self.size or len(self.grid)

    def copy_grid(self) -> list[list[str]]:
        """返回迷宫矩阵的深拷贝。"""
        return [row[:] for row in self.grid]

    def to_dict(self) -> dict[str, Any]:
        """序列化为可保存的字典。"""
        return {
            "size": self.size,
            "algorithm": self.algorithm,
            "seed": self.seed,
            "maze": ["".join(row) for row in self.grid],
            "metadata": self.metadata,
            "validation": self.validation,
            "metrics": self.metrics,
            "generation_steps_count": len(self.generation_steps),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Maze":
        """从 JSON 字典恢复 Maze。"""
        return cls(
            grid=_to_grid(data.get("maze") or data.get("grid") or []),
            size=data.get("size"),
            algorithm=data.get("algorithm", "loaded"),
            seed=data.get("seed"),
            metadata=data.get("metadata", {}),
            validation=data.get("validation", {}),
            metrics=data.get("metrics", {}),
        )

    def save_json(self, path: str | Path) -> Path:
        """保存迷宫 JSON。"""
        return save_json(self.to_dict(), path)

    def print_maze(self) -> None:
        """在终端输出迷宫。"""
        for row in self.grid:
            print("".join(row))
