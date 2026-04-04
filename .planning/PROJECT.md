# Fast FSM

## What This Is

High-performance, memory-efficient finite state machine library for Python. Outperforms popular alternatives (python-statemachine, transitions) by 5–20× in speed and ~1000× in memory usage through `__slots__` optimization, direct dictionary lookups, and minimal abstraction layers. Targets Python ≥3.10.

## Core Value

Blazing-fast, zero-overhead FSM transitions — `trigger()` must stay ≥200,000 ops/sec and all core operations must remain O(1).

## Completed: v0.2.1 Code Health & Quality (shipped 2026-04-04)

14/14 requirements satisfied. See `.planning/milestones/v0.2.1-ROADMAP.md` for full details.

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
- ✓ **VERSION-01**: `__version__` derived from `importlib.metadata` — v0.2.1
- ✓ **EXCEPT-01/02/03**: All 16 `except Exception` catches annotated; `safe_trigger()` semantics documented — v0.2.1
- ✓ **TYPES-01/02**: `py.typed` PEP 561 marker; package recognized as typed — v0.2.1
- ✓ **IMPORTS-01**: `condition_templates.py` uses relative import — v0.2.1
- ✓ **STATE-01/02**: `State` no longer inherits from `ABC`; all subclassing works identically — v0.2.1
- ✓ **TESTS-01/02/03**: Test suite audited; 4 low-value tests removed; coverage gaps documented — v0.2.1
- ✓ **CI-01/02**: `benchmark` CI job with 200k ops/sec throughput gate — v0.2.1

### Active

*(No active milestone — plan next milestone with `/gsd-new-milestone`)*

### Out of Scope

| Feature | Reason |
|---------|--------|
| `core.py` refactoring into mixins/modules | Hard constraint — single-file is required for mypyc compilation unit |
| New public API additions | Maintenance milestone only |
| Filling test coverage gaps | Audit only in this milestone; filling is future work |
| Benchmark comparison vs competitors in CI | Too slow for CI; manual only |

## Context

- **Current version:** v0.2.1 (shipped 2026-04-04)
- **mypyc compilation boundary:** Only `core.py` compiles; `conditions.py` stays interpreted for user subclassing
- **Pure-Python fallback:** `FAST_FSM_PURE_PYTHON=1` must continue to work; `py.typed` solution cannot break this
- **Single runtime dependency:** `mypy-extensions` only — keep it that way
- **Test count:** 634 (post-triage; 4 low-value tests removed from 637)

## Constraints

- **Performance:** `trigger()` throughput ≥200,000 ops/sec — must verify after any change to `core.py`
- **Backward compatibility:** No public API changes — all condition and callback signatures preserved
- **Compilation:** `core.py` changes must pass `uv run mypy src/fast_fsm/core.py` (mypyc compat)
- **Python version:** ≥3.10

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Keep `core.py` as single file | mypyc compilation unit must be single module | ✓ Upheld — no refactoring |
| Remove `ABC` from `State` | No abstract methods exist; `ABC` provides no enforcement and misleads users | ✓ Removed in v0.2.1 — 637 tests pass unchanged |
| Automate version via `importlib.metadata` | Single source of truth in `pyproject.toml`; zero drift possible | ✓ Shipped in v0.2.1 |
| Detect compiled mode by module file suffix | `FAST_FSM_PURE_PYTHON` env var only suppresses build-time compilation; can't reliably detect runtime mode | ✓ `find_spec().origin.endswith(".so")` is accurate |

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
*Last updated: 2026-04-04 after v0.2.1 milestone completion*
