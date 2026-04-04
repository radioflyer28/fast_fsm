"""
Tests for the StateMachine listener / observer pattern.

Covers: add_listener(), on_exit_state, on_enter_state, after_transition,
multiple listeners, partial implementations, error isolation,
AsyncStateMachine integration, and real-world patterns.

All tests use real FSM components — no mocking.
"""

from fast_fsm.core import AsyncStateMachine, State, StateMachine


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_fsm():
    """Simple 2-state FSM: idle -[start]-> running -[stop]-> idle."""
    fsm = StateMachine.quick_build(
        "idle",
        [("start", "idle", "running"), ("stop", "running", "idle")],
        name="Test",
    )
    return fsm


class _Recorder:
    """Full-protocol listener that records all calls."""

    def __init__(self):
        self.exits = []  # (source.name, target.name, trigger)
        self.enters = []  # (target.name, source.name, trigger)
        self.afters = []  # (source.name, target.name, trigger)

    def on_exit_state(self, source, target, trigger, **kwargs):
        self.exits.append((source.name, target.name, trigger))

    def on_enter_state(self, target, source, trigger, **kwargs):
        self.enters.append((target.name, source.name, trigger))

    def after_transition(self, source, target, trigger, **kwargs):
        self.afters.append((source.name, target.name, trigger))


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


class TestListenerRegistration:
    def test_register_single_listener(self):
        fsm = _make_fsm()
        rec = _Recorder()
        fsm.add_listener(rec)
        fsm.trigger("start")
        assert len(rec.afters) == 1

    def test_register_multiple_listeners_at_once(self):
        fsm = _make_fsm()
        rec1, rec2 = _Recorder(), _Recorder()
        fsm.add_listener(rec1, rec2)
        fsm.trigger("start")
        assert len(rec1.afters) == 1
        assert len(rec2.afters) == 1

    def test_register_multiple_calls(self):
        fsm = _make_fsm()
        rec1, rec2 = _Recorder(), _Recorder()
        fsm.add_listener(rec1)
        fsm.add_listener(rec2)
        fsm.trigger("start")
        assert len(rec1.afters) == 1
        assert len(rec2.afters) == 1

    def test_silent_skip_no_protocol_methods(self):
        """Objects without any protocol methods register without error."""
        fsm = _make_fsm()
        fsm.add_listener(object())  # has none of the protocol methods
        fsm.trigger("start")  # should not raise

    def test_partial_listener_only_after(self):
        """Listener with only after_transition is valid."""
        fsm = _make_fsm()
        log = []

        class AfterOnly:
            def after_transition(self, source, target, trigger, **kwargs):
                log.append(trigger)

        fsm.add_listener(AfterOnly())
        fsm.trigger("start")
        assert log == ["start"]

    def test_partial_listener_only_on_exit(self):
        fsm = _make_fsm()
        log = []

        class ExitOnly:
            def on_exit_state(self, source, target, trigger, **kwargs):
                log.append(source.name)

        fsm.add_listener(ExitOnly())
        fsm.trigger("start")
        assert log == ["idle"]


# ---------------------------------------------------------------------------
# on_exit_state
# ---------------------------------------------------------------------------


class TestOnExitStateListener:
    def test_called_after_exit_callback(self):
        """on_exit_state fires after the state's own on_exit."""
        order = []

        from fast_fsm.core import CallbackState

        idle = CallbackState(
            "idle", on_exit=lambda *a, **kw: order.append("state_exit")
        )
        running = State("running")
        fsm = StateMachine(idle, name="t")
        fsm.add_state(running)
        fsm.add_transition("start", "idle", "running")

        class L:
            def on_exit_state(self, source, target, trigger, **kwargs):
                order.append("listener_exit")

        fsm.add_listener(L())
        fsm.trigger("start")
        assert order == ["state_exit", "listener_exit"]

    def test_receives_correct_args(self):
        fsm = _make_fsm()
        rec = _Recorder()
        fsm.add_listener(rec)
        fsm.trigger("start")
        assert rec.exits == [("idle", "running", "start")]

    def test_not_called_on_blocked_transition(self):
        fsm = _make_fsm()
        rec = _Recorder()
        fsm.add_listener(rec)
        fsm.trigger("stop")  # blocked — already idle, no "stop" from idle
        assert rec.exits == []

    def test_source_is_state_object(self):
        """Confirm source/target are State objects, not strings."""
        fsm = _make_fsm()
        captured = []

        class L:
            def on_exit_state(self, source, target, trigger, **kwargs):
                captured.append((type(source).__name__, type(target).__name__))

        fsm.add_listener(L())
        fsm.trigger("start")
        assert captured == [("State", "State")]


# ---------------------------------------------------------------------------
# on_enter_state
# ---------------------------------------------------------------------------


