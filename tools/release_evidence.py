"""Non-destructive maintainer checks for source and wheel release evidence."""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from email.parser import Parser
import importlib
from importlib import machinery, metadata
import json
from pathlib import Path
import sys
from typing import Any, Iterable, Mapping, Sequence
from zipfile import ZipFile


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
PACKAGE_NAME = "fast_fsm"
CORE_MODULE_NAME = f"{PACKAGE_NAME}.core"

REGISTERED_SLOTS_EXCEPTIONS: Mapping[str, str] = {
    "fast_fsm.core.CompiledFuncCondition": (
        "@mypyc_attr(native_class=False) preserves the interpreted Condition "
        "inheritance boundary."
    ),
    "fast_fsm.core.TransitionError": (
        "@mypyc_attr(native_class=False) preserves normal Python exception behavior."
    ),
}


class EvidenceError(RuntimeError):
    """Raised when local release evidence is incomplete or contradictory."""


@dataclass(frozen=True)
class ClassDeclaration:
    """A top-level class declaration discovered by the static slots inventory."""

    qualified_name: str
    source_path: str
    line: int
    base_names: tuple[str, ...]
    has_own_slots: bool


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


def _module_name_for_path(source_root: Path, source_file: Path) -> str:
    """Map an importable package path to its module name."""
    relative = source_file.relative_to(source_root).with_suffix("")
    parts = list(relative.parts)
    if parts and parts[0] == PACKAGE_NAME:
        parts.pop(0)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join([PACKAGE_NAME, *parts])


def _base_names(class_node: ast.ClassDef) -> tuple[str, ...]:
    """Extract simple local base names for static inheritance resolution."""
    names: list[str] = []
    for base in class_node.bases:
        if isinstance(base, ast.Name):
            names.append(base.id)
        elif isinstance(base, ast.Attribute):
            names.append(base.attr)
    return tuple(names)


def _has_own_slots(class_node: ast.ClassDef) -> bool:
    """Recognize ``__slots__`` and ``@dataclass(slots=True)`` declarations."""
    for statement in class_node.body:
        if isinstance(statement, ast.Assign):
            if any(
                isinstance(target, ast.Name) and target.id == "__slots__"
                for target in statement.targets
            ):
                return True
        elif isinstance(statement, ast.AnnAssign):
            if (
                isinstance(statement.target, ast.Name)
                and statement.target.id == "__slots__"
            ):
                return True

    for decorator in class_node.decorator_list:
        if not isinstance(decorator, ast.Call):
            continue
        decorator_name = (
            decorator.func.id
            if isinstance(decorator.func, ast.Name)
            else decorator.func.attr
            if isinstance(decorator.func, ast.Attribute)
            else ""
        )
        if decorator_name != "dataclass":
            continue
        if any(
            keyword.arg == "slots"
            and isinstance(keyword.value, ast.Constant)
            and keyword.value.value is True
            for keyword in decorator.keywords
        ):
            return True
    return False


def collect_class_declarations(source_root: Path) -> list[ClassDeclaration]:
    """Recursively collect importable top-level production classes from source."""
    resolved_source_root = source_root.resolve()
    package_root = resolved_source_root / PACKAGE_NAME
    if not package_root.is_dir():
        raise EvidenceError(f"Package directory does not exist: {package_root}")

    declarations: list[ClassDeclaration] = []
    for source_file in sorted(package_root.rglob("*.py")):
        source = source_file.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(source_file))
        module_name = _module_name_for_path(resolved_source_root, source_file)
        source_path = _normalized_relative_path(
            source_file, resolved_source_root.parent
        )
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            declarations.append(
                ClassDeclaration(
                    qualified_name=f"{module_name}.{node.name}",
                    source_path=source_path,
                    line=node.lineno,
                    base_names=_base_names(node),
                    has_own_slots=_has_own_slots(node),
                )
            )
    return sorted(declarations, key=lambda declaration: declaration.qualified_name)


def _is_inherited_slot_protected(
    declaration: ClassDeclaration,
    declarations_by_short_name: Mapping[str, ClassDeclaration],
    visited: set[str] | None = None,
) -> bool:
    """Return whether a declaration inherits slots from a local ancestor."""
    seen = set() if visited is None else visited
    if declaration.qualified_name in seen:
        return False
    seen.add(declaration.qualified_name)
    for base_name in declaration.base_names:
        base = declarations_by_short_name.get(base_name)
        if base is None:
            continue
        if base.has_own_slots or _is_inherited_slot_protected(
            base, declarations_by_short_name, seen
        ):
            return True
    return False


