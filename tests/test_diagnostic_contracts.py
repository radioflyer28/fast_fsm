"""Strict diagnostic contracts staged by Phase 19.

The green tests in this module exercise the one-snapshot reachability tracer.
Later-plan contracts are added as strict XFAIL rows once the tracer exists.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
from collections.abc import Callable
from pathlib import Path

import pytest
import fast_fsm._diagnostics as diagnostics

from fast_fsm import (
    DiagnosticBudgetExceeded,
    DiagnosticLimits,
    DiagnosticStatus,
    FSMValidator,
    State,
    StateMachine,
    batch_validate,
    compare_fsms,
    to_json,
    validate_and_score,
)
from fast_fsm._diagnostics import (
    _DiagnosticBudget,
    _dense_adjacency,
    _generate_paths,
    _graph_from_snapshot,
    _sparse_adjacency,
    _strongly_connected_components,
    _structural_depth,
)
from fast_fsm.conditions import FuncCondition


def _moved_machine(
    *, label: str = "diagnostic-machine"
) -> tuple[StateMachine, State, State, State, FuncCondition]:
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


@pytest.fixture
def single_state_machine() -> StateMachine:
    """A real single-state graph for the diagnostic fixture inventory."""
    return StateMachine.from_states("only", name="single-state")


@pytest.fixture
def empty_machine() -> StateMachine:
    """The smallest valid real machine: no transitions and one initial state."""
    return StateMachine.from_states("empty", name="empty")


@pytest.fixture
def self_loop_machine() -> StateMachine:
    """A real graph with a one-state cyclic SCC."""
    machine = StateMachine.from_states("loop", name="self-loop")
    machine.add_transition("again", "loop", "loop")
    return machine


@pytest.fixture
def three_cycle_machine() -> StateMachine:
    """A real three-member cyclic SCC."""
    machine = StateMachine.from_states("a", "b", "c", initial="a", name="cycle")
    machine.add_transition("ab", "a", "b")
    machine.add_transition("bc", "b", "c")
    machine.add_transition("ca", "c", "a")
    return machine


@pytest.fixture
def multi_scc_tail_machine() -> StateMachine:
    """Two cyclic components plus an acyclic tail for future SCC assertions."""
    machine = StateMachine.from_states(
        "a", "b", "c", "d", "tail", initial="a", name="multi-scc"
    )
    machine.add_transition("ab", "a", "b")
    machine.add_transition("ba", "b", "a")
    machine.add_transition("bc", "b", "c")
    machine.add_transition("cd", "c", "d")
    machine.add_transition("dc", "d", "c")
    machine.add_transition("tail", "d", "tail")
    return machine


@pytest.fixture
def long_chain_machine() -> StateMachine:
    """An iterative-depth fixture longer than Python's normal recursion limit."""
    names = tuple(f"chain-{index}" for index in range(1_100))
    machine = StateMachine.from_states(*names, initial=names[0], name="long-chain")
    for index in range(len(names) - 1):
        machine.add_transition(f"next-{index}", names[index], names[index + 1])
    return machine


@pytest.fixture
def high_fanout_machine() -> StateMachine:
    """A deterministic high-fan-out DAG."""
    names = ("root",) + tuple(f"leaf-{index}" for index in range(32))
    machine = StateMachine.from_states(*names, initial="root", name="fanout")
    for leaf in names[1:]:
        machine.add_transition(f"to-{leaf}", "root", leaf)
    return machine


@pytest.fixture
def sparse_zero_edge_machine() -> StateMachine:
    """A many-state graph that must remain sparse until dense output is requested."""
    names = tuple(f"isolated-{index}" for index in range(128))
    return StateMachine.from_states(*names, initial=names[0], name="zero-edge")


@pytest.fixture
def duplicate_name_machines() -> tuple[StateMachine, StateMachine, StateMachine]:
    """Same-label machines whose positional identities must remain distinct."""
    return tuple(StateMachine.from_states("only", name="duplicate") for _ in range(3))  # type: ignore[return-value]


@pytest.fixture
def barrier_controlled_mutation() -> tuple[StateMachine, threading.Barrier]:
    """Coordinate post-capture mutation without timing sleeps in later rows."""
    machine, _, _, _, _ = _moved_machine()
    return machine, threading.Barrier(2)


