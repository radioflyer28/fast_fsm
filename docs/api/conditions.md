# Conditions API

Conditions answer one focused question: whether an event may take a particular
transition. Keep each rule named, small, and independent of the machine that
uses it. A condition receives the same `*args, **kwargs` supplied to
`trigger()`.

## Recommended interface

Use these six public building blocks for new code:

- `Condition` for a reusable domain rule with its own state or validation.
- `FuncCondition` to give an ordinary predicate a stable name.
- `AsyncCondition` for a rule that must await I/O; use it with
  `AsyncStateMachine`.
- `AndCondition`, `OrCondition`, and `NotCondition` for explicit composition.

The operators `&`, `|`, and `~` create the same canonical composition types.
They preserve ordinary left-to-right short-circuiting, so a failed left side of
an `AndCondition` does not evaluate its right side.

```python
from fast_fsm import FuncCondition

has_identity = FuncCondition(
    lambda *, user_id=None, **_: user_id is not None,
    name="has_identity",
)
has_credit = FuncCondition(
    lambda *, credit=0, cost=0, **_: credit >= cost,
    name="has_credit",
)
eligible = has_identity & has_credit
not_blocked = ~FuncCondition(
    lambda *, blocked=False, **_: blocked,
    name="is_blocked",
)
checkout_rule = eligible & not_blocked
```

For a complete custom-condition example, including a condition with an
injected clock, see
[`custom_conditions.py`](../../examples/custom_conditions.py). For a compact
tour of composition, priority candidates, and entry timing, see
[`condition_toolkit.py`](../../examples/condition_toolkit.py).

```{eval-rst}
.. autoclass:: fast_fsm.Condition
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: fast_fsm.FuncCondition
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: fast_fsm.AsyncCondition
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: fast_fsm.AndCondition
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: fast_fsm.OrCondition
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: fast_fsm.NotCondition
   :members:
   :undoc-members:
   :show-inheritance:
```

## Transition-entry timing

Timing is transition metadata, not mutable guard state. Add `after=` to delay
eligibility from the moment the source state was entered, `within=` to set an
exclusive deadline, or both for a half-open `[after, within)` window. Values
must be finite, non-negative built-in numbers and `after` must be less than
`within` when both are supplied.

```python
machine.add_transition(
    "release",
    "pending",
    "ready",
    condition=checkout_rule,
    after=5.0,
    within=30.0,
)
```

Each machine owns an injectable monotonic clock. Selection reads it once for a
timed direct transition or local priority group; `can_trigger()` never changes
the entry timestamp. Untimed singleton transitions do not sample the clock.

## Compatibility imports

The previous template collection remains importable so existing applications
can migrate gradually. `NegatedCondition`, `CompiledFuncCondition`, and the
leaves in `fast_fsm.condition_templates` emit `DeprecationWarning` when they
are constructed. They remain supported until no earlier than the next major
release, but new code should use the focused interface above and model domain
rules with `Condition` or `FuncCondition`.

`NegatedCondition` stays as a deprecated constructor; use canonical
`NotCondition` (or `~rule`) for new code. Replace mutable timeout, cooldown,
and elapsed template objects with `after=` and `within=` on the transition
that owns the policy.
