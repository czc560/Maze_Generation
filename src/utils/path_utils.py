"""路径工具。"""

from __future__ import annotations

from pathlib import Path


def project_root() -> Path:
    """返回项目根目录。"""
    return Path(__file__).resolve().parents[2]


def ensure_project_dirs(base: str | Path | None = None) -> dict[str, Path]:
    """创建常用输出目录，并返回路径字典。"""
    base_path = Path(base) if base else project_root()
    paths = {
        "figures": base_path / "outputs" / "figures",
        "logs": base_path / "outputs" / "logs",
        "generated_mazes": base_path / "outputs" / "generated_mazes",
        "ai_runs": base_path / "outputs" / "ai_runs",
        "models": base_path / "outputs" / "models",
        "data": base_path / "data",
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    return paths