@pytest.fixture
def snapshot_call_counter(
    monkeypatch: pytest.MonkeyPatch,
) -> Callable[[], int]:
    """Install a reusable one-capture counter for later top-level callers."""
    original_snapshot = StateMachine._graph_snapshot
    calls = 0

    def count_snapshot(self: StateMachine):
        nonlocal calls
        calls += 1
        return original_snapshot(self)

    monkeypatch.setattr(StateMachine, "_graph_snapshot", count_snapshot)
    return lambda: calls


def _assert_exact_budget(
    machine_factory: Callable[[], StateMachine],
    action: Callable[[FSMValidator], object],
    count: Callable[[DiagnosticStatus], int],
    make_limits: Callable[[int], DiagnosticLimits],
    forbidden_operation: Callable[[DiagnosticStatus, int], bool],
) -> int:
    """Prove generous, exact, and one-less boundaries for one future budget row."""
    generous = FSMValidator(
        machine_factory(), limits=DiagnosticLimits(max_work=100_000)
    )
    action(generous)
    required = count(generous.diagnostic_status)
    assert required > 0

    exact = FSMValidator(machine_factory(), limits=make_limits(required))
    action(exact)
    assert count(exact.diagnostic_status) == required

    exhausted = FSMValidator(machine_factory(), limits=make_limits(required - 1))
    with pytest.raises(DiagnosticBudgetExceeded) as raised:
        action(exhausted)
    assert forbidden_operation(raised.value.status, required)
    return required


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

    assert (
        _assert_exact_budget(
            lambda: _moved_machine(label="caller-secret-machine")[0],
            lambda validator: validator.get_reachable_states(),
            lambda status: status.work_count,
            lambda limit: DiagnosticLimits(max_work=limit),
            lambda status, limit: status.work_count == limit - 1,
        )
        == required_work
    )


def test_package_root_exports_only_diagnostic_contract_types() -> None:
    import fast_fsm

    assert fast_fsm.DiagnosticLimits is DiagnosticLimits
    assert fast_fsm.DiagnosticStatus is DiagnosticStatus
    assert fast_fsm.DiagnosticBudgetExceeded is DiagnosticBudgetExceeded
    assert {
        "DiagnosticLimits",
        "DiagnosticStatus",
        "DiagnosticBudgetExceeded",
    } <= set(fast_fsm.__all__)
    assert {name for name in fast_fsm.__all__ if name.startswith("Diagnostic")} == {
        "DiagnosticLimits",
        "DiagnosticStatus",
        "DiagnosticBudgetExceeded",
    }


def test_validation_analysis_uses_only_captured_topology() -> None:
    """Validation may retain the machine for compatibility but never read its maps."""
    source = Path("src/fast_fsm/validation.py").read_text(encoding="utf-8")

    assert "fsm._states" not in source
    assert "fsm._transitions" not in source
    assert ".fsm._states" not in source
    assert ".fsm._transitions" not in source


def _hash_seed_payload(seed: str) -> dict[str, object]:
    source = """
import json
from fast_fsm import FSMValidator, StateMachine

machine = StateMachine.from_states("a", "b", "orphan", initial="a", name="seed")
machine.add_transition("go", "a", "b")
validator = FSMValidator(machine)
graph = validator._diagnostic_graph
reachable = sorted(validator.get_reachable_states())
print(json.dumps({
    "states": graph.state_names,
    "edges": [(edge.from_index, edge.trigger, edge.to_index) for edge in graph.edges],
    "reachable": reachable,
    "work": validator.diagnostic_status.work_count,
}))
"""
    environment = {**os.environ, "PYTHONHASHSEED": seed}
    completed = subprocess.run(
        [sys.executable, "-c", source],
        check=True,
        capture_output=True,
        env=environment,
        text=True,
    )
    return json.loads(completed.stdout)


def test_tracer_counts_and_order_are_hash_seed_stable() -> None:
    assert _hash_seed_payload("1") == _hash_seed_payload("2")


def test_scc_membership_includes_self_loops_components_and_excludes_tails(
    multi_scc_tail_machine: StateMachine,
    self_loop_machine: StateMachine,
    empty_machine: StateMachine,
) -> None:
    multi_graph = _graph_from_snapshot(multi_scc_tail_machine._graph_snapshot())
    self_graph = _graph_from_snapshot(self_loop_machine._graph_snapshot())
    empty_graph = _graph_from_snapshot(empty_machine._graph_snapshot())

    assert _strongly_connected_components(multi_graph, _DiagnosticBudget()) == (
        ("a", "b"),
        ("c", "d"),
    )
    assert _strongly_connected_components(self_graph, _DiagnosticBudget()) == (
        ("loop",),
    )
    assert _strongly_connected_components(empty_graph, _DiagnosticBudget()) == ()


