"""
Tests for AsyncStateMachine, AsyncCondition, and async workflows.

Covers trigger_async, can_trigger_async, AsyncCondition.check_async,
FSMBuilder async auto-detection, and AsyncDeclarativeState.
"""

import pytest

from fast_fsm.condition_templates import AndCondition, NotCondition, OrCondition
from fast_fsm.conditions import AsyncCondition, Condition, NegatedCondition
from fast_fsm.core import (
    AsyncDeclarativeState,
    AsyncStateMachine,
    CompiledFuncCondition,
    FSMBuilder,
    State,
    StateMachine,
    TransitionResult,
    transition,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class AlwaysTrueCondition(Condition):
    """Sync condition that always passes."""

    def __init__(self):
        super().__init__("always_true", "always true")

    def check(self, **kwargs) -> bool:
        return True


class RejectingState(State):
    """State that rejects all transitions via can_transition."""

    def can_transition(self, trigger, to_state, *args, **kwargs):
        return False


class AsyncDeclarativeInvocationCounter(AsyncDeclarativeState):
    """Test-only async declarative state that records ordinary dispatch."""

    def __init__(self, name: str = "source", result=None):
        super().__init__(name)
        self.invocations = 0
        self._result = result

    @transition("advance", from_state="source", to_state="target")
    async def handle_advance(self, *args, **kwargs):
        self.invocations += 1
        if self._result == "raise":
            raise RuntimeError("phase 17 owns handler failure semantics")
        return self._result

    @transition("前進⚡", from_state="source", to_state="target")
    async def handle_unicode_advance(self, *args, **kwargs):
        self.invocations += 1
        return self._result


async def _invoke_and_ignore_phase17_outcome(invoker):
    """Exercise a handler without fixing Phase 17 lifecycle outcomes in this phase."""
    try:
        await invoker()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class AlwaysAsyncCondition(AsyncCondition):
    """Async condition that always passes."""

    def __init__(self):
        super().__init__("always_async", "Always passes asynchronously")
        self.call_count = 0

    async def check_async(self, **kwargs) -> bool:
        self.call_count += 1
        return True


class NeverAsyncCondition(AsyncCondition):
    """Async condition that always fails."""

    def __init__(self):
        super().__init__("never_async", "Always fails asynchronously")

    async def check_async(self, **kwargs) -> bool:
        return False


class ThresholdAsyncCondition(AsyncCondition):
    """Async condition that checks a value threshold."""

    def __init__(self, key: str, threshold: int):
        super().__init__(f"threshold_{key}", f"{key} >= {threshold}")
        self.key = key
        self.threshold = threshold

    async def check_async(self, **kwargs) -> bool:
        return kwargs.get(self.key, 0) >= self.threshold


class ExplodingAsyncCondition(AsyncCondition):
    """Async condition that raises an exception."""

    def __init__(self):
        super().__init__("exploding_async", "Raises RuntimeError")

    async def check_async(self, **kwargs) -> bool:
        raise RuntimeError("async boom")


class SyncCounter(Condition):
    """Sync condition for mixing with async in same FSM."""

    def __init__(self):
        super().__init__("sync_counter", "Sync counter")
        self.call_count = 0

    def check(self, **kwargs) -> bool:
        self.call_count += 1
        return True


class RecordingAsyncCondition(AsyncCondition):
    """Async guard fixture that captures positional and keyword context."""

    def __init__(self, result=True):
        super().__init__("recording_async", "records async guard context")
        self.result = result
        self.calls = []

    async def check_async(self, *args, **kwargs) -> bool:
        self.calls.append((args, kwargs, id(kwargs)))
        return self.result


class ShortCircuitCondition(AsyncCondition):
    """Async leaf whose counter proves short-circuit evaluation order."""

    def __init__(self, result):
        super().__init__("short_circuit_async", "counts async evaluation")
        self.result = result
        self.calls = 0

    async def check_async(self, *args, **kwargs) -> bool:
        self.calls += 1
        return self.result


def make_negated_cycle():
    """Build a supported-wrapper cycle without exposing any public protocol."""
    condition = NegatedCondition(AlwaysTrueCondition())
    condition._inner = condition
    return condition


def make_and_cycle():
    """Build an AndCondition self-cycle for deterministic rejection tests."""
    condition = AndCondition(AlwaysTrueCondition())
    condition.conditions = (condition,)
    return condition


def make_or_cycle():
    """Build an OrCondition self-cycle for deterministic rejection tests."""
    condition = OrCondition(AlwaysTrueCondition())
    condition.conditions = (condition,)
    return condition


def make_not_cycle():
    """Build a NotCondition self-cycle for deterministic rejection tests."""
    condition = NotCondition(AlwaysTrueCondition())
    condition.condition = condition
    return condition


def make_shared_condition_dag():
    """Return an acyclic graph that reuses one async leaf twice."""
    shared = RecordingAsyncCondition()
    return AndCondition(shared, NotCondition(NegatedCondition(shared)))


@pytest.fixture
def two_state_async_fsm():
    """AsyncStateMachine with idle → running."""
    idle = State("idle")
    running = State("running")
    fsm = AsyncStateMachine(idle, name="async_two")
    fsm.add_state(running)
    return fsm, idle, running


# ---------------------------------------------------------------------------
# AsyncStateMachine basics
# ---------------------------------------------------------------------------


class TestAsyncStateMachineBasics:
    """Basic lifecycle of AsyncStateMachine."""

    def test_is_subclass_of_state_machine(self):
        fsm = AsyncStateMachine(State("s"), name="sub_check")
        assert isinstance(fsm, StateMachine)

    @pytest.mark.asyncio
    async def test_trigger_async_success(self, two_state_async_fsm):
        fsm, idle, running = two_state_async_fsm
        fsm.add_transition("go", "idle", "running")
        result = await fsm.trigger_async("go")
        assert result.success
        assert fsm.current_state.name == "running"

    @pytest.mark.asyncio
    async def test_trigger_async_no_transition(self, two_state_async_fsm):
        fsm, idle, running = two_state_async_fsm
        result = await fsm.trigger_async("nonexistent")
        assert not result.success
        assert "No transition" in result.error

    @pytest.mark.asyncio
    async def test_trigger_async_roundtrip(self, two_state_async_fsm):
        fsm, idle, running = two_state_async_fsm
        fsm.add_transition("go", "idle", "running")
        fsm.add_transition("stop", "running", "idle")

        await fsm.trigger_async("go")
        assert fsm.current_state.name == "running"
        await fsm.trigger_async("stop")
        assert fsm.current_state.name == "idle"


# ---------------------------------------------------------------------------
# AsyncCondition evaluation
# ---------------------------------------------------------------------------


class TestAsyncConditionEvaluation:
    """trigger_async with AsyncCondition instances."""

    @pytest.mark.asyncio
    async def test_async_condition_passes(self, two_state_async_fsm):
        fsm, idle, running = two_state_async_fsm
        cond = AlwaysAsyncCondition()
        fsm.add_transition("go", "idle", "running", cond)

        result = await fsm.trigger_async("go")
        assert result.success
        assert cond.call_count == 1

    @pytest.mark.asyncio
    async def test_async_condition_blocks(self, two_state_async_fsm):
        fsm, idle, running = two_state_async_fsm
        fsm.add_transition("go", "idle", "running", NeverAsyncCondition())

        result = await fsm.trigger_async("go")
        assert not result.success
        assert fsm.current_state.name == "idle"

    @pytest.mark.asyncio
    async def test_async_condition_with_kwargs(self, two_state_async_fsm):
        fsm, idle, running = two_state_async_fsm
        cond = ThresholdAsyncCondition("level", 10)
        fsm.add_transition("go", "idle", "running", cond)

        # Below threshold
        result = await fsm.trigger_async("go", level=5)
        assert not result.success

        # At threshold
        result = await fsm.trigger_async("go", level=10)
        assert result.success

    @pytest.mark.asyncio
    async def test_async_condition_exception_caught(self, two_state_async_fsm):
        fsm, idle, running = two_state_async_fsm
        fsm.add_transition("go", "idle", "running", ExplodingAsyncCondition())

        result = await fsm.trigger_async("go")
        assert not result.success
        assert "async boom" in result.error
        assert fsm.current_state.name == "idle"

    @pytest.mark.asyncio
    async def test_sync_condition_in_async_fsm(self, two_state_async_fsm):
        """AsyncStateMachine should tolerate sync conditions too."""
        fsm, idle, running = two_state_async_fsm
        sync_cond = SyncCounter()
        fsm.add_transition("go", "idle", "running", sync_cond)

        result = await fsm.trigger_async("go")
        assert result.success
        assert sync_cond.call_count == 1


# ---------------------------------------------------------------------------
# can_trigger_async
# ---------------------------------------------------------------------------


class TestCanTriggerAsync:
    """can_trigger_async probes without mutating state."""

    @pytest.mark.asyncio
    async def test_can_trigger_async_true(self, two_state_async_fsm):
        fsm, idle, running = two_state_async_fsm
        fsm.add_transition("go", "idle", "running", AlwaysAsyncCondition())
        assert await fsm.can_trigger_async("go")

    @pytest.mark.asyncio
    async def test_can_trigger_async_false_no_transition(self, two_state_async_fsm):
        fsm, *_ = two_state_async_fsm
        assert not await fsm.can_trigger_async("nope")

    @pytest.mark.asyncio
    async def test_can_trigger_async_false_condition(self, two_state_async_fsm):
        fsm, idle, running = two_state_async_fsm
        fsm.add_transition("go", "idle", "running", NeverAsyncCondition())
        assert not await fsm.can_trigger_async("go")

    @pytest.mark.asyncio
    async def test_can_trigger_async_does_not_mutate(self, two_state_async_fsm):
        fsm, idle, running = two_state_async_fsm
        fsm.add_transition("go", "idle", "running")
        await fsm.can_trigger_async("go")
        assert fsm.current_state.name == "idle"

    @pytest.mark.asyncio
    async def test_async_guard_context_is_sanitized_and_positional(
        self, two_state_async_fsm
    ):
        fsm, idle, running = two_state_async_fsm
        condition = RecordingAsyncCondition()
        fsm.add_transition("go", idle, running, condition)
        marker = object()

        assert await fsm.can_trigger_async(
            "go", marker, safe="visible", _private="hidden"
        )

        args, kwargs, _ = condition.calls[-1]
        assert args[0] is marker
        assert kwargs == {"safe": "visible"}


class TestAsyncWrapperEvaluation:
    """D-11/D-14 nested built-in wrapper behavior."""

    @staticmethod
    def _machine(condition):
        initial = State("initial")
        target = State("target")
        machine = AsyncStateMachine(initial, name="async_wrapper")
        machine.add_state(target)
        machine.add_transition("go", initial, target, condition)
        return machine

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "factory",
        [
            lambda: NegatedCondition(RecordingAsyncCondition(result=False)),
            lambda: AndCondition(RecordingAsyncCondition(), RecordingAsyncCondition()),
            lambda: OrCondition(
                RecordingAsyncCondition(result=False), RecordingAsyncCondition()
            ),
            lambda: NotCondition(RecordingAsyncCondition(result=False)),
        ],
    )
    async def test_async_wrappers_await_nested_leaves_for_can_and_trigger(
        self, factory
    ):
        condition = factory()
        machine = self._machine(condition)
        marker = object()
        payload = object()

        assert await machine.can_trigger_async("go", marker, payload=payload)
        assert (await machine.trigger_async("go", marker, payload=payload)).success

    @pytest.mark.asyncio
    async def test_async_wrappers_preserve_short_circuit_order(self):
        false_left = ShortCircuitCondition(False)
        skipped_and = ShortCircuitCondition(True)
        true_left = ShortCircuitCondition(True)
        skipped_or = ShortCircuitCondition(False)

        assert not await self._machine(
            AndCondition(false_left, skipped_and)
        ).can_trigger_async("go")
        assert await self._machine(
            OrCondition(true_left, skipped_or)
        ).can_trigger_async("go")
        assert false_left.calls == 1
        assert skipped_and.calls == 0
        assert true_left.calls == 1
        assert skipped_or.calls == 0

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "factory",
        [make_negated_cycle, make_and_cycle, make_or_cycle, make_not_cycle],
    )
    async def test_supported_wrapper_cycles_raise_value_error(self, factory):
        initial = State("initial")
        target = State("target")
        machine = AsyncStateMachine(initial, name="async_cycle")
        machine.add_state(target)

        with pytest.raises(ValueError, match="cycle"):
            machine.add_transition("go", initial, target, factory())

    @pytest.mark.parametrize(
        "factory",
        [make_negated_cycle, make_and_cycle, make_or_cycle, make_not_cycle],
    )
    def test_async_sibling_does_not_hide_a_supported_wrapper_cycle(self, factory):
        initial = State("initial")
        target = State("target")
        machine = AsyncStateMachine(initial, name="hidden_async_cycle")
        machine.add_state(target)

        with pytest.raises(ValueError, match="cycle"):
            machine.add_transition(
                "go",
                initial,
                target,
                AndCondition(RecordingAsyncCondition(), factory()),
            )

    @pytest.mark.asyncio
    async def test_shared_condition_dag_is_accepted_and_awaited(self):
        machine = self._machine(make_shared_condition_dag())

        assert await machine.can_trigger_async("go")
        assert (await machine.trigger_async("go")).success

    def test_deep_sync_wrapper_graph_avoids_python_recursion_limit(self):
        condition = AlwaysTrueCondition()
        for _ in range(1_500):
            condition = NotCondition(condition)

        initial = State("initial")
        target = State("target")
        machine = StateMachine(initial, name="deep_sync_wrapper")
        machine.add_state(target)
        machine.add_transition("go", initial, target, condition)

        assert machine.can_trigger("go")
        assert machine.trigger("go").success

    @pytest.mark.asyncio
    async def test_deep_async_wrapper_graph_avoids_python_recursion_limit(self):
        leaf = RecordingAsyncCondition()
        condition = leaf
        for _ in range(1_500):
            condition = NotCondition(condition)

        machine = self._machine(condition)

        assert await machine.can_trigger_async("go")
        assert (await machine.trigger_async("go")).success
        assert len(leaf.calls) == 2

    def test_sync_wrapper_runtime_handles_empty_composites_and_late_cycle(self):
        initial = State("initial")
        target = State("target")
        machine = StateMachine(initial, name="sync_wrapper_edges")
        machine.add_state(target)

        assert machine._evaluate_condition_sync(AndCondition(), (), {})
        assert not machine._evaluate_condition_sync(OrCondition(), (), {})
        assert machine._evaluate_condition_sync(
            OrCondition(NegatedCondition(AlwaysTrueCondition()), AlwaysTrueCondition()),
            (),
            {},
        )
        with pytest.raises(TypeError, match="AsyncCondition"):
            machine._evaluate_condition_sync(RecordingAsyncCondition(), (), {})

        cycle = NotCondition(AlwaysTrueCondition())
        machine.add_transition("go", initial, target, cycle)
        cycle.condition = cycle

        with pytest.raises(ValueError, match="cycle"):
            machine.can_trigger("go")

    @pytest.mark.asyncio
    async def test_async_wrapper_runtime_handles_empty_composites_and_late_cycle(self):
        assert await self._machine(AndCondition()).can_trigger_async("go")
        assert not await self._machine(OrCondition()).can_trigger_async("go")

        initial = State("initial")
        target = State("target")
        machine = AsyncStateMachine(initial, name="async_wrapper_edges")
        machine.add_state(target)
        cycle = NotCondition(AlwaysTrueCondition())
        machine.add_transition("go", initial, target, cycle)
        cycle.condition = cycle

        with pytest.raises(ValueError, match="cycle"):
            await machine.can_trigger_async("go")

    def test_sync_machine_rejects_nested_async_wrapper(self):
        initial = State("initial")
        target = State("target")
        machine = StateMachine(initial, name="sync_wrapper")
        machine.add_state(target)

        with pytest.raises(TypeError, match="AsyncCondition"):
            machine.add_transition(
                "go", initial, target, NegatedCondition(RecordingAsyncCondition())
            )

    def test_compiled_func_condition_forwards_positional_context(self):
        captured = []
        marker = object()

        def guard(*args, **kwargs):
            captured.append((args, kwargs))
            return True

        assert CompiledFuncCondition(guard).check(marker, payload="value")
        assert captured[0][0][0] is marker
        assert captured[0][1] == {"payload": "value"}


