"""资源路径可视化。"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from src.visualization.maze_visualizer import _matrix


def draw_resource_path(grid, path, title: str, save_path: str | Path) -> Path:
    """绘制资源最优路径。"""
    save_path = Path(save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    arr = _matrix(grid)
    plt.figure(figsize=(7, 7))
    plt.imshow(arr, interpolation="nearest")
    if path:
        pts = np.array(path)
        plt.plot(pts[:, 1], pts[:, 0], linewidth=2)
    plt.title(title)
    plt.xticks([])
    plt.yticks([])
    plt.tight_layout()
    plt.savefig(save_path, dpi=160)
    plt.close()
    return save_path
