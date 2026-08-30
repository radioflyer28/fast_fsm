"""
Tests for FSMBuilder, DeclarativeState, AsyncDeclarativeState,
@transition decorator, condition_builder, quick_fsm, and simple_fsm.

All tests use real components — no mocking.
"""

import pytest

from fast_fsm.condition_templates import AndCondition, NotCondition, OrCondition
from fast_fsm.conditions import (
    AsyncCondition,
    Condition,
    FuncCondition,
    NegatedCondition,
)
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


class ConfigurableAsyncCondition(AsyncCondition):
    """Async condition with configurable result for gap tests."""

    def __init__(self, result: bool = True):
        super().__init__("configurable_async", "configurable async")
        self._result = result

    async def check_async(self, **kwargs) -> bool:
        return self._result


class ExplodingCondition(Condition):
    """Condition that raises an exception on check."""

    def __init__(self):
        super().__init__("exploding", "always explodes")

    def check(self, **kwargs) -> bool:
        raise RuntimeError("condition exploded")


class ExplodingAsyncCondition(AsyncCondition):
    """Async condition that raises an exception."""

    def __init__(self):
        super().__init__("exploding_async", "explodes asynchronously")

    async def check_async(self, **kwargs) -> bool:
        raise RuntimeError("async boom")


class DeclarativeInvocationCounter(DeclarativeState):
    """Test-only declarative state that records ordinary-dispatch invocations."""

    def __init__(self, name: str = "source", result=None):
        super().__init__(name)
        self.invocations = 0
        self._result = result

    @transition("advance", from_state="source", to_state="target")
    def handle_advance(self, *args, **kwargs):
        self.invocations += 1
        if self._result == "raise":
            raise RuntimeError("phase 17 owns handler failure semantics")
        return self._result

    @transition("前進⚡", from_state="source", to_state="target")
    def handle_unicode_advance(self, *args, **kwargs):
        self.invocations += 1
        return self._result


def _invoke_and_ignore_phase17_outcome(invoker):
    """Exercise a handler without fixing Phase 17 lifecycle outcomes in this phase."""
    try:
        invoker()
    except Exception:
        pass


def _machine_topology_fingerprint(machine):
    """Capture the identity-bearing topology that a builder publishes."""
    return (
        machine._graph_version,
        tuple((name, id(state)) for name, state in machine._states.items()),
        tuple(
            (source, trigger, id(entry.to_state), id(entry.condition))
            for source, entries in machine._transitions.items()
            for trigger, entry in entries.items()
        ),
    )


def builder_staging_fingerprint(builder):
    """Capture builder staging and any published topology without mutating it."""
    machine = builder._machine
    return (
        tuple((name, id(state)) for name, state in builder._states.items()),
        tuple(
            (
                trigger,
                tuple(from_state) if isinstance(from_state, list) else from_state,
                to_state,
                id(condition),
            )
            for trigger, from_state, to_state, condition in builder._transitions
        ),
        tuple(
            (state_name, id(callback))
            for state_name, callback in builder._enter_callbacks
        ),
        tuple(
            (state_name, id(callback))
            for state_name, callback in builder._exit_callbacks
        ),
        tuple(
            (state_name, id(callback))
            for state_name, callback in builder._enter_async_callbacks
        ),
        tuple(
            (state_name, id(callback))
            for state_name, callback in builder._exit_async_callbacks
        ),
        builder._machine_type,
        builder._auto_detect,
        id(machine) if machine is not None else None,
        _machine_topology_fingerprint(machine) if machine is not None else None,
    )


def _make_supported_wrapper_cycle(shape):
    """Build one private supported-wrapper cycle for builder rejection tests."""
    if shape == "negated":
        condition = NegatedCondition(AlwaysTrue())
        condition._inner = condition
    elif shape == "and":
        condition = AndCondition(AlwaysTrue())
        condition.conditions = (condition,)
    elif shape == "or":
        condition = OrCondition(AlwaysTrue())
        condition.conditions = (condition,)
    else:
        condition = NotCondition(AlwaysTrue())
        condition.condition = condition
    return condition


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


