"""Smoke tests for every user-facing runnable example."""

from pathlib import Path
import subprocess
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = tuple(sorted((PROJECT_ROOT / "examples").glob("*.py")))


@pytest.mark.parametrize("example", EXAMPLES, ids=lambda path: path.stem)
def test_example_runs_to_completion(example: Path) -> None:
    """Each documented example should run successfully from a source checkout."""
    result = subprocess.run(
        [sys.executable, str(example)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    assert result.returncode == 0, (
        f"{example.name} exited with {result.returncode}\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
