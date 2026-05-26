"""生成过程可视化辅助。"""

from __future__ import annotations

from pathlib import Path

from src.visualization.maze_visualizer import draw_maze


def draw_generation_process(generation_steps, save_dir: str | Path, every: int = 10) -> list[Path]:
    """将生成过程若干帧保存为图片。"""
    save_dir = Path(save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for i, grid in enumerate(generation_steps):
        if i % every == 0 or i == len(generation_steps) - 1:
            paths.append(draw_maze(grid, f"Generation Step {i}", save_dir / f"step_{i:04d}.png"))
    return paths
