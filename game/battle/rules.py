"""Boss battle simulation, game rules, and optimal skill DP."""

from __future__ import annotations

import random
from functools import lru_cache
from typing import Any

from game.maze.symbols import SYMBOLS, COIN_VALUE
from game.maze.pathfinding import bfs_path


def generate_player_skills(rng: random.Random) -> list[list[int]]:
    skill_count = rng.randint(3, 5)
    normal_damage = rng.randint(3, 6)
    skills = [[normal_damage, 0]]
    for _ in range(skill_count - 1):
        skills.append([rng.randint(6, 12), rng.randint(1, 3)])
    return skills


def min_turns_to_defeat(hp: int, skills: list[list[int]]) -> int:
    cooldowns = [0] * len(skills)
    turns, remaining = 0, max(1, hp)
    while remaining > 0:
        for i, cd in enumerate(cooldowns):
            if cd > 0:
                cooldowns[i] = cd - 1
        available = [i for i, cd in enumerate(cooldowns) if cd == 0]
        if not available:
            turns += 1; continue
        idx = max(available, key=lambda i: (skills[i][0], -skills[i][1]))
        remaining -= max(0, skills[idx][0])
        cooldowns[idx] = skills[idx][1] + 1
        turns += 1
    return turns


def choose_skill_index(available: list[int], skills: list[list[int]], target_hp: int | None) -> int:
    """Pick best skill. If target_hp is known, try to finish efficiently."""
    if target_hp is None:
        return max(available, key=lambda i: (skills[i][0], -skills[i][1]))
    finisher = [i for i in available if skills[i][0] >= target_hp]
    if finisher:
        return min(finisher, key=lambda i: (skills[i][0], skills[i][1]))
    return max(available, key=lambda i: (skills[i][0], -skills[i][1]))


# ============================================================================
#  Optimal skill DP  (used when boss HP is known)
# ============================================================================

def optimal_skill_dp(hp: int, skills: list[list[int]]) -> list[int]:
    """Return optimal skill index sequence to defeat boss with *hp* in minimal turns.

    Uses memoized recursion over (remaining_hp, cooldown_tuple).
    Only called when boss HP is revealed.
    """
    cooldowns = tuple([0] * len(skills))

    @lru_cache(maxsize=None)
    def min_turns_and_next(hp_left: int, cds: tuple[int, ...]) -> tuple[int, int | None]:
        """Returns (min_turns_to_kill, best_skill_index_to_use_now)."""
        if hp_left <= 0:
            return (0, None)

        # Tick cooldowns
        ticked = tuple(max(0, c - 1) for c in cds)

        best_turns = 10**9
        best_idx = None

        for i, cd in enumerate(ticked):
            if cd == 0:
                # Use skill i
                new_hp = hp_left - skills[i][0]
                new_cds = list(ticked)
                new_cds[i] = skills[i][1] + 1  # set cooldown (will be ticked next call)
                turns, _ = min_turns_and_next(new_hp, tuple(new_cds))
                if turns + 1 < best_turns:
                    best_turns = turns + 1
                    best_idx = i

        # Option: wait (skip turn if all on cooldown)
        if best_idx is None:
            turns, _ = min_turns_and_next(hp_left, ticked)
            best_turns = turns + 1
            best_idx = -1  # wait

        return (best_turns, best_idx)

    # Reconstruct optimal sequence
    seq: list[int] = []
    hp_left = hp
    cds = tuple([0] * len(skills))

    while hp_left > 0:
        _, idx = min_turns_and_next(hp_left, cds)
        # Tick
        cds = tuple(max(0, c - 1) for c in cds)
        if idx is None:
            break
        seq.append(idx)
        if idx >= 0:
            hp_left -= skills[idx][0]
            cds_list = list(cds)
            cds_list[idx] = skills[idx][1] + 1
            cds = tuple(cds_list)

    return seq


def optimal_skill_index_for(available: list[int], skills: list[list[int]],
                            hp_left: int) -> int | None:
    """Return the optimal skill to use NOW given known *hp_left*.

    Uses DP to compute full sequence, then returns the first action.
    """
    seq = optimal_skill_dp(hp_left, skills)
    for idx in seq:
        if idx >= 0 and idx in available:
            return idx
    return None


# ============================================================================
#  Battle simulation
# ============================================================================

def simulate_battle(hp: int, skills: list[list[int]]) -> list[dict[str, Any]]:
    cooldowns = [0] * len(skills)
    remaining, turn = max(1, hp), 0
    log: list[dict[str, Any]] = []
    while remaining > 0:
        for i, cd in enumerate(cooldowns):
            if cd > 0: cooldowns[i] = cd - 1
        available = [i for i, cd in enumerate(cooldowns) if cd == 0]
        if available:
            idx = max(available, key=lambda i: (skills[i][0], -skills[i][1]))
            damage = max(0, skills[idx][0])
            remaining = max(0, remaining - damage)
            cooldowns[idx] = skills[idx][1] + 1
        else:
            idx, damage = None, 0
        turn += 1
        log.append({"turn": turn, "skill_index": idx, "damage": damage,
                     "boss_hp": remaining, "cooldowns": list(cooldowns)})
    return log


