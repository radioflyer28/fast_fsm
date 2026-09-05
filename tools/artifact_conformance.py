"""Checkout-independent deterministic conformance collector for Fast FSM artifacts.

The collector deliberately imports only the installed :mod:`fast_fsm` package
and the standard library.  Its semantic record is made entirely of documented,
payload-free scalar observations so it can be compared across source, pure-wheel,
and compiled-wheel executions.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
from importlib import machinery, metadata
import json
from pathlib import Path
import platform
import sys
from typing import Any, Callable, Mapping, Sequence


SCHEMA_VERSION = 1
_PACKAGE_NAME = "fast_fsm"
_CORE_MODULE_NAME = f"{_PACKAGE_NAME}.core"
_SCENARIO_FIELDS = (
    "id",
    "family",
    "success",
    "committed",
    "stage",
    "state",
    "callback_order",
    "history",
    "redacted",
)
_SCENARIO_DEFINITIONS = (
    {
        "id": "lifecycle.destination-enter-failure",
        "family": "lifecycle-result-history",
        "fields": _SCENARIO_FIELDS,
    },
)
_PAYLOAD_SENTINELS = ("caller-secret", "destination-secret", "observer-secret")


class ConformanceError(RuntimeError):
    """Raised when a deterministic conformance contract is contradicted."""


def canonical_json(value: Mapping[str, Any]) -> str:
    """Serialize one evidence object with canonical, finite JSON semantics."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _sha256(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _suite_sha256() -> str:
    return _sha256(
        {
            "schema_version": SCHEMA_VERSION,
            "scenario_definitions": list(_SCENARIO_DEFINITIONS),
        }
    )


def _lifecycle_destination_enter_failure() -> dict[str, Any]:
    """Exercise the committed post-destination-enter failure contract."""
    core = importlib.import_module(_CORE_MODULE_NAME)
    callback_state = core.CallbackState
    state_machine = core.StateMachine

    callback_order: list[str] = []
    destination_secret = "destination-secret"
    observer_secret = "observer-secret"

    def source_exit(*_args: object, **_kwargs: object) -> None:
        callback_order.append("source-exit")

    def destination_enter(*_args: object, **_kwargs: object) -> None:
        callback_order.append("destination-enter")
        raise RuntimeError(destination_secret)

    source = callback_state("source", on_exit=source_exit)
    destination = callback_state("destination", on_enter=destination_enter)
    machine = state_machine(source, name="artifact-conformance-lifecycle")
    machine.add_state(destination)
    machine.add_transition("advance", "source", "destination")
    machine.enable_history()

    def first_observer(
        _trigger: str, _from_state: str, _error: str, **_kwargs: object
    ) -> None:
        callback_order.append("observer-one")
        raise RuntimeError(observer_secret)

    def second_observer(
        _trigger: str, _from_state: str, _error: str, **_kwargs: object
    ) -> None:
        callback_order.append("observer-two")

    machine.on_failed(first_observer)
    machine.on_failed(second_observer)
    result = machine.trigger("advance", payload="caller-secret")

    history = [
        [record.from_state, record.trigger, record.to_state]
        for record in machine.history
    ]
    return {
        "id": "lifecycle.destination-enter-failure",
        "family": "lifecycle-result-history",
        "success": result.success,
        "committed": result.committed,
        "stage": result.stage,
        "state": machine.current_state.name,
        "callback_order": callback_order,
        "history": history,
        "redacted": all(
            sentinel not in repr(result) for sentinel in _PAYLOAD_SENTINELS
        ),
    }


def _scenario_collectors() -> tuple[Callable[[], dict[str, Any]], ...]:
    """Return ordered standalone scenario adapters; later families extend this seam."""
    return (_lifecycle_destination_enter_failure,)


def _validate_scenarios(scenarios: Sequence[Mapping[str, Any]]) -> None:
    """Reject unknown, missing, duplicate, or non-allowlisted tracer records."""
    expected_by_id = {
        str(definition["id"]): definition for definition in _SCENARIO_DEFINITIONS
    }
    ids = [str(record.get("id", "")) for record in scenarios]
    if len(ids) != len(set(ids)):
        raise ConformanceError("Conformance scenario inventory has duplicate IDs.")
    if set(ids) != set(expected_by_id):
        raise ConformanceError(
            "Conformance scenario inventory does not match the required set."
        )
    if ids != sorted(ids):
        raise ConformanceError("Conformance scenario inventory is not sorted by ID.")
    for record in scenarios:
        identifier = str(record.get("id", ""))
        expected = expected_by_id[identifier]
        expected_fields = tuple(expected["fields"])
        if tuple(record) != expected_fields:
            raise ConformanceError(
                f"Conformance scenario {identifier} has unexpected fields."
            )
        if record["family"] != expected["family"]:
            raise ConformanceError(
                f"Conformance scenario {identifier} has wrong family."
            )
        if not isinstance(record["callback_order"], list) or not all(
            isinstance(value, str) for value in record["callback_order"]
        ):
            raise ConformanceError(
                f"Conformance scenario {identifier} has invalid callback order."
            )
        if not isinstance(record["history"], list) or not all(
            isinstance(value, list)
            and len(value) == 3
            and all(isinstance(part, str) for part in value)
            for value in record["history"]
        ):
            raise ConformanceError(
                f"Conformance scenario {identifier} has invalid history."
            )
        if not isinstance(record["success"], bool) or not isinstance(
            record["committed"], bool
        ):
            raise ConformanceError(
                f"Conformance scenario {identifier} has invalid result flags."
            )
        if not isinstance(record["stage"], str) or not isinstance(record["state"], str):
            raise ConformanceError(
                f"Conformance scenario {identifier} has invalid scalar outcome."
            )
        if not isinstance(record["redacted"], bool):
            raise ConformanceError(
                f"Conformance scenario {identifier} has invalid redaction verdict."
            )