# ---------------------------------------------------------------------------
# Callbacks in async transitions
# ---------------------------------------------------------------------------


class TestAsyncCallbacks:
    """on_enter / on_exit still fire during trigger_async."""

    @pytest.mark.asyncio
    async def test_callbacks_execute_during_async_trigger(self):
        log = []

        idle = State.create(
            "idle",
            on_exit=lambda to_state, trigger, *a, **kw: log.append("exit_idle"),
        )
        running = State.create(
            "running",
            on_enter=lambda from_state, trigger, *a, **kw: log.append("enter_running"),
        )

        fsm = AsyncStateMachine(idle, name="cb_async")
        fsm.add_state(running)
        fsm.add_transition("go", "idle", "running")

        await fsm.trigger_async("go")
        assert "exit_idle" in log
        assert "enter_running" in log

    @pytest.mark.asyncio
    async def test_callback_exception_does_not_block_transition(self):
        """Transition completes even when a callback raises."""

        def bad_exit(to_state, trigger, *a, **kw):
            raise ValueError("exit crash")

        idle = State.create("idle", on_exit=bad_exit)
        running = State("running")

        fsm = AsyncStateMachine(idle, name="crash_cb")
        fsm.add_state(running)
        fsm.add_transition("go", "idle", "running")

        result = await fsm.trigger_async("go")
        assert result.success
        assert fsm.current_state.name == "running"


