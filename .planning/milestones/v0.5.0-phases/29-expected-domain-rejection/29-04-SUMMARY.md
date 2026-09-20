---
phase: 29-expected-domain-rejection
plan: "04"
subsystem: runtime-conformance
tags: [expected-rejection, mypyc, native-parity, slots-policy, performance]
requires:
  - phase: 29-03
    provides: lifecycle-boundary, logging, and public API rejection evidence
provides:
  - exact structural and pure/native oracle for expected domain rejection
  - subclass-safe compiled rejection classification at the six selector seams
  - restored pure source after fresh native performance and regression closure
affects:
  - 30-builder-first-construction-and-persistence-parity
  - 31-semantic-diagnostics-and-visualization
  - 32-performance-artifact-and-progressive-guidance-proof
actuals:
  tokens: 9769
  tasks: 2
  commits: 2
tech-stack:
  added: []
  patterns:
    - cold-path dynamic signal classification for interpreted subclasses crossing mypyc
    - exact six selector-only conversion calls with no trigger or lifecycle conversion
key-files:
  created: []
  modified:
    - src/fast_fsm/core.py
    - tests/test_mypyc_guard.py
    - .github/copilot-instructions.md
    - .specify/memory/spr-core-api.md
key-decisions:
  - "Use a dynamic subclass-safe check only after an eligibility hook raises, preserving direct singleton success dispatch."
  - "Keep the expected-rejection signal in core.py but allow interpreted subclasses and avoid compiled exact-type narrowing."
requirements-completed: [REJECT-01, REJECT-02, REJECT-03, REJECT-04, REJECT-05, REJECT-06, REJECT-07, REJECT-08, REJECT-09]
coverage:
  - id: D1
    description: "Runtime, stub, package export, selector structure, slots registry, and internal policy state one bounded rejection contract."
    requirement: REJECT-01
    verification:
      - kind: unit
        ref: tests/test_mypyc_guard.py#test_expected_rejection_contract_is_a_read_only_result_tail_and_public_export
        status: pass
      - kind: unit
        ref: tests/test_release_evidence.py#test_slots_policy_authorities_name_the_same_four_exceptions
        status: pass
    human_judgment: false
  - id: D2
    description: "Pure and fresh compiled selectors keep false fallthrough separate from terminal rejection, queries, lifecycle failures, composition, cancellation, and one observer finalization."
    requirement: REJECT-03
    verification:
      - kind: integration
        ref: tests/test_mypyc_guard.py#test_expected_rejection_selector_contract_is_exact_and_mode_invariant
        status: pass
      - kind: other
        ref: FAST_FSM_BUILD_MODE=compiled uv run pytest tests/test_expected_rejection.py tests/test_priority_selection.py tests/test_condition_interface.py tests/test_transition_lifecycle.py tests/test_async.py tests/test_logging_config.py tests/test_mypyc_guard.py tests/test_release_evidence.py -x -q -k "rejection or query or async or cancellation or compos or lifecycle or logging or transition_result or slots_policy"
        status: pass
    human_judgment: false
  - id: D3
    description: "The untouched compiled singleton dispatch retains its existing throughput regression floor and the source package finishes in verified pure mode."
    requirement: REJECT-05
    verification:
      - kind: other
        ref: FAST_FSM_BUILD_MODE=compiled uv run pytest tests/test_performance_benchmarks.py::TestAdvancedPerformance::test_trigger_min_throughput -x -q
        status: pass
      - kind: other
        ref: FAST_FSM_BUILD_MODE=pure uv run pytest tests/ -x -q
        status: pass
    human_judgment: false
duration: 11min
completed: 2026-09-17
status: complete
---

# Phase 29 Plan 04: Native and Release Closure Summary

**Expected domain rejection now has an exact structural contract and a pure/native oracle, including interpreted rejection subclasses, without adding work to direct singleton success dispatch.**

## Performance

- **Duration:** 11 min
- **Started:** 2026-09-17T16:51:09Z
- **Completed:** 2026-09-17T17:01:38Z
- **Tasks:** 2/2
- **Files modified:** 4

## Accomplishments

