"""Installed-wheel proof uses concrete archives outside the source checkout."""

from __future__ import annotations

import hashlib
import json
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


def _runtime_probe(
    environment: Path, *, direct_url: object | None = None
) -> dict[str, object]:
    """Build one parent-side runtime fixture without importing a real checkout."""
    package = environment / "site-packages" / "fast_fsm" / "__init__.py"
    core = environment / "site-packages" / "fast_fsm" / "core.py"
    interpreter = environment / "bin" / "python"
    return {
        "distribution_version": "0.2.2",
        "package_version": "0.2.2",
        "package_origin": str(package),
        "core_origin": str(core),
        "core_loader": "SourceFileLoader",
        "interpreter": str(interpreter),
        "python_implementation": "cpython",
        "python_version": "3.12.10",
        "platform": "Darwin",
        "machine": "arm64",
        "direct_url": direct_url,
        "extension_suffixes": [".so", ".pyd"],
    }


def test_runtime_provenance_rejects_checkout_and_symlink_escapes(tmp_path: Path) -> None:
    """Fresh-env evidence never accepts editable or checkout-backed origins."""
    environment = tmp_path / "environment"
    checkout_direct_url = {"url": ROOT.as_uri(), "dir_info": {"editable": False}}
    with pytest.raises(release_evidence.EvidenceError, match="provenance"):
        release_evidence._validate_runtime_probe(
            _runtime_probe(environment, direct_url=checkout_direct_url),
            environment_root=environment,
            expected_mode="pure",
            version="0.2.2",
        )

    escaped = _runtime_probe(environment)
    escaped["core_origin"] = str(ROOT / "src" / "fast_fsm" / "core.py")
    with pytest.raises(release_evidence.EvidenceError, match="origin"):
        release_evidence._validate_runtime_probe(
            escaped,
            environment_root=environment,
            expected_mode="pure",
            version="0.2.2",
        )


def test_child_probe_rejects_payloads_resource_abuse_and_parent_identity_drift() -> None:
    """Child output is untrusted even when its top-level JSON is well formed."""
    conformance = artifact_conformance.collect_conformance()
    conformance["scenarios"][0]["state"] = "caller-secret"
    conformance["semantic_sha256"] = "0" * 64
    child = {
        "artifact_sha256": "0" * 64,
        "conformance": conformance,
        "runtime": _runtime_probe(Path("/environment")),
    }

    with pytest.raises(release_evidence.EvidenceError, match="artifact identity"):
        release_evidence._validate_child_probe(
            child,
            expected_artifact_sha256="f" * 64,
        )

    with pytest.raises(release_evidence.EvidenceError, match="malformed"):
        release_evidence._strict_json_object(
            '{"value": 1, "value": 2}', field="child probe"
        )
    with pytest.raises(release_evidence.EvidenceError, match="malformed"):
        release_evidence._strict_json_object('{"value": NaN}', field="child probe")

    oversized = json.dumps(
        {"value": "x" * (release_evidence._MAX_CHILD_OUTPUT_BYTES + 1)}
    )
    with pytest.raises(release_evidence.EvidenceError, match="size limit"):
        release_evidence._strict_json_object(oversized, field="child probe")
