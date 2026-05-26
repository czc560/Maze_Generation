"""BOSS 战分支限界求解器。"""

from __future__ import annotations

import heapq
from dataclasses import dataclass
from typing import Any


@dataclass
class Skill:
    """玩家技能。"""

    name: str
    damage: int
    cooldown: int
    cost: int = 0


def _parse_boss_hps(config: dict) -> list[int]:
    raw = config.get("B", [11, 13, 9, 15])
    if isinstance(raw, list) and raw and all(isinstance(x, (int, float)) for x in raw):
        return [int(x) for x in raw]
    if isinstance(raw, list) and raw and isinstance(raw[0], dict):
        return [int(x.get("hp", 10)) for x in raw]
    return [10]


def _parse_skills(config: dict) -> list[Skill]:
    raw = config.get("PlayerSkills") or []
    skills: list[Skill] = []
    if raw and isinstance(raw[0], dict):
        for i, item in enumerate(raw):
            skills.append(
                Skill(
                    name=str(item.get("name", f"技能{i}")),
                    damage=int(item.get("damage", 1)),
                    cooldown=int(item.get("cooldown", 0)),
                    cost=int(item.get("cost", 0)),
                )
            )
    elif raw and isinstance(raw[0], list):
        names = ["火球术", "普通攻击", "连击", "斩击"]
        for i, item in enumerate(raw):
            damage = int(item[0]) if len(item) > 0 else 1
            cooldown = int(item[1]) if len(item) > 1 else 0
            skills.append(Skill(name=names[i] if i < len(names) else f"技能{i}", damage=damage, cooldown=cooldown))
    if not skills:
        skills = [
            Skill("普通攻击", 2, 0, 0),
            Skill("火球术", 8, 4, 2),
            Skill("连击", 4, 2, 1),
            Skill("斩击", 6, 3, 1),
        ]
    if not any(s.cooldown == 0 for s in skills):
        skills.append(Skill("补充普通攻击", 1, 0, 0))
    return skills


def _boss_damage(config: dict, round_no: int) -> int:
    """根据 BOSS 能力接口计算本回合伤害；没有配置时给轻微默认伤害。"""
    abilities = config.get("BossAbilities") or []
    damage = 1
    for ability in abilities:
        cd = int(ability.get("cooldown", 1) or 1)
        if round_no % cd == 0:
            damage += int(ability.get("damage", 0))
    return damage


def solve_boss_battle(config: dict) -> dict:
    """使用分支限界/优先队列搜索求击败全部 BOSS 的最少回合数。"""
    boss_hps = _parse_boss_hps(config)
    skills = _parse_skills(config)
    min_limit = int(config.get("minRouds", config.get("minRounds", 20)))
    revive_cost = int(config.get("CoinConsumption", 5))
    initial_hp = int(config.get("PlayerHP", 100))
    initial_coin = int(config.get("PlayerCoin", 20))
    max_damage = max(max(s.damage for s in skills), 1)

    start = (0, 0, boss_hps[0], tuple([0] * len(skills)), initial_hp, initial_coin, 0)
    heap: list[tuple[int, int, tuple]] = []
    heapq.heappush(heap, (0, 0, start))
    dist = {start[1:]: 0}
    parent: dict[tuple, tuple[tuple, int, dict[str, Any]]] = {}
    searched = 0
    pruned = 0
    best_rounds = None
    best_state = None
    process: list[dict] = []
    tie_counter = 0
    max_nodes = 200000

    while heap and searched < max_nodes:
        rounds, _tie, state = heapq.heappop(heap)
        searched += 1
        _, boss_idx, cur_hp, cds, player_hp, coin, revive_count = state
        if boss_idx >= len(boss_hps):
            best_rounds = rounds
            best_state = state
            break

        remaining_hp = cur_hp + sum(boss_hps[boss_idx + 1 :])
        lower_bound = (remaining_hp + max_damage - 1) // max_damage
        if best_rounds is not None and rounds + lower_bound >= best_rounds:
            pruned += 1
            continue

        available = [(i, s) for i, s in enumerate(skills) if cds[i] == 0 and s.cost <= coin]
        if not available:
            available = [(i, s) for i, s in enumerate(skills) if s.cooldown == 0 and s.cost <= coin]

        available.sort(key=lambda item: (-item[1].damage, item[1].cooldown, item[1].cost))

        for skill_idx, skill in available:
            next_round = rounds + 1
            hp_after = cur_hp - skill.damage
            next_boss_idx = boss_idx
            next_hp = hp_after
            defeated = False
            if hp_after <= 0:
                defeated = True
                next_boss_idx += 1
                next_hp = boss_hps[next_boss_idx] if next_boss_idx < len(boss_hps) else 0

            next_cds = list(cds)
            for i in range(len(next_cds)):
                next_cds[i] = max(0, next_cds[i] - 1)
            next_cds[skill_idx] = max(next_cds[skill_idx], skill.cooldown)

            next_coin = coin - skill.cost
            next_player_hp = player_hp
            if not defeated:
                next_player_hp -= _boss_damage(config, next_round)

            next_revive = revive_count
            if next_player_hp <= 0:
                if next_coin >= revive_cost:
                    next_coin -= revive_cost
                    next_player_hp = initial_hp
                    next_revive += 1
                else:
                    pruned += 1
                    continue

            next_state = (
                next_round,
                next_boss_idx,
                next_hp,
                tuple(next_cds),
                next_player_hp,
                next_coin,
                next_revive,
            )
            key = next_state[1:]
            if dist.get(key, 10**9) <= next_round:
                pruned += 1
                continue
            dist[key] = next_round
            detail = {
                "round": next_round,
                "boss_index": boss_idx,
                "skill_index": skill_idx,
                "skill_name": skill.name,
                "damage": skill.damage,
                "boss_remaining_hp": max(0, hp_after),
                "player_hp": next_player_hp,
                "player_coin": next_coin,
                "defeated": defeated,
            }
            parent[next_state] = (state, skill_idx, detail)
            if len(process) < 200:
                process.append(detail)
            tie_counter += 1
            heapq.heappush(heap, (next_round, tie_counter, next_state))

    if best_state is None:
        return {
            "min_rounds": None,
            "skill_sequence": [],
            "round_details": [],
            "boss_defeat_rounds": [],
            "success_within_limit": False,
            "need_revive": False,
            "coin_consumption": 0,
            "searched_nodes": searched,
            "pruned_nodes": pruned,
            "process": process,
            "message": "未能在搜索节点上限内求解",
        }

    details_rev: list[dict] = []
    seq_rev: list[int] = []
    cur = best_state
    while cur != start:
        prev, skill_idx, detail = parent[cur]
        details_rev.append(detail)
        seq_rev.append(skill_idx)
        cur = prev
    round_details = list(reversed(details_rev))
    skill_sequence = list(reversed(seq_rev))
    defeat_rounds = [d["round"] for d in round_details if d.get("defeated")]
    coin_spent = initial_coin - best_state[5]
    need_revive = best_state[6] > 0

    return {
        "min_rounds": best_rounds,
        "skill_sequence": skill_sequence,
        "round_details": round_details,
        "boss_defeat_rounds": defeat_rounds,
        "success_within_limit": best_rounds is not None and best_rounds <= min_limit,
        "need_revive": need_revive,
        "coin_consumption": max(0, coin_spent),
        "searched_nodes": searched,
        "pruned_nodes": pruned,
        "process": process,
        "skills": [s.__dict__ for s in skills],
        "boss_hps": boss_hps,
        "visualization": {"timeline": round_details, "defeat_rounds": defeat_rounds},
    }
