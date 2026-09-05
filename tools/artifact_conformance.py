"""Checkout-independent deterministic conformance collector for Fast FSM artifacts.

The collector deliberately imports only the installed :mod:`fast_fsm` package
and the standard library.  Its semantic record is made entirely of documented,
payload-free scalar observations so it can be compared across source, pure-wheel,
and compiled-wheel executions.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib
from importlib import machinery, metadata
import json
import logging
from pathlib import Path
import platform
import sys
from typing import Any, Callable, Mapping, Sequence

from fast_fsm.conditions import AsyncCondition
from fast_fsm.core import DeclarativeState, transition


SCHEMA_VERSION = 1
_PACKAGE_NAME = "fast_fsm"
_CORE_MODULE_NAME = f"{_PACKAGE_NAME}.core"
_LIFECYCLE_FIELDS = (
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
        "fields": _LIFECYCLE_FIELDS,
    },
    {
        "id": "lifecycle.precommit-failure-observation",
        "family": "lifecycle-result-history",
        "fields": _LIFECYCLE_FIELDS,
    },
    {
        "id": "builder-declarative.dispatch",
        "family": "builder-declarative",
        "fields": (
            "id",
            "family",
            "builder_success",
            "declarative_success",
            "handler_calls",
            "state",
            "builder_sealed",
            "async_detected",
            "redacted",
        ),
    },
    {
        "id": "diagnostic.exact-limit",
        "family": "diagnostic-budget",
        "fields": (
            "id",
            "family",
            "exact_complete",
            "one_less_exhausted",
            "exhausted_dimension",
            "redacted",
        ),
    },
    {
        "id": "graph.guard-rejection",
        "family": "graph-guard",
        "fields": (
            "id",
            "family",
            "success",
            "committed",
            "stage",
            "state",
            "history",
            "canonical_endpoints",
            "duplicate_state_rejected",
            "snapshot_immutable",
            "redacted",
        ),
    },
    {
        "id": "logging.metadata-redaction",
        "family": "logging-redaction",
        "fields": (
            "id",
            "family",
            "success",
            "recorded",
            "custom_redactor_called",
            "custom_redactor_safe",
            "redacted",
            "handler_restored",
        ),
    },
    {
        "id": "output.grammar-containment",
        "family": "output-containment",
        "fields": (
            "id",
            "family",
            "mermaid_safe",
            "plantuml_safe",
            "json_safe",
            "output_sha256",
            "redacted",
        ),
    },
    {
        "id": "ownership.reentry-independent-machine",
        "family": "ownership-cancellation",
        "fields": (
            "id",
            "family",
            "outer_success",
            "nested_rejected",
            "independent_success",
            "redacted",
        ),
    },
    {
        "id": "ownership.cancellation-reuse",
        "family": "ownership-cancellation",
        "fields": ("id", "family", "cancelled", "reused", "state", "redacted"),
    },
    {
        "id": "sync-async.equivalence",
        "family": "sync-async",
        "fields": (
            "id",
            "family",
            "sync_success",
            "async_success",
            "sync_committed",
            "async_committed",
            "sync_stage",
            "async_stage",
            "sync_state",
            "async_state",
            "sync_callback_order",
            "async_callback_order",
            "sync_history",
            "async_history",
            "redacted",
        ),
    },
)
REQUIRED_FAMILIES = frozenset(
    str(definition["family"]) for definition in _SCENARIO_DEFINITIONS
)
_PAYLOAD_SENTINELS = ("caller-secret", "destination-secret", "observer-secret")


class ConformanceError(RuntimeError):
    """Raised when a deterministic conformance contract is contradicted."""


def canonical_json(value: Mapping[str, Any]) -> str:
    """Serialize one evidence object with canonical, finite JSON semantics."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _sha256(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _suite_sha256(source_path: Path | None = None) -> str:
    """Bind the accepted oracle to every byte of its collector implementation.

    Individual-function introspection leaves schema validation, serialization,
    runtime probes, and the CLI emission seam unbound.  The collector is a
    deliberately single-file, standard-library-only oracle, so hashing its
    complete normalized source is both simpler and complete.  ``source_path``
    is an internal test seam for mutation coverage; production always hashes
    the installed module itself.
    """
    path = source_path or Path(__file__)
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def _lifecycle_precommit_failure_observation() -> dict[str, Any]:
    """Prove pre-commit failure, ordered observers, and empty history stay aligned."""
    core = importlib.import_module(_CORE_MODULE_NAME)
    callback_state = core.CallbackState
    callback_order: list[str] = []

    def source_exit(*_args: object, **_kwargs: object) -> None:
        callback_order.append("source-exit")
        raise RuntimeError("destination-secret")

    source = callback_state("source", on_exit=source_exit)
    destination = core.State("destination")
    machine = core.StateMachine(source, name="artifact-conformance-precommit")
    machine.add_state(destination)
    machine.add_transition("advance", source, destination)
    machine.enable_history()

    def first_observer(*_args: object, **_kwargs: object) -> None:
        callback_order.append("observer-one")

    def second_observer(*_args: object, **_kwargs: object) -> None:
        callback_order.append("observer-two")

    machine.on_failed(first_observer)
    machine.on_failed(second_observer)
    result = machine.trigger("advance", payload="caller-secret")
    return {
        "id": "lifecycle.precommit-failure-observation",
        "family": "lifecycle-result-history",
        "success": result.success,
        "committed": result.committed,
        "stage": result.stage,
        "state": machine.current_state.name,
        "callback_order": callback_order,
        "history": [
            [record.from_state, record.trigger, record.to_state]
            for record in machine.history
        ],
        "redacted": all(
            sentinel not in repr(result) for sentinel in _PAYLOAD_SENTINELS
        ),
    }


