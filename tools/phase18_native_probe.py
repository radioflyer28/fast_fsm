#!/usr/bin/env python3
"""Compile-first probe for the private Phase 18 ownership representation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shlex
import subprocess
import tempfile

import yaml


_PROBE_MODULE = "ownership_probe_runtime"
_SUPPORTED_PYTHONS = ("3.10", "3.11", "3.12", "3.13", "3.14")
_WORKFLOW_NAME = "CI"
_NATIVE_SUFFIXES = (".so", ".pyd", ".dll")
ROOT = Path(__file__).resolve().parents[1]
_OWNERSHIP_TEST_FILES = (
    "tests/test_ownership_concurrency.py",
    "tests/test_transition_lifecycle.py",
    "tests/test_async.py",
    "tests/test_mypyc_guard.py",
)
_CI_CONTRACT_STEP = "Validate ownership native matrix contract"
_CI_COMPILE_CORE_STEP = "Compile actual ownership core"
_CI_NATIVE_ORIGIN_STEP = "Assert native ownership core origin"
_CI_TEST_STEP = "Run native ownership and lifecycle semantics"
_CI_REPRESENTATION_PROBE_STEP = "Compile and import ownership representation probe"
_NATIVE_PROBE_JOB_NAME = "Ownership native probe · Python ${{ matrix.python-version }}"
_NATIVE_PROBE_JOB_ENV = {"FAST_FSM_BUILD_MODE": "compiled"}
_NATIVE_PROBE_JOB_STRATEGY = {
    "fail-fast": False,
    "matrix": {"python-version": list(_SUPPORTED_PYTHONS)},
}
_NATIVE_PROBE_JOB_KEYS = frozenset({"name", "runs-on", "strategy", "env", "steps"})
_NATIVE_PROBE_RUN_STEP_KEYS = frozenset({"name", "run"})
_CI_CHECKOUT_STEP = {
    "uses": "actions/checkout@11d5960a326750d5838078e36cf38b85af677262",
    "with": {"fetch-depth": 0},
}
_CI_SETUP_UV_STEP = {
    "uses": "astral-sh/setup-uv@d4b2f3b6ecc6e67c4457f6d3e41ec42d3d0fcb86",
    "with": {
        "version": "0.12.6",
        "python-version": "${{ matrix.python-version }}",
    },
}
_CI_INSTALL_STEP = "Install locked native probe dependencies"
_CI_INSTALL_COMMAND = ("uv", "sync", "--locked", "--all-groups")
_RUNTIME_SOURCE = """\
from __future__ import annotations

import asyncio
from contextvars import ContextVar
import threading
from typing import Optional

_ownership_root: ContextVar[object | None] = ContextVar("ownership_root", default=None)


class OwnershipRepresentation:
    __slots__ = (
        "_sync_lock",
        "_sync_owner_thread_id",
        "_async_lock",
        "_bound_loop",
        "_async_owner_task",
        "_async_owner_root",
    )

    def __init__(self) -> None:
        self._sync_lock = threading.Lock()
        self._sync_owner_thread_id: Optional[int] = None
        self._async_lock: Optional[asyncio.Lock] = None
        self._bound_loop: Optional[asyncio.AbstractEventLoop] = None
        self._async_owner_task: Optional[asyncio.Task[object]] = None
        self._async_owner_root: object | None = None

    def acquire_sync(self) -> int:
        owner_thread_id = threading.get_ident()
        if self._sync_owner_thread_id == owner_thread_id:
            raise RuntimeError("FSM ownership violation: reentrant probe")
        self._sync_lock.acquire()
        self._sync_owner_thread_id = owner_thread_id
        return owner_thread_id

    def release_sync(self, owner_thread_id: int) -> None:
        if self._sync_owner_thread_id != owner_thread_id:
            raise RuntimeError("FSM ownership violation: foreign probe release")
        self._sync_owner_thread_id = None
        self._sync_lock.release()

    async def acquire_async(self) -> None:
        loop = asyncio.get_running_loop()
        if self._bound_loop is None:
            self._bound_loop = loop
        elif self._bound_loop is not loop:
            raise RuntimeError("FSM ownership violation: cross-loop probe")
        if self._async_lock is None:
            self._async_lock = asyncio.Lock()
        task = asyncio.current_task()
        if task is None:
            raise RuntimeError("FSM ownership violation: taskless probe")
        root = _ownership_root.get()
        if self._async_owner_task is task or (
            root is not None and root is self._async_owner_root
        ):
            raise RuntimeError("FSM ownership violation: reentrant probe")
        await self._async_lock.acquire()
        self._async_owner_task = task
        self._async_owner_root = object()

    def release_async(self) -> None:
        assert self._async_lock is not None
        self._async_owner_task = None
        self._async_owner_root = None
        self._async_lock.release()