def validate_conformance(payload: Mapping[str, Any]) -> None:
    """Check a child semantic object before a parent accepts it as evidence."""
    if tuple(payload) != (
        "schema_version",
        "suite_sha256",
        "scenarios",
        "semantic_sha256",
        "payload_leak_free",
    ):
        raise ConformanceError("Conformance object has unexpected fields.")
    if payload["schema_version"] != SCHEMA_VERSION:
        raise ConformanceError("Conformance schema version is unsupported.")
    scenarios = payload["scenarios"]
    if not isinstance(scenarios, list):
        raise ConformanceError("Conformance scenarios must be a list.")
    _validate_scenarios(scenarios)
    if payload["suite_sha256"] != _suite_sha256():
        raise ConformanceError(
            "Conformance suite digest does not match this collector."
        )
    expected_semantic = _sha256(
        {
            "schema_version": SCHEMA_VERSION,
            "suite_sha256": payload["suite_sha256"],
            "scenarios": scenarios,
        }
    )
    if payload["semantic_sha256"] != expected_semantic:
        raise ConformanceError("Conformance semantic digest does not match scenarios.")
    rendered = canonical_json(payload)
    leak_free = all(sentinel not in rendered for sentinel in _PAYLOAD_SENTINELS)
    if payload["payload_leak_free"] is not leak_free or not leak_free:
        raise ConformanceError("Conformance object failed the payload-leak verdict.")


def collect_conformance() -> dict[str, Any]:
    """Collect the stable semantic oracle independent of checkout-specific details."""
    scenarios = sorted(
        (collector() for collector in _scenario_collectors()),
        key=lambda item: item["id"],
    )
    suite_sha256 = _suite_sha256()
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "suite_sha256": suite_sha256,
        "scenarios": scenarios,
        "semantic_sha256": _sha256(
            {
                "schema_version": SCHEMA_VERSION,
                "suite_sha256": suite_sha256,
                "scenarios": scenarios,
            }
        ),
        "payload_leak_free": False,
    }
    payload["payload_leak_free"] = all(
        sentinel not in canonical_json(payload) for sentinel in _PAYLOAD_SENTINELS
    )
    validate_conformance(payload)
    return payload


def compare_conformance(
    expected: Mapping[str, Any], actual: Mapping[str, Any]
) -> list[str]:
    """Return payload-free scenario/field differences for two semantic records."""
    expected_scenarios = {
        str(record["id"]): record for record in expected.get("scenarios", [])
    }
    actual_scenarios = {
        str(record["id"]): record for record in actual.get("scenarios", [])
    }
    differences: list[str] = []
    for identifier in sorted(set(expected_scenarios) | set(actual_scenarios)):
        left = expected_scenarios.get(identifier)
        right = actual_scenarios.get(identifier)
        if left is None or right is None:
            differences.append(f"{identifier}: scenario")
            continue
        fields = sorted(set(left) | set(right))
        changed = [
            field
            for field in fields
            if field != "id" and left.get(field) != right.get(field)
        ]
        if changed:
            differences.append(f"{identifier}: {', '.join(changed)}")
    return differences


def _runtime_facts() -> dict[str, Any]:
    """Collect installed-runtime facts outside the semantic conformance digest."""
    package = importlib.import_module(_PACKAGE_NAME)
    core = importlib.import_module(_CORE_MODULE_NAME)
    package_origin = getattr(package, "__file__", None)
    core_origin = getattr(core, "__file__", None)
    if not package_origin or not core_origin:
        raise ConformanceError("Installed runtime did not expose package/core origins.")
    distribution = metadata.distribution("fast-fsm")
    direct_url_path = Path(distribution.locate_file("direct_url.json"))
    direct_url: object | None = None
    if direct_url_path.is_file():
        try:
            direct_url = json.loads(direct_url_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ConformanceError(
                "Installed direct-url metadata is malformed."
            ) from error
    loader = importlib.util.find_spec(_CORE_MODULE_NAME)
    return {
        "distribution_version": distribution.version,
        "package_version": str(getattr(package, "__version__", "")),
        "package_origin": str(Path(package_origin).resolve()),
        "core_origin": str(Path(core_origin).resolve()),
        "core_loader": type(loader.loader).__name__ if loader and loader.loader else "",
        # Keep the venv entrypoint path; resolving it follows the intentional
        # symlink to the externally managed base interpreter.
        "interpreter": str(Path(sys.executable).absolute()),
        "python_implementation": sys.implementation.name,
        "python_version": sys.version.split()[0],
        "platform": platform.system(),
        "machine": platform.machine(),
        "direct_url": direct_url,
        "extension_suffixes": sorted(machinery.EXTENSION_SUFFIXES),
    }


def collect_installed_probe() -> dict[str, Any]:
    """Return one JSON child probe with semantic records plus runtime evidence."""
    return {"conformance": collect_conformance(), "runtime": _runtime_facts()}


def main(arguments: Sequence[str] | None = None) -> int:
    """Emit a semantic record or an installed-runtime probe without diagnostics."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit semantic JSON")
    parser.add_argument(
        "--installed-probe", action="store_true", help="include installed runtime facts"
    )
    parsed = parser.parse_args(arguments)
    try:
        payload: Mapping[str, Any]
        if parsed.installed_probe:
            payload = collect_installed_probe()
        else:
            payload = collect_conformance()
        print(canonical_json(payload))
    except ConformanceError:
        print("ERROR: conformance collection rejected", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
