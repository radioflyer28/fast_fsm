---
phase: 17-atomic-transition-lifecycle
plan: 02
subsystem: runtime
tags: [lifecycle, transition-result, observers, mypyc, redaction]
requires:
  - phase: 17-01
    provides: additive TransitionResult fields, destination-enter tracer, and clean-export verification harness
provides:
  - staged pre-commit failures for resolution, guard, and state permission
  - one ordered, non-recursive failure observer boundary for sync and async triggers
  - explicit opt-in TransitionError cause chaining across pure and compiled artifacts
affects: [17-03, 17-04, core-runtime, lifecycle-conformance]
actuals:
  tokens: 9967
  tasks: 2
  commits: 4
tech-stack:
  added: []
  patterns:
    - lower helpers construct a staged failure while public trigger boundaries finalize it
    - cause identity remains private result data and is chained only at raise_if_failed
key-files:
  created: []
  modified:
    - src/fast_fsm/core.py
    - tests/test_transition_lifecycle.py
    - tests/test_boundary_negative.py
    - tests/test_mypyc_guard.py
    - tests/test_safety_kwargs.py
    - .specify/memory/spr-core-api.md
key-decisions:
  - "Resolution, guard, and state-permission failures are all pre-commit results finalized once from the public sync or async trigger boundary."
  - "Failure observer isolation catches observer BaseException locally, while ordinary guard and permission causes remain directly available only as result.cause."
  - "raise_if_failed uses explicit exception chaining after assigning the cause so pure Python and mypyc retain identical cause identity."
patterns-established:
  - "Use _build_failure_result below public trigger boundaries and _finalize_failure exactly once at those boundaries."
  - "Use asserted fresh pure and compiled exports for core semantic evidence when checkout native shadows are present."
requirements-completed: [LIFE-02, LIFE-04]
coverage:
  - id: D1
    description: "Sync and async missing-transition, guard, and state-permission failures retain truthful pre-commit state, original cause identity, and one ordered observer pass."
    requirement: LIFE-02
    verification:
      - kind: integration
        ref: "tests/test_transition_lifecycle.py#test_precommit_failures_are_truthful_and_finalize_once"
        status: pass
      - kind: integration
        ref: "tests/test_transition_lifecycle.py#test_async_precommit_failures_match_the_result_finalizer_contract"
        status: pass
    human_judgment: false
  - id: D2
    description: "TransitionResult remains additive and slotted while its opt-in error boundary retains direct cause chaining without disclosing cause text."
    requirement: LIFE-04
    verification:
      - kind: unit
        ref: "tests/test_boundary_negative.py#TestTransitionResult.test_additive_lifecycle_fields_preserve_legacy_constructor_and_equality"
        status: pass
      - kind: unit
        ref: "tests/test_mypyc_guard.py#test_transition_result_keeps_its_additive_slots_and_chained_error_boundary"
        status: pass
      - kind: integration
        ref: "uv run python tools/phase16_isolated_verify.py --mode task --build-mode compiled"
        status: pass
    human_judgment: false
duration: 10 min
completed: 2026-09-01
status: complete
---

# Phase 17 Plan 02: Truthful Pre-Lifecycle Results Summary

**Resolution, guard, and state-permission failures now return one redacted, stage-aware pre-commit result and notify failure observers once in both sync and async triggers.**

## Performance

- **Duration:** 10 min
- **Started:** 2026-09-01T16:55:17Z
- **Completed:** 2026-09-01T17:05:17Z
- **Tasks:** 2/2
- **Files modified:** 6

## Accomplishments

- Routed all missing-transition, false/raising guard, and false/raising state-permission outcomes through a shared staged result builder and one public failure finalizer.
- Preserved observer registration order and original caller kwargs even when earlier observers raise `RuntimeError`, cancellation, interruption, or exit exceptions.
- Kept the value-returning API additive and slotted; `raise_if_failed()` now explicitly chains its concise error from the hidden original cause in pure and freshly compiled exports.

## Task Commits

1. **Task 1 RED: pre-lifecycle failure contract** — `94bd5b4` (test)
2. **Task 1 GREEN: finalize resolution, guard, and permission failures** — `4952970` (feat)
3. **Task 2 RED: result chaining contract** — `8cff6e7` (test)
4. **Task 2 GREEN: explicit cause chaining** — `a237be7` (feat)

## Files Created/Modified

- `src/fast_fsm/core.py` — shared pre-lifecycle result builder, exact-once finalization routes, redacted cause handling, and explicit error chaining.
- `tests/test_transition_lifecycle.py` — sync/async preparation matrix and BaseException observer isolation coverage.
- `tests/test_boundary_negative.py`, `tests/test_mypyc_guard.py`, and `tests/test_safety_kwargs.py` — additive API, slotted mypyc boundary, and cause-redaction regressions.
- `.specify/memory/spr-core-api.md` — synchronized staged result, observer, defaults, chaining, and redaction contract.

## Decisions Made

- Kept failure observation at public `trigger()` and `trigger_async()` boundaries; lower helpers construct but never notify, preventing duplicate notification.
- Continued through all failure observers after their local `BaseException` failures without exposing exception text or replacing the transition result.
- Used `raise error from cause` alongside explicit cause assignment to retain direct cause identity under mypyc.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Regression] Updated the direct guard-exception assertion for the new redaction contract**

- **Found during:** Task 1
- **Issue:** `tests/test_safety_kwargs.py` asserted that a guard exception message appeared in the public result and logs, conflicting with the required hidden-cause contract.
- **Fix:** Asserted the stable guard stage/error, direct cause identity, and absence of exception text instead.
- **Files modified:** `tests/test_safety_kwargs.py`
- **Verification:** Fresh pure-source lifecycle and safety matrix passed.
- **Committed in:** `4952970`

**2. [Rule 1 - Test guard] Corrected the AST predicate for explicit exception chaining**

- **Found during:** Task 2
- **Issue:** The new mypyc guard inspected the `raise ... from self.cause` AST shape one level too deeply.
- **Fix:** Corrected the predicate and re-ran the fresh compiled matrix.
- **Files modified:** `tests/test_mypyc_guard.py`
- **Verification:** Fresh compiled matrix passed all selected tests.
- **Committed in:** `a237be7`

---

**Total deviations:** 2 auto-fixed (Rule 1).
**Impact on plan:** Both fixes directly preserve the non-disclosure and compiled compatibility requirements without expanding the lifecycle scope.

## Issues Encountered

The checkout intentionally retains native shadows that do not represent the edited source. All semantic evidence therefore ran in asserted fresh pure or freshly compiled exports; no checkout artifact was deleted or treated as evidence.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Plan 17-03 can extend the same builder/finalizer boundary across the synchronous lifecycle slots and commit-owned history without duplicating pre-lifecycle logic.

## Self-Check: PASSED

- All six modified runtime, test, and SPR files plus `17-02-SUMMARY.md` exist on disk.
- All four TDD RED/GREEN commits are present in git history.
- Fresh pure and freshly compiled lifecycle/result matrices, Ruff, and blocking mypy passed.
