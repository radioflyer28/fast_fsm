"""Non-destructive maintainer checks for source and wheel release evidence."""

from __future__ import annotations

import argparse
from email.parser import Parser
import importlib
from importlib import machinery, metadata
import json
from pathlib import Path
import sys
from typing import Any, Iterable, Sequence
from zipfile import ZipFile


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
PACKAGE_NAME = "fast_fsm"
CORE_MODULE_NAME = f"{PACKAGE_NAME}.core"


class EvidenceError(RuntimeError):
    """Raised when local release evidence is incomplete or contradictory."""


def _native_suffixes() -> tuple[str, ...]:
    """Return normalized import-extension suffixes with portable fallbacks."""
    suffixes = {suffix.lower() for suffix in machinery.EXTENSION_SUFFIXES}
    suffixes.update({".so", ".pyd"})
    return tuple(sorted(suffixes, key=lambda suffix: (-len(suffix), suffix)))


def _is_native_member(name: str) -> bool:
    """Return whether a path/member name ends with a native-extension suffix."""
    normalized = name.lower()
    return any(normalized.endswith(suffix) for suffix in _native_suffixes())


def find_native_core_shadows(package_root: Path) -> list[Path]:
    """Find native siblings that would outrank ``core.py`` during import."""
    if not package_root.is_dir():
        raise EvidenceError(f"Package directory does not exist: {package_root}")
    return sorted(
        (
            candidate.resolve()
            for candidate in package_root.iterdir()
            if candidate.is_file()
            and candidate.name.startswith("core")
            and _is_native_member(candidate.name)
        ),
        key=lambda path: path.as_posix(),
    )


def _normalized_relative_path(path: Path, root: Path) -> str:
    """Return an evidence-safe path relative to a trusted repository root."""
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as error:
        raise EvidenceError(
            f"Expected {path} to remain inside the inspected source tree {root}."
        ) from error


def verify_source(source_root: Path | None = None) -> dict[str, str]:
    """Verify that ``fast_fsm.core`` resolves to clean Python source.

    Native siblings are checked before importing the package, so this function
    cannot accidentally certify a native module that shadowed ``core.py``.
    It deliberately performs no cleanup or mutation.
    """
    resolved_source_root = (source_root or REPOSITORY_ROOT / "src").resolve()
    package_root = resolved_source_root / PACKAGE_NAME
    shadows = find_native_core_shadows(package_root)
    if shadows:
        rendered_paths = "\n".join(f"  - {path}" for path in shadows)
        raise EvidenceError(
            "Native core shadow(s) found before importing fast_fsm.core:\n"
            f"{rendered_paths}\n"
            "Remove or relocate these generated artifacts explicitly, then rerun "
            "verify-source. This command never deletes developer files."
        )

    source_root_text = str(resolved_source_root)
    if source_root_text not in sys.path:
        sys.path.insert(0, source_root_text)
    importlib.invalidate_caches()
    core_module = importlib.import_module(CORE_MODULE_NAME)
    origin_text = getattr(core_module, "__file__", None)
    if not origin_text:
        raise EvidenceError(f"{CORE_MODULE_NAME} did not expose a module origin.")
    origin = Path(origin_text).resolve()
    if origin.suffix != ".py":
        raise EvidenceError(
            f"Expected a pure Python {CORE_MODULE_NAME} origin ending in '.py', "
            f"got {origin}."
        )

    return {
        "core_origin": _normalized_relative_path(origin, resolved_source_root.parent),
        "distribution_version": metadata.version("fast-fsm"),
    }


def _wheel_filename_tags(wheel_path: Path) -> tuple[str, ...]:
    """Parse normalized compatibility tags from a wheel filename."""
    if wheel_path.suffix.lower() != ".whl":
        raise EvidenceError(f"Expected a .whl archive, got {wheel_path.name!r}.")
    parts = wheel_path.stem.split("-")
    if len(parts) < 5:
        raise EvidenceError(f"Invalid wheel filename: {wheel_path.name!r}.")
    python_tags, abi_tags, platform_tags = parts[-3:]
    return tuple(
        sorted(
            f"{python_tag}-{abi_tag}-{platform_tag}"
            for python_tag in python_tags.split(".")
            for abi_tag in abi_tags.split(".")
            for platform_tag in platform_tags.split(".")
        )
    )


def _archive_metadata(archive: ZipFile, suffix: str) -> str:
    """Read the one required dist-info metadata file without extracting it."""
    matches = sorted(
        name
        for name in archive.namelist()
        if name.endswith(suffix) and ".dist-info/" in name
    )
    if len(matches) != 1:
        raise EvidenceError(
            f"Expected exactly one .dist-info/{suffix} file, found {matches!r}."
        )
    return archive.read(matches[0]).decode("utf-8")


