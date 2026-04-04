---
phase: 260404-exx
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - src/fast_fsm/core.py
  - tests/test_listeners.py
  - tests/test_advanced_functionality.py
autonomous: true
requirements:
  - QUICK-260404-EXX
must_haves:
  truths:
    - "before_transition listener method fires before on_exit_state in _execute_transition()"
    - "before_transition is NOT called when a trigger is blocked (no matching transition, condition fail)"
    - "fsm.after_transition(fn) convenience method appends to _after_listeners and fires after successful transitions"
    - "fsm.on_failed(fn) fires for every failure return path in trigger() and trigger_async()"
    - "fsm.on_failed(fn) is NOT called on successful transitions"
    - "fsm.on_trigger(name, fn) fires only for the matching trigger name after a successful transition"
    - "fsm.on_trigger(name, fn) is NOT called when the trigger fails or when a different trigger fires"
    - "clone() copies _trigger_callbacks but does NOT copy _before_listeners or _on_failed_callbacks"
  artifacts:
    - path: "src/fast_fsm/core.py"
      provides: "New slots (_before_listeners, _on_failed_callbacks, _trigger_callbacks) and methods"
      contains: "_before_listeners"
    - path: "tests/test_listeners.py"
      provides: "Tests for before_transition listener protocol hook"
      contains: "before_transition"
    - path: "tests/test_advanced_functionality.py"
      provides: "Tests for after_transition convenience method, on_failed, on_trigger"
      contains: "on_failed"
  key_links:
    - from: "StateMachine._execute_transition()"
      to: "_before_listeners"
      via: "fired at start of _execute_transition before on_exit callback"
      pattern: "_before_listeners"
    - from: "StateMachine.trigger() / trigger_async()"
      to: "_on_failed_callbacks"
      via: "fired at every early-return failure path"
      pattern: "_on_failed_callbacks"
    - from: "StateMachine._execute_transition()"
      to: "_trigger_callbacks"
      via: "fired after _after_listeners loop, keyed by trigger name"
      pattern: "_trigger_callbacks"
    - from: "StateMachine.add_listener()"
      to: "_before_listeners"
      via: "extracts before_transition attribute from listener objects"
      pattern: "before_transition"
    - from: "StateMachine.clone()"
      to: "_trigger_callbacks"
      via: "deep-copies the per-trigger callback dict into the new instance"
      pattern: "clone"
---

<objective>
Add four missing callback/hook capabilities to StateMachine (and AsyncStateMachine):

1. `before_transition` listener protocol slot — fires at start of `_execute_transition()`.
2. `after_transition(fn)` convenience method — direct append to `_after_listeners`.
3. `on_failed(fn)` method + `_on_failed_callbacks` slot — fires on every failed trigger path.
4. `on_trigger(name, fn)` method + `_trigger_callbacks` slot — fires after successful transition for matching trigger name.

Purpose: Close the ergonomic gaps in the listener/callback API so users can observe blocked triggers, react to specific trigger names, and register inline callbacks without subclassing a listener object.
Output: Updated `core.py` (rebuilt with mypyc), tests in test_listeners.py and test_advanced_functionality.py.
</objective>

<execution_context>
@.github/copilot-instructions.md
</execution_context>

<context>
@src/fast_fsm/core.py
@tests/test_listeners.py
@tests/test_advanced_functionality.py

<interfaces>
<!-- Key slots and conventions inferred from codebase context -->

StateMachine.__slots__ currently:
  _name, _initial_state, _current_state, _states, _transitions, _logger,
  _on_exit_listeners, _on_enter_listeners, _after_listeners,
  _state_exit_callbacks, _state_enter_callbacks

Listener protocol currently extracted in add_listener():
  - on_exit_state   → _on_exit_listeners
  - on_enter_state  → _on_enter_listeners
  - after_transition → _after_listeners

_execute_transition() fire order (current):
  1. on_exit callback (CallbackState)
  2. _state_exit_callbacks[source]
  3. _on_exit_listeners → fn(source, target, trigger, **kwargs)
  4. [state change: _current_state = target]
  5. on_enter callback (CallbackState)
  6. _state_enter_callbacks[target]
  7. _on_enter_listeners → fn(source, target, trigger, **kwargs)
  8. _after_listeners → fn(source, target, trigger, **kwargs)

trigger() early-return failure paths:
  - No matching transition (returns FAILED TransitionResult)
  - Condition check fails
  - can_transition check fails

clone() copies: topology, _state_exit_callbacks, _state_enter_callbacks
clone() does NOT copy: _on_exit_listeners, _on_enter_listeners, _after_listeners

Existing convenience methods for reference:
  fsm.on_enter(state_name, callback)  → appends to _state_enter_callbacks[state_name]
  fsm.on_exit(state_name, callback)   → appends to _state_exit_callbacks[state_name]
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Implement four hooks in core.py (StateMachine + AsyncStateMachine)</name>
  <files>src/fast_fsm/core.py</files>
  <action>
Read core.py fully before editing to understand exact slot declarations, __init__ bodies, add_listener(), _execute_transition(), trigger(), trigger_async(), and clone().

