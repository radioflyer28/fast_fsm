"""
Tests for FSMBuilder, DeclarativeState, AsyncDeclarativeState,
@transition decorator, condition_builder, quick_fsm, and simple_fsm.

All tests use real components — no mocking.
"""

import inspect
import pickle
from pathlib import Path
import typing

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
    CompiledFuncCondition,
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
from fast_fsm.core import _TransitionGroup, _TransitionRequest


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


def _machine_topology_fingerprint(machine):
    """Capture the identity-bearing topology that a builder publishes."""
    return (
        machine._graph_version,
        tuple((name, id(state)) for name, state in machine._states.items()),
        tuple(
            (
                source,
                trigger,
                tuple(
                    (
                        id(entry.to_state),
                        id(entry.condition),
                        entry.priority,
                        entry.internal,
                    )
                    for entry in (
                        slot.entries if isinstance(slot, _TransitionGroup) else (slot,)
                    )
                ),
            )
            for source, entries in machine._transitions.items()
            for trigger, slot in entries.items()
        ),
    )


def builder_staging_fingerprint(builder):
    """Capture builder staging and any published topology without mutating it."""
    machine = builder._machine
    return (
        tuple((name, id(state)) for name, state in builder._states.items()),
        tuple(
            (
                request.trigger,
                request.sources,
                request.to_state,
                id(request.condition),
                request.priority,
                id(request.unless) if request.unless is not None else None,
                request.condition_ref,
                request.after,
                request.within,
                request.internal,
            )
            for request in builder._transitions
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


def test_builder_priority_staging_materializes_one_atomic_transition_batch():
    """Builder priority rows retain every candidate and publish them together."""
    builder = FSMBuilder(State("idle"))
    builder.add_state(State("running"))
    builder.add_state(State("complete"))
    builder.add_transition("go", "idle", "running", priority=7)
    builder.add_transition("go", "idle", "complete", priority=-3)
    builder.add_transition("advance", ["idle", "running"], "complete", priority=2)

    machine = builder.build()

    group = machine._transitions["idle"]["go"]
    assert isinstance(group, _TransitionGroup)
    assert tuple(entry.priority for entry in group.entries) == (-3, 7)
    assert machine._transitions["running"]["advance"].priority == 2
    assert machine._graph_version == 3


def test_builder_stages_immutable_named_transition_requests() -> None:
    """Builder staging copies source collections into the canonical carrier."""
    sources = ["idle"]
    guard = AlwaysTrue()
    builder = FSMBuilder(State("idle"))

    builder.add_transition(
        "go", sources, "running", guard, priority=-2, after=1, within=3
    )
    sources.append("late-mutation")

    assert len(builder._transitions) == 1
    request = builder._transitions[0]
    assert isinstance(request, _TransitionRequest)
    assert request.trigger == "go"
    assert request.sources == ("idle",)
    assert request.to_state == "running"
    assert request.condition is guard
    assert request.priority == -2
    assert request.after == 1.0
    assert request.within == 3.0
    with pytest.raises((AttributeError, TypeError)):
        request.trigger = "changed"  # type: ignore[misc]


def test_declarative_transition_internal_is_exact_and_metadata_is_immutable() -> None:
    """Decorator mode is exact while plural sources are copied before discovery."""
    sources = ["hover"]

    class RefreshingState(DeclarativeState):
        @transition("refresh", from_state=sources, to_state="hover", internal=True)
        def refresh(self, *_args, **_kwargs):
            return True

    sources.append("mutated-after-decoration")
    state = RefreshingState("hover")
    handler = state._handlers["refresh"][0]

    assert handler.from_state == ("hover",)
    assert handler.internal is True

    with pytest.raises(TypeError, match="exact built-in bool"):
        transition("refresh", internal=1)

    class DefaultModeState(DeclarativeState):
        @transition("refresh", to_state="hover")
        def refresh(self, *_args, **_kwargs):
            return True

    assert DefaultModeState("hover")._handlers["refresh"][0].internal is False


def test_declarative_builder_keeps_destinationless_handlers_direct_only() -> None:
    """A compatibility handler without a target never becomes invented topology."""
    calls: list[str] = []

    class DirectOnlyState(DeclarativeState):
        @transition("refresh")
        def refresh(self, *_args, **_kwargs):
            calls.append("handler")
            return True

    state = DirectOnlyState("hover")
    machine = FSMBuilder(state).build()

    assert "refresh" not in machine._transitions["hover"]
    assert state.handle_event("refresh").success is True
    assert calls == ["handler"]


def test_builder_imports_initial_and_later_declaration_owners_without_mirroring() -> (
    None
):
    """Only the declaration owner contributes its applicable canonical edge."""
    initial_sources = ["initial"]
    later_sources = ["armed"]
    calls: list[str] = []

    class Initial(DeclarativeState):
        @transition("launch", from_state=initial_sources, to_state="armed", priority=2)
        def launch(self, *_args: object, **_kwargs: object) -> bool:
            calls.append("launch")
            return True

    class Armed(DeclarativeState):
        @transition("complete", from_state=later_sources, to_state="done", priority=-3)
        def complete(self, *_args: object, **_kwargs: object) -> bool:
            calls.append("complete")
            return True

    initial = Initial("initial")
    armed = Armed("armed")
    builder = FSMBuilder(initial).add_state(armed).add_state(State("done"))
    initial_sources.append("mutated-after-decoration")
    later_sources.append("mutated-after-decoration")

    machine = builder.build()

    assert initial._handlers["launch"][0].from_state == ("initial",)
    assert armed._handlers["complete"][0].from_state == ("armed",)
    assert "launch" in machine._transitions["initial"]
    assert "complete" not in machine._transitions["initial"]
    assert "complete" in machine._transitions["armed"]
    assert machine.trigger("launch").success is True
    assert machine.trigger("complete").success is True
    assert machine.current_state.name == "done"
    assert calls == ["launch", "complete"]


def test_builder_declarative_conflict_is_atomic_and_repairable() -> None:
    """An explicit collision is rejected before the builder cache is published."""

    class Source(DeclarativeState):
        @transition("go", from_state="source", to_state="first", priority=0)
        def go(self, *_args: object, **_kwargs: object) -> bool:
            return True

    source = Source("source")
    builder = FSMBuilder(source)
    builder.add_state(State("first")).add_state(State("second"))
    builder.add_transition("go", "source", "second", priority=0)
    before = builder_staging_fingerprint(builder)

    with pytest.raises(ValueError, match="priority"):
        builder.build()

    assert builder._machine is None
    assert builder_staging_fingerprint(builder) == before
    builder._transitions[-1] = _TransitionRequest(
        "go", ("source",), "second", priority=1
    )
    machine = builder.build()

    assert machine.trigger("go").to_state == "first"
    assert builder.build() is machine


def test_builder_declarative_exact_duplicate_is_version_neutral() -> None:
    """An equivalent explicit row shares the canonical entry without a graph bump."""

    class Source(DeclarativeState):
        @transition("go", from_state="source", to_state="target", priority=-2)
        def go(self, *_args: object, **_kwargs: object) -> bool:
            return True

    source = Source("source")
    builder = FSMBuilder(source)
    builder.add_state(State("target"))
    builder.add_transition("go", "source", "target", priority=-2)

    machine = builder.build()

    assert machine._graph_version == 2
    assert machine._transitions["source"]["go"].priority == -2
    assert machine.trigger("go").success is True


def test_builder_ignores_nonapplicable_declarative_guards_during_preflight() -> None:
    """A foreign source constraint cannot poison an owner's staged build attempt."""
    cyclic_guard = NotCondition(AlwaysTrue())

    class ForeignDeclaration(DeclarativeState):
        @transition(
            "ignored",
            from_state="somewhere-else",
            to_state="target",
            condition=cyclic_guard,
        )
        def ignored(self, *_args: object, **_kwargs: object) -> bool:
            return True

    cyclic_guard.condition = cyclic_guard
    foreign = ForeignDeclaration("later")
    builder = FSMBuilder(State("initial"))

    builder.add_state(foreign).add_state(State("target"))
    machine = builder.build()

    assert isinstance(machine, StateMachine)
    assert "ignored" not in machine._transitions["later"]


@pytest.mark.asyncio
async def test_builder_declarative_async_topology_owns_each_runtime_seam_once() -> None:
    """Imported async declarations retain one guard, permission, handler, and entry."""
    calls = {"guard": 0, "permission": 0, "handler": 0, "entry": 0}

    async def guard(*_args: object, **_kwargs: object) -> bool:
        calls["guard"] += 1
        return True

    class Source(AsyncDeclarativeState):
        @transition("go", from_state="source", to_state="target", condition=guard)
        async def go(self, *_args: object, **_kwargs: object) -> bool:
            calls["handler"] += 1
            return True

        async def can_transition_async(
            self, trigger: str, to_state: State, *_args: object, **_kwargs: object
        ) -> bool:
            calls["permission"] += 1
            return await super().can_transition_async(trigger, to_state)

    class Target(State):
        def on_enter(
            self,
            _from_state: State | None,
            _trigger: str,
            *_args: object,
            **_kwargs: object,
        ) -> None:
            calls["entry"] += 1

    source = Source("source")
    target = Target("target")
    machine = FSMBuilder(source).add_state(target).build()

    assert isinstance(machine, AsyncStateMachine)
    assert (await machine.trigger_async("go")).success is True
    assert machine.current_state is target
    assert calls == {"guard": 1, "permission": 1, "handler": 1, "entry": 1}


def test_builder_build_submits_one_endpoint_bound_request_transaction() -> None:
    """Build binds endpoints without converting staging back to positional rows."""
    source = (Path(__file__).parents[1] / "src" / "fast_fsm" / "core.py").read_text()
    builder_start = source.index("class FSMBuilder:")
    build_start = source.index("    def build(", builder_start)
    build_end = source.index("    @property\n    def machine_type", build_start)
    build_source = source[build_start:build_end]

    assert "_TransitionRequest" in build_source
    assert "candidate._apply_transition_requests_owned" in build_source
    assert "candidate.add_transitions" not in build_source


def test_builder_rejects_bad_priority_before_staging_or_auto_mode_mutation():
    """The object-to-exact-int boundary happens before the builder changes state."""
    builder = FSMBuilder(State("idle"))
    before = builder_staging_fingerprint(builder)

    with pytest.raises(TypeError, match="exact built-in int"):
        builder.add_transition("go", "idle", "missing", priority=True)

    assert builder_staging_fingerprint(builder) == before


def test_builder_priority_failure_stays_repairable_until_candidate_publication():
    """A failed priority build leaves the staged rows repairable and unpublished."""
    builder = FSMBuilder(State("idle"))
    builder.add_transition("go", "idle", "missing", priority=-3)
    before = builder_staging_fingerprint(builder)

    with pytest.raises(ValueError, match="not registered"):
        builder.build()

    assert builder._machine is None
    assert builder_staging_fingerprint(builder) == before
    builder.add_state(State("missing"))
    machine = builder.build()
    assert machine._transitions["idle"]["go"].priority == -3


def test_builder_stages_and_builds_an_internal_self_transition():
    """The primary builder surface carries the explicit per-entry mode scalar."""
    idle = State("idle")
    builder = FSMBuilder(idle)
    builder.add_transition("refresh", "idle", "idle", internal=True)

    machine = builder.build()

    assert machine._transitions["idle"]["refresh"].internal is True


def test_builder_fingerprints_include_internal_transition_mode():
    """Atomicity fixtures distinguish otherwise-identical transition modes."""
    idle = State("idle")
    external_builder = FSMBuilder(idle)
    internal_builder = FSMBuilder(idle)
    external_builder.add_transition("refresh", "idle", "idle", internal=False)
    internal_builder.add_transition("refresh", "idle", "idle", internal=True)

    assert builder_staging_fingerprint(external_builder) != builder_staging_fingerprint(
        internal_builder
    )

    external_machine = external_builder.build()
    internal_machine = internal_builder.build()

    assert _machine_topology_fingerprint(
        external_machine
    ) != _machine_topology_fingerprint(internal_machine)


@pytest.mark.parametrize("internal", (1, 0, "true", object()))
def test_builder_rejects_non_bool_internal_before_staging(internal: object):
    """The builder preserves repairable staging at the exact-bool boundary."""
    builder = FSMBuilder(State("idle"))
    before = builder_staging_fingerprint(builder)

    with pytest.raises(TypeError, match="exact built-in bool"):
        builder.add_transition("refresh", "idle", "idle", internal=internal)

    assert builder_staging_fingerprint(builder) == before


def test_builder_internal_validation_failure_leaves_staging_repairable():
    """Invalid internal topology rejects only the private build candidate."""
    idle = State("idle")
    running = State("running")
    builder = FSMBuilder(idle)
    builder.add_state(running).add_transition(
        "refresh", "idle", "running", internal=True
    )
    before = builder_staging_fingerprint(builder)

    with pytest.raises(ValueError, match="internal transition"):
        builder.build()

    assert builder._machine is None
    assert builder_staging_fingerprint(builder) == before
    builder._transitions[-1] = _TransitionRequest(
        "refresh", ("idle",), "idle", internal=True
    )
    assert builder.build()._transitions["idle"]["refresh"].internal is True


def test_builder_final_source_failure_preserves_staging_and_can_be_repaired():
    """A final staged source rejects only the private candidate build."""
    idle = State("idle")
    done = State("done", final=True)
    builder = FSMBuilder(idle)
    builder.add_state(done).add_transition("finish", "done", "idle")
    before = builder_staging_fingerprint(builder)

    with pytest.raises(ValueError, match="^final state cannot be a transition source$"):
        builder.build()

    assert builder._machine is None
    assert builder_staging_fingerprint(builder) == before
    builder._transitions[-1] = _TransitionRequest("finish", ("idle",), "done")

    machine = builder.build()
    assert machine._states["done"] is done
    assert machine.trigger("finish").success
    assert machine.current_state is done


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
    def test_declarative_ordinary_failure_outcomes_are_committed_once(
        self, handler_result
    ):
        source = DeclarativeInvocationCounter(result=handler_result)
        fsm = self._machine(source)

        result = fsm.trigger("advance")

        assert source.invocations == 1
        assert not result.success
        assert result.committed
        assert result.stage == "declarative-handler"
        assert fsm.current_state_name == "target"


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
        assert s._handlers["go"][0].is_async is True

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

    def test_priority_defaults_to_zero_and_requires_exact_builtin_int(self):
        @transition("t")
        def handler():
            pass

        assert handler._fsm_priority == 0

        with pytest.raises(TypeError, match="exact built-in int"):
            transition("t", priority=True)


class TestPriorityAwareDeclarativeCandidates:
    """Declarative metadata must retain and resolve every candidate."""

    def test_plural_metadata_uses_priority_not_discovery_order(self):
        calls: list[tuple[str, int]] = []

        class Source(DeclarativeState):
            @transition("go", from_state="source", to_state="alternate", priority=9)
            def z_later_attribute(self, *args, **kwargs):
                calls.append(("alternate", kwargs["priority"]))

            @transition("go", from_state="source", to_state="safe", priority=1)
            def a_earlier_attribute(self, *args, **kwargs):
                calls.append(("safe", kwargs["priority"]))

        source = Source("source")
        safe = State("safe")
        alternate = State("alternate")
        machine = StateMachine(source)
        machine.add_state(safe)
        machine.add_state(alternate)
        machine.add_transition("go", "source", "alternate", priority=9)
        machine.add_transition("go", "source", "safe", priority=1)

        assert isinstance(source._handlers["go"], tuple)
        assert len(source._handlers["go"]) == 2
        result = machine.trigger("go", priority=42)

        assert result.success
        assert result.to_state == "safe"
        assert result.priority == 1
        assert calls == [("safe", 42)]

    def test_direct_handler_ambiguity_invokes_no_declaration(self):
        calls: list[str] = []

        class Source(DeclarativeState):
            @transition("go", from_state="source", to_state="one", priority=1)
            def first(self):
                calls.append("first")

            @transition("go", from_state="source", to_state="two", priority=2)
            def second(self):
                calls.append("second")

        result = Source("source").handle_event("go")

        assert result.success is False
        assert calls == []

    def test_same_target_candidates_bind_by_priority_and_ambiguous_direct_query_fails(
        self,
    ):
        calls: list[str] = []

        class Source(DeclarativeState):
            @transition("go", from_state="source", to_state="target", priority=9)
            def high_priority_number(self):
                calls.append("high-number")

            @transition("go", from_state="source", to_state="target", priority=1)
            def low_priority_number(self):
                calls.append("low-number")

        source = Source("source")
        target = State("target")
        machine = StateMachine(source)
        machine.add_state(target)
        machine.add_transition("go", "source", "target", priority=9)
        machine.add_transition("go", "source", "target", priority=1)

        assert not source.can_transition("go", target)
        assert machine.trigger("go").success
        assert calls == ["low-number"]

    def test_duplicate_declarative_identity_is_rejected_before_machine_build(self):
        class Source(DeclarativeState):
            @transition("go", from_state="source", to_state="target", priority=1)
            def first(self):
                pass

            @transition("go", from_state="source", to_state="target", priority=1)
            def second(self):
                pass

        with pytest.raises(ValueError, match="duplicate declarative candidate"):
            Source("source")

    def test_builder_preflight_inspects_later_stacked_declaration(self):
        async def later_guard(*args, **kwargs):
            return True

        class Source(DeclarativeState):
            @transition("go", from_state="source", to_state="target", priority=1)
            @transition(
                "go",
                from_state="source",
                to_state="target",
                condition=later_guard,
                priority=2,
            )
            def handle_go(self, *args, **kwargs):
                return True

        source = Source("source")
        auto = FSMBuilder(source)
        explicit_sync = FSMBuilder(source, async_mode=False)

        assert len(source._handlers["go"]) == 2
        assert auto.machine_type is AsyncStateMachine
        with pytest.raises(RuntimeError, match="explicit sync.*declarative condition"):
            explicit_sync.build()
        assert explicit_sync._machine is None
        assert explicit_sync._states["source"] is source


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

    @pytest.mark.parametrize("invalid_target", [None, 1])
    def test_quick_build_rejects_non_state_target_values(self, invalid_target):
        with pytest.raises(TypeError):
            StateMachine.quick_build("initial", [("go", "initial", invalid_target)])

    @pytest.mark.parametrize("invalid_state", [None, 1])
    def test_quick_build_rejects_non_state_entries(self, invalid_state):
        with pytest.raises(TypeError):
            StateMachine.quick_build("initial", [], states=[invalid_state])

    @staticmethod
    def _candidate_fingerprint(machine: StateMachine) -> tuple[object, ...]:
        """Return semantic candidate rows without comparing machine-local identities."""
        rows: list[object] = []
        for source_name, trigger_rows in machine._transitions.items():
            for trigger, slot in trigger_rows.items():
                entries = (
                    slot.entries if isinstance(slot, _TransitionGroup) else (slot,)
                )
                rows.append(
                    (
                        source_name,
                        trigger,
                        tuple(
                            (
                                entry.to_state.name,
                                entry.priority,
                                entry.condition is not None,
                            )
                            for entry in entries
                        ),
                    )
                )
        return tuple(sorted(rows, key=repr))

    def test_all_constructors_preserve_the_same_priority_candidate_fingerprint(self):
        """Every adapter replays the registrar's ordered candidate topology."""
        rows = [
            ("go", "idle", "high", None, 4),
            ("go", "idle", "low", None, -1),
            ("finish", ["low", "high"], "done", None, 2),
        ]

        def direct_machine() -> StateMachine:
            machine = StateMachine(State("idle"))
            for name in ("low", "high", "done"):
                machine.add_state(State(name))
            for row in rows:
                machine.add_transition(*row[:4], priority=row[4])
            return machine

        def batch_machine() -> StateMachine:
            machine = StateMachine(State("idle"))
            for name in ("low", "high", "done"):
                machine.add_state(State(name))
            machine.add_transitions(rows)
            return machine

        def builder_machine() -> StateMachine:
            builder = FSMBuilder(State("idle"))
            for name in ("low", "high", "done"):
                builder.add_state(State(name))
            for row in rows:
                builder.add_transition(*row[:4], priority=row[4])
            return builder.build()

        class DeclarativeIdle(DeclarativeState):
            @transition(
                "finish", from_state=["low", "high"], to_state="done", priority=2
            )
            def finish(self, *args, **kwargs):
                return True

            @transition("go", from_state="idle", to_state="high", priority=4)
            def high(self, *args, **kwargs):
                return True

            @transition("go", from_state="idle", to_state="low", priority=-1)
            def low(self, *args, **kwargs):
                return True

        declarative_builder = FSMBuilder(DeclarativeIdle("idle"))
        for name in ("low", "high", "done"):
            declarative_builder.add_state(State(name))
        for row in rows:
            declarative_builder.add_transition(*row[:4], priority=row[4])
        machines = (
            direct_machine(),
            batch_machine(),
            builder_machine(),
            StateMachine.quick_build("idle", rows),
            quick_fsm("idle", rows),
            declarative_builder.build(),
            StateMachine.from_dict(
                {
                    "initial": "idle",
                    "states": ["idle", "low", "high", "done"],
                    "transitions": [
                        {"trigger": "go", "from": "idle", "to": "high", "priority": 4},
                        {"trigger": "go", "from": "idle", "to": "low", "priority": -1},
                        {
                            "trigger": "finish",
                            "from": ["low", "high"],
                            "to": "done",
                            "priority": 2,
                        },
                    ],
                }
            ),
        )

        expected = self._candidate_fingerprint(machines[0])
        assert all(
            self._candidate_fingerprint(machine) == expected for machine in machines
        )
        assert machines[3].trigger("go").to_state == "low"

    def test_quick_factories_keep_state_guard_and_priority_rows_in_one_batch(self):
        """Quick construction transports 4/5-field rows without adapter policy."""
        initial = State("initial")
        middle = State("middle")
        target = State("target")
        guard = FuncCondition(lambda **kwargs: True)
        rows = [("go", [initial, middle], target, guard, -3)]
        machine = StateMachine.quick_build(initial, rows)

        source = (Path(__file__).parents[1] / "src" / "fast_fsm" / "core.py").read_text(
            encoding="utf-8"
        )
        method_start = source.index("    def quick_build(")
        method_end = source.index("    @classmethod\n    def from_dict(", method_start)
        quick_build_source = source[method_start:method_end]
        assert "_TransitionRequest" in quick_build_source
        assert "fsm._apply_transition_requests_owned(requests)" in quick_build_source
        assert "fsm.add_transition(" not in quick_build_source
        assert "fsm.add_transitions(" not in quick_build_source
        assert machine._states["initial"] is initial
        assert machine._states["middle"] is middle
        assert machine._states["target"] is target
        slot = machine._transitions["initial"]["go"]
        entry = slot.entries[0] if isinstance(slot, _TransitionGroup) else slot
        assert entry.condition is guard
        assert entry.priority == -3
        assert machine.trigger("go").success

    @pytest.mark.parametrize(
        "bad_row, expected_error",
        (
            (("go", "initial", "target", None, True), TypeError),
            (("go", "initial", "target", SimpleAsyncCondition()), TypeError),
            (("go", "initial", "target", None, 0), ValueError),
        ),
    )
    def test_quick_factory_late_failures_do_not_publish_a_prefix(
        self, bad_row, expected_error
    ):
        """A complete batch rejects late invalid rows rather than committing a prefix."""
        rows = [("go", "initial", "one", None, 0), bad_row]

        with pytest.raises(expected_error):
            StateMachine.quick_build("initial", rows)

    def test_builder_tie_failure_stays_unpublished_and_is_repairable(self):
        """Builder cache/staging survives a registrar conflict for explicit repair."""
        builder = FSMBuilder(State("initial"))
        builder.add_state(State("one")).add_state(State("two"))
        builder.add_transition("go", "initial", "one", priority=0)
        builder.add_transition("go", "initial", "two", priority=0)
        before = builder_staging_fingerprint(builder)

        with pytest.raises(ValueError, match="priority"):
            builder.build()

        assert builder._machine is None
        assert builder_staging_fingerprint(builder) == before
        builder._transitions[-1] = _TransitionRequest(
            "go", ("initial",), "two", priority=1
        )
        repaired = builder.build()
        assert repaired.trigger("go").to_state == "one"


# ---------------------------------------------------------------------------
# DeclarativeState gap coverage
# ---------------------------------------------------------------------------


class TestDeclarativeStateGaps:
    """Cover uncovered paths in DeclarativeState."""

    def test_direct_sync_policy_rejects_awaitable_condition_protocol(self, recwarn):
        """A sync declarative policy closes and rejects an awaitable condition."""

        class AwaitableCondition(Condition):
            def __init__(self):
                super().__init__("awaitable")
                self.calls = 0

            async def check(self, *args, **kwargs):
                self.calls += 1
                return True

        condition = AwaitableCondition()

        class GuardedState(DeclarativeState):
            @transition("go", condition=condition)
            def handle_go(self, *args, **kwargs):
                return True

        assert not GuardedState("source").can_transition("go", State("target"))
        assert condition.calls == 0
        assert not any(
            issubclass(warning.category, RuntimeWarning) for warning in recwarn
        )

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
            result = machine.trigger("go")
            assert not result.success
            assert result.stage == "state-permission"
            assert isinstance(result.cause, RuntimeError)
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
            result = await machine.trigger_async("go")
            assert not result.success
            assert result.stage == "state-permission"
            assert isinstance(result.cause, RuntimeError)
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
        source = (Path(__file__).parents[1] / "src" / "fast_fsm" / "core.py").read_text(
            encoding="utf-8"
        )
        builder_start = source.index("class FSMBuilder:")
        method_start = source.index("    def on_enter_async(", builder_start)
        method_end = source.index("    def on_exit_async(", method_start)
        on_enter_async_source = source[method_start:method_end]
        assert "remains staged" in on_enter_async_source
        assert "raises before publishing" in on_enter_async_source
        with pytest.raises(RuntimeError, match="explicit sync.*async callback"):
            builder.build()
        assert builder._machine is None


class TestOwnershipConstructionIndependence:
    """Publication creates machines, not shared ownership primitives."""

    @staticmethod
    def _assert_sync_independence(*machines: StateMachine) -> None:
        assert len({id(machine._sync_ownership_lock) for machine in machines}) == len(
            machines
        )
        assert all(machine._sync_owner_thread_id is None for machine in machines)

    def test_builder_factories_and_clones_have_distinct_sync_ownership(self):
        builder = FSMBuilder(State("builder-start"))
        builder.add_state(State("builder-finish"))
        builder.add_transition("go", "builder-start", "builder-finish")
        built = builder.build()
        quick = StateMachine.quick_build(
            "quick-start", [("go", "quick-start", "quick-finish")]
        )
        configured = StateMachine.from_dict(
            {
                "initial": "config-start",
                "transitions": [
                    {
                        "trigger": "go",
                        "from": "config-start",
                        "to": "config-finish",
                    }
                ],
            }
        )
        clone = built.clone()

        self._assert_sync_independence(built, quick, configured, clone)

    def test_async_builder_and_clone_reset_all_ownership_metadata(self):
        async def callback(*_args, **_kwargs):
            pass

        builder = FSMBuilder(State("source"))
        builder.add_state(State("destination"))
        builder.add_transition("go", "source", "destination")
        builder.on_enter_async("destination", callback)
        machine = builder.build()

        assert isinstance(machine, AsyncStateMachine)
        clone = machine.clone()
        assert machine._sync_ownership_lock is not clone._sync_ownership_lock
        assert machine._async_ownership_lock is not clone._async_ownership_lock
        assert machine._async_admission_lock is not clone._async_admission_lock
        for owned in (machine, clone):
            assert owned._bound_loop is None
            assert owned._bound_loop_thread_id is None
            assert owned._async_owner_task is None
            assert owned._async_owner_root is None


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

    @pytest.mark.parametrize("repair_to_async", (False, True))
    def test_failed_auto_build_recomputes_and_publishes_current_machine_type(
        self, repair_to_async
    ):
        """A failed auto candidate cannot persist its transient async choice."""

        def sync_guard(*args, **kwargs):
            return True

        async def async_guard(*args, **kwargs):
            return True

        condition = FuncCondition(sync_guard)
        builder = FSMBuilder(State("start"))
        builder.add_transition("go", "start", "missing", condition)
        before_failure = builder_staging_fingerprint(builder)

        # Public callable-backed conditions are intentionally mutable. Force
        # auto preflight to choose async, then fail later during graph wiring.
        condition.func = async_guard
        with pytest.raises(ValueError, match="not registered"):
            builder.build()

        assert builder._machine is None
        assert builder.machine_type is StateMachine
        assert builder_staging_fingerprint(builder) == before_failure

        builder.add_state(State("missing"))
        condition.func = async_guard if repair_to_async else sync_guard
        machine = builder.build()

        expected_type = AsyncStateMachine if repair_to_async else StateMachine
        assert type(machine) is expected_type
        assert builder.machine_type is expected_type
        assert builder.build() is machine


# ---------------------------------------------------------------------------
# FSMBuilder async preflight
# ---------------------------------------------------------------------------


class TestFSMBuilderAsyncPreflight:
    """D-11 builder mode selection before candidate publication."""

    @staticmethod
    def _async_callable_instance():
        """Return an inspectable callable whose invocation is asynchronous."""

        class AsyncCallable:
            def __init__(self) -> None:
                self.calls = 0

            async def __call__(self, *args, **kwargs) -> bool:
                self.calls += 1
                return True

        return AsyncCallable()

    @staticmethod
    def _async_callable_instance_condition(shape, guard):
        """Wrap one async callable instance through every public guard shape."""
        if shape == "func":
            return FuncCondition(guard)
        if shape == "compiled":
            return CompiledFuncCondition(guard)
        if shape == "inherited-func":

            class InheritedFuncCondition(FuncCondition):
                pass

            return InheritedFuncCondition(guard)
        if shape == "inherited-compiled":

            class InheritedCompiledFuncCondition(CompiledFuncCondition):
                pass

            return InheritedCompiledFuncCondition(guard)
        return guard

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "shape",
        ("func", "compiled", "inherited-func", "inherited-compiled", "direct"),
    )
    async def test_auto_detects_async_callable_instances_and_awaits_them(self, shape):
        """Both incremental detection and build preflight inspect ``__call__``."""
        guard = self._async_callable_instance()
        builder = FSMBuilder(State("start"))
        builder.add_state(State("finish"))
        builder.add_transition(
            "go",
            "start",
            "finish",
            self._async_callable_instance_condition(shape, guard),
        )

        # This assertion covers incremental staging; the build repeats the
        # traversal before candidate allocation.
        assert builder.machine_type is AsyncStateMachine
        machine = builder.build()
        assert isinstance(machine, AsyncStateMachine)
        assert await machine.can_trigger_async("go")
        assert (await machine.trigger_async("go")).success
        assert guard.calls == 2

    @pytest.mark.parametrize(
        "shape",
        ("func", "compiled", "inherited-func", "inherited-compiled", "direct"),
    )
    def test_explicit_sync_rejects_async_callable_instances_before_invocation(
        self, shape
    ):
        """Forced sync rejects callable instances without running user code."""
        guard = self._async_callable_instance()
        builder = FSMBuilder(State("start"), async_mode=False)
        builder.add_state(State("finish"))
        builder.add_transition(
            "go",
            "start",
            "finish",
            self._async_callable_instance_condition(shape, guard),
        )

        with pytest.raises(RuntimeError, match="explicit sync.*condition"):
            builder.build()

        assert guard.calls == 0

    @pytest.mark.asyncio
    async def test_declarative_async_callable_instance_guard_uses_the_same_classifier(
        self,
    ):
        """Decorator guards select async mode and are awaited through dispatch."""
        guard = self._async_callable_instance()

        class GuardedState(DeclarativeState):
            @transition("go", from_state="start", to_state="finish", condition=guard)
            def handle_go(self, *args, **kwargs):
                return True

        builder = FSMBuilder(GuardedState("start"))
        builder.add_state(State("finish"))
        builder.add_transition("go", "start", "finish")

        assert builder.machine_type is AsyncStateMachine
        machine = builder.build()
        assert isinstance(machine, AsyncStateMachine)
        assert await machine.can_trigger_async("go")
        assert (await machine.trigger_async("go")).success
        assert guard.calls == 2

    def test_explicit_sync_rejects_declarative_async_callable_instance_before_invocation(
        self,
    ):
        """Decorator callable instances fail at preflight, not at runtime."""
        guard = self._async_callable_instance()

        class GuardedState(DeclarativeState):
            @transition("go", condition=guard)
            def handle_go(self, *args, **kwargs):
                return True

        builder = FSMBuilder(GuardedState("start"), async_mode=False)

        with pytest.raises(RuntimeError, match="explicit sync.*declarative condition"):
            builder.build()

        assert guard.calls == 0

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

    @staticmethod
    def _callable_backed_async_condition(shape):
        """Return each supported callable-backed async condition shape."""

        async def async_guard(*args, **kwargs):
            return True

        if shape == "compiled":
            return CompiledFuncCondition(async_guard)
        if shape == "inherited":

            class InheritedFuncCondition(FuncCondition):
                pass

            return InheritedFuncCondition(async_guard)

        class AsyncCheckFuncCondition(FuncCondition):
            async def check(self, *args, **kwargs):
                return True

        return AsyncCheckFuncCondition(lambda *args, **kwargs: False)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("shape", ("compiled", "inherited", "override"))
    async def test_auto_detects_callable_backed_async_conditions(self, shape):
        """Auto mode follows each callable-backed condition's effective hook."""
        builder = FSMBuilder(State("start"))
        builder.add_state(State("finish"))
        builder.add_transition(
            "go",
            "start",
            "finish",
            self._callable_backed_async_condition(shape),
        )

        assert builder.machine_type is AsyncStateMachine
        machine = builder.build()
        assert isinstance(machine, AsyncStateMachine)
        assert await machine.can_trigger_async("go")
        assert (await machine.trigger_async("go")).success

    @pytest.mark.parametrize("shape", ("compiled", "inherited", "override"))
    def test_explicit_sync_rejects_callable_backed_async_conditions(self, shape):
        """Explicit sync rejects every detectable callable-backed async guard."""
        builder = FSMBuilder(State("start"), async_mode=False)
        builder.add_state(State("finish"))
        builder.add_transition(
            "go",
            "start",
            "finish",
            self._callable_backed_async_condition(shape),
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

    @pytest.mark.asyncio
    async def test_auto_async_builder_keeps_callbacks_at_their_lifecycle_slots(self):
        """Builder wiring preserves same-slot order and exactly-once invocation."""
        events: list[str] = []

        async def exit_async(*args, **kwargs):
            events.append("exit-async")

        async def enter_async(*args, **kwargs):
            events.append("enter-async")

        builder = FSMBuilder(State("start"))
        builder.add_state(State("finish"))
        builder.add_transition("go", "start", "finish")
        builder.on_exit("start", lambda *args, **kwargs: events.append("exit-sync"))
        builder.on_exit_async("start", exit_async)
        builder.on_enter("finish", lambda *args, **kwargs: events.append("enter-sync"))
        builder.on_enter_async("finish", enter_async)

        machine = builder.build()

        assert isinstance(machine, AsyncStateMachine)
        assert (await machine.trigger_async("go")).success
        assert events == ["exit-sync", "exit-async", "enter-sync", "enter-async"]

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


@pytest.mark.parametrize(
    "symbol",
    ("simple_fsm", "quick_fsm", "StateMachine.quick_build", "StateMachine.from_states"),
)
def test_deprecated_construction_boundaries_warn_once_at_the_user_call_site(symbol):
    """Each retained compatibility boundary warns once before construction."""
    import warnings

    expected = (
        f"{symbol} is deprecated and remains supported through v0.5.x; "
        "use FSMBuilder for programmatic construction or StateMachine.from_dict() "
        "for serialized topology. It may be removed no earlier than v0.6.0."
    )

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        if symbol == "simple_fsm":
            valid_line = inspect.currentframe().f_lineno + 1
            machine = simple_fsm("idle", initial="idle")
        elif symbol == "quick_fsm":
            valid_line = inspect.currentframe().f_lineno + 1
            machine = quick_fsm("idle", [("go", "idle", "done")])
        elif symbol == "StateMachine.quick_build":
            valid_line = inspect.currentframe().f_lineno + 1
            machine = StateMachine.quick_build("idle", [("go", "idle", "done")])
        else:
            valid_line = inspect.currentframe().f_lineno + 1
            machine = StateMachine.from_states("idle", initial="idle")

    assert isinstance(machine, StateMachine)
    assert len(captured) == 1
    warning = captured[0]
    assert warning.category is DeprecationWarning
    assert str(warning.message) == expected
    assert warning.filename == __file__
    assert warning.lineno == valid_line
    assert "object at 0x" not in str(warning.message)

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        with pytest.raises((TypeError, ValueError)):
            if symbol == "simple_fsm":
                invalid_line = inspect.currentframe().f_lineno + 1
                simple_fsm(initial=object())
            elif symbol == "quick_fsm":
                invalid_line = inspect.currentframe().f_lineno + 1
                quick_fsm("idle", [("go", "idle")])
            elif symbol == "StateMachine.quick_build":
                invalid_line = inspect.currentframe().f_lineno + 1
                StateMachine.quick_build("idle", [("go", "idle")])
            else:
                invalid_line = inspect.currentframe().f_lineno + 1
                StateMachine.from_states()

    assert len(captured) == 1
    assert captured[0].category is DeprecationWarning
    assert str(captured[0].message) == expected
    assert captured[0].filename == __file__
    assert captured[0].lineno == invalid_line


def test_nondeprecated_construction_surfaces_remain_silent():
    """Only the four retained compatibility constructors warn."""
    import warnings

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        StateMachine(State("idle"))
        StateMachine.from_dict(
            {
                "states": ["idle"],
                "initial": "idle",
                "transitions": [],
            }
        )
        State.create("idle")
        FSMBuilder(State("idle"))
        DeclarativeState("idle")

    assert captured == []


def test_deprecated_construction_public_surface_remains_typed_exported_and_subclass_safe():
    """The v0.5.x compatibility names retain their public contracts."""
    import inspect
    import warnings

    import fast_fsm

    class DerivedMachine(StateMachine):
        pass

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        from_states = DerivedMachine.from_states("idle")
        quick_build = DerivedMachine.quick_build("idle", [])

    assert len(captured) == 2
    assert all(warning.category is DeprecationWarning for warning in captured)
    assert type(from_states) is DerivedMachine
    assert type(quick_build) is DerivedMachine
    assert fast_fsm.simple_fsm is simple_fsm
    assert fast_fsm.quick_fsm is quick_fsm
    assert {"simple_fsm", "quick_fsm"} <= set(fast_fsm.__all__)
    assert inspect.signature(StateMachine.from_states).parameters.keys() == {
        "state_names",
        "initial",
        "name",
        "clock",
    }
    assert inspect.signature(StateMachine.quick_build).parameters.keys() == {
        "initial_state",
        "transitions",
        "states",
        "name",
        "clock",
    }

    stub = (Path(__file__).parents[1] / "src" / "fast_fsm" / "core.pyi").read_text(
        encoding="utf-8"
    )
    assert "def from_states(" in stub
    assert "def quick_build(" in stub
    assert "def simple_fsm(" in stub
    assert "def quick_fsm(" in stub


def test_deprecated_construction_wrappers_keep_public_runtime_provenance() -> None:
    """The interpreted warning boundaries remain ordinary public callables."""
    import fast_fsm.core as core

    boundaries = (
        (
            "simple_fsm",
            core.simple_fsm,
            "simple_fsm",
            ("state_names", "initial", "name", "clock"),
        ),
        (
            "quick_fsm",
            core.quick_fsm,
            "quick_fsm",
            ("initial_state", "transitions", "name", "clock"),
        ),
        (
            "from_states",
            StateMachine.from_states,
            "StateMachine.from_states",
            ("state_names", "initial", "name", "clock"),
        ),
        (
            "quick_build",
            StateMachine.quick_build,
            "StateMachine.quick_build",
            ("initial_state", "transitions", "states", "name", "clock"),
        ),
    )

    for expected_name, boundary, expected_qualname, expected_parameters in boundaries:
        assert boundary.__module__ == "fast_fsm.core"
        assert boundary.__name__ == expected_name
        assert boundary.__qualname__ == expected_qualname
        assert boundary.__doc__
        if hasattr(boundary, "__wrapped__"):
            assert boundary.__doc__ == boundary.__wrapped__.__doc__
        assert tuple(inspect.signature(boundary).parameters) == expected_parameters
        assert typing.get_type_hints(boundary)

    assert pickle.loads(pickle.dumps(core.simple_fsm)) is core.simple_fsm
    assert pickle.loads(pickle.dumps(core.quick_fsm)) is core.quick_fsm

    class DerivedMachine(StateMachine):
        pass

    assert DerivedMachine.from_states("idle").__class__ is DerivedMachine
    assert DerivedMachine.quick_build("idle", []).__class__ is DerivedMachine
