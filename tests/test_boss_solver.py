from src.boss.boss_branch_bound import solve_boss_battle


def test_boss_solver_new_format():
    config = {
        "B": [5, 6],
        "PlayerSkills": [
            {"name": "普通攻击", "damage": 2, "cooldown": 0, "cost": 0},
            {"name": "火球术", "damage": 5, "cooldown": 2, "cost": 0},
        ],
        "minRouds": 20,
        "CoinConsumption": 5,
    }
    result = solve_boss_battle(config)
    assert result["min_rounds"] is not None
    assert result["boss_defeat_rounds"]
    assert result["success_within_limit"]


def test_boss_solver_old_format():
    config = {
        "B": [5],
        "PlayerSkills": [[5, 2], [2, 0]],
        "minRouds": 10,
        "CoinConsumption": 5,
    }
    result = solve_boss_battle(config)
    assert result["min_rounds"] is not None
    assert result["round_details"]