**A. New slots — add to StateMachine.__slots__ (keep alphabetical or grouped with similar):**
```
"_before_listeners",      # List[Any] — before_transition protocol callbacks
"_on_failed_callbacks",   # List[Any] — on_failed direct callbacks
"_trigger_callbacks",     # Dict[str, List[Any]] — per-trigger-name callbacks
```

**B. __init__ — initialize the three new slots:**
```python
self._before_listeners: list = []
self._on_failed_callbacks: list = []
self._trigger_callbacks: dict = {}
```
(Use the same style as the existing listener list initializations.)

**C. add_listener() — extract `before_transition` from listener objects:**
In the loop that checks for `on_exit_state`, `on_enter_state`, `after_transition` on each listener, add:
```python
if hasattr(listener, "before_transition"):
    self._before_listeners.append(listener.before_transition)
```

**D. New convenience methods (after existing on_enter/on_exit methods):**
```python
def after_transition(self, callback: Any) -> None:
    """Register a callback fired after every successful transition.

    Args:
        callback: Callable fn(source, target, trigger, **kwargs).
    """
    self._after_listeners.append(callback)

def on_failed(self, callback: Any) -> None:
    """Register a callback fired whenever trigger() returns a failed result.

    Args:
        callback: Callable fn(trigger, from_state, error, **kwargs).
    """
    self._on_failed_callbacks.append(callback)

def on_trigger(self, trigger_name: str, callback: Any) -> None:
    """Register a callback fired after a successful transition for trigger_name.

    Args:
        trigger_name: The trigger name to watch.
        callback: Callable fn(from_state, to_state, trigger, **kwargs).
    """
    if trigger_name not in self._trigger_callbacks:
        self._trigger_callbacks[trigger_name] = []
    self._trigger_callbacks[trigger_name].append(callback)
```

**E. _execute_transition() — fire _before_listeners at the very start (before on_exit):**
Insert at the top of `_execute_transition()`, before any existing callback fires:
```python
for fn in self._before_listeners:
    try:
        fn(source, target, trigger, **kwargs)
    except Exception as e:
        self._logger.error("before_transition listener error: %s", e)
```
Use `source` / `target` / `trigger` / `**kwargs` to match the method's parameter names (read the actual signature first and match exactly).

After the existing `_after_listeners` loop, fire per-trigger callbacks:
```python
if trigger in self._trigger_callbacks:
    for fn in self._trigger_callbacks[trigger]:
        try:
            fn(source, target, trigger, **kwargs)
        except Exception as e:
            self._logger.error("on_trigger callback error: %s", e)
```

**F. trigger() — fire _on_failed_callbacks at every early-return failure path:**
At each point where trigger() currently returns a failed/empty TransitionResult WITHOUT having called _execute_transition(), insert (before or after the return, still in the method body):
```python
for fn in self._on_failed_callbacks:
    try:
        fn(trigger, self._current_state, <error_string>, **kwargs)
    except Exception as e:
        self._logger.error("on_failed callback error: %s", e)
```
Use a descriptive error string matching the failure reason (e.g., "no matching transition", "condition failed", "can_transition blocked").

**G. trigger_async() — same _on_failed_callbacks wiring as trigger():**
Apply the identical pattern to all failure return paths in trigger_async().

**H. clone() — copy _trigger_callbacks, skip _before_listeners and _on_failed_callbacks:**
In the clone() method body, add copying of `_trigger_callbacks`:
```python
# Copy per-trigger callbacks (shallow copy of the outer dict; deep copy inner lists)
for tname, cbs in self._trigger_callbacks.items():
    new_fsm._trigger_callbacks[tname] = list(cbs)
```
Do NOT copy `_before_listeners` or `_on_failed_callbacks` — consistent with existing listener list behaviour in clone().

**I. AsyncStateMachine — apply the same changes:**
AsyncStateMachine inherits or duplicates many of these. Check carefully:
- If AsyncStateMachine has its own __slots__, add the three new slots there too.
- If it has its own __init__, initialize the three new lists/dicts.
- If it has its own add_listener(), patch the `before_transition` extraction there too.
- Its trigger_async() already exists — apply the _on_failed_callbacks pattern there.
- If it has its own _execute_transition (async variant), apply _before_listeners and _trigger_callbacks firing there.
- If it has its own clone(), apply the _trigger_callbacks copy there.

After editing, rebuild with mypyc:
```bash
uv run python setup.py build_ext --inplace -q
```
  </action>
  <verify>
    <automated>uv run python setup.py build_ext --inplace -q && uv run python -c "from fast_fsm import StateMachine; sm = StateMachine('t','s'); sm.add_state('s'); sm.after_transition(lambda *a,**k: None); sm.on_failed(lambda *a,**k: None); sm.on_trigger('go', lambda *a,**k: None); print('slots OK')"</automated>
  </verify>
  <done>
    - StateMachine has _before_listeners, _on_failed_callbacks, _trigger_callbacks slots
    - after_transition(), on_failed(), on_trigger() methods exist and are callable
    - mypyc build succeeds with no errors
  </done>
