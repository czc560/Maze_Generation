"""动画管理器。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AnimationClip:
    frames: list
    fps: int = 8
    loop: bool = True
    playing: bool = True
    time_acc: float = 0.0
    index: int = 0


class AnimationManager:
    """管理 player_idle、player_move、boss_idle 及事件动画。"""

    def __init__(self):
        self.animations: dict[str, AnimationClip] = {}

    def register_animation(self, name: str, frames: list, fps: int = 8, loop: bool = True):
        """注册动画。"""
        self.animations[name] = AnimationClip(frames or [None], fps=fps, loop=loop)

    def play(self, name: str):
        """播放动画。"""
        if name in self.animations:
            self.animations[name].playing = True

    def stop(self, name: str):
        """停止动画。"""
        if name in self.animations:
            self.animations[name].playing = False

    def update(self, dt: float):
        """更新所有动画。"""
        for clip in self.animations.values():
            if not clip.playing or not clip.frames:
                continue
            clip.time_acc += dt
            frame_time = 1.0 / max(clip.fps, 1)
            while clip.time_acc >= frame_time:
                clip.time_acc -= frame_time
                clip.index += 1
                if clip.index >= len(clip.frames):
                    clip.index = 0 if clip.loop else len(clip.frames) - 1
                    if not clip.loop:
                        clip.playing = False

    def get_current_frame(self, name: str):
        """返回当前帧。"""
        clip = self.animations.get(name)
        if not clip or not clip.frames:
            return None
        return clip.frames[clip.index]

    def draw(self, screen, name: str, position):
        """绘制当前帧。"""
        frame = self.get_current_frame(name)
        if frame is not None and screen is not None:
            screen.blit(frame, position)