def test_structural_depth_uses_an_iterative_condensation_dag(
    long_chain_machine: StateMachine,
    three_cycle_machine: StateMachine,
) -> None:
    chain = _graph_from_snapshot(long_chain_machine._graph_snapshot())
    cycle = _graph_from_snapshot(three_cycle_machine._graph_snapshot())

    assert _structural_depth(chain, _DiagnosticBudget()) == {
        "interpretation": "dag_longest_path",
        "depth": 1_099,
    }
    assert _structural_depth(cycle, _DiagnosticBudget()) == {
        "interpretation": "condensation_dag_depth",
        "depth": 0,
    }


def test_scc_work_boundary_is_exact_and_fails_before_the_next_visit(
    multi_scc_tail_machine: StateMachine,
) -> None:
    """SCC traversal consumes deterministic shared work before each action."""
    graph = _graph_from_snapshot(multi_scc_tail_machine._graph_snapshot())

    generous_budget = _DiagnosticBudget(DiagnosticLimits(max_work=10_000))
    _strongly_connected_components(graph, generous_budget)
    required_work = generous_budget.status.work_count

    exact_budget = _DiagnosticBudget(DiagnosticLimits(max_work=required_work))
    assert _strongly_connected_components(graph, exact_budget) == (
        ("a", "b"),
        ("c", "d"),
    )
    assert exact_budget.status.work_count == required_work

    exhausted_budget = _DiagnosticBudget(DiagnosticLimits(max_work=required_work - 1))
    with pytest.raises(DiagnosticBudgetExceeded) as raised:
        _strongly_connected_components(graph, exhausted_budget)

    assert raised.value.status.exhausted_dimension == "max_work"
    assert raised.value.status.work_count == required_work - 1
    assert raised.value.status.exhausted_stage in {
        "scc.forward.visit",
        "scc.forward.edge",
        "scc.reverse.visit",
        "scc.reverse.edge",
    }


def test_validator_cycle_adapter_returns_deterministic_closed_scc_paths(
    multi_scc_tail_machine: StateMachine,
    self_loop_machine: StateMachine,
) -> None:
    """The legacy path-shaped adapter is derived from canonical SCC membership."""
    assert FSMValidator(multi_scc_tail_machine).find_cycles() == [
        ["a", "b", "a"],
        ["c", "d", "c"],
    ]
    assert FSMValidator(self_loop_machine).find_cycles() == [["loop", "loop"]]


def test_sparse_dense_paths_and_result_budget_have_distinct_boundaries(
    sparse_zero_edge_machine: StateMachine,
    high_fanout_machine: StateMachine,
) -> None:
    sparse_graph = _graph_from_snapshot(sparse_zero_edge_machine._graph_snapshot())
    fanout_graph = _graph_from_snapshot(high_fanout_machine._graph_snapshot())
    assert _sparse_adjacency(sparse_graph, _DiagnosticBudget()) == {
        "states": sparse_graph.state_names,
        "events": (),
        "edges": (),
    }
    with pytest.raises(DiagnosticBudgetExceeded):
        _dense_adjacency(
            fanout_graph, _DiagnosticBudget(DiagnosticLimits(max_dense_cells=1))
        )
    with pytest.raises(DiagnosticBudgetExceeded):
        _generate_paths(
            fanout_graph,
            _DiagnosticBudget(DiagnosticLimits(max_path_expansions=1)),
        )
    with pytest.raises(DiagnosticBudgetExceeded):
        FSMValidator(
            high_fanout_machine, limits=DiagnosticLimits(max_results=1)
        ).generate_test_paths()


