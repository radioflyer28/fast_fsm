#!/usr/bin/env python3
"""Run Phase 16 checks in an asserted pure or compiled temporary checkout.

The developer checkout may intentionally contain native build shadows.  This helper
never imports Fast FSM itself: it exports ``HEAD`` to a fresh temporary tree, overlays
only explicitly named working-tree files, selects an artifact mode before setup, and
asserts the module origin before handing control to a semantic command.
"""

from __future__ import annotations

import argparse
import io
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
from typing import Iterable, Sequence


ROOT = Path(__file__).resolve().parents[1]
NATIVE_SUFFIXES = (".so", ".pyd", ".dll")
PHASE16_INVENTORY = (
    "src/fast_fsm/core.py",
    "src/fast_fsm/conditions.py",
    "src/fast_fsm/condition_templates.py",
    "tests/test_graph_invariants.py",
    "tests/test_boundary_negative.py",
    "tests/test_builder.py",
    "tests/test_async.py",
    "tests/test_safety_kwargs.py",
    "tests/test_condition_templates.py",
    "tests/test_advanced_functionality.py",
    "tests/test_mypyc_guard.py",
    "tests/test_performance_benchmarks.py",
    ".specify/memory/spr-core-api.md",
    "docs/dev/architecture.md",
    "docs/dev/testing.md",
    "evidence/release-baseline.json",
    ".planning/phases/16-canonical-graph-dispatch-invariants/16-PERFORMANCE-EVIDENCE.md",
)


class VerificationError(RuntimeError):
    """Raised when an isolation precondition cannot be established."""


def _run(
    command: Sequence[str], *, cwd: Path, env: dict[str, str], check: bool = True
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        check=check,
    )


def _assert_relative_include(value: str) -> Path:
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise VerificationError(f"include must be repository-relative: {value!r}")
    source = (ROOT / candidate).resolve()
    try:
        source.relative_to(ROOT)
    except ValueError as exc:
        raise VerificationError(f"include escapes repository root: {value!r}") from exc
    if not source.is_file():
        raise VerificationError(f"include does not name a working-tree file: {value!r}")
    return candidate


def _safe_extract(archive: bytes, destination: Path) -> None:
    resolved_destination = destination.resolve()
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        for member in tar.getmembers():
            member_path = (destination / member.name).resolve()
            try:
                member_path.relative_to(resolved_destination)
            except ValueError as exc:
                raise VerificationError(
                    f"git archive contained an unsafe path: {member.name!r}"
                ) from exc
        tar.extractall(destination, filter="data")