</task>

<task type="auto">
  <name>Task 2: Write tests for all four hooks</name>
  <files>tests/test_listeners.py, tests/test_advanced_functionality.py</files>
  <action>
Read both test files first to understand fixture patterns and helper FSM setups, then APPEND tests (do not modify existing tests).

**In tests/test_listeners.py — add a section for `before_transition` listener protocol:**

Test class/functions to add:

1. `test_before_transition_fires_before_on_exit_state`:
   Create a listener class with `before_transition`, `on_exit_state`, and `after_transition` methods that record call order via a list. Add to fsm via add_listener(). Fire a valid trigger. Assert `before_transition` index < `on_exit_state` index < `after_transition` index.

2. `test_before_transition_not_called_on_blocked_trigger`:
   Create listener with `before_transition` that records calls. Attempt a trigger that has no matching transition (wrong state or nonexistent trigger). Assert `before_transition` was never called.

3. `test_before_transition_receives_correct_args`:
   Verify signature: listener receives `(source: State, target: State, trigger: str)`. Assert types and values match expected states.

**In tests/test_advanced_functionality.py — add tests for convenience methods:**

4. `test_after_transition_convenience_fires_after_success`:
   Use `fsm.after_transition(fn)` (inline lambda/mock). Fire valid trigger. Assert fn was called exactly once with correct source, target, trigger args.

5. `test_on_failed_fires_on_no_matching_transition`:
   Register `fsm.on_failed(fn)`. Trigger a non-existent trigger name. Assert fn called.

6. `test_on_failed_fires_on_condition_fail`:
   Register a condition that always returns False. Register `fsm.on_failed(fn)`. Fire the guarded trigger. Assert fn called.

7. `test_on_failed_not_called_on_success`:
   Register `fsm.on_failed(fn)`. Fire a valid transition. Assert fn was NOT called.

8. `test_on_trigger_fires_for_matching_trigger`:
   `fsm.on_trigger("go", fn)`. Fire "go". Assert fn called.

9. `test_on_trigger_not_fires_for_different_trigger`:
   `fsm.on_trigger("go", fn)`. Fire "stop" (different trigger). Assert fn NOT called.

10. `test_on_trigger_not_called_on_failed_transition`:
    `fsm.on_trigger("go", fn)`. Trigger "go" when in wrong state (blocked). Assert fn NOT called.

11. `test_clone_copies_trigger_callbacks`:
    Register `fsm.on_trigger("go", fn)`. Clone the FSM. Fire "go" on clone. Assert fn called.

12. `test_clone_does_not_copy_before_listeners`:
    Register a listener with `before_transition` via `add_listener()`. Clone the FSM. Verify the clone's `_before_listeners` list is empty.

13. `test_clone_does_not_copy_on_failed_callbacks`:
    Register `fsm.on_failed(fn)`. Clone the FSM. Trigger a bad trigger on clone. Assert fn NOT called on the clone.

Use simple call-counting: `calls = []` and `fn = lambda *a, **k: calls.append(a)` pattern (consistent with existing tests).
  </action>
  <verify>
    <automated>uv run pytest tests/test_listeners.py tests/test_advanced_functionality.py -x -q 2>&1 | tail -20</automated>
  </verify>
  <done>
    - All 13 new tests pass
    - No existing tests broken in the two test files
  </done>
</task>

<task type="auto">
  <name>Task 3: Full regression suite</name>
  <files></files>
  <action>
Run the complete test suite to confirm no regressions across all modules. If any failures appear, read the failing test, trace back to core.py, and fix without altering test expectations.
  </action>
  <verify>
    <automated>uv run pytest tests/ -x -q 2>&1 | tail -10</automated>
  </verify>
  <done>
    - All 636+ tests pass (new tests raise the count above 636)
    - 0 failures, 0 errors
  </done>
</task>

</tasks>

<verification>
1. `uv run python setup.py build_ext --inplace -q` exits 0
2. Import check: `from fast_fsm import StateMachine; sm = StateMachine('t','s'); sm.add_state('s')` — all four methods available
3. `uv run pytest tests/test_listeners.py tests/test_advanced_functionality.py -x -q` — all new tests pass
4. `uv run pytest tests/ -x -q` — full suite green
</verification>

<success_criteria>
- StateMachine and AsyncStateMachine have three new slots: `_before_listeners`, `_on_failed_callbacks`, `_trigger_callbacks`
- Four public methods added: `after_transition()`, `on_failed()`, `on_trigger()`, plus `before_transition` extracted in `add_listener()`
- Execution order: before_transition → on_exit → … → after_transition → on_trigger callbacks
- on_failed fires exclusively on failed paths; never on success
- clone() preserves per-trigger callbacks; drops listener/on_failed lists
- mypyc build clean; full test suite passes (count ≥ 637)
</success_criteria>

<output>
After completion, create `.planning/quick/260404-exx-fill-callback-hook-gaps-before-transitio/260404-exx-SUMMARY.md`
</output>