def _graph_guard_rejection() -> dict[str, Any]:
    """Exercise a real guard failure without exposing its supplied context."""
    core = importlib.import_module(_CORE_MODULE_NAME)
    conditions = importlib.import_module(f"{_PACKAGE_NAME}.conditions")
    source = core.State("guard-source")
    destination = core.State("guard-destination")
    machine = core.StateMachine(source, name="artifact-conformance-guard")
    machine.add_state(destination)
    machine.add_transition(
        "advance",
        source,
        destination,
        conditions.FuncCondition(lambda *_args, **_kwargs: False, "false-guard"),
    )
    machine.enable_history()
    snapshot = machine._graph_snapshot()
    canonical_endpoints = bool(snapshot.transitions) and (
        snapshot.transitions[0].from_state is source
        and snapshot.transitions[0].to_state is destination
    )
    duplicate_state_rejected = False
    try:
        machine.add_state(core.State("guard-source"))
    except ValueError:
        duplicate_state_rejected = True
    snapshot_immutable = False
    try:
        snapshot.states += (core.State("forbidden"),)
    except (AttributeError, TypeError):
        snapshot_immutable = True
    result = machine.trigger("advance", payload="caller-secret")
    return {
        "id": "graph.guard-rejection",
        "family": "graph-guard",
        "success": result.success,
        "committed": result.committed,
        "stage": result.stage,
        "state": machine.current_state.name,
        "history": [],
        "canonical_endpoints": canonical_endpoints,
        "duplicate_state_rejected": duplicate_state_rejected,
        "snapshot_immutable": snapshot_immutable,
        "redacted": "caller-secret" not in repr(result),
    }


