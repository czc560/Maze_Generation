"""音频管理器。"""

from __future__ import annotations

from pathlib import Path


class AudioManager:
    """BGM 与 SFX 接口；缺少音频文件时不崩溃。"""

    def __init__(self):
        self.bgm = {}
        self.sfx = {}
        self.volume = 0.6
        try:
            import pygame
            self.pygame = pygame
            if not pygame.get_init():
                pygame.init()
            try:
                pygame.mixer.init()
            except Exception:
                pass
        except Exception:
            self.pygame = None

    def load_bgm(self, name, path):
        path = Path(path)
        if path.exists():
            self.bgm[name] = str(path)

    def play_bgm(self, name, loop=True):
        if self.pygame is None or name not in self.bgm:
            return
        try:
            self.pygame.mixer.music.load(self.bgm[name])
            self.pygame.mixer.music.set_volume(self.volume)
            self.pygame.mixer.music.play(-1 if loop else 0)
        except Exception:
            return

    def stop_bgm(self):
        if self.pygame is not None:
            try:
                self.pygame.mixer.music.stop()
            except Exception:
                pass

    def load_sfx(self, name, path):
        path = Path(path)
        if self.pygame is None or not path.exists():
            return
        try:
            sound = self.pygame.mixer.Sound(str(path))
            sound.set_volume(self.volume)
            self.sfx[name] = sound
        except Exception:
            pass

    def play_sfx(self, name):
        sound = self.sfx.get(name)
        if sound is not None:
            try:
                sound.play()
            except Exception:
                pass

    def set_volume(self, volume):
        self.volume = max(0.0, min(1.0, float(volume)))
        for sound in self.sfx.values():
            try:
                sound.set_volume(self.volume)
            except Exception:
                pass
