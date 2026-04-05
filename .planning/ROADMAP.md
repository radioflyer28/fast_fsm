# Roadmap: Fast FSM

## Milestones

- ✅ **v0.2.1 Code Health & Quality** — Phases 1–6 (shipped 2026-04-04)
- 🔧 **v0.2.2 Introspection & Agent Tooling** — Phases 7–11.1 (20/21 reqs — gap closure pending)
- 🔄 **v0.2.3 Timing Condition Helpers** — Phases 12–14 (in progress)

## Phases

<details>
<summary>✅ v0.2.1 Code Health & Quality (Phases 1–6) — SHIPPED 2026-04-04</summary>

- [x] Phase 1: Quick Wins — version sync + import fix
- [x] Phase 2: State ABC Cleanup — remove misleading `ABC` base
- [x] Phase 3: Exception Handling Audit — annotate all 16 broad catches
- [x] Phase 4: py.typed Marker — PEP 561 typed package declaration
- [x] Phase 5: Test Suite Triage — audit and prune 4 low-value tests
- [x] Phase 6: Benchmark CI — 200k ops/sec throughput gate + CI job

**14/14 requirements satisfied.** Full details: `.planning/milestones/v0.2.1-ROADMAP.md`

</details>

<details>
<summary>✅ v0.2.2 Introspection & Agent Tooling (Phases 7–11.1) — SHIPPED 2026-04-05</summary>

- [x] Phase 7: Serialization (`to_dict()`) — topology roundtrip via `StateMachine.to_dict()`
- [x] Phase 8: Transition History — opt-in `enable_history()` / `disable_history()` with `TransitionRecord`
- [x] Phase 9: PlantUML Output — `to_plantuml()` in `visualization.py`
- [x] Phase 10: Machine-Readable JSON Export — `to_json()` with topology + analysis + quality signals
- [x] Phase 11: Performance Verification & Docs — benchmark gate, README updates, milestone wrap-up
- [ ] Phase 11.1: History-Enabled Performance Benchmark — gap closure for PERF-02

**20/21 requirements satisfied.** 694 tests, 1.2M ops/sec. Gap closure phase 11.1 pending.

</details>

### Phase 11.1: History-Enabled Performance Benchmark (Gap Closure)

**Goal:** Measure and document `trigger()` throughput with `enable_history()` active; verify ≤ 2× degradation vs. disabled baseline.

**Milestone:** v0.2.2 (gap closure — identified by milestone audit)

**Requirements:** PERF-02

**Depends on:** None (history implementation already shipped in Phase 8)

**Success Criteria** (what must be TRUE):
1. `test_performance_benchmarks.py` contains a test that enables history, measures `trigger()` throughput, and asserts it is no more than 2× slower than the disabled baseline
2. README performance section documents measured overhead of history-enabled mode
3. Full test suite passes (694+ baseline, 0 failures)

**Plans:** TBD

---

# Roadmap: Fast FSM v0.2.3

**Milestone:** v0.2.3 Timing Condition Helpers
**Goal:** Add reusable, platform-safe time-based condition classes so users can express timeout, cooldown, and elapsed-time guards without writing clock logic.
**Defined:** 2026-04-05
**Phase numbering:** continues from v0.2.2 (last phase was Phase 11)

---

## v0.2.3 Phases

- [ ] **Phase 12: Timing Condition Implementation** — `TimeoutCondition`, `CooldownCondition`, `ElapsedCondition` in `condition_templates.py` + exports
- [ ] **Phase 13: Testing & Integration Verification** — unit tests, integration tests (sync + async FSM guards), performance benchmark, regression gate
- [ ] **Phase 14: Documentation** — README timing condition examples, Sphinx API reference updates, milestone wrap-up

---

## Phase Details

---

### Phase 12: Timing Condition Implementation

**Goal:** Users can instantiate `TimeoutCondition`, `CooldownCondition`, and `ElapsedCondition` from `fast_fsm` and use them as transition guards.

**Depends on:** Nothing (purely additive to `condition_templates.py`; no `core.py` changes, no mypyc rebuild)

**Requirements:** TIME-01, TIME-02, TIME-03, TIME-04, TIME-05, TIME-06, TIME-07, INT-01, INT-02