def _sync_async_equivalence() -> dict[str, Any]:
    """Drive equivalent sync and async transitions through real FSM classes."""
    core = importlib.import_module(_CORE_MODULE_NAME)

    class AlwaysAsync(AsyncCondition):
        def __init__(self) -> None:
            super().__init__("always-async", "artifact collector guard")

        async def check_async(self, **_kwargs: object) -> bool:
            return True

    sync_source = core.State("source")
    sync_destination = core.State("destination")
    sync_machine = core.StateMachine(sync_source, name="artifact-conformance-sync")
    sync_machine.add_state(sync_destination)
    sync_machine.add_transition("advance", sync_source, sync_destination)
    sync_callbacks: list[str] = []
    sync_machine.on_exit(
        "source", lambda *_args, **_kwargs: sync_callbacks.append("exit")
    )
    sync_machine.on_enter(
        "destination", lambda *_args, **_kwargs: sync_callbacks.append("enter")
    )
    sync_machine.enable_history()
    sync_result = sync_machine.trigger("advance", payload="caller-secret")

    async def collect_async() -> tuple[
        bool, bool, str, str, list[str], list[list[str]]
    ]:
        async_source = core.State("source")
        async_destination = core.State("destination")
        async_machine = core.AsyncStateMachine(
            async_source, name="artifact-conformance-async"
        )
        async_machine.add_state(async_destination)
        async_machine.add_transition(
            "advance", async_source, async_destination, AlwaysAsync()
        )
        async_callbacks: list[str] = []

        async def on_exit(*_args: object, **_kwargs: object) -> None:
            async_callbacks.append("exit")

        async def on_enter(*_args: object, **_kwargs: object) -> None:
            async_callbacks.append("enter")

        async_machine.on_exit_async("source", on_exit)
        async_machine.on_enter_async("destination", on_enter)
        async_machine.enable_history()
        async_result = await async_machine.trigger_async(
            "advance", payload="caller-secret"
        )
        return (
            async_result.success,
            async_result.committed,
            async_result.stage,
            async_machine.current_state.name,
            async_callbacks,
            [
                [record.from_state, record.trigger, record.to_state]
                for record in async_machine.history
            ],
        )

    (
        async_success,
        async_committed,
        async_stage,
        async_state,
        async_callbacks,
        async_history,
    ) = asyncio.run(collect_async())
    return {
        "id": "sync-async.equivalence",
        "family": "sync-async",
        "sync_success": sync_result.success,
        "async_success": async_success,
        "sync_committed": sync_result.committed,
        "async_committed": async_committed,
        "sync_stage": sync_result.stage,
        "async_stage": async_stage,
        "sync_state": sync_machine.current_state.name,
        "async_state": async_state,
        "sync_callback_order": sync_callbacks,
        "async_callback_order": async_callbacks,
        "sync_history": [
            [record.from_state, record.trigger, record.to_state]
            for record in sync_machine.history
        ],
        "async_history": async_history,
        "redacted": True,
    }


def _builder_declarative_dispatch() -> dict[str, Any]:
    """Exercise builder and decorator dispatch without test-module helpers."""
    core = importlib.import_module(_CORE_MODULE_NAME)

    class DeclarativeCollectorState(DeclarativeState):
        __slots__ = ("calls",)

        def __init__(self) -> None:
            self.calls = 0
            super().__init__("source")

        @transition("advance", from_state="source", to_state="target")
        def handle_advance(self, *_args: object, **_kwargs: object) -> None:
            self.calls += 1

    builder = core.FSMBuilder(core.State("source"), name="artifact-conformance-builder")
    builder.add_state(core.State("target"))
    builder.add_transition("advance", "source", "target")
    builder_machine = builder.build()
    builder_result = builder_machine.trigger("advance", payload="caller-secret")
    builder_sealed = False
    try:
        builder.add_state(core.State("late"))
    except RuntimeError:
        builder_sealed = True

    class NestedAsync(AsyncCondition):
        def __init__(self) -> None:
            super().__init__("nested-async", "artifact collector async guard")

        async def check_async(self, **_kwargs: object) -> bool:
            return True

    async_builder = core.FSMBuilder(core.State("async-source"))
    async_builder.add_state(core.State("async-target"))
    async_builder.add_transition(
        "advance", "async-source", "async-target", NestedAsync()
    )
    async_detected = isinstance(async_builder.build(), core.AsyncStateMachine)

    declarative_source = DeclarativeCollectorState()
    declarative_target = core.State("target")
    declarative_machine = core.StateMachine(
        declarative_source, name="artifact-conformance-declarative"
    )
    declarative_machine.add_state(declarative_target)
    declarative_machine.add_transition(
        "advance", declarative_source, declarative_target
    )
    declarative_result = declarative_machine.trigger("advance", payload="caller-secret")
    return {
        "id": "builder-declarative.dispatch",
        "family": "builder-declarative",
        "builder_success": builder_result.success,
        "declarative_success": declarative_result.success,
        "handler_calls": declarative_source.calls,
        "state": declarative_machine.current_state.name,
        "builder_sealed": builder_sealed,
        "async_detected": async_detected,
        "redacted": True,
    }


