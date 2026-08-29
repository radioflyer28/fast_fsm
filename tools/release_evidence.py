"""Non-destructive maintainer checks for source and wheel release evidence."""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from email.parser import Parser
import importlib
from importlib import machinery, metadata
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import tempfile
from typing import Any, Iterable, Mapping, Sequence
from zipfile import ZipFile
from xml.etree import ElementTree


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
PACKAGE_NAME = "fast_fsm"
CORE_MODULE_NAME = f"{PACKAGE_NAME}.core"
REQUIRED_UV_VERSION = "0.12.6"
MANIFEST_SCHEMA_VERSION = 1

_RELEASE_TAG_PATTERN = re.compile(r"^v\d+\.\d+\.\d+$")
_RELEASE_HISTORY_FACTS = (
    "defective 0.2.2 package metadata",
    "remains a shipped release",
    "existing v0.2.3 tag and published artifacts are immutable and unchanged",
    "v0.3.0",
)

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


def _run_git_history_command(arguments: Sequence[str], *, repository_root: Path) -> str:
    """Read historical Git evidence with argument-array subprocess safety."""
    completed = subprocess.run(
        ["git", "-C", str(repository_root), *arguments],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        rendered = " ".join(arguments)
        raise EvidenceError(
            f"Release-history Git command failed ({completed.returncode}): {rendered}\n"
            f"{completed.stderr.strip()}"
        )
    return completed.stdout


def _require_release_history_facts(text: str, *, artifact_name: str) -> None:
    """Require canonical immutable-history facts in a mutable correction artifact."""
    normalized = re.sub(r"\s+", " ", text.casefold())
    missing = [fact for fact in _RELEASE_HISTORY_FACTS if fact not in normalized]
    if missing:
        rendered = "\n".join(f"  - {fact}" for fact in missing)
        raise EvidenceError(
            f"{artifact_name} is missing required immutable-history facts:\n{rendered}"
        )


def _require_dated_release_section(changelog: str, version: str) -> None:
    """Require a dated Keep-a-Changelog section for a shipped release."""
    pattern = re.compile(
        rf"^## \[{re.escape(version)}\] — \d{{4}}-\d{{2}}-\d{{2}}$",
        flags=re.MULTILINE,
    )
    if not pattern.search(changelog):
        raise EvidenceError(
            f"CHANGELOG.md is missing dated {version} section; expected "
            f"'## [{version}] — YYYY-MM-DD'."
        )


def _tag_pyproject_version(tag: str, *, repository_root: Path) -> str:
    """Read the immutable tagged package version without changing Git state."""
    pyproject = _run_git_history_command(
        ["show", f"{tag}:pyproject.toml"], repository_root=repository_root
    )
    version_match = re.search(r'^version\s*=\s*"([^"]+)"\s*$', pyproject, re.MULTILINE)
    if not version_match:
        raise EvidenceError(f"{tag}:pyproject.toml does not declare [project] version.")
    return version_match.group(1)


def verify_history(
    *, tag: str, correction_path: Path, repository_root: Path | None = None
) -> dict[str, str]:
    """Audit the immutable v0.2.3 metadata mismatch and additive correction.

    This command only reads Git objects and repository text. It deliberately
    refuses to retag, rewrite artifacts, or infer correction facts from mutable
    prose that does not state the complete immutable-history policy.
    """
    if not _RELEASE_TAG_PATTERN.fullmatch(tag):
        raise EvidenceError(f"Expected a version tag such as 'v0.2.3', got {tag!r}.")

    root = (repository_root or REPOSITORY_ROOT).resolve()
    resolved_correction = correction_path.resolve()
    correction_relative = _normalized_relative_path(resolved_correction, root)
    try:
        correction = resolved_correction.read_text(encoding="utf-8")
        changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    except OSError as error:
        raise EvidenceError(
            f"Could not read release-history artifact: {error}"
        ) from error

    _require_dated_release_section(changelog, "0.2.2")
    _require_dated_release_section(changelog, tag.removeprefix("v"))
    _require_release_history_facts(correction, artifact_name=correction_relative)
    _require_release_history_facts(changelog, artifact_name="CHANGELOG.md")

    tag_object = _run_git_history_command(
        ["rev-parse", "--verify", f"{tag}^{{}}"], repository_root=root
    ).strip()
    tagged_version = _tag_pyproject_version(tag, repository_root=root)
    if tagged_version != "0.2.2":
        raise EvidenceError(
            f"Expected {tag}:pyproject.toml to declare defective 0.2.2 metadata, "
            f"observed {tagged_version!r}."
        )

    return {
        "tag": tag,
        "tag_target": tag_object,
        "tag_pyproject_version": tagged_version,
        "correction_path": correction_relative,
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
        "filename": resolved_wheel.name,
        "normalized_basename": resolved_wheel.name.lower(),
        "filename_tags": list(filename_tags),
        "archive_tags": list(wheel_tags),
        "wheel_tags": list(wheel_tags),
        "metadata_version": package_version,
        "native_members": list(native_members),
        "classified_mode": mode,
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


def serialize_manifest(manifest: Mapping[str, Any]) -> str:
    """Render evidence as one stable JSON document with exactly one newline."""
    return json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def _render_field_value(value: Any) -> str:
    """Make a compact, deterministic field-level diff value."""
    return json.dumps(value, sort_keys=True, ensure_ascii=True)


def _python_major_minor(version: Any) -> str:
    """Return a fail-closed major.minor identity from an exact Python version."""
    if not isinstance(version, str):
        raise EvidenceError("Manifest has malformed toolchain.python identity.")
    components = version.split(".")
    if len(components) != 3 or not all(component.isdigit() for component in components):
        raise EvidenceError("Manifest has malformed toolchain.python identity.")
    return f"{int(components[0])}.{int(components[1])}"


def _stable_manifest(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Return fields whose equality defines evidence freshness.

    Platform/runtime observations are retained for audit context, but a different
    runner must not churn a stable release baseline merely because its host or
    timing characteristics differ.
    """
    stable = json.loads(serialize_manifest(manifest))
    stable.pop("measurement_environment", None)
    toolchain = stable.get("toolchain")
    if isinstance(toolchain, dict) and "python" in toolchain:
        toolchain["python"] = _python_major_minor(toolchain["python"])
    return stable


def compare_manifests(
    expected: Mapping[str, Any], observed: Mapping[str, Any]
) -> list[str]:
    """Return deterministic, actionable stable-field differences.

    Lists deliberately compare as whole values. Their members are evidence
    collections whose deterministic sort order is part of the release contract.
    """
    differences: list[str] = []

    def compare(expected_value: Any, observed_value: Any, path: str) -> None:
        if isinstance(expected_value, Mapping) and isinstance(observed_value, Mapping):
            for key in sorted(set(expected_value) | set(observed_value)):
                key_path = f"{path}.{key}" if path else str(key)
                if key not in expected_value:
                    differences.append(
                        f"{key_path}: expected <missing>, observed "
                        f"{_render_field_value(observed_value[key])}"
                    )
                elif key not in observed_value:
                    differences.append(
                        f"{key_path}: expected {_render_field_value(expected_value[key])}, "
                        "observed <missing>"
                    )
                else:
                    compare(expected_value[key], observed_value[key], key_path)
            return
        if expected_value != observed_value:
            differences.append(
                f"{path}: expected {_render_field_value(expected_value)}, observed "
                f"{_render_field_value(observed_value)}"
            )

    compare(_stable_manifest(expected), _stable_manifest(observed), "")
    return differences


def validate_manifest_regressions(
    baseline: Mapping[str, Any], observed: Mapping[str, Any]
) -> None:
    """Reject source-coverage regressions before considering baseline freshness."""
    try:
        baseline_coverage = baseline["quality_baseline"]["coverage"]
        observed_coverage = observed["quality_baseline"]["coverage"]
    except (KeyError, TypeError) as error:
        raise EvidenceError("Manifest is missing quality_baseline.coverage.") from error

    for field in ("total_percent", "core_percent"):
        try:
            expected_value = round(float(baseline_coverage[field]), 2)
            observed_value = round(float(observed_coverage[field]), 2)
        except (KeyError, TypeError, ValueError) as error:
            raise EvidenceError(
                f"Manifest is missing numeric quality_baseline.coverage.{field}."
            ) from error
        if observed_value < expected_value:
            raise EvidenceError(
                f"coverage regression at quality_baseline.coverage.{field}: "
                f"expected at least {expected_value:.2f}, observed {observed_value:.2f}"
            )


def _command_environment() -> dict[str, str]:
    """Force pure mode without leaking ambient environment into evidence."""
    environment = dict(os.environ)
    environment["FAST_FSM_BUILD_MODE"] = "pure"
    environment.pop("FAST_FSM_PURE_PYTHON", None)
    return environment


def _run_checked(
    arguments: Sequence[str], *, cwd: Path, environment: Mapping[str, str]
) -> str:
    """Run one controlled evidence command with argument-array safety."""
    completed = subprocess.run(
        list(arguments),
        cwd=cwd,
        env=dict(environment),
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        rendered = " ".join(arguments)
        raise EvidenceError(
            f"Evidence subprocess failed ({completed.returncode}): {rendered}\n"
            f"{completed.stderr.strip()}"
        )
    return completed.stdout


def _parse_junit_results(junit_path: Path) -> dict[str, int]:
    """Parse exact pytest outcomes from JUnit XML rather than console text."""
    try:
        root = ElementTree.parse(junit_path).getroot()
    except (ElementTree.ParseError, OSError) as error:
        raise EvidenceError(
            f"Could not parse pytest JUnit XML: {junit_path}"
        ) from error

    suites = [
        suite
        for suite in root.iter("testsuite")
        if not any(child.tag == "testsuite" for child in suite)
    ]
    if not suites:
        raise EvidenceError("JUnit XML contained no leaf testsuite results.")

    def total(attribute: str) -> int:
        try:
            return sum(int(suite.attrib.get(attribute, "0")) for suite in suites)
        except ValueError as error:
            raise EvidenceError(
                f"JUnit XML has invalid {attribute!r} count."
            ) from error

    collected = total("tests")
    failures = total("failures")
    errors = total("errors")
    skipped = total("skipped")
    passed = collected - failures - errors - skipped
    if collected <= 0 or passed < 0:
        raise EvidenceError("JUnit XML reported inconsistent test outcome counts.")
    return {
        "collected": collected,
        "passed": passed,
        "failed": failures,
        "errors": errors,
        "skipped": skipped,
    }


def _coverage_percentages(coverage_path: Path) -> dict[str, float]:
    """Read rounded total and core.py source coverage from pytest-cov JSON."""
    try:
        payload = json.loads(coverage_path.read_text(encoding="utf-8"))
        total_percent = float(payload["totals"]["percent_covered"])
        core_entry = next(
            entry
            for source_path, entry in payload["files"].items()
            if Path(source_path).as_posix().endswith("src/fast_fsm/core.py")
        )
        core_percent = float(core_entry["summary"]["percent_covered"])
    except (KeyError, OSError, StopIteration, TypeError, ValueError) as error:
        raise EvidenceError(
            "Coverage JSON is missing total or src/fast_fsm/core.py source coverage."
        ) from error
    return {
        "total_percent": round(total_percent, 2),
        "core_percent": round(core_percent, 2),
    }


def _distribution_version(distribution: str) -> str:
    """Read one resolved package version with a useful missing-tool error."""
    try:
        return metadata.version(distribution)
    except metadata.PackageNotFoundError as error:
        raise EvidenceError(
            f"Required evidence tool {distribution!r} is not installed in the locked environment."
        ) from error


def _locked_package_version(package_name: str, lock_path: Path | None = None) -> str:
    """Read one resolved package version from uv.lock without a runtime import.

    Build-system requirements are installed in uv's isolated build environment,
    not necessarily in the project environment.  Their evidence must therefore
    come from the reviewed lock instead of turning a build tool into a runtime
    dependency merely to ask it for ``__version__``.
    """
    path = lock_path or REPOSITORY_ROOT / "uv.lock"
    try:
        sections = path.read_text(encoding="utf-8").split("[[package]]")
    except OSError as error:
        raise EvidenceError(f"Could not read resolved lock file {path}.") from error
    name_marker = f'name = "{package_name}"'
    for section in sections[1:]:
        section_lines = [line for line in section.splitlines() if line]
        if not section_lines or section_lines[0] != name_marker:
            continue
        for line in section_lines:
            if line.startswith("version = "):
                return line.split('"', 2)[1]
    raise EvidenceError(f"Resolved package {package_name!r} is missing from {path}.")


def _resolved_uv_version(*, environment: Mapping[str, str]) -> str:
    """Return and validate the exact uv executable version for this phase."""
    stdout = _run_checked(
        ["uv", "--version"], cwd=REPOSITORY_ROOT, environment=environment
    )
    parts = stdout.strip().split()
    if len(parts) < 2 or parts[0] != "uv":
        raise EvidenceError(f"Could not parse uv version output: {stdout!r}")
    version = parts[1]
    if version != REQUIRED_UV_VERSION:
        raise EvidenceError(
            f"Release evidence requires uv {REQUIRED_UV_VERSION}, resolved {version}."
        )
    return version


def _source_preflight(
    *, source_root: Path, environment: Mapping[str, str]
) -> dict[str, str]:
    """Run the native-shadow/source-origin proof before any collection command."""
    output = _run_checked(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "verify-source",
            "--source-root",
            str(source_root),
            "--json",
        ],
        cwd=REPOSITORY_ROOT,
        environment=environment,
    )
    try:
        payload = json.loads(output)
    except json.JSONDecodeError as error:
        raise EvidenceError(
            "Source preflight did not emit valid JSON evidence."
        ) from error
    if not str(payload.get("core_origin", "")).endswith(".py"):
        raise EvidenceError("Source preflight did not prove a core.py module origin.")
    return {str(key): str(value) for key, value in payload.items()}


def _collect_test_and_coverage(
    *, environment: Mapping[str, str]
) -> tuple[dict[str, int], dict[str, float]]:
    """Collect test and coverage facts only after source preflight succeeded."""
    with tempfile.TemporaryDirectory(prefix="fast-fsm-evidence-") as temp_directory:
        temporary_root = Path(temp_directory)
        junit_path = temporary_root / "pytest.xml"
        coverage_path = temporary_root / "coverage.json"
        _run_checked(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/",
                "-x",
                "-q",
                f"--junitxml={junit_path}",
                "--cov=src/fast_fsm",
                f"--cov-report=json:{coverage_path}",
            ],
            cwd=REPOSITORY_ROOT,
            environment=environment,
        )
        return _parse_junit_results(junit_path), _coverage_percentages(coverage_path)


def collect_manifest(
    *, source_root: Path | None = None, wheel_paths: Iterable[Path] = ()
) -> dict[str, Any]:
    """Collect the schema-v1 release baseline in a deterministic shape.

    The source preflight is intentionally the first subprocess action.  All
    later tool, test, coverage, and wheel observations inherit explicit pure
    mode, preventing a native build residue from being certified as source.
    """
    resolved_source_root = (source_root or REPOSITORY_ROOT / "src").resolve()
    environment = _command_environment()
    source = _source_preflight(
        source_root=resolved_source_root, environment=environment
    )
    tests, coverage = _collect_test_and_coverage(environment=environment)
    wheel_artifacts = verify_wheels(wheel_paths)["artifacts"]
    slots = slots_policy(resolved_source_root)
    uv_version = _resolved_uv_version(environment=environment)

    toolchain = {
        "python": sys.version.split()[0],
        "uv": uv_version,
        "pytest": _distribution_version("pytest"),
        "pytest_cov": _distribution_version("pytest-cov"),
        "ruff": _distribution_version("ruff"),
        "mypy": _locked_package_version("mypy"),
        "mypyc": _locked_package_version("mypy"),
        "ty": _distribution_version("ty"),
        "sphinx": _distribution_version("sphinx"),
        "setuptools": _locked_package_version("setuptools"),
        "wheel": _locked_package_version("wheel"),
    }
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "release_identity": {
            "package": PACKAGE_NAME,
            "distribution_version": source["distribution_version"],
        },
        "quality_baseline": {
            "build_mode": "pure",
            "tests": tests,
            "coverage": coverage,
            "source": {"core_origin": source["core_origin"]},
        },
        "toolchain": toolchain,
        "artifact_evidence": {
            "wheels": wheel_artifacts,
            "source": {"core_origin": source["core_origin"]},
        },
        "slots_policy": {
            "inventory": slots["inventory"],
            "registered_exceptions": slots["registered_exceptions"],
            "measurements": slots["representative_measurements"],
        },
        "performance_contract": {
            "compiled_trigger_ops_per_sec_min": 200000,
            "measurement": "environment-labeled; exact timing is not a freshness field",
        },
        "measurement_environment": {
            "implementation": sys.implementation.name,
            "python_version": sys.version.split()[0],
            "platform": platform.platform(),
            "machine": platform.machine(),
            "comparison": "stable fields exclude this environment observation",
        },
    }


def _read_manifest(path: Path) -> dict[str, Any]:
    """Load a tracked manifest without normalizing its source bytes."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise EvidenceError(f"Could not read manifest {path}: {error}") from error
    if not isinstance(payload, dict):
        raise EvidenceError(f"Manifest {path} must contain a JSON object.")
    return payload


def _write_manifest(path: Path, manifest: Mapping[str, Any]) -> None:
    """Write only the explicitly selected baseline path with deterministic bytes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialize_manifest(manifest), encoding="utf-8")


def write_or_check_manifest(
    manifest: Mapping[str, Any], *, manifest_path: Path, write: bool
) -> dict[str, Any]:
    """Intentionally write a baseline or compare it without mutating its bytes."""
    if write:
        _write_manifest(manifest_path, manifest)
        return dict(manifest)

    baseline = _read_manifest(manifest_path)
    validate_manifest_regressions(baseline, manifest)
    differences = compare_manifests(baseline, manifest)
    if differences:
        raise EvidenceError(
            "Release evidence manifest is stale:\n"
            + "\n".join(f"  - {difference}" for difference in differences)
        )
    return dict(manifest)


def _render_summary(manifest: Mapping[str, Any]) -> str:
    """Return a compact human-readable evidence summary."""
    baseline = manifest["quality_baseline"]
    tests = baseline["tests"]
    coverage = baseline["coverage"]
    return "\n".join(
        [
            f"Release evidence schema: {manifest['schema_version']}",
            f"Pure tests: {tests['passed']}/{tests['collected']} passed",
            "Source coverage: "
            f"total {coverage['total_percent']:.2f}%, core.py {coverage['core_percent']:.2f}%",
            f"uv: {manifest['toolchain']['uv']}",
            f"core origin: {baseline['source']['core_origin']}",
        ]
    )


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

    history_parser = commands.add_parser(
        "verify-history",
        help="audit an immutable release tag against its additive correction",
    )
    history_parser.add_argument("--tag", required=True, help="immutable release tag")
    history_parser.add_argument(
        "--correction",
        type=Path,
        required=True,
        help="canonical correction record under the repository root",
    )
    history_parser.add_argument("--json", action="store_true")

    evidence_parser = commands.add_parser(
        "evidence", help="write or non-destructively check release baseline evidence"
    )
    evidence_mode = evidence_parser.add_mutually_exclusive_group(required=True)
    evidence_mode.add_argument(
        "--write", action="store_true", help="intentionally regenerate the manifest"
    )
    evidence_mode.add_argument(
        "--check",
        action="store_true",
        help="compare in-memory evidence without writing",
    )
    evidence_parser.add_argument(
        "--manifest",
        type=Path,
        default=REPOSITORY_ROOT / "evidence" / "release-baseline.json",
        help="tracked manifest path (default: evidence/release-baseline.json)",
    )
    evidence_parser.add_argument(
        "--wheel",
        type=Path,
        action="append",
        default=[],
        help="wheel archive to preserve as independent artifact evidence (repeatable)",
    )
    evidence_parser.add_argument(
        "--summary",
        type=Path,
        help="optional explicitly requested human-readable summary output path",
    )
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
        elif parsed.command == "verify-history":
            _emit(
                verify_history(tag=parsed.tag, correction_path=parsed.correction),
                parsed.json,
            )
        elif parsed.command == "evidence":
            manifest = collect_manifest(wheel_paths=parsed.wheel)
            write_or_check_manifest(
                manifest, manifest_path=parsed.manifest, write=parsed.write
            )
            summary = _render_summary(manifest)
            if parsed.summary:
                parsed.summary.write_text(summary + "\n", encoding="utf-8")
            print(summary)
        else:  # pragma: no cover - argparse constrains this branch.
            parser.error(f"Unknown command: {parsed.command}")
    except EvidenceError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
