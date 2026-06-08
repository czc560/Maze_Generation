"""AssetManager: loads images, sounds, fonts.
Falls back to PlaceholderGenerator when real files are missing."""

from __future__ import annotations

import os
import pygame

from game.assets.placeholder import PlaceholderGenerator

_SPRITE_DIR = os.path.join(os.path.dirname(__file__), "sprites")
_SOUND_DIR = os.path.join(os.path.dirname(__file__), "sounds")


class AssetManager:
    """Loads and caches game assets.

    - Images: tries ``sprites/{key}.png``, falls back to placeholder generator.
    - Sounds: tries ``sounds/{key}.wav`` then ``.ogg``, returns None if missing.
    - Fonts: tries to load a .ttf from the fonts directory, falls back to system default.
    """

    def __init__(self) -> None:
        self._image_cache: dict[tuple[str, int, int], pygame.Surface] = {}
        self._sound_cache: dict[str, pygame.mixer.Sound | None] = {}
        self._font_cache: dict[tuple[str, int], pygame.font.Font] = {}
        self._placeholder = PlaceholderGenerator()

    # ---- Images -----------------------------------------------------------

    def get_image(self, key: str, size: tuple[int, int] | None = None) -> pygame.Surface:
        """Return a Surface for *key*, optionally scaled to *size*.

        Resolution order:
        1. RAM cache ``(key, w, h)``
        2. File ``sprites/{key}.png``
        3. PlaceholderGenerator
        """
        w, h = size if size is not None else (32, 32)
        cache_key = (key, w, h)

        if cache_key in self._image_cache:
            return self._image_cache[cache_key]

        # Try loading from file
        surface = self._try_load_image(key)
        if surface is None:
            # Generate placeholder
            surface = self._placeholder.generate(key, w, h)

        # Scale to requested size
        if surface.get_width() != w or surface.get_height() != h:
            surface = pygame.transform.scale(surface, (w, h))

        self._image_cache[cache_key] = surface
        return surface

    def _try_load_image(self, key: str) -> pygame.Surface | None:
        filepath = os.path.join(_SPRITE_DIR, f"{key}.png")
        if os.path.isfile(filepath):
            try:
                return pygame.image.load(filepath).convert_alpha()
            except pygame.error:
                pass
        return None

    # ---- Sounds -----------------------------------------------------------

    def get_sound(self, key: str) -> pygame.mixer.Sound | None:
        """Return a Sound for *key*, or None if the file is missing.

        Tries ``{key}.wav`` then ``{key}.ogg``.
        """
        if key in self._sound_cache:
            return self._sound_cache[key]

        for ext in (".wav", ".ogg"):
            filepath = os.path.join(_SOUND_DIR, f"{key}{ext}")
            if os.path.isfile(filepath):
                try:
                    snd = pygame.mixer.Sound(filepath)
                    self._sound_cache[key] = snd
                    return snd
                except pygame.error:
                    pass

        self._sound_cache[key] = None
        return None

    def play_sound(self, key: str, volume: float = 1.0) -> None:
        """Play a sound if available, silently skip otherwise."""
        snd = self.get_sound(key)
        if snd is not None:
            snd.set_volume(volume)
            snd.play()

    # ---- Fonts ------------------------------------------------------------

    def get_font(self, name: str | None, size: int) -> pygame.font.Font:
        """Return a Font. *name* can be a .ttf filename or a system font name."""
        cache_key = (name or "__default__", size)
        if cache_key in self._font_cache:
            return self._font_cache[cache_key]

        if name is not None:
            font_dir = os.path.join(os.path.dirname(__file__), "fonts")
            ttf_path = os.path.join(font_dir, name)
            if os.path.isfile(ttf_path):
                font = pygame.font.Font(ttf_path, size)
                self._font_cache[cache_key] = font
                return font

        # Fall back to system font — try Chinese-capable fonts first.
        # We test with a pure-CJK string: each Chinese glyph should render at
        # roughly the font size in pixels.  Latin-only fallback fonts give tiny
        # widths (tofu boxes), so we require width >= size * len / 3.
        _CJK_TEST = "迷宫探"
        _CJK_FONT_CANDIDATES = [
            "wenquanyimicrohei", "notosanscjksc", "notoserifcjksc",
            "wqymicrohei", "notosanscjk",
            "simhei", "microsoftyahei", "arialunicode", "arial",
        ]
        font = None
        for candidate in _CJK_FONT_CANDIDATES:
            try:
                f = pygame.font.SysFont(candidate, size)
                test_surf = f.render(_CJK_TEST, True, (255, 255, 255))
                # Each Chinese char should be at least size/3 pixels wide
                min_w = max(4, size * len(_CJK_TEST) // 3)
                if test_surf.get_width() >= min_w:
                    font = f
                    break
            except Exception:
                continue

        if font is None:
            # Last resort: try direct .ttc path
            _DIRECT_FONT_PATHS = [
                "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            ]
            for fp in _DIRECT_FONT_PATHS:
                if os.path.isfile(fp):
                    try:
                        font = pygame.font.Font(fp, size)
                        break
                    except Exception:
                        continue

        if font is None:
            font = pygame.font.Font(None, size)

        self._font_cache[cache_key] = font
        return font

    # ---- Cache management -------------------------------------------------

    def clear_image_cache(self) -> None:
        """Clear the image cache (call when cell size changes)."""
        self._image_cache.clear()

    def preload_all(self, cell_size: int) -> None:
        """Eagerly load all known sprite keys to avoid mid-game stutter."""
        from game.constants import SPRITE_KEYS
        for key in SPRITE_KEYS:
            self.get_image(key, (cell_size, cell_size))
