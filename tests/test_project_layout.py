from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_asset_sources_and_runtime_assets_have_separate_directories() -> None:
    source_dir = ROOT / "game" / "assets" / "source"
    sprite_dir = ROOT / "game" / "assets" / "sprites"

    assert {path.name for path in source_dir.glob("*.png")} == {
        "boss.png",
        "地板.png",
        "墙.png",
        "陷阱.png",
    }
    assert not list(ROOT.glob("*.png"))
    assert {
        "boss.png",
        "coin.png",
        "floor.png",
        "player.png",
        "trap.png",
        "wall.png",
    }.issubset({path.name for path in sprite_dir.glob("*.png")})


def test_golden_cli_snapshots_live_under_tests() -> None:
    golden_dir = ROOT / "tests" / "golden"
    assert golden_dir.is_dir()
    assert not (ROOT / ".golden_baseline").exists()
    assert list(golden_dir.glob("*_utf8.stdout.bin"))
