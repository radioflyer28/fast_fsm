"""Private canonical-topology contract tests for Phase 16.

These tests intentionally use real ``State`` and ``StateMachine`` objects.  The
``graph_fingerprint`` helper makes every rejection assertion sensitive to registry
identity, endpoint/guard identity, topology version, active state, and the private
tool snapshot without turning any of those details into public API.
"""

from __future__ import annotations

import importlib.util
import threading
from enum import IntEnum
from pathlib import Path
from typing import Any

import pytest

from fast_fsm import FuncCondition, State, StateMachine, TransitionEntry
from fast_fsm.core import _TransitionGroup, _TransitionRequest


def graph_fingerprint(machine: StateMachine) -> tuple[Any, ...]:
    """Return a test-only identity fingerprint of a machine's topology."""
    transitions = tuple(
        sorted(
            (
                source_name,
                trigger,
                (
                    "group" if isinstance(slot, _TransitionGroup) else "singleton",
                    tuple(
                        (
                            id(entry),
                            entry.priority,
                            id(entry.to_state),
                            id(entry.condition)
                            if entry.condition is not None
                            else None,
                            entry.condition_ref,
                            entry.after,
                            entry.within,
                            entry.internal,
                        )
                        for entry in (
                            slot.entries
                            if isinstance(slot, _TransitionGroup)
                            else (slot,)
                        )
                    ),
                ),
            )
            for source_name, entries in machine._transitions.items()
            for trigger, slot in entries.items()
        )
    )
    snapshot = machine._graph_snapshot()
    return (
        tuple((name, id(state)) for name, state in sorted(machine._states.items())),
        transitions,
        machine._graph_version,
        id(machine.current_state),
        snapshot,
    )


def make_machine() -> tuple[StateMachine, State, State]:
    idle = State("idle")
    running = State("running")
    machine = StateMachine(idle, name="graph-contract")
    machine.add_state(running)
    return machine, idle, running


def test_graph_snapshot_is_fresh_sorted_immutable_and_canonical() -> None:
    machine, idle, running = make_machine()
    machine.add_transition("go", idle, running)

    first = machine._graph_snapshot()
    second = machine._graph_snapshot()

    assert first is not second
    assert first.name == "graph-contract"
    assert first.initial_state is idle
    assert first.states == (idle, running)
    assert first.transitions[0].from_state is idle
    assert first.transitions[0].to_state is running
    assert first.transitions[0].trigger == "go"
    assert first.graph_version == 2
    with pytest.raises((AttributeError, TypeError)):
        first.states += (State("invalid"),)
    with pytest.raises((AttributeError, TypeError)):
        first.transitions[0].trigger = "changed"

    later = machine._graph_snapshot()
    assert later.states == (idle, running)
    assert later.transitions[0].trigger == "go"


def test_graph_snapshot_flattens_candidate_groups_with_scalar_identity() -> None:
    """Cold graph projections retain every candidate in canonical order."""
    from fast_fsm import FuncCondition

    low = FuncCondition(lambda **kw: False, name="low")
    high = FuncCondition(lambda **kw: True, name="high")
    machine = StateMachine.from_dict(
        {
            "initial": "idle",
            "transitions": [
                {
                    "trigger": "go",
                    "from": "idle",
                    "to": "safe",
                    "priority": 5,
                    "condition_ref": "high",
                },
                {
                    "trigger": "go",
                    "from": "idle",
                    "to": "alternate",
                    "priority": -1,
                    "condition_ref": "low",
                },
                {
                    "trigger": "go",
                    "from": "middle",
                    "to": "safe",
                    "priority": 0,
                    "condition_ref": "high",
                },
            ],
        },
        conditions={"low": low, "high": high},
    )

    snapshot = machine._graph_snapshot()
    assert [
        (row.from_state_name, row.trigger, row.priority, row.condition_ref)
        for row in snapshot.transitions
    ] == [
        ("idle", "go", -1, "low"),
        ("idle", "go", 5, "high"),
        ("middle", "go", 0, "high"),
    ]
    assert snapshot.transitions[0].condition is low
    with pytest.raises((AttributeError, TypeError)):
        snapshot.transitions[0].condition_ref = "changed"


