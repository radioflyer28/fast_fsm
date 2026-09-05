"""Installed-wheel proof uses concrete archives outside the source checkout."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import artifact_conformance, release_evidence  # noqa: E402


def _build_wheel(output: Path, mode: str) -> Path:
    """Build one intentional local wheel under the requested release intent."""
    environment = dict(os.environ)
    environment["FAST_FSM_BUILD_MODE"] = mode
    environment.pop("FAST_FSM_PURE_PYTHON", None)
    completed = subprocess.run(
        ["uv", "build", "--wheel", "--out-dir", str(output)],
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    wheels = sorted(output.glob("*.whl"))
    assert len(wheels) == 1
    return wheels[0].resolve()


@pytest.fixture(scope="module")
def tracer_wheels(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    """Build concrete pure and compiled archives once for the tracer proof."""
    root = tmp_path_factory.mktemp("artifact-tracer")
    return {mode: _build_wheel(root / mode, mode) for mode in ("pure", "compiled")}


@pytest.mark.integration
@pytest.mark.parametrize("mode", ("pure", "compiled"))
def test_tracer_installs_exact_artifact_and_matches_source_lifecycle(
    tracer_wheels: dict[str, Path], mode: str
) -> None:
    """An absolute artifact path proves the same real lifecycle record in isolation."""
    wheel = tracer_wheels[mode]
    record = release_evidence.verify_installed_wheel(
        wheel,
        expected_mode=mode,
        build_intent=mode,
    )

    assert (
        record["artifact"]["sha256"] == hashlib.sha256(wheel.read_bytes()).hexdigest()
    )
    assert record["runtime"]["expected_mode"] == mode
    assert record["conformance"]["payload_leak_free"] is True
    assert (
        artifact_conformance.compare_conformance(
            artifact_conformance.collect_conformance(), record["conformance"]
        )
        == []
    )
