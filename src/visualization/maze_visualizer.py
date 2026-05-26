"""迷宫静态可视化。"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from src.maze.maze_metrics import normalize_grid


SYMBOL_TO_VALUE = {
    "#": 0,
    ".": 1,
    "S": 2,
    "E": 3,
    "G": 4,
    "T": 5,
    "B": 6,
}


def _matrix(grid):
    g = normalize_grid(grid)
    return np.array([[SYMBOL_TO_VALUE.get(ch, 1) for ch in row] for row in g])


def draw_maze(grid, title: str = "Maze", save_path: str | Path = "maze.png") -> Path:
    """绘制迷宫矩阵。"""
    save_path = Path(save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    arr = _matrix(grid)
    plt.figure(figsize=(7, 7))
    plt.imshow(arr, interpolation="nearest")
    plt.title(title)
    plt.xticks([])
    plt.yticks([])
    plt.tight_layout()
    plt.savefig(save_path, dpi=160)
    plt.close()
    return save_path


def draw_maze_comparison(results: list[dict], save_path: str | Path) -> Path:
    """绘制算法评分对比。"""
    save_path = Path(save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    names = [r.get("algorithm", r.get("name", "?")) for r in results]
    scores = [r.get("score", r.get("metrics", {}).get("shortest_path_length", 0)) for r in results]
    plt.figure(figsize=(8, 4))
    plt.bar(names, scores)
    plt.title("Maze Algorithm Comparison")
    plt.ylabel("Score")
    plt.tight_layout()
    plt.savefig(save_path, dpi=160)
    plt.close()
    return save_path


def draw_runtime_comparison(metrics: list[dict], save_path: str | Path) -> Path:
    """绘制运行时间对比。"""
    save_path = Path(save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    names = [m.get("algorithm", "?") for m in metrics]
    values = [m.get("runtime_seconds", 0) for m in metrics]
    plt.figure(figsize=(8, 4))
    plt.bar(names, values)
    plt.title("Runtime Comparison")
    plt.ylabel("Seconds")
    plt.tight_layout()
    plt.savefig(save_path, dpi=160)
    plt.close()
    return save_path


def draw_metric_comparison(metrics: list[dict], save_path: str | Path) -> Path:
    """绘制分支与死胡同指标对比。"""
    save_path = Path(save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    names = [m.get("algorithm", "?") for m in metrics]
    branches = [m.get("branches", 0) for m in metrics]
    dead_ends = [m.get("dead_ends", 0) for m in metrics]
    x = np.arange(len(names))
    width = 0.35
    plt.figure(figsize=(9, 4))
    plt.bar(x - width / 2, branches, width, label="Branches")
    plt.bar(x + width / 2, dead_ends, width, label="Dead Ends")
    plt.xticks(x, names)
    plt.title("Maze Metrics Comparison")
    plt.legend()
    plt.tight_layout()
    plt.savefig(save_path, dpi=160)
    plt.close()
    return save_path
