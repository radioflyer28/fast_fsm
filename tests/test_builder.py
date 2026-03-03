"""
Tests for FSMBuilder, DeclarativeState, AsyncDeclarativeState,
@transition decorator, condition_builder, quick_fsm, and simple_fsm.

All tests use real components — no mocking.
"""

import pytest

from fast_fsm.conditions import AsyncCondition, Condition, FuncCondition
from fast_fsm.core import (
    AsyncDeclarativeState,
    AsyncStateMachine,
    DeclarativeState,
    FSMBuilder,
    State,
    StateMachine,
    TransitionResult,
    condition_builder,
    quick_fsm,
    simple_fsm,
    transition,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class AlwaysTrue(Condition):
    """Condition that always passes."""

    def __init__(self):
        super().__init__("always_true", "always true")

    def check(self, **kwargs) -> bool:
        return True


class AlwaysFalse(Condition):
    """Condition that always fails."""

    def __init__(self):
        super().__init__("always_false", "always false")

    def check(self, **kwargs) -> bool:
        return False


class SimpleAsyncCondition(AsyncCondition):
    """Async condition for builder auto-detection tests."""

    def __init__(self):
        super().__init__("simple_async", "simple async condition")

    async def check_async(self, **kwargs) -> bool:
        return True


# ---------------------------------------------------------------------------
# FSMBuilder basics
# ---------------------------------------------------------------------------


class TestFSMBuilderBasics:
    def test_build_simple_fsm(self):
        idle = State("idle")
        builder = FSMBuilder(idle, name="basic")
        builder.add_state(State("running"))
        builder.add_transition("go", "idle", "running")
        fsm = builder.build()

        assert isinstance(fsm, StateMachine)
        assert fsm.name == "basic"
        assert fsm.current_state.name == "idle"
        assert fsm.trigger("go").success
        assert fsm.current_state.name == "running"

    def test_build_returns_same_instance(self):
        builder = FSMBuilder(State("s"), name="once")
        fsm1 = builder.build()
        fsm2 = builder.build()
        assert fsm1 is fsm2

    def test_fluent_chaining(self):
        fsm = (
            FSMBuilder(State("a"), name="chain")
            .add_state(State("b"))
            .add_state(State("c"))
            .add_transition("ab", "a", "b")
            .add_transition("bc", "b", "c")
            .build()
        )
        assert fsm.trigger("ab").success
        assert fsm.trigger("bc").success
        assert fsm.current_state.name == "c"

    def test_build_with_condition(self):
        builder = FSMBuilder(State("a"), name="cond")
        builder.add_state(State("b"))
        builder.add_transition("go", "a", "b", AlwaysTrue())
        fsm = builder.build()
        assert fsm.trigger("go").success

    def test_build_with_failing_condition(self):
        builder = FSMBuilder(State("a"), name="fail_cond")
        builder.add_state(State("b"))
        builder.add_transition("go", "a", "b", AlwaysFalse())
        fsm = builder.build()
        assert not fsm.trigger("go").success

    def test_repr(self):
        builder = FSMBuilder(State("s"), name="repr_test")
        r = repr(builder)
        assert "FSMBuilder" in r
        assert "states=1" in r
        assert "built=False" in r

    def test_repr_after_build(self):
        builder = FSMBuilder(State("s"), name="repr_test2")
        builder.build()
        assert "built=True" in repr(builder)


# ---------------------------------------------------------------------------
# FSMBuilder async auto-detection
# ---------------------------------------------------------------------------


class TestFSMBuilderAsyncDetection:
    def test_sync_by_default(self):
        builder = FSMBuilder(State("s"))
        assert builder.machine_type is StateMachine
        assert not builder.is_async

    def test_auto_detects_async_condition(self):
        builder = FSMBuilder(State("a"))
        builder.add_state(State("b"))
        builder.add_transition("go", "a", "b", SimpleAsyncCondition())
        assert builder.is_async
        assert builder.machine_type is AsyncStateMachine

    def test_auto_detects_async_declarative_state(self):
        async_state = AsyncDeclarativeState("async_s")
        builder = FSMBuilder(async_state)
        assert builder.is_async

    def test_force_async(self):
        builder = FSMBuilder(State("s"))
        builder.force_async()
        assert builder.is_async
        fsm = builder.build()
        assert isinstance(fsm, AsyncStateMachine)

    def test_force_sync(self):
        builder = FSMBuilder(State("s"))
        builder.force_sync()
        assert not builder.is_async
        fsm = builder.build()
        assert isinstance(fsm, StateMachine)
        assert not isinstance(fsm, AsyncStateMachine)

    def test_force_after_build_raises(self):
        builder = FSMBuilder(State("s"))
        builder.build()
        with pytest.raises(RuntimeError, match="Cannot change machine type"):
            builder.force_async()
        with pytest.raises(RuntimeError, match="Cannot change machine type"):
            builder.force_sync()

    def test_explicit_async_mode_true(self):
        builder = FSMBuilder(State("s"), async_mode=True)
        assert builder.is_async

    def test_explicit_async_mode_false(self):
        builder = FSMBuilder(State("s"), async_mode=False)
        assert not builder.is_async


# ---------------------------------------------------------------------------
# DeclarativeState + @transition
# ---------------------------------------------------------------------------


class TestDeclarativeState:
    def test_handler_discovery(self):
        class MyState(DeclarativeState):
            @transition("go")
            def handle_go(self, *args, **kwargs):
                return TransitionResult(True)

        s = MyState("test_state")
        assert "go" in s._handlers

    def test_handle_event_success(self):
        class MyState(DeclarativeState):
            @transition("go")
            def handle_go(self, *args, **kwargs):
                return TransitionResult(True)

        s = MyState("s1")
        result = s.handle_event("go")
        assert result.success

    def test_handle_event_returns_none_treated_as_success(self):
        class MyState(DeclarativeState):
            @transition("process")
            def handle_process(self, *args, **kwargs):
                pass  # returns None

        s = MyState("s1")
        result = s.handle_event("process")
        assert result.success

    def test_handle_event_returns_bool(self):
        class MyState(DeclarativeState):
            @transition("check")
            def handle_check(self, *args, **kwargs):
                return False

        s = MyState("s1")
        result = s.handle_event("check")
        assert not result.success

    def test_handle_event_exception(self):
        class MyState(DeclarativeState):
            @transition("crash")
            def handle_crash(self, *args, **kwargs):
                raise ValueError("boom")

        s = MyState("s1")
        result = s.handle_event("crash")
        assert not result.success
        assert "boom" in result.error

    def test_handle_event_unknown_falls_through(self):
        class MyState(DeclarativeState):
            pass

        s = MyState("s1")
        result = s.handle_event("unknown")
        assert isinstance(result, TransitionResult)

    def test_can_transition_with_condition(self):
        cond = AlwaysTrue()

        class MyState(DeclarativeState):
            @transition("go", condition=cond)
            def handle_go(self, *args, **kwargs):
                return True

        s = MyState("s1")
        assert s.can_transition("go", State("target"))

    def test_can_transition_with_failing_condition(self):
        cond = AlwaysFalse()

        class MyState(DeclarativeState):
            @transition("go", condition=cond)
            def handle_go(self, *args, **kwargs):
                return True

        s = MyState("s1")
        assert not s.can_transition("go", State("target"))

    def test_can_transition_with_callable_condition(self):
        class MyState(DeclarativeState):
            @transition("go", condition=lambda *a, **kw: kw.get("ok", False))
            def handle_go(self, *args, **kwargs):
                return True

        s = MyState("s1")
        assert not s.can_transition("go", State("target"))
        assert s.can_transition("go", State("target"), ok=True)


# ---------------------------------------------------------------------------
# AsyncDeclarativeState
# ---------------------------------------------------------------------------


class TestAsyncDeclarativeState:
    def test_creates_with_handlers(self):
        class MyState(AsyncDeclarativeState):
            @transition("go")
            async def handle_go(self, *args, **kwargs):
                return TransitionResult(True)

        s = MyState("async_s")
        assert "go" in s._handlers
        assert s._handlers["go"]["is_async"] is True

    @pytest.mark.asyncio
    async def test_handle_event_async(self):
        class MyState(AsyncDeclarativeState):
            @transition("go")
            async def handle_go(self, *args, **kwargs):
                return TransitionResult(True)

        s = MyState("async_s")
        result = await s.handle_event_async("go")
        assert result.success

    @pytest.mark.asyncio
    async def test_handle_event_async_with_sync_handler(self):
        class MyState(AsyncDeclarativeState):
            @transition("sync_op")
            def handle_sync_op(self, *args, **kwargs):
                return TransitionResult(True)

        s = MyState("mixed_s")
        result = await s.handle_event_async("sync_op")
        assert result.success

    @pytest.mark.asyncio
    @pytest.mark.xfail(
        reason="GH#5 / fast_fsm-xfm: can_transition_async double-evaluates "
        "condition — parent sync path rejects AsyncCondition",
        strict=True,
    )
    async def test_can_transition_async_with_async_condition(self):
        cond = SimpleAsyncCondition()

        class MyState(AsyncDeclarativeState):
            @transition("go", condition=cond)
            async def handle_go(self, *args, **kwargs):
                return True

        s = MyState("s")
        assert await s.can_transition_async("go", State("target"))


# ---------------------------------------------------------------------------
# @transition decorator metadata
# ---------------------------------------------------------------------------


class TestTransitionDecorator:
    def test_sets_trigger(self):
        @transition("my_trigger")
        def handler():
            pass

        assert handler._fsm_trigger == "my_trigger"

    def test_sets_from_state(self):
        @transition("t", from_state="idle")
        def handler():
            pass

        assert handler._fsm_from_state == "idle"

    def test_sets_to_state(self):
        @transition("t", to_state="running")
        def handler():
            pass

        assert handler._fsm_to_state == "running"

    def test_sets_condition(self):
        cond = AlwaysTrue()

        @transition("t", condition=cond)
        def handler():
            pass

        assert handler._fsm_condition is cond

    def test_defaults_are_none(self):
        @transition("t")
        def handler():
            pass

        assert handler._fsm_from_state is None
        assert handler._fsm_to_state is None
        assert handler._fsm_condition is None


# ---------------------------------------------------------------------------
# condition_builder decorator
# ---------------------------------------------------------------------------


class TestConditionBuilder:
    def test_creates_func_condition(self):
        @condition_builder(name="fuel_check", description="Check fuel level")
        def has_fuel(level=0, **kwargs):
            return level > 0

        assert isinstance(has_fuel, FuncCondition)
        assert has_fuel.name == "fuel_check"
        assert has_fuel.check(level=10) is True
        assert has_fuel.check(level=0) is False

    def test_default_name_from_function(self):
        @condition_builder
        def my_condition(**kwargs):
            return True

        assert isinstance(my_condition, FuncCondition)
        assert my_condition.name == "my_condition"

    def test_used_in_fsm(self):
        @condition_builder(name="ready_check")
        def is_ready(ready=False, **kwargs):
            return ready

        fsm = StateMachine(State("waiting"), name="cb_fsm")
        fsm.add_state(State("active"))
        fsm.add_transition("activate", "waiting", "active", is_ready)

        assert not fsm.trigger("activate").success
        assert fsm.trigger("activate", ready=True).success


# ---------------------------------------------------------------------------
# Convenience functions: quick_fsm, simple_fsm
# ---------------------------------------------------------------------------


class TestConvenienceFunctions:
    def test_quick_fsm(self):
        fsm = quick_fsm(
            "idle",
            [("start", "idle", "running"), ("stop", "running", "idle")],
            name="quick",
        )
        assert isinstance(fsm, StateMachine)
        assert fsm.current_state.name == "idle"
        assert fsm.trigger("start").success
        assert fsm.trigger("stop").success
        assert fsm.current_state.name == "idle"

    def test_simple_fsm(self):
        fsm = simple_fsm("a", "b", "c", initial="a", name="simple")
        assert isinstance(fsm, StateMachine)
        assert fsm.current_state.name == "a"
        assert set(fsm.states) == {"a", "b", "c"}

    def test_simple_fsm_default_initial(self):
        fsm = simple_fsm("first", "second")
        assert fsm.current_state.name == "first"

    def test_quick_fsm_creates_states_from_transitions(self):
        fsm = quick_fsm("s1", [("go", "s1", "s2"), ("back", "s2", "s1")])
        assert "s1" in fsm.states
        assert "s2" in fsm.states