- Added structural and semantic proof for the result tail, read-only properties, public export, six selector-only conversion sites, false fallthrough, query behavior, composition, lifecycle classification, cancellation, observer cardinality, and pure/native equivalence.
- Fixed a mypyc parity defect where an application-defined `TransitionRejected` subclass could be constructed but was rejected by compiled exact-type narrowing; classification now happens only in the six cold selector exception paths.
- Passed the mandatory formatter, blocking mypy, advisory ty, slots policy, warnings-as-errors docs build, fresh compiled oracle, singleton throughput regression, verified shadow relocation, restored pure-origin assertion, and full sequential pure suite.

## Task Commits

1. **Task 1: Lock structural, slots-policy, and dual-origin rejection contracts** — `8195f58` (test)
2. **Task 2: Execute the mandatory quality, native, restoration, and regression closure** — `ab1606a` (fix)

## Files Created/Modified

- `tests/test_mypyc_guard.py` — locks public/result structure, conversion-boundary topology, and the dual-origin behavioral oracle.
- `src/fast_fsm/core.py` — preserves expected-rejection subclasses under mypyc while retaining selector-only, exception-path conversion.
- `.github/copilot-instructions.md` and `.specify/memory/spr-core-api.md` — record the interpreted-subclass and native-parity maintenance contract.

## Decisions Made

- Retained `TransitionRejected` as the public core control signal; moving it out of the compilation unit was unnecessary once its methods and selector classification use subclass-safe dynamic boundaries.
- The dynamic signal check is evaluated only after a guard/declarative/permission hook has raised. Direct singleton lookup and successful dispatch retain their existing O(1) path.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Native parity] Repaired compiled handling of interpreted rejection subclasses**
- **Found during:** Task 2 fresh compiled semantic oracle.
- **Issue:** mypyc exact-type narrowing turned a valid `TransitionRejected` subclass into an ordinary `TypeError` during selector handling.
- **Fix:** Allowed interpreted subclasses on the public signal and used a cold-path dynamic recognition/revalidation helper at the existing three sync and three async eligibility boundaries.
- **Files modified:** `src/fast_fsm/core.py`, `tests/test_mypyc_guard.py`, `.github/copilot-instructions.md`, `.specify/memory/spr-core-api.md`.
- **Verification:** Fresh compiled hostile-subclass regression, complete compiled semantic matrix, singleton benchmark, restored pure-origin assertion, and pure full suite all passed.
- **Committed in:** `ab1606a`

**2. [Rule 1 - Structural test] Corrected the async finalizer ownership assertion**
- **Found during:** Task 1 focused structural check.
- **Issue:** The new oracle expected an async duplicate of `_finalize_failure`, but `AsyncStateMachine` correctly inherits the shared finalizer.
- **Fix:** Asserted the shared finalizer only on its defining base class while preserving no-conversion checks for async trigger and lifecycle methods.
- **Files modified:** `tests/test_mypyc_guard.py`.
- **Verification:** Focused structural/release selection passed.
- **Committed in:** `8195f58`

**Total deviations:** 2 auto-fixed Rule 1 corrections.
**Impact on plan:** Both corrections strengthen artifact parity and structural truth without changing the public result model, lifecycle contract, or hot success path.

## Issues Encountered

- `task typecheck-ty` still reports its existing relative-import diagnostic for `src/fast_fsm/core.py`; blocking mypy passed. The advisory command is visible by design and does not block release closure.
- Fresh mypyc async cancellation cases emit the existing Python 3.12 deprecated `throw(type, exc, tb)` warning. The required cancellation semantics passed in both origins.

## TDD Gate Compliance

- Task 1 extends closure evidence over the runtime behavior implemented by Plans 29-01 through 29-03. Its initial test run exposed an invalid inherited-finalizer assumption rather than an absent feature; the corrected contract tests then passed before the native closure.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Phase 29 now provides a complete bounded expected-rejection contract across synchronous and asynchronous selection, queries, composition, lifecycle boundaries, logging, pure source, and fresh compiled execution. Phase 30 can build on this settled runtime behavior for construction and persistence parity.

## Self-Check: PASSED

- `29-04-SUMMARY.md`, the four modified contract artifacts, and task commits `8195f58` and `ab1606a` exist.
- The only generated native shadows were moved to recoverable temporary backup directories; `task pure-source-check` and an exact module-origin assertion both finished on `src/fast_fsm/core.py`.
- No known stubs, skipped tests, unrun plan verifications, or new trust-boundary surfaces remain.

---
*Phase: 29-expected-domain-rejection*
*Completed: 2026-09-17*