# ---------------------------------------------------------------------------
# Additional async trigger / can_trigger_async gap coverage
# ---------------------------------------------------------------------------


class ConfigurableAsyncCondition(AsyncCondition):
    """Async condition with configurable result."""

    def __init__(self, result: bool = True):
        super().__init__("configurable_async", "configurable async")
        self._result = result

    async def check_async(self, **kwargs) -> bool:
        return self._result


class TestAsyncTriggerGaps:
    """Cover async condition exception handling and state rejection."""

    @pytest.mark.asyncio
    async def test_async_condition_exception_in_trigger(self):
        """Exception in async condition check during trigger_async."""
        s1 = State("s1")
        s2 = State("s2")
        fsm = AsyncStateMachine(s1, name="async_exc")
        fsm.add_state(s2)
        fsm.add_transition("go", "s1", "s2", ExplodingAsyncCondition())

        result = await fsm.trigger_async("go")
        assert not result.success
        assert result.error is not None
        assert "async boom" in result.error

    @pytest.mark.asyncio
    async def test_async_trigger_state_rejection(self):
        """When state.can_transition returns False in trigger_async."""
        rejecting = RejectingState("reject")
        target = State("target")
        fsm = AsyncStateMachine(rejecting, name="async_reject")
        fsm.add_state(target)
        fsm.add_transition("go", "reject", "target")

        result = await fsm.trigger_async("go")
        assert not result.success
        assert result.error is not None
        assert "rejected" in result.error.lower()

    @pytest.mark.asyncio
    async def test_can_trigger_async_with_failing_condition(self):
        """can_trigger_async should return False if condition fails."""
        s1 = State("s1")
        s2 = State("s2")
        fsm = AsyncStateMachine(s1, name="async_ct")
        fsm.add_state(s2)
        fsm.add_transition("go", "s1", "s2", ConfigurableAsyncCondition(result=False))

        assert not await fsm.can_trigger_async("go")

    @pytest.mark.asyncio
    async def test_can_trigger_async_with_sync_condition(self):
        """can_trigger_async dispatches to sync condition.check() correctly."""
        s1 = State("s1")
        s2 = State("s2")
        fsm = AsyncStateMachine(s1, name="async_ct_sync")
        fsm.add_state(s2)
        fsm.add_transition("go", "s1", "s2", AlwaysTrueCondition())

        assert await fsm.can_trigger_async("go")

    @pytest.mark.asyncio
    async def test_can_trigger_async_state_rejection(self):
        """can_trigger_async should return False when state rejects transition."""
        rejecting = RejectingState("reject")
        target = State("target")
        fsm = AsyncStateMachine(rejecting, name="async_ct_reject")
        fsm.add_state(target)
        fsm.add_transition("go", "reject", "target")

        assert not await fsm.can_trigger_async("go")

    @pytest.mark.asyncio
    async def test_async_trigger_with_sync_condition(self):
        """trigger_async handles sync Condition objects correctly."""
        s1 = State("s1")
        s2 = State("s2")
        fsm = AsyncStateMachine(s1, name="async_sync_cond")
        fsm.add_state(s2)
        fsm.add_transition("go", "s1", "s2", AlwaysTrueCondition())

        result = await fsm.trigger_async("go")
        assert result.success
        assert fsm.current_state.name == "s2"