class TestOrdinaryDeclarativeDispatch:
    """Ordinary machine dispatch shares one declarative invocation boundary."""

    @staticmethod
    def _machine(source, target_name="target"):
        target = State(target_name)
        fsm = StateMachine(source, name="ordinary_declarative")
        fsm.add_state(target)
        fsm.add_transition("advance", source, target)
        return fsm

    def test_declarative_ordinary_exactly_once(self):
        source = DeclarativeInvocationCounter(result=None)
        fsm = self._machine(source)

        result = fsm.trigger("advance")

        assert result.success
        assert source.invocations == 1

    @pytest.mark.parametrize("handler_result", [None, True, TransitionResult(True)])
    def test_declarative_ordinary_success_normalization_parity(self, handler_result):
        source = DeclarativeInvocationCounter(result=handler_result)
        fsm = self._machine(source)

        result = fsm.trigger("advance")

        assert result.success
        assert source.invocations == 1

    def test_declarative_ordinary_matches_unicode_canonical_metadata(self):
        source = DeclarativeInvocationCounter(result=True)
        target = State("target")
        fsm = StateMachine(source, name="unicode_declarative")
        fsm.add_state(target)
        fsm.add_transition("前進⚡", source, target)

        result = fsm.trigger("前進⚡")

        assert result.success
        assert source.invocations == 1

    def test_declarative_ordinary_ignores_nonmatching_source_metadata(self):
        source = DeclarativeInvocationCounter(name="wrong_source", result=True)
        fsm = self._machine(source)

        fsm.trigger("advance")

        assert source.invocations == 0

    def test_declarative_ordinary_ignores_nonmatching_target_metadata(self):
        source = DeclarativeInvocationCounter(result=True)
        fsm = self._machine(source, target_name="wrong_target")

        fsm.trigger("advance")

        assert source.invocations == 0

    def test_declarative_ordinary_unknown_trigger_has_no_side_effect(self):
        source = DeclarativeInvocationCounter(result=True)
        fsm = self._machine(source)

        fsm.trigger("missing")

        assert source.invocations == 0

    def test_declarative_handle_event_uses_the_same_handler_boundary(self):
        source = DeclarativeInvocationCounter(result=True)

        result = source.handle_event("advance")

        assert result.success
        assert source.invocations == 1

    @pytest.mark.parametrize("handler_result", [False, "invalid", "raise"])
    def test_declarative_ordinary_invocation_only_for_phase17_outcomes(
        self, handler_result
    ):
        source = DeclarativeInvocationCounter(result=handler_result)
        fsm = self._machine(source)

        _invoke_and_ignore_phase17_outcome(lambda: fsm.trigger("advance"))

        assert source.invocations == 1


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
    async def test_can_transition_async_with_async_condition(self):
        """Regression test for GH#5 / fast_fsm-xfm: can_transition_async
        previously double-evaluated the condition via the parent sync path,
        which rejected AsyncCondition."""
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

    def test_quick_build_preserves_state_object_initial(self):
        """The lower-level factory preserves an explicitly supplied initial State."""

        initial = State("idle")
        fsm = StateMachine.quick_build(initial, [("start", "idle", "running")])

        assert fsm.current_state is initial
        assert fsm._states["idle"] is initial

    def test_quick_build_preserves_custom_state_supplied_in_states(self):
        """Convenience construction retains a supplied state callback object."""

        entered = []

        class CallbackState(State):
            def on_enter(self, from_state, trigger, *args, **kwargs):
                entered.append((from_state, trigger))

        target = CallbackState("target")
        fsm = StateMachine.quick_build(
            "initial",
            [("go", "initial", "target")],
            states=[target],
        )

        assert fsm._states["target"] is target
        assert fsm.trigger("go").success
        assert entered == [(fsm._states["initial"], "go")]

    def test_quick_build_uses_identity_when_states_compare_equal(self):
        """Equal-comparing state subclasses never cause a canonical state skip."""

        class EqualState(State):
            def __eq__(self, other):
                return isinstance(other, State)

        initial = EqualState("initial")
        target = EqualState("target")
        fsm = StateMachine.quick_build(
            initial,
            [("go", "initial", "target")],
            states=[target],
        )

        assert fsm._states["initial"] is initial
        assert fsm._states["target"] is target
        assert fsm.trigger("go").success

    def test_quick_build_rejects_different_objects_with_the_same_name(self):
        """Name collisions do not silently discard one supplied State object."""

        first = State("target")
        second = State("target")

        with pytest.raises(ValueError, match="different objects"):
            StateMachine.quick_build(
                State("initial"),
                [("go", "initial", "target")],
                states=[first, second],
            )

    def test_quick_build_preserves_state_objects_in_transition_endpoints(self):
        """Object endpoints, including list sources, retain their exact identities."""

        initial = State("initial")
        middle = State("middle")
        target = State("target")
        fsm = StateMachine.quick_build(
            initial,
            [("advance", [initial, middle], target)],
        )

        assert fsm._states["initial"] is initial
        assert fsm._states["middle"] is middle
        assert fsm._states["target"] is target
        assert fsm.trigger("advance").success

    @pytest.mark.parametrize("invalid_endpoint", [None, 1])
    def test_quick_build_rejects_non_state_endpoint_values(self, invalid_endpoint):
        with pytest.raises(TypeError):
            StateMachine.quick_build("initial", [("go", invalid_endpoint, "target")])

    @pytest.mark.parametrize("invalid_state", [None, 1])
    def test_quick_build_rejects_non_state_entries(self, invalid_state):
        with pytest.raises(TypeError):
            StateMachine.quick_build("initial", [], states=[invalid_state])


# ---------------------------------------------------------------------------
# DeclarativeState gap coverage
# ---------------------------------------------------------------------------


class TestDeclarativeStateGaps:
    """Cover uncovered paths in DeclarativeState."""

    def test_can_transition_async_condition_in_sync_context(self):
        """AsyncCondition on a sync DeclarativeState — should warn and return False."""

        class MyState(DeclarativeState):
            @transition("go", condition=SimpleAsyncCondition())
            def handle_go(self, *args, **kwargs):
                return True

        s = MyState("s1")
        assert not s.can_transition("go", State("target"))

    def test_can_transition_callable_condition(self):
        """Callable condition (not Condition subclass) works in can_transition."""

        class MyState(DeclarativeState):
            @transition("go", condition=lambda *a, **kw: True)
            def handle_go(self, *args, **kwargs):
                return True

        s = MyState("s1")
        assert s.can_transition("go", State("target"))

    def test_sync_policy_rejects_coroutine_returning_callable_without_warning(
        self, recwarn
    ):
        """Sync direct policies close an accidental coroutine-returning guard."""

        def guard(*args, **kwargs):
            async def pending():
                return True

            return pending()

        class MyState(DeclarativeState):
            @transition("go", condition=guard)
            def handle_go(self, *args, **kwargs):
                return True

        assert not MyState("source").can_transition("go", State("target"))
        assert not any(
            issubclass(warning.category, RuntimeWarning) for warning in recwarn
        )

    def test_sync_policy_rejects_async_callable_without_runtime_warning(self, recwarn):
        """Direct sync policies reject coroutine functions before invoking them."""

        async def guard(*args, **kwargs):
            return True

        class MyState(DeclarativeState):
            @transition("go", condition=guard)
            def handle_go(self, *args, **kwargs):
                return True

        assert not MyState("source").can_transition("go", State("target"))
        assert not any(
            issubclass(warning.category, RuntimeWarning) for warning in recwarn
        )

    def test_can_transition_truthy_non_callable_condition(self):
        """A truthy non-callable condition evaluates via bool()."""

        class MyState(DeclarativeState):
            @transition("go", condition="truthy_string")
            def handle_go(self, *args, **kwargs):
                return True

        s = MyState("s1")
        assert s.can_transition("go", State("target"))

    def test_can_transition_condition_exception(self):
        """Exception during condition evaluation returns False."""

        class MyState(DeclarativeState):
            @transition("go", condition=ExplodingCondition())
            def handle_go(self, *args, **kwargs):
                return True

        s = MyState("s1")
        assert not s.can_transition("go", State("target"))

    def test_handle_event_async_handler_in_sync_context(self):
        """Async handler in sync DeclarativeState — should fail with error."""

        class MyState(DeclarativeState):
            @transition("go")
            async def handle_go(self, *args, **kwargs):
                return TransitionResult(True)

        s = MyState("s1")
        result = s.handle_event("go")
        assert not result.success
        assert result.error is not None
        assert "sync context" in result.error.lower() or "Async" in result.error

    def test_handle_event_invalid_return_type(self):
        """Handler returning non-bool, non-TransitionResult, non-None gets wrapped."""

        class MyState(DeclarativeState):
            @transition("go")
            def handle_go(self, *args, **kwargs):
                return "unexpected_string"

        s = MyState("s1")
        result = s.handle_event("go")
        assert result.success
        assert "Invalid return type" in (result.error or "")

    def test_handle_event_failure_result(self):
        """Handler returning TransitionResult(False) logs as failure."""

        class MyState(DeclarativeState):
            @transition("go")
            def handle_go(self, *args, **kwargs):
                return TransitionResult(False, error="intentional failure")

        s = MyState("s1")
        result = s.handle_event("go")
        assert not result.success
        assert result.error is not None
        assert "intentional failure" in result.error