def test_graph_snapshot_captures_only_narrow_static_unconditional_evidence() -> None:
    """Snapshot proof is limited to an unguarded exact-base-State source."""

    class PermissionSubclass(State):
        def can_transition(self, **_: object) -> bool:
            raise AssertionError("diagnostic snapshots must not call state permissions")

    guard_calls = 0

    def guarded(**_: object) -> bool:
        nonlocal guard_calls
        guard_calls += 1
        raise AssertionError("diagnostic snapshots must not call guards")

    source = State("source")
    guarded_target = State("guarded")
    plain_target = State("plain")
    machine = StateMachine(source)
    machine.add_state(guarded_target)
    machine.add_state(plain_target)
    machine.add_transition("go", source, guarded_target, condition=guarded, priority=1)
    machine.add_transition("go", source, plain_target, priority=2)

    subclass_source = PermissionSubclass("subclass")
    subclass_target = State("subclass-target")
    subclass_machine = StateMachine(subclass_source)
    subclass_machine.add_state(subclass_target)
    subclass_machine.add_transition("go", subclass_source, subclass_target, priority=0)

    from fast_fsm.core import DeclarativeState

    declarative_source = DeclarativeState("declarative")
    declarative_target = State("declarative-target")
    declarative_machine = StateMachine(declarative_source)
    declarative_machine.add_state(declarative_target)
    declarative_machine.add_transition(
        "go", declarative_source, declarative_target, priority=0
    )

    snapshot = machine._graph_snapshot()
    subclass_snapshot = subclass_machine._graph_snapshot()
    declarative_snapshot = declarative_machine._graph_snapshot()

    assert [row.priority for row in snapshot.transitions] == [1, 2]
    assert [row.statically_unconditional for row in snapshot.transitions] == [
        False,
        True,
    ]
    assert subclass_snapshot.transitions[0].statically_unconditional is False
    assert declarative_snapshot.transitions[0].statically_unconditional is False
    assert guard_calls == 0
    with pytest.raises((AttributeError, TypeError)):
        snapshot.transitions[1].statically_unconditional = False


def test_clone_shares_candidate_identity_but_not_candidate_tables() -> None:
    """Clones rebuild entries while retaining canonical collaborator identity."""
    from fast_fsm import FuncCondition

    shared = FuncCondition(lambda **kw: True, name="shared")
    machine = StateMachine.from_dict(
        {
            "initial": "idle",
            "transitions": [
                {
                    "trigger": "go",
                    "from": "idle",
                    "to": "safe",
                    "priority": 1,
                    "condition_ref": "shared",
                },
                {
                    "trigger": "go",
                    "from": "idle",
                    "to": "alternate",
                    "priority": 2,
                    "condition_ref": "shared",
                },
            ],
        },
        conditions={"shared": shared},
    )

    clone = machine.clone()
    original_slot = machine._transitions["idle"]["go"]
    clone_slot = clone._transitions["idle"]["go"]
    assert clone._transitions is not machine._transitions
    assert clone._transitions["idle"] is not machine._transitions["idle"]
    assert clone_slot is not original_slot
    assert isinstance(clone_slot, _TransitionGroup)
    assert isinstance(original_slot, _TransitionGroup)
    assert all(
        clone_entry is not original_entry
        for clone_entry, original_entry in zip(
            clone_slot.entries, original_slot.entries, strict=True
        )
    )
    assert all(
        clone_entry.to_state is original_entry.to_state
        for clone_entry, original_entry in zip(
            clone_slot.entries, original_slot.entries, strict=True
        )
    )
    assert tuple(entry.condition_ref for entry in original_slot.entries) == (
        "shared",
        "shared",
    )
    assert all(entry.condition is shared for entry in clone_slot.entries)
    assert tuple(
        (entry.priority, entry.condition_ref, entry.after, entry.within)
        for entry in clone_slot.entries
    ) == tuple(
        (entry.priority, entry.condition_ref, entry.after, entry.within)
        for entry in original_slot.entries
    )

    clone.add_transition("go", "idle", "alternate", priority=-1)
    assert len(machine._transitions["idle"]["go"].entries) == 2
    assert len(clone._transitions["idle"]["go"].entries) == 3


