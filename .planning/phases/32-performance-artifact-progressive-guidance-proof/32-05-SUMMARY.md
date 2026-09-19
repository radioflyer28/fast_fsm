---
phase: 32-performance-artifact-progressive-guidance-proof
plan: 05
subsystem: documentation
tags: [documentation, FSMBuilder, migration, finality, transition-results]
requires:
  - phase: 32-04
    provides: "Controller-owned drone tutorial with priority, finality, rejection, and self-transition behavior"
provides:
  - "Builder-first public onboarding with tested compatibility migrations"
  - "Runnable public contrasts for flat-FSM finality, selection, failure, and self-transition semantics"
affects: [README, QUICK_START, docs, phase-32-plan-06]
actuals:
  tokens: 5686
  tasks: 2
  commits: 4
tech-stack:
  added: []
  patterns:
    - "Marked self-contained documentation fences execute through public-guide regression tests"
    - "Compatibility prose maps each warned helper to explicit builder operations without recommending legacy calls"
key-files:
  created: []
  modified:
    - README.md
    - docs/QUICK_START.md
    - tests/test_readme_examples.py
key-decisions:
  - "Keep the first runnable recipe builder-first while retaining direct constructors and from_dict as supported distinct advanced paths."
  - "Teach finality, selection, and self-transition mode through exact result fields and lifecycle observations rather than graph shape or state name."
patterns-established:
  - "Public documentation markers use docs-exec:<topic> fences that are extracted and executed by tests."
requirements-completed: [DOC-02, DOC-03, DOC-04]
coverage:
  - id: D1
    description: "README and Quick Start establish FSMBuilder as the first runnable construction route and retain advanced construction roles."
    requirement: DOC-02
    verification:
      - kind: unit
        ref: "tests/test_readme_examples.py#test_public_entry_guides_start_with_a_small_builder_recipe"
        status: pass
      - kind: other
        ref: "task docs-check"
        status: pass
    human_judgment: false
  - id: D2
    description: "All four warned convenience helpers have literal FSMBuilder replacements, executable builder-side recipes, and v0.5.x/v0.6.0 timing guidance."
    requirement: DOC-03
    verification:
      - kind: unit
        ref: "tests/test_readme_examples.py#test_compatibility_migration_maps_each_warned_helper_to_builder"
        status: pass
      - kind: unit
        ref: "tests/test_readme_examples.py#test_documented_builder_migration_replacements_execute"
        status: pass
    human_judgment: false
  - id: D3
    description: "Both public entry guides execute final-versus-sink, false-guard/rejection/failure, and internal-versus-external-self contrasts."
    requirement: DOC-04
    verification:
      - kind: unit
        ref: "tests/test_readme_examples.py#test_documented_flat_fsm_semantic_contrasts_execute"
        status: pass
      - kind: other
        ref: "task docs-test"
        status: pass
    human_judgment: false
duration: 6min
completed: 2026-09-19
status: complete
---

# Phase 32 Plan 05: Builder-First Public Guidance Summary

**The README and Quick Start now lead with a small FSMBuilder recipe, give exact compatibility migrations, and execute the flat-FSM semantics that diagrams alone cannot show.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-09-19T23:47:17Z
- **Completed:** 2026-09-19T23:53:01Z
- **Tasks:** 2/2
- **Files modified:** 3

## Accomplishments

- Replaced generic legacy-helper advice with one literal FSMBuilder migration for each warned convenience API, its per-call warning behavior, and the v0.5.x/v0.6.0 compatibility window.
- Kept the public learning path builder-first while clearly preserving direct construction, declarative states, and serialized `from_dict()` topology as supported distinct uses.
- Added paired executable finality, priority-selection, expected-rejection, unexpected-failure, and self-transition lifecycle examples to both public entry guides.
- Linked the concise examples to the deterministic controller-owned drone tutorial for the fuller telemetry and post-commit command story.

## Task Commits

1. **Task 1: Reorder onboarding and provide exact migration replacements** - `f1eba02` (test), `8a3f5f2` (docs)
2. **Task 2: Add paired semantic contrasts with observable results** - `819994b` (test), `04b0102` (docs)

## Files Created/Modified

- `README.md` - Progressive public landing page with migration mapping, lower-page migration recipes, semantic contrasts, and drone link.
- `docs/QUICK_START.md` - Builder-first quick path with lower-page executable migrations and semantic contrasts.
- `tests/test_readme_examples.py` - Order, compatibility timing, legacy-scan, and marked-snippet execution regressions.

## Decisions Made

- Kept short initial construction snippets small; detailed migrations and semantic comparisons appear after the initial builder path.
- Used exact `TransitionResult` fields, `is_terminated`, and callback counts to prove behavior rather than suggesting a visual graph or unchanged state name is sufficient.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- The sandboxed Sphinx command could not open the existing user uv cache. Re-running the same project command in the normal permitted environment passed; no project configuration changed.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Public guidance and executable documentation proof are ready for Phase 32's remaining release/audit work.
- No documentation implementation blocker remains.

## Self-Check: PASSED

- All three modified documentation/test files and the four task commits are present.
- `uv run pytest tests/test_readme_examples.py -x -q` passed (35 tests).
- `task docs-check` and `task docs-test` passed.

---
*Phase: 32-performance-artifact-progressive-guidance-proof*
*Completed: 2026-09-19*
