from __future__ import annotations

import json
import os
from typing import Any


DEFAULT_ASSETS: dict[str, Any] = {
    "symbols": {
        "wall": "#",
        "floor": ".",
        "start": "S",
        "end": "E",
        "boss": "B",
        "coin": "C",
        "trap": "T",
    },
    "values": {
        "coin": 50,
        "trap": -30,
    },
    "colors": {
        "wall": "#2b2b2b",
        "floor": "#e3e3e3",
        "start": "#009dff",
        "end": "#2fff00",
        "boss": "#756bb1",
        "coin": "#fdae6b",
        "trap": "#920000",
        "visited": "#b7d7e8",
        "ai": "#ffd43b",
    },
}

GAME_RULES: dict[str, Any] = {
    "boss_hp": [11, 13, 9, 15],
    "player_skills": [[8, 4], [2, 0], [4, 2], [6, 3]],
    "min_rounds": 20,
    "coin_consumption": 5,
}


def _merge_assets(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = {
        "symbols": dict(base.get("symbols", {})),
        "values": dict(base.get("values", {})),
        "colors": dict(base.get("colors", {})),
    }
    for key in ("symbols", "values", "colors"):
        result[key].update(override.get(key, {}))
    return result


def load_assets(path: str | None = None) -> dict[str, Any]:
    if path is None:
        here = os.path.dirname(__file__)
        path = os.path.abspath(os.path.join(here, "..", "assets", "maze_assets.json"))

    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, dict):
            return _merge_assets(DEFAULT_ASSETS, data)
    except OSError:
        pass
    except json.JSONDecodeError:
        pass

    return dict(DEFAULT_ASSETS)


ASSETS = load_assets()