def simulate_boss_gauntlet(
    boss_hp_list: list[int], skills: list[list[int]],
    round_limit: int, coin_total: int, coin_consumption: int,
) -> dict[str, Any]:
    cooldowns = [0] * len(skills)
    known_hp: list[int | None] = [None] * len(boss_hp_list)
    boss_index, boss_remaining = 0, (boss_hp_list[0] if boss_hp_list else 0)
    rounds_used, coins_left = 0, coin_total
    log: list[dict[str, Any]] = []

    def reset_run():
        nonlocal cooldowns, boss_index, boss_remaining, rounds_used
        cooldowns = [0] * len(skills)
        boss_index = 0
        boss_remaining = boss_hp_list[0] if boss_hp_list else 0
        rounds_used = 0

    while boss_index < len(boss_hp_list):
        if rounds_used >= round_limit:
            if coins_left >= coin_consumption:
                coins_left -= coin_consumption
                log.append({"event": "revive", "coins_left": coins_left, "known_hp": list(known_hp)})
                reset_run(); continue
            log.append({"event": "fail", "boss_index": boss_index, "boss_hp": boss_remaining,
                         "coins_left": coins_left}); break

        for i, cd in enumerate(cooldowns):
            if cd > 0: cooldowns[i] = cd - 1
        available = [i for i, cd in enumerate(cooldowns) if cd == 0]

        if not available:
            rounds_used += 1
            log.append({"event": "wait", "round": rounds_used, "boss_index": boss_index,
                         "boss_hp": boss_remaining, "cooldowns": list(cooldowns),
                         "known_hp": list(known_hp)}); continue

        # Strategy: unknown HP → max damage; known HP → DP optimal
        if known_hp[boss_index] is None:
            idx = max(available, key=lambda i: (skills[i][0], -skills[i][1]))
        else:
            idx = optimal_skill_index_for(available, skills, boss_remaining)
            if idx is None:
                idx = max(available, key=lambda i: (skills[i][0], -skills[i][1]))

        damage = max(0, skills[idx][0])
        boss_remaining = max(0, boss_remaining - damage)
        cooldowns[idx] = skills[idx][1] + 1
        rounds_used += 1

        log.append({"event": "attack", "round": rounds_used, "boss_index": boss_index,
                     "skill_index": idx, "damage": damage, "boss_hp": boss_remaining,
                     "cooldowns": list(cooldowns), "known_hp": list(known_hp)})

        if boss_remaining <= 0:
            known_hp[boss_index] = boss_hp_list[boss_index]
            log.append({"event": "defeat", "round": rounds_used, "boss_index": boss_index,
                         "boss_hp": 0, "known_hp": list(known_hp)})
            boss_index += 1
            if boss_index < len(boss_hp_list):
                boss_remaining = boss_hp_list[boss_index]
                cooldowns = [0] * len(skills)

    return {"log": log, "coins_left": coins_left, "rounds_used": rounds_used,
            "known_hp": known_hp,
            "boss_remaining": boss_remaining if boss_index < len(boss_hp_list) else 0,
            "boss_index": boss_index}


def count_coins(maze) -> int:
    return sum(1 for r in range(maze.rows) for c in range(maze.cols)
               if maze.grid[r][c].content == SYMBOLS["coin"])


def generate_game_rules(maze) -> dict[str, Any]:
    seed = maze.seed if maze.seed is not None else random.randint(0, 2**31 - 1)
    rng = random.Random(seed)
    skills = generate_player_skills(rng)
    path = bfs_path(maze, maze.start, maze.end) if maze.start and maze.end else []
    path_steps = max(0, len(path) - 1)
    boss_count = maze.boss_count if hasattr(maze, 'boss_count') else (1 if maze.boss is not None else 0)
    boss_count = max(1, min(4, max(1, boss_count, path_steps // 10))) if boss_count > 0 else 0
    max_dmg = max(s[0] for s in skills); min_dmg = max(1, min(s[0] for s in skills))
    boss_hp, boss_turns = [], []
    for _ in range(boss_count):
        target_turns = rng.randint(3, 6)
        hp_low = max(1, min_dmg * 2)
        hp_high = max(hp_low + 1, max_dmg * target_turns)
        hp = rng.randint(hp_low, hp_high)
        boss_hp.append(hp)
        boss_turns.append(min_turns_to_defeat(hp, skills))
    optimal_rounds = path_steps + sum(boss_turns)
    min_rounds = max(1, int(optimal_rounds * rng.uniform(0.85, 0.98)))
    coin_total = count_coins(maze) * COIN_VALUE
    coin_consumption = max(1, coin_total // max(1, boss_count)) if boss_count else 1
    return {"boss_hp": boss_hp, "player_skills": skills, "min_rounds": min_rounds,
            "coin_consumption": coin_consumption}
