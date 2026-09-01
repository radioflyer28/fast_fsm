"""Deterministic Wave 0 contracts for per-machine ownership admission."""

from dataclasses import dataclass
import threading

import pytest

from fast_fsm.core import CallbackState, State, StateMachine


@dataclass(frozen=True)
class OwnershipContractCase:
    """One requirement/probe row and the plan that turns it green."""

    identifier: str
    requirement: str
    owner_plan: str
    scenario: str


OWNERSHIP_CONTRACT_CASES = (
    OwnershipContractCase("SYNC-TRACER", "OWN-01", "18-01", "sync trigger"),
    OwnershipContractCase(
        "OWN-01-direct-reentry", "OWN-01", "18-02", "all sync trigger stages"
    ),
    OwnershipContractCase(
        "OWN-02-full-envelope", "OWN-02", "18-02", "finalizer-held contention"
    ),
    OwnershipContractCase(
        "OWN-03-same-loop", "OWN-03", "18-03", "non-blocking task contention"
    ),
    OwnershipContractCase(
        "OWN-04-loop-binding", "OWN-04", "18-03", "permanent loop identity"
    ),
    OwnershipContractCase(
        "OWN-05-topology-history", "OWN-05", "18-04", "owned graph/history writes"
    ),
    OwnershipContractCase(
        "OWN-05-registrars", "OWN-05", "18-04", "owned callback registrars"
    ),
    OwnershipContractCase(
        "OWN-06-sync-release", "OWN-06", "18-02", "control/BaseException reuse"
    ),
    OwnershipContractCase(
        "OWN-06-async-cancellation", "OWN-06", "18-03", "waiter/owner cancellation"
    ),
    OwnershipContractCase(
        "OWN-07-inline-callback", "OWN-07", "18-03", "same-loop callback slots"
    ),
    OwnershipContractCase(
        "SAFE-TRIGGER", "OWN-01", "18-05", "admission outside conversion"
    ),
    OwnershipContractCase(
        "DECLARATIVE-MARKER", "OWN-05", "18-05", "context-local machine marker"
    ),
)

FALLBACK_PROBE_ROWS = (
    ("probe-1", "OWN-01", "18-02", "direct/callback same-owner admission"),
    ("probe-2", "OWN-02", "18-02", "two-thread serialization"),
    ("probe-3", "OWN-03", "18-03", "same-loop task contention"),
    ("probe-4", "OWN-04", "18-03", "foreign/closed-loop rejection"),
    ("probe-5", "OWN-05", "18-04", "full public writer inventory"),
    ("probe-6", "OWN-06", "18-03", "throwable/cancellation reuse"),
    ("probe-7", "OWN-06", "none", "numeric precision is irrelevant"),
    ("probe-8", "OWN-07", "18-03", "inline callback/no-offload"),
)


def test_contract_inventory_accounts_for_every_requirement_and_probe() -> None:
    """Wave 0 has no hidden ownership scenario or unassigned RED row."""
    assert {case.requirement for case in OWNERSHIP_CONTRACT_CASES} == {
        "OWN-01",
        "OWN-02",
        "OWN-03",
        "OWN-04",
        "OWN-05",
        "OWN-06",
        "OWN-07",
    }
    assert [row[0] for row in FALLBACK_PROBE_ROWS] == [
        "probe-1",
        "probe-2",
        "probe-3",
        "probe-4",
        "probe-5",
        "probe-6",
        "probe-7",
        "probe-8",
    ]
    assert {case.owner_plan for case in OWNERSHIP_CONTRACT_CASES} == {
        "18-01",
        "18-02",
        "18-03",
        "18-04",
        "18-05",
    }
    assert FALLBACK_PROBE_ROWS[6][2] == "none"


