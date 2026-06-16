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


# ============================================================================
#  Skill sequence verification — CLI grading support
# ============================================================================


def simulate_skill_sequence(
    boss_hp_list: list[int],
    player_skills: list[list[int]],
    skill_sequence: list[int],
) -> dict[str, Any]:
    """Simulate a given skill sequence against a gauntlet of bosses.

    Cooldown model (consistent with ``simulate_battle`` / ``optimal_skill_dp``):
      1. Tick all cooldowns down by 1 (min 0)
      2. Check if the chosen skill is ready (cd == 0); error if not
      3. Apply damage
      4. Set the used skill's cooldown = skill_cd + 1
      5. When a boss is defeated, cooldowns reset and next boss starts

    ``skill_sequence[i] == -1`` means "wait" (skip this turn, no damage).

    Returns a dict with keys:
        legal, turns_used, total_damage_dealt, bosses_defeated,
        bosses_total, errors, boss_details.
    """
    # Short-circuit: empty boss list is trivially legal
    if not boss_hp_list:
        return {
            "legal": True,
            "turns_used": 0,
            "total_damage_dealt": 0,
            "bosses_defeated": 0,
            "bosses_total": 0,
            "errors": [],
            "boss_details": [],
        }

    n_skills = len(player_skills)
    cooldowns: list[int] = [0] * n_skills
    boss_idx = 0
    boss_hp_left = boss_hp_list[0]
    total_damage = 0
    turns_used = 0
    boss_details: list[dict[str, Any]] = []
    errors: list[str] = []

    boss_turns = 0

    for step, skill_idx in enumerate(skill_sequence):
        # ---- 1. Tick cooldowns ------------------------------------------------
        for i in range(n_skills):
            if cooldowns[i] > 0:
                cooldowns[i] -= 1

        # ---- 2. Wait action --------------------------------------------------
        if skill_idx == -1:
            turns_used += 1
            boss_turns += 1
            continue

        # ---- 3. Validate skill index -----------------------------------------
        if skill_idx < 0 or skill_idx >= n_skills:
            errors.append(
                f"第{step + 1}回合: 技能下标 {skill_idx} 无效 "
                f"(有效范围 0~{n_skills - 1})"
            )
            break

        # ---- 4. Check cooldown -----------------------------------------------
        if cooldowns[skill_idx] > 0:
            errors.append(
                f"第{step + 1}回合: 技能#{skill_idx + 1} "
                f"冷却中 (还需 {cooldowns[skill_idx]} 回合)"
            )
            break

        # ---- 5. Apply damage -------------------------------------------------
        damage = max(0, player_skills[skill_idx][0])
        boss_hp_left -= damage
        total_damage += damage
        cooldowns[skill_idx] = player_skills[skill_idx][1] + 1
        turns_used += 1
        boss_turns += 1

        # ---- 6. Boss defeated? -----------------------------------------------
        if boss_hp_left <= 0:
            boss_details.append({
                "boss_index": boss_idx,
                "hp": boss_hp_list[boss_idx],
                "turns": boss_turns,
                "defeated": True,
            })
            boss_idx += 1
            if boss_idx >= len(boss_hp_list):
                break  # all bosses defeated!
            boss_hp_left = boss_hp_list[boss_idx]
            # NOTE: cooldowns persist across bosses — do NOT reset.
            boss_turns = 0

    # ---- Post-simulation checks ----------------------------------------------
    if boss_idx < len(boss_hp_list) and not errors:
        # Sequence ended before all bosses were defeated
        errors.append(
            f"序列耗尽但 Boss#{boss_idx + 1} 仍有 {max(0, boss_hp_left)} HP, "
            f"共击败 {boss_idx}/{len(boss_hp_list)} 个Boss"
        )
        # Record the unfinished boss
        boss_details.append({
            "boss_index": boss_idx,
            "hp": boss_hp_list[boss_idx],
            "turns": boss_turns,
            "defeated": False,
            "hp_remaining": max(0, boss_hp_left),
        })

    legal = len(errors) == 0

    return {
        "legal": legal,
        "turns_used": turns_used,
        "total_damage_dealt": total_damage,
        "bosses_defeated": boss_idx,
        "bosses_total": len(boss_hp_list),
        "errors": errors,
        "boss_details": boss_details,
    }


