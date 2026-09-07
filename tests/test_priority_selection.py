"""Focused synchronous selection contracts for priority candidate groups."""

from __future__ import annotations


from fast_fsm.conditions import Condition
from fast_fsm.core import DeclarativeState, State, StateMachine, transition


class _RecordingCondition(Condition):
    """Guard that records its evaluation without mocking the dispatch path."""

    __slots__ = ("_events", "_label", "_outcome", "_payloads")

    def __init__(
        self,
        events: list[str],
        label: str,
        outcome: bool | BaseException,
        payloads: list[tuple[tuple[object, ...], dict[str, object]]],
    ) -> None:
        super().__init__(label, "priority selection test guard")
        self._events = events
        self._label = label
        self._outcome = outcome
        self._payloads = payloads

    def check(self, *args: object, **kwargs: object) -> bool:
        self._events.append(self._label)
        self._payloads.append((args, dict(kwargs)))
        if isinstance(self._outcome, BaseException):
            raise self._outcome
        return self._outcome


def test_sync_group_selects_the_first_fully_eligible_candidate_before_lifecycle() -> (
    None
):
    """Priority selection retains the exact target handler and caller payload."""
    events: list[str] = []
    guard_payloads: list[tuple[tuple[object, ...], dict[str, object]]] = []
    handler_payloads: list[tuple[tuple[object, ...], dict[str, object]]] = []

    def declarative_guard(*args: object, **kwargs: object) -> bool:
        events.append("declarative-guard")
        assert args == ("telemetry",)
        assert kwargs == {"priority": "caller-payload", "battery": 41}
        return True

    class Source(DeclarativeState):
        __slots__ = ("_events",)

        def __init__(self) -> None:
            self._events = events
            super().__init__("source")

        def can_transition(
            self, trigger_name: str, to_state: State, *args: object, **kwargs: object
        ) -> bool:
            self._events.append("permission")
            assert trigger_name == "go"
            assert to_state.name == "winner"
            assert args == ("telemetry",)
            assert kwargs == {"priority": "caller-payload", "battery": 41}
            return super().can_transition(trigger_name, to_state, *args, **kwargs)

        def on_exit(
            self, to_state: State, trigger_name: str, *args: object, **kwargs: object
        ) -> None:
            self._events.append("source-exit")

        @transition("go", to_state="winner", condition=declarative_guard)
        def go(self, *args: object, **kwargs: object) -> None:
            events.append("handler")
            handler_payloads.append((args, dict(kwargs)))

    source = Source()
    rejected = State("rejected")
    winner = State("winner")
    later = State("later")
    machine = StateMachine(source, name="priority-sync-winner")
    for state in (rejected, winner, later):
        machine.add_state(state)
    machine.enable_history()

    class Listener:
        def before_transition(self, *_args: object, **_kwargs: object) -> None:
            events.append("before-transition")

    machine.add_listener(Listener())
    machine.on_trigger("go", lambda *_args, **_kwargs: events.append("trigger"))
    machine.after_transition(
        lambda *_args, **_kwargs: events.append("after-transition")
    )

    # Register out of precedence order.  The negative candidate rejects; the
    # zero candidate wins; the positive candidate must never be inspected.
    machine.add_transition(
        "go",
        source,
        later,
        _RecordingCondition(events, "guard-later", True, guard_payloads),
        priority=9,
    )
    machine.add_transition(
        "go",
        source,
        winner,
        _RecordingCondition(events, "guard-winner", True, guard_payloads),
        priority=0,
    )
    machine.add_transition(
        "go",
        source,
        rejected,
        _RecordingCondition(events, "guard-rejected", False, guard_payloads),
        priority=-5,
    )

    result = machine.trigger("go", "telemetry", priority="caller-payload", battery=41)

    assert result.success is True
    assert result.from_state == "source"
    assert result.to_state == "winner"
    assert machine.current_state is winner
    assert [
        (record.from_state, record.trigger, record.to_state)
        for record in machine.history
    ] == [("source", "go", "winner")]
    assert events == [
        "guard-rejected",
        "guard-winner",
        "declarative-guard",
        "permission",
        "before-transition",
        "source-exit",
        "handler",
        "trigger",
        "after-transition",
    ]
    assert guard_payloads == [
        (("telemetry",), {"priority": "caller-payload", "battery": 41}),
        (("telemetry",), {"priority": "caller-payload", "battery": 41}),
    ]
    assert handler_payloads == [
        (("telemetry",), {"priority": "caller-payload", "battery": 41})
    ]
