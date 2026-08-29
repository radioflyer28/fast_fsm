"""Regression coverage for the maintainer build-mode selector."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build_modes import BuildMode, resolve_build_mode  # noqa: E402


@pytest.mark.parametrize(
    ("environ", "expected"),
    [
        ({}, BuildMode.AUTO),
        ({"FAST_FSM_BUILD_MODE": "pure"}, BuildMode.PURE),
        ({"FAST_FSM_BUILD_MODE": "PURE"}, BuildMode.PURE),
        ({"FAST_FSM_BUILD_MODE": "compiled"}, BuildMode.COMPILED),
        ({"FAST_FSM_BUILD_MODE": "AUTO"}, BuildMode.AUTO),
        ({"FAST_FSM_PURE_PYTHON": "0"}, BuildMode.AUTO),
        ({"FAST_FSM_PURE_PYTHON": "1"}, BuildMode.PURE),
        (
            {"FAST_FSM_BUILD_MODE": "pure", "FAST_FSM_PURE_PYTHON": "1"},
            BuildMode.PURE,
        ),
    ],
)
def test_resolve_build_mode_supports_explicit_and_legacy_intent(
    environ: dict[str, str], expected: BuildMode
) -> None:
    """Explicit intent and the legacy pure alias have deterministic semantics."""
    assert resolve_build_mode(environ) is expected


@pytest.mark.parametrize(
    "environ",
    [
        {"FAST_FSM_BUILD_MODE": "native"},
        {"FAST_FSM_PURE_PYTHON": "true"},
        {"FAST_FSM_BUILD_MODE": "compiled", "FAST_FSM_PURE_PYTHON": "1"},
        {"FAST_FSM_BUILD_MODE": "auto", "FAST_FSM_PURE_PYTHON": "1"},
    ],
)
def test_resolve_build_mode_rejects_invalid_or_conflicting_configuration(
    environ: dict[str, str],
) -> None:
    """Misconfigured selectors fail closed with both variable names and values."""
    with pytest.raises(ValueError) as error:
        resolve_build_mode(environ)

    message = str(error.value)
    for name, value in environ.items():
        assert name in message
        assert value in message


def test_build_mode_is_python_310_compatible_string_enum() -> None:
    """The selector avoids enum.StrEnum, which was introduced after Python 3.10."""
    assert issubclass(BuildMode, str)
    assert BuildMode.PURE.value == "pure"


def _setup_extensions(environ: dict[str, str]) -> list[str]:
    """Run setup.py with a fake mypyc module and capture its extension decision."""
    script = """
import json
import runpy
import sys
import types
import setuptools

build = types.ModuleType('mypyc.build')
build.mypycify = lambda files, **kwargs: list(files)
mypyc = types.ModuleType('mypyc')
mypyc.build = build
sys.modules['mypyc'] = mypyc
sys.modules['mypyc.build'] = build
setuptools.setup = lambda **kwargs: print(json.dumps(kwargs['ext_modules']))
runpy.run_path('setup.py', run_name='__setup__')
"""
    process_environ = os.environ.copy()
    process_environ.pop("FAST_FSM_BUILD_MODE", None)
    process_environ.pop("FAST_FSM_PURE_PYTHON", None)
    process_environ.update(environ)
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=ROOT,
        env=process_environ,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(completed.stdout)


@pytest.mark.parametrize(
    "environ",
    [
        {"FAST_FSM_BUILD_MODE": "auto"},
        {"FAST_FSM_BUILD_MODE": "compiled"},
        {"FAST_FSM_PURE_PYTHON": "0"},
    ],
)
def test_auto_and_compiled_select_only_core_for_mypyc(
    environ: dict[str, str],
) -> None:
    """The explicit selector retains ADR-003's one-module compilation seam."""
    assert _setup_extensions(environ) == ["src/fast_fsm/core.py"]


@pytest.mark.parametrize(
    "environ",
    [
        {"FAST_FSM_BUILD_MODE": "pure"},
        {"FAST_FSM_PURE_PYTHON": "1"},
    ],
)
def test_pure_intent_suppresses_mypyc_extensions(environ: dict[str, str]) -> None:
    """Both pure selectors must reach setup.py and avoid extension generation."""
    assert _setup_extensions(environ) == []


def test_invalid_selector_is_not_swallowed_by_mypyc_fallback() -> None:
    """Selector errors must surface before setup's optional compiler fallback."""
    completed = subprocess.run(
        [sys.executable, "setup.py", "--name"],
        cwd=ROOT,
        env={**os.environ, "FAST_FSM_BUILD_MODE": "invalid"},
        capture_output=True,
        text=True,
    )
    assert completed.returncode != 0
    assert "FAST_FSM_BUILD_MODE" in completed.stderr
    assert "invalid" in completed.stderr


def test_pure_sdist_contains_selector_and_can_build_wheel_in_isolation(
    tmp_path: Path,
) -> None:
    """A source archive retains setup-time selector imports without repository access."""
    dist_dir = tmp_path / "dist"
    build_constraints = tmp_path / "build-constraints.txt"
    build_constraints.write_text(
        "setuptools==80.9.0\nwheel==0.45.1\nmypy[mypyc]==1.17.1\n",
        encoding="utf-8",
    )
    build_env = {**os.environ, "FAST_FSM_BUILD_MODE": "pure"}
    subprocess.run(
        [
            "uv",
            "build",
            "--build-constraints",
            str(build_constraints),
            "--sdist",
            "--out-dir",
            str(dist_dir),
        ],
        cwd=ROOT,
        env=build_env,
        check=True,
    )
    sdist = next(dist_dir.glob("*.tar.gz"))
    with tarfile.open(sdist) as archive:
        names = archive.getnames()
        assert any(name.endswith("/tools/__init__.py") for name in names)
        assert any(name.endswith("/tools/build_modes.py") for name in names)
        unpacked = tmp_path / "unpacked"
        if sys.version_info >= (3, 12):
            archive.extractall(unpacked, filter="data")
        else:
            archive.extractall(unpacked)

    source_root = next(unpacked.iterdir())
    wheel_dir = tmp_path / "wheel"
    subprocess.run(
        [
            "uv",
            "build",
            "--build-constraints",
            str(build_constraints),
            "--wheel",
            "--out-dir",
            str(wheel_dir),
        ],
        cwd=source_root,
        env=build_env,
        check=True,
    )
    assert list(wheel_dir.glob("*.whl"))