def _ownership_cancellation_reuse() -> dict[str, Any]:
    """Cancel one owned async dispatch and prove the machine can be reused."""
    core = importlib.import_module(_CORE_MODULE_NAME)

    class CancellationGate(AsyncCondition):
        def __init__(self) -> None:
            super().__init__("cancellation-gate", "artifact collector gate")
            self.started = asyncio.Event()
            self.calls = 0

        async def check_async(self, **_kwargs: object) -> bool:
            self.calls += 1
            if self.calls == 1:
                self.started.set()
                await asyncio.Event().wait()
            return True

    async def collect_async() -> tuple[bool, bool, str]:
        source = core.State("source")
        destination = core.State("destination")
        gate = CancellationGate()
        machine = core.AsyncStateMachine(
            source, name="artifact-conformance-cancellation"
        )
        machine.add_state(destination)
        machine.add_transition("advance", source, destination, gate)
        task = asyncio.create_task(
            machine.trigger_async("advance", payload="caller-secret")
        )
        await gate.started.wait()
        task.cancel()
        cancelled = False
        try:
            await task
        except asyncio.CancelledError:
            cancelled = True
        result = await machine.trigger_async("advance", payload="caller-secret")
        return cancelled, result.success, machine.current_state.name

    cancelled, reused, state = asyncio.run(collect_async())
    return {
        "id": "ownership.cancellation-reuse",
        "family": "ownership-cancellation",
        "cancelled": cancelled,
        "reused": reused,
        "state": state,
        "redacted": True,
    }


def _ownership_reentry_independent_machine() -> dict[str, Any]:
    """Reject direct reentry without blocking an unrelated machine's progress."""
    core = importlib.import_module(_CORE_MODULE_NAME)
    callback_state = core.CallbackState
    independent = core.StateMachine(core.State("source"), name="artifact-independent")
    independent.add_state(core.State("destination"))
    independent.add_transition("advance", "source", "destination")
    independent_results: list[Any] = []
    nested_rejected = False
    machine: Any

    def source_exit(*_args: object, **_kwargs: object) -> None:
        nonlocal nested_rejected
        try:
            machine.trigger("nested", payload="caller-secret")
        except RuntimeError:
            nested_rejected = True
        independent_results.append(
            independent.trigger("advance", payload="caller-secret")
        )

    source = callback_state("source", on_exit=source_exit)
    destination = core.State("destination")
    alternate = core.State("alternate")
    machine = core.StateMachine(source, name="artifact-conformance-reentry")
    machine.add_state(destination)
    machine.add_state(alternate)
    machine.add_transition("outer", source, destination)
    machine.add_transition("nested", source, alternate)
    outer = machine.trigger("outer", payload="caller-secret")

    independent_result = independent_results[0] if independent_results else None
    return {
        "id": "ownership.reentry-independent-machine",
        "family": "ownership-cancellation",
        "outer_success": outer.success,
        "nested_rejected": nested_rejected,
        "independent_success": bool(
            independent_result is not None and independent_result.success
        ),
        "redacted": all(
            sentinel not in repr(value)
            for value in (outer, independent_result)
            for sentinel in _PAYLOAD_SENTINELS
        ),
    }


