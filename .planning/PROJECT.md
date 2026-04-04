# Fast FSM

## What This Is

High-performance, memory-efficient finite state machine library for Python. Outperforms popular alternatives (python-statemachine, transitions) by 5–20× in speed and ~1000× in memory usage through `__slots__` optimization, direct dictionary lookups, and minimal abstraction layers. Targets Python ≥3.10.

## Core Value

Blazing-fast, zero-overhead FSM transitions — `trigger()` must stay ≥200,000 ops/sec and all core operations must remain O(1).

## Current Milestone: v0.2.1 Code Health & Quality

**Goal:** Resolve technical debt and correctness concerns identified in the codebase audit — version hygiene, exception handling posture, type annotations, import consistency, `State` ABC cleanup, and test suite quality — without touching the public API.

**Target features:**
- Automated version sync between `pyproject.toml` and `__version__`
- Exception handling audit and documentation of intent
- `py.typed` PEP 561 marker (with pure-Python fallback safety)
- `condition_templates.py` relative import fix
- Remove misleading `ABC` base from `State`
- Test suite triage — remove/consolidate low-value tests, document gaps
- Benchmark regression job in CI

## Requirements

### Validated

- ✓ `StateMachine` with O(1) `trigger()`, `can_trigger()`, `add_state()`, `add_transition()` — existing
- ✓ `AsyncStateMachine` with `trigger_async()` and async condition/callback support — existing
- ✓ `FSMBuilder` fluent builder with auto async detection — existing
- ✓ `DeclarativeState` / `AsyncDeclarativeState` convention-based state handling — existing
- ✓ `Condition` ABC, `FuncCondition`, `CompiledFuncCondition`, `AsyncCondition`, `NegatedCondition` — existing
- ✓ `condition_templates.py` reusable condition patterns — existing
- ✓ `FSMValidator` / `EnhancedFSMValidator` design-time analysis and scoring — existing
- ✓ `visualization.py` Mermaid diagram generation — existing
- ✓ `TransitionResult.raise_if_failed()` exception-style flow — existing
- ✓ `StateMachine.snapshot()` / `restore()` / `clone()` — existing
- ✓ `StateMachine.from_dict()` / `quick_build()` / `from_states()` factories — existing
- ✓ Per-state callbacks via `on_enter()` / `on_exit()` — existing
- ✓ Listener/observer pattern via `add_listener()` — existing
- ✓ `unless=` negation shorthand on `add_transition()` — existing
- ✓ CI pipeline: lint, tests (3.10–3.13 × Linux/macOS/Windows), docs, release — existing

### Active

- [ ] **VERSION-01**: `__version__` in `__init__.py` is automatically derived from `pyproject.toml` at import time so they cannot drift
- [ ] **EXCEPT-01**: Every `except Exception` catch in `core.py` is annotated with a comment explaining why the broad catch is intentional
- [ ] **EXCEPT-02**: Catches in construction/validation paths narrowed to specific exception types where broad catch is unwarranted
- [ ] **EXCEPT-03**: `safe_trigger()` exception semantics documented clearly in docstring
- [ ] **TYPES-01**: `py.typed` PEP 561 marker file present in `src/fast_fsm/`
- [ ] **TYPES-02**: Package recognized as typed by mypy/pyright after install, with pure-Python fallback remaining functional
- [ ] **IMPORTS-01**: `condition_templates.py` uses relative import `from .conditions import Condition`
- [ ] **STATE-01**: `State` no longer inherits from `abc.ABC` (no abstract methods exist; direct instantiation is the primary pattern)
- [ ] **STATE-02**: All existing `State` subclassing and instantiation behavior unchanged post-removal
- [ ] **TESTS-01**: Audit report identifies redundant, over-specified, and low-value tests
- [ ] **TESTS-02**: Redundant/low-value tests removed or consolidated; test count reduced without reducing meaningful coverage
- [ ] **TESTS-03**: Any coverage gaps identified and documented (not necessarily filled in this milestone)
- [ ] **CI-01**: `@pytest.mark.slow` performance benchmarks run in a dedicated CI job on push to `main`
- [ ] **CI-02**: Benchmark job uses a fixed performance threshold so regressions fail the build

### Out of Scope

| Feature | Reason |
|---------|--------|
| `core.py` refactoring into mixins/modules | Hard constraint — single-file is required for mypyc compilation unit |
| New public API additions | Maintenance milestone only |
| Filling test coverage gaps | Audit only in this milestone; filling is future work |
| Benchmark comparison vs competitors in CI | Too slow for CI; manual only |

## Context

- **Brownfield library:** v0.2.0 shipped in March 2026 with substantial API additions
- **mypyc compilation boundary:** Only `core.py` compiles; `conditions.py` stays interpreted for user subclassing
- **Pure-Python fallback:** `FAST_FSM_PURE_PYTHON=1` must continue to work; `py.typed` solution cannot break this
- **Single runtime dependency:** `mypy-extensions` only — keep it that way
- **Version discrepancy at audit time:** `pyproject.toml` = 0.2.0, `__init__.py` = 0.1.0 (this milestone fixes it)

## Constraints

- **Performance:** `trigger()` throughput ≥200,000 ops/sec — must verify after any change to `core.py`
- **Backward compatibility:** No public API changes — all condition and callback signatures preserved
- **Compilation:** `core.py` changes must pass `uv run mypy src/fast_fsm/core.py` (mypyc compat)
- **Python version:** ≥3.10

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Keep `core.py` as single file | mypyc compilation unit must be single module | — Pending |
| Remove `ABC` from `State` | No abstract methods exist; `ABC` provides no enforcement and misleads users | — Pending |
| Automate version via `importlib.metadata` | Single source of truth in `pyproject.toml`; zero drift possible | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-04 after v0.2.1 milestone initialization*
