#!/usr/bin/env python3
"""
Collection of common TransitionCondition patterns for real-world usage
"""

import time

from .conditions import Condition
from typing import Any, Set
import re


class AlwaysCondition(Condition):
    """A condition that always passes - useful for explicit documentation"""

    __slots__ = ()

    def __init__(self):
        super().__init__("always", "Always allows transition")

    def check(self, **kwargs) -> bool:
        return True


class NeverCondition(Condition):
    """A condition that never passes - useful for disabling transitions"""

    __slots__ = ()

    def __init__(self):
        super().__init__("never", "Never allows transition")

    def check(self, **kwargs) -> bool:
        return False


class KeyExistsCondition(Condition):
    """Check if specific keys exist in the kwargs"""

    __slots__ = ("required_keys",)

    def __init__(self, *required_keys: str):
        keys_str = ", ".join(required_keys)
        super().__init__(
            f"keys_exist_{len(required_keys)}", f"Requires keys: {keys_str}"
        )
        self.required_keys = set(required_keys)

    def check(self, **kwargs) -> bool:
        return self.required_keys.issubset(kwargs.keys())


class ValueInSetCondition(Condition):
    """Check if a value is in a predefined set"""

    __slots__ = ("key", "valid_values")

    def __init__(self, key: str, valid_values: Set[Any]):
        values_str = ", ".join(str(v) for v in sorted(valid_values))
        super().__init__(f"{key}_in_set", f"{key} must be one of: {values_str}")
        self.key = key
        self.valid_values = valid_values

    def check(self, **kwargs) -> bool:
        return kwargs.get(self.key) in self.valid_values


class RegexCondition(Condition):
    """Check if a string value matches a regex pattern"""

    __slots__ = ("key", "pattern", "_compiled_regex")

    def __init__(self, key: str, pattern: str):
        super().__init__(f"{key}_regex", f"{key} must match pattern: {pattern}")
        self.key = key
        self.pattern = pattern
        self._compiled_regex = re.compile(pattern)

    def check(self, **kwargs) -> bool:
        value = kwargs.get(self.key, "")
        return bool(self._compiled_regex.match(str(value)))


class ComparisonCondition(Condition):
    """Generic comparison condition"""

    __slots__ = ("key", "operator", "target_value")

    def __init__(self, key: str, operator: str, target_value: Any):
        super().__init__(
            f"{key}_{operator}_{target_value}", f"{key} {operator} {target_value}"
        )
        self.key = key
        self.operator = operator
        self.target_value = target_value

    def check(self, **kwargs) -> bool:
        value = kwargs.get(self.key)
        if value is None:
            return False

        if self.operator == "==":
            return value == self.target_value
        elif self.operator == "!=":
            return value != self.target_value
        elif self.operator == "<":
            return value < self.target_value
        elif self.operator == "<=":
            return value <= self.target_value
        elif self.operator == ">":
            return value > self.target_value
        elif self.operator == ">=":
            return value >= self.target_value
        else:
            raise ValueError(f"Unsupported operator: {self.operator}")


class AndCondition(Condition):
    """Condition that requires ALL sub-conditions to be true"""

    __slots__ = ("conditions",)

    def __init__(self, *conditions: Condition):
        condition_names = [str(c) for c in conditions]
        super().__init__(
            f"and_{len(conditions)}", f"ALL of: {', '.join(condition_names)}"
        )
        self.conditions = conditions

    def check(self, **kwargs) -> bool:
        return all(condition.check(**kwargs) for condition in self.conditions)


class OrCondition(Condition):
    """Logical OR of multiple conditions"""

    __slots__ = ("conditions",)

    def __init__(self, *conditions: Condition):
        condition_names = [str(c) for c in conditions]
        super().__init__(
            f"or_{len(conditions)}", f"ANY of: {', '.join(condition_names)}"
        )
        self.conditions = conditions

    def check(self, **kwargs) -> bool:
        return any(condition.check(**kwargs) for condition in self.conditions)


