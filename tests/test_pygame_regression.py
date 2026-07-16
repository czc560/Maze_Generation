from __future__ import annotations

from dataclasses import dataclass, field
from types import SimpleNamespace

import pygame

from game.engine import GameEngine
from game.scene_manager import SceneManager
from game.scenes.base import Scene
from game.scenes.menu import MainMenuScene
from game.scenes.gameplay import GameplayScene


@dataclass
class _EngineStub:
    running: bool = True


@dataclass
class _Lifecycle:
    calls: list[str] = field(default_factory=list)


class _TrackedScene(Scene):
    def __init__(self, manager: SceneManager, name: str, log: _Lifecycle) -> None:
        super().__init__(manager)
        self.name = name
        self.log = log

    def enter(self) -> None:
        self.log.calls.append(f"{self.name}.enter")

    def exit(self) -> None:
        self.log.calls.append(f"{self.name}.exit")

    def pause(self) -> None:
        self.log.calls.append(f"{self.name}.pause")

    def resume(self) -> None:
        self.log.calls.append(f"{self.name}.resume")

    def handle_event(self, event: pygame.event.Event) -> None:
        self.log.calls.append(f"{self.name}.event")

    def update(self, dt: float) -> None:
        self.log.calls.append(f"{self.name}.update")

    def render(self, surface: pygame.Surface) -> None:
        self.log.calls.append(f"{self.name}.render")


def test_scene_manager_lifecycle_order_is_unchanged() -> None:
    manager = SceneManager(_EngineStub())  # type: ignore[arg-type]
    log = _Lifecycle()
    first = _TrackedScene(manager, "first", log)
    second = _TrackedScene(manager, "second", log)

    manager.push(first)
    manager.push(second)
    manager.pop()
    manager.handle_event(pygame.event.Event(pygame.USEREVENT))
    manager.update(0.016)
    manager.render(pygame.Surface((1, 1)))

    assert log.calls == [
        "first.enter",
        "first.pause",
        "second.enter",
        "second.exit",
        "first.resume",
        "first.event",
        "first.update",
        "first.render",
    ]


def test_main_menu_headless_smoke_keeps_window_defaults() -> None:
    engine = GameEngine()
    try:
        scene = MainMenuScene(engine.scene_manager)
        engine.scene_manager.push(scene)
        engine.scene_manager.render(engine.screen)

        assert (engine.width, engine.height) == (1280, 720)
        assert engine.fps == 60
        assert pygame.display.get_caption()[0] == "Maze Explorer"
        assert engine.scene_manager.current is scene
    finally:
        pygame.quit()


def test_asset_placeholder_and_cache_are_stable() -> None:
    pygame.init()
    pygame.display.set_mode((1, 1))
    try:
        from game.assets.manager import AssetManager

        manager = AssetManager()
        first = manager.get_image("definitely_missing", (19, 23))
        second = manager.get_image("definitely_missing", (19, 23))
        assert first is second
        assert first.get_size() == (19, 23)
        assert manager.get_sound("definitely_missing") is None
    finally:
        pygame.quit()


def test_boss_result_resume_writes_resources_before_results() -> None:
    engine = GameEngine()
    try:
        scene = GameplayScene(engine.scene_manager, config={"seed": 42})
        scene._player = SimpleNamespace(resources=100)  # type: ignore[assignment]

        scene._boss_battle_result = {
            "victory": True,
            "coins_remaining": 65,
        }
        scene.resume()
        assert scene._player.resources == 65
        assert scene._boss_battle_result is None

        results_calls: list[bool] = []
        scene._goto_results = lambda player_lost=False: results_calls.append(player_lost)  # type: ignore[method-assign]
        scene._boss_battle_result = {
            "victory": False,
            "coins_remaining": 25,
        }
        scene.resume()
        assert scene._player.resources == 25
        assert results_calls == [True]
    finally:
        pygame.quit()
