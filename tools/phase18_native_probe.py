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
_NON_EXECUTING_PYTEST_OPTIONS = frozenset(
    ("--collect-only", "--co", "--help", "-h", "--version", "-V")
)
_SHELL_CONTROL_TOKENS = frozenset(("&", "&&", "|", "||", ";", "<", ">", "<<", ">>"))
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


def _parse_ownership_pytest_command(run: str) -> tuple[str, ...]:
    """Return the one permitted pytest command from the native test step."""
    command_lines = tuple(
        line.strip()
        for line in run.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    )
    if len(command_lines) != 1:
        raise SystemExit(
            "CI ownership native probe test step must contain exactly one "
            "non-comment shell command"
        )

    try:
        lexer = shlex.shlex(command_lines[0], posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        lexer.commenters = "#"
        tokens = tuple(lexer)
    except ValueError as exc:
        raise SystemExit(
            "CI ownership native probe test step has invalid shell syntax"
        ) from exc

    if tokens[:3] != ("uv", "run", "pytest"):
        raise SystemExit(
            "CI ownership native probe test step must run exactly: uv run pytest ..."
        )
    if any(
        token in _SHELL_CONTROL_TOKENS or "$" in token or "`" in token
        for token in tokens
    ):
        raise SystemExit(
            "CI ownership native probe test step must not contain shell control "
            "operators"
        )
    for token in tokens[3:]:
        if any(
            token == option or token.startswith(f"{option}=")
            for option in _NON_EXECUTING_PYTEST_OPTIONS
        ):
            raise SystemExit(
                "CI ownership native probe test step must not use non-executing "
                f"pytest option: {token}"
            )
    missing = [
        test_file for test_file in _OWNERSHIP_TEST_FILES if test_file not in tokens
    ]
    if missing:
        raise SystemExit(
            "CI ownership native probe test step is missing pytest arguments: "
            + ", ".join(missing)
        )
    return tokens


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

    def executable_step_run(name: str) -> str:
        matching_steps = [
            step
            for step in steps
            if isinstance(step, dict) and step.get("name") == name
        ]
        if len(matching_steps) != 1:
            raise SystemExit(
                "CI ownership native probe must contain exactly one executable "
                f"step named: {name}"
            )
        run = matching_steps[0].get("run")
        if not isinstance(run, str):
            raise SystemExit(
                f"CI ownership native probe step has no executable run scalar: {name}"
            )
        return run

    def executable_step_lines(name: str) -> tuple[str, ...]:
        run = executable_step_run(name)
        return tuple(
            line.strip()
            for line in run.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        )

    for step in steps:
        if not isinstance(step, dict):
            raise SystemExit("CI ownership native probe has an invalid step")

    def require_command(step_name: str, command: str) -> tuple[str, ...]:
        lines = executable_step_lines(step_name)
        if not any(line.startswith(command) for line in lines):
            raise SystemExit(
                "CI ownership native probe is missing executable command in "
                f"{step_name}: {command}"
            )
        return lines

    require_command(
        _CI_CONTRACT_STEP,
        "uv run python tools/phase18_native_probe.py --check-ci ",
    )
    require_command(
        _CI_COMPILE_CORE_STEP,
        "uv run python setup.py build_ext --inplace -q",
    )
    native_origin_lines = require_command(
        _CI_NATIVE_ORIGIN_STEP,
        "uv run python -c ",
    )
    _parse_ownership_pytest_command(executable_step_run(_CI_TEST_STEP))
    require_command(
        _CI_REPRESENTATION_PROBE_STEP,
        "uv run python tools/phase18_native_probe.py --build-mode compiled "
        "--assert-native",
    )

    for required in (
        "import fast_fsm.core as core",
        "origin = Path(core.__file__).resolve()",
        "assert origin.suffix in ('.so', '.pyd', '.dll')",
    ):
        if not any(required in line for line in native_origin_lines):
            raise SystemExit(
                "CI ownership native probe is missing executable native-origin check: "
                + required
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
    parser.add_argument("--check-ci", type=Path)
    parser.add_argument("--assert-hosted-ci-sha")
    args = parser.parse_args()

    if args.check_ci is not None:
        _check_ci(args.check_ci)
    if args.assert_native:
        _build_and_assert_native()
    if args.assert_hosted_ci_sha is not None:
        _assert_hosted_ci_sha(args.assert_hosted_ci_sha)
    if (
        args.check_ci is None
        and not args.assert_native
        and args.assert_hosted_ci_sha is None
    ):
        parser.error(
            "select --assert-native, --check-ci, and/or --assert-hosted-ci-sha"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