def validate_slots_inventory(
    declarations: Iterable[ClassDeclaration],
    registry: Mapping[str, str] = REGISTERED_SLOTS_EXCEPTIONS,
) -> list[dict[str, Any]]:
    """Classify every discovered class or fail on stale/un-slotted entries."""
    ordered_declarations = sorted(declarations, key=lambda item: item.qualified_name)
    declarations_by_name = {
        declaration.qualified_name: declaration for declaration in ordered_declarations
    }
    declarations_by_short_name = {
        declaration.qualified_name.rsplit(".", 1)[-1]: declaration
        for declaration in ordered_declarations
    }
    stale_entries = sorted(set(registry) - set(declarations_by_name))
    if stale_entries:
        raise EvidenceError(
            "Registered slots-policy exception(s) no longer exist in source: "
            + ", ".join(stale_entries)
        )

    inventory: list[dict[str, Any]] = []
    unprotected: list[ClassDeclaration] = []
    for declaration in ordered_declarations:
        entry: dict[str, Any] = {
            "qualified_name": declaration.qualified_name,
            "source_path": declaration.source_path,
            "line": declaration.line,
        }
        exception_reason = registry.get(declaration.qualified_name)
        if exception_reason is not None:
            entry.update(
                classification="registered-exception", exception_reason=exception_reason
            )
        elif declaration.has_own_slots:
            entry["classification"] = "slot-protected"
        elif _is_inherited_slot_protected(declaration, declarations_by_short_name):
            entry["classification"] = "inherited-slot-protected"
        else:
            unprotected.append(declaration)
            continue
        inventory.append(entry)

    if unprotected:
        locations = "\n".join(
            f"  - {item.qualified_name} ({item.source_path}:{item.line})"
            for item in unprotected
        )
        raise EvidenceError(
            "Unregistered instance-__dict__ class(es) in slots-policy inventory:\n"
            + locations
        )
    return inventory


def _measure_instance(instance: object) -> dict[str, Any]:
    """Return deliberate, environment-labeled instance memory evidence."""
    return {
        "has_instance_dict": hasattr(instance, "__dict__"),
        "instance_size_bytes": sys.getsizeof(instance),
    }


def _slots_measurements(
    source_root: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Instantiate registered and representative classes without exposing internals."""
    source_root_text = str(source_root.resolve())
    if source_root_text not in sys.path:
        sys.path.insert(0, source_root_text)
    importlib.invalidate_caches()
    core = importlib.import_module(CORE_MODULE_NAME)

    registered_instances = {
        "fast_fsm.core.CompiledFuncCondition": core.CompiledFuncCondition(
            lambda **_kwargs: True
        ),
        "fast_fsm.core.TransitionError": core.TransitionError(
            core.TransitionResult(False)
        ),
    }
    registered = [
        {
            "qualified_name": qualified_name,
            "exception_reason": REGISTERED_SLOTS_EXCEPTIONS[qualified_name],
            **_measure_instance(instance),
        }
        for qualified_name, instance in sorted(registered_instances.items())
    ]
    representatives = [
        {
            "qualified_name": "fast_fsm.core.State",
            **_measure_instance(core.State("slots-policy")),
        },
        {
            "qualified_name": "fast_fsm.core.TransitionResult",
            **_measure_instance(core.TransitionResult(True)),
        },
    ]
    return registered, representatives


def slots_policy(source_root: Path | None = None) -> dict[str, Any]:
    """Produce a complete static and measured slots-policy inventory."""
    resolved_source_root = (source_root or REPOSITORY_ROOT / "src").resolve()
    declarations = collect_class_declarations(resolved_source_root)
    inventory = validate_slots_inventory(declarations)
    registered, representatives = _slots_measurements(resolved_source_root)
    return {
        "inventory": inventory,
        "registered_exceptions": registered,
        "representative_measurements": representatives,
        "measurement_environment": {
            "implementation": sys.implementation.name,
            "python_version": sys.version.split()[0],
        },
    }


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

    slots_policy_parser = commands.add_parser(
        "slots-policy", help="recursively audit source classes against the slots policy"
    )
    slots_policy_parser.add_argument(
        "--source-root",
        type=Path,
        default=REPOSITORY_ROOT / "src",
        help="source directory containing the fast_fsm package (default: repository src)",
    )
    slots_policy_parser.add_argument("--json", action="store_true")
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
        elif parsed.command == "slots-policy":
            _emit(slots_policy(parsed.source_root), parsed.json)
        else:  # pragma: no cover - argparse constrains this branch.
            parser.error(f"Unknown command: {parsed.command}")
    except EvidenceError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
