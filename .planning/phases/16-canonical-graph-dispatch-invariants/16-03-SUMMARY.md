---
phase: 16-canonical-graph-dispatch-invariants
plan: 03
subsystem: builder
tags: [fsm-builder, async, mypyc, state-machine, transaction]
requires:
  - phase: 16-02
    provides: Cycle-safe built-in wrapper classification and async guard evaluation.
provides:
  - Transactional FSMBuilder publication with frozen post-build staging.
  - Recursive async preflight across staged guards, declarative metadata, and callbacks.
affects: [16-04-declarative-history, 17-atomic-transition-lifecycle, 20-installed-artifact-parity]
actuals:
  tokens: 9111
  tasks: 2
  commits: 5
tech-stack:
  added: []
  patterns: [publish-on-success cache, first-statement builder freeze guard, shared wrapper preflight, asserted pure-compiled parity]
key-files:
  created: []
  modified:
    - src/fast_fsm/core.py
    - tests/test_builder.py
    - tests/test_async.py
    - .specify/memory/spr-core-api.md
key-decisions:
  - "A successful builder cache is the sole freeze marker; all construction remains local until wiring completes."
  - "Static wrapper classification is shared between builder preflight and runtime evaluation without allocating a candidate machine."
  - "force_async() and force_sync() disable auto selection so explicit modes remain authoritative through build()."
patterns-established:
  - "Builder mutations begin with _ensure_mutable(), preserving staging and topology after a rejected call."
  - "Async compatibility is preflighted over every staged source before candidate allocation or cache publication."
requirements-completed: [GRAF-02, GRAF-04, GRAF-05, GRAF-08]
coverage:
  - id: D1
    description: "Builder staging preserves canonical State identity, freezes every mutation after successful publication, and remains repairable after failed wiring."
    requirement: GRAF-04
    verification:
      - kind: integration
        ref: "tests/test_builder.py#TestFSMBuilderPublication"
        status: pass
      - kind: integration
        ref: "tools/phase16_isolated_verify.py --mode task --build-mode compiled ... pytest tests/test_mypyc_guard.py tests/test_builder.py tests/test_async.py -x -q"
        status: pass
    human_judgment: false
  - id: D2
    description: "Builder preflight detects nested built-in async wrappers, declarative metadata, and queued callbacks; explicit sync rejects them before publication."
    requirement: GRAF-05
    verification:
      - kind: integration
        ref: "tests/test_builder.py#TestFSMBuilderAsyncPreflight"
        status: pass
      - kind: integration
        ref: "tests/test_async.py#TestAsyncBuilderPreflight"
        status: pass
    human_judgment: false
  - id: D3
    description: "The builder retains the single core.py mypyc boundary while matching pure and compiled materialization behavior."
    requirement: GRAF-08
    verification:
      - kind: integration
        ref: "task typecheck-mypy"
        status: pass
      - kind: integration
        ref: "tools/phase16_isolated_verify.py --mode task --build-mode compiled ... pytest tests/test_mypyc_guard.py tests/test_builder.py tests/test_async.py -x -q"
        status: pass
    human_judgment: false
duration: 12m
completed: 2026-08-30
status: complete
---

# Phase 16 Plan 03: Builder Publication and Async Preflight Summary

**FSMBuilder now freezes only after a fully wired local machine is published, and preflights nested asynchronous requirements before choosing or allocating that machine.**

## Performance

- **Duration:** 12m
- **Started:** 2026-08-30T05:06:15Z
- **Completed:** 2026-08-30T05:18:41Z
- **Tasks:** 2/2
- **Files modified:** 4

## Accomplishments

- Added identity-canonical builder staging, immediate post-success mutation rejection, and cache-last local candidate publication.
- Added shared recursive async preflight over built-in wrappers, declarative handlers/guards, and queued async callbacks.
- Made explicit force modes authoritative and made explicit sync fail before candidate allocation instead of dropping async behavior.
- Proved materialization and nested async evaluation against asserted pure and compiled temporary-tree contexts.

## Task Commits

1. **Task 1: Freeze every builder mutation only after successful publication**
   - `22d9d0e` — RED builder publication coverage
   - `762262d` — transactional builder publication, freeze guard, and SPR update
2. **Task 2: Preflight nested async requirements before choosing or allocating a machine**
   - `4dfbd22` — RED nested async preflight coverage
   - `c42647c` — recursive preflight, authoritative force modes, and SPR update
   - `ccf9c9a` — compiled/pure exception-contract parity correction

## Files Created/Modified

- `src/fast_fsm/core.py` — builder freeze guard, identity-safe staging, cache-last materialization, and preflight selection.
- `tests/test_builder.py` — lifecycle, repair, explicit-mode, wrapper, DAG, and cycle behavior matrix.
- `tests/test_async.py` — real builder-selected async nested-leaf execution proof.
- `.specify/memory/spr-core-api.md` — builder publication and async-preflight contracts.

## Decisions Made

- Use the existing `StateMachine._contains_async_requirement()` classifier directly from preflight so supported wrappers cannot be classified differently at construction and runtime.
- Treat force modes as explicit selections by disabling automatic mode when either force method is called.
- Keep a failed candidate private and discard it naturally; there is no rollback work because no cache is published early.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Compiled parity] Made the invalid-initial-state test mode-neutral.**

- **Found during:** Task 2 final compiled verification
- **Issue:** The mypyc constructor type guard raises `TypeError` before the pure-Python body can emit its more specific message.
- **Fix:** Assert the stable `TypeError` contract rather than a pure-mode-only message.
- **Files modified:** `tests/test_builder.py`
- **Verification:** Final asserted pure and compiled matrices passed.
- **Committed in:** `ccf9c9a`

---

**Total deviations:** 1 auto-fixed (Rule 1)
**Impact on plan:** The correction preserves the intended input contract across both supported artifact modes with no scope expansion.

## Issues Encountered

- The first full compiled matrix exposed the mypyc boundary difference above; the final native matrix passed after the test correction.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Plan 16-04 can build on frozen, transactionally published builders and a deterministic recursive async-selection contract. No plan-local blockers remain.

## Self-Check: PASSED

- All four task artifacts and this summary exist.
- All five Task 1/Task 2 commits are present in history.
- The resolved mypyc parity correction is recorded in `.planning/WINDOWS.md` as fixed.

---
*Phase: 16-canonical-graph-dispatch-invariants*
*Plan: 03*
*Completed: 2026-08-30*
