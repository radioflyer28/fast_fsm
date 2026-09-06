---
phase: 16-canonical-graph-dispatch-invariants
plan: 04
subsystem: core-runtime
tags: [declarative-dispatch, transition-history, deque, mypyc, slots]
requires:
  - phase: 16-canonical-graph-dispatch-invariants
    provides: "Canonical transition preparation, guard context, and builder lifecycle seams from Plans 16-01 through 16-03."
provides:
  - "A single canonical declarative-handler resolution and invocation boundary for ordinary sync and async dispatch."
  - "Validated positive-capacity bounded deque history with O(1) FIFO eviction and defensive list reads."
affects: [phase-17-lifecycle-semantics, phase-18-ownership, phase-19-diagnostics]
actuals:
  tokens: 8669.5
  tasks: 2
  commits: 5
tech-stack:
  added: []
  patterns:
    - "Private resolver/invoker seam separates metadata matching from exactly-once user-code invocation."
    - "Optional deque(maxlen=...) retains the disabled-history None fast path and bounds enabled history."
key-files:
  created: []
  modified:
    - src/fast_fsm/core.py
    - tests/test_builder.py
    - tests/test_async.py
    - tests/test_advanced_functionality.py
    - tests/test_performance_benchmarks.py
    - .specify/memory/spr-core-api.md
key-decisions:
  - "Declarative handlers are resolved by canonical source, trigger, and target metadata and invoked only through a shared ordinary-dispatch seam."
  - "History accepts only positive non-bool integer capacities; re-enabling replaces storage with an empty bounded deque."
patterns-established:
  - "Handler failure tests assert invocation cardinality only, leaving Phase 17 lifecycle outcomes and ordering unspecified."
  - "Public history is always a copied chronological list; internal bounded storage is never exposed."
requirements-completed: [GRAF-07, GRAF-08, LIFE-07]
coverage:
  - id: D1
    description: "Ordinary sync and async declarative dispatch resolves the matching handler once, while compatibility helpers delegate to the same seam."
    requirement: GRAF-07
    verification:
      - kind: unit
        ref: "tests/test_builder.py and tests/test_async.py declarative dispatch cases via isolated pure and compiled pytest"
        status: pass
    human_judgment: false
  - id: D2
    description: "Declarative metadata mismatch, absent handlers, and handler failure forms do not create duplicate side effects or encode Phase 17 outcomes."
    requirement: GRAF-08
    verification:
      - kind: unit
        ref: "tests/test_builder.py and tests/test_async.py invocation-count-only declarative cases via isolated pure and compiled pytest"
        status: pass
    human_judgment: false
  - id: D3
    description: "Transition history validates capacity atomically, uses bounded FIFO deque eviction, and returns defensive chronological copies."
    requirement: LIFE-07
    verification:
      - kind: unit
        ref: "tests/test_advanced_functionality.py, tests/test_async.py, and tests/test_performance_benchmarks.py via isolated pure and compiled pytest"
        status: pass
      - kind: other
        ref: "isolated compiled tools/release_evidence.py slots-policy --json"
        status: pass
    human_judgment: false
duration: 54m
completed: 2026-08-30
status: complete
---

# Phase 16 Plan 04: Declarative Dispatch and Bounded History Summary

**Ordinary declarative sync/async dispatch now resolves one canonical handler and invokes it exactly once, while bounded deque history validates capacity atomically and retains the disabled fast path.**

## Performance

- **Duration:** 54 min
- **Started:** 2026-08-30T05:26:17Z
- **Completed:** 2026-08-30T06:20:00Z
- **Tasks:** 2/2
- **Files modified:** 6

## Accomplishments

