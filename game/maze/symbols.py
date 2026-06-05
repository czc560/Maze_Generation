"""Maze cell symbols, values, and method name normalization."""

from game.assets.config import ASSETS

SYMBOLS = ASSETS["symbols"]
COIN_VALUE = ASSETS["values"]["coin"]
TRAP_VALUE = ASSETS["values"]["trap"]

GENERATION_METHODS: dict[str, str] = {
    "mst": "最小生成树算法", "prim": "最小生成树算法",
    "minimum_spanning_tree": "最小生成树算法",
    "backtracking": "回溯法", "dfs": "回溯法",
    "divide_conquer": "分治法", "recursive_division": "分治法", "division": "分治法",
    "branch_bound": "分支限界法", "branch_and_bound": "分支限界法",
}


def normalize_generation_method(method: str | None) -> str:
    if method is None:
        return "mst"
    key = method.strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "最小生成树": "mst", "最小生成树算法": "mst", "mst": "mst",
        "prim": "mst", "minimum_spanning_tree": "mst",
        "回溯": "backtracking", "回溯法": "backtracking", "dfs": "backtracking",
        "depth_first_search": "backtracking", "backtracking": "backtracking",
        "分治": "divide_conquer", "分治法": "divide_conquer",
        "recursive_division": "divide_conquer", "division": "divide_conquer",
        "divide_conquer": "divide_conquer",
        "分支限界": "branch_bound", "分支限界法": "branch_bound",
        "branch_bound": "branch_bound", "branch_and_bound": "branch_bound",
    }
    if key not in aliases:
        valid = ", ".join(sorted({"mst", "backtracking", "divide_conquer", "branch_bound"}))
        raise ValueError(f"Unknown maze generation method: {method!r}. Valid methods: {valid}")
    return aliases[key]
