---
phase: 22-ordered-runtime-selection-lifecycle-integration
plan: 03
subsystem: runtime-selection
tags: [priority, lifecycle, tracing, mypyc, performance]
requires:
  - phase: 22-02
    provides: sequential synchronous and asynchronous priority selection
provides:
  - selected candidate priority on runtime result, history, and trace records
  - structural and counted-work proof for direct singleton and local group dispatch
affects: [23-construction-declarative-serialization-parity, 25-artifact-performance-drone-guidance]
actuals:
  tokens: 12679
  tasks: 2
  commits: 2
tech-stack:
  added: []
  patterns:
    - priority remains on the selected TransitionEntry instead of caller kwargs
    - AST plus operation-count tests enforce selector complexity boundaries
key-files:
  created: []
  modified:
    - src/fast_fsm/core.py
    - tests/test_transition_lifecycle.py
    - tests/test_logging_config.py
    - tests/test_mypyc_guard.py
    - tests/test_performance_benchmarks.py
    - .specify/memory/spr-core-api.md
key-decisions:
  - "Keep candidate priority as nullable additive metadata on result, history, and trace records."
  - "Use explicit TransitionEntry casts at singleton selection boundaries to keep the mypyc union closed."
patterns-established:
  - "Trace emits one attempt-level trace_priority scalar; candidate scans never create per-candidate trace events."
  - "Selector AST guards reject sorting, sequence copying, unrelated topology scanning, and async fan-out."
requirements-completed: [SEL-01, SEL-02, SEL-03, SEL-04]
coverage:
  - id: D1
    description: "Selected or evaluated candidate priority is retained across runtime result, committed history, lifecycle failures, cancellation bookkeeping, and one metadata-only trace event."
    requirement: SEL-03
    verification:
      - kind: integration
        ref: "tests/test_transition_lifecycle.py#priority metadata and cancellation tests; tests/test_logging_config.py#test_trace_priority_is_one_scalar_for_default_and_redacted_attempts"
        status: pass
    human_judgment: false
  - id: D2
    description: "Singleton dispatch remains a direct O(1) lookup while candidate groups do local O(k) short-circuited work."
    requirement: SEL-01
    verification:
      - kind: unit
        ref: "tests/test_mypyc_guard.py#test_priority_selectors_keep_their_closed_slotted_boundary; tests/test_performance_benchmarks.py#test_priority_group_work_stops_at_winner_and_ignores_unrelated_topology"
        status: pass
    human_judgment: false
  - id: D3
    description: "Pure and freshly compiled core preserve selected priority, winner order, history, query semantics, and existing async cancellation behavior."
    requirement: SEL-02
    verification:
      - kind: integration
        ref: "FAST_FSM_BUILD_MODE=compiled pytest tests/test_mypyc_guard.py tests/test_priority_selection.py tests/test_transition_lifecycle.py tests/test_async.py tests/test_performance_benchmarks.py -k priority-or-selection"
        status: pass
    human_judgment: false
duration: 15 min
completed: 2026-09-07
status: complete
---

# Phase 22 Plan 03: Runtime Priority Metadata and Complexity Proof Summary

**Priority-aware selection now carries one candidate scalar through results, history, and metadata-only tracing, with source/native proof that singleton dispatch stays direct and grouped work stays local.**

## Performance

- **Duration:** 15 min
- **Started:** 2026-09-07T01:00:00Z
- **Completed:** 2026-09-07T01:13:42Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- Appended nullable `priority` to `TransitionResult`, `TransitionRecord`, and `FSMTraceEvent` without changing legacy result equality or callback signatures.
- Routed selected/evaluated priority through normal and asynchronous lifecycle failures, history commits, cancellation bookkeeping, and exactly one attempt-level trace record.
- Locked selector structure and group-local complexity with AST, pure/native semantic, slots, type, and counted-operation tests.

## Task Commits

1. **Task 1: Carry one candidate priority through result, history, trace, and failure truth** — `00f9e22` (feat)
2. **Task 2: Prove compiled structure, pure/native semantics, and singleton/group complexity** — `c1cecfc` (test)

## Files Created/Modified

- `.specify/memory/spr-core-api.md` — documents ordered selection, priority metadata, trace confidentiality, and O(1)/O(k) boundaries.
- `src/fast_fsm/core.py` — propagates priority without adding another selection result or public topology API.
- `tests/test_transition_lifecycle.py` and `tests/test_logging_config.py` — cover result/history/lifecycle and trace-redactor behavior.
- `tests/test_mypyc_guard.py` and `tests/test_performance_benchmarks.py` — enforce native-safe structure and local candidate work.

## Decisions Made

- Priority is metadata derived only from the selected `TransitionEntry`; it is never forwarded as application callback data.
- Async cancellation stores only the currently evaluated priority in a task-local scalar, so it can build a truthful internal failure without per-machine mutable selection state.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Test compatibility] Replaced an interpreted async-machine test subclass**
- **Found during:** Task 2 native proof
- **Issue:** mypyc correctly rejects interpreted subclasses of compiled `AsyncStateMachine`.
- **Fix:** Used a native-safe observer assertion and locked the internal cancellation-priority handoff with an AST assertion.
- **Files modified:** `tests/test_transition_lifecycle.py`, `tests/test_mypyc_guard.py`
- **Verification:** Scoped compiled selection suite passed.
- **Committed in:** `c1cecfc`

**Total deviations:** 1 auto-fixed Rule 1 test-compatibility correction. No runtime contract or plan boundary changed.

## Issues Encountered

- The task-scoped offline UV cache lacked locked build dependencies for one isolated sdist test. The same offline test passed against the existing host cache; no dependency or source change was made.
- Beads' local Dolt server was unavailable during both commits. Git commits succeeded; no beads or remote mutation was attempted.

## Verification

- Focused pure lifecycle/logging and structural/complexity tests: passed.
- Full pure suite was run; the isolated sdist test was independently re-run and passed with the existing offline cache.
- Ruff, mypy, ty, and the slots-policy audit: passed.
- `FAST_FSM_BUILD_MODE=compiled task build-check`: passed.
- Scoped compiled selection/lifecycle/performance suite: passed, with pre-existing asyncio deprecation warnings only.

## Next Phase Readiness

Phase 22's ordered runtime selection contract is complete and ready for Phase 23 to preserve candidate identity through public construction, declarative, query, and serialization paths. No Phase 22 blocker remains.

## Self-Check: PASSED

- Summary exists, and task commits `00f9e22` and `c1cecfc` are present in local history.

---
*Phase: 22-ordered-runtime-selection-lifecycle-integration*
*Completed: 2026-09-07*