def test_clone_reconstruction_failure_preserves_source_and_retryability(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A late clone transaction failure cannot mutate the source template."""
    spec = importlib.util.find_spec("fast_fsm.core")
    assert spec is not None and spec.origin is not None
    if spec.origin.endswith((".so", ".pyd")):
        pytest.skip("private monkeypatch injection requires the pure Python core")

    machine, idle, running = make_machine()
    complete = State("complete")
    machine.add_state(complete)
    machine.add_transition("go", idle, running, priority=1)
    machine.add_transition("go", idle, complete, priority=2)
    before = graph_fingerprint(machine)
    original_apply = StateMachine._apply_transition_requests_owned

    def fail_clone_apply(
        candidate: StateMachine, requests: tuple[_TransitionRequest, ...] | None
    ) -> None:
        if candidate is not machine:
            raise RuntimeError("injected clone reconstruction failure")
        original_apply(candidate, requests)

    monkeypatch.setattr(
        StateMachine, "_apply_transition_requests_owned", fail_clone_apply
    )
    with pytest.raises(RuntimeError, match="injected clone reconstruction failure"):
        machine.clone()
    assert graph_fingerprint(machine) == before

    monkeypatch.setattr(
        StateMachine, "_apply_transition_requests_owned", original_apply
    )
    clone = machine.clone()
    assert clone._graph_snapshot() == machine._graph_snapshot()
    assert clone._transitions["idle"]["go"] is not machine._transitions["idle"]["go"]


def test_retained_transition_adapters_use_the_canonical_request_transaction() -> None:
    """Each retained topology adapter has one request-based publication seam."""
    core_source = (
        Path(__file__).parents[1] / "src" / "fast_fsm" / "core.py"
    ).read_text()
    regions = (
        core_source[
            core_source.index("    def quick_build(") : core_source.index(
                "    @classmethod\n    def from_dict(",
                core_source.index("    def quick_build("),
            )
        ],
        core_source[
            core_source.index("    def from_dict(") : core_source.index(
                "    def to_dict(", core_source.index("    def from_dict(")
            )
        ],
        core_source[
            core_source.index(
                "    def _add_bidirectional_transition_owned("
            ) : core_source.index(
                "    def add_emergency_transition(",
                core_source.index("    def _add_bidirectional_transition_owned("),
            )
        ],
        core_source[
            core_source.index(
                "    def _add_emergency_transition_owned("
            ) : core_source.index(
                "    def can_trigger(",
                core_source.index("    def _add_emergency_transition_owned("),
            )
        ],
        core_source[
            core_source.index("    def _clone_owned(") : core_source.index(
                "    def _resolve_trigger(", core_source.index("    def _clone_owned(")
            )
        ],
    )

    for adapter_source in regions:
        assert "_TransitionRequest" in adapter_source
        assert adapter_source.count("_apply_transition_requests_owned") == 1
        assert "_commit_transition_plan" not in adapter_source


def test_declarative_builder_derives_into_one_canonical_transaction() -> None:
    """Builder declaration import owns no normalization, commit, or registry seam."""
    core_source = (
        Path(__file__).parents[1] / "src" / "fast_fsm" / "core.py"
    ).read_text()
    builder_start = core_source.index("class FSMBuilder:")
    build_start = core_source.index("    def build(", builder_start)
    build_end = core_source.index("    @property\n    def machine_type", build_start)
    build_source = core_source[build_start:build_end]

    assert "_DeclarativeHandler" not in build_source
    assert "_TransitionRequest" in build_source
    assert build_source.count("_apply_transition_requests_owned") == 1
    assert "_normalize_transition_request" not in build_source
    assert "_commit_transition_plan" not in build_source
    assert "candidate._transitions" not in build_source
    assert "self._transitions.append" not in build_source


def test_batch_transition_mode_rows_remain_one_canonical_request_transaction() -> None:
    """The batch parser carries internal mode without a second publication path."""
    core_source = (
        Path(__file__).parents[1] / "src" / "fast_fsm" / "core.py"
    ).read_text()
    parser_start = core_source.index("    def _transition_requests_from_rows(")
    parser_end = core_source.index(
        "    def add_bidirectional_transition(", parser_start
    )
    parser_source = core_source[parser_start:parser_end]

    assert "(3, 4, 5, 6, 7, 8)" in parser_source
    assert "internal: object = rest[4]" in parser_source
    assert "internal=internal" in parser_source
    assert parser_source.count("_apply_transition_requests_owned") == 1
    assert "_commit_transition_plan" not in parser_source


def test_priority_selectors_do_not_call_the_cold_projection_helper() -> None:
    """Phase 22 keeps direct singleton/group selection independently guarded."""
    core_source = (
        Path(__file__).parents[1] / "src" / "fast_fsm" / "core.py"
    ).read_text()
    start = core_source.index("    def _select_transition_sync(")
    end = core_source.index("    def _select_sync_candidate(", start)
    selector_source = core_source[start:end]
    assert "_transition_entries" not in selector_source
    assert "slot.entries" in selector_source


def test_version_changes_only_for_successful_topology_changes() -> None:
    idle = State("idle")
    running = State("running")
    machine = StateMachine(idle)

    assert machine._graph_version == 0
    machine.add_state(running)
    assert machine._graph_version == 1
    machine.add_state(running)
    assert machine._graph_version == 1
    machine.add_transition("go", idle, running)
    assert machine._graph_version == 2
    machine.force_state(running.name)
    assert machine._graph_version == 2
    machine.add_transition("go", idle, running)
    assert machine._graph_version == 2


def test_registration_requires_exact_identity_and_rejection_is_non_mutating() -> None:
    machine, idle, _ = make_machine()
    before = graph_fingerprint(machine)

    with pytest.raises(ValueError, match="already registered"):
        machine.add_state(State("idle"))
    assert graph_fingerprint(machine) == before

    machine.add_state(idle)
    assert graph_fingerprint(machine) == before

    with pytest.raises(TypeError, match="State"):
        machine.add_state(None)  # type: ignore[arg-type]
    assert graph_fingerprint(machine) == before


def test_single_state_snapshot_and_public_schemas_remain_unchanged() -> None:
    idle = State("")
    machine = StateMachine(idle, name="unicode-✓")

    graph = machine._graph_snapshot()
    assert graph.states == (idle,)
    assert graph.transitions == ()
    assert graph.initial_state is idle
    assert graph.graph_version == 0
    assert machine.snapshot() == {"state": "", "version": 1}
    assert machine.to_dict() == {
        "name": "unicode-✓",
        "initial": "",
        "states": [""],
        "final_states": [],
        "transitions": [],
    }


def test_clone_copies_graph_version_into_an_independent_lineage() -> None:
    machine, idle, running = make_machine()
    machine.add_transition("go", idle, running)

    clone = machine.clone()

    assert clone._graph_version == machine._graph_version
    clone.add_transition("back", running, idle)
    assert clone._graph_version == machine._graph_version + 1
    assert machine._graph_snapshot().transitions != clone._graph_snapshot().transitions


@pytest.mark.parametrize(
    ("from_state", "to_state"),
    [
        ("unknown", "running"),
        ("idle", "unknown"),
        (State("idle"), "running"),
        ("idle", State("running")),
        (None, "running"),
        ("idle", None),
    ],
)
def test_endpoints_must_be_exact_registered_objects_without_mutation(
    from_state: object, to_state: object
) -> None:
    machine, _, _ = make_machine()
    before = graph_fingerprint(machine)

    with pytest.raises((TypeError, ValueError)):
        machine.add_transition("go", from_state, to_state)  # type: ignore[arg-type]

    assert graph_fingerprint(machine) == before


def test_multi_source_and_batch_validation_are_atomic() -> None:
    machine, idle, running = make_machine()
    before = graph_fingerprint(machine)

    invalid_requests = (
        lambda: machine.add_transition("go", [], running),
        lambda: machine.add_transition("go", [idle, idle], running),
        lambda: machine.add_transition("go", [idle, State("foreign")], running),
        lambda: machine.add_transition("go", [idle, None], running),
        lambda: machine.add_transition(
            "go", idle, running, condition=lambda **_: True, unless=lambda **_: False
        ),
        lambda: machine.add_transitions(
            [("go", idle, running), ("bad", "unknown", running)]
        ),
    )

    for request in invalid_requests:
        with pytest.raises(ValueError):
            request()
        assert graph_fingerprint(machine) == before


def test_final_source_mixed_batch_and_multi_source_fail_before_publication() -> None:
    """A late canonical final source rejects the complete request transaction."""
    machine, idle, running = make_machine()
    done = State("done", final=True)
    machine.add_state(done)
    before = graph_fingerprint(machine)

    with pytest.raises(ValueError, match="^final state cannot be a transition source$"):
        machine.add_transitions(
            [
                ("first", idle, running),
                ("invalid", done, idle),
                ("last", running, idle),
            ]
        )
    assert graph_fingerprint(machine) == before

    with pytest.raises(ValueError, match="^final state cannot be a transition source$"):
        machine.add_transition("fanout", [idle, done], running)
    assert graph_fingerprint(machine) == before


def test_final_source_validation_lives_only_in_canonical_normalization() -> None:
    """Dispatch and lifecycle code stay unaware of construction-only finality."""
    core_source = (
        Path(__file__).parents[1] / "src" / "fast_fsm" / "core.py"
    ).read_text()
    normalizer_start = core_source.index("    def _normalize_transition_request(")
    normalizer_end = core_source.index(
        "    def _commit_transition_plan(", normalizer_start
    )
    normalizer = core_source[normalizer_start:normalizer_end]
    selector_start = core_source.index("    def _prepare_transition(")
    selector_end = core_source.index("    def _execute_transition(", selector_start)
    selector = core_source[selector_start:selector_end]

    assert normalizer.count("final state cannot be a transition source") == 1
    assert normalizer.index(
        "source = self._resolve_canonical_state"
    ) < normalizer.index("final state cannot be a transition source")
    assert "final state cannot be a transition source" not in selector


def test_final_source_helpers_and_priority_reject_without_a_prefix() -> None:
    """Helper fanout and candidate registration share the same atomic rule."""
    idle = State("idle")
    done = State("done", final=True)
    safe = State("safe")
    machine = StateMachine(idle)
    machine.add_state(done)
    machine.add_state(safe)
    before = graph_fingerprint(machine)

    with pytest.raises(ValueError, match="^final state cannot be a transition source$"):
        machine.add_bidirectional_transition("finish", "restart", idle, done)
    assert graph_fingerprint(machine) == before

    with pytest.raises(ValueError, match="^final state cannot be a transition source$"):
        machine.add_emergency_transition("abort", safe)
    assert graph_fingerprint(machine) == before

    machine.add_transition("advance", idle, safe, priority=3)
    before_priority = graph_fingerprint(machine)
    with pytest.raises(ValueError, match="^final state cannot be a transition source$"):
        machine.add_transition("advance", done, safe, priority=-1)
    assert graph_fingerprint(machine) == before_priority


def test_declarative_and_corrupted_clone_final_sources_never_publish() -> None:
    """Declarative and clone reconstruction remain ordinary canonical clients."""
    from fast_fsm.core import DeclarativeState

    source = DeclarativeState("done", final=True)
    target = State("idle")
    machine = StateMachine(source)
    machine.add_state(target)
    before = graph_fingerprint(machine)

    with pytest.raises(ValueError, match="^final state cannot be a transition source$"):
        machine.add_transition("restart", source, target)
    assert graph_fingerprint(machine) == before

    valid_source = State("source")
    valid_final = State("final", final=True)
    valid = StateMachine(valid_source)
    valid.add_state(valid_final)
    valid.add_transition("finish", valid_source, valid_final)
    clone = valid.clone()
    assert clone._states["final"] is valid_final
    assert (
        clone._transitions["source"]["finish"]
        is not valid._transitions["source"]["finish"]
    )

    corrupted = StateMachine(source)
    corrupted.add_state(target)
    corrupted._transitions[source.name]["invalid"] = TransitionEntry(target)
    corrupted_before = graph_fingerprint(corrupted)
    with pytest.raises(ValueError, match="^final state cannot be a transition source$"):
        corrupted.clone()
    assert graph_fingerprint(corrupted) == corrupted_before


def test_bidirectional_and_emergency_helpers_commit_as_single_transactions() -> None:
    machine, idle, running = make_machine()
    before = graph_fingerprint(machine)

    with pytest.raises(TypeError):
        machine.add_bidirectional_transition(
            "go",
            "back",
            idle,
            running,
            condition2=object(),  # type: ignore[arg-type]
        )
    assert graph_fingerprint(machine) == before

    machine.add_bidirectional_transition("go", "back", idle, running)
    assert machine._graph_version == before[2] + 1

    emergency_before = machine._graph_version
    machine.add_emergency_transition("stop", idle)
    assert machine._graph_version == emergency_before + 1
    assert {
        row.from_state
        for row in machine._graph_snapshot().transitions
        if row.trigger == "stop"
    } == {
        idle,
        running,
    }


class _PriorityIntEnum(IntEnum):
    """An integer-like value which the priority boundary must reject."""

    VALUE = 1


class _PriorityIntSubclass(int):
    """An exact-int boundary regression input."""


class _PriorityCoercible:
    """An object whose ``__int__`` must never run during registration."""

    def __int__(self) -> int:
        return 1


def test_priority_registration_keeps_singletons_direct_and_groups_immutable() -> None:
    machine, idle, running = make_machine()
    complete = State("complete")
    machine.add_state(complete)

    machine.add_transition("go", idle, running)
    singleton = machine._transitions[idle.name]["go"]

    assert isinstance(singleton, TransitionEntry)
    assert singleton.priority == 0

    machine.add_transition("go", idle, complete, priority=-4)
    group = machine._transitions[idle.name]["go"]

    assert isinstance(group, _TransitionGroup)
    assert tuple(entry.priority for entry in group.entries) == (-4, 0)
    assert tuple(entry.to_state for entry in group.entries) == (complete, running)
    with pytest.raises((AttributeError, TypeError)):
        group.entries += (singleton,)  # type: ignore[misc]
    with pytest.raises((AttributeError, TypeError)):
        group.entries[0] = singleton  # type: ignore[index]


@pytest.mark.parametrize(
    "priority",
    [
        True,
        _PriorityIntEnum.VALUE,
        _PriorityIntSubclass(1),
        1.0,
        "1",
        _PriorityCoercible(),
    ],
)
def test_priority_rejection_happens_before_topology_or_version_mutation(
    priority: object,
) -> None:
    machine, idle, running = make_machine()
    machine.add_transition("go", idle, running)
    before_slot = machine._transitions[idle.name]["go"]
    before_version = machine._graph_version

    with pytest.raises(TypeError, match="priority"):
        machine.add_transition("go", idle, running, priority=priority)

    assert machine._transitions[idle.name]["go"] is before_slot
    assert machine._graph_version == before_version


def test_grouped_runtime_selects_while_projections_remain_candidate_complete() -> None:
    machine, idle, running = make_machine()
    complete = State("complete")
    machine.add_state(complete)
    machine.add_transition("go", idle, running, priority=1)
    machine.add_transition("go", idle, complete, priority=0)

    assert machine.can_trigger("go")
    result = machine.trigger("go")
    assert result.success
    assert result.to_state == "complete"
    assert machine.to_dict()["transitions"] == [
        {"trigger": "go", "from": "idle", "to": "complete", "priority": 0},
        {"trigger": "go", "from": "idle", "to": "running", "priority": 1},
    ]


def test_exact_duplicate_is_version_neutral_and_preserves_slot_identity() -> None:
    machine, idle, running = make_machine()
    machine.add_transition("go", idle, running, priority=-2)
    first = machine._transitions[idle.name]["go"]
    before_version = machine._graph_version

    machine.add_transition("go", idle, running, priority=-2)

    assert machine._transitions[idle.name]["go"] is first
    assert machine._graph_version == before_version


def test_internal_registration_rejects_non_self_canonical_endpoints_atomically() -> (
    None
):
    """Internal mode is valid only for an identical canonical source and target."""
    machine, idle, running = make_machine()
    before = graph_fingerprint(machine)

    with pytest.raises(ValueError, match="internal transition"):
        machine.add_transition("refresh", idle, running, internal=True)

    assert graph_fingerprint(machine) == before


@pytest.mark.parametrize("internal", (1, 0, "true", object()))
def test_internal_requires_an_exact_builtin_bool_before_mutation(
    internal: object,
) -> None:
    """Truthy and coercible inputs cannot weaken the immutable mode contract."""
    machine, idle, _ = make_machine()
    before = graph_fingerprint(machine)

    with pytest.raises(TypeError, match="exact built-in bool"):
        machine.add_transition("refresh", idle, idle, internal=internal)

    assert graph_fingerprint(machine) == before


def test_mode_is_part_of_equal_priority_candidate_identity() -> None:
    """External and internal candidates cannot silently collapse as duplicates."""
    machine, idle, _ = make_machine()
    machine.add_transition("refresh", idle, idle)
    first_slot = machine._transitions[idle.name]["refresh"]
    before_version = machine._graph_version

    with pytest.raises(ValueError, match="priority"):
        machine.add_transition("refresh", idle, idle, internal=True)

    assert machine._transitions[idle.name]["refresh"] is first_slot
    assert machine._graph_version == before_version


def test_graph_snapshot_and_clone_preserve_internal_mode_independently() -> None:
    """Cold projections retain mode without sharing mutable topology containers."""
    machine, idle, _ = make_machine()
    machine.add_transition("refresh", idle, idle, internal=True)

    snapshot = machine._graph_snapshot()
    assert snapshot.transitions[0].internal is True

    clone = machine.clone()
    original_slot = machine._transitions[idle.name]["refresh"]
    clone_slot = clone._transitions[idle.name]["refresh"]
    assert clone_slot is not original_slot
    assert clone_slot.internal is True


def test_construction_request_copies_sources_and_is_immutable() -> None:
    machine, idle, running = make_machine()
    raw_sources = [idle]

    request = _TransitionRequest("go", tuple(raw_sources), running)
    raw_sources.append(running)

    assert request.sources == (idle,)
    assert request.sources[0] is idle
    assert request.to_state is running
    with pytest.raises((AttributeError, TypeError)):
        request.trigger = "changed"  # type: ignore[misc]


def test_construction_request_direct_and_batch_share_canonical_transaction() -> None:
    direct, direct_idle, direct_running = make_machine()
    batch, batch_idle, batch_running = make_machine()

    direct.add_transition("go", direct_idle, direct_running, priority=-3)
    batch.add_transitions([("go", batch_idle, batch_running, None, -3)])

    direct_row = direct._graph_snapshot().transitions[0]
    batch_row = batch._graph_snapshot().transitions[0]
    assert (
        direct_row.trigger,
        direct_row.from_state_name,
        direct_row.to_state_name,
        direct_row.priority,
    ) == (
        batch_row.trigger,
        batch_row.from_state_name,
        batch_row.to_state_name,
        batch_row.priority,
    )
    assert direct._graph_version == batch._graph_version


def test_construction_request_collection_rejects_before_publication() -> None:
    machine, idle, running = make_machine()
    before = graph_fingerprint(machine)

    with pytest.raises(TypeError, match="request collection"):
        machine._apply_transition_requests_owned(None)  # type: ignore[arg-type]
    assert graph_fingerprint(machine) == before

    with pytest.raises(TypeError, match="transition request"):
        machine._apply_transition_requests_owned(
            (
                _TransitionRequest("go", (idle,), running),
                object(),  # type: ignore[arg-type]
            )
        )
    assert graph_fingerprint(machine) == before

    machine._apply_transition_requests_owned(())
    assert graph_fingerprint(machine) == before


def test_construction_request_batch_publishes_all_slots_once() -> None:
    machine, idle, running = make_machine()
    complete = State("complete")
    machine.add_state(complete)
    before_version = machine._graph_version

    machine.add_transitions(
        [
            ("go", idle, running, None, 5),
            ("go", idle, complete, None, -2),
            ("finish", running, complete),
        ]
    )

    group = machine._transitions[idle.name]["go"]
    assert isinstance(group, _TransitionGroup)
    assert tuple(entry.priority for entry in group.entries) == (-2, 5)
    assert machine._transitions[running.name]["finish"].to_state is complete
    assert machine._graph_version == before_version + 1


def test_construction_request_adapters_delegate_only_to_canonical_apply() -> None:
    core_source = (
        Path(__file__).parents[1] / "src" / "fast_fsm" / "core.py"
    ).read_text()
    direct_start = core_source.index("    def _add_transition_owned(")
    direct_end = core_source.index("    def add_transitions(", direct_start)
    batch_start = core_source.index("    def _add_transitions_owned(")
    batch_end = core_source.index("    def add_bidirectional_transition(", batch_start)

    for adapter_source in (
        core_source[direct_start:direct_end],
        core_source[batch_start:batch_end],
    ):
        assert "_apply_transition_requests_owned" in adapter_source
        assert "_normalize_transition_request" not in adapter_source
        assert "_commit_transition_plan" not in adapter_source


def test_construction_request_is_idempotent_with_complete_candidate_identity() -> None:
    machine, idle, running = make_machine()
    condition = FuncCondition(lambda **_: True, name="allowed")
    request = _TransitionRequest(
        "go",
        (idle,),
        running,
        condition,
        priority=-4,
        condition_ref="allowed",
        after=1,
        within=3,
    )

    machine._apply_transition_requests_owned((request,))
    first_slot = machine._transitions[idle.name]["go"]
    first_version = machine._graph_version
    first_snapshot = machine._graph_snapshot()

    machine._apply_transition_requests_owned((request,))

    assert machine._transitions[idle.name]["go"] is first_slot
    assert machine._graph_version == first_version
    assert machine.current_state is idle
    assert machine._graph_snapshot() == first_snapshot


class _InterruptingSources(list[State]):
    """Raise a BaseException after exposing one raw source."""

    def __iter__(self):
        yield self[0]
        raise KeyboardInterrupt


def test_construction_request_interruption_releases_ownership_without_publication() -> (
    None
):
    machine, idle, running = make_machine()
    before = graph_fingerprint(machine)

    with pytest.raises(KeyboardInterrupt):
        machine.add_transition("go", _InterruptingSources([idle]), running)

    assert graph_fingerprint(machine) == before
    machine.add_transition("go", idle, running)
    assert machine._transitions[idle.name]["go"].to_state is running


def test_concurrent_construction_requests_are_serialized_as_whole_transactions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec = importlib.util.find_spec("fast_fsm.core")
    assert spec is not None and spec.origin is not None
    if spec.origin.endswith((".so", ".pyd")):
        pytest.skip("private monkeypatch injection requires the pure Python core")

    machine, idle, running = make_machine()
    complete = State("complete")
    machine.add_state(complete)
    before = graph_fingerprint(machine)
    first_owned = threading.Event()
    release_first = threading.Event()
    second_started = threading.Event()
    failures: list[BaseException] = []
    original_apply = StateMachine._apply_transition_requests_owned

    def paused_apply(
        owned_machine: StateMachine,
        requests: tuple[_TransitionRequest, ...] | None,
    ) -> None:
        if requests and requests[0].trigger == "first":
            first_owned.set()
            if not release_first.wait(timeout=2):
                raise RuntimeError("test failed to release first construction request")
        original_apply(owned_machine, requests)

    monkeypatch.setattr(StateMachine, "_apply_transition_requests_owned", paused_apply)

    def register(trigger: str, target: State) -> None:
        try:
            if trigger == "second":
                second_started.set()
            machine.add_transition(trigger, idle, target)
        except BaseException as error:
            failures.append(error)

    first = threading.Thread(target=register, args=("first", running))
    second = threading.Thread(target=register, args=("second", complete))
    first.start()
    assert first_owned.wait(timeout=2)
    second.start()
    assert second_started.wait(timeout=2)
    assert "first" not in machine._transitions[idle.name]
    assert "second" not in machine._transitions[idle.name]
    assert machine._graph_version == before[2]
    assert second.is_alive()

    release_first.set()
    first.join(timeout=2)
    second.join(timeout=2)

    assert not first.is_alive()
    assert not second.is_alive()
    assert failures == []
    assert machine._transitions[idle.name]["first"].to_state is running
    assert machine._transitions[idle.name]["second"].to_state is complete


def test_internal_construction_requests_publish_whole_transactions_under_contention(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mode propagation remains inside the existing single-owner transaction."""
    spec = importlib.util.find_spec("fast_fsm.core")
    assert spec is not None and spec.origin is not None
    if spec.origin.endswith((".so", ".pyd")):
        pytest.skip("private monkeypatch injection requires the pure Python core")

    machine, idle, _ = make_machine()
    before = graph_fingerprint(machine)
    first_owned = threading.Event()
    release_first = threading.Event()
    second_started = threading.Event()
    failures: list[BaseException] = []
    original_apply = StateMachine._apply_transition_requests_owned

    def paused_apply(
        owned_machine: StateMachine,
        requests: tuple[_TransitionRequest, ...] | None,
    ) -> None:
        if requests and requests[0].trigger == "first":
            first_owned.set()
            if not release_first.wait(timeout=2):
                raise RuntimeError("test failed to release first construction request")
        original_apply(owned_machine, requests)

    monkeypatch.setattr(StateMachine, "_apply_transition_requests_owned", paused_apply)

    def register(trigger: str) -> None:
        try:
            if trigger == "second":
                second_started.set()
            machine.add_transition(trigger, idle, idle, internal=True)
        except BaseException as error:
            failures.append(error)

    first = threading.Thread(target=register, args=("first",))
    second = threading.Thread(target=register, args=("second",))
    first.start()
    assert first_owned.wait(timeout=2)
    second.start()
    assert second_started.wait(timeout=2)
    assert "first" not in machine._transitions[idle.name]
    assert "second" not in machine._transitions[idle.name]
    assert machine._graph_version == before[2]
    assert second.is_alive()

    release_first.set()
    first.join(timeout=2)
    second.join(timeout=2)

    assert not first.is_alive()
    assert not second.is_alive()
    assert failures == []
    assert machine._transitions[idle.name]["first"].internal is True
    assert machine._transitions[idle.name]["second"].internal is True


def test_construction_hot_path_symbols_are_absent_from_runtime_regions() -> None:
    core_source = (
        Path(__file__).parents[1] / "src" / "fast_fsm" / "core.py"
    ).read_text()
    regions = (
        core_source[
            core_source.index("    def _select_transition_sync(") : core_source.index(
                "    def _select_sync_candidate("
            )
        ],
        core_source[
            core_source.index("    def _execute_transition(") : core_source.index(
                "    def _execute_control_transition("
            )
        ],
        core_source[
            core_source.index(
                "    async def _execute_transition_async("
            ) : core_source.index("    async def can_trigger_async(")
        ],
        core_source[
            core_source.index(
                "    async def _select_transition_async("
            ) : core_source.index("    async def _select_async_candidate(")
        ],
    )

    for region in regions:
        assert "_TransitionRequest" not in region
        assert "_apply_transition_requests_owned" not in region
        assert "_fsm_declarations" not in region
        assert "_discover_handlers" not in region
        assert "_DeclarativeHandlerMetadata" not in region
        assert "warnings.warn" not in region


def test_equal_priority_conflict_rolls_back_all_staged_replacements() -> None:
    machine, idle, running = make_machine()
    complete = State("complete")
    failed = State("failed")
    machine.add_state(complete)
    machine.add_state(failed)
    machine.add_transition("go", idle, running, priority=0)
    before = graph_fingerprint(machine)

    new_candidate = machine._normalize_transition_request(
        "go", idle, complete, priority=-1
    )
    late_conflict = machine._normalize_transition_request(
        "go", idle, failed, priority=0
    )
    with pytest.raises(ValueError, match="priority"):
        machine._commit_transition_plan((new_candidate, late_conflict))

    assert graph_fingerprint(machine) == before


def test_staged_same_slot_merges_once_and_sorts_all_candidates() -> None:
    machine, idle, running = make_machine()
    complete = State("complete")
    failed = State("failed")
    machine.add_state(complete)
    machine.add_state(failed)
    before_version = machine._graph_version

    plans = (
        machine._normalize_transition_request("go", idle, running, priority=7),
        machine._normalize_transition_request("go", idle, complete, priority=-3),
        machine._normalize_transition_request("go", idle, failed, priority=2),
    )
    machine._commit_transition_plan(plans)
    group = machine._transitions[idle.name]["go"]

    assert isinstance(group, _TransitionGroup)
    assert tuple(entry.priority for entry in group.entries) == (-3, 2, 7)
    assert tuple(entry.to_state for entry in group.entries) == (
        complete,
        failed,
        running,
    )
    assert machine._graph_version == before_version + 1


def test_repeated_raw_callable_and_unless_values_conflict_by_condition_identity() -> (
    None
):
    machine, idle, running = make_machine()

    def permitted(**_: object) -> bool:
        return True

    machine.add_transition("go", idle, running, condition=permitted, priority=1)
    with pytest.raises(ValueError, match="priority"):
        machine.add_transition("go", idle, running, condition=permitted, priority=1)

    machine.add_transition("back", idle, running, unless=permitted, priority=2)
    with pytest.raises(ValueError, match="priority"):
        machine.add_transition("back", idle, running, unless=permitted, priority=2)


def test_priority_helpers_transport_atomic_fanout_without_interpreting_winners() -> (
    None
):
    """Every priority helper stages a complete topology plan before publication."""
    machine, idle, running = make_machine()
    complete = State("complete")
    machine.add_state(complete)

    before_batch = machine._graph_version
    machine.add_transitions(
        [
            ("go", idle, running, None, 7),
            ("go", idle, complete, None, -3),
            ("advance", [idle, running], complete, None, 2),
        ]
    )

    go_slot = machine._transitions["idle"]["go"]
    assert isinstance(go_slot, _TransitionGroup)
    assert tuple(entry.priority for entry in go_slot.entries) == (-3, 7)
    assert machine._transitions["idle"]["advance"].priority == 2
    assert machine._transitions["running"]["advance"].priority == 2
    assert machine._graph_version == before_batch + 1

    before_conflict = {
        (source_name, trigger): slot
        for source_name, entries in machine._transitions.items()
        for trigger, slot in entries.items()
    }
    before_conflict_version = machine._graph_version
    with pytest.raises(ValueError, match="priority"):
        machine.add_transitions(
            [
                ("go", idle, complete, None, -9),
                ("go", idle, running, None, -3),
            ]
        )
    assert {
        (source_name, trigger): slot
        for source_name, entries in machine._transitions.items()
        for trigger, slot in entries.items()
    } == before_conflict
    assert machine._graph_version == before_conflict_version

    before_bidirectional = machine._graph_version
    machine.add_bidirectional_transition(
        "forward",
        "reverse",
        idle,
        running,
        priority1=-11,
        priority2=13,
    )
    assert machine._transitions["idle"]["forward"].priority == -11
    assert machine._transitions["running"]["reverse"].priority == 13
    assert machine._graph_version == before_bidirectional + 1

    before_emergency = machine._graph_version
    machine.add_emergency_transition("abort", complete, priority=-20)
    assert {
        machine._transitions[state.name]["abort"].priority
        for state in (idle, running, complete)
    } == {-20}
    assert machine._graph_version == before_emergency + 1
