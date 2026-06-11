"""Game-wide constants: screen, events, asset keys, default settings."""

# ---------- Screen ----------
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

# Maze display — occupies the left/center; HUD panel on the right
MAZE_AREA_LEFT = 40
MAZE_AREA_TOP = 40
MAZE_AREA_WIDTH = 960
MAZE_AREA_HEIGHT = 640
HUD_PANEL_X = 1020
HUD_PANEL_WIDTH = 240

# ---------- Default maze settings ----------
DEFAULT_ROWS = 15
DEFAULT_COLS = 15
DEFAULT_SEED = 42
DEFAULT_K = 4.0
DEFAULT_METHOD = "mst"

# AI defaults
DEFAULT_AGGRESSION = 0.55
DEFAULT_PROBE_DEPTH = 6
DEFAULT_ROLLOUTS = 6

# ---------- Custom pygame events ----------
import pygame

class GameEvent:
    COLLECT_COIN      = pygame.USEREVENT + 1
    TRIGGER_TRAP      = pygame.USEREVENT + 2
    REACH_END         = pygame.USEREVENT + 3
    ENTER_BOSS_CELL   = pygame.USEREVENT + 4
    BOSS_BATTLE_START = pygame.USEREVENT + 5
    BOSS_BATTLE_OVER  = pygame.USEREVENT + 6
    PLAYER_FINISHED   = pygame.USEREVENT + 7
    BOSS_RETRY        = pygame.USEREVENT + 10  # player spends coins to retry

# ---------- Asset keys ----------
ASSET_WALL         = "wall"
ASSET_FLOOR        = "floor"
ASSET_PLAYER       = "player"
ASSET_COIN         = "coin"
ASSET_TRAP         = "trap"
ASSET_BOSS         = "boss"
ASSET_START        = "start_portal"
ASSET_END          = "end_portal"
ASSET_AI_MARKER    = "ai_marker"
ASSET_FOG          = "fog"            # unexplored fog tile
ASSET_FOG_DIM      = "fog_dim"        # explored-but-out-of-sight dim overlay

# ---------- Sprite asset keys (for AssetManager) ----------
SPRITE_KEYS = [
    ASSET_WALL, ASSET_FLOOR, ASSET_PLAYER, ASSET_COIN,
    ASSET_TRAP, ASSET_BOSS, ASSET_START, ASSET_END,
    ASSET_FOG, ASSET_FOG_DIM,
]

# ---------- Visibility ----------
VISIBILITY_RANGE = 1  # Manhattan distance from player (3×3 area)

# ---------- Colors ----------
COLOR_BG           = (18, 18, 24)
COLOR_HUD_BG       = (30, 30, 40)
COLOR_FOG          = (8, 8, 16, 160)       # unexplored — dark translucent
COLOR_FOG_DIM      = (8, 8, 16, 70)        # explored, outside 3×3 — dim translucent
COLOR_TEXT         = (220, 220, 230)
COLOR_TEXT_DIM     = (140, 140, 160)
COLOR_ACCENT       = (100, 140, 255)
COLOR_GOLD         = (255, 200, 60)
COLOR_RED          = (220, 50, 50)
COLOR_GREEN        = (80, 220, 80)

# Optimal path overlay
COLOR_OPTIMAL_HIGHLIGHT = (255, 215, 0)   # gold — visible cells
COLOR_OPTIMAL_DIM       = (180, 150, 30)  # dim gold — fog-covered cells
COLOR_OPTIMAL_BORDER    = (255, 200, 60)  # gold border
