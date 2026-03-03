"""
Tests for AsyncStateMachine, AsyncCondition, and async workflows.

Covers trigger_async, can_trigger_async, AsyncCondition.check_async,
FSMBuilder async auto-detection, and AsyncDeclarativeState.
"""

import pytest

from fast_fsm.conditions import AsyncCondition, Condition
from fast_fsm.core import (
    AsyncStateMachine,
    State,
    StateMachine,
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
