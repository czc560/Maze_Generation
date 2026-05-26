"""BOSS 战可视化。"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def draw_boss_timeline(boss_result: dict, save_path: str | Path) -> Path:
    """绘制 BOSS 战伤害时间线。"""
    save_path = Path(save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    details = boss_result.get("round_details", [])
    rounds = [d.get("round", i + 1) for i, d in enumerate(details)]
    damage = [d.get("damage", 0) for d in details]
    plt.figure(figsize=(8, 4))
    plt.plot(rounds, damage, marker="o")
    plt.title("Boss Battle Damage Timeline")
    plt.xlabel("Round")
    plt.ylabel("Damage")
    plt.tight_layout()
    plt.savefig(save_path, dpi=160)
    plt.close()
    return save_path