def _diagnostic_exact_limit() -> dict[str, Any]:
    """Check the exact diagnostics limit and the deterministic one-less failure."""
    public = importlib.import_module(_PACKAGE_NAME)
    core = importlib.import_module(_CORE_MODULE_NAME)
    source = core.State("source")
    destination = core.State("destination")
    machine = core.StateMachine(source, name="artifact-conformance-diagnostic")
    machine.add_state(destination)
    machine.add_transition("advance", source, destination)
    exact = public.to_json(
        machine,
        include_adjacency=True,
        limits=public.DiagnosticLimits(max_dense_cells=4),
    )
    exhausted_dimension = ""
    try:
        public.to_json(
            machine,
            include_adjacency=True,
            limits=public.DiagnosticLimits(max_dense_cells=3),
        )
    except public.DiagnosticBudgetExceeded as error:
        exhausted_dimension = error.status.exhausted_dimension or ""
    return {
        "id": "diagnostic.exact-limit",
        "family": "diagnostic-budget",
        "exact_complete": bool(exact["analysis"]["diagnostic_status"]["complete"]),
        "one_less_exhausted": bool(exhausted_dimension),
        "exhausted_dimension": exhausted_dimension,
        "redacted": True,
    }


def _output_grammar_containment() -> dict[str, Any]:
    """Use hostile syntax inputs while recording only structural output facts."""
    public = importlib.import_module(_PACKAGE_NAME)
    core = importlib.import_module(_CORE_MODULE_NAME)
    source = core.State("source")
    destination = core.State("target")
    machine = core.StateMachine(source, name="artifact-conformance-output")
    machine.add_state(destination)
    machine.add_transition("advance", source, destination)
    hostile_title = "!include caller-secret"
    mermaid = public.to_mermaid(machine, title=hostile_title)
    plantuml = public.to_plantuml(machine, title=hostile_title)
    structured = public.to_json(machine)
    rendered = mermaid + plantuml + canonical_json(structured)
    return {
        "id": "output.grammar-containment",
        "family": "output-containment",
        "mermaid_safe": mermaid.count("stateDiagram-v2") == 1 and "\x00" not in mermaid,
        "plantuml_safe": plantuml.startswith("@startuml")
        and plantuml.endswith("@enduml"),
        "json_safe": isinstance(structured, dict)
        and "\x00" not in canonical_json(structured),
        "output_sha256": hashlib.sha256(rendered.encode("utf-8")).hexdigest(),
        "redacted": "caller-secret"
        not in canonical_json(
            {"output_sha256": hashlib.sha256(rendered.encode("utf-8")).hexdigest()}
        ),
    }


def _logging_metadata_redaction() -> dict[str, Any]:
    """Collect one real trace record and prove no caller payload enters its text."""
    core = importlib.import_module(_CORE_MODULE_NAME)

    class CaptureHandler(logging.Handler):
        def __init__(self) -> None:
            super().__init__()
            self.records: list[logging.LogRecord] = []

        def emit(self, record: logging.LogRecord) -> None:
            self.records.append(record)

    logger_name = "fast_fsm.artifact-conformance.logging"
    logger = logging.getLogger(logger_name)
    prior_handlers = list(logger.handlers)
    prior_level = logger.level
    prior_propagate = logger.propagate
    handler = CaptureHandler()
    logger.handlers = [handler]
    logger.setLevel(logging.DEBUG - 5)
    logger.propagate = False
    custom_redactor_called = False
    custom_redactor_safe = False
    custom_handle: Any | None = None
    try:
        source = core.State("source")
        destination = core.State("destination")
        machine = core.StateMachine(
            source, name="artifact-conformance-logging", logger_name=logger_name
        )
        machine.add_state(destination)
        machine.add_transition("advance", source, destination)
        result = machine.trigger("advance", payload="caller-secret")
        records = [record.getMessage() for record in handler.records]
        redacted = all("caller-secret" not in message for message in records)

        custom_logger_name = f"{logger_name}.custom"

        def redactor(_event: object) -> dict[str, str]:
            nonlocal custom_redactor_called, custom_redactor_safe
            custom_redactor_called = True
            custom_redactor_safe = True
            return {"operation": "trusted-redaction", "detail": "allowed"}

        custom_handle = core.configure_fsm_logging(
            logging.DEBUG - 5,
            custom_logger_name,
            propagate=False,
            redactor=redactor,
        )
        custom_machine = core.StateMachine(
            core.State("source"),
            name="artifact-conformance-custom-redactor",
            logger_name=custom_logger_name,
        )
        custom_machine.add_state(core.State("destination"))
        custom_machine.add_transition("advance", "source", "destination")
        custom_machine.trigger("advance", payload="caller-secret")
    finally:
        if custom_handle is not None:
            custom_handle.restore()
        logger.handlers = prior_handlers
        logger.setLevel(prior_level)
        logger.propagate = prior_propagate
    return {
        "id": "logging.metadata-redaction",
        "family": "logging-redaction",
        "success": result.success,
        "recorded": bool(records),
        "custom_redactor_called": custom_redactor_called,
        "custom_redactor_safe": custom_redactor_safe,
        "redacted": redacted,
        "handler_restored": logger.handlers == prior_handlers,
    }


