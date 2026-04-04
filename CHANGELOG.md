# Changelog

All notable changes to Fast FSM are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added

#### Callback / Hook API
- `StateMachine.after_transition(fn)` — convenience method; appends `fn` directly to
  the after-transition listener list without creating a listener class.
  Signature: `fn(source, target, trigger, **kwargs)`.
- `StateMachine.on_failed(fn)` — register a callback that fires whenever `trigger()` or
  `trigger_async()` returns a failed result (wrong state, condition blocked, unknown
  trigger).  Signature: `fn(trigger, from_state, error, **kwargs)`.
  Not copied by `clone()` — intentional, consistent with listener lists.
- `StateMachine.on_trigger(trigger_name, fn)` — per-trigger callback fired after every
  *successful* transition for the named trigger.  Signature:
  `fn(from_state, to_state, trigger, **kwargs)`.  Copied by `clone()`.
- `before_transition` listener protocol slot — add `before_transition(source, target,
  trigger, **kwargs)` to any listener object passed to `add_listener()` to receive a
  hook that fires at the very start of `_execute_transition()`, before any `on_exit`
  callback.

#### CI / Build
- Python 3.14 added to test matrix (`ci.yml`) and compiled wheel build (`release.yml`,
  `cp314-*`).
- `mypy[mypyc]` lower bound bumped to `>=1.17` (required for Python 3.14 mypyc support).

### Changed

- `set_fsm_logging_level()` now accepts standard Python logging level names:
  `'debug'`, `'info'`, `'warning'`, `'error'`, `'critical'`.  Convenience aliases
  `'off'` (→ WARNING) and `'trace'` (→ DEBUG−5 ultra-verbose) are retained.  The
  old `'basic'` / `'detailed'` / `'ultra'` vocabulary has been **removed**.
  Input is now case-insensitive.
- Default parameter for `set_fsm_logging_level()` changed from `'off'` to
  `'warning'` (explicit).
- All per-transition log calls moved from `INFO` to `DEBUG` — library consumers
  calling `logging.basicConfig(level=logging.INFO)` will no longer see FSM
  transition noise in their application logs.

---

## [0.2.1] — 2026-04-04

### Changed

- `__version__` now derived dynamically from package metadata via `importlib.metadata`
  so version string and `pyproject.toml` can never drift.
- `condition_templates.py` uses relative import (`from .conditions import Condition`)
  for consistency and source-install compatibility.
- `State` no longer inherits from `abc.ABC` — no abstract methods were defined;
  direct instantiation (`State("name")`) is the primary usage pattern.
- All 16 `except Exception` catches in `core.py` annotated with inline comments
  explaining the intentional broad-catch rationale (callback/condition isolation).
- `safe_trigger()` docstring now fully documents exception isolation semantics vs
  `trigger()`.

### Added

- `src/fast_fsm/py.typed` — PEP 561 marker; mypy/pyright now recognise fast_fsm
  as a typed package after installation.
- `test_trigger_min_throughput` — hot-path throughput regression gate (200k ops/sec
  floor compiled, 30k pure-Python); marked `@pytest.mark.slow`.
- `benchmark` CI job — compiles mypyc extension and runs `@pytest.mark.slow` tests
  on every push to `main`.

### Removed

- 4 low-value/redundant tests pruned; test count 637 → 634 (net, including new
  benchmark test).

---
## [0.2.0] — 2026-03-06

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