async def exercise_async() -> None:
    value = OwnershipRepresentation()
    await value.acquire_async()
    value.release_async()


def exercise() -> None:
    value = OwnershipRepresentation()
    owner_thread_id = value.acquire_sync()
    value.release_sync(owner_thread_id)
    asyncio.run(exercise_async())
"""

_SETUP_SOURCE = """\
from setuptools import setup
from mypyc.build import mypycify

setup(ext_modules=mypycify(["ownership_probe_runtime.py"], opt_level="3"))
"""


def _run(command: list[str], *, cwd: Path) -> None:
    subprocess.run(command, cwd=cwd, check=True)


def _build_and_assert_native() -> None:
    with tempfile.TemporaryDirectory(prefix="fast-fsm-phase18-native-") as tempdir:
        directory = Path(tempdir)
        (directory / f"{_PROBE_MODULE}.py").write_text(_RUNTIME_SOURCE)
        (directory / "setup.py").write_text(_SETUP_SOURCE)
        _run(
            [
                "uv",
                "run",
                "python",
                "setup.py",
                "build_ext",
                "--inplace",
                "-q",
            ],
            cwd=directory,
        )
        assertion = (
            "from pathlib import Path; "
            f"import {_PROBE_MODULE} as probe; "
            "origin = Path(probe.__file__).resolve(); "
            "print(origin); "
            f"assert origin.suffix in {_NATIVE_SUFFIXES!r}; "
            "probe.exercise()"
        )
        _run(["uv", "run", "python", "-c", assertion], cwd=directory)


def _assert_core_native() -> None:
    """Print and require the installed core module to be a native extension."""
    import fast_fsm.core as core

    origin = Path(core.__file__).resolve()
    print(origin)
    if origin.suffix not in _NATIVE_SUFFIXES:
        raise SystemExit(
            f"fast_fsm.core must resolve to a native extension, got: {origin}"
        )


def _parse_exact_command(
    run: str,
    *,
    description: str,
    expected_tokens: tuple[str, ...],
) -> tuple[str, ...]:
    """Return one shell command only when its parsed argv exactly matches."""
    command_lines = tuple(
        line.strip()
        for line in run.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    )
    if not command_lines:
        raise SystemExit(
            f"CI ownership native probe is missing executable command in {description}"
        )
    if len(command_lines) != 1:
        raise SystemExit(
            f"CI ownership native probe {description} step must contain exactly one "
            "non-comment shell command"
        )

    try:
        lexer = shlex.shlex(command_lines[0], posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        lexer.commenters = "#"
        tokens = tuple(lexer)
    except ValueError as exc:
        raise SystemExit(
            f"CI ownership native probe {description} step has invalid shell syntax"
        ) from exc

    if tokens != expected_tokens:
        raise SystemExit(
            f"CI ownership native probe {description} step must exactly match the "
            f"required {description} argv: " + " ".join(expected_tokens)
        )
    return tokens


def _exact_workflow_value(actual: object, expected: object) -> bool:
    """Compare YAML values without accepting type-coerced equivalents."""
    if type(actual) is not type(expected):
        return False
    if isinstance(expected, dict):
        return set(actual) == set(expected) and all(
            _exact_workflow_value(actual[key], value) for key, value in expected.items()
        )
    if isinstance(expected, (list, tuple)):
        return len(actual) == len(expected) and all(
            _exact_workflow_value(item, value) for item, value in zip(actual, expected)
        )
    return actual == expected


def _require_native_probe_execution_context(
    workflow: dict[object, object], job: dict[object, object]
) -> None:
    """Require the fixed Actions context that executes the native commands.

    The required commands are security evidence, not configurable workflow hooks.
    Keeping the context allowlisted prevents Actions metadata or environment values
    from skipping a command, accepting its failure, or changing its Python/uv/pytest
    behavior outside the exact argv contract.
    """
    for scope_name, scope in (("workflow", workflow), ("job", job)):
        if "defaults" in scope:
            raise SystemExit(
                f"CI ownership native probe must not define {scope_name} defaults"
            )

    if "env" in workflow:
        raise SystemExit(
            "CI ownership native probe must not define workflow environment overrides"
        )

    if "if" in job:
        raise SystemExit(
            "CI ownership native probe job must not define an if condition"
        )
    if job.get("continue-on-error", False) is not False:
        raise SystemExit(
            "CI ownership native probe job must not continue after an error"
        )
    if "continue-on-error" in job:
        raise SystemExit(
            "CI ownership native probe job must not define continue-on-error"
        )
    unexpected_job_keys = set(job).difference(_NATIVE_PROBE_JOB_KEYS)
    if unexpected_job_keys:
        raise SystemExit(
            "CI ownership native probe job has unsupported execution metadata: "
            + ", ".join(sorted(unexpected_job_keys))
        )
    if job.get("name") != _NATIVE_PROBE_JOB_NAME:
        raise SystemExit("CI ownership native probe job name must remain fixed")
    if job.get("runs-on") != "ubuntu-latest":
        raise SystemExit(
            "CI ownership native probe job runner must remain ubuntu-latest"
        )
    if not _exact_workflow_value(job.get("strategy"), _NATIVE_PROBE_JOB_STRATEGY):
        raise SystemExit("CI ownership native probe job strategy must remain fixed")
    if not _exact_workflow_value(job.get("env"), _NATIVE_PROBE_JOB_ENV):
        raise SystemExit(
            "CI ownership native probe job environment must exactly set "
            "FAST_FSM_BUILD_MODE=compiled; PYTEST_ADDOPTS and Python/uv/pytest "
            "overrides are forbidden"
        )


def _require_exact_step_mapping(
    step: object, *, expected: dict[str, object], position: int, description: str
) -> None:
    """Require one fixed preparation step without accepting extra metadata."""
    if not _exact_workflow_value(step, expected):
        raise SystemExit(
            "CI ownership native probe step "
            f"{position} must exactly match the fixed {description} mapping"
        )


def _required_step_run(step: object, *, step_name: str, position: int) -> str:
    """Return a run scalar only from its fixed position and full mapping."""
    if not isinstance(step, dict):
        raise SystemExit(f"CI ownership native probe step {position} must be a mapping")
    if "if" in step:
        raise SystemExit(
            f"CI ownership native probe required step must not define an if condition: "
            f"{step_name}"
        )
    if step.get("continue-on-error", False) is not False:
        raise SystemExit(
            "CI ownership native probe required step must not continue after an "
            f"error: {step_name}"
        )
    if "continue-on-error" in step:
        raise SystemExit(
            "CI ownership native probe required step must not define "
            f"continue-on-error: {step_name}"
        )
    unexpected_step_keys = set(step).difference(_NATIVE_PROBE_RUN_STEP_KEYS)
    if unexpected_step_keys:
        raise SystemExit(
            f"CI ownership native probe step has unsupported execution metadata: "
            f"{step_name}: " + ", ".join(sorted(unexpected_step_keys))
        )

    if set(step) != _NATIVE_PROBE_RUN_STEP_KEYS or step.get("name") != step_name:
        raise SystemExit(
            "CI ownership native probe step "
            f"{position} must exactly match the required named step: {step_name}"
        )

    run = step.get("run")
    if not isinstance(run, str):
        raise SystemExit(
            f"CI ownership native probe step has no executable run scalar: {step_name}"
        )
    return run


def _check_ci(path: Path) -> None:
    try:
        workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise SystemExit(f"could not parse CI workflow: {path}") from exc
    if not isinstance(workflow, dict):
        raise SystemExit("CI workflow must be a mapping")
    jobs = workflow.get("jobs")
    if not isinstance(jobs, dict):
        raise SystemExit("CI workflow has no jobs mapping")
    job = jobs.get("ownership_native_probe")
    if not isinstance(job, dict):
        raise SystemExit("CI is missing the ownership_native_probe job")
    _require_native_probe_execution_context(workflow, job)

    strategy = job.get("strategy")
    matrix = strategy.get("matrix") if isinstance(strategy, dict) else None
    versions = matrix.get("python-version") if isinstance(matrix, dict) else None
    if not isinstance(versions, list) or tuple(versions) != _SUPPORTED_PYTHONS:
        raise SystemExit(
            "CI ownership native probe matrix must contain exactly: "
            + ", ".join(_SUPPORTED_PYTHONS)
        )

    steps = job.get("steps")
    if not isinstance(steps, list):
        raise SystemExit("CI ownership native probe has no steps list")
    required_commands = (
        (
            _CI_INSTALL_STEP,
            "dependency install",
            _CI_INSTALL_COMMAND,
        ),
        (
            _CI_CONTRACT_STEP,
            "contract self-check",
            (
                "uv",
                "run",
                "python",
                "tools/phase18_native_probe.py",
                "--check-ci",
                ".github/workflows/ci.yml",
            ),
        ),
        (
            _CI_COMPILE_CORE_STEP,
            "actual-core compile",
            (
                "uv",
                "run",
                "python",
                "setup.py",
                "build_ext",
                "--inplace",
                "-q",
            ),
        ),
        (
            _CI_NATIVE_ORIGIN_STEP,
            "core-origin assertion",
            (
                "uv",
                "run",
                "python",
                "tools/phase18_native_probe.py",
                "--assert-core-native",
            ),
        ),
        (
            _CI_TEST_STEP,
            "pytest",
            ("uv", "run", "pytest", *_OWNERSHIP_TEST_FILES, "-x", "-q"),
        ),
        (
            _CI_REPRESENTATION_PROBE_STEP,
            "representation probe",
            (
                "uv",
                "run",
                "python",
                "tools/phase18_native_probe.py",
                "--build-mode",
                "compiled",
                "--assert-native",
            ),
        ),
    )
    expected_step_count = 2 + len(required_commands)
    if len(steps) != expected_step_count:
        raise SystemExit(
            "CI ownership native probe must contain exactly "
            f"{expected_step_count} ordered steps"
        )

    _require_exact_step_mapping(
        steps[0],
        expected=_CI_CHECKOUT_STEP,
        position=1,
        description="checkout",
    )
    _require_exact_step_mapping(
        steps[1],
        expected=_CI_SETUP_UV_STEP,
        position=2,
        description="setup-uv",
    )
    for position, (step_name, description, expected_tokens) in enumerate(
        required_commands, start=3
    ):
        _parse_exact_command(
            _required_step_run(
                steps[position - 1], step_name=step_name, position=position
            ),
            description=description,
            expected_tokens=expected_tokens,
        )

    print(f"CI ownership native probe matrix verified: {', '.join(_SUPPORTED_PYTHONS)}")


def _resolve_commit(ref: str) -> str:
    completed = subprocess.run(
        ("git", "rev-parse", "--verify", f"{ref}^{{commit}}"),
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode:
        raise SystemExit(f"could not resolve hosted CI ref to a commit: {ref}")
    return completed.stdout.strip()


def _gh_json(arguments: list[str]) -> object:
    completed = subprocess.run(
        ("gh", *arguments),
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode:
        detail = completed.stderr.strip() or "GitHub CLI command failed"
        raise SystemExit(detail)
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit("GitHub CLI returned invalid workflow JSON") from exc


def _has_successful_native_matrix(jobs: list[object]) -> bool:
    """Return whether one successful ownership job exists for every version."""
    for version in _SUPPORTED_PYTHONS:
        expected_name = f"Ownership native probe · Python {version}"
        expected_jobs = [
            job
            for job in jobs
            if isinstance(job, dict) and job.get("name") == expected_name
        ]
        if len(expected_jobs) != 1 or expected_jobs[0].get("conclusion") != "success":
            return False
    return True


def _assert_hosted_ci_sha(ref: str) -> None:
    """Require a successful native ownership matrix from an exact SHA."""
    candidate = _resolve_commit(ref)
    runs = _gh_json(
        [
            "run",
            "list",
            "--workflow",
            _WORKFLOW_NAME,
            "--commit",
            candidate,
            "--limit",
            "20",
            "--json",
            "databaseId,headSha,status,conclusion,workflowName",
        ]
    )
    if not isinstance(runs, list):
        raise SystemExit("GitHub CLI returned an invalid workflow run list")
    matching_runs = [
        run
        for run in runs
        if isinstance(run, dict)
        and run.get("headSha") == candidate
        and run.get("workflowName") == _WORKFLOW_NAME
        and run.get("status") == "completed"
        and run.get("conclusion") == "success"
    ]
    if not matching_runs:
        raise SystemExit(
            f"no completed successful {_WORKFLOW_NAME} runs found for {candidate}"
        )

    for run in matching_runs:
        database_id = run.get("databaseId")
        if not isinstance(database_id, int):
            continue
        details = _gh_json(
            [
                "run",
                "view",
                str(database_id),
                "--json",
                "headSha,status,conclusion,jobs",
            ]
        )
        if not isinstance(details, dict) or details.get("headSha") != candidate:
            continue
        if (
            details.get("status") != "completed"
            or details.get("conclusion") != "success"
        ):
            continue
        jobs = details.get("jobs")
        if not isinstance(jobs, list):
            continue
        if _has_successful_native_matrix(jobs):
            print(
                f"Hosted CI native ownership matrix verified for exact SHA {candidate}"
            )
            return

    raise SystemExit(
        "no completed successful CI run contains the full native ownership matrix "
        f"for {candidate}"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-mode", choices=("compiled",))
    parser.add_argument("--assert-native", action="store_true")
    parser.add_argument("--assert-core-native", action="store_true")
    parser.add_argument("--check-ci", type=Path)
    parser.add_argument("--assert-hosted-ci-sha")
    args = parser.parse_args()

    if args.check_ci is not None:
        _check_ci(args.check_ci)
    if args.assert_native:
        _build_and_assert_native()
    if args.assert_core_native:
        _assert_core_native()
    if args.assert_hosted_ci_sha is not None:
        _assert_hosted_ci_sha(args.assert_hosted_ci_sha)
    if (
        args.check_ci is None
        and not args.assert_native
        and not args.assert_core_native
        and args.assert_hosted_ci_sha is None
    ):
        parser.error(
            "select --assert-native, --assert-core-native, --check-ci, and/or "
            "--assert-hosted-ci-sha"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
