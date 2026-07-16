from __future__ import annotations

from game.battle.rules import (
    _optimal_skill_dp_continuous,
    check_sequence_optimality,
    optimal_skill_sequence,
    simulate_boss_gauntlet,
    simulate_skill_sequence,
)


def test_optimal_sequence_remains_legal_and_minimal() -> None:
    bosses = [20, 35]
    skills = [[5, 0], [10, 2]]
    sequence = _optimal_skill_dp_continuous(bosses, skills)

    assert sequence == [0, 1, 0, 0, 1, 0, 0, 1]
    assert optimal_skill_sequence(bosses, skills) == sequence
    assert simulate_skill_sequence(bosses, skills, sequence) == {
        "legal": True,
        "turns_used": 8,
        "total_damage_dealt": 55,
        "bosses_defeated": 2,
        "bosses_total": 2,
        "errors": [],
        "boss_details": [
            {"boss_index": 0, "hp": 20, "turns": 3, "defeated": True},
            {"boss_index": 1, "hp": 35, "turns": 5, "defeated": True},
        ],
    }


def test_documented_sequence_is_still_rejected_as_non_optimal() -> None:
    result = check_sequence_optimality(
        [20, 35], [[5, 0], [10, 2]], [0, 1, 0, 0, 1]
    )
    assert result["legal"] is False
    assert result["is_optimal"] is False
    assert result["bosses_defeated"] == 1


def test_gauntlet_revive_consumes_resources_once_per_restart() -> None:
    result = simulate_boss_gauntlet(
        boss_hp_list=[50],
        skills=[[10, 0]],
        round_limit=2,
        coin_total=5,
        coin_consumption=5,
    )
    events = [entry["event"] for entry in result["log"]]
    assert events.count("revive") == 1
    assert events[-1] == "fail"
    assert result["coins_left"] == 0
