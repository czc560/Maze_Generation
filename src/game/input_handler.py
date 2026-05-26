"""键盘输入处理。"""


def pygame_key_to_action(key) -> str | None:
    """将 pygame 按键映射到动作；未安装 pygame 时也能被安全导入。"""
    try:
        import pygame
    except Exception:
        return None
    mapping = {
        pygame.K_UP: "UP",
        pygame.K_w: "UP",
        pygame.K_DOWN: "DOWN",
        pygame.K_s: "DOWN",
        pygame.K_LEFT: "LEFT",
        pygame.K_a: "LEFT",
        pygame.K_RIGHT: "RIGHT",
        pygame.K_d: "RIGHT",
        pygame.K_SPACE: "USE_SKILL",
    }
    return mapping.get(key)