def test_dense_preflight_reserves_exact_cells_before_matrix_allocation(
    monkeypatch: pytest.MonkeyPatch,
    high_fanout_machine: StateMachine,
) -> None:
    """A one-less dense budget cannot reach the adjacency allocator."""
    graph = _graph_from_snapshot(high_fanout_machine._graph_snapshot())
    required_cells = len(graph.state_names) * len(graph.state_names)

    exact = _DiagnosticBudget(DiagnosticLimits(max_dense_cells=required_cells))
    adjacency = _dense_adjacency(graph, exact)
    assert adjacency["states"] == list(graph.state_names)
    assert exact.status.dense_cell_count == required_cells

    def fail_if_allocated(*args: object, **kwargs: object) -> object:
        raise AssertionError("dense allocation must follow successful preflight")

    monkeypatch.setattr(diagnostics, "_allocate_dense_matrix", fail_if_allocated)
    with pytest.raises(DiagnosticBudgetExceeded) as raised:
        _dense_adjacency(
            graph,
            _DiagnosticBudget(DiagnosticLimits(max_dense_cells=required_cells - 1)),
        )

    assert raised.value.status.exhausted_dimension == "max_dense_cells"
    assert raised.value.status.exhausted_stage == "dense.adjacency.preflight"


def test_transition_matrix_preflight_uses_state_event_cells(
    high_fanout_machine: StateMachine,
) -> None:
    """The legacy transition matrix charges V times ordered event count."""
    graph = _graph_from_snapshot(high_fanout_machine._graph_snapshot())
    required_cells = len(graph.state_names) * len(
        {edge.trigger for edge in graph.edges}
    )

    exact = _DiagnosticBudget(DiagnosticLimits(max_dense_cells=required_cells))
    transition_matrix = _dense_adjacency(graph, exact, representation="transition")
    assert transition_matrix["root"]["to-leaf-0"] == ["leaf-0"]
    assert exact.status.dense_cell_count == required_cells

    with pytest.raises(DiagnosticBudgetExceeded) as raised:
        _dense_adjacency(
            graph,
            _DiagnosticBudget(DiagnosticLimits(max_dense_cells=required_cells - 1)),
            representation="transition",
        )

    assert raised.value.status.exhausted_stage == "dense.transition.preflight"


def test_iterative_paths_distinguish_length_result_and_expansion_limits(
    high_fanout_machine: StateMachine,
) -> None:
    """Path caps are explicit, deterministic, and fail closed on exhaustion."""
    graph = _graph_from_snapshot(high_fanout_machine._graph_snapshot())
    edge_count = len(graph.edges)

    assert (
        _generate_paths(
            graph,
            _DiagnosticBudget(),
            max_length=0,
            max_paths=edge_count,
        )
        == ()
    )

    exact_expansions = _DiagnosticBudget(
        DiagnosticLimits(max_path_expansions=edge_count, max_results=edge_count)
    )
    paths = _generate_paths(
        graph,
        exact_expansions,
        max_length=1,
        max_paths=edge_count,
    )
    assert len(paths) == edge_count
    assert exact_expansions.status.path_expansion_count == edge_count
    assert exact_expansions.status.result_count == edge_count

    with pytest.raises(DiagnosticBudgetExceeded) as expansion_raised:
        _generate_paths(
            graph,
            _DiagnosticBudget(DiagnosticLimits(max_path_expansions=edge_count - 1)),
            max_length=1,
            max_paths=edge_count,
        )
    assert expansion_raised.value.status.exhausted_dimension == "max_path_expansions"
    assert expansion_raised.value.status.exhausted_stage == "path.expand"

    with pytest.raises(DiagnosticBudgetExceeded) as result_raised:
        _generate_paths(
            graph,
            _DiagnosticBudget(DiagnosticLimits(max_results=edge_count - 1)),
            max_length=1,
            max_paths=edge_count,
        )
    assert result_raised.value.status.exhausted_dimension == "max_results"
    assert result_raised.value.status.exhausted_stage == "path.result"


def test_diagnostic_defaults_are_finite_and_pinned() -> None:
    """Default ceilings are explicit calibrated constants, never wall-clock state."""
    assert DiagnosticLimits() == DiagnosticLimits(
        max_work=50_000,
        max_results=10_000,
        max_dense_cells=200_000,
        max_path_expansions=20_000,
    )


