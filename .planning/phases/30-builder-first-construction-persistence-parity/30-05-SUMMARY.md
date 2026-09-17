---
phase: 30-builder-first-construction-persistence-parity
plan: 05
subsystem: documentation
tags: [fsm-builder, deprecation, persistence, sphinx, examples]
requires:
  - phase: 30-04
    provides: final/internal dictionary, clone, and snapshot parity contracts
provides:
  - Builder-first public teaching surfaces with executable regression coverage
  - Focused compatibility migration guidance for retained construction helpers
  - Architecture guidance for canonical construction and directional persistence parity
affects: [30-06, 31-semantic-diagnostics, 32-progressive-guidance]
actuals:
  tokens: 7000
  tasks: 2
  commits: 2
tech-stack:
  added: []
  patterns:
    - Extract only executable Python regions when enforcing documentation construction guidance
    - Present FSMBuilder as primary, direct machines as advanced, and from_dict as serialized-topology reconstruction
key-files:
  created: []
  modified:
    - README.md
    - docs/QUICK_START.md
    - docs/TUTORIAL.md
    - docs/api/core.md
    - docs/api/visualization.md
    - docs/api/validation.md
    - docs/dev/architecture.md
    - examples/cross_fsm_demo.py
    - tests/test_readme_examples.py
key-decisions:
  - Keep focused guidance builder-first while reserving the full progressive documentation rewrite for Phase 32.
  - Keep compatibility names in bounded prose and API references, never in executable teaching recipes.
  - Document adapter policy as cold-path canonical request publication, preserving direct dispatch isolation.
requirements-completed: [BUILD-01, BUILD-02, BUILD-03, BUILD-06, BUILD-07, BUILD-08]
coverage:
  - id: D1
    description: README, Quick Start, Tutorial, and cross-FSM example teach caller-owned states assembled through FSMBuilder and do not execute deprecated construction helpers.
    requirement: BUILD-01
    verification:
      - kind: integration
        ref: tests/test_readme_examples.py#test_active_construction_guidance_uses_builder
        status: pass
      - kind: integration
        ref: tests/test_examples_smoke.py#cross_fsm_demo
        status: pass
    human_judgment: false
  - id: D2
    description: API samples and architecture guidance consistently describe builder-first construction, warned helper compatibility, canonical request publication, directional dictionary compatibility, clone isolation, and snapshot-v1 ownership.
    requirement: BUILD-07
    verification:
      - kind: other
        ref: task docs-check
        status: pass
      - kind: other
        ref: task docs-test
        status: pass
    human_judgment: false
duration: 11 min
completed: 2026-09-17
status: complete
---

# Phase 30 Plan 05: Builder-First Guidance Summary

**Focused public and maintainer guidance now leads new programmatic construction with `FSMBuilder`, confines retained helpers to a v0.5.x migration boundary, and records accurate persistence and adapter ownership semantics.**

## Performance

- **Duration:** 11 min
- **Started:** 2026-09-17T20:12:00Z
- **Completed:** 2026-09-17T20:23:00Z
- **Tasks:** 2/2
- **Files modified:** 9

## Accomplishments

- Migrated prominent README, Quick Start, Tutorial, and cross-FSM recipes to caller-owned `State` objects built through `FSMBuilder`.
- Added a stable executable-region inventory for six active teaching surfaces, allowing compatibility prose while rejecting deprecated helper imports and calls in runnable examples.
- Updated API and architecture material with the builder/direct/from-dict roles, one canonical cold-path request transaction, exact directional persistence semantics, clone ownership, and unchanged state-only snapshot v1.

## Task Commits

1. **Task 1: Make prominent guides and the cross-FSM example builder-first** — `03de1d3`
2. **Task 2: Migrate API teaching examples and synchronize architecture guidance** — `30615ff`

## Files Created/Modified

- `README.md`, `docs/QUICK_START.md`, and `docs/TUTORIAL.md` — primary builder recipes and bounded migration guidance.
- `examples/cross_fsm_demo.py` — runnable coordinated machines assembled through `FSMBuilder`.
- `docs/api/core.md`, `docs/api/visualization.md`, and `docs/api/validation.md` — builder-first API hierarchy and teaching examples.
- `docs/dev/architecture.md` — canonical adapter transaction, compatibility, persistence, clone, snapshot, and hot-path boundaries.
- `tests/test_readme_examples.py` — executable teaching-surface inventory with stable identifiers.

## Decisions Made

- `FSMBuilder` is the ordinary programmatic path; direct sync/async machine construction remains explicitly advanced, and `from_dict()` remains serialized-topology reconstruction.
- The four retained helpers remain callable through v0.5.x and may be removed no earlier than v0.6.0, but are no longer taught as active construction recipes.
- Phase 30 records focused migration truth only; Phase 32 still owns the complete progressive documentation and release walkthrough revision.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Test validation] Corrected escaped regular-expression boundaries in the new executable-region inventory**

- **Found during:** Task 1 focused test review.
- **Issue:** The first expression used doubled raw-string escapes and would not enforce word boundaries or fenced-region extraction correctly.
- **Fix:** Restored the exact raw regular-expression escapes before running the inventory tests.
- **Files modified:** `tests/test_readme_examples.py`
- **Verification:** All six inventory cases and the complete plan verification suite pass.
- **Committed in:** `03de1d3`

**Total deviations:** 1 auto-fixed (Rule 1 test-validation correction).
**Impact on plan:** The correction makes the planned regression meaningful without expanding runtime or documentation scope.

## Issues Encountered

The sandbox could not read the shared `uv` cache; rerunning the same approved project commands with cache access completed all checks successfully.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Plan 30-06 can synchronize the normative API memory and perform the final structural, pure/native, and parity closure against a consistent public contract.

## Self-Check: PASSED

- All nine plan-owned documentation, example, and test files exist.
- Task commits `03de1d3` and `30615ff` exist in git history.
- The six-surface inventory, cross-FSM smoke test, strict Sphinx HTML build, and doctest build pass.

---
*Phase: 30-builder-first-construction-persistence-parity*
*Completed: 2026-09-17*
