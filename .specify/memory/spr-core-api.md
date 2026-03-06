# SPR: StateMachine core API

**Category**: core-api  
**Created**: 2026-03-06  
**Updated**: 2026-03-06 (added force_state / reset / initial_state_name / snapshot / restore / clone / on_enter / on_exit / from_dict / raise_if_failed / CompiledFuncCondition)

- `StateMachine` and all hot-path classes use `__slots__`; dynamic attribute assignment on core objects is prohibited.
- Core operations (`trigger`, `can_trigger`, `add_state`, `add_transition`) are O(1) via direct dict lookup; throughput target ≥ 250,000 ops/sec.
- `TransitionEntry(to_state, condition)` is the internal container replacing raw dicts; slots-optimised.
- `trigger()` returns `TransitionResult(success, from_state, to_state, trigger, error)`; never raises by default.
- `safe_trigger()` wraps `trigger()` in try/except; never raises under any circumstance.
- `add_transition(trigger, from_state, to_state, condition=None, *, unless=None)` — `unless=` is a negation shorthand, mutually exclusive with `condition=`.
- `from_state` accepts a string, `State` object, or list of either; fan-out to multiple sources in one call.
- `add_bidirectional_transition(t1, t2, s1, s2, c1, c2)` registers two directed transitions; thin convenience wrapper, no special internal representation.
- `add_emergency_transition(trigger, to_state)` fans from all current states to one target.
- `add_transitions(list_of_tuples)` batch-registers `(trigger, from, to)` tuples.
- `StateMachine.from_transitions(transitions, initial_state)` classmethod builds a machine from a flat list.
- `is_in(state)` — O(1) identity/name check against `_current_state`.
- `can_trigger(trigger)` — evaluates guard condition synchronously before committing; use for pre-flight checks.
- Listener protocol: objects with `on_exit_state`, `on_enter_state`, `after_transition` methods; registered via `add_listener(*listeners)`.
- `AsyncStateMachine` subclasses `StateMachine`; adds `trigger_async` and `can_trigger_async`; auto-detects `AsyncCondition`.
- `FSMBuilder` fluent builder; auto-detects async requirement from states/conditions; `force_async()` / `force_sync()` override; `build()` is idempotent.
- `CallbackState` extends `State` with `_on_enter` / `_on_exit` slots; use when state-level callbacks needed without losing slots optimisation.
- `DeclarativeState` enables `@transition`-decorated methods on state classes; auto-discovers via `_discover_handlers()`.
- mypyc compiles `core.py` only; `conditions.py` and `condition_templates.py` must stay interpreted (users subclass `Condition` from Python).
- `_sanitize_condition_kwargs` strips private kwargs (leading `_`) and caps at 50 items before passing to conditions.
- `force_state(name)` sets `_current_state` directly without guard checks; fires full on_exit / on_enter / after_transition callback chain with synthetic trigger `"__force__"`; raises `KeyError` for unregistered state names.
- `reset()` calls `force_state(initial_state_name)`; fires callbacks even when already in initial state.
- `initial_state_name` read-only property returns the name of the state passed to `__init__`; stored in `_initial_state` slot.
- `snapshot()` returns `{"state": current_state_name, "version": 1}`; JSON-serialisable, safe to pickle.
- `restore(snapshot)` validates version/type then calls `force_state(snapshot["state"])`; raises `ValueError` for bad version or non-string state, `KeyError` for unregistered state.
- `clone()` returns a new instance of the same class with identical topology (shared `State` and `TransitionEntry` objects, independent inner transition dicts), current state at initial, empty listener lists; per-state callbacks are shallow-copied.
- `on_enter(state_name, fn)` registers a per-state callback fired after `State.on_enter` and before `on_enter_state` listeners. Signature: `fn(from_state, trigger, **kwargs)`. Multiple callbacks fire in registration order.
- `on_exit(state_name, fn)` registers a per-state callback fired after `State.on_exit` and before `on_exit_state` listeners. Signature: `fn(to_state, trigger, **kwargs)`. Both are stored in `_state_enter_callbacks` / `_state_exit_callbacks` slots (`Dict[str, List]`).
- Callback exception safety: exceptions in per-state callbacks are caught and logged as warnings, not re-raised; the transition still completes.
- `from_dict(config, *, name=None)` classmethod builds a machine from a plain dict; required keys: `"initial"` (str), `"transitions"` (list of `{"trigger", "from", "to"}`); optional keys: `"name"` (str), `"states"` (list of extra state names for isolated/terminal states). `"from"` may be a string or a list of strings (fan-out). Internally uses `from_states` + `add_transition`, bypassing `quick_build`'s typed tuple constraint.
- `TransitionResult.raise_if_failed()` returns `self` unchanged on success (enabling one-liner chaining like `.raise_if_failed().to_state`); raises `TransitionError` on failure. `TransitionError(RuntimeError)` carries the originating result as `.result` attribute; message includes trigger, from_state, and error string. Decorated `@mypyc_attr(native_class=False)` because mypyc cannot natively compile `RuntimeError` subclasses.
- `CompiledFuncCondition(func, *, name=None, description="")` — opt-in compiled callable wrapper in `core.py`; its `check()` method body is compiled to native code by mypyc, reducing per-call dispatch overhead vs the interpreted `FuncCondition`. Uses `@mypyc_attr(native_class=False)` to avoid `__slots__` conflicts when subclassing the uncompiled `Condition` ABC; attribute storage is `__dict__`-based. Drop-in replacement for `FuncCondition` when profiling shows guard evaluation is a bottleneck. Subclassable from interpreted Python (unlike fully-native mypyc classes).
