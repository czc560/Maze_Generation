"""基础 UI 组件。"""

from __future__ import annotations


class Button:
    """简单 pygame 按钮。"""

    def __init__(self, rect, text, callback=None):
        self.rect = rect
        self.text = text
        self.callback = callback

    def draw(self, screen, font):
        try:
            import pygame
        except Exception:
            return
        pygame.draw.rect(screen, (70, 90, 130), self.rect)
        pygame.draw.rect(screen, (230, 230, 230), self.rect, 2)
        label = font.render(self.text, True, (255, 255, 255))
        screen.blit(label, label.get_rect(center=self.rect.center))

    def handle_event(self, event):
        try:
            import pygame
        except Exception:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            if self.callback:
                self.callback()
            return True
        return False