# ---------------------------------------------------------------------------
# AsyncDeclarativeState gap coverage
# ---------------------------------------------------------------------------


class TestAsyncDeclarativeStateGaps:
    """Cover uncovered paths in AsyncDeclarativeState."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "factory",
        (
            lambda: NegatedCondition(ConfigurableAsyncCondition(result=False)),
            lambda: NotCondition(ConfigurableAsyncCondition(result=False)),
            lambda: AndCondition(AlwaysTrue(), ConfigurableAsyncCondition(result=True)),
            lambda: OrCondition(AlwaysFalse(), ConfigurableAsyncCondition(result=True)),
        ),
    )
    async def test_direct_async_policy_awaits_supported_async_wrappers(
        self, factory, recwarn
    ):
        """Direct async state policies use the machine's wrapper evaluator."""

        class MyState(AsyncDeclarativeState):
            @transition("go", condition=factory())
            async def handle_go(self, *args, **kwargs):
                return True

        state = MyState("source")

        assert await state.can_transition_async("go", State("target"))
        assert not any(
            issubclass(warning.category, RuntimeWarning) for warning in recwarn
        )

    @pytest.mark.asyncio
    async def test_direct_async_policy_awaits_async_func_condition(self, recwarn):
        """FuncCondition leaves returning coroutines are awaited directly."""

        async def guard(*args, **kwargs):
            return True

        class MyState(AsyncDeclarativeState):
            @transition("go", condition=FuncCondition(guard))
            async def handle_go(self, *args, **kwargs):
                return True

        state = MyState("source")

        assert await state.can_transition_async("go", State("target"))
        assert not any(
            issubclass(warning.category, RuntimeWarning) for warning in recwarn
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("outcome", ("reject", "raise", "awaitable"))
    async def test_direct_async_policy_honors_func_condition_subclass_check(
        self, outcome, recwarn
    ):
        """Public FuncCondition subclasses retain their effective check hook."""

        class OverridingFuncCondition(FuncCondition):
            def __init__(self):
                super().__init__(lambda *args, **kwargs: True)
                self.calls = 0

            def check(self, *args, **kwargs):
                self.calls += 1
                if outcome == "reject":
                    return False
                if outcome == "raise":
                    raise RuntimeError("subclass guard boom")

                async def allow():
                    return True

                return allow()

        condition = OverridingFuncCondition()

        class MyState(AsyncDeclarativeState):
            @transition("go", condition=condition)
            async def handle_go(self, *args, **kwargs):
                return True

        result = await MyState("source").can_transition_async("go", State("target"))

        assert result is (outcome == "awaitable")
        assert condition.calls == 1
        assert not any(
            issubclass(warning.category, RuntimeWarning) for warning in recwarn
        )

    @pytest.mark.asyncio
    async def test_direct_async_policy_awaits_async_callable_condition(self, recwarn):
        """Raw async decorator callables are awaited by direct policies too."""

        async def guard(*args, **kwargs):
            return True

        class MyState(AsyncDeclarativeState):
            @transition("go", condition=guard)
            async def handle_go(self, *args, **kwargs):
                return True

        assert await MyState("source").can_transition_async("go", State("target"))
        assert not any(
            issubclass(warning.category, RuntimeWarning) for warning in recwarn
        )

    @pytest.mark.asyncio
    async def test_can_transition_async_with_async_condition_pass(self):
        cond = ConfigurableAsyncCondition(result=True)

        class MyState(AsyncDeclarativeState):
            @transition("go", condition=cond)
            async def handle_go(self, *args, **kwargs):
                return True

        s = MyState("s1")
        assert await s.can_transition_async("go", State("target"))

    @pytest.mark.asyncio
    async def test_can_transition_async_with_async_condition_fail(self):
        cond = ConfigurableAsyncCondition(result=False)

        class MyState(AsyncDeclarativeState):
            @transition("go", condition=cond)
            async def handle_go(self, *args, **kwargs):
                return True

        s = MyState("s1")
        assert not await s.can_transition_async("go", State("target"))

    @pytest.mark.asyncio
    async def test_can_transition_async_with_sync_condition(self):
        cond = AlwaysTrue()

        class MyState(AsyncDeclarativeState):
            @transition("go", condition=cond)
            async def handle_go(self, *args, **kwargs):
                return True

        s = MyState("s1")
        assert await s.can_transition_async("go", State("target"))

    @pytest.mark.asyncio
    async def test_can_transition_async_callable_condition(self):
        class MyState(AsyncDeclarativeState):
            @transition("go", condition=lambda *a, **kw: True)
            async def handle_go(self, *args, **kwargs):
                return True

        s = MyState("s1")
        assert await s.can_transition_async("go", State("target"))

    @pytest.mark.asyncio
    async def test_can_transition_async_truthy_non_callable(self):
        class MyState(AsyncDeclarativeState):
            @transition("go", condition="truthy")
            async def handle_go(self, *args, **kwargs):
                return True

        s = MyState("s1")
        assert await s.can_transition_async("go", State("target"))

    @pytest.mark.asyncio
    async def test_can_transition_async_condition_exception(self):
        class MyState(AsyncDeclarativeState):
            @transition("go", condition=ExplodingAsyncCondition())
            async def handle_go(self, *args, **kwargs):
                return True

        s = MyState("s1")
        assert not await s.can_transition_async("go", State("target"))

    @pytest.mark.asyncio
    async def test_handle_event_async_returns_none(self):
        class MyState(AsyncDeclarativeState):
            @transition("go")
            async def handle_go(self, *args, **kwargs):
                pass

        s = MyState("s1")
        result = await s.handle_event_async("go")
        assert result.success

    @pytest.mark.asyncio
    async def test_handle_event_async_returns_bool(self):
        class MyState(AsyncDeclarativeState):
            @transition("go")
            async def handle_go(self, *args, **kwargs):
                return False

        s = MyState("s1")
        result = await s.handle_event_async("go")
        assert not result.success

    @pytest.mark.asyncio
    async def test_handle_event_async_exception(self):
        class MyState(AsyncDeclarativeState):
            @transition("go")
            async def handle_go(self, *args, **kwargs):
                raise ValueError("async handler boom")

        s = MyState("s1")
        result = await s.handle_event_async("go")
        assert not result.success
        assert result.error is not None
        assert "async handler boom" in result.error

    @pytest.mark.asyncio
    async def test_handle_event_async_failure_result(self):
        class MyState(AsyncDeclarativeState):
            @transition("go")
            async def handle_go(self, *args, **kwargs):
                return TransitionResult(False, error="async fail")

        s = MyState("s1")
        result = await s.handle_event_async("go")
        assert not result.success
        assert result.error is not None
        assert "async fail" in result.error

    @pytest.mark.asyncio
    async def test_handle_event_async_unknown_falls_through(self):
        class MyState(AsyncDeclarativeState):
            pass

        s = MyState("s1")
        result = await s.handle_event_async("unknown")
        assert isinstance(result, TransitionResult)


class TestDeclarativePolicyCompatibility:
    """Ordinary dispatch must retain the effective subclass policy hook."""

    @pytest.mark.parametrize("policy", ("reject", "raise", "super"))
    def test_sync_policy_override_runs_once_after_prepared_guard(self, policy):
        guard_calls = []

        def guard(*args, **kwargs):
            guard_calls.append((args, kwargs))
            return True

        class PolicyState(DeclarativeState):
            def __init__(self, name):
                super().__init__(name)
                self.policy_calls = 0

            @transition("go", from_state="source", to_state="target", condition=guard)
            def handle_go(self, *args, **kwargs):
                return True

            def can_transition(self, trigger, to_state, *args, **kwargs):
                self.policy_calls += 1
                if policy == "reject":
                    return False
                if policy == "raise":
                    raise RuntimeError("sync policy boom")
                return super().can_transition(trigger, to_state, *args, **kwargs)

        source = PolicyState("source")
        target = State("target")
        machine = StateMachine(source)
        machine.add_state(target)
        machine.add_transition("go", source, target)

        if policy == "raise":
            with pytest.raises(RuntimeError, match="sync policy boom"):
                machine.can_trigger("go")
            with pytest.raises(RuntimeError, match="sync policy boom"):
                machine.trigger("go")
        else:
            expected = policy == "super"
            assert machine.can_trigger("go") is expected
            assert machine.trigger("go").success is expected

        assert source.policy_calls == 2
        assert len(guard_calls) == 2

    @pytest.mark.asyncio
    @pytest.mark.parametrize("policy", ("reject", "raise", "super"))
    async def test_async_policy_override_runs_once_after_prepared_guard(self, policy):
        guard_calls = []

        def guard(*args, **kwargs):
            guard_calls.append((args, kwargs))
            return True

        class PolicyState(AsyncDeclarativeState):
            def __init__(self, name):
                super().__init__(name)
                self.policy_calls = 0

            @transition("go", from_state="source", to_state="target", condition=guard)
            async def handle_go(self, *args, **kwargs):
                return True

            async def can_transition_async(self, trigger, to_state, *args, **kwargs):
                self.policy_calls += 1
                if policy == "reject":
                    return False
                if policy == "raise":
                    raise RuntimeError("async policy boom")
                return await super().can_transition_async(
                    trigger, to_state, *args, **kwargs
                )

        source = PolicyState("source")
        target = State("target")
        machine = AsyncStateMachine(source)
        machine.add_state(target)
        machine.add_transition("go", source, target)

        if policy == "raise":
            with pytest.raises(RuntimeError, match="async policy boom"):
                await machine.can_trigger_async("go")
            with pytest.raises(RuntimeError, match="async policy boom"):
                await machine.trigger_async("go")
        else:
            expected = policy == "super"
            assert await machine.can_trigger_async("go") is expected
            assert (await machine.trigger_async("go")).success is expected

        assert source.policy_calls == 2
        assert len(guard_calls) == 2


# ---------------------------------------------------------------------------
# FSMBuilder gap coverage
# ---------------------------------------------------------------------------


class TestFSMBuilderGaps:
    """Cover uncovered FSMBuilder paths."""

    def test_auto_detects_async_declarative_callable_guard(self):
        """A decorator's raw async callable upgrades an auto-detected builder."""

        async def guard(*args, **kwargs):
            return True

        class MyState(DeclarativeState):
            @transition("go", condition=guard)
            def handle_go(self, *args, **kwargs):
                return True

        builder = FSMBuilder(MyState("source"))

        assert builder.machine_type is AsyncStateMachine
        assert builder.is_async

    def test_unless_rejects_non_guard_value_before_staging(self):
        """Builder shorthand validates invalid guards before mutating staging."""

        builder = FSMBuilder(State("source"))

        with pytest.raises(TypeError, match="'unless' must be a Condition or callable"):
            builder.add_transition("go", "source", "target", unless="not-a-guard")

        assert builder._transitions == []

    def test_force_sync_with_async_state_rejects_at_build(self):
        builder = FSMBuilder(AsyncDeclarativeState("async_s"))
        builder.force_sync()
        with pytest.raises(RuntimeError, match="explicit sync.*AsyncDeclarativeState"):
            builder.build()

    def test_force_sync_with_async_condition_raises_at_build(self):
        """After force_sync(), preflight must reject AsyncCondition before build."""
        builder = FSMBuilder(State("a"))
        builder.add_state(State("b"))
        builder.add_transition("go", "a", "b", SimpleAsyncCondition())
        builder.force_sync()
        with pytest.raises(RuntimeError, match="explicit sync.*condition"):
            builder.build()

    def test_add_state_explicit_sync_rejects_async_state_at_build(self):
        builder = FSMBuilder(State("a"), async_mode=False)
        builder.add_state(AsyncDeclarativeState("async_s"))
        assert not builder.is_async
        with pytest.raises(RuntimeError, match="explicit sync.*AsyncDeclarativeState"):
            builder.build()

    def test_add_transition_explicit_sync_rejects_async_condition_at_build(self):
        builder = FSMBuilder(State("a"), async_mode=False)
        builder.add_state(State("b"))
        builder.add_transition("go", "a", "b", SimpleAsyncCondition())
        assert not builder.is_async
        with pytest.raises(RuntimeError, match="explicit sync.*condition"):
            builder.build()

    def test_build_with_list_from_state(self):
        a = State("a")
        b = State("b")
        c = State("c")
        builder = FSMBuilder(a)
        builder.add_state(b)
        builder.add_state(c)
        builder.add_transition("go", ["a", "b"], "c")
        fsm = builder.build()
        assert fsm.trigger("go").success
        assert fsm.current_state.name == "c"

    def test_build_returns_cached_machine(self):
        builder = FSMBuilder(State("a"))
        fsm1 = builder.build()
        fsm2 = builder.build()
        assert fsm1 is fsm2

    def test_auto_detect_async_from_declarative_handlers(self):
        class MyState(DeclarativeState):
            @transition("go", condition=SimpleAsyncCondition())
            def handle_go(self, *args, **kwargs):
                return True

        builder = FSMBuilder(MyState("s"))
        assert builder.is_async

    def test_auto_detect_async_from_async_handlers(self):
        class MyState(DeclarativeState):
            @transition("go")
            async def handle_go(self, *args, **kwargs):
                return True

        builder = FSMBuilder(MyState("s"))
        assert builder.is_async


# ---------------------------------------------------------------------------
# FSMBuilder fluent callback registration  (fast_fsm-ker)
# ---------------------------------------------------------------------------


class TestFSMBuilderCallbacks:
    """Tests for FSMBuilder.on_enter / on_exit / on_enter_async / on_exit_async."""

    def _two_state_builder(self, **builder_kwargs) -> FSMBuilder:
        a = State("a")
        b = State("b")
        builder = FSMBuilder(a, **builder_kwargs)
        builder.add_state(b)
        builder.add_transition("go", "a", "b")
        builder.add_transition("back", "b", "a")
        return builder

    # ---- return-self / chaining ------------------------------------------------

    def test_on_enter_returns_self(self):
        builder = self._two_state_builder()
        result = builder.on_enter("b", lambda *a, **k: None)
        assert result is builder

    def test_on_exit_returns_self(self):
        builder = self._two_state_builder()
        result = builder.on_exit("a", lambda *a, **k: None)
        assert result is builder

    def test_on_enter_async_returns_self(self):
        async def cb(*a, **k):
            pass

        builder = self._two_state_builder()
        result = builder.on_enter_async("b", cb)
        assert result is builder

    def test_on_exit_async_returns_self(self):
        async def cb(*a, **k):
            pass

        builder = self._two_state_builder()
        result = builder.on_exit_async("a", cb)
        assert result is builder

    def test_fluent_chaining(self):
        a = State("a")
        b = State("b")
        calls = []
        fsm = (
            FSMBuilder(a)
            .add_state(b)
            .add_transition("go", "a", "b")
            .on_enter("b", lambda *a, **k: calls.append("enter_b"))
            .on_exit("a", lambda *a, **k: calls.append("exit_a"))
            .build()
        )
        fsm.trigger("go")
        assert "enter_b" in calls
        assert "exit_a" in calls

    # ---- sync callbacks fire ---------------------------------------------------

    def test_on_enter_fires(self):
        calls = []
        builder = self._two_state_builder()
        builder.on_enter(
            "b", lambda from_s, trigger, **k: calls.append((from_s.name, trigger))
        )
        fsm = builder.build()
        fsm.trigger("go")
        assert calls == [("a", "go")]

    def test_on_exit_fires(self):
        calls = []
        builder = self._two_state_builder()
        builder.on_exit(
            "a", lambda to_s, trigger, **k: calls.append((to_s.name, trigger))
        )
        fsm = builder.build()
        fsm.trigger("go")
        assert calls == [("b", "go")]

    def test_on_enter_not_visited_does_not_fire(self):
        calls = []
        builder = self._two_state_builder()
        builder.on_enter("b", lambda *a, **k: calls.append(1))
        builder.build()  # never trigger
        assert calls == []

    def test_multiple_on_enter_callbacks_fire_in_order(self):
        calls = []
        builder = self._two_state_builder()
        builder.on_enter("b", lambda *a, **k: calls.append(1))
        builder.on_enter("b", lambda *a, **k: calls.append(2))
        builder.on_enter("b", lambda *a, **k: calls.append(3))
        fsm = builder.build()
        fsm.trigger("go")
        assert calls == [1, 2, 3]

    def test_on_enter_and_on_exit_each_fire_once_per_transition(self):
        enter_calls = []
        exit_calls = []
        builder = self._two_state_builder()
        builder.on_enter("b", lambda *a, **k: enter_calls.append(1))
        builder.on_exit("a", lambda *a, **k: exit_calls.append(1))
        fsm = builder.build()
        fsm.trigger("go")
        fsm.trigger("back")
        fsm.trigger("go")
        assert len(enter_calls) == 2  # fired on each entry to b
        assert len(exit_calls) == 2  # fired on each exit from a

    # ---- async auto-upgrade ----------------------------------------------------

    def test_on_enter_async_upgrades_to_async_machine(self):
        async def cb(*a, **k):
            pass

        builder = self._two_state_builder()
        assert not builder.is_async
        builder.on_enter_async("b", cb)
        assert builder.is_async

    def test_on_exit_async_upgrades_to_async_machine(self):
        async def cb(*a, **k):
            pass

        builder = self._two_state_builder()
        assert not builder.is_async
        builder.on_exit_async("a", cb)
        assert builder.is_async

    def test_on_enter_async_does_not_downgrade_explicit_async(self):
        async def cb(*a, **k):
            pass

        builder = self._two_state_builder(async_mode=True)
        builder.on_enter_async("b", cb)
        assert isinstance(builder.build(), AsyncStateMachine)

    # ---- async callbacks fire --------------------------------------------------

    @pytest.mark.asyncio
    async def test_on_enter_async_fires(self):
        calls = []

        async def cb(from_s, trigger, **k):
            calls.append((from_s.name, trigger))

        builder = self._two_state_builder()
        builder.on_enter_async("b", cb)
        fsm = builder.build()
        assert isinstance(fsm, AsyncStateMachine)
        await fsm.trigger_async("go")
        assert calls == [("a", "go")]

    @pytest.mark.asyncio
    async def test_on_exit_async_fires(self):
        calls = []

        async def cb(to_s, trigger, **k):
            calls.append((to_s.name, trigger))

        builder = self._two_state_builder()
        builder.on_exit_async("a", cb)
        fsm = builder.build()
        assert isinstance(fsm, AsyncStateMachine)
        await fsm.trigger_async("go")
        assert calls == [("b", "go")]

    @pytest.mark.asyncio
    async def test_async_and_sync_callbacks_both_fire(self):
        sync_calls = []
        async_calls = []

        async def async_cb(*a, **k):
            async_calls.append(1)

        builder = self._two_state_builder()
        builder.on_enter("b", lambda *a, **k: sync_calls.append(1))
        builder.on_enter_async("b", async_cb)
        fsm = builder.build()
        await fsm.trigger_async("go")
        assert sync_calls == [1]
        assert async_calls == [1]

    # ---- async callbacks reject explicit sync machine --------------------------

    def test_async_callbacks_rejected_on_explicit_sync(self):
        async def cb(*a, **k):
            pass

        builder = self._two_state_builder(async_mode=False)
        builder.on_enter_async("b", cb)
        with pytest.raises(RuntimeError, match="explicit sync.*async callback"):
            builder.build()


# ---------------------------------------------------------------------------
# FSMBuilder publication transaction
# ---------------------------------------------------------------------------


class TestFSMBuilderPublication:
    """D-09/D-10 builder staging, cache, and publication behavior."""

    @staticmethod
    def _builder():
        builder = FSMBuilder(State("start"), name="publication")
        builder.add_state(State("finish"))
        builder.add_transition("go", "start", "finish")
        return builder

    @pytest.mark.parametrize(
        "mutator",
        (
            "add_state",
            "add_transition",
            "on_enter",
            "on_exit",
            "on_enter_async",
            "on_exit_async",
            "force_async",
            "force_sync",
        ),
    )
    def test_every_builder_mutator_freezes_after_success(self, mutator):
        builder = self._builder()
        builder.build()
        before = builder_staging_fingerprint(builder)

        async def async_callback(*args, **kwargs):
            pass

        operations = {
            "add_state": lambda: builder.add_state(State("later")),
            "add_transition": lambda: builder.add_transition(
                "later", "start", "finish"
            ),
            "on_enter": lambda: builder.on_enter(
                "finish", lambda *args, **kwargs: None
            ),
            "on_exit": lambda: builder.on_exit("start", lambda *args, **kwargs: None),
            "on_enter_async": lambda: builder.on_enter_async("finish", async_callback),
            "on_exit_async": lambda: builder.on_exit_async("start", async_callback),
            "force_async": builder.force_async,
            "force_sync": builder.force_sync,
        }

        with pytest.raises(RuntimeError, match="Cannot mutate builder"):
            operations[mutator]()

        assert builder_staging_fingerprint(builder) == before

    def test_same_object_staging_is_idempotent_and_same_name_rejection_is_atomic(self):
        initial = State("同じ")
        builder = FSMBuilder(initial)
        before = builder_staging_fingerprint(builder)

        assert builder.add_state(initial) is builder
        assert builder_staging_fingerprint(builder) == before

        with pytest.raises(ValueError, match="different State object"):
            builder.add_state(State("同じ"))

        assert builder_staging_fingerprint(builder) == before
        machine = builder.build()
        assert _machine_topology_fingerprint(machine) == (
            machine._graph_version,
            (("同じ", id(initial)),),
            (),
        )

    def test_publication_uses_identity_when_states_compare_equal(self):
        """Distinct state objects remain distinct despite custom equality."""

        class EqualComparingState(State):
            def __eq__(self, other: object) -> bool:
                return isinstance(other, State)

        initial = EqualComparingState("initial")
        distinct = EqualComparingState("distinct")
        same_name = EqualComparingState("initial")

        assert initial == distinct
        builder = FSMBuilder(initial)
        builder.add_state(distinct)

        with pytest.raises(ValueError, match="different State object"):
            builder.add_state(same_name)

        machine = builder.build()
        assert machine._states == {"initial": initial, "distinct": distinct}
        assert machine._states["initial"] is initial
        assert machine._states["distinct"] is distinct

    def test_invalid_initial_or_staged_state_is_rejected_before_materialization(self):
        with pytest.raises(TypeError):
            FSMBuilder(None)

        builder = FSMBuilder(State("valid"))
        before = builder_staging_fingerprint(builder)
        with pytest.raises(TypeError, match="State"):
            builder.add_state(None)
        assert builder_staging_fingerprint(builder) == before

    def test_empty_single_and_ordered_content_publish_once(self):
        initial = State("初期")
        middle = State("途中")
        final = State("完了")
        calls = []
        builder = FSMBuilder(initial)
        builder.add_state(middle).add_state(final)
        builder.add_transition("進む", "初期", "途中")
        builder.add_transition("終える", "途中", "完了")
        builder.on_enter("途中", lambda *args, **kwargs: calls.append("first"))
        builder.on_enter("途中", lambda *args, **kwargs: calls.append("second"))

        machine = builder.build()
        before_repeat = _machine_topology_fingerprint(machine)

        assert tuple(machine._states) == ("初期", "途中", "完了")
        assert machine.trigger("進む").success
        assert calls == ["first", "second"]
        assert builder.build() is machine
        assert _machine_topology_fingerprint(machine) == before_repeat

        single = FSMBuilder(State("単独")).build()
        assert tuple(single._states) == ("単独",)
        assert not single._transitions["単独"]

    def test_wiring_failure_stays_unpublished_and_repairable(self):
        calls = []
        builder = FSMBuilder(State("start"))
        builder.on_enter("repair", lambda *args, **kwargs: calls.append("repair"))
        builder.add_transition("go", "start", "repair")
        before_failure = builder_staging_fingerprint(builder)

        with pytest.raises(ValueError, match="not registered"):
            builder.build()

        assert builder._machine is None
        assert builder_staging_fingerprint(builder) == before_failure

        builder.add_state(State("repair"))
        builder.add_transition("go", "start", "repair")
        machine = builder.build()

        assert machine.trigger("go").success
        assert calls == ["repair"]


# ---------------------------------------------------------------------------
# FSMBuilder async preflight
# ---------------------------------------------------------------------------


class TestFSMBuilderAsyncPreflight:
    """D-11 builder mode selection before candidate publication."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "factory",
        (
            lambda: NegatedCondition(ConfigurableAsyncCondition(result=False)),
            lambda: AndCondition(AlwaysTrue(), ConfigurableAsyncCondition(result=True)),
            lambda: OrCondition(AlwaysFalse(), ConfigurableAsyncCondition(result=True)),
            lambda: NotCondition(ConfigurableAsyncCondition(result=False)),
        ),
    )
    async def test_auto_detects_nested_async_wrappers_and_executes_them(self, factory):
        builder = FSMBuilder(State("start"))
        builder.add_state(State("finish"))
        builder.add_transition("go", "start", "finish", factory())

        assert builder.machine_type is AsyncStateMachine
        machine = builder.build()
        assert isinstance(machine, AsyncStateMachine)
        assert await machine.can_trigger_async("go")
        assert (await machine.trigger_async("go")).success

    def test_unless_async_condition_uses_nested_preflight(self):
        builder = FSMBuilder(State("start"))
        builder.add_state(State("finish"))
        builder.add_transition(
            "go", "start", "finish", unless=ConfigurableAsyncCondition(result=False)
        )

        assert builder.machine_type is AsyncStateMachine
        assert isinstance(builder.build(), AsyncStateMachine)

    @pytest.mark.asyncio
    async def test_auto_detects_async_func_condition_subclass_check(self):
        """Auto mode classifies the effective public subclass hook."""

        class AsyncCheckFuncCondition(FuncCondition):
            async def check(self, *args, **kwargs):
                return True

        builder = FSMBuilder(State("start"))
        builder.add_state(State("finish"))
        builder.add_transition(
            "go",
            "start",
            "finish",
            AsyncCheckFuncCondition(lambda *args, **kwargs: False),
        )

        assert builder.machine_type is AsyncStateMachine
        machine = builder.build()
        assert isinstance(machine, AsyncStateMachine)
        assert await machine.can_trigger_async("go")
        assert (await machine.trigger_async("go")).success

    def test_explicit_sync_rejects_async_func_condition_subclass_check(self):
        """Explicit sync fails before it can publish an unreachable async guard."""

        class AsyncCheckFuncCondition(FuncCondition):
            async def check(self, *args, **kwargs):
                return True

        builder = FSMBuilder(State("start"), async_mode=False)
        builder.add_state(State("finish"))
        builder.add_transition(
            "go",
            "start",
            "finish",
            AsyncCheckFuncCondition(lambda *args, **kwargs: False),
        )

        with pytest.raises(RuntimeError, match="explicit sync.*condition"):
            builder.build()

    def test_auto_detects_declarative_async_handler_and_nested_guard(self):
        class DecoratedState(DeclarativeState):
            @transition("go", condition=NotCondition(ConfigurableAsyncCondition(False)))
            async def handle_go(self, *args, **kwargs):
                return True

        builder = FSMBuilder(DecoratedState("start"))

        assert builder.machine_type is AsyncStateMachine
        assert isinstance(builder.build(), AsyncStateMachine)

    def test_add_state_upgrades_only_after_async_preflight_succeeds(self):
        builder = FSMBuilder(State("start"))

        builder.add_state(AsyncDeclarativeState("async"))

        assert builder.machine_type is AsyncStateMachine

    def test_callable_unless_is_normalized_before_staging(self):
        builder = FSMBuilder(State("start"))
        builder.add_state(State("finish"))
        builder.add_transition("go", "start", "finish", unless=lambda: False)

        assert builder.build().trigger("go").success

    def test_explicit_async_remains_authoritative_without_async_staging(self):
        builder = FSMBuilder(State("start"), async_mode=True)

        assert builder.machine_type is AsyncStateMachine
        assert isinstance(builder.build(), AsyncStateMachine)

    def test_explicit_sync_rejects_nested_async_before_publication_and_can_repair(self):
        builder = FSMBuilder(State("start"), async_mode=False)
        builder.add_state(State("finish"))
        builder.add_transition(
            "go",
            "start",
            "finish",
            AndCondition(AlwaysTrue(), ConfigurableAsyncCondition()),
        )
        before = builder_staging_fingerprint(builder)

        with pytest.raises(RuntimeError, match="explicit sync.*condition"):
            builder.build()

        assert builder._machine is None
        assert builder_staging_fingerprint(builder) == before
        builder.force_async()
        assert isinstance(builder.build(), AsyncStateMachine)

    @pytest.mark.asyncio
    async def test_explicit_sync_rejects_queued_async_callbacks_without_dropping_them(
        self,
    ):
        calls = []

        async def callback(*args, **kwargs):
            calls.append("called")

        builder = FSMBuilder(State("start"), async_mode=False)
        builder.add_state(State("finish"))
        builder.add_transition("go", "start", "finish")
        builder.on_enter_async("finish", callback)
        before = builder_staging_fingerprint(builder)

        with pytest.raises(RuntimeError, match="explicit sync.*async callback"):
            builder.build()

        assert builder._machine is None
        assert builder_staging_fingerprint(builder) == before
        builder.force_async()
        machine = builder.build()
        assert (await machine.trigger_async("go")).success
        assert calls == ["called"]

    def test_wrapper_cycle_rejects_without_freezing_staging(self):
        cycle = NotCondition(AlwaysTrue())
        builder = FSMBuilder(State("start"))
        builder.add_state(State("finish"))
        builder.add_transition("go", "start", "finish", cycle)
        cycle.condition = cycle
        before = builder_staging_fingerprint(builder)

        with pytest.raises(ValueError, match="cycle"):
            builder.build()

        assert builder._machine is None
        assert builder_staging_fingerprint(builder) == before

    def test_transition_cycle_is_rejected_before_staging_mutates(self):
        cycle = NotCondition(AlwaysTrue())
        cycle.condition = cycle
        builder = FSMBuilder(State("start"))
        before = builder_staging_fingerprint(builder)

        with pytest.raises(ValueError, match="cycle"):
            builder.add_transition("go", "start", "finish", cycle)

        assert builder_staging_fingerprint(builder) == before

    def test_declarative_guard_cycle_is_rejected_before_state_staging_mutates(self):
        cycle = NotCondition(AlwaysTrue())
        cycle.condition = cycle

        class CyclicDeclarativeState(DeclarativeState):
            @transition("go", condition=cycle)
            def handle_go(self, *args, **kwargs):
                return True

        builder = FSMBuilder(State("start"))
        before = builder_staging_fingerprint(builder)

        with pytest.raises(ValueError, match="cycle"):
            builder.add_state(CyclicDeclarativeState("cyclic"))

        assert builder_staging_fingerprint(builder) == before

    def test_shared_dag_and_deep_nesting_terminate_and_select_async(self):
        shared = ConfigurableAsyncCondition()
        condition = AndCondition(shared, OrCondition(AlwaysFalse(), shared))
        for _ in range(24):
            condition = NotCondition(NotCondition(condition))
        builder = FSMBuilder(State("start"))
        builder.add_state(State("finish"))
        builder.add_transition("go", "start", "finish", condition)

        assert builder.machine_type is AsyncStateMachine
        assert isinstance(builder.build(), AsyncStateMachine)

    @pytest.mark.parametrize("shape", ("negated", "and", "or", "not"))
    @pytest.mark.parametrize("async_mode", (None, False, True))
    def test_every_builder_mode_rejects_every_cycle_before_transition_staging(
        self, shape, async_mode
    ):
        builder = FSMBuilder(State("start"), async_mode=async_mode)
        before = builder_staging_fingerprint(builder)

        with pytest.raises(ValueError, match="cycle"):
            builder.add_transition(
                "go", "start", "finish", _make_supported_wrapper_cycle(shape)
            )

        assert builder_staging_fingerprint(builder) == before

    @pytest.mark.parametrize("shape", ("negated", "and", "or", "not"))
    @pytest.mark.parametrize("async_mode", (None, False, True))
    def test_every_builder_mode_rejects_every_cycle_before_state_staging(
        self, shape, async_mode
    ):
        cycle = _make_supported_wrapper_cycle(shape)

        class CyclicDeclarativeState(DeclarativeState):
            @transition("go", condition=cycle)
            def handle_go(self, *args, **kwargs):
                return True

        builder = FSMBuilder(State("start"), async_mode=async_mode)
        before = builder_staging_fingerprint(builder)

        with pytest.raises(ValueError, match="cycle"):
            builder.add_state(CyclicDeclarativeState("cyclic"))

        assert builder_staging_fingerprint(builder) == before

    @pytest.mark.parametrize("async_mode", (None, False, True))
    def test_async_handler_does_not_hide_later_declarative_guard_cycle(
        self, async_mode
    ):
        cycle = _make_supported_wrapper_cycle("not")

        class MixedDeclarativeState(DeclarativeState):
            @transition("async-handler")
            async def a_async_handler(self, *args, **kwargs):
                return True

            @transition("cycle-guard", condition=cycle)
            def z_cycle_guard(self, *args, **kwargs):
                return True

        builder = FSMBuilder(State("start"), async_mode=async_mode)
        before = builder_staging_fingerprint(builder)

        with pytest.raises(ValueError, match="cycle"):
            builder.add_state(MixedDeclarativeState("mixed"))

        assert builder_staging_fingerprint(builder) == before

    @pytest.mark.parametrize("async_mode", (None, False, True))
    def test_build_preflight_validates_all_handlers_after_classification(
        self, async_mode
    ):
        guard = NotCondition(AlwaysTrue())

        class MixedDeclarativeState(DeclarativeState):
            @transition("async-handler")
            async def a_async_handler(self, *args, **kwargs):
                return True

            @transition("cycle-guard", condition=guard)
            def z_cycle_guard(self, *args, **kwargs):
                return True

        builder = FSMBuilder(State("start"), async_mode=async_mode)
        builder.add_state(MixedDeclarativeState("mixed"))
        guard.condition = guard
        before = builder_staging_fingerprint(builder)

        with pytest.raises(ValueError, match="cycle"):
            builder.build()

        assert builder_staging_fingerprint(builder) == before

    @pytest.mark.asyncio
    @pytest.mark.parametrize("handler_kind", ("sync", "async"))
    @pytest.mark.parametrize("outcome", ("false", "true", "raise"))
    async def test_async_callable_declarative_guards_are_awaited_once_per_can_do(
        self, handler_kind, outcome, recwarn
    ):
        guard_calls = []

        async def guard(*args, **kwargs):
            guard_calls.append((args, kwargs))
            if outcome == "raise":
                raise RuntimeError("async guard boom")
            return outcome == "true"

        if handler_kind == "sync":

            class GuardedState(DeclarativeState):
                @transition(
                    "go", from_state="source", to_state="target", condition=guard
                )
                def handle_go(self, *args, **kwargs):
                    return True

        else:

            class GuardedState(AsyncDeclarativeState):
                @transition(
                    "go", from_state="source", to_state="target", condition=guard
                )
                async def handle_go(self, *args, **kwargs):
                    return True

        source = GuardedState("source")
        target = State("target")
        builder = FSMBuilder(source)
        builder.add_state(target)
        builder.add_transition("go", "source", "target")

        assert builder.machine_type is AsyncStateMachine
        machine = builder.build()
        expected = outcome == "true"
        assert await machine.can_trigger_async("go") is expected
        assert (await machine.trigger_async("go")).success is expected
        assert len(guard_calls) == 2
        assert not any(
            issubclass(warning.category, RuntimeWarning) for warning in recwarn
        )

    @pytest.mark.parametrize("handler_kind", ("sync", "async"))
    def test_explicit_sync_builder_rejects_async_callable_declarative_guard(
        self, handler_kind, recwarn
    ):
        async def guard(*args, **kwargs):
            return True

        if handler_kind == "sync":

            class GuardedState(DeclarativeState):
                @transition("go", condition=guard)
                def handle_go(self, *args, **kwargs):
                    return True

        else:

            class GuardedState(AsyncDeclarativeState):
                @transition("go", condition=guard)
                async def handle_go(self, *args, **kwargs):
                    return True

        builder = FSMBuilder(GuardedState("source"), async_mode=False)

        with pytest.raises(RuntimeError, match="explicit sync"):
            builder.build()

        assert not any(
            issubclass(warning.category, RuntimeWarning) for warning in recwarn
        )

    @pytest.mark.parametrize("handler_kind", ("sync", "async"))
    def test_sync_machine_rejects_async_callable_declarative_guard_without_calling_it(
        self, handler_kind, recwarn
    ):
        guard_calls = []

        async def guard(*args, **kwargs):
            guard_calls.append((args, kwargs))
            return True

        if handler_kind == "sync":

            class GuardedState(DeclarativeState):
                @transition(
                    "go", from_state="source", to_state="target", condition=guard
                )
                def handle_go(self, *args, **kwargs):
                    return True

        else:

            class GuardedState(AsyncDeclarativeState):
                @transition(
                    "go", from_state="source", to_state="target", condition=guard
                )
                async def handle_go(self, *args, **kwargs):
                    return True

        source = GuardedState("source")
        target = State("target")
        machine = StateMachine(source)
        machine.add_state(target)
        machine.add_transition("go", source, target)

        assert not machine.can_trigger("go")
        assert not machine.trigger("go").success
        assert guard_calls == []
        assert not any(
            issubclass(warning.category, RuntimeWarning) for warning in recwarn
        )