def inspect_wheel(wheel_path: Path) -> dict[str, Any]:
    """Inspect one wheel's filename, metadata, tags, and native members."""
    resolved_wheel = wheel_path.resolve()
    if not resolved_wheel.is_file():
        raise EvidenceError(f"Wheel does not exist: {resolved_wheel}")

    filename_tags = _wheel_filename_tags(resolved_wheel)
    with ZipFile(resolved_wheel) as archive:
        wheel_headers = Parser().parsestr(_archive_metadata(archive, "WHEEL"))
        package_headers = Parser().parsestr(_archive_metadata(archive, "METADATA"))
        wheel_tags = tuple(sorted(wheel_headers.get_all("Tag", [])))
        native_members = tuple(
            sorted(name for name in archive.namelist() if _is_native_member(name))
        )

    if not wheel_tags:
        raise EvidenceError(f"Wheel metadata has no Tag header: {resolved_wheel.name}")
    if filename_tags != wheel_tags:
        raise EvidenceError(
            f"Wheel tag mismatch for {resolved_wheel.name}: filename tags "
            f"{list(filename_tags)!r} disagree with WHEEL tags {list(wheel_tags)!r}."
        )

    universal_tags = ("py3-none-any",)
    if filename_tags == universal_tags:
        if native_members:
            raise EvidenceError(
                f"Universal pure wheel {resolved_wheel.name} contains native member(s): "
                f"{list(native_members)!r}."
            )
        mode = "pure"
    else:
        if not native_members:
            raise EvidenceError(
                f"Platform wheel {resolved_wheel.name} has no native members and "
                "cannot be classified as compiled evidence."
            )
        mode = "compiled"

    package_version = package_headers.get("Version")
    if not package_version:
        raise EvidenceError(
            f"Wheel METADATA has no Version header: {resolved_wheel.name}"
        )
    return {
        "normalized_basename": resolved_wheel.name.lower(),
        "filename_tags": list(filename_tags),
        "wheel_tags": list(wheel_tags),
        "metadata_version": package_version,
        "native_members": list(native_members),
        "mode": mode,
    }


def verify_wheels(wheel_paths: Iterable[Path]) -> dict[str, list[dict[str, Any]]]:
    """Collect deterministic independent evidence for a repeated wheel input."""
    artifacts = [inspect_wheel(path) for path in wheel_paths]
    artifacts.sort(
        key=lambda artifact: (
            artifact["normalized_basename"],
            tuple(artifact["filename_tags"]),
        )
    )
    normalized_basenames = [artifact["normalized_basename"] for artifact in artifacts]
    duplicates = sorted(
        name
        for name in set(normalized_basenames)
        if normalized_basenames.count(name) > 1
    )
    if duplicates:
        raise EvidenceError(
            "Duplicate normalized wheel artifact identities: " + ", ".join(duplicates)
        )
    return {"artifacts": artifacts}


def _emit(payload: dict[str, Any], as_json: bool) -> None:
    """Write deterministic CLI output without exposing the caller environment."""
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    print(json.dumps(payload, indent=2, sort_keys=True))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    verify_source_parser = commands.add_parser(
        "verify-source", help="fail closed when core.py is shadowed by native output"
    )
    verify_source_parser.add_argument(
        "--source-root",
        type=Path,
        default=REPOSITORY_ROOT / "src",
        help="source directory containing the fast_fsm package (default: repository src)",
    )
    verify_source_parser.add_argument("--json", action="store_true")

    verify_wheel_parser = commands.add_parser(
        "verify-wheel", help="classify repeated wheel archives without extraction"
    )
    verify_wheel_parser.add_argument(
        "--wheel",
        type=Path,
        action="append",
        required=True,
        help="wheel archive to inspect",
    )
    verify_wheel_parser.add_argument("--json", action="store_true")
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    """Run a release-evidence subcommand and convert domain errors to exit 1."""
    parser = _build_parser()
    parsed = parser.parse_args(arguments)
    try:
        if parsed.command == "verify-source":
            _emit(verify_source(parsed.source_root), parsed.json)
        elif parsed.command == "verify-wheel":
            _emit(verify_wheels(parsed.wheel), parsed.json)
        else:  # pragma: no cover - argparse constrains this branch.
            parser.error(f"Unknown command: {parsed.command}")
    except EvidenceError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