def _optimal_skill_dp_continuous(
    boss_hp_list: list[int],
    player_skills: list[list[int]],
) -> list[int]:
    """DP for multi-boss gauntlet with cooldowns persisting across bosses.

    Returns the optimal skill-index sequence (including -1 for waits).
    Uses memoized recursion over (boss_idx, hp_left, cds_tuple).
    """
    n_skills = len(player_skills)
    if not boss_hp_list:
        return []

    from functools import lru_cache

    @lru_cache(maxsize=None)
    def solve(
        boss_idx: int,
        hp_left: int,
        cds: tuple[int, ...],
    ) -> tuple[int, int | None]:
        """Return (min_turns_from_here, best_action_now).

        best_action_now: skill index (0..n-1), -1 (wait), or None (done).
        """
        if boss_idx >= len(boss_hp_list):
            return (0, None)  # done

        ticked = tuple(max(0, c - 1) for c in cds)
        best_turns = 10**9
        best_action: int | None = -1  # default to wait

        # Try each available skill
        for i in range(n_skills):
            if ticked[i] == 0:
                new_hp = hp_left - player_skills[i][0]
                new_cds = list(ticked)
                new_cds[i] = player_skills[i][1] + 1
                new_cds_t = tuple(new_cds)

                if new_hp <= 0:
                    # Boss defeated → advance to next boss, cd persists
                    next_idx = boss_idx + 1
                    next_hp = (
                        boss_hp_list[next_idx]
                        if next_idx < len(boss_hp_list)
                        else 0
                    )
                    t, _ = solve(next_idx, next_hp, new_cds_t)
                else:
                    t, _ = solve(boss_idx, new_hp, new_cds_t)

                if t + 1 < best_turns:
                    best_turns = t + 1
                    best_action = i

        # Wait option — only if no skill is available (to avoid infinite loops)
        if best_action == -1:
            t, _ = solve(boss_idx, hp_left, ticked)
            if t + 1 < best_turns:
                best_turns = t + 1
                # best_action stays -1

        return (best_turns, best_action)

    # ---- Reconstruct optimal sequence ----------------------------------------
    seq: list[int] = []
    boss_idx = 0
    hp_left = boss_hp_list[0]
    cds: tuple[int, ...] = tuple([0] * n_skills)

    while boss_idx < len(boss_hp_list):
        _, action = solve(boss_idx, hp_left, cds)
        if action is None:
            break
        # Tick (matching DP internal tick)
        cds = tuple(max(0, c - 1) for c in cds)
        seq.append(action)
        if action >= 0:
            hp_left -= player_skills[action][0]
            cds_l = list(cds)
            cds_l[action] = player_skills[action][1] + 1
            cds = tuple(cds_l)
        # action == -1: wait, cds already ticked above
        if hp_left <= 0:
            boss_idx += 1
            if boss_idx < len(boss_hp_list):
                hp_left = boss_hp_list[boss_idx]
                # cooldowns PERSIST — do NOT reset!

    return seq


def check_sequence_optimality(
    boss_hp_list: list[int],
    player_skills: list[list[int]],
    skill_sequence: list[int],
) -> dict[str, Any]:
    """Check whether *skill_sequence* is a minimum-turn optimal sequence.

    Simulates the given sequence, then compares its turn count against
    the theoretical optimum computed via continuous DP (cooldowns persist
    across bosses — consistent with the evaluation system).

    Returns a dict with keys:
        legal, is_optimal, turns_used, optimal_turns, total_damage_dealt,
        bosses_defeated, bosses_total, errors, boss_details,
        optimal_sequence (reference optimal skill indices, with -1 for waits).
    """
    # ---- 1. Simulate the given sequence (cooldowns persist across bosses) ----
    sim = simulate_skill_sequence(boss_hp_list, player_skills, skill_sequence)

    if not sim["legal"]:
        return {
            **sim,
            "is_optimal": False,
            "optimal_turns": -1,
            "optimal_sequence": [],
        }

    # ---- 2. Compute optimal with continuous DP (cooldowns persist) -----------
    optimal_seq = _optimal_skill_dp_continuous(boss_hp_list, player_skills)
    total_optimal_turns = len(optimal_seq)

    # ---- 3. Annotate boss_details with per-boss optimal (from continuous) ----
    # Split the continuous optimal sequence into per-boss segments
    boss_idx = 0
    hp_left = boss_hp_list[0] if boss_hp_list else 0
    cds: tuple[int, ...] = tuple([0] * len(player_skills))
    segment_start = 0

    for i, action in enumerate(optimal_seq):
        cds = tuple(max(0, c - 1) for c in cds)
        if action >= 0:
            hp_left -= player_skills[action][0]
            cds_l = list(cds)
            cds_l[action] = player_skills[action][1] + 1
            cds = tuple(cds_l)
        if hp_left <= 0 and boss_idx < len(boss_hp_list):
            # Record this boss's segment
            segment = optimal_seq[segment_start : i + 1]
            for d in sim["boss_details"]:
                if d["boss_index"] == boss_idx:
                    d["optimal_turns"] = len(segment)
                    d["optimal_sequence"] = segment
                    break
            segment_start = i + 1
            boss_idx += 1
            if boss_idx < len(boss_hp_list):
                hp_left = boss_hp_list[boss_idx]

    # ---- 4. Check optimality -------------------------------------------------
    extra_entries = len(skill_sequence) - sim["turns_used"]
    is_optimal = (
        sim["turns_used"] == total_optimal_turns
        and extra_entries == 0
    )

    if extra_entries > 0:
        sim.setdefault("errors", []).append(
            f"序列有 {extra_entries} 个多余条目（Boss已全部击败，不计入回合数）"
        )

    return {
        **sim,
        "is_optimal": is_optimal,
        "optimal_turns": total_optimal_turns,
        "optimal_sequence": optimal_seq,
    }