class NotCondition(Condition):
    """Logical NOT of a condition"""

    __slots__ = ("condition",)

    def __init__(self, condition: Condition):
        super().__init__(f"not_{condition.name}", f"NOT {condition.description}")
        self.condition = condition

    def check(self, **kwargs) -> bool:
        return not self.condition.check(**kwargs)


class TimeoutCondition(Condition):
    """Allows transitions until a timeout expires. Returns True before timeout, False after."""

    __slots__ = ("seconds", "_ref")

    def __init__(self, seconds: float):
        super().__init__(f"timeout_{seconds}", f"Blocks after {seconds}s")
        self.seconds = seconds
        self._ref = time.monotonic()

    def check(self, **kwargs) -> bool:
        return (time.monotonic() - self._ref) < self.seconds

    def reset(self) -> None:
        self._ref = time.monotonic()


class CooldownCondition(Condition):
    """Enforces a minimum interval between successful checks. Passes on first call, then blocks until cooldown elapses since last success."""

    __slots__ = ("seconds", "_last_success")

    def __init__(self, seconds: float):
        super().__init__(f"cooldown_{seconds}", f"Minimum {seconds}s between successes")
        self.seconds = seconds
        self._last_success: float = 0.0

    def check(self, **kwargs) -> bool:
        now = time.monotonic()
        if (now - self._last_success) >= self.seconds:
            self._last_success = now
            return True
        return False

    def reset(self) -> None:
        self._last_success = 0.0


class ElapsedCondition(Condition):
    """Returns True once a minimum elapsed time has passed. Returns False before, True after."""

    __slots__ = ("seconds", "_ref")

    def __init__(self, seconds: float):
        super().__init__(f"elapsed_{seconds}", f"Passes after {seconds}s elapsed")
        self.seconds = seconds
        self._ref = time.monotonic()

    def check(self, **kwargs) -> bool:
        return (time.monotonic() - self._ref) >= self.seconds

    def reset(self) -> None:
        self._ref = time.monotonic()


# Demo function
def main():  # pragma: no cover
    print("📚 Common TransitionCondition Patterns")
    print("=" * 40)

    # Create example conditions
    always = AlwaysCondition()
    never = NeverCondition()

    keys_required = KeyExistsCondition("user_id", "session_token")
    status_valid = ValueInSetCondition("status", {"active", "pending", "verified"})
    email_format = RegexCondition(
        "email", r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    )

    age_check = ComparisonCondition("age", ">=", 18)
    amount_check = ComparisonCondition("amount", ">", 0)

    # Compound conditions
    valid_user = AndCondition(keys_required, status_valid)
    payment_or_admin = OrCondition(
        amount_check, ComparisonCondition("role", "==", "admin")
    )
    not_banned = NotCondition(ValueInSetCondition("status", {"banned", "suspended"}))

    conditions = [
        always,
        never,
        keys_required,
        status_valid,
        email_format,
        age_check,
        amount_check,
        valid_user,
        payment_or_admin,
        not_banned,
    ]

    print("\n🎯 Condition Examples:")
    for condition in conditions:
        print(f"• {condition} - {condition.description}")

    print("\n🧪 Testing conditions:")

    test_data = {
        "user_id": 123,
        "session_token": "abc123",
        "status": "active",
        "email": "user@example.com",
        "age": 25,
        "amount": 100,
        "role": "user",
    }

    print(f"Test data: {test_data}")
    print()

    for condition in conditions:
        result = condition.check(**test_data)
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {condition}")

    print("\n🔧 Usage in FSM:")
    print("fsm.add_transition('login', 'guest', 'user', condition=valid_user)")
    print(
        "fsm.add_transition('purchase', 'cart', 'payment', condition=payment_or_admin)"
    )
    print("fsm.add_transition('access', 'user', 'premium', condition=not_banned)")


if __name__ == "__main__":  # pragma: no cover
    main()
