# Changelog

All notable changes to Fast FSM are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added

#### Core API
- `StateMachine.on_enter(state_name, cb)` / `on_exit(state_name, cb)` — register
  per-state callbacks after construction; multiple callbacks per state, called in
  registration order.  Callbacks are shallow-copied by `clone()`.
- `StateMachine.force_state(name)` — teleport to any state, bypassing guards
  (full callback chain fires with trigger `"__force__"`).
- `StateMachine.reset()` — return to `initial_state_name`; full callback chain fires.
- `StateMachine.initial_state_name` property.
- `StateMachine.snapshot()` / `restore(snap)` — JSON- and pickle-safe state
  serialisation; `restore` teleports and fires callbacks.
- `StateMachine.clone()` — same topology, independent `current_state`, empty
  listeners; per-state callbacks are shallow-copied.
- `StateMachine.from_dict(config, *, name=None, conditions=None)` — build a machine
  from a plain dict / JSON / YAML config; `conditions=` maps trigger names to
  guards at construction time.
- `StateMachine.add_transition(…, unless=cond)` — negation shorthand; transition
  fires when `cond` is **False**.  Mutually exclusive with `condition=`.
- `StateMachine.add_transitions([…])` — accepts 4-tuples
  `(trigger, from_state(s), to_state, condition)` in addition to 3-tuples;
  backward-compatible.
- `StateMachine.add_bidirectional_transition(…, unless1=…, unless2=…)` — negation
  shorthands for both directions; mutually exclusive with `condition1`/`condition2`.
- `StateMachine.add_emergency_transition(…, unless=…)` — negation shorthand for
  emergency guards.
- `TransitionResult.raise_if_failed()` — raise `TransitionError` when the transition
  did not succeed; enables exception-based control flow.
- `TransitionError` exception class (importable from top-level `fast_fsm`).
- `StateMachine.is_in(*state_names)` — readable O(1) membership check.

#### AsyncStateMachine
- `AsyncStateMachine.on_enter_async(state_name, cb)` /
  `on_exit_async(state_name, cb)` — register async per-state callbacks; fire after
  all synchronous callbacks within the same `trigger_async()` call; exceptions
  are caught and logged.
- `AsyncStateMachine.clone()` — overrides base to also copy the two async callback
  dicts.
- `AsyncCondition` instances are now **rejected with `TypeError`** when passed to a
  sync `StateMachine.add_transition` (including via `from_dict(conditions=)` and
  `FSMBuilder` in explicit-sync mode).  Previously they silently fell back to
  `asyncio.run()`, which misbehaves inside running event loops.

#### FSMBuilder
- `.on_enter(state_name, cb)` / `.on_exit(state_name, cb)` — fluent, synchronous
  per-state callback registration; callbacks wired in `build()`.  Returns `self`.
- `.on_enter_async(state_name, cb)` / `.on_exit_async(state_name, cb)` — fluent,
  async per-state callback registration; auto-upgrades auto-detect builder to
  `AsyncStateMachine`; wired in `build()`.  Returns `self`.

#### Conditions
- `CompiledFuncCondition` — mypyc-compiled `FuncCondition` drop-in for hot-path
  guards; same interface, ~2–3× faster `check()`.
- `NegatedCondition` — wraps any `Condition` and inverts its result; used
  internally by `unless=`.

#### Validation (`fast_fsm.validation`)
- `EnhancedFSMValidator.design_style_threshold` — tunable percentage cut-off
  separating sparse from dense FSMs (default `0.3`).
- `EnhancedFSMValidator.min_transitions_for_style` — minimum transition count
  before style classification is applied (default `3`).
- `EnhancedFSMValidator.completeness_weight` — blend factor (0.0–1.0) controlling
  how much completeness score influences `overall_score` (default `0.3`).

#### mypyc / build
- AST-based `mypyc_guard` prevents accidental subclassing of mypyc-compiled
  classes from interpreted Python (raises `TypeError` with a clear message).

### Fixed
- `AsyncCondition` passed to sync `StateMachine.add_transition` (or `from_dict`,
  `FSMBuilder` in sync mode) now raises `TypeError` instead of silently using
  `asyncio.run()`.
- `docs/api/visualization.md` was wrapped in a stray ```` ```markdown ```` fence,
  causing a Sphinx toctree warning on every build.  Outer fence removed.
- `clone()` docstring updated to clarify which callback structures are copied
  (per-state callback dicts are shallow-copied; listener objects are not).

### Documentation
- Sphinx docs (furo theme) with full autodoc API reference, Quick Start, Tutorial,
  FSM Linking Techniques guide, Examples gallery, and Developer Guide.
- "Tuning the Validator" section in `docs/api/validation.md`.
- `sphinx.ext.doctest` infrastructure — `{testcode}` / `{testoutput}` blocks
  verified on every `task docs-test` run.

---

## [0.1.0] — Initial release

- Core `StateMachine` with `__slots__`, O(1) `trigger()` / `add_transition()` /
  `add_state()`.
- `AsyncStateMachine` with `trigger_async()` and `AsyncCondition`.
- `FSMBuilder` fluent builder with auto-async detection.
- `DeclarativeState` / `AsyncDeclarativeState` with `@transition` decorator.
- `CallbackState` with `on_enter` / `on_exit` constructor kwargs.
- `Condition`, `FuncCondition`, `AsyncCondition` base classes.
- `condition_templates` reusable guard builders.
- `FSMValidator` / `EnhancedFSMValidator` design-time validation, scoring, lint,
  adjacency matrix.
- `to_mermaid` / `to_mermaid_fenced` / `to_mermaid_document` visualisation helpers.
- `simple_fsm` / `quick_fsm` factory helpers.
- mypyc compilation of `core.py`; `conditions.py` stays interpreted for
  user subclassing.
- 290 tests; `ty` + `ruff` clean.
