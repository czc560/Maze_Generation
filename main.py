"""Maze Explorer — Pygame entry point."""

# Ensure core/ is importable (it's a sibling package)
import sys
import os

ROOT = os.path.dirname(__file__)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from game.engine import GameEngine
from game.scenes.menu import MainMenuScene


def main() -> None:
    engine = GameEngine(title="Maze Explorer")
    engine.run(MainMenuScene)


if __name__ == "__main__":
    main()
