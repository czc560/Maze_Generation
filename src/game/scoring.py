"""计分规则。"""


def compute_score(coin: int, hp: int, steps: int, victory: bool) -> int:
    """简单计分：资源、血量、步数和胜利加成。"""
    return coin + hp - steps + (200 if victory else 0)