class TestAsyncPerStateCallbacks:
    """Tests for on_enter_async / on_exit_async (fast_fsm-61j)."""

    @pytest.mark.asyncio
    async def test_on_enter_async_fires_on_successful_transition(self):
        idle = State("idle")
        running = State("running")
        fsm = AsyncStateMachine(idle, name="enter_async")
        fsm.add_state(running)
        fsm.add_transition("start", "idle", "running")

        log: list = []

        async def on_enter(from_s, t, **kw):
            log.append(("enter", from_s.name, t))

        fsm.on_enter_async("running", on_enter)
        result = await fsm.trigger_async("start")
        assert result.success
        assert log == [("enter", "idle", "start")]

    @pytest.mark.asyncio
    async def test_on_exit_async_fires_on_successful_transition(self):
        idle = State("idle")
        running = State("running")
        fsm = AsyncStateMachine(idle, name="exit_async")
        fsm.add_state(running)
        fsm.add_transition("start", "idle", "running")

        log: list = []

        async def on_exit(to_s, t, **kw):
            log.append(("exit", to_s.name, t))

        fsm.on_exit_async("idle", on_exit)
        result = await fsm.trigger_async("start")
        assert result.success
        assert log == [("exit", "running", "start")]

    @pytest.mark.asyncio
    async def test_async_callbacks_do_not_fire_on_failed_transition(self):
        idle = State("idle")
        running = State("running")
        fsm = AsyncStateMachine(idle, name="no_fire")
        fsm.add_state(running)
        fsm.add_transition("start", "idle", "running", condition=NeverAsyncCondition())

        log: list = []
        fsm.on_enter_async("running", lambda from_s, t, **kw: log.append("enter"))
        fsm.on_exit_async("idle", lambda to_s, t, **kw: log.append("exit"))

        result = await fsm.trigger_async("start")
        assert not result.success
        assert log == []

    @pytest.mark.asyncio
    async def test_multiple_async_callbacks_called_in_order(self):
        idle = State("idle")
        running = State("running")
        fsm = AsyncStateMachine(idle, name="multi_async")
        fsm.add_state(running)
        fsm.add_transition("start", "idle", "running")

        log: list = []

        async def cb1(from_s, t, **kw):
            log.append(1)

        async def cb2(from_s, t, **kw):
            log.append(2)

        fsm.on_enter_async("running", cb1)
        fsm.on_enter_async("running", cb2)
        await fsm.trigger_async("start")
        assert log == [1, 2]

    @pytest.mark.asyncio
    async def test_async_callback_exception_is_caught_not_raised(self):
        idle = State("idle")
        running = State("running")
        fsm = AsyncStateMachine(idle, name="exc_async")
        fsm.add_state(running)
        fsm.add_transition("start", "idle", "running")

        async def bad_cb(from_s, t, **kw):
            raise RuntimeError("boom")

        fsm.on_enter_async("running", bad_cb)
        result = await fsm.trigger_async("start")
        # Transition still succeeds; exception is caught and logged
        assert result.success
        assert fsm.current_state.name == "running"

    @pytest.mark.asyncio
    async def test_async_callbacks_receive_kwargs(self):
        idle = State("idle")
        running = State("running")
        fsm = AsyncStateMachine(idle, name="kw_async")
        fsm.add_state(running)
        fsm.add_transition("start", "idle", "running")

        received: list = []

        async def on_enter(from_s, t, **kw):
            received.append(kw.get("payload"))

        fsm.on_enter_async("running", on_enter)
        await fsm.trigger_async("start", payload="hello")
        assert received == ["hello"]

    @pytest.mark.asyncio
    async def test_on_enter_exit_async_order_relative_to_sync(self):
        """Async callbacks fire AFTER all sync callbacks."""
        from fast_fsm import CallbackState

        log: list = []

        idle = CallbackState(
            "idle", on_exit=lambda to_s, t, **kw: log.append("sync_exit")
        )
        running = CallbackState(
            "running", on_enter=lambda from_s, t, **kw: log.append("sync_enter")
        )

        fsm = AsyncStateMachine(idle, name="order_async")
        fsm.add_state(running)
        fsm.add_transition("start", "idle", "running")

        async def async_exit(to_s, t, **kw):
            log.append("async_exit")

        async def async_enter(from_s, t, **kw):
            log.append("async_enter")

        fsm.on_exit_async("idle", async_exit)
        fsm.on_enter_async("running", async_enter)
        await fsm.trigger_async("start")
        # sync callbacks fire first (inside _execute_transition),
        # then async callbacks fire in exit→enter order
        assert log == ["sync_exit", "sync_enter", "async_exit", "async_enter"]

    @pytest.mark.asyncio
    async def test_clone_copies_async_callbacks(self):
        idle = State("idle")
        running = State("running")
        fsm = AsyncStateMachine(idle, name="clone_async")
        fsm.add_state(running)
        fsm.add_transition("start", "idle", "running")

        log: list = []

        async def on_enter(from_s, t, **kw):
            log.append("enter")

        fsm.on_enter_async("running", on_enter)

        cloned = fsm.clone()
        assert isinstance(cloned, AsyncStateMachine)
        await cloned.trigger_async("start")
        assert log == ["enter"]

    @pytest.mark.asyncio
    async def test_clone_async_callbacks_independent(self):
        """Registering callbacks on clone doesn't affect original."""
        idle = State("idle")
        running = State("running")
        fsm = AsyncStateMachine(idle, name="indep_async")
        fsm.add_state(running)
        fsm.add_transition("start", "idle", "running")

        cloned = fsm.clone()
        log: list = []

        async def extra(from_s, t, **kw):
            log.append("extra")

        cloned.on_enter_async("running", extra)

        # Original has no async enter callback for running
        await fsm.trigger_async("start")
        assert log == []  # not fired on original