@pytest.mark.xfail(strict=True, reason="RED until Plan 18-02")
def test_strict_red_sync_control_requires_private_owned_body() -> None:
    """Plan 18-02 must prevent control callbacks from reentering public writes."""
    source = State("source")
    destination = State("destination")
    machine = StateMachine(source)
    machine.add_state(destination)
    machine.add_transition("advance", "source", "destination")

    def reenter(*_args: object, **_kwargs: object) -> None:
        machine.force_state("source")

    machine.on_exit("source", reenter)
    result = machine.trigger("advance")
    assert result.success is False
    assert result.stage == "source-exit-callback"
    assert machine.current_state is source


@pytest.mark.xfail(strict=True, reason="RED until Plan 18-03")
def test_strict_red_async_ownership_representation_is_present() -> None:
    """Plan 18-03 owns loop/task/root state and its async admission seam."""
    from pathlib import Path

    source = (Path(__file__).parent.parent / "src" / "fast_fsm" / "core.py").read_text()
    assert "_async_ownership_lock" in source
    assert "_acquire_async_ownership" in source
    assert "_ownership_root" in source


@pytest.mark.xfail(strict=True, reason="RED until Plan 18-04")
def test_strict_red_all_public_writer_entries_are_owned() -> None:
    """Plan 18-04 upgrades the Wave 0 name list to one-entry enforcement."""
    from pathlib import Path

    source = (Path(__file__).parent.parent / "src" / "fast_fsm" / "core.py").read_text()
    for method in (
        "add_state",
        "add_transition",
        "enable_history",
        "add_listener",
        "on_trigger",
    ):
        start = source.index(f"    def {method}(")
        body = source[start : start + 800]
        assert "_acquire_sync_ownership" in body


@pytest.mark.xfail(strict=True, reason="RED until Plan 18-05")
def test_strict_red_safe_trigger_keeps_ownership_errors_outside_conversion() -> None:
    """Plan 18-05 makes a nested safe trigger raise instead of return a result."""
    machine: StateMachine

    def on_exit(*_args: object, **_kwargs: object) -> None:
        with pytest.raises(RuntimeError, match="reentrant trigger"):
            machine.safe_trigger("nested", payload="safe-secret")

    source = CallbackState("source", on_exit=on_exit)
    destination = State("destination")
    alternate = State("alternate")
    machine = StateMachine(source)
    machine.add_state(destination)
    machine.add_state(alternate)
    machine.add_transition("outer", "source", "destination")
    machine.add_transition("nested", "source", "alternate")

    assert machine.trigger("outer").success is True


@pytest.mark.xfail(strict=True, reason="RED until Plan 18-05")
def test_strict_red_declarative_marker_is_context_local_and_machine_qualified() -> None:
    """Plan 18-05 replaces the shared marker registry with a ContextVar token."""
    from pathlib import Path

    source = (Path(__file__).parent.parent / "src" / "fast_fsm" / "core.py").read_text()
    assert "_prepared_declarative_guards" not in source
    assert "ContextVar" in source
    assert "_prepared_declarative_guard" in source


def test_sync_reentrant_callback_is_rejected_before_nested_preparation() -> None:
    """A caught nested trigger cannot prepare or commit inside its owner."""
    observed: list[str] = []
    nested_once = True
    machine: StateMachine

    def on_exit(*_args: object, **_kwargs: object) -> None:
        nonlocal nested_once
        observed.append("outer-exit")
        if nested_once:
            nested_once = False
            with pytest.raises(
                RuntimeError, match=r"^FSM ownership violation: reentrant trigger$"
            ):
                machine.trigger("nested", payload="callback-secret")
            observed.append("nested-rejected")

    source = CallbackState("source", on_exit=on_exit)
    destination = State("destination")
    alternate = State("alternate")
    machine = StateMachine(source, name="ownership-tracer")
    machine.add_state(destination)
    machine.add_state(alternate)
    machine.add_transition("outer", "source", "destination")
    machine.add_transition("nested", "source", "alternate")

    result = machine.trigger("outer", payload="caller-secret")

    assert result.success is True
    assert machine.current_state is destination
    assert observed == ["outer-exit", "nested-rejected"]


