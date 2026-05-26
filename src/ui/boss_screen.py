"""BOSS 对战画面与动画接口。"""

from __future__ import annotations


def show_boss_battle_screen(boss_state, player_state):
    """BOSS 对战画面接口。"""
    return {"screen": "boss", "boss_state": boss_state, "player_state": player_state}


def play_skill_animation(skill_name, damage):
    """技能释放动画接口。"""
    return {"type": "skill", "skill_name": skill_name, "damage": damage}


def play_hp_change_animation(target, old_hp, new_hp):
    """血量变化动画接口。"""
    return {"type": "hp_change", "target": target, "old_hp": old_hp, "new_hp": new_hp}
