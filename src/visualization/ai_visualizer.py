"""AI 路径可视化。"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from src.visualization.maze_visualizer import _matrix


def draw_ai_path(grid, ai_path, save_path: str | Path) -> Path:
    """绘制 AI 玩家路径。"""
    save_path = Path(save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    arr = _matrix(grid)
    plt.figure(figsize=(7, 7))
    plt.imshow(arr, interpolation="nearest")
    if ai_path:
        pts = np.array(ai_path)
        plt.plot(pts[:, 1], pts[:, 0], linewidth=2)
    plt.title("AI Player Path")
    plt.xticks([])
    plt.yticks([])
    plt.tight_layout()
    plt.savefig(save_path, dpi=160)
    plt.close()
    return save_path