def test_sync_uncaught_reentry_uses_existing_source_exit_failure_stage() -> None:
    """An uncaught admission failure follows the normal Phase 17 callback path."""
    nested_once = True
    machine: StateMachine

    def on_exit(*_args: object, **_kwargs: object) -> None:
        nonlocal nested_once
        if nested_once:
            nested_once = False
            machine.trigger("nested", payload="callback-secret")

    source = CallbackState("source", on_exit=on_exit)
    destination = State("destination")
    alternate = State("alternate")
    machine = StateMachine(source, name="ownership-uncaught")
    machine.add_state(destination)
    machine.add_state(alternate)
    machine.add_transition("outer", "source", "destination")
    machine.add_transition("nested", "source", "alternate")

    result = machine.trigger("outer", payload="caller-secret")

    assert result.success is False
    assert result.stage == "source-exit"
    assert result.committed is False
    assert machine.current_state is source
    assert result.cause is not None
    assert "callback-secret" not in result.error
    assert "callback-secret" not in str(result.cause)


@pytest.mark.parametrize("failure_type", (RuntimeError, KeyboardInterrupt, SystemExit))
def test_sync_release_tracer_reuses_machine_after_every_throwable(
    failure_type: type[BaseException],
) -> None:
    """The ownership envelope releases after result failures and BaseException."""
    raise_once = True

    def on_exit(*_args: object, **_kwargs: object) -> None:
        nonlocal raise_once
        if raise_once:
            raise_once = False
            raise failure_type("release-sentinel")

    source = CallbackState("source", on_exit=on_exit)
    destination = State("destination")
    machine = StateMachine(source, name="ownership-release")
    machine.add_state(destination)
    machine.add_transition("advance", "source", "destination")

    if issubclass(failure_type, Exception):
        result = machine.trigger("advance")
        assert result.success is False
        assert result.stage == "source-exit"
        assert machine.current_state is source
    else:
        with pytest.raises(failure_type, match="release-sentinel"):
            machine.trigger("advance")
        assert machine.current_state is source

    retry = machine.trigger("advance")
    assert retry.success is True
    assert machine.current_state is destination


def test_sync_thread_tracer_serializes_one_machine_without_global_lock() -> None:
    """One machine blocks a competing writer while another remains independent."""
    first_entered = threading.Event()
    release_first = threading.Event()
    second_finished = threading.Event()
    other_finished = threading.Event()
    start_first = threading.Barrier(2)
    results: list[bool] = []

    class BlockingListener:
        def before_transition(
            self, _from_state: State, _to_state: State, trigger: str, **_kwargs: object
        ) -> None:
            if trigger == "first":
                first_entered.set()
                assert release_first.wait(timeout=5)

    source = State("source")
    destination = State("destination")
    machine = StateMachine(source, name="owned-machine")
    machine.add_state(destination)
    machine.add_transition("first", "source", "destination")
    machine.add_transition("second", "destination", "source")
    machine.add_listener(BlockingListener())

    other_source = State("source")
    other_destination = State("destination")
    other_machine = StateMachine(other_source, name="independent-machine")
    other_machine.add_state(other_destination)
    other_machine.add_transition("other", "source", "destination")

    def run_first() -> None:
        start_first.wait(timeout=5)
        results.append(machine.trigger("first").success)

    def run_second() -> None:
        assert first_entered.wait(timeout=5)
        results.append(machine.trigger("second").success)
        second_finished.set()

    def run_other() -> None:
        results.append(other_machine.trigger("other").success)
        other_finished.set()

    first = threading.Thread(target=run_first)
    second = threading.Thread(target=run_second)
    other = threading.Thread(target=run_other)
    first.start()
    start_first.wait(timeout=5)
    assert first_entered.wait(timeout=5)
    second.start()
    other.start()

    assert other_finished.wait(timeout=5)
    assert not second_finished.wait(timeout=0.05)
    release_first.set()
    first.join(timeout=5)
    second.join(timeout=5)
    other.join(timeout=5)

    assert not first.is_alive()
    assert not second.is_alive()
    assert not other.is_alive()
    assert results == [True, True, True]
    assert machine.current_state is source
    assert other_machine.current_state is other_destination