class TestOnEnterStateListener:
    def test_called_after_enter_callback(self):
        """on_enter_state fires after the state's own on_enter."""
        order = []

        from fast_fsm.core import CallbackState

        idle = State("idle")
        running = CallbackState(
            "running", on_enter=lambda *a, **kw: order.append("state_enter")
        )
        fsm = StateMachine(idle, name="t")
        fsm.add_state(running)
        fsm.add_transition("start", "idle", "running")

        class L:
            def on_enter_state(self, target, source, trigger, **kwargs):
                order.append("listener_enter")

        fsm.add_listener(L())
        fsm.trigger("start")
        assert order == ["state_enter", "listener_enter"]

    def test_receives_correct_args(self):
        fsm = _make_fsm()
        rec = _Recorder()
        fsm.add_listener(rec)
        fsm.trigger("start")
        # enters: (target, source, trigger) — note swapped order vs exits
        assert rec.enters == [("running", "idle", "start")]

    def test_not_called_on_blocked_transition(self):
        fsm = _make_fsm()
        rec = _Recorder()
        fsm.add_listener(rec)
        fsm.trigger("stop")
        assert rec.enters == []


# ---------------------------------------------------------------------------
# after_transition
# ---------------------------------------------------------------------------


class TestAfterTransitionListener:
    def test_called_once_per_successful_trigger(self):
        fsm = _make_fsm()
        rec = _Recorder()
        fsm.add_listener(rec)
        fsm.trigger("start")
        fsm.trigger("stop")
        assert len(rec.afters) == 2

    def test_receives_correct_args(self):
        fsm = _make_fsm()
        rec = _Recorder()
        fsm.add_listener(rec)
        fsm.trigger("start")
        assert rec.afters == [("idle", "running", "start")]

    def test_not_called_on_failed_trigger(self):
        fsm = _make_fsm()
        rec = _Recorder()
        fsm.add_listener(rec)
        fsm.trigger("stop")  # no "stop" from "idle"
        assert rec.afters == []

    def test_kwargs_forwarded(self):
        """kwargs from trigger() reach the listener."""
        fsm = _make_fsm()
        received = {}

        class L:
            def after_transition(self, source, target, trigger, **kwargs):
                received.update(kwargs)

        fsm.add_listener(L())
        fsm.trigger("start", order_id="ORD-42")
        assert received.get("order_id") == "ORD-42"

    def test_called_after_both_exit_and_enter(self):
        """after_transition is the last listener hook."""
        order = []

        class L:
            def on_exit_state(self, *a, **kw):
                order.append("exit")

            def on_enter_state(self, *a, **kw):
                order.append("enter")

            def after_transition(self, *a, **kw):
                order.append("after")

        fsm = _make_fsm()
        fsm.add_listener(L())
        fsm.trigger("start")
        assert order == ["exit", "enter", "after"]


# ---------------------------------------------------------------------------
# Multiple listeners — ordering
# ---------------------------------------------------------------------------


class TestListenerOrdering:
    def test_called_in_registration_order(self):
        fsm = _make_fsm()
        order = []
        for i in range(3):
            idx = i  # capture

            class L:
                def __init__(self, n):
                    self.n = n

                def after_transition(self, *a, **kw):
                    order.append(self.n)

            fsm.add_listener(L(idx))
        fsm.trigger("start")
        assert order == [0, 1, 2]

    def test_all_listeners_called_independently(self):
        fsm = _make_fsm()
        rec1, rec2, rec3 = _Recorder(), _Recorder(), _Recorder()
        fsm.add_listener(rec1, rec2, rec3)
        fsm.trigger("start")
        fsm.trigger("stop")
        for rec in (rec1, rec2, rec3):
            assert len(rec.afters) == 2


# ---------------------------------------------------------------------------
# Error isolation
# ---------------------------------------------------------------------------


class TestListenerErrorIsolation:
    def test_crashing_listener_does_not_crash_fsm(self):
        fsm = _make_fsm()

        class BrokenListener:
            def after_transition(self, *a, **kw):
                raise RuntimeError("boom")

        fsm.add_listener(BrokenListener())
        result = fsm.trigger("start")
        assert result.success
        assert fsm.is_in("running")

    def test_subsequent_listeners_called_after_crash(self):
        fsm = _make_fsm()
        log = []

        class BrokenFirst:
            def after_transition(self, *a, **kw):
                raise RuntimeError("first breaks")

        class GoodSecond:
            def after_transition(self, *a, **kw):
                log.append("second")

        fsm.add_listener(BrokenFirst(), GoodSecond())
        fsm.trigger("start")
        assert log == ["second"]

    def test_crash_in_on_exit_does_not_block_enter(self):
        fsm = _make_fsm()
        log = []

        class ExitCrash:
            def on_exit_state(self, *a, **kw):
                raise RuntimeError("exit crash")

            def on_enter_state(self, *a, **kw):
                log.append("entered")

        fsm.add_listener(ExitCrash())
        fsm.trigger("start")
        assert log == ["entered"]


# ---------------------------------------------------------------------------
# Zero-overhead when no listeners
# ---------------------------------------------------------------------------


