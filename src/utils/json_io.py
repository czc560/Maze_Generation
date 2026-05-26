"""JSON 读写工具。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def save_json(data: Any, path: str | Path) -> Path:
    """保存 JSON，并自动创建父目录。"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_json(path: str | Path) -> Any:
    """读取 JSON 文件。"""
    path = Path(path)
    return json.loads(path.read_text(encoding="utf-8"))
