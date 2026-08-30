"""Private canonical-topology contract tests for Phase 16.

These tests intentionally use real ``State`` and ``StateMachine`` objects.  The
``graph_fingerprint`` helper makes every rejection assertion sensitive to registry
identity, endpoint/guard identity, topology version, active state, and the private
tool snapshot without turning any of those details into public API.
"""

from __future__ import annotations

from typing import Any

import pytest

from fast_fsm import State, StateMachine


def graph_fingerprint(machine: StateMachine) -> tuple[Any, ...]:
    """Return a test-only identity fingerprint of a machine's topology."""
    transitions = tuple(
        sorted(
            (
                source_name,
                trigger,
                id(entry.to_state),
                id(entry.condition) if entry.condition is not None else None,
            )
            for source_name, entries in machine._transitions.items()
            for trigger, entry in entries.items()
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
