# Fast FSM

## What This Is

High-performance, memory-efficient finite state machine library for Python. Outperforms popular alternatives (python-statemachine, transitions) by 5–20× in speed and ~1000× in memory usage through `__slots__` optimization, direct dictionary lookups, and minimal abstraction layers. Targets Python ≥3.10.

## Core Value

Blazing-fast, zero-overhead FSM transitions — `trigger()` must stay ≥200,000 ops/sec and all core operations must remain O(1).

## Completed: v0.2.3 Timing Condition Helpers (shipped 2026-04-05)

15/15 requirements satisfied. `TimeoutCondition`, `CooldownCondition`, `ElapsedCondition`. 722 tests.

## Completed: v0.2.2 Introspection & Agent Tooling (shipped 2026-04-05)

21/21 requirements satisfied. `to_dict()`, transition history, `to_plantuml()`, `to_json()`. 694 tests, 1.2M ops/sec.

## Completed: v0.2.1 Code Health & Quality (shipped 2026-04-04)

14/14 requirements satisfied. See `.planning/milestones/v0.2.1-ROADMAP.md` for full details.

## Completed: v0.3.0 Reliability & Runtime Hardening (2026-09-06)

**Goal:** Make Fast FSM release-auditable, internally consistent, and safe by default before expanding its API.

**Target features:**
- Restore release integrity across package metadata, changelog, documentation, quality gates, and compiled artifacts
- Enforce runtime graph, builder, guard, history, declarative-dispatch, and sync/async invariants
- Make callback failure, reentrancy, and concurrent-access behavior safe by default
- Correct and bound validation, comparison, cycle analysis, visualization, and diagnostic behavior
- Preserve the performance contract and verify compiled/pure-Python parity

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
- ✓ **SERIAL-01**: `StateMachine.to_dict()` topology serialization roundtrip — v0.2.2
- ✓ **HIST-01/02/03**: Opt-in transition history with `TransitionRecord`, bounded buffer, zero-cost when disabled — v0.2.2
- ✓ **VIS-01/02/03/04**: `to_plantuml()`, `to_json()` with topology + analysis + quality signals — v0.2.2
- ✓ **PERF-02**: History-enabled throughput measured and documented (≤ 2× degradation verified) — v0.2.2
- ✓ **TIME-01/02/03**: `TimeoutCondition`, `CooldownCondition`, `ElapsedCondition` — v0.2.3
- ✓ **TIME-04/05/06/07**: `time.monotonic()`, `reset()`, `**kwargs`, `__slots__` on all timing conditions — v0.2.3
- ✓ **INT-01/02**: Timing conditions in `condition_templates.py`, exported from `fast_fsm` — v0.2.3
- ✓ **INT-03/04**: Timing conditions work as guards on StateMachine, AsyncStateMachine, and FSMBuilder — v0.2.3
- ✓ **PERF-01**: `trigger()` with timing guard ≥ 200k ops/sec — v0.2.3
- ✓ **DOC-01/02**: README + Sphinx docs updated with timing condition examples — v0.2.3
- ✓ Runtime graph construction, transition dispatch, guards, history, declarative states, and builders preserve explicit invariants — Phase 16
- ✓ Callback failures, reentrant transitions, and concurrent access use safe default behavior — Phases 17–18
- ✓ Validation, comparison, visualization, and diagnostic APIs produce correct bounded results — Phase 19
- ✓ Logging and trace output avoid leaking payloads or disrupting application-owned handlers — Phase 19
- ✓ Release metadata, changelog, documentation, and quality gates agree on one auditable v0.3.0 baseline — Phases 15 and 20
- ✓ Installed compiled and pure-Python artifacts pass the same hardened-behavior oracle while preserving the throughput contract — Phase 20

## Current Milestone: v0.4.0 Priority-Aware Guarded Transitions

**Goal:** Add deterministic, priority-aware guarded transition resolution so one
`(state, trigger)` selects among finite ordered candidates without external
dispatch.

**Target features:**
- Evolve `add_transition(..., priority=...)` to register competing guarded
  candidates for one source state and trigger.
- Resolve candidates deterministically across synchronous and asynchronous
  machines, builders, and declarative states.
- Keep topology exports, validation, visualizations, diagnostics, benchmarks,
  and examples truthful about priority-aware transition groups.

### Active

- [ ] Deterministic, priority-aware guarded transition resolution for one
  `(state, trigger)` candidate group

### Out of Scope

| Feature | Reason |
|---------|--------|
| `core.py` refactoring into mixins/modules | Hard constraint — single-file is required for mypyc compilation unit |
| Benchmark comparison vs competitors in CI | Too slow for CI; manual only |
| Auto-fire/scheduler timers | Conditions are passive guards; scheduling belongs one layer up (user's event loop) |
| `snapshot()` v2 including topology | `to_dict()` + `snapshot()` solve this composably without a format change |
| Transition API evolution | Duplicate `(state, trigger)` registrations become explicit priority-aware candidates; pre-production scope permits this semantic change |

## Context

- **Current published version:** v0.2.3 (shipped 2026-04-05)
- **Internal milestone state:** v0.3.0 is verified and archived, but remains untagged and unreleased by design
- **mypyc compilation boundary:** Only `core.py` compiles; `conditions.py` and `condition_templates.py` stay interpreted for user subclassing
- **Pure-Python fallback:** `FAST_FSM_PURE_PYTHON=1` must continue to work
- **Single runtime dependency:** `mypy-extensions` only — keep it that way
- **Test count:** 1,503 (after Phase 19)
- **Clock source:** `time.monotonic()` for all timing — immune to NTP jumps across macOS/Linux/Windows
- **v0.3.0 scope source:** `.planning/codebase/CONCERNS.md` audit dated 2026-08-29
- **Compatibility posture:** Existing public symbols remain available, but safe default behavior takes precedence over preserving unsafe pre-production semantics

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
| History recording is zero-cost when disabled | Single `None` check in `trigger()` hot path; bounded `deque` when enabled | ✓ Verified ≤ 2× overhead in benchmark |
| Timing conditions in condition_templates.py (not core.py) | condition_templates.py stays interpreted for user subclassing; no mypyc rebuild needed | ✓ Purely additive — no core.py changes |
| Adopt safe defaults for callback failure, reentrancy, and concurrent access in v0.3.0 | The library is not yet used in production; correcting unsafe semantics now is cheaper than preserving them indefinitely | ✓ Implemented and verified in Phases 17–19 |
| Use immutable graph snapshots plus explicit deterministic budgets for diagnostics | Diagnostics must remain truthful under concurrent mutation and bounded on adversarial graphs | ✓ Implemented in Phase 19; incomplete work is explicit |
| Keep default trace metadata-only and fail closed on redactor errors | Diagnostic convenience must not expose application payloads | ✓ Implemented and accepted in Phase 19 |
| Treat logging handlers as application-owned unless the library created them | Configuration must be reversible and non-invasive | ✓ Implemented and accepted in Phase 19 |
| Require exact-SHA hosted evidence and independently recomputed downloads before a v0.3.0 tag | Release authorization needs both host execution and local evidence verification; the tag workflow retains a separate identity gate | ✓ Verified in Phase 20; no tag or release created |
| Evolve `add_transition()` rather than add a second candidate-registration API | Priority is an attribute of an ordinary transition; one coherent API avoids redundant abstractions | — Pending v0.4.0 |

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
*Last updated: 2026-09-06 after starting v0.4.0 Priority-Aware Guarded Transitions*
