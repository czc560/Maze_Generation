from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "tests" / "golden"


CASES = (
    (
        "solve_require_end_utf8",
        ("solve_maze.py", "best_maze_design_林士清.json", "--require-end"),
        None,
    ),
    (
        "solve_require_end_out_utf8",
        (
            "solve_maze.py",
            "best_maze_design_林士清.json",
            "--require-end",
            "--out",
            "result.json",
        ),
        "result.json",
    ),
    (
        "generate_mst_utf8",
        (
            "solve_maze.py",
            "--generate",
            "15",
            "15",
            "--seed",
            "42",
            "--method",
            "mst",
            "--out",
            "mst.json",
        ),
        "mst.json",
    ),
    (
        "generate_backtracking_utf8",
        (
            "solve_maze.py",
            "--generate",
            "15",
            "15",
            "--seed",
            "42",
            "--method",
            "backtracking",
            "--out",
            "backtracking.json",
        ),
        "backtracking.json",
    ),
    (
        "generate_divide_conquer_utf8",
        (
            "solve_maze.py",
            "--generate",
            "15",
            "15",
            "--seed",
            "42",
            "--method",
            "divide_conquer",
            "--out",
            "divide_conquer.json",
        ),
        "divide_conquer.json",
    ),
    (
        "generate_branch_bound_utf8",
        (
            "solve_maze.py",
            "--generate",
            "15",
            "15",
            "--seed",
            "42",
            "--method",
            "branch_bound",
            "--out",
            "branch_bound.json",
        ),
        "branch_bound.json",
    ),
    (
        "check_sequence_utf8",
        ("solve_maze.py", "--check-sequence", "input.json"),
        None,
    ),
    (
        "check_sequence_out_utf8",
        (
            "solve_maze.py",
            "--check-sequence",
            "input.json",
            "--out",
            "result.json",
        ),
        "result.json",
    ),
    (
        "optimal_sequence_out_utf8",
        (
            "solve_maze.py",
            "--optimal-sequence",
            "input.json",
            "--out",
            "output.json",
        ),
        "output.json",
    ),
    (
        "optimal_sequence_utf8",
        ("solve_maze.py", "--optimal-sequence", "input.json"),
        "input_optimal.json",
    ),
)


@pytest.mark.parametrize(("name", "args", "output_name"), CASES)
def test_cli_output_is_byte_identical(
    name: str, args: tuple[str, ...], output_name: str | None
) -> None:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    output_path = ROOT / output_name if output_name else None
    if output_path is not None:
        output_path.unlink(missing_ok=True)

    try:
        completed = subprocess.run(
            [sys.executable, *args],
            cwd=ROOT,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        assert completed.returncode == int(
            (GOLDEN / f"{name}.exitcode").read_text(encoding="utf-8")
        )
        assert completed.stdout == (GOLDEN / f"{name}.stdout.bin").read_bytes()
        assert completed.stderr == (GOLDEN / f"{name}.stderr.bin").read_bytes()
        if output_path is not None:
            assert output_path.read_bytes() == (
                GOLDEN / f"{name}.json.bin"
            ).read_bytes()
    finally:
        if output_path is not None:
            output_path.unlink(missing_ok=True)
