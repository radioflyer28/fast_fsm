#!/usr/bin/env python3
"""Tier 2: compose reusable, negated, and time-aware transition conditions."""

import time

from fast_fsm import CooldownCondition, ElapsedCondition, State, StateMachine
from fast_fsm.condition_templates import (
    AndCondition,
    ComparisonCondition,
    KeyExistsCondition,
    NotCondition,
    ValueInSetCondition,
)


def main() -> None:
    draft = State("Draft")
    approvals = StateMachine(draft, name="ApprovalFlow")
    approvals.add_state(State("Approved"))

    has_identity = KeyExistsCondition("user_id", "role")
    adult = ComparisonCondition("age", ">=", 18)
    known_role = ValueInSetCondition("role", {"editor", "owner"})
    blocked = ValueInSetCondition("status", {"blocked"})
    eligible = AndCondition(has_identity, adult, known_role, NotCondition(blocked))
    approvals.add_transition("approve", "Draft", "Approved", eligible)

    denied = approvals.trigger(
        "approve", user_id=7, role="editor", age=17, status="active"
    )
    print(f"under-age approval={denied.success}")
    accepted = approvals.trigger(
        "approve", user_id=7, role="editor", age=22, status="active"
    )
    print(f"eligible approval={accepted.success}")

    cooldown = CooldownCondition(0.01)
    print(f"cooldown first={cooldown.check()} immediate={cooldown.check()}")
    time.sleep(0.012)
    print(f"cooldown later={cooldown.check()}")

    elapsed = ElapsedCondition(0.01)
    print(f"elapsed immediate={elapsed.check()}")
    time.sleep(0.012)
    print(f"elapsed later={elapsed.check()}")


if __name__ == "__main__":
    main()