def _export_head(destination: Path, env: dict[str, str]) -> None:
    archive = subprocess.run(
        ("git", "archive", "--format=tar", "HEAD"),
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout
    _safe_extract(archive, destination)


def _overlay(includes: Iterable[str], destination: Path) -> tuple[str, ...]:
    checked = tuple(str(_assert_relative_include(value)) for value in includes)
    for value in checked:
        source = ROOT / value
        target = destination / value
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    return checked


def _native_artifacts(source_tree: Path) -> list[Path]:
    package_dir = source_tree / "src" / "fast_fsm"
    if not package_dir.is_dir():
        raise VerificationError("temporary checkout is missing src/fast_fsm")
    return sorted(
        path
        for path in package_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in NATIVE_SUFFIXES
    )


def _assert_origin(source_tree: Path, build_mode: str, env: dict[str, str]) -> None:
    assertion = (
        "from pathlib import Path; import fast_fsm.core as core; "
        "origin = Path(core.__file__).resolve(); "
        "print(origin); "
        "expected = '.py' if __import__('os').environ['FAST_FSM_BUILD_MODE'] == 'pure' "
        "else None; "
        "assert origin.suffix == expected if expected else origin.suffix in ('.so', '.pyd', '.dll')"
    )
    _run(("uv", "run", "python", "-c", assertion), cwd=source_tree, env=env)


def _validate_child_command(command: Sequence[str], source_tree: Path) -> None:
    """Validate a trusted task command's shape and prepared working directory.

    Task mode runs arbitrary verifier commands with the temporary checkout as
    their initial working directory. It is not an OS sandbox and does not claim
    to confine a trusted command that deliberately selects another path.
    """
    if not command:
        raise VerificationError("task mode requires a command after '--'")
    if command[0].startswith("-"):
        raise VerificationError("task command must begin with an executable")
    if not source_tree.resolve().is_dir():
        raise VerificationError("temporary repository path could not be resolved")


def _prepare_tree(
    *, build_mode: str, includes: Iterable[str]
) -> tuple[tempfile.TemporaryDirectory[str], Path, dict[str, str], tuple[str, ...]]:
    tempdir = tempfile.TemporaryDirectory(prefix=f"fast-fsm-phase16-{build_mode}-")
    source_tree = Path(tempdir.name) / "repo"
    source_tree.mkdir()
    env = os.environ.copy()
    env["FAST_FSM_BUILD_MODE"] = build_mode
    env.pop("PYTHONPATH", None)
    env.pop("VIRTUAL_ENV", None)
    _export_head(source_tree, env)
    overlaid = _overlay(includes, source_tree)
    if build_mode == "pure":
        artifacts = _native_artifacts(source_tree)
        if artifacts:
            rendered = ", ".join(
                str(path.relative_to(source_tree)) for path in artifacts
            )
            raise VerificationError(
                f"pure task mode refuses native artifacts: {rendered}"
            )
    _run(("uv", "sync", "--locked", "--all-groups"), cwd=source_tree, env=env)
    if build_mode == "compiled":
        _run(
            ("uv", "run", "python", "setup.py", "build_ext", "--inplace"),
            cwd=source_tree,
            env=env,
        )
    _assert_origin(source_tree, build_mode, env)
    return tempdir, source_tree, env, overlaid


def _task_mode(args: argparse.Namespace) -> int:
    tempdir, source_tree, env, overlaid = _prepare_tree(
        build_mode=args.build_mode, includes=args.include
    )
    try:
        _validate_child_command(args.command, source_tree)
        print(
            "phase16 task context "
            f"mode={args.build_mode} root={source_tree} overlays={','.join(overlaid)}"
        )
        return _run(args.command, cwd=source_tree, env=env, check=False).returncode
    finally:
        tempdir.cleanup()


def _run_suite_command(
    *, build_mode: str, includes: Sequence[str], command: Sequence[str]
) -> int:
    tempdir, source_tree, env, _ = _prepare_tree(
        build_mode=build_mode, includes=includes
    )
    try:
        _validate_child_command(command, source_tree)
        return _run(command, cwd=source_tree, env=env, check=False).returncode
    finally:
        tempdir.cleanup()


def _manifest_output(value: str) -> Path:
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise VerificationError(
            f"manifest output must be repository-relative: {value!r}"
        )
    destination = (ROOT / candidate).resolve()
    try:
        destination.relative_to(ROOT)
    except ValueError as exc:
        raise VerificationError(
            f"manifest output escapes repository root: {value!r}"
        ) from exc
    return destination


def _coverage_values(manifest_path: Path) -> dict[str, float]:
    """Load the two durable coverage floors from one evidence manifest."""
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        coverage = manifest["quality_baseline"]["coverage"]
        return {
            field: _coverage_percentage(coverage[field])
            for field in ("total_percent", "core_percent")
        }
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise VerificationError(
            f"invalid coverage baseline manifest: {manifest_path}"
        ) from exc


def _coverage_percentage(value: object) -> float:
    """Validate one JSON coverage percentage before rounding or comparison."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("coverage percentage must be a JSON number")
    percentage = float(value)
    if not math.isfinite(percentage) or not 0.0 <= percentage <= 100.0:
        raise ValueError("coverage percentage must be finite and between 0 and 100")
    return round(percentage, 2)


def _validate_coverage_floor_migration(
    migration_path: Path,
    previous: dict[str, float],
    replacement: dict[str, float],
) -> None:
    """Require an explicit, separately reviewed record for a lower floor."""
    try:
        migration = json.loads(migration_path.read_text(encoding="utf-8"))
        record = migration["coverage_floor_migration"]
        if migration["schema_version"] != 1:
            raise ValueError("unsupported schema")
        reviewed = (record["reason"], record["reviewed_by"], record["reviewed_at"])
        if not all(isinstance(value, str) and value.strip() for value in reviewed):
            raise ValueError("missing review metadata")
        expected_previous = {
            field: _coverage_percentage(record["previous"][field])
            for field in ("total_percent", "core_percent")
        }
        expected_replacement = {
            field: _coverage_percentage(record["replacement"][field])
            for field in ("total_percent", "core_percent")
        }
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise VerificationError(
            f"invalid coverage-floor migration record: {migration_path}"
        ) from exc
    if expected_previous != previous or expected_replacement != replacement:
        raise VerificationError(
            "coverage-floor migration record does not match the existing and "
            "generated manifests"
        )


def _validate_coverage_floor(
    existing: Path, generated: Path, migration_path: Path | None = None
) -> None:
    """Fail closed before a baseline write lowers durable coverage evidence."""
    if not existing.is_file():
        return
    previous = _coverage_values(existing)
    replacement = _coverage_values(generated)
    lowered = {
        field: (previous[field], replacement[field])
        for field in previous
        if replacement[field] < previous[field]
    }
    if not lowered:
        return
    if migration_path is None:
        rendered = ", ".join(
            f"{field} {before:.2f}->{after:.2f}"
            for field, (before, after) in sorted(lowered.items())
        )
        raise VerificationError(f"coverage floor regression: {rendered}")
    _validate_coverage_floor_migration(migration_path, previous, replacement)


def _coverage_floor_migration(value: str) -> Path:
    """Resolve one explicit migration record without accepting an absent path."""
    migration = _manifest_output(value)
    if not migration.is_file():
        raise VerificationError(f"coverage-floor migration file not found: {value!r}")
    return migration


def _export_manifest_atomically(
    generated: Path, output: str, migration_path: Path | None = None
) -> None:
    """Publish a validated generated manifest without following temp symlinks."""
    if not generated.is_file():
        raise VerificationError("baseline-write did not generate release-baseline.json")
    destination = _manifest_output(output)
    _validate_coverage_floor(destination, generated, migration_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        # NamedTemporaryFile uses an unpredictable O_EXCL name in the resolved
        # destination directory. Unlike the former predictable sibling name,
        # it neither opens nor replaces a pre-positioned symlink.
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary = Path(temporary_file.name)
            with generated.open("rb") as generated_file:
                shutil.copyfileobj(generated_file, temporary_file)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.replace(temporary, destination)
        temporary = None
    finally:
        if temporary is not None:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass


def _suite_mode(args: argparse.Namespace) -> int:
    if args.suite == "graph":
        command = (
            "uv",
            "run",
            "pytest",
            "tests/test_mypyc_guard.py",
            "tests/test_graph_invariants.py",
            "-x",
            "-q",
        )
        for build_mode in ("pure", "compiled"):
            status = _run_suite_command(
                build_mode=build_mode,
                includes=("tools/phase16_isolated_verify.py", *PHASE16_INVENTORY),
                command=command,
            )
            if status:
                return status
        return 0
    if args.suite == "baseline-check":
        return _run_suite_command(
            build_mode="pure",
            includes=(
                "tools/phase16_isolated_verify.py",
                "evidence/release-baseline.json",
            ),
            command=("task", "release-baseline-check"),
        )
    if args.suite == "baseline-write":
        if args.manifest_output is None:
            raise VerificationError(
                "baseline-write requires --manifest-output REPOSITORY_RELATIVE_PATH"
            )
        tempdir, source_tree, env, _ = _prepare_tree(
            build_mode="pure",
            includes=("tools/phase16_isolated_verify.py", *PHASE16_INVENTORY),
        )
        try:
            status = _run(
                ("task", "release-baseline-write"),
                cwd=source_tree,
                env=env,
                check=False,
            ).returncode
            if status:
                return status
            _export_manifest_atomically(
                source_tree / "evidence" / "release-baseline.json",
                args.manifest_output,
                (
                    _coverage_floor_migration(args.coverage_floor_migration)
                    if args.coverage_floor_migration is not None
                    else None
                ),
            )
            return 0
        finally:
            tempdir.cleanup()
    if args.suite == "phase16":
        semantic = (
            "uv",
            "run",
            "pytest",
            "tests/test_graph_invariants.py",
            "tests/test_boundary_negative.py",
            "tests/test_builder.py",
            "tests/test_async.py",
            "tests/test_safety_kwargs.py",
            "tests/test_condition_templates.py",
            "tests/test_advanced_functionality.py",
            "tests/test_mypyc_guard.py",
            "-x",
            "-q",
        )
        for build_mode in ("pure", "compiled"):
            status = _run_suite_command(
                build_mode=build_mode,
                includes=("tools/phase16_isolated_verify.py", *PHASE16_INVENTORY),
                command=semantic,
            )
            if status:
                return status
        performance = (
            "uv",
            "run",
            "pytest",
            "tests/test_performance_benchmarks.py",
            "-x",
            "-q",
            "-k",
            "trigger or history",
        )
        status = _run_suite_command(
            build_mode="compiled",
            includes=("tools/phase16_isolated_verify.py", *PHASE16_INVENTORY),
            command=performance,
        )
        if status:
            return status
        return _run_suite_command(
            build_mode="pure",
            includes=("tools/phase16_isolated_verify.py", *PHASE16_INVENTORY),
            command=("task", "release-gate"),
        )
    raise AssertionError(f"unhandled suite: {args.suite}")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("task",), default="task")
    parser.add_argument("--build-mode", choices=("pure", "compiled"))
    parser.add_argument("--include", action="append", default=[])
    parser.add_argument("--manifest-output")
    parser.add_argument("--coverage-floor-migration")
    parser.add_argument(
        "--suite", choices=("graph", "baseline-write", "baseline-check", "phase16")
    )
    parser.add_argument("command", nargs=argparse.REMAINDER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command[:1] == ["--"]:
        args.command = args.command[1:]
    if args.suite is not None:
        if (
            args.build_mode is not None
            or args.include
            or args.command
            or (args.manifest_output is not None and args.suite != "baseline-write")
            or (
                args.coverage_floor_migration is not None
                and args.suite != "baseline-write"
            )
        ):
            raise VerificationError("suite mode does not accept task-mode arguments")
        return _suite_mode(args)
    if args.build_mode is None:
        raise VerificationError("task mode requires --build-mode pure or compiled")
    return _task_mode(args)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (VerificationError, subprocess.CalledProcessError) as exc:
        print(f"phase16 isolation failed: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