**Success Criteria** (what must be TRUE):
1. `from fast_fsm import TimeoutCondition, CooldownCondition, ElapsedCondition` works without error
2. `TimeoutCondition(5.0).check()` returns `True` before 5 seconds elapsed and `False` after; `CooldownCondition(2.0).check()` passes on first call, blocks until 2 seconds after last successful check; `ElapsedCondition(3.0).check()` returns `False` before 3 seconds and `True` after
3. All three conditions have a `reset()` method that restarts their internal clock reference
4. All three accept `**kwargs` in `check()` (per `Condition` ABC contract) and use `time.monotonic()` exclusively
5. No `__dict__` on any instance — `__slots__` enforced

**Plans:** TBD

---

### Phase 13: Testing & Integration Verification

**Goal:** Timing conditions are verified as guards on both sync and async state machines, with performance within contract and no regressions.

**Depends on:** Phase 12

**Requirements:** INT-03, INT-04, PERF-01, COMPAT-01

**Success Criteria** (what must be TRUE):
1. A `StateMachine` with a `TimeoutCondition` guard correctly blocks transitions after the timeout expires
2. An `AsyncStateMachine` with a `CooldownCondition` guard correctly enforces cooldown via `trigger_async()`
3. `FSMBuilder().add_transition(condition=ElapsedCondition(1.0))` builds a working machine that respects the elapsed-time guard
4. `trigger()` throughput with a timing condition guard ≥ 200,000 ops/sec (single `time.monotonic()` call in hot path)
5. Full test suite passes (694+ baseline, 0 failures)

**Plans:** TBD

---

### Phase 14: Documentation

**Goal:** README and Sphinx docs show users how to use timing conditions with clear, runnable examples.

**Depends on:** Phase 13

**Requirements:** DOC-01, DOC-02

**Success Criteria** (what must be TRUE):
1. README contains working code examples for all three timing conditions (timeout, cooldown, elapsed) showing real FSM guard usage
2. Sphinx API reference documents `TimeoutCondition`, `CooldownCondition`, `ElapsedCondition` with constructor parameters, methods (`check`, `reset`), and docstrings
3. Sphinx build passes with `-W` (warnings as errors): `uv run sphinx-build -b html docs docs/_build/html -W --keep-going`
4. `CHANGELOG.md` updated with v0.2.3 entry and `pyproject.toml` version bumped to `0.2.3`

**Plans:** TBD

---

## Requirements Traceability

| Requirement | Phase | Notes |
|-------------|-------|-------|
| TIME-01     | 12    | `TimeoutCondition(seconds)` — blocks after elapsed time exceeds threshold |
| TIME-02     | 12    | `CooldownCondition(seconds)` — blocks until N seconds since last successful check |
| TIME-03     | 12    | `ElapsedCondition(seconds)` — passes when ≥ N seconds elapsed |
| TIME-04     | 12    | All use `time.monotonic()` — cross-platform monotonic clock |
| TIME-05     | 12    | All provide `reset()` to restart internal clock reference |
| TIME-06     | 12    | All accept `**kwargs` in `check()` (Condition ABC contract) |
| TIME-07     | 12    | All use `__slots__` — consistent with library memory model |
| INT-01      | 12    | Added to `condition_templates.py` alongside existing helpers |
| INT-02      | 12    | Exported from `fast_fsm.__init__` |
| INT-03      | 13    | Work as guards on `StateMachine` and `AsyncStateMachine` |
| INT-04      | 13    | `FSMBuilder` supports via standard `condition=` parameter |
| PERF-01     | 13    | `trigger()` throughput with timing guard ≥ 200,000 ops/sec |
| COMPAT-01   | 13    | All existing tests pass (694 baseline) |
| DOC-01      | 14    | README updated with timing condition examples |
| DOC-02      | 14    | Sphinx docs updated — API reference for timing conditions |

**Coverage:** 15/15 requirements mapped ✓

---

## Build Notes

No `core.py` changes in this milestone — timing conditions live in `condition_templates.py` (interpreted). No mypyc rebuild needed.

Targeted tests per phase:
- Phase 12: `uv run pytest tests/test_condition_templates.py tests/test_safety_kwargs.py -x -q`
- Phase 13: `uv run pytest tests/test_condition_templates.py tests/test_basic_functionality.py tests/test_async.py tests/test_builder.py tests/test_performance_benchmarks.py -x -q`
- Phase 14: `uv run pytest tests/ -x -q` (full suite)

---

## Progress Table

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 12. Timing Condition Implementation | 0/1 | Not started | - |
| 13. Testing & Integration Verification | 0/1 | Not started | - |
| 14. Documentation | 0/1 | Not started | - |

---
*v0.2.3 roadmap defined: 2026-04-05*
