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
import threading
from typing import Any, Callable, Mapping, Sequence

from fast_fsm.conditions import AsyncCondition, NegatedCondition
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
    *(
        {
            "id": f"diagnostic.{dimension}-boundary",
            "family": "diagnostic-budget",
            "fields": (
                "id",
                "family",
                "exact_complete",
                "exact_limit",
                "exact_count",
                "one_less_limit",
                "one_less_exhausted",
                "exhausted_dimension",
                "error_redacted",
                "redacted",
            ),
            "required_values": {
                "exact_complete": True,
                "one_less_exhausted": True,
                "exhausted_dimension": f"max_{dimension}",
                "error_redacted": True,
                "redacted": True,
            },
        }
        for dimension in ("work", "results", "dense_cells", "path_expansions")
    ),
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
            "snapshot_facts_exact",
            "guard_context_observed",
            "rejected_topology_unchanged",
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
            "custom_failure_safe",
            "redacted",
            "handler_restored",
        ),
    },
    {
        "id": "priority.sync.winner",
        "family": "priority-selection",
        "fields": (
            "id",
            "family",
            "success",
            "committed",
            "state",
            "target",
            "guard_order",
            "result_priority",
            "history_priority",
            "history_count",
            "lower_candidate_suppressed",
            "redacted",
        ),
        "required_values": {
            "success": True,
            "committed": True,
            "state": "winner",
            "target": "winner",
            "guard_order": ["rejected", "winner"],
            "result_priority": 3,
            "history_priority": 3,
            "history_count": 1,
            "lower_candidate_suppressed": True,
            "redacted": True,
        },
    },
    {
        "id": "priority.sync.exhaustion",
        "family": "priority-selection",
        "fields": (
            "id",
            "family",
            "success",
            "committed",
            "stage",
            "state",
            "guard_order",
            "result_priority",
            "history_count",
            "observer_count",
            "all_candidates_evaluated",
            "redacted",
        ),
        "required_values": {
            "success": False,
            "committed": False,
            "stage": "selection",
            "state": "source",
            "guard_order": ["first", "second"],
            "result_priority": None,
            "history_count": 0,
            "observer_count": 1,
            "all_candidates_evaluated": True,
            "redacted": True,
        },
    },
    {
        "id": "priority.sync.guard_exception",
        "family": "priority-selection",
        "fields": (
            "id",
            "family",
            "success",
            "committed",
            "stage",
            "state",
            "guard_order",
            "active_priority",
            "history_count",
            "lower_candidate_suppressed",
            "observer_count",
            "redacted",
        ),
        "required_values": {
            "success": False,
            "committed": False,
            "stage": "guard",
            "state": "source",
            "guard_order": ["raising"],
            "active_priority": -3,
            "history_count": 0,
            "lower_candidate_suppressed": True,
            "observer_count": 1,
            "redacted": True,
        },
    },
    {
        "id": "priority.async.winner",
        "family": "priority-selection",
        "fields": (
            "id",
            "family",
            "success",
            "committed",
            "state",
            "target",
            "guard_order",
            "result_priority",
            "history_priority",
            "history_count",
            "lower_candidate_suppressed",
            "redacted",
        ),
        "required_values": {
            "success": True,
            "committed": True,
            "state": "winner",
            "target": "winner",
            "guard_order": ["rejected", "winner"],
            "result_priority": 3,
            "history_priority": 3,
            "history_count": 1,
            "lower_candidate_suppressed": True,
            "redacted": True,
        },
    },
    {
        "id": "priority.async.guard_exception",
        "family": "priority-selection",
        "fields": (
            "id",
            "family",
            "success",
            "committed",
            "stage",
            "state",
            "guard_order",
            "active_priority",
            "history_count",
            "lower_candidate_suppressed",
            "observer_count",
            "redacted",
        ),
        "required_values": {
            "success": False,
            "committed": False,
            "stage": "guard",
            "state": "source",
            "guard_order": ["raising"],
            "active_priority": -3,
            "history_count": 0,
            "lower_candidate_suppressed": True,
            "observer_count": 1,
            "redacted": True,
        },
    },
    {
        "id": "priority.async.cancellation",
        "family": "priority-selection",
        "fields": (
            "id",
            "family",
            "cancelled",
            "stage",
            "active_priority",
            "state",
            "guard_order",
            "history_count",
            "lower_candidate_suppressed",
            "observer_count",
            "post_cancellation_reuse",
            "redacted",
        ),
        "required_values": {
            "cancelled": True,
            "stage": "guard",
            "active_priority": -3,
            "state": "source",
            "guard_order": ["blocked"],
            "history_count": 0,
            "lower_candidate_suppressed": True,
            "observer_count": 1,
            "post_cancellation_reuse": True,
            "redacted": True,
        },
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
        "id": "ownership.sync-thread-serialization",
        "family": "ownership-cancellation",
        "fields": (
            "id",
            "family",
            "first_success",
            "second_success",
            "second_blocked_while_owned",
            "redacted",
        ),
        "required_values": {
            "first_success": True,
            "second_success": True,
            "second_blocked_while_owned": True,
            "redacted": True,
        },
    },
    {
        "id": "ownership.async-task-serialization",
        "family": "ownership-cancellation",
        "fields": (
            "id",
            "family",
            "owner_success",
            "waiter_success",
            "waiter_blocked_while_owned",
            "heartbeat_ran",
            "redacted",
        ),
        "required_values": {
            "owner_success": True,
            "waiter_success": True,
            "waiter_blocked_while_owned": True,
            "heartbeat_ran": True,
            "redacted": True,
        },
    },
    {
        "id": "ownership.cross-loop-rejection",
        "family": "ownership-cancellation",
        "fields": (
            "id",
            "family",
            "foreign_loop_rejected",
            "bound_loop_preserved",
            "foreign_guard_not_evaluated",
            "redacted",
        ),
        "required_values": {
            "foreign_loop_rejected": True,
            "bound_loop_preserved": True,
            "foreign_guard_not_evaluated": True,
            "redacted": True,
        },
    },
    {
        "id": "ownership.mutator-baseexception-release",
        "family": "ownership-cancellation",
        "fields": (
            "id",
            "family",
            "mutator_rejected_while_owned",
            "topology_unchanged",
            "baseexception_propagated",
            "mutator_admitted_after_release",
            "redacted",
        ),
        "required_values": {
            "mutator_rejected_while_owned": True,
            "topology_unchanged": True,
            "baseexception_propagated": True,
            "mutator_admitted_after_release": True,
            "redacted": True,
        },
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
    source = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(source).hexdigest()


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
    guard_context_observed = False

    def denied_guard(*args: object, **kwargs: object) -> bool:
        nonlocal guard_context_observed
        guard_context_observed = args == ("guard-position",) and kwargs == {
            "token": "caller-secret"
        }
        return False

    machine.add_transition(
        "advance",
        source,
        destination,
        conditions.FuncCondition(denied_guard, "false-guard"),
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
    before_rejection_version = snapshot.graph_version
    rejected_topology_unchanged = False
    try:
        machine.add_transition("invalid", "missing", destination)
    except (KeyError, ValueError):
        rejected_topology_unchanged = (
            machine._graph_snapshot().graph_version == before_rejection_version
        )
    result = machine.trigger("advance", "guard-position", token="caller-secret")
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
        "snapshot_facts_exact": (
            snapshot.initial_state is source
            and snapshot.initial_state_name == "guard-source"
            and snapshot.current_state_name == "guard-source"
            and snapshot.state_names == ("guard-destination", "guard-source")
            and snapshot.graph_version == 2
        ),
        "guard_context_observed": guard_context_observed,
        "rejected_topology_unchanged": rejected_topology_unchanged,
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
        "advance",
        "async-source",
        "async-target",
        unless=NegatedCondition(NestedAsync()),
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


def _ownership_sync_thread_serialization() -> dict[str, Any]:
    """Prove one machine serializes independent writers without a global lock."""
    core = importlib.import_module(_CORE_MODULE_NAME)
    first_entered = threading.Event()
    contender_attempted = threading.Event()
    second_finished = threading.Event()
    release_first = threading.Event()
    outcomes: dict[str, bool] = {}
    thread_errors: list[BaseException] = []
    second_blocked_while_owned = False

    class BlockingListener:
        def before_transition(
            self,
            _from_state: object,
            _to_state: object,
            trigger: str,
            **_kwargs: object,
        ) -> None:
            nonlocal second_blocked_while_owned
            if trigger != "first":
                return
            first_entered.set()
            if not contender_attempted.wait(timeout=5):
                raise RuntimeError("artifact conformance contender did not start")
            second_blocked_while_owned = not second_finished.wait(timeout=0.05)
            if not release_first.wait(timeout=5):
                raise RuntimeError("artifact conformance owner was not released")

    source = core.State("source")
    destination = core.State("destination")
    machine = core.StateMachine(source, name="artifact-conformance-thread-owner")
    machine.add_state(destination)
    machine.add_transition("first", source, destination)
    machine.add_transition("second", destination, source)
    machine.add_listener(BlockingListener())

    def run_first() -> None:
        try:
            outcomes["first"] = machine.trigger("first").success
        except BaseException as error:  # pragma: no cover - returned as a record fact
            thread_errors.append(error)

    def run_second() -> None:
        try:
            if not first_entered.wait(timeout=5):
                raise RuntimeError("artifact conformance owner did not enter")
            contender_attempted.set()
            outcomes["second"] = machine.trigger("second").success
            second_finished.set()
        except BaseException as error:  # pragma: no cover - returned as a record fact
            thread_errors.append(error)

    first = threading.Thread(target=run_first)
    second = threading.Thread(target=run_second)
    first.start()
    first_entered.wait(timeout=5)
    second.start()
    try:
        contender_attempted.wait(timeout=5)
    finally:
        release_first.set()
        first.join(timeout=5)
        second.join(timeout=5)

    return {
        "id": "ownership.sync-thread-serialization",
        "family": "ownership-cancellation",
        "first_success": (
            outcomes.get("first") is True and not first.is_alive() and not thread_errors
        ),
        "second_success": (
            outcomes.get("second") is True
            and not second.is_alive()
            and not thread_errors
        ),
        "second_blocked_while_owned": second_blocked_while_owned,
        "redacted": True,
    }


def _ownership_async_task_serialization() -> dict[str, Any]:
    """Prove same-loop task contention yields instead of bypassing ownership."""
    core = importlib.import_module(_CORE_MODULE_NAME)

    async def collect_async() -> tuple[bool, bool, bool, bool]:
        owner_entered = asyncio.Event()
        release_owner = asyncio.Event()
        waiter_attempted = asyncio.Event()
        heartbeat_ran = asyncio.Event()
        source = core.State("source")
        destination = core.State("destination")
        machine = core.AsyncStateMachine(
            source, name="artifact-conformance-async-owner"
        )
        machine.add_state(destination)
        machine.add_transition("advance", source, destination)
        machine.add_transition("return", destination, source)

        async def hold_owner(*_args: object, **_kwargs: object) -> None:
            owner_entered.set()
            await asyncio.wait_for(release_owner.wait(), timeout=5)

        machine.on_exit_async("source", hold_owner)
        owner = asyncio.create_task(machine.trigger_async("advance"))
        waiter: asyncio.Task[Any] | None = None
        heartbeat: asyncio.Task[Any] | None = None
        try:
            await asyncio.wait_for(owner_entered.wait(), timeout=5)

            async def contend() -> object:
                waiter_attempted.set()
                return await machine.trigger_async("return")

            waiter = asyncio.create_task(contend())
            await asyncio.wait_for(waiter_attempted.wait(), timeout=5)

            async def beat() -> None:
                heartbeat_ran.set()

            heartbeat = asyncio.create_task(beat())
            await asyncio.wait_for(heartbeat_ran.wait(), timeout=5)
            await asyncio.wait_for(heartbeat, timeout=5)
            waiter_blocked = not waiter.done()
            release_owner.set()
            owner_result = await asyncio.wait_for(owner, timeout=5)
            waiter_result = await asyncio.wait_for(waiter, timeout=5)
            return (
                bool(owner_result.success),
                bool(waiter_result.success),
                waiter_blocked,
                heartbeat_ran.is_set(),
            )
        finally:
            release_owner.set()
            active = tuple(
                task for task in (owner, waiter, heartbeat) if task is not None
            )
            for task in active:
                if not task.done():
                    task.cancel()
            if active:
                await asyncio.gather(*active, return_exceptions=True)

    owner_success, waiter_success, waiter_blocked, heartbeat_ran = asyncio.run(
        collect_async()
    )
    return {
        "id": "ownership.async-task-serialization",
        "family": "ownership-cancellation",
        "owner_success": owner_success,
        "waiter_success": waiter_success,
        "waiter_blocked_while_owned": waiter_blocked,
        "heartbeat_ran": heartbeat_ran,
        "redacted": True,
    }


def _ownership_cross_loop_rejection() -> dict[str, Any]:
    """Bind once and reject a foreign event loop before it evaluates a guard."""
    core = importlib.import_module(_CORE_MODULE_NAME)

    async def collect_async() -> tuple[bool, bool, bool]:
        guard_calls: list[str] = []
        source = core.State("source")
        destination = core.State("destination")
        machine = core.AsyncStateMachine(source, name="artifact-conformance-loop")
        machine.add_state(destination)
        machine.add_transition(
            "advance",
            source,
            destination,
            lambda *_args, **_kwargs: guard_calls.append("guard") or True,
        )
        initial_ready = await machine.can_trigger_async("advance")
        original_loop = asyncio.get_running_loop()
        foreign_errors: list[BaseException] = []

        def use_foreign_loop() -> None:
            async def attempt() -> None:
                try:
                    await machine.can_trigger_async("advance")
                except RuntimeError as error:
                    foreign_errors.append(error)

            asyncio.run(attempt())

        foreign = threading.Thread(target=use_foreign_loop)
        foreign.start()
        foreign.join(timeout=5)
        rejected = (
            not foreign.is_alive()
            and len(foreign_errors) == 1
            and "foreign async loop" in str(foreign_errors[0])
        )
        return (
            bool(initial_ready) and rejected,
            machine._bound_loop is original_loop,
            guard_calls == ["guard"],
        )

    foreign_rejected, loop_preserved, guard_untouched = asyncio.run(collect_async())
    return {
        "id": "ownership.cross-loop-rejection",
        "family": "ownership-cancellation",
        "foreign_loop_rejected": foreign_rejected,
        "bound_loop_preserved": loop_preserved,
        "foreign_guard_not_evaluated": guard_untouched,
        "redacted": True,
    }


def _ownership_mutator_baseexception_release() -> dict[str, Any]:
    """Reject a mutator while owned, then admit it after BaseException cleanup."""
    core = importlib.import_module(_CORE_MODULE_NAME)
    mutator_rejected = False
    machine: Any
    alternate = core.State("alternate")

    def reject_mutator(*_args: object, **_kwargs: object) -> None:
        nonlocal mutator_rejected
        try:
            machine.add_state(alternate)
        except RuntimeError:
            mutator_rejected = True

    source = core.CallbackState("source", on_exit=reject_mutator)
    destination = core.State("destination")
    machine = core.StateMachine(source, name="artifact-conformance-mutator-owner")
    machine.add_state(destination)
    machine.add_transition("advance", source, destination)
    version_before = machine._graph_version
    machine.trigger("advance")
    topology_unchanged = (
        "alternate" not in machine._states and machine._graph_version == version_before
    )

    raise_once = True

    def raise_baseexception(*_args: object, **_kwargs: object) -> None:
        nonlocal raise_once
        if raise_once:
            raise_once = False
            raise KeyboardInterrupt("caller-secret")

    recovery_source = core.CallbackState("source", on_exit=raise_baseexception)
    recovery_destination = core.State("destination")
    recovery = core.StateMachine(
        recovery_source, name="artifact-conformance-baseexception"
    )
    recovery.add_state(recovery_destination)
    recovery.add_transition("advance", recovery_source, recovery_destination)
    baseexception_propagated = False
    try:
        recovery.trigger("advance", payload="caller-secret")
    except KeyboardInterrupt:
        baseexception_propagated = True
    post_release = core.State("post-release")
    try:
        recovery.add_state(post_release)
        mutator_admitted = "post-release" in recovery._states
    except BaseException:  # pragma: no cover - returned as a record fact
        mutator_admitted = False

    return {
        "id": "ownership.mutator-baseexception-release",
        "family": "ownership-cancellation",
        "mutator_rejected_while_owned": mutator_rejected,
        "topology_unchanged": topology_unchanged,
        "baseexception_propagated": baseexception_propagated,
        "mutator_admitted_after_release": mutator_admitted,
        "redacted": True,
    }


def _diagnostic_boundary(dimension: str) -> dict[str, Any]:
    """Prove exact and one-less limits for one public diagnostic dimension."""
    public = importlib.import_module(_PACKAGE_NAME)
    core = importlib.import_module(_CORE_MODULE_NAME)

    def make_machine() -> Any:
        source = core.State("source")
        destination = core.State("destination")
        machine = core.StateMachine(source, name="artifact-conformance-diagnostic")
        machine.add_state(destination)
        machine.add_transition("advance", source, destination)
        return machine

    count_field = {
        "work": "work_count",
        "results": "result_count",
        "dense_cells": "dense_cell_count",
        "path_expansions": "path_expansion_count",
    }[dimension]

    def limits(limit: int) -> Any:
        kwargs = {
            "max_work": 100_000,
            "max_results": 100_000,
            "max_dense_cells": 100_000,
            "max_path_expansions": 100_000,
        }
        kwargs[f"max_{dimension}"] = limit
        return public.DiagnosticLimits(**kwargs)

    def action(limit: int) -> tuple[bool, int]:
        machine = make_machine()
        if dimension == "dense_cells":
            payload = public.to_json(
                machine, include_adjacency=True, limits=limits(limit)
            )
            status = payload["analysis"]["diagnostic_status"]
            return bool(status["complete"]), int(status[count_field])
        validator = public.FSMValidator(machine, limits=limits(limit))
        if dimension == "work":
            validator.get_reachable_states()
        else:
            validator.generate_test_paths(max_length=1, max_paths=1)
        status = validator.diagnostic_status
        return bool(status.complete), int(getattr(status, count_field))

    _complete, exact_limit = action(100_000)
    exact_complete, exact_count = action(exact_limit)
    exhausted_dimension = ""
    error_redacted = False
    try:
        action(exact_limit - 1)
    except public.DiagnosticBudgetExceeded as error:
        exhausted_dimension = error.status.exhausted_dimension or ""
        error_redacted = all(
            sentinel not in str(error) for sentinel in _PAYLOAD_SENTINELS
        )
    return {
        "id": f"diagnostic.{dimension}-boundary",
        "family": "diagnostic-budget",
        "exact_complete": exact_complete,
        "exact_limit": exact_limit,
        "exact_count": exact_count,
        "one_less_limit": exact_limit - 1,
        "one_less_exhausted": bool(exhausted_dimension),
        "exhausted_dimension": exhausted_dimension,
        "error_redacted": error_redacted,
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
    # The title is adversarial grammar, but not a caller payload.  Payload
    # sentinels stay separate so the record proves both grammar containment and
    # trace redaction instead of requiring a user-visible title to be secret.
    hostile_title = "!include hostile-grammar"
    mermaid = public.to_mermaid(machine, title=hostile_title)
    plantuml = public.to_plantuml(machine, title=hostile_title)
    structured = public.to_json(machine)
    structured_json = canonical_json(structured)
    rendered = mermaid + plantuml + structured_json
    rendered_safe = (
        all(sentinel not in rendered for sentinel in _PAYLOAD_SENTINELS)
        and "\x00" not in rendered
    )
    return {
        "id": "output.grammar-containment",
        "family": "output-containment",
        "mermaid_safe": mermaid.count("stateDiagram-v2") == 1 and rendered_safe,
        "plantuml_safe": plantuml.startswith("@startuml")
        and plantuml.endswith("@enduml")
        and rendered_safe,
        "json_safe": isinstance(structured, dict) and rendered_safe,
        "output_sha256": hashlib.sha256(rendered.encode("utf-8")).hexdigest(),
        "redacted": rendered_safe,
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
    custom_failure_safe = False
    custom_handle: Any | None = None
    failure_handle: Any | None = None
    custom_logger: logging.Logger | None = None
    failure_logger: logging.Logger | None = None
    custom_capture: CaptureHandler | None = None
    failure_capture: CaptureHandler | None = None
    custom_prior: tuple[list[logging.Handler], int, bool] | None = None
    failure_prior: tuple[list[logging.Handler], int, bool] | None = None
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
        custom_logger = logging.getLogger(custom_logger_name)
        custom_prior = (
            list(custom_logger.handlers),
            custom_logger.level,
            custom_logger.propagate,
        )
        custom_capture = CaptureHandler()
        custom_logger.addHandler(custom_capture)
        custom_logger.setLevel(logging.DEBUG - 5)

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
        custom_records = custom_capture.records
        custom_redactor_safe = (
            custom_redactor_called
            and bool(custom_records)
            and all(
                sentinel not in record.getMessage()
                for record in custom_records
                for sentinel in _PAYLOAD_SENTINELS
            )
            and any(
                getattr(record, "trace_operation", None) == "trusted-redaction"
                for record in custom_records
            )
        )

        failure_logger_name = f"{logger_name}.custom-failure"
        failure_logger = logging.getLogger(failure_logger_name)
        failure_prior = (
            list(failure_logger.handlers),
            failure_logger.level,
            failure_logger.propagate,
        )
        failure_capture = CaptureHandler()
        failure_logger.addHandler(failure_capture)
        failure_logger.setLevel(logging.DEBUG - 5)

        def failing_redactor(_event: object) -> dict[str, str]:
            raise ValueError("caller-secret")

        failure_handle = core.configure_fsm_logging(
            logging.DEBUG - 5,
            failure_logger_name,
            propagate=False,
            redactor=failing_redactor,
        )
        failure_machine = core.StateMachine(
            core.State("source"),
            name="artifact-conformance-custom-redactor-failure",
            logger_name=failure_logger_name,
        )
        failure_machine.add_state(core.State("destination"))
        failure_machine.add_transition("advance", "source", "destination")
        failure_machine.trigger("advance", payload="caller-secret")
        custom_failure_safe = (
            bool(failure_capture.records)
            and all(
                sentinel not in record.getMessage()
                for record in failure_capture.records
                for sentinel in _PAYLOAD_SENTINELS
            )
            and any(
                getattr(record, "trace_operation", None) == "redaction_failure"
                for record in failure_capture.records
            )
        )
    finally:
        if failure_handle is not None:
            failure_handle.restore()
        if custom_handle is not None:
            custom_handle.restore()
        if failure_logger is not None and failure_capture is not None:
            failure_logger.removeHandler(failure_capture)
        if failure_logger is not None and failure_prior is not None:
            failure_logger.handlers = failure_prior[0]
            failure_logger.setLevel(failure_prior[1])
            failure_logger.propagate = failure_prior[2]
        if custom_logger is not None and custom_capture is not None:
            custom_logger.removeHandler(custom_capture)
        if custom_logger is not None and custom_prior is not None:
            custom_logger.handlers = custom_prior[0]
            custom_logger.setLevel(custom_prior[1])
            custom_logger.propagate = custom_prior[2]
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
        "custom_failure_safe": custom_failure_safe,
        "redacted": redacted,
        "handler_restored": logger.handlers == prior_handlers,
    }


def _priority_sync_winner() -> dict[str, Any]:
    """Prove a lower numeric eligible priority wins without probing later guards."""
    core = importlib.import_module(_CORE_MODULE_NAME)
    guard_order: list[str] = []
    source = core.State("source")
    rejected = core.State("rejected")
    winner = core.State("winner")
    later = core.State("later")
    machine = core.StateMachine(source, name="artifact-conformance-priority-sync")
    for state in (rejected, winner, later):
        machine.add_state(state)

    def guard(label: str, outcome: bool) -> Callable[..., bool]:
        def evaluate(*_args: object, **_kwargs: object) -> bool:
            guard_order.append(label)
            return outcome

        return evaluate

    machine.add_transition("advance", source, later, guard("later", True), priority=9)
    machine.add_transition("advance", source, winner, guard("winner", True), priority=3)
    machine.add_transition(
        "advance", source, rejected, guard("rejected", False), priority=-2
    )
    machine.enable_history()
    result = machine.trigger("advance", payload="caller-secret")
    history = machine.history
    return {
        "id": "priority.sync.winner",
        "family": "priority-selection",
        "success": result.success,
        "committed": result.committed,
        "state": machine.current_state.name,
        "target": result.to_state,
        "guard_order": guard_order,
        "result_priority": result.priority,
        "history_priority": history[0].priority if history else None,
        "history_count": len(history),
        "lower_candidate_suppressed": "later" not in guard_order,
        "redacted": "caller-secret" not in repr(result),
    }


def _priority_sync_exhaustion() -> dict[str, Any]:
    """Record one observer-visible selection failure after every candidate rejects."""
    core = importlib.import_module(_CORE_MODULE_NAME)
    guard_order: list[str] = []
    observer_count = 0
    source = core.State("source")
    first = core.State("first")
    second = core.State("second")
    machine = core.StateMachine(source, name="artifact-conformance-priority-exhaustion")
    machine.add_state(first)
    machine.add_state(second)

    def rejected(label: str) -> Callable[..., bool]:
        def evaluate(*_args: object, **_kwargs: object) -> bool:
            guard_order.append(label)
            return False

        return evaluate

    machine.add_transition("advance", source, second, rejected("second"), priority=3)
    machine.add_transition("advance", source, first, rejected("first"), priority=-3)
    machine.enable_history()

    def observer(*_args: object, **_kwargs: object) -> None:
        nonlocal observer_count
        observer_count += 1

    machine.on_failed(observer)
    result = machine.trigger("advance", payload="caller-secret")
    return {
        "id": "priority.sync.exhaustion",
        "family": "priority-selection",
        "success": result.success,
        "committed": result.committed,
        "stage": result.stage,
        "state": machine.current_state.name,
        "guard_order": guard_order,
        "result_priority": result.priority,
        "history_count": len(machine.history),
        "observer_count": observer_count,
        "all_candidates_evaluated": guard_order == ["first", "second"],
        "redacted": "caller-secret" not in repr(result),
    }


def _priority_sync_guard_exception() -> dict[str, Any]:
    """Keep an active guard exception terminal at its exact priority."""
    core = importlib.import_module(_CORE_MODULE_NAME)
    guard_order: list[str] = []
    observer_count = 0
    source = core.State("source")
    failed = core.State("failed")
    later = core.State("later")
    machine = core.StateMachine(source, name="artifact-conformance-priority-error")
    machine.add_state(failed)
    machine.add_state(later)

    def raises(*_args: object, **_kwargs: object) -> bool:
        guard_order.append("raising")
        raise RuntimeError("guard-secret")

    def lower(*_args: object, **_kwargs: object) -> bool:
        guard_order.append("later")
        return True

    machine.add_transition("advance", source, later, lower, priority=4)
    machine.add_transition("advance", source, failed, raises, priority=-3)
    machine.enable_history()

    def observer(*_args: object, **_kwargs: object) -> None:
        nonlocal observer_count
        observer_count += 1

    machine.on_failed(observer)
    result = machine.trigger("advance", payload="caller-secret")
    return {
        "id": "priority.sync.guard_exception",
        "family": "priority-selection",
        "success": result.success,
        "committed": result.committed,
        "stage": result.stage,
        "state": machine.current_state.name,
        "guard_order": guard_order,
        "active_priority": result.priority,
        "history_count": len(machine.history),
        "lower_candidate_suppressed": "later" not in guard_order,
        "observer_count": observer_count,
        "redacted": all(
            sentinel not in repr(result)
            for sentinel in ("caller-secret", "guard-secret")
        ),
    }


def _priority_async_winner() -> dict[str, Any]:
    """Await ordered candidates one at a time and commit only the first winner."""
    core = importlib.import_module(_CORE_MODULE_NAME)

    class AsyncGuard(AsyncCondition):
        __slots__ = ("_guard_order", "_label", "_outcome")

        def __init__(self, guard_order: list[str], label: str, outcome: bool) -> None:
            super().__init__(label, "artifact priority guard")
            self._guard_order = guard_order
            self._label = label
            self._outcome = outcome

        async def check_async(self, **_kwargs: object) -> bool:
            self._guard_order.append(self._label)
            return self._outcome

    async def collect_async() -> dict[str, Any]:
        guard_order: list[str] = []
        source = core.State("source")
        rejected = core.State("rejected")
        winner = core.State("winner")
        later = core.State("later")
        machine = core.AsyncStateMachine(
            source, name="artifact-conformance-priority-async"
        )
        for state in (rejected, winner, later):
            machine.add_state(state)
        machine.add_transition(
            "advance", source, later, AsyncGuard(guard_order, "later", True), priority=9
        )
        machine.add_transition(
            "advance",
            source,
            winner,
            AsyncGuard(guard_order, "winner", True),
            priority=3,
        )
        machine.add_transition(
            "advance",
            source,
            rejected,
            AsyncGuard(guard_order, "rejected", False),
            priority=-2,
        )
        machine.enable_history()
        result = await machine.trigger_async("advance", payload="caller-secret")
        history = machine.history
        return {
            "id": "priority.async.winner",
            "family": "priority-selection",
            "success": result.success,
            "committed": result.committed,
            "state": machine.current_state.name,
            "target": result.to_state,
            "guard_order": guard_order,
            "result_priority": result.priority,
            "history_priority": history[0].priority if history else None,
            "history_count": len(history),
            "lower_candidate_suppressed": "later" not in guard_order,
            "redacted": "caller-secret" not in repr(result),
        }

    return asyncio.run(collect_async())


def _priority_async_guard_exception() -> dict[str, Any]:
    """Stop asynchronous selection at the raising candidate without fallback."""
    core = importlib.import_module(_CORE_MODULE_NAME)

    class AsyncGuard(AsyncCondition):
        __slots__ = ("_guard_order", "_label", "_outcome")

        def __init__(self, guard_order: list[str], label: str, outcome: object) -> None:
            super().__init__(label, "artifact priority guard")
            self._guard_order = guard_order
            self._label = label
            self._outcome = outcome

        async def check_async(self, **_kwargs: object) -> bool:
            self._guard_order.append(self._label)
            if isinstance(self._outcome, BaseException):
                raise self._outcome
            return bool(self._outcome)

    async def collect_async() -> dict[str, Any]:
        guard_order: list[str] = []
        observer_count = 0
        source = core.State("source")
        failed = core.State("failed")
        later = core.State("later")
        machine = core.AsyncStateMachine(
            source, name="artifact-conformance-priority-async-error"
        )
        machine.add_state(failed)
        machine.add_state(later)
        machine.add_transition(
            "advance", source, later, AsyncGuard(guard_order, "later", True), priority=4
        )
        machine.add_transition(
            "advance",
            source,
            failed,
            AsyncGuard(guard_order, "raising", RuntimeError("guard-secret")),
            priority=-3,
        )
        machine.enable_history()

        def observer(*_args: object, **_kwargs: object) -> None:
            nonlocal observer_count
            observer_count += 1

        machine.on_failed(observer)
        result = await machine.trigger_async("advance", payload="caller-secret")
        return {
            "id": "priority.async.guard_exception",
            "family": "priority-selection",
            "success": result.success,
            "committed": result.committed,
            "stage": result.stage,
            "state": machine.current_state.name,
            "guard_order": guard_order,
            "active_priority": result.priority,
            "history_count": len(machine.history),
            "lower_candidate_suppressed": "later" not in guard_order,
            "observer_count": observer_count,
            "redacted": all(
                sentinel not in repr(result)
                for sentinel in ("caller-secret", "guard-secret")
            ),
        }

    return asyncio.run(collect_async())


def _priority_async_cancellation() -> dict[str, Any]:
    """Re-raise one cancellation, finalize once, and release the machine for reuse."""
    core = importlib.import_module(_CORE_MODULE_NAME)

    class BlockingGuard(AsyncCondition):
        __slots__ = ("_guard_order", "started")

        def __init__(self, guard_order: list[str], started: asyncio.Event) -> None:
            super().__init__("blocked", "artifact priority cancellation guard")
            self._guard_order = guard_order
            self.started = started

        async def check_async(self, **_kwargs: object) -> bool:
            self._guard_order.append("blocked")
            self.started.set()
            await asyncio.Event().wait()
            return True

    class LaterGuard(AsyncCondition):
        __slots__ = ("_guard_order",)

        def __init__(self, guard_order: list[str]) -> None:
            super().__init__("later", "artifact priority later guard")
            self._guard_order = guard_order

        async def check_async(self, **_kwargs: object) -> bool:
            self._guard_order.append("later")
            return True

    async def collect_async() -> dict[str, Any]:
        guard_order: list[str] = []
        observer_count = 0
        started = asyncio.Event()
        source = core.State("source")
        blocked = core.State("blocked")
        later = core.State("later")
        recovered = core.State("recovered")
        machine = core.AsyncStateMachine(
            source, name="artifact-conformance-priority-cancellation"
        )
        for state in (blocked, later, recovered):
            machine.add_state(state)
        machine.add_transition(
            "advance", source, blocked, BlockingGuard(guard_order, started), priority=-3
        )
        machine.add_transition(
            "advance", source, later, LaterGuard(guard_order), priority=4
        )
        machine.add_transition("recover", source, recovered)
        machine.enable_history()

        def observer(*_args: object, **_kwargs: object) -> None:
            nonlocal observer_count
            observer_count += 1

        machine.on_failed(observer)
        pending = asyncio.create_task(
            machine.trigger_async("advance", payload="caller-secret")
        )
        await started.wait()
        pending.cancel()
        cancelled = False
        try:
            await pending
        except asyncio.CancelledError:
            cancelled = True
        state_after_cancellation = machine.current_state.name
        history_count = len(machine.history)
        reused = await machine.trigger_async("recover", payload="caller-secret")
        return {
            "id": "priority.async.cancellation",
            "family": "priority-selection",
            "cancelled": cancelled,
            "stage": "guard" if observer_count == 1 else "unexpected",
            "active_priority": -3,
            "state": state_after_cancellation,
            "guard_order": guard_order,
            "history_count": history_count,
            "lower_candidate_suppressed": guard_order == ["blocked"],
            "observer_count": observer_count,
            "post_cancellation_reuse": reused.success
            and machine.current_state.name == "recovered",
            "redacted": all(
                sentinel not in repr(value)
                for value in (reused,)
                for sentinel in _PAYLOAD_SENTINELS
            ),
        }

    return asyncio.run(collect_async())


def _scenario_collectors() -> tuple[Callable[[], dict[str, Any]], ...]:
    """Return ordered standalone scenario adapters; later families extend this seam."""
    return (
        _lifecycle_destination_enter_failure,
        _lifecycle_precommit_failure_observation,
        _builder_declarative_dispatch,
        lambda: _diagnostic_boundary("work"),
        lambda: _diagnostic_boundary("results"),
        lambda: _diagnostic_boundary("dense_cells"),
        lambda: _diagnostic_boundary("path_expansions"),
        _graph_guard_rejection,
        _logging_metadata_redaction,
        _priority_sync_winner,
        _priority_sync_exhaustion,
        _priority_sync_guard_exception,
        _priority_async_winner,
        _priority_async_guard_exception,
        _priority_async_cancellation,
        _output_grammar_containment,
        _ownership_cancellation_reuse,
        _ownership_reentry_independent_machine,
        _ownership_sync_thread_serialization,
        _ownership_async_task_serialization,
        _ownership_cross_loop_rejection,
        _ownership_mutator_baseexception_release,
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
        if identifier.startswith("priority."):
            guard_order = record.get("guard_order")
            if (
                not isinstance(guard_order, list)
                or not guard_order
                or len(guard_order) > 3
                or not all(isinstance(value, str) for value in guard_order)
            ):
                raise ConformanceError(
                    f"Conformance scenario {identifier} has invalid guard order."
                )
            for field in ("state", "stage", "target"):
                if field in record and not isinstance(record[field], str):
                    raise ConformanceError(
                        f"Conformance scenario {identifier} has invalid scalar outcome."
                    )
            for field in ("result_priority", "history_priority", "active_priority"):
                if (
                    field in record
                    and record[field] is not None
                    and (
                        type(record[field]) is bool
                        or not isinstance(record[field], int)
                    )
                ):
                    raise ConformanceError(
                        f"Conformance scenario {identifier} has invalid priority."
                    )
            for field in ("history_count", "observer_count"):
                if field in record and (
                    type(record[field]) is bool
                    or not isinstance(record[field], int)
                    or record[field] < 0
                    or record[field] > 3
                ):
                    raise ConformanceError(
                        f"Conformance scenario {identifier} has invalid count."
                    )
            for field in (
                "success",
                "committed",
                "cancelled",
                "lower_candidate_suppressed",
                "all_candidates_evaluated",
                "post_cancellation_reuse",
            ):
                if field in record and not isinstance(record[field], bool):
                    raise ConformanceError(
                        f"Conformance scenario {identifier} has invalid boolean outcome."
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
        required_values = expected.get("required_values", {})
        if not isinstance(required_values, Mapping):
            raise ConformanceError(
                f"Conformance scenario {identifier} has invalid required values."
            )
        for field, required_value in required_values.items():
            if record.get(field) != required_value:
                raise ConformanceError(
                    f"Conformance scenario {identifier} contradicted {field}."
                )
        if identifier.startswith("diagnostic."):
            exact_limit = record.get("exact_limit")
            exact_count = record.get("exact_count")
            one_less_limit = record.get("one_less_limit")
            if (
                isinstance(exact_limit, bool)
                or not isinstance(exact_limit, int)
                or exact_limit <= 0
                or exact_count != exact_limit
                or one_less_limit != exact_limit - 1
            ):
                raise ConformanceError(
                    f"Conformance scenario {identifier} has invalid budget boundary."
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
