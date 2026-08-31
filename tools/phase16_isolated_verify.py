#!/usr/bin/env python3
"""Run Phase 16 checks in an asserted pure or compiled temporary checkout.

The developer checkout may intentionally contain native build shadows.  This helper
never imports Fast FSM itself: it exports ``HEAD`` to a fresh temporary tree, overlays
only explicitly named working-tree files, selects an artifact mode before setup, and
asserts the module origin before handing control to a semantic command.
"""

from __future__ import annotations

import argparse
import errno
import io
import json
import math
import os
from pathlib import Path
import secrets
import shutil
import stat
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
    "src/fast_fsm/__init__.py",
    "tests/test_graph_invariants.py",
    "tests/test_boundary_negative.py",
    "tests/test_builder.py",
    "tests/test_async.py",
    "tests/test_safety_kwargs.py",
    "tests/test_condition_templates.py",
    "tests/test_advanced_functionality.py",
    "tests/test_mypyc_guard.py",
    "tests/test_release_evidence.py",
    "tests/test_performance_benchmarks.py",
    "tools/release_evidence.py",
    ".specify/memory/spr-core-api.md",
    ".specify/decisions/ADR-003-mypyc-compilation-boundary.md",
    "docs/dev/architecture.md",
    "docs/dev/contributing.md",
    "docs/dev/testing.md",
    "evidence/release-baseline.json",
    ".planning/phases/16-canonical-graph-dispatch-invariants/16-PERFORMANCE-EVIDENCE.md",
)
MANIFEST_DESCRIPTOR_SUPPORT = (
    all(
        hasattr(os, flag) for flag in ("O_DIRECTORY", "O_NOFOLLOW", "O_CREAT", "O_EXCL")
    )
    and all(
        operation in os.supports_dir_fd
        for operation in (os.open, os.stat, os.mkdir, os.rename, os.unlink)
    )
    and hasattr(os, "fchmod")
    and hasattr(os, "fsync")
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
    """Return one lexical repository destination without resolving its parent."""
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts or not candidate.name:
        raise VerificationError(
            f"manifest output must be repository-relative: {value!r}"
        )
    return ROOT / candidate


def _require_manifest_descriptor_support() -> None:
    """Reject publication when the platform lacks no-follow descriptor primitives."""
    if not MANIFEST_DESCRIPTOR_SUPPORT:
        raise VerificationError(
            "secure manifest publication requires no-follow directory-descriptor "
            "operations on this platform"
        )


def _same_directory(left: os.stat_result, right: os.stat_result) -> bool:
    """Compare stable directory identity without relying on a pathname."""
    return left.st_dev == right.st_dev and left.st_ino == right.st_ino


def _open_manifest_parent(destination: Path) -> tuple[int, str]:
    """Anchor a repository-relative destination below one no-follow root fd."""
    _require_manifest_descriptor_support()
    try:
        relative = destination.relative_to(ROOT)
    except ValueError as exc:
        raise VerificationError(
            f"manifest output escapes repository root: {destination}"
        ) from exc
    if not relative.name or ".." in relative.parts:
        raise VerificationError(f"invalid manifest output: {destination}")

    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    try:
        parent_fd = os.open(ROOT, flags)
    except OSError as exc:
        raise VerificationError(
            "could not open repository root without following links"
        ) from exc
    try:
        root_stat = os.stat(ROOT, follow_symlinks=False)
        if not _same_directory(os.fstat(parent_fd), root_stat):
            raise VerificationError(
                "repository root changed while opening manifest output"
            )

        # Every descent starts from the repository descriptor and refuses a
        # symlink. The resulting descriptor therefore remains beneath this
        # exact root even if a lexical parent is renamed and replaced later.
        for component in relative.parent.parts:
            if component in ("", "."):
                continue
            try:
                child_fd = os.open(component, flags, dir_fd=parent_fd)
            except FileNotFoundError:
                try:
                    os.mkdir(component, 0o755, dir_fd=parent_fd)
                    child_fd = os.open(component, flags, dir_fd=parent_fd)
                except OSError as exc:
                    raise VerificationError(
                        f"could not create manifest directory: {component!r}"
                    ) from exc
            except OSError as exc:
                raise VerificationError(
                    f"could not open manifest directory without following links: {component!r}"
                ) from exc
            os.close(parent_fd)
            parent_fd = child_fd
        return parent_fd, relative.name
    except BaseException:
        os.close(parent_fd)
        raise


def _reject_json_constant(value: str) -> object:
    """Reject non-standard JSON constants such as ``NaN`` and ``Infinity``."""
    raise ValueError(f"non-standard JSON constant: {value}")


def _strict_json_bytes(contents: bytes, *, label: str) -> dict[str, object]:
    """Decode strict manifest bytes without permissive JSON constants."""
    try:
        manifest = json.loads(
            contents.decode("utf-8"),
            parse_constant=_reject_json_constant,
        )
    except (UnicodeDecodeError, OverflowError, ValueError, json.JSONDecodeError) as exc:
        raise VerificationError(f"invalid {label}") from exc
    if not isinstance(manifest, dict):
        raise VerificationError(f"invalid {label}")
    return manifest


def _strict_json_object(manifest_path: Path, *, label: str) -> dict[str, object]:
    """Load one manifest as a strict JSON object without permissive constants."""
    try:
        contents = manifest_path.read_bytes()
    except OSError as exc:
        raise VerificationError(f"invalid {label}: {manifest_path}") from exc
    try:
        return _strict_json_bytes(contents, label=f"{label}: {manifest_path}")
    except VerificationError as exc:
        raise VerificationError(f"invalid {label}: {manifest_path}") from exc


def _coverage_values_from_manifest(manifest: dict[str, object]) -> dict[str, float]:
    """Extract the two durable coverage floors from one decoded manifest."""
    try:
        coverage = manifest["quality_baseline"]["coverage"]
        return {
            field: _coverage_percentage(coverage[field])
            for field in ("total_percent", "core_percent")
        }
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        raise VerificationError("invalid coverage baseline manifest") from exc


def _coverage_values(manifest_path: Path) -> dict[str, float]:
    """Load the two durable coverage floors from one evidence manifest."""
    return _coverage_values_from_manifest(
        _strict_json_object(manifest_path, label="coverage baseline manifest")
    )


def _coverage_percentage(value: object) -> float:
    """Validate one JSON coverage percentage before rounding or comparison."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("coverage percentage must be a JSON number")
    percentage = float(value)
    if not math.isfinite(percentage) or not 0.0 <= percentage <= 100.0:
        raise ValueError("coverage percentage must be finite and between 0 and 100")
    return round(percentage, 2)


def _test_count(value: object) -> int:
    """Validate one durable test-count field without accepting booleans."""
    if type(value) is not int or value < 0:
        raise ValueError("test count must be a non-negative JSON integer")
    return value


def _test_values_from_manifest(manifest: dict[str, object]) -> dict[str, int]:
    """Extract durable successful-test evidence from one decoded manifest."""
    try:
        quality_baseline = manifest["quality_baseline"]
        if not isinstance(quality_baseline, dict):
            raise TypeError("quality_baseline must be an object")
        tests = quality_baseline["tests"]
        if not isinstance(tests, dict):
            raise TypeError("tests must be an object")
        values = {
            field: _test_count(tests[field])
            for field in ("collected", "passed", "failed", "errors")
        }
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        raise VerificationError("invalid test baseline manifest") from exc
    if values["collected"] <= 0 or values["passed"] != values["collected"]:
        raise VerificationError("invalid test baseline manifest")
    if values["failed"] != 0 or values["errors"] != 0:
        raise VerificationError("invalid test baseline manifest")
    return values


def _test_values(manifest_path: Path) -> dict[str, int]:
    """Load durable successful-test evidence from one evidence manifest."""
    return _test_values_from_manifest(
        _strict_json_object(manifest_path, label="test baseline manifest")
    )


def _quality_floor_values(manifest_path: Path) -> dict[str, dict[str, object]]:
    """Load the complete durable coverage and successful-test floor."""
    return {
        "coverage": _coverage_values(manifest_path),
        "tests": _test_values(manifest_path),
    }


def _quality_floor_values_from_bytes(contents: bytes) -> dict[str, dict[str, object]]:
    """Validate an anchored existing-manifest snapshot before replacement."""
    manifest = _strict_json_bytes(contents, label="coverage baseline manifest")
    return {
        "coverage": _coverage_values_from_manifest(manifest),
        "tests": _test_values_from_manifest(manifest),
    }


def _migration_quality_floor(
    migration_path: Path, record: dict[str, object], section: str
) -> dict[str, dict[str, object]]:
    """Validate one exact quality-floor snapshot from a reviewed migration."""
    try:
        snapshot = record[section]
        if not isinstance(snapshot, dict):
            raise TypeError("migration snapshot must be an object")
        coverage = snapshot["coverage"]
        tests = snapshot["tests"]
        if not isinstance(coverage, dict) or not isinstance(tests, dict):
            raise TypeError("migration coverage and tests must be objects")
        return {
            "coverage": {
                field: _coverage_percentage(coverage[field])
                for field in ("total_percent", "core_percent")
            },
            "tests": {
                field: _test_count(tests[field])
                for field in ("collected", "passed", "failed", "errors")
            },
        }
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        raise VerificationError(
            f"invalid quality-floor migration record: {migration_path}"
        ) from exc


def _validate_quality_floor_migration(
    migration_path: Path,
    previous: dict[str, dict[str, object]],
    replacement: dict[str, dict[str, object]],
) -> None:
    """Require an exact, separately reviewed record for a lower quality floor."""
    migration = _strict_json_object(
        migration_path, label="quality-floor migration record"
    )
    try:
        record = migration["quality_floor_migration"]
        if not isinstance(record, dict) or migration["schema_version"] != 2:
            raise ValueError("unsupported schema")
        reviewed = (record["reason"], record["reviewed_by"], record["reviewed_at"])
        if not all(isinstance(value, str) and value.strip() for value in reviewed):
            raise ValueError("missing review metadata")
    except (KeyError, TypeError, ValueError) as exc:
        raise VerificationError(
            f"invalid quality-floor migration record: {migration_path}"
        ) from exc
    expected_previous = _migration_quality_floor(migration_path, record, "previous")
    expected_replacement = _migration_quality_floor(
        migration_path, record, "replacement"
    )
    if expected_previous != previous or expected_replacement != replacement:
        raise VerificationError(
            "quality-floor migration record does not match the existing and "
            "generated manifests"
        )


def _validate_quality_floor(
    previous: dict[str, dict[str, object]] | None,
    generated: Path,
    migration_path: Path | None = None,
) -> None:
    """Fail closed before a baseline write lowers durable quality evidence."""
    # A first write establishes durable evidence, so it receives exactly the
    # same generated-manifest validation as a replacement write.
    replacement = _quality_floor_values(generated)
    if previous is None:
        return
    lowered_coverage = {
        field: (previous["coverage"][field], replacement["coverage"][field])
        for field in previous["coverage"]
        if replacement["coverage"][field] < previous["coverage"][field]
    }
    lowered_tests = {
        field: (previous["tests"][field], replacement["tests"][field])
        for field in ("collected", "passed")
        if replacement["tests"][field] < previous["tests"][field]
    }
    if not lowered_coverage and not lowered_tests:
        return
    if migration_path is None:
        rendered_coverage = ", ".join(
            f"{field} {before:.2f}->{after:.2f}"
            for field, (before, after) in sorted(lowered_coverage.items())
        )
        rendered_tests = ", ".join(
            f"{field} {before}->{after}"
            for field, (before, after) in sorted(lowered_tests.items())
        )
        if rendered_coverage and not rendered_tests:
            raise VerificationError(f"coverage floor regression: {rendered_coverage}")
        if rendered_tests and not rendered_coverage:
            raise VerificationError(f"test floor regression: {rendered_tests}")
        raise VerificationError(
            "quality floor regression: "
            f"coverage [{rendered_coverage}]; tests [{rendered_tests}]"
        )
    _validate_quality_floor_migration(migration_path, previous, replacement)


def _validate_coverage_floor(
    existing: Path, generated: Path, migration_path: Path | None = None
) -> None:
    """Validate a path-backed floor for direct tests and migration tooling."""
    previous = _quality_floor_values(existing) if existing.is_file() else None
    _validate_quality_floor(previous, generated, migration_path)


def _coverage_floor_migration(value: str) -> Path:
    """Resolve one explicit migration record without accepting an absent path."""
    migration = _manifest_output(value)
    if not migration.is_file():
        raise VerificationError(f"coverage-floor migration file not found: {value!r}")
    return migration


def _manifest_destination_snapshot(
    parent_fd: int, name: str
) -> tuple[int | None, bytes | None]:
    """Read one regular leaf through the anchored parent without following links."""
    try:
        file_fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=parent_fd)
    except FileNotFoundError:
        return None, None
    except OSError as exc:
        if exc.errno == errno.ELOOP:
            raise VerificationError(
                f"manifest output must not be a symlink: {name}"
            ) from exc
        raise VerificationError(f"could not open manifest output: {name}") from exc
    try:
        existing = os.fstat(file_fd)
        if not stat.S_ISREG(existing.st_mode):
            raise VerificationError(f"manifest output must be a regular file: {name}")
        with os.fdopen(file_fd, "rb", closefd=False) as existing_file:
            return stat.S_IMODE(existing.st_mode), existing_file.read()
    finally:
        os.close(file_fd)


def _new_manifest_temporary(parent_fd: int, destination_name: str) -> tuple[str, int]:
    """Reserve one private same-directory temporary through the anchored fd."""
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    for _ in range(128):
        temporary_name = f".{destination_name}.{secrets.token_hex(16)}.tmp"
        try:
            temporary_fd = os.open(temporary_name, flags, 0o600, dir_fd=parent_fd)
        except FileExistsError:
            continue
        return temporary_name, temporary_fd
    raise VerificationError("could not reserve a private manifest temporary file")


def _manifest_new_file_mode(parent_fd: int, destination_name: str) -> int:
    """Read the caller's normal file mode through an exclusive anchored probe."""
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    for _ in range(128):
        probe_name = f".{destination_name}.{secrets.token_hex(16)}.mode-probe"
        try:
            probe_fd = os.open(probe_name, flags, 0o666, dir_fd=parent_fd)
        except FileExistsError:
            continue
        try:
            return stat.S_IMODE(os.fstat(probe_fd).st_mode)
        finally:
            os.close(probe_fd)
            os.unlink(probe_name, dir_fd=parent_fd)
    raise VerificationError("could not reserve a manifest mode probe")


def _fsync_manifest_directory(parent_fd: int) -> None:
    """Persist the directory rename when the platform permits directory fsync."""
    try:
        os.fsync(parent_fd)
    except OSError as exc:
        if exc.errno not in (errno.EINVAL, errno.ENOTSUP):
            raise


def _export_manifest_atomically(
    generated: Path, output: str, migration_path: Path | None = None
) -> None:
    """Publish a validated generated manifest without following temp symlinks."""
    if not generated.is_file():
        raise VerificationError("baseline-write did not generate release-baseline.json")
    destination = _manifest_output(output)
    parent_fd, destination_name = _open_manifest_parent(destination)
    temporary_name: str | None = None
    temporary_fd: int | None = None
    try:
        existing_mode, existing_contents = _manifest_destination_snapshot(
            parent_fd, destination_name
        )
        previous = (
            _quality_floor_values_from_bytes(existing_contents)
            if existing_contents is not None
            else None
        )
        _validate_quality_floor(previous, generated, migration_path)
        intended_mode = (
            existing_mode
            if existing_mode is not None
            else _manifest_new_file_mode(parent_fd, destination_name)
        )
        temporary_name, temporary_fd = _new_manifest_temporary(
            parent_fd, destination_name
        )
        with os.fdopen(temporary_fd, "wb", closefd=False) as temporary_file:
            with generated.open("rb") as generated_file:
                shutil.copyfileobj(generated_file, temporary_file)
            temporary_file.flush()
        # The mode probe has captured the caller's normal creation mode
        # without mutating process-global umask. Existing destinations retain
        # their reviewed mode, while payload temporary contents stay private.
        os.fchmod(temporary_fd, intended_mode)
        os.fsync(temporary_fd)
        os.close(temporary_fd)
        temporary_fd = None
        # Rename is anchored to the descriptor opened beneath ROOT. If a
        # lexical parent is swapped after validation, this still publishes in
        # the original directory and cannot redirect through the replacement.
        os.rename(
            temporary_name,
            destination_name,
            src_dir_fd=parent_fd,
            dst_dir_fd=parent_fd,
        )
        temporary_name = None
        _fsync_manifest_directory(parent_fd)
    finally:
        if temporary_fd is not None:
            os.close(temporary_fd)
        if temporary_name is not None:
            try:
                os.unlink(temporary_name, dir_fd=parent_fd)
            except FileNotFoundError:
                pass
        os.close(parent_fd)


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
