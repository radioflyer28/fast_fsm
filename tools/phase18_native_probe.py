#!/usr/bin/env python3
"""Compile-first probe for the private Phase 18 ownership representation."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap


_PROBE_MODULE = "ownership_probe_runtime"
_SUPPORTED_PYTHONS = ("3.10", "3.11", "3.12", "3.13", "3.14")
_RUNTIME_SOURCE = '''\
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
'''

_SETUP_SOURCE = '''\
from setuptools import setup
from mypyc.build import mypycify

setup(ext_modules=mypycify(["ownership_probe_runtime.py"], opt_level="3"))
'''


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
            "assert origin.suffix in ('.so', '.pyd', '.dll'); "
            "probe.exercise()"
        )
        _run(["uv", "run", "python", "-c", assertion], cwd=directory)


def _check_ci(path: Path) -> None:
    content = path.read_text()
    if "ownership_native_probe:" not in content:
        raise SystemExit("CI is missing the ownership_native_probe job")
    if "tools/phase18_native_probe.py --build-mode compiled --assert-native" not in content:
        raise SystemExit("CI ownership probe job does not run the native assertion")
    for version in _SUPPORTED_PYTHONS:
        if f'"{version}"' not in content:
            raise SystemExit(f"CI is missing supported Python {version}")
    print(f"CI ownership native probe matrix verified: {', '.join(_SUPPORTED_PYTHONS)}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-mode", choices=("compiled",))
    parser.add_argument("--assert-native", action="store_true")
    parser.add_argument("--check-ci", type=Path)
    args = parser.parse_args()

    if args.check_ci is not None:
        _check_ci(args.check_ci)
    if args.assert_native:
        _build_and_assert_native()
    if args.check_ci is None and not args.assert_native:
        parser.error("select --assert-native and/or --check-ci")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