class TestAsyncOrdinaryDeclarativeDispatch:
    """Async ordinary dispatch shares the declarative invocation boundary."""

    @staticmethod
    def _machine(source, target_name="target"):
        target = State(target_name)
        fsm = AsyncStateMachine(source, name="async_ordinary_declarative")
        fsm.add_state(target)
        fsm.add_transition("advance", source, target)
        return fsm

    @pytest.mark.asyncio
    async def test_async_declarative_ordinary_exactly_once(self):
        source = AsyncDeclarativeInvocationCounter(result=None)
        fsm = self._machine(source)

        result = await fsm.trigger_async("advance")

        assert result.success
        assert source.invocations == 1

    @pytest.mark.asyncio
    @pytest.mark.parametrize("handler_result", [None, True, TransitionResult(True)])
    async def test_async_declarative_ordinary_success_normalization_parity(
        self, handler_result
    ):
        source = AsyncDeclarativeInvocationCounter(result=handler_result)
        fsm = self._machine(source)

        result = await fsm.trigger_async("advance")

        assert result.success
        assert source.invocations == 1

    @pytest.mark.asyncio
    async def test_async_declarative_ordinary_matches_unicode_canonical_metadata(self):
        source = AsyncDeclarativeInvocationCounter(result=True)
        target = State("target")
        fsm = AsyncStateMachine(source, name="async_unicode_declarative")
        fsm.add_state(target)
        fsm.add_transition("前進⚡", source, target)

        result = await fsm.trigger_async("前進⚡")

        assert result.success
        assert source.invocations == 1

    @pytest.mark.asyncio
    async def test_async_declarative_ordinary_ignores_nonmatching_source_metadata(self):
        source = AsyncDeclarativeInvocationCounter(name="wrong_source", result=True)
        fsm = self._machine(source)

        await fsm.trigger_async("advance")

        assert source.invocations == 0

    @pytest.mark.asyncio
    async def test_async_declarative_ordinary_ignores_nonmatching_target_metadata(self):
        source = AsyncDeclarativeInvocationCounter(result=True)
        fsm = self._machine(source, target_name="wrong_target")

        await fsm.trigger_async("advance")

        assert source.invocations == 0

    @pytest.mark.asyncio
    async def test_async_declarative_ordinary_unknown_trigger_has_no_side_effect(self):
        source = AsyncDeclarativeInvocationCounter(result=True)
        fsm = self._machine(source)

        await fsm.trigger_async("missing")

        assert source.invocations == 0

    @pytest.mark.asyncio
    async def test_async_declarative_handle_event_uses_the_same_handler_boundary(self):
        source = AsyncDeclarativeInvocationCounter(result=True)

        result = await source.handle_event_async("advance")

        assert result.success
        assert source.invocations == 1

    @pytest.mark.asyncio
    @pytest.mark.parametrize("handler_result", [False, "invalid", "raise"])
    async def test_async_declarative_ordinary_invocation_only_for_phase17_outcomes(
        self, handler_result
    ):
        source = AsyncDeclarativeInvocationCounter(result=handler_result)
        fsm = self._machine(source)

        await _invoke_and_ignore_phase17_outcome(lambda: fsm.trigger_async("advance"))

        assert source.invocations == 1


