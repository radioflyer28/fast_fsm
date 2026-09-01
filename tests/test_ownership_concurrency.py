"""Deterministic Wave 0 contracts for per-machine ownership admission."""

import threading

import pytest

from fast_fsm.core import CallbackState, State, StateMachine


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


def test_sync_thread_tracer_serializes_one_machine_without_global_lock() -> None:
    """One machine blocks a competing writer while another remains independent."""
    first_entered = threading.Event()
    release_first = threading.Event()
    second_finished = threading.Event()
    other_finished = threading.Event()
    start_first = threading.Barrier(2)
    results: list[bool] = []

    def before_transition(
        _from_state: State, _to_state: State, trigger: str, **_kwargs: object
    ) -> None:
        if trigger == "first":
            first_entered.set()
            assert release_first.wait(timeout=5)

    source = State("source")
    destination = State("destination")
    machine = StateMachine(source, name="owned-machine")
    machine.add_state(destination)
    machine.add_transition("first", "source", "destination")
    machine.add_transition("second", "source", "destination")
    machine.before_transition(before_transition)

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
    assert machine.current_state is destination
    assert other_machine.current_state is other_destination
