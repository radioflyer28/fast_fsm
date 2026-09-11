"""Public contract tests for the focused condition interface."""

from __future__ import annotations

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
    StateMachine,
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
