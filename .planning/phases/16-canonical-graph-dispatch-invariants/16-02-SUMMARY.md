---
phase: 16-canonical-graph-dispatch-invariants
plan: 02
subsystem: core-runtime
tags: [fsm, guards, async, mypyc, condition-wrappers, isolation]
requires:
  - phase: 16-01
    provides: canonical topology seams and asserted pure/compiled temporary-tree verification
provides:
  - one guard-lookup and filter-then-cap context contract for sync and async can/do paths
  - positional context forwarding through interpreted condition wrappers and compiled callable guards
  - cycle-safe recursive evaluation of the supported built-in wrapper graph
affects: [16-03, 16-04, 16-05, 17-atomic-transition-lifecycle, 20-installed-artifact-parity]
actuals:
  tokens: 12657
  tasks: 3
  commits: 7
tech-stack:
  added: []
  patterns: [fresh prepared guard context, exact private wrapper classifier, active-cycle rejection, asserted pure/compiled verification]
key-files:
  created: []
  modified:
    - src/fast_fsm/core.py
    - src/fast_fsm/conditions.py
    - src/fast_fsm/condition_templates.py
    - tests/test_safety_kwargs.py
    - tests/test_async.py
    - tests/test_condition_templates.py
    - .specify/memory/spr-core-api.md
key-decisions:
  - "Guard preparation is fresh per public call, filters invalid keys before applying the 50-key cap, and never sanitizes missing or unconditional transitions."
  - "Only exact built-in wrapper edges are traversed; active cycles raise ValueError while repeated acyclic DAG references remain legal."
  - "Async leaves are awaited only by the asynchronous evaluator; synchronous machines reject nested async requirements before mutation."
patterns-established:
  - "Guard dispatch: _prepare_transition performs one canonical lookup and creates a sanitized mapping only when a guard exists."
  - "Wrapper traversal: classify exact private edges, track active identities for cycles, and keep boolean short-circuit order explicit."
requirements-completed: [GRAF-05, GRAF-06, GRAF-08]
coverage:
  - id: D1
    description: "Sync and async can/do paths share positional and filter-then-cap guard context semantics."
    requirement: GRAF-06
    verification:
      - kind: integration
        ref: "tools/phase16_isolated_verify.py --mode task --build-mode pure ... pytest tests/test_safety_kwargs.py tests/test_condition_templates.py tests/test_async.py -x -q"
        status: pass
    human_judgment: false
  - id: D2
    description: "Nested supported wrappers await async leaves, preserve short-circuiting, reject cycles, and accept shared DAGs."
    requirement: GRAF-05
    verification:
      - kind: integration
        ref: "tests/test_async.py#TestAsyncWrapperEvaluation"
        status: pass
    human_judgment: false
  - id: D3
    description: "Condition signature changes retain the single core.py mypyc boundary in asserted native execution."
    requirement: GRAF-08
    verification:
      - kind: integration
        ref: "tools/phase16_isolated_verify.py --mode task --build-mode compiled ... pytest tests/test_mypyc_guard.py tests/test_safety_kwargs.py tests/test_condition_templates.py tests/test_async.py -x -q"
        status: pass
    human_judgment: false
duration: 19m
completed: 2026-08-30
status: complete
---

# Phase 16 Plan 02: Guard Context and Wrapper Evaluation Summary

**Canonical, filter-first guard context now behaves equivalently across sync and async dispatch, while built-in wrapper graphs await nested async leaves and reject cycles safely.**

## Performance

- **Duration:** 19m
- **Started:** 2026-08-30T00:41:35-04:00
- **Completed:** 2026-08-30T01:00:11-04:00
- **Tasks:** 3/3
- **Files modified:** 7

## Accomplishments

- Added one private preparation seam for sync/async can/do calls, with deterministic filter-then-cap keyword sanitization, positional identity preservation, and no context allocation for missing or unconditional transitions.
- Extended interpreted conditions and templates to accept and forward `*args, **kwargs`, retaining ordinary wrapper short-circuit and inversion behavior.
- Added exact built-in wrapper traversal with paired sync/async evaluators: nested async leaves await in async dispatch, synchronous construction rejects hidden async requirements, cycles fail closed, and shared DAGs remain valid.

## Task Commits

1. **Task 1: Converge transition lookup and sanitized guard context across four paths**
   - `5daa020` — RED four-path guard-context coverage
   - `e7e9854` — shared preparation and filter-then-cap implementation
2. **Task 2: Propagate positional context through interpreted condition signatures**
   - `88a6a73` — RED positional wrapper and short-circuit coverage
   - `83fed27` — interpreted condition forwarding implementation
3. **Task 3: Recursively await built-in wrappers with explicit cycle rejection**
   - `eca765e` — RED nested async wrapper/cycle/compiled condition coverage
   - `21bded6` — recursive evaluators, cycle detection, and compiled callable forwarding
   - `f5279fc` — compatibility repair for the established key-only diagnostic

## Files Created/Modified

- `src/fast_fsm/core.py` — shared guard preparation, deterministic sanitization, exact wrapper classification, recursive evaluators, and compiled callable forwarding.
- `src/fast_fsm/conditions.py` and `src/fast_fsm/condition_templates.py` — compatible positional context signatures with direct wrapper propagation.
- `tests/test_safety_kwargs.py`, `tests/test_async.py`, and `tests/test_condition_templates.py` — four-path parity, wrapper forwarding, cycles, DAG reuse, and short-circuit coverage.
- `.specify/memory/spr-core-api.md` — records guard preparation, condition signatures, and wrapper recursion contracts with their implementation commits.

## Decisions Made

- Guard inputs are sanitized once per evaluation, not cached between `can_*` and `trigger*` calls; user guards may have side effects, so calls remain independently evaluated.
- The private traversal intentionally recognizes only exact existing wrapper types rather than introducing a public traversal protocol.
- Key names may remain diagnostic metadata, but raw positional and keyword payload values are not logged by this change.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Cycle detection] Scan every wrapper child before declaring an async requirement.**

- **Found during:** Task 3
- **Issue:** An `any()` traversal could stop after an earlier async leaf and leave a later active wrapper cycle undetected.
- **Fix:** Visit every supported child while accumulating the async result; added a regression that places each named cycle after an async sibling.
- **Files modified:** `src/fast_fsm/core.py`, `tests/test_async.py`
- **Verification:** final asserted pure and compiled matrices passed.
- **Commit:** `21bded6`

**2. [Rule 1 - Compatibility] Preserve the established private-key diagnostic message.**

- **Found during:** Plan-wide pure regression
- **Issue:** Removing private key names from a debug message broke the existing logging contract, even though payload values remained protected.
- **Fix:** Restore key-only debug metadata without logging any payload value.
- **Files modified:** `src/fast_fsm/core.py`
- **Verification:** 205 pure tests and 213 compiled tests passed in asserted temporary-tree contexts.
- **Commit:** `f5279fc`

**Total deviations:** 2 Rule 1 auto-fixes.

## Issues Encountered

- Clean compiled-mode checks require temporary native builds and took longer than pure checks; both completed with asserted native origins and passed.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Plan 16-03 can consume `_contains_async_requirement()` for builder preflight and the common guard evaluator rules. Plans 16-04 and 17 can use the unified transition preparation seam without redefining guard-context behavior.

## Self-Check: PASSED

- All seven production, test, and SPR artifacts exist.
- All seven task commits are present in repository history.
- No plan-blocking stubs, skipped tests, or unrun verification remain.

---
*Phase: 16-canonical-graph-dispatch-invariants*
*Plan: 02*
*Completed: 2026-08-30*
