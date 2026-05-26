"""图片素材管理器。"""

from __future__ import annotations

from pathlib import Path


class AssetManager:
    """加载图片、文件夹帧动画和精灵图；缺失素材时降级为占位图。"""

    def __init__(self):
        self.images = {}
        self.animations = {}
        try:
            import pygame
            self.pygame = pygame
            if not pygame.get_init():
                pygame.init()
        except Exception:
            self.pygame = None

    def _placeholder(self, size=(32, 32)):
        if self.pygame is None:
            return None
        surf = self.pygame.Surface(size)
        surf.fill((180, 180, 180))
        return surf

    def load_image(self, name, path):
        """加载单张图片。"""
        path = Path(path)
        if self.pygame is None or not path.exists():
            self.images[name] = self._placeholder()
            return self.images[name]
        try:
            image = self.pygame.image.load(str(path)).convert_alpha()
        except Exception:
            image = self._placeholder()
        self.images[name] = image
        return image

    def get_image(self, name):
        """获取图片；不存在时返回占位图。"""
        return self.images.get(name) or self._placeholder()

    def load_folder(self, folder_path, animation_name=None):
        """加载文件夹中的 png/jpg 帧。"""
        folder = Path(folder_path)
        frames = []
        if folder.exists():
            for p in sorted(folder.glob("*.png")) + sorted(folder.glob("*.jpg")) + sorted(folder.glob("*.jpeg")):
                frames.append(self.load_image(p.stem, p))
        if not frames:
            frames = [self._placeholder()]
        if animation_name:
            self.animations[animation_name] = frames
        return frames

    def scale_image(self, image, size):
        """缩放图片。"""
        if self.pygame is None or image is None:
            return image
        return self.pygame.transform.scale(image, size)

    def load_sprite_sheet(self, name, path, rows: int, cols: int, frame_width: int | None = None, frame_height: int | None = None):
        """从 rows×cols 精灵图切帧。"""
        if self.pygame is None or not Path(path).exists():
            frames = [self._placeholder() for _ in range(rows * cols)]
            self.animations[name] = frames
            return frames
        sheet = self.pygame.image.load(str(path)).convert_alpha()
        sw, sh = sheet.get_size()
        fw = frame_width or sw // cols
        fh = frame_height or sh // rows
        frames = []
        for r in range(rows):
            for c in range(cols):
                rect = self.pygame.Rect(c * fw, r * fh, fw, fh)
                frame = self.pygame.Surface((fw, fh), self.pygame.SRCALPHA)
                frame.blit(sheet, (0, 0), rect)
                frames.append(frame)
        self.animations[name] = frames
        return frames

    def get_animation_frames(self, animation_name):
        """获取动画帧列表。"""
        return self.animations.get(animation_name, [self._placeholder()])