def test_comparison_and_batch_preserve_duplicate_positional_identity(
    duplicate_name_machines: tuple[StateMachine, StateMachine, StateMachine],
) -> None:
    comparison = compare_fsms(*duplicate_name_machines)
    batch = batch_validate(*duplicate_name_machines, show_summary=False)
    assert [entry["position"] for entry in comparison["entries"]] == [0, 1, 2]
    assert [entry["name"] for entry in comparison["entries"]] == [
        "duplicate",
        "duplicate",
        "duplicate",
    ]
    assert [(entry["position"], entry["name"]) for entry in comparison["rankings"]] == [
        (0, "duplicate"),
        (1, "duplicate"),
        (2, "duplicate"),
    ]
    assert len({entry["score"] for entry in comparison["rankings"]}) == 1
    assert comparison["best_fsm"] == {"position": 0, "name": "duplicate"}
    assert all(entry["diagnostic_status"].complete for entry in comparison["entries"])
    assert batch["count"] == 3
    assert [entry["position"] for entry in batch["entries"]] == [0, 1, 2]
    assert [entry["name"] for entry in batch["entries"]] == [
        "duplicate",
        "duplicate",
        "duplicate",
    ]
    assert all(
        entry["validator"].diagnostic_status.complete for entry in batch["entries"]
    )


def test_empty_comparison_returns_exact_structured_undefined_aggregates() -> None:
    empty = compare_fsms()
    assert empty == {
        "entries": [],
        "rankings": [],
        "best_fsm": None,
        "comparison_metrics": {
            "count": 0,
            "total_issues": 0,
            "avg_score": None,
            "score_range": None,
            "diagnostic_status": DiagnosticStatus(
                complete=True,
                exhausted_dimension=None,
                exhausted_stage=None,
                work_count=0,
                result_count=0,
                dense_cell_count=0,
                path_expansion_count=0,
            ),
        },
    }


def test_comparison_captures_each_input_once(
    duplicate_name_machines: tuple[StateMachine, StateMachine, StateMachine],
    snapshot_call_counter: Callable[[], int],
) -> None:
    comparison = compare_fsms(*duplicate_name_machines)

    assert snapshot_call_counter() == 3
    assert [entry["position"] for entry in comparison["entries"]] == [0, 1, 2]


def test_structured_report_has_complete_snapshot_analysis_metadata(
    multi_scc_tail_machine: StateMachine,
) -> None:
    report = FSMValidator(multi_scc_tail_machine).validate_completeness()

    assert report["initial_state"] == "a"
    assert report["current_state"] == "a"
    assert report["cyclic_components"] == (("a", "b"), ("c", "d"))
    assert report["states_in_cycles"] == ("a", "b", "c", "d")
    assert report["structural_depth"] == 2
    assert report["depth_interpretation"] == "condensation_dag_depth"
    assert report["sparse_adjacency"]["states"] == ("a", "b", "c", "d", "tail")
    assert report["diagnostic_status"].complete is True


def test_report_uses_one_aggregate_budget_without_nested_resets() -> None:
    def make_machine() -> StateMachine:
        return StateMachine.quick_build(
            "a",
            [("ab", "a", "b"), ("ba", "b", "a"), ("tail", "b", "tail")],
            name="aggregate-budget",
        )

    generous = FSMValidator(make_machine(), limits=DiagnosticLimits(max_work=100_000))
    generous_report = generous.validate_completeness()
    required = generous_report["diagnostic_status"].work_count
    assert required > 0

    exact = FSMValidator(make_machine(), limits=DiagnosticLimits(max_work=required))
    assert exact.validate_completeness()["diagnostic_status"].work_count == required

    exhausted = FSMValidator(
        make_machine(), limits=DiagnosticLimits(max_work=required - 1)
    )
    with pytest.raises(DiagnosticBudgetExceeded) as raised:
        exhausted.validate_completeness()
    assert raised.value.status.work_count == required - 1
    assert raised.value.status.exhausted_stage is not None


def test_validate_and_score_captures_once_and_carries_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    machine, _, _, _, _ = _moved_machine()
    original_snapshot = StateMachine._graph_snapshot
    calls = 0

    def count_snapshot(self: StateMachine):
        nonlocal calls
        calls += 1
        return original_snapshot(self)

    monkeypatch.setattr(StateMachine, "_graph_snapshot", count_snapshot)
    result = validate_and_score(machine)

    assert calls == 1
    assert result["diagnostic_status"].complete is True


@pytest.mark.xfail(strict=True, reason="RED until 19-06")
def test_json_captures_one_snapshot_and_never_rereads_live_topology(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    machine, _, _, _, _ = _moved_machine()
    original_snapshot = StateMachine._graph_snapshot
    calls = 0

    def count_snapshot(self: StateMachine):
        nonlocal calls
        calls += 1
        return original_snapshot(self)

    monkeypatch.setattr(StateMachine, "_graph_snapshot", count_snapshot)
    payload = to_json(machine)
    assert calls == 1
    assert payload["analysis"]["status"].complete is True
