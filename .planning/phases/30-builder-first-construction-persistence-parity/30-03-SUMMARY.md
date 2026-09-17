---
phase: 30-builder-first-construction-persistence-parity
plan: 03
subsystem: core-construction
tags: [deprecation, compatibility, fsm-builder, construction-parity, typing]
requires:
  - phase: 30-02
    provides: canonical builder and adapter final/internal transition parity
provides:
  - Exactly one caller-attributed, payload-free deprecation warning per retained construction helper
  - Private non-warning compatibility workers that preserve classmethod and topology semantics
  - Deprecated-helper parity coverage for finality, internal mode, priority, atomicity, exports, and stubs
affects: [30-04, 30-05, 30-06, compatibility-guidance, construction-parity]
actuals:
  tokens: 2941
  tasks: 2
  commits: 3
tech-stack:
  added: []
  patterns:
    - Public warning boundary followed by a private non-warning compatibility worker
    - Warning-contained helper parity oracle for retained construction APIs
key-files:
  created: []
  modified:
    - src/fast_fsm/core.py
    - tests/test_builder.py
    - tests/test_final_states.py
    - tests/test_construction_parity.py
    - .specify/memory/spr-core-api.md
key-decisions:
  - Each deprecated entry emits its warning before any validation, then invokes a private worker rather than another public boundary.
  - Existing stubs and package exports already retain the required public signatures and names, so no synchronization edit was needed.
requirements-completed: [BUILD-03, BUILD-06]
coverage:
  - id: D1
    description: Four legacy construction boundaries emit exactly one fixed caller-attributed warning, including invalid calls, while modern construction surfaces remain silent.
    requirement: BUILD-03
    verification:
      - kind: unit
        ref: tests/test_builder.py#test_deprecated_construction_boundaries_warn_once_at_the_user_call_site
        status: pass
      - kind: unit
        ref: tests/test_builder.py#test_nondeprecated_construction_surfaces_remain_silent
        status: pass
    human_judgment: false
  - id: D2
    description: Deprecated helpers retain exports, PEP 561 declarations, subclass construction, state identity, finality, internal priority selection, and atomic late-failure behavior.
    requirement: BUILD-06
    verification:
      - kind: integration
        ref: tests/test_construction_parity.py#test_deprecated_quick_helpers_keep_final_internal_priority_and_atomicity
        status: pass
      - kind: unit
        ref: tests/test_builder.py#test_deprecated_construction_public_surface_remains_typed_exported_and_subclass_safe
        status: pass
    human_judgment: false
duration: 6 min
completed: 2026-09-17
status: complete
---

# Phase 30 Plan 03: Warned Compatibility Constructors Summary

**The four retained convenience constructors now provide one actionable, caller-attributed migration warning while preserving their v0.5.x construction behavior through private canonical workers.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-09-17T19:50:46Z
- **Completed:** 2026-09-17T19:56:28Z
- **Tasks:** 2/2
- **Files modified:** 5

## Accomplishments

- Added fixed payload-free `DeprecationWarning` boundaries for `simple_fsm`, `quick_fsm`, `StateMachine.quick_build`, and `StateMachine.from_states` before validation begins.
- Routed public wrappers to private non-warning workers, preventing nested warnings while retaining `cls` construction, state identity, canonical transaction validation, and failure atomicity.
- Extended the construction oracle with warning-contained helper cells for state-only and quick adapters, including final destinations, internal priority fallthrough, and late invalid rows.
- Verified package exports and PEP 561 declarations remain intact, and recorded the supported compatibility window in the project API memory as required by `AGENTS.md`.

## Task Commits

1. **Task 1: Add exactly-once user-attributed warning boundaries** — `7d20831` (RED coverage), `35f67ac` (implementation)
2. **Task 2: Preserve helper API, typing, identity, and semantic parity through v0.5.x** — `81db409` (parity and API-contract evidence)

## Files Created/Modified

- `src/fast_fsm/core.py` — fixed warning constants, public warning boundaries, and private compatibility workers.
- `tests/test_builder.py` — exact warning, attribution, error-path, silence, export, stub, and subclass tests.
- `tests/test_final_states.py` — captures expected helper warnings while retaining final-source failure coverage.
- `tests/test_construction_parity.py` — warning-contained state-only and quick-helper parity cells.
- `.specify/memory/spr-core-api.md` — durable v0.5.x compatibility and migration contract.

## Decisions Made

- Use one fixed message per public symbol and `stacklevel=2`; warnings remain cold construction-path work and never enter dispatch.
- Preserve the existing stub and root-export declarations unchanged because they already describe the retained compatibility cycle exactly.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Test placement bug] Restored the central parity helper return path**

- **Found during:** Task 2 targeted parity verification.
- **Issue:** The first parity-test insertion placed the new warning helper inside the existing shared topology exercise function, making that function return `None`.
- **Fix:** Restored the full topology exercise body and moved the warning helper below it.
- **Files modified:** `tests/test_construction_parity.py`
- **Verification:** Targeted helper parity suite passes.
- **Committed in:** `81db409`

**2. [Rule 2 - Project contract] Synchronized the changed public API contract into project memory**

- **Found during:** Task 2 closeout.
- **Issue:** `AGENTS.md` requires a relevant SPR update in the same commit as a public API or behavior change.
- **Fix:** Recorded the exact compatibility window, one-warning boundary, private-worker rule, and silent modern surfaces.
- **Files modified:** `.specify/memory/spr-core-api.md`
- **Verification:** The documented contract matches the direct warning and parity tests.
- **Committed in:** `81db409`

**Total deviations:** 2 auto-fixed (1 Rule 1 test correction, 1 Rule 2 project-contract requirement).
**Impact on plan:** Both adjustments preserve the plan's compatibility boundary without creating another topology path or changing dispatch behavior.

## Issues Encountered

- `task typecheck-ty` remains advisory and reports the pre-existing unresolved relative import `.conditions` in `src/fast_fsm/core.py`. Blocking `task typecheck-mypy` passes with no issues.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 04 can extend the settled adapter contract into strict dictionary, clone, and snapshot persistence parity.
- Plan 05 can present the now-fixed migration wording in focused user-facing guidance without changing runtime behavior.

## Self-Check: PASSED

- Required modified files and commits `7d20831`, `35f67ac`, and `81db409` exist.
- The focused 38-test Plan 30-03 suite, Ruff format/lint, and blocking mypy pass.
- `ty` was run and retains only the documented pre-existing advisory diagnostic.

---
*Phase: 30-builder-first-construction-persistence-parity*
*Completed: 2026-09-17*
