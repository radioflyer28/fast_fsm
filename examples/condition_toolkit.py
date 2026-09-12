#!/usr/bin/env python3
"""Tier 2: compose focused conditions, priorities, and transition timing."""

from fast_fsm import FuncCondition, State, StateMachine


class FakeClock:
    """A deterministic monotonic clock for an executable timing example."""

    __slots__ = ("now",)

    def __init__(self, now: float = 0.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now


def main() -> None:
    draft = State("draft")
    approvals = StateMachine(draft, name="ApprovalFlow")
    approvals.add_state(State("approved"))
    approvals.add_state(State("manual_review"))

    has_identity = FuncCondition(
        lambda *, user_id=None, **_: user_id is not None,
        name="has_identity",
    )
    adult = FuncCondition(lambda *, age=0, **_: age >= 18, name="is_adult")
    known_role = FuncCondition(
        lambda *, role="", **_: role in {"editor", "owner"},
        name="known_role",
    )
    is_blocked = FuncCondition(
        lambda *, status="", **_: status == "blocked",
        name="is_blocked",
    )
    eligible = has_identity & adult & known_role & ~is_blocked
    needs_review = is_blocked | ~adult

    approvals.add_transition(
        "approve",
        "draft",
        "manual_review",
        condition=needs_review,
        priority=0,
    )
    approvals.add_transition(
        "approve",
        "draft",
        "approved",
        condition=eligible,
        priority=10,
    )
    review = approvals.trigger("approve", user_id=7, role="editor", age=17)
    print(f"under_age={review.success} destination={approvals.current_state.name}")

    approvals.reset()
    accepted = approvals.trigger(
        "approve", user_id=7, role="editor", age=22, status="active"
    )
    print(f"eligible={accepted.success} destination={approvals.current_state.name}")

    clock = FakeClock()
    pending = StateMachine(State("pending"), name="TimedRelease", clock=clock)
    pending.add_state(State("ready"))
    pending.add_transition("release", "pending", "ready", after=5.0, within=10.0)

    print(f"release_at_0={pending.can_trigger('release')}")
    clock.now = 5.0
    print(f"release_at_5={pending.trigger('release').success}")


if __name__ == "__main__":
    main()
