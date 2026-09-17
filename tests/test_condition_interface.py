"""Public contract tests for the focused condition interface."""

from __future__ import annotations

import asyncio
import warnings

import pytest

from fast_fsm import (
    AndCondition,
    AsyncCondition,
    CompiledFuncCondition,
    Condition,
    FuncCondition,
    NegatedCondition,
    NotCondition,
    OrCondition,
    State,
    AsyncStateMachine,
    StateMachine,
    TransitionRejected,
)
from fast_fsm.condition_templates import (
    AlwaysCondition,
    ComparisonCondition,
    CooldownCondition,
    ElapsedCondition,
    KeyExistsCondition,
    NeverCondition,
    RegexCondition,
    TimeoutCondition,
    ValueInSetCondition,
)


class FakeClock:
    """A deterministic monotonic clock controlled by the test."""

    def __init__(self, now: float = 0.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now


class AsyncLeaf(AsyncCondition):
    __slots__ = ("_result",)

    def __init__(self, result: bool) -> None:
        super().__init__("async-leaf")
        self._result = result

    async def check_async(self, *args: object, **kwargs: object) -> bool:
        return self._result


def test_operators_construct_canonical_wrappers_and_short_circuit() -> None:
    calls: list[str] = []

    def record_false() -> bool:
        calls.append("false")
        return False

    def record_true() -> bool:
        calls.append("true")
        return True

    false = FuncCondition(record_false)
    true = FuncCondition(record_true)

    combined_and = false & true
    combined_or = false | true
    negated = ~false

    assert type(combined_and) is AndCondition
    assert type(combined_or) is OrCondition
    assert type(negated) is NotCondition
    assert not combined_and.check()
    assert calls == ["false"]
    assert combined_or.check()
    assert calls == ["false", "false", "true"]
    assert negated.check()
    with pytest.raises(TypeError):
        _ = false & object()  # type: ignore[operator]
    with pytest.raises(TypeError):
        _ = false | object()  # type: ignore[operator]


@pytest.mark.asyncio
async def test_deferred_compound_guard_result_has_single_await_ownership() -> None:
    """A composed async guard must not re-run its first awaitable on reuse."""

    async def async_true() -> bool:
        return True

    deferred = (FuncCondition(async_true) & FuncCondition(lambda: True)).check()

    assert await deferred
    with pytest.raises(RuntimeError, match="cannot reuse an awaited guard result"):
        await deferred


def test_reject_08_direct_and_synchronous_composition_preserve_signal_identity() -> (
    None
):
    """REJECT-08: synchronous wrappers do not reinterpret expected rejection."""
    signal = TransitionRejected("mission.altitude_limit")

    def verify(factory) -> None:
        calls: list[str] = []

        def reject() -> bool:
            calls.append("rejected")
            raise signal

        def later() -> bool:
            calls.append("later")
            return True

        rejected = FuncCondition(reject)
        later_condition = FuncCondition(later)
        with pytest.raises(TransitionRejected) as raised:
            factory(rejected, later_condition).check()
        assert raised.value is signal
        assert calls == ["rejected"]

    verify(lambda rejected, later: rejected)
    verify(lambda rejected, later: rejected & later)
    verify(lambda rejected, later: rejected | later)
    verify(lambda rejected, later: NotCondition(rejected))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        verify(lambda rejected, later: NegatedCondition(rejected))
    verify(lambda rejected, later: OrCondition(AndCondition(rejected, later), later))


@pytest.mark.parametrize(
    ("factory", "prefix_result"),
    (
        (lambda prefix, rejected, later: AndCondition(prefix, rejected, later), True),
        (lambda prefix, rejected, later: OrCondition(prefix, rejected, later), False),
    ),
)
def test_reject_08_composition_propagates_rejection_after_eligible_prefix(
    factory, prefix_result: bool
) -> None:
    """REJECT-08: operator position cannot turn rejection into fallthrough."""
    signal = TransitionRejected("mission.altitude_limit")
    calls: list[str] = []

    def prefix() -> bool:
        calls.append("prefix")
        return prefix_result

    def reject() -> bool:
        calls.append("reject")
        raise signal

    def later() -> bool:
        calls.append("later")
        return True

    condition = factory(
        FuncCondition(prefix), FuncCondition(reject), FuncCondition(later)
    )

    with pytest.raises(TransitionRejected) as raised:
        condition.check()

    assert raised.value is signal
    assert calls == ["prefix", "reject"]


@pytest.mark.asyncio
async def test_reject_08_deferred_composition_keeps_signal_and_cancellation_terminal() -> (
    None
):
    """REJECT-08: awaited wrappers retain one owner and stop at the raised child."""
    signal = TransitionRejected("link.lost")
    rejection_calls: list[str] = []

    async def reject() -> bool:
        rejection_calls.append("rejected")
        await asyncio.sleep(0)
        raise signal

    def earlier_false() -> bool:
        rejection_calls.append("earlier")
        return False

    def later() -> bool:
        rejection_calls.append("later")
        return True

    deferred = OrCondition(
        FuncCondition(earlier_false),
        FuncCondition(reject),
        FuncCondition(later),
    ).check()
    with pytest.raises(TransitionRejected) as raised:
        await deferred
    assert raised.value is signal
    assert rejection_calls == ["earlier", "rejected"]
    with pytest.raises(RuntimeError, match="cannot reuse an awaited guard result"):
        await deferred

    started = asyncio.Event()
    release = asyncio.Event()
    cancellation_calls: list[str] = []
    cancellations: list[asyncio.CancelledError] = []

    async def wait_for_cancellation() -> bool:
        cancellation_calls.append("blocking")
        started.set()
        try:
            await asyncio.wait_for(release.wait(), timeout=5)
        except asyncio.CancelledError as cancellation:
            cancellations.append(cancellation)
            raise
        return True

    deferred_cancellation = AndCondition(
        FuncCondition(wait_for_cancellation), FuncCondition(later)
    ).check()
    pending = asyncio.ensure_future(deferred_cancellation)
    await asyncio.wait_for(started.wait(), timeout=5)
    pending.cancel()
    with pytest.raises(asyncio.CancelledError) as cancelled:
        await pending
    assert cancellations == [cancelled.value]
    assert cancellation_calls == ["blocking"]


@pytest.mark.asyncio
async def test_reject_08_direct_async_leaf_and_fsm_boundary_have_distinct_owners() -> (
    None
):
    """REJECT-08: direct evaluation raises; the selector alone returns a result."""
    signal = TransitionRejected("battery.low")
    direct_calls: list[str] = []

    class RaisingAsyncCondition(AsyncCondition):
        __slots__ = ()

        def __init__(self) -> None:
            super().__init__("raising", "raises an expected rejection")

        async def check_async(self, *args: object, **kwargs: object) -> bool:
            direct_calls.append("rejected")
            raise signal

    direct = RaisingAsyncCondition()
    with pytest.raises(TransitionRejected) as raised:
        await direct.check_async()
    assert raised.value is signal

    source = State("source")
    target = State("target")
    machine = StateMachine(source, name="composition-rejection-boundary")
    machine.add_state(target)
    later_calls: list[str] = []

    def later() -> bool:
        later_calls.append("later")
        return True

    def reject() -> bool:
        raise signal

    machine.add_transition(
        "go", source, target, AndCondition(FuncCondition(reject), FuncCondition(later))
    )

    result = machine.trigger("go")

    assert result.rejected is True
    assert result.rejection_code == "battery.low"
    assert later_calls == []

    async_source = State("async-source")
    async_target = State("async-target")
    async_machine = AsyncStateMachine(
        async_source, name="async-composition-rejection-boundary"
    )
    async_machine.add_state(async_target)

    async def async_reject() -> bool:
        raise signal

    async_machine.add_transition(
        "go",
        async_source,
        async_target,
        AndCondition(FuncCondition(async_reject), FuncCondition(later)),
    )

    async_result = await async_machine.trigger_async("go")

    assert async_result.rejected is True
    assert async_result.rejection_code == "battery.low"
    assert later_calls == []


def test_unless_stores_canonical_not_condition_without_warning() -> None:
    source = State("source")
    machine = StateMachine(source)
    machine.add_state(State("target"))
    locked = FuncCondition(lambda *, locked=False: locked)

    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always")
        machine.add_transition("go", "source", "target", unless=locked)

    entry = machine._transitions["source"]["go"]
    assert type(entry.condition) is NotCondition
    assert entry.condition.condition is locked
    assert not record


@pytest.mark.parametrize(
    ("factory", "replacement"),
    [
        (lambda: NegatedCondition(FuncCondition(lambda: True)), "NotCondition"),
        (lambda: CompiledFuncCondition(lambda: True), "FuncCondition"),
        (AlwaysCondition, "omit condition"),
        (NeverCondition, "FuncCondition"),
        (lambda: KeyExistsCondition("payload"), "custom Condition"),
        (lambda: ValueInSetCondition("mode", {"safe"}), "custom Condition"),
        (lambda: RegexCondition("tag", ".*"), "custom Condition"),
        (lambda: ComparisonCondition("value", ">", 0), "custom Condition"),
        (lambda: TimeoutCondition(1.0), "after="),
        (lambda: CooldownCondition(1.0), "after="),
        (lambda: ElapsedCondition(1.0), "after="),
    ],
)
def test_legacy_conditions_warn_but_remain_constructible(
    factory, replacement: str
) -> None:
    with pytest.warns(DeprecationWarning, match=replacement):
        condition = factory()
    assert isinstance(condition, Condition)


def test_direct_timed_transition_uses_committed_entry_without_query_mutation() -> None:
    clock = FakeClock()
    source = State("source")
    machine = StateMachine(source, clock=clock)
    machine.add_state(State("target"))
    machine.add_transition("go", "source", "target", after=5.0)

    assert not machine.can_trigger("go")
    assert machine.current_state is source
    clock.now = 5.0
    assert machine.can_trigger("go")
    assert machine.trigger("go").success
