"""Strict diagnostic contracts staged by Phase 19.

The green tests in this module exercise the one-snapshot reachability tracer.
Later-plan contracts are added as strict XFAIL rows once the tracer exists.
"""

from __future__ import annotations

import pytest

from fast_fsm import FSMValidator, State, StateMachine
from fast_fsm._diagnostics import DiagnosticBudgetExceeded, DiagnosticLimits
from fast_fsm.conditions import FuncCondition


def _moved_machine(*, label: str = "diagnostic-machine") -> tuple[
    StateMachine, State, State, State, FuncCondition
]:
    """Build a real machine whose runtime state differs from its initial state."""
    initial = State("initial")
    middle = State("middle")
    orphan = State("orphan")
    condition = FuncCondition(lambda: True, name="condition-label")
    machine = StateMachine(initial, name=label)
    machine.add_state(middle)
    machine.add_state(orphan)
    machine.add_transition("advance", initial, middle, condition)
    machine.trigger("advance")
    return machine, initial, middle, orphan, condition


def test_declared_initial_reachability_reports_current_state_separately() -> None:
    machine, _, _, _, _ = _moved_machine()

    validator = FSMValidator(machine)

    assert validator.initial_state == "initial"
    assert validator.current_state == "middle"
    assert validator.get_reachable_states() == {"initial", "middle"}
    assert validator.find_unreachable_states() == {"orphan"}
    report = validator.validate_completeness()
    assert report["initial_state"] == "initial"
    assert report["current_state"] == "middle"


def test_snapshot_captures_immutable_scalar_labels() -> None:
    machine, initial, middle, _, condition = _moved_machine()

    snapshot = machine._graph_snapshot()
    initial.name = "initial-mutated"
    middle.name = "middle-mutated"
    condition.name = "condition-mutated"

    assert snapshot.initial_state_name == "initial"
    assert snapshot.current_state_name == "middle"
    assert snapshot.state_names == ("initial", "middle", "orphan")
    assert snapshot.transitions[0].from_state_name == "initial"
    assert snapshot.transitions[0].to_state_name == "middle"
    assert snapshot.transitions[0].condition_name == "condition-label"


def test_validator_captures_once_and_reachability_uses_only_the_snapshot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    machine, initial, middle, _, condition = _moved_machine()
    original_snapshot = StateMachine._graph_snapshot
    calls = 0

    def capture_then_mutate(self: StateMachine):
        nonlocal calls
        calls += 1
        snapshot = original_snapshot(self)
        initial.name = "initial-after-capture"
        middle.name = "middle-after-capture"
        condition.name = "condition-after-capture"
        return snapshot

    monkeypatch.setattr(StateMachine, "_graph_snapshot", capture_then_mutate)

    validator = FSMValidator(machine, limits=DiagnosticLimits(max_work=100))

    assert calls == 1
    assert validator.get_reachable_states() == {"initial", "middle"}
    assert validator.find_unreachable_states() == {"orphan"}
    assert validator._diagnostic_graph.state_names == ("initial", "middle", "orphan")
    assert validator._diagnostic_graph.edges[0].condition_name == "condition-label"


def test_exact_work_budget_succeeds_and_one_less_fails_redacted() -> None:
    machine, _, _, _, _ = _moved_machine(label="caller-secret-machine")

    generous = FSMValidator(machine, limits=DiagnosticLimits(max_work=100))
    assert generous.get_reachable_states() == {"initial", "middle"}
    required_work = generous.diagnostic_status.work_count
    assert required_work > 0

    exact = FSMValidator(machine, limits=DiagnosticLimits(max_work=required_work))
    assert exact.get_reachable_states() == {"initial", "middle"}
    assert exact.diagnostic_status.complete is True
    assert exact.diagnostic_status.work_count == required_work

    exhausted = FSMValidator(
        machine, limits=DiagnosticLimits(max_work=required_work - 1)
    )
    with pytest.raises(DiagnosticBudgetExceeded) as raised:
        exhausted.get_reachable_states()

    assert str(raised.value) == "diagnostic budget exhausted"
    assert "caller-secret-machine" not in str(raised.value)
    assert raised.value.status.complete is False
    assert raised.value.status.exhausted_dimension == "max_work"
    assert raised.value.status.exhausted_stage in {
        "reachability.visit",
        "reachability.edge",
    }
    assert raised.value.status.work_count == required_work - 1
