#!/usr/bin/env python3
"""Compile-first probe for the private Phase 18 ownership representation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import tempfile


_PROBE_MODULE = "ownership_probe_runtime"
_SUPPORTED_PYTHONS = ("3.10", "3.11", "3.12", "3.13", "3.14")
_WORKFLOW_NAME = "CI"
_NATIVE_SUFFIXES = (".so", ".pyd", ".dll")
ROOT = Path(__file__).resolve().parents[1]
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


def _check_ci(path: Path) -> None:
    content = path.read_text()
    if "ownership_native_probe:" not in content:
        raise SystemExit("CI is missing the ownership_native_probe job")
    try:
        job = content.split("  ownership_native_probe:", maxsplit=1)[1].split(
            "\n  supported_python_build:", maxsplit=1
        )[0]
    except IndexError as exc:
        raise SystemExit(
            "CI ownership native probe job boundary is not explicit"
        ) from exc
    for required in (
        "uv run python tools/phase18_native_probe.py --check-ci .github/workflows/ci.yml",
        "uv run python setup.py build_ext --inplace -q",
        "import fast_fsm.core as core",
        "tests/test_ownership_concurrency.py",
        "tests/test_transition_lifecycle.py",
        "tests/test_async.py",
        "tests/test_mypyc_guard.py",
        "tools/phase18_native_probe.py --build-mode compiled --assert-native",
    ):
        if required not in job:
            raise SystemExit(f"CI ownership native probe is missing: {required}")
    for version in _SUPPORTED_PYTHONS:
        if f'"{version}"' not in job:
            raise SystemExit(f"CI is missing supported Python {version}")
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


def _assert_hosted_ci_sha(ref: str) -> None:
    """Require successful native ownership jobs from one exact candidate SHA."""
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
    ]
    if len(matching_runs) != 1:
        raise SystemExit(
            f"expected exactly one {_WORKFLOW_NAME} run for {candidate}, "
            f"found {len(matching_runs)}"
        )
    run = matching_runs[0]
    if run.get("status") != "completed" or run.get("conclusion") != "success":
        raise SystemExit(
            "exact-SHA CI run is not a completed success: "
            f"status={run.get('status')!r} conclusion={run.get('conclusion')!r}"
        )
    database_id = run.get("databaseId")
    if not isinstance(database_id, int):
        raise SystemExit("exact-SHA CI run has no numeric database ID")
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
        raise SystemExit("hosted CI details do not match the requested candidate SHA")
    if details.get("status") != "completed" or details.get("conclusion") != "success":
        raise SystemExit("exact-SHA CI details are not a completed success")
    jobs = details.get("jobs")
    if not isinstance(jobs, list):
        raise SystemExit("exact-SHA CI details have no job inventory")
    for version in _SUPPORTED_PYTHONS:
        expected_name = f"Ownership native probe · Python {version}"
        expected_jobs = [
            job
            for job in jobs
            if isinstance(job, dict) and job.get("name") == expected_name
        ]
        if len(expected_jobs) != 1 or expected_jobs[0].get("conclusion") != "success":
            raise SystemExit(f"native ownership job did not succeed: {expected_name}")
    print(f"Hosted CI native ownership matrix verified for exact SHA {candidate}")


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
