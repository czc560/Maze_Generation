from __future__ import annotations

import random
from typing import Any

from .maze import COIN_VALUE, Maze, SYMBOLS
from .strategies import bfs_path


def generate_player_skills(rng: random.Random) -> list[list[int]]:
    skill_count = rng.randint(3, 5)
    normal_damage = rng.randint(3, 6)
    skills = [[normal_damage, 0]]
    for _ in range(skill_count - 1):
        damage = rng.randint(6, 12)
        cooldown = rng.randint(1, 3)
        skills.append([damage, cooldown])
    return skills


def min_turns_to_defeat(hp: int, skills: list[list[int]]) -> int:
    cooldowns = [0 for _ in skills]
    turns = 0
    remaining = max(1, hp)
    while remaining > 0:
        for i, cd in enumerate(cooldowns):
            if cd > 0:
                cooldowns[i] = cd - 1

        available = [i for i, cd in enumerate(cooldowns) if cd == 0]
        if not available:
            turns += 1
            continue

        idx = max(available, key=lambda i: (skills[i][0], -skills[i][1]))
        remaining -= max(0, skills[idx][0])
        cooldowns[idx] = skills[idx][1] + 1
        turns += 1
    return turns


def choose_skill_index(available: list[int], skills: list[list[int]], target_hp: int | None) -> int:
    if target_hp is None:
        return max(available, key=lambda i: (skills[i][0], -skills[i][1]))

    finisher = [i for i in available if skills[i][0] >= target_hp]
    if finisher:
        return min(finisher, key=lambda i: (skills[i][0], skills[i][1]))
    return max(available, key=lambda i: (skills[i][0], -skills[i][1]))


def simulate_battle(hp: int, skills: list[list[int]]) -> list[dict[str, Any]]:
    cooldowns = [0 for _ in skills]
    remaining = max(1, hp)
    turn = 0
    log: list[dict[str, Any]] = []

    while remaining > 0:
        for i, cd in enumerate(cooldowns):
            if cd > 0:
                cooldowns[i] = cd - 1

        available = [i for i, cd in enumerate(cooldowns) if cd == 0]
        if available:
            idx = max(available, key=lambda i: (skills[i][0], -skills[i][1]))
            damage = max(0, skills[idx][0])
            remaining = max(0, remaining - damage)
            cooldowns[idx] = skills[idx][1] + 1
        else:
            idx = None
            damage = 0

        turn += 1
        log.append(
            {
                "turn": turn,
                "skill_index": idx,
                "damage": damage,
                "boss_hp": remaining,
                "cooldowns": list(cooldowns),
            }
        )

    return log


def simulate_boss_gauntlet(
    boss_hp_list: list[int],
    skills: list[list[int]],
    round_limit: int,
    coin_total: int,
    coin_consumption: int,
) -> dict[str, Any]:
    cooldowns = [0 for _ in skills]
    known_hp: list[int | None] = [None for _ in boss_hp_list]
    boss_index = 0
    boss_remaining = boss_hp_list[0] if boss_hp_list else 0
    rounds_used = 0
    coins_left = coin_total
    log: list[dict[str, Any]] = []

    def reset_run() -> None:
        nonlocal cooldowns, boss_index, boss_remaining, rounds_used
        cooldowns = [0 for _ in skills]
        boss_index = 0
        boss_remaining = boss_hp_list[0] if boss_hp_list else 0
        rounds_used = 0

    while boss_index < len(boss_hp_list):
        if rounds_used >= round_limit:
            if coins_left >= coin_consumption:
                coins_left -= coin_consumption
                log.append(
                    {
                        "event": "revive",
                        "coins_left": coins_left,
                        "known_hp": list(known_hp),
                    }
                )
                reset_run()
                continue
            log.append(
                {
                    "event": "fail",
                    "boss_index": boss_index,
                    "boss_hp": boss_remaining,
                    "coins_left": coins_left,
                }
            )
            break

        for i, cd in enumerate(cooldowns):
            if cd > 0:
                cooldowns[i] = cd - 1

        available = [i for i, cd in enumerate(cooldowns) if cd == 0]
        if not available:
            rounds_used += 1
            log.append(
                {
                    "event": "wait",
                    "round": rounds_used,
                    "boss_index": boss_index,
                    "boss_hp": boss_remaining,
                    "cooldowns": list(cooldowns),
                    "known_hp": list(known_hp),
                }
            )
            continue

        target_hp = known_hp[boss_index]
        skill_index = choose_skill_index(available, skills, target_hp)
        damage = max(0, skills[skill_index][0])
        boss_remaining = max(0, boss_remaining - damage)
        cooldowns[skill_index] = skills[skill_index][1] + 1
        rounds_used += 1

        log.append(
            {
                "event": "attack",
                "round": rounds_used,
                "boss_index": boss_index,
                "skill_index": skill_index,
                "damage": damage,
                "boss_hp": boss_remaining,
                "cooldowns": list(cooldowns),
                "known_hp": list(known_hp),
            }
        )

        if boss_remaining <= 0:
            known_hp[boss_index] = boss_hp_list[boss_index]
            log.append(
                {
                    "event": "defeat",
                    "round": rounds_used,
                    "boss_index": boss_index,
                    "boss_hp": 0,
                    "known_hp": list(known_hp),
                }
            )
            boss_index += 1
            if boss_index < len(boss_hp_list):
                boss_remaining = boss_hp_list[boss_index]
                cooldowns = [0 for _ in skills]

    return {
        "log": log,
        "coins_left": coins_left,
        "rounds_used": rounds_used,
        "known_hp": known_hp,
        "boss_remaining": boss_remaining if boss_index < len(boss_hp_list) else 0,
        "boss_index": boss_index,
    }


def count_coins(maze: Maze) -> int:
    count = 0
    for row in range(maze.rows):
        for col in range(maze.cols):
            if maze.grid[row][col].content == SYMBOLS["coin"]:
                count += 1
    return count


def generate_game_rules(maze: Maze) -> dict[str, Any]:
    seed = maze.seed if maze.seed is not None else random.randint(0, 2**31 - 1)
    rng = random.Random(seed)

    skills = generate_player_skills(rng)

    path = []
    if maze.start is not None and maze.end is not None:
        path = bfs_path(maze, maze.start, maze.end)
    path_steps = max(0, len(path) - 1)

    boss_count = 0
    if maze.boss is not None:
        boss_count = max(1, min(4, max(1, path_steps // 10)))
    max_damage = max(skill[0] for skill in skills)
    min_damage = max(1, min(skill[0] for skill in skills))

    boss_hp: list[int] = []
    boss_turns: list[int] = []
    for _ in range(boss_count):
        target_turns = rng.randint(3, 6)
        hp_low = max(1, min_damage * 2)
        hp_high = max(hp_low + 1, max_damage * target_turns)
        hp = rng.randint(hp_low, hp_high)
        boss_hp.append(hp)
        boss_turns.append(min_turns_to_defeat(hp, skills))

    optimal_rounds = path_steps + sum(boss_turns)
    min_rounds = max(1, int(optimal_rounds * rng.uniform(0.85, 0.98)))

    coin_total = count_coins(maze) * COIN_VALUE
    coin_consumption = max(1, coin_total // max(1, boss_count)) if boss_count else 1

    return {
        "boss_hp": boss_hp,
        "player_skills": skills,
        "min_rounds": min_rounds,
        "coin_consumption": coin_consumption,
        "player_hp": 100,
    }
