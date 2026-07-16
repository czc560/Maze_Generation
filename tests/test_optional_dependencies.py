from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_dqn_module_imports_without_numpy_or_torch() -> None:
    script = r'''
import builtins

original_import = builtins.__import__

def without_dqn_dependencies(name, *args, **kwargs):
    if name == "numpy" or name == "torch" or name.startswith("torch."):
        raise ImportError(f"blocked optional dependency: {name}")
    return original_import(name, *args, **kwargs)

builtins.__import__ = without_dqn_dependencies
from game.ai import dqn

assert dqn.HAS_TORCH is False
try:
    dqn.DQNAI(object())
except ImportError as error:
    assert str(error) == "DQNAI requires torch. Install: pip install torch"
else:
    raise AssertionError("DQNAI must reject use when torch is unavailable")
'''
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