class TestAsyncDeclarativeWrapperGuards:
    """Resolved decorator guards use the same recursive evaluator as entries."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("factory", "leaf_result"),
        (
            (lambda leaf: NegatedCondition(leaf), False),
            (lambda leaf: AndCondition(leaf), True),
            (lambda leaf: OrCondition(leaf), True),
            (lambda leaf: NotCondition(leaf), False),
        ),
    )
    async def test_nested_async_decorator_guard_awaits_for_can_and_trigger(
        self, factory, leaf_result
    ):
        leaf = RecordingAsyncCondition(result=leaf_result)
        condition = factory(leaf)

        class Source(AsyncDeclarativeState):
            def __init__(self, name):
                super().__init__(name)
                self.handler_calls = 0

            @transition(
                "advance",
                from_state="source",
                to_state="target",
                condition=condition,
            )
            async def handle_advance(self, *args, **kwargs):
                self.handler_calls += 1
                return True

        source = Source("source")
        target = State("target")
        builder = FSMBuilder(source)
        builder.add_state(target).add_transition("advance", "source", "target")

        machine = builder.build()
        assert isinstance(machine, AsyncStateMachine)
        assert await machine.can_trigger_async("advance")
        assert (await machine.trigger_async("advance")).success
        assert len(leaf.calls) == 2
        assert source.handler_calls == 1


class TestAsyncHistory:
    """HIST-07: AsyncStateMachine records to the same history buffer."""

    @pytest.mark.asyncio
    async def test_trigger_async_records_history(self):
        idle = State("idle")
        running = State("running")
        done = State("done")
        fsm = AsyncStateMachine(idle, name="async_hist")
        fsm.add_state(running)
        fsm.add_state(done)
        fsm.add_transition("start", "idle", "running")
        fsm.add_transition("finish", "running", "done")

        fsm.enable_history()
        await fsm.trigger_async("start")
        await fsm.trigger_async("finish")

        h = fsm.history
        assert len(h) == 2
        assert h[0].from_state == "idle"
        assert h[0].to_state == "running"
        assert h[1].from_state == "running"
        assert h[1].to_state == "done"

    @pytest.mark.asyncio
    async def test_trigger_async_history_capacity_and_fifo_parity(self):
        idle = State("idle")
        running = State("running")
        done = State("done")
        fsm = AsyncStateMachine(idle, name="async_hist_fifo")
        fsm.add_state(running)
        fsm.add_state(done)
        fsm.add_transition("start", "idle", "running")
        fsm.add_transition("finish", "running", "done")
        fsm.add_transition("reset", "done", "idle")
        fsm.enable_history(max_entries=2)

        await fsm.trigger_async("start")
        await fsm.trigger_async("finish")
        await fsm.trigger_async("reset")

        assert [(record.from_state, record.to_state) for record in fsm.history] == [
            ("running", "done"),
            ("done", "idle"),
        ]

    @pytest.mark.asyncio
    async def test_trigger_async_history_invalid_capacity_preserves_buffer(self):
        idle = State("idle")
        running = State("running")
        fsm = AsyncStateMachine(idle, name="async_hist_invalid")
        fsm.add_state(running)
        fsm.add_transition("start", "idle", "running")
        fsm.enable_history(max_entries=2)
        await fsm.trigger_async("start")
        previous_buffer = fsm._history
        previous_records = fsm.history
        previous_max_entries = fsm._history_max

        with pytest.raises(ValueError):
            fsm.enable_history(0)

        assert fsm._history is previous_buffer
        assert fsm.history == previous_records
        assert fsm._history_max == previous_max_entries


# ---------------------------------------------------------------------------
# FSMBuilder nested async materialization
# ---------------------------------------------------------------------------


class TestAsyncBuilderPreflight:
    """Builder preflight must choose an await-capable machine for nested leaves."""

    @pytest.mark.asyncio
    async def test_builder_awaits_nested_async_leaf_after_auto_selection(self):
        leaf = AlwaysAsyncCondition()
        builder = FSMBuilder(State("idle"))
        builder.add_state(State("running"))
        builder.add_transition(
            "start",
            "idle",
            "running",
            OrCondition(
                NeverAsyncCondition(), AndCondition(AlwaysTrueCondition(), leaf)
            ),
        )

        machine = builder.build()

        assert isinstance(machine, AsyncStateMachine)
        assert await machine.can_trigger_async("start")
        assert (await machine.trigger_async("start")).success
        assert leaf.call_count == 2
