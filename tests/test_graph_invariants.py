"""Private canonical-topology contract tests for Phase 16.

These tests intentionally use real ``State`` and ``StateMachine`` objects.  The
``graph_fingerprint`` helper makes every rejection assertion sensitive to registry
identity, endpoint/guard identity, topology version, active state, and the private
tool snapshot without turning any of those details into public API.
"""

from __future__ import annotations

from enum import IntEnum
from typing import Any

import pytest

from fast_fsm import State, StateMachine, TransitionEntry
from fast_fsm.core import _TransitionGroup


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


def test_clone_shares_candidate_identity_but_not_candidate_tables() -> None:
    """Clones retain immutable entries/references while registrations isolate."""
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
    assert clone._transitions["idle"]["go"] is original_slot
    assert tuple(entry.condition_ref for entry in original_slot.entries) == (
        "shared",
        "shared",
    )
    assert all(entry.condition is shared for entry in original_slot.entries)

    clone.add_transition("go", "idle", "alternate", priority=-1)
    assert len(machine._transitions["idle"]["go"].entries) == 2
    assert len(clone._transitions["idle"]["go"].entries) == 3


def test_priority_selectors_do_not_call_the_cold_projection_helper() -> None:
    """Phase 22 keeps direct singleton/group selection independently guarded."""
    import inspect

    selector_source = inspect.getsource(StateMachine._select_transition_sync)
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


def test_grouped_runtime_selects_while_projections_remain_fail_closed() -> None:
    machine, idle, running = make_machine()
    complete = State("complete")
    machine.add_state(complete)
    machine.add_transition("go", idle, running, priority=1)
    machine.add_transition("go", idle, complete, priority=0)

    assert machine.can_trigger("go")
    result = machine.trigger("go")
    assert result.success
    assert result.to_state == "complete"
    with pytest.raises(
        RuntimeError,
        match="Priority candidate groups are not supported by this projection",
    ):
        machine.to_dict()


def test_exact_duplicate_is_version_neutral_and_preserves_slot_identity() -> None:
    machine, idle, running = make_machine()
    machine.add_transition("go", idle, running, priority=-2)
    first = machine._transitions[idle.name]["go"]
    before_version = machine._graph_version

    machine.add_transition("go", idle, running, priority=-2)

    assert machine._transitions[idle.name]["go"] is first
    assert machine._graph_version == before_version


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
