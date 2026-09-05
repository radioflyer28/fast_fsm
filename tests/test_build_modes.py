"""Regression coverage for the maintainer build-mode selector."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
from zipfile import ZipFile

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


def _run_setup_extensions(
    environ: dict[str, str], *, failure: str | None = None
) -> subprocess.CompletedProcess[str]:
    """Run setup.py with a controlled mypyc import or compiler failure."""
    if failure not in {None, "import", "compile"}:
        raise ValueError(f"Unsupported test mypyc failure mode: {failure!r}")

    script = """
import json
import runpy
import sys
import types
import setuptools

failure = {failure!r}
if failure == 'import':
    class BlockMypyc:
        def find_spec(self, fullname, path=None, target=None):
            if fullname == 'mypyc' or fullname.startswith('mypyc.'):
                raise ImportError('forced mypyc import failure')
            return None
    sys.meta_path.insert(0, BlockMypyc())
else:
    build = types.ModuleType('mypyc.build')
    if failure == 'compile':
        def mypycify(*args, **kwargs):
            raise RuntimeError('forced mypyc compilation failure')
        build.mypycify = mypycify
    else:
        build.mypycify = lambda files, **kwargs: list(files)
    mypyc = types.ModuleType('mypyc')
    mypyc.build = build
    sys.modules['mypyc'] = mypyc
    sys.modules['mypyc.build'] = build
setuptools.setup = lambda **kwargs: print(json.dumps(kwargs['ext_modules']))
runpy.run_path('setup.py', run_name='__setup__')
""".format(failure=failure)
    process_environ = os.environ.copy()
    process_environ.pop("FAST_FSM_BUILD_MODE", None)
    process_environ.pop("FAST_FSM_PURE_PYTHON", None)
    process_environ.update(environ)
    return subprocess.run(
        [sys.executable, "-c", script],
        cwd=ROOT,
        env=process_environ,
        capture_output=True,
        text=True,
        check=False,
    )


def _setup_extensions(environ: dict[str, str]) -> list[str]:
    """Capture setup.py's selected extensions for a successful fake build."""
    completed = _run_setup_extensions(environ)
    assert completed.returncode == 0, completed.stderr
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


@pytest.mark.parametrize("failure", ("import", "compile"))
def test_compiled_intent_propagates_mypyc_failures(failure: str) -> None:
    """A requested compiled artifact must never silently become a pure fallback."""
    completed = _run_setup_extensions(
        {"FAST_FSM_BUILD_MODE": "compiled"}, failure=failure
    )

    assert completed.returncode != 0
    assert "forced mypyc" in completed.stderr


@pytest.mark.parametrize("failure", ("import", "compile"))
def test_auto_intent_can_fall_back_when_mypyc_is_unavailable(failure: str) -> None:
    """Optional automatic builds retain the documented pure-Python fallback."""
    completed = _run_setup_extensions({"FAST_FSM_BUILD_MODE": "auto"}, failure=failure)

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == []


def test_pure_intent_never_imports_mypyc() -> None:
    """An explicit pure build bypasses even a deliberately broken mypyc import."""
    completed = _run_setup_extensions({"FAST_FSM_BUILD_MODE": "pure"}, failure="import")

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == []


def test_compiled_archive_requires_a_native_core_member(tmp_path: Path) -> None:
    """A native extension elsewhere in the package cannot certify compiled core proof."""
    wheel = tmp_path / "fast_fsm-0.2.2-cp312-cp312-macosx_11_0_arm64.whl"
    with ZipFile(wheel, "w") as archive:
        archive.writestr("fast_fsm/__init__.py", "")
        archive.writestr("fast_fsm/core.py", "not the native core")
        archive.writestr("fast_fsm/not_core.abi3.so", "native but irrelevant")
        archive.writestr(
            "fast_fsm-0.2.2.dist-info/WHEEL",
            "Wheel-Version: 1.0\nTag: cp312-cp312-macosx_11_0_arm64\n",
        )
        archive.writestr(
            "fast_fsm-0.2.2.dist-info/METADATA",
            "Name: fast_fsm\nVersion: 0.2.2\n",
        )

    from tools import release_evidence

    with pytest.raises(release_evidence.EvidenceError, match="native fast_fsm.core"):
        release_evidence.inspect_wheel(wheel)


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