- Added shared sync/async declarative handler resolution and invocation helpers, so ordinary dispatch and compatibility helpers cannot independently invoke selected metadata handlers.
- Added exact-once sync/async coverage for matching, nonmatching, Unicode, successful normalization, and invocation-only failure cases without constraining Phase 17 lifecycle semantics.
- Replaced front-trimmed list history with validated optional `deque(maxlen=...)`, preserving atomic failed reconfiguration, chronological copies, clone compatibility, and disabled-history allocation behavior.
- Confirmed source linting, blocking mypy compatibility, isolated pure contracts, isolated compiled native-origin/slot policy, and compiled throughput/history checks.

## Task Commits

1. **Task 1: Invoke matched declarative handlers exactly once in ordinary dispatch**
   - `ab23274` — `test(16-04): add failing ordinary dispatch coverage`
   - `a51af76` — `feat(16-04): unify declarative dispatch invocation`
2. **Task 2: Validate capacity and replace linear history trimming with bounded O(1) eviction**
   - `10e4073` — `test(16-04): add failing bounded history coverage`
   - `c32f7f7` — `feat(16-04): bound transition history with deque`
   - `0bd7668` — `fix(16-04): retain boolean history rejection compiled`

## Files Created/Modified

- `src/fast_fsm/core.py` — canonical declarative invocation boundary and optional bounded deque history.
- `tests/test_builder.py` — sync declarative matching, normalization, compatibility, and invocation-count contracts.
- `tests/test_async.py` — async declarative exactly-once and async history contracts.
- `tests/test_advanced_functionality.py` — capacity validation, reset, FIFO, copy-on-read, disabled, and clone history coverage.
- `tests/test_performance_benchmarks.py` — enabled bounded-history steady-state and compiled trigger-floor coverage.
- `.specify/memory/spr-core-api.md` — records dispatch and history contracts with their owning commits.

## Verification

- `uv run ruff check src/fast_fsm/core.py tests/test_builder.py tests/test_async.py tests/test_advanced_functionality.py tests/test_performance_benchmarks.py` — passed.
- Isolated pure pytest for declarative/history behavior — 83 passed.
- `task typecheck-mypy` — passed: no issues in 6 source files.
- Isolated compiled `uv run python tools/release_evidence.py slots-policy --json` — passed with compiled native origin and slot policy clean.
- Isolated compiled pytest for declarative/history/mypyc/trigger throughput behavior — 92 passed.

## Decisions Made

- Canonical source/trigger/target metadata decides whether a declarative handler is selected; the handler itself is reached through a single private sync or async invocation seam.
- Invalid capacities—including `bool`—raise before existing history configuration changes; a valid re-enable starts an empty new buffer.
- Tests deliberately avoid result, order, callback, cancellation, commit-boundary, and history-on-failure assertions that Phase 17 owns.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Compilation parity] Retained boolean-capacity rejection in the compiled implementation**
- **Found during:** Task 2 (bounded history)
- **Issue:** `bool` is an `int` subclass, so the compiled path needed an explicit non-bool guard to preserve the planned capacity contract.
- **Fix:** Rejected boolean capacities before history storage can change.
- **Files modified:** `src/fast_fsm/core.py`, `tests/test_advanced_functionality.py`
- **Verification:** Isolated pure and compiled history tests passed.
- **Committed in:** `0bd7668`

**Total deviations:** 1 auto-fixed (Rule 1 compilation parity)

**Impact on plan:** The correction enforces the stated D-17 contract without expanding scope.

## Issues Encountered

- Sandboxed `uv` could not access its existing cache. Re-running the same non-mutating validation commands with approved cache access succeeded; no source or environment configuration was changed.

## Known Stubs

None.

## Next Phase Readiness

- Declarative success-side-effect and bounded-history invariants are ready for Phase 17 to define lifecycle ordering and failure behavior without changing the Phase 16 cardinality contract.
- No blocker was found.

## Self-Check: PASSED

- `16-04-SUMMARY.md` exists at the required phase path.
- All five Task 1/Task 2 commits are present in repository history.

---
*Phase: 16-canonical-graph-dispatch-invariants*
*Plan: 04*
*Completed: 2026-08-30*