class TestNoListenerOverhead:
    def test_fsm_without_listeners_still_works(self):
        fsm = _make_fsm()
        result = fsm.trigger("start")
        assert result.success

    def test_listener_lists_empty_initially(self):
        fsm = _make_fsm()
        assert fsm._on_exit_listeners == []
        assert fsm._on_enter_listeners == []
        assert fsm._after_listeners == []


# ---------------------------------------------------------------------------
# AsyncStateMachine integration
# ---------------------------------------------------------------------------


class TestAsyncListeners:
    async def test_listeners_inherited_by_async_state_machine(self):
        idle = State("idle")
        running = State("running")
        fsm = AsyncStateMachine(idle, name="AsyncTest")
        fsm.add_state(running)
        fsm.add_transition("start", "idle", "running")

        rec = _Recorder()
        fsm.add_listener(rec)

        await fsm.trigger_async("start")
        assert rec.afters == [("idle", "running", "start")]
        assert rec.exits == [("idle", "running", "start")]
        assert rec.enters == [("running", "idle", "start")]

    async def test_async_kwargs_forwarded(self):
        idle = State("idle")
        running = State("running")
        fsm = AsyncStateMachine(idle, name="AsyncKwarg")
        fsm.add_state(running)
        fsm.add_transition("start", "idle", "running")

        received = {}

        class L:
            def after_transition(self, source, target, trigger, **kwargs):
                received.update(kwargs)

        fsm.add_listener(L())
        await fsm.trigger_async("start", token="xyz")
        assert received.get("token") == "xyz"


# ---------------------------------------------------------------------------
# Real-world pattern: transition history as a listener
# ---------------------------------------------------------------------------


class TestTransitionHistoryPattern:
    def test_history_listener_records_all_transitions(self):
        class HistoryListener:
            def __init__(self):
                self.history = []

            def after_transition(self, source, target, trigger, **kwargs):
                self.history.append((source.name, trigger, target.name))

        fsm = StateMachine.quick_build(
            "a",
            [("go", "a", "b"), ("go", "b", "c"), ("go", "c", "a")],
            name="Cyclic",
        )
        hist = HistoryListener()
        fsm.add_listener(hist)
        fsm.trigger("go")
        fsm.trigger("go")
        fsm.trigger("go")

        assert hist.history == [
            ("a", "go", "b"),
            ("b", "go", "c"),
            ("c", "go", "a"),
        ]

    def test_metrics_listener_counts_by_trigger(self):
        class MetricsListener:
            def __init__(self):
                self.counts = {}

            def after_transition(self, source, target, trigger, **kwargs):
                self.counts[trigger] = self.counts.get(trigger, 0) + 1

        fsm = _make_fsm()
        metrics = MetricsListener()
        fsm.add_listener(metrics)
        fsm.trigger("start")
        fsm.trigger("stop")
        fsm.trigger("start")

        assert metrics.counts == {"start": 2, "stop": 1}


# ---------------------------------------------------------------------------
# before_transition listener protocol hook
# ---------------------------------------------------------------------------


class TestBeforeTransitionListener:
    def test_before_transition_fires_before_on_exit_state(self):
        """before_transition fires before on_exit_state and after_transition."""
        order = []

        class OrderListener:
            def before_transition(self, source, target, trigger, **kwargs):
                order.append("before")

            def on_exit_state(self, source, target, trigger, **kwargs):
                order.append("exit")

            def after_transition(self, source, target, trigger, **kwargs):
                order.append("after")

        fsm = _make_fsm()
        fsm.add_listener(OrderListener())
        fsm.trigger("start")

        assert order.index("before") < order.index("exit") < order.index("after")

    def test_before_transition_not_called_on_blocked_trigger(self):
        """before_transition must NOT fire when a trigger has no matching transition."""
        calls = []

        class L:
            def before_transition(self, source, target, trigger, **kwargs):
                calls.append(trigger)

        fsm = _make_fsm()
        fsm.add_listener(L())
        fsm.trigger("stop")  # blocked — no "stop" from idle
        assert calls == []

    def test_before_transition_receives_correct_args(self):
        """before_transition receives (source: State, target: State, trigger: str)."""
        captured = []

        class L:
            def before_transition(self, source, target, trigger, **kwargs):
                captured.append((type(source).__name__, type(target).__name__, trigger))

        fsm = _make_fsm()
        fsm.add_listener(L())
        fsm.trigger("start")

        assert len(captured) == 1
        src_type, tgt_type, trig = captured[0]
        assert src_type == "State"
        assert tgt_type == "State"
        assert trig == "start"

    def test_before_transition_state_values_correct(self):
        """before_transition receives the correct source and target state objects."""
        captured = []

        class L:
            def before_transition(self, source, target, trigger, **kwargs):
                captured.append((source.name, target.name))

        fsm = _make_fsm()
        fsm.add_listener(L())
        fsm.trigger("start")

        assert captured == [("idle", "running")]