def _scenario_collectors() -> tuple[Callable[[], dict[str, Any]], ...]:
    """Return ordered standalone scenario adapters; later families extend this seam."""
    return (
        _lifecycle_destination_enter_failure,
        _lifecycle_precommit_failure_observation,
        _builder_declarative_dispatch,
        _diagnostic_exact_limit,
        _graph_guard_rejection,
        _logging_metadata_redaction,
        _output_grammar_containment,
        _ownership_cancellation_reuse,
        _ownership_reentry_independent_machine,
        _sync_async_equivalence,
    )


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
        if "callback_order" in record and (
            not isinstance(record["callback_order"], list)
            or not all(isinstance(value, str) for value in record["callback_order"])
        ):
            raise ConformanceError(
                f"Conformance scenario {identifier} has invalid callback order."
            )
        if "history" in record and (
            not isinstance(record["history"], list)
            or not all(
                isinstance(value, list)
                and len(value) == 3
                and all(isinstance(part, str) for part in value)
                for value in record["history"]
            )
        ):
            raise ConformanceError(
                f"Conformance scenario {identifier} has invalid history."
            )
        if "success" in record and not isinstance(record["success"], bool):
            raise ConformanceError(
                f"Conformance scenario {identifier} has invalid success outcome."
            )
        if "committed" in record and not isinstance(record["committed"], bool):
            raise ConformanceError(
                f"Conformance scenario {identifier} has invalid commit outcome."
            )
        if "stage" in record and not isinstance(record["stage"], str):
            raise ConformanceError(
                f"Conformance scenario {identifier} has invalid scalar outcome."
            )
        if "state" in record and not isinstance(record["state"], str):
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
    direct_url_path = Path(str(distribution.locate_file("direct_url.json")))
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


def collect_installed_probe(*, artifact_sha256: str) -> dict[str, Any]:
    """Return one JSON child probe with semantic records plus runtime evidence."""
    if len(artifact_sha256) != 64 or any(
        character not in "0123456789abcdef" for character in artifact_sha256
    ):
        raise ConformanceError("Installed artifact identity is invalid.")
    return {
        "artifact_sha256": artifact_sha256,
        "conformance": collect_conformance(),
        "runtime": _runtime_facts(),
    }


def main(arguments: Sequence[str] | None = None) -> int:
    """Emit a semantic record or an installed-runtime probe without diagnostics."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit semantic JSON")
    parser.add_argument(
        "--installed-probe", action="store_true", help="include installed runtime facts"
    )
    parser.add_argument(
        "--artifact-sha256",
        help="parent-computed exact artifact identity for the installed probe",
    )
    parsed = parser.parse_args(arguments)
    try:
        payload: Mapping[str, Any]
        if parsed.installed_probe:
            if not parsed.artifact_sha256:
                raise ConformanceError("Installed artifact identity is required.")
            payload = collect_installed_probe(artifact_sha256=parsed.artifact_sha256)
        else:
            payload = collect_conformance()
        print(canonical_json(payload))
    except ConformanceError:
        print("ERROR: conformance collection rejected", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
