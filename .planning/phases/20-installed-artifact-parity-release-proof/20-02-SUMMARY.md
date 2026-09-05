---
phase: 20-installed-artifact-parity-release-proof
plan: "02"
subsystem: release-evidence
tags: [uv, mypyc, sdist, wheel, artifact-verification, provenance]
requires:
  - phase: 20-installed-artifact-parity-release-proof
    provides: exact-path fresh-environment installed wheel verifier and shared conformance oracle
provides:
  - fail-closed explicit compiled builds with a native fast_fsm.core archive requirement
  - bounded sdist inspection before extraction with pure and compiled installed child-wheel proof
  - parent SHA-256 lineage for explicit offline sdist derivations
affects: [20-03, 20-04, 20-05, 20-06, release-workflow]
actuals:
  tokens: 7762.75
  tasks: 2
  commits: 4
tech-stack:
  added: []
  patterns:
    - explicit build intent checked independently at compiler, archive, and installed-runtime boundaries
    - validate full sdist inventory before safe extraction, then reuse the exact installed-wheel verifier
    - parent-computed sdist SHA-256 and explicit child intent form deterministic derivation lineage
key-files:
  created: []
  modified:
    - setup.py
    - MANIFEST.in
    - tools/release_evidence.py
    - tests/test_build_modes.py
    - tests/test_installed_artifacts.py
key-decisions:
  - "Only AUTO may warn and fall back from a mypyc failure; explicit COMPILED propagates the error."
  - "Compiled archive evidence requires a native fast_fsm.core member, not merely any native package member."
  - "Sdist child wheels build offline for the verifier interpreter, use exact pinned build requirements, and retain parent SHA-256 lineage."
patterns-established:
  - "Sdist proof: bound archive inspection → safe extraction → explicit child build → exact installed verifier → lineage validation."
requirements-completed: [REL-03, REL-07, TEST-04]
coverage:
  - id: D1
    description: Explicit compiled builds reject compiler failures and archives without a native fast_fsm.core member while AUTO and PURE retain their distinct contracts.
    requirement: REL-03
    verification:
      - kind: unit
        ref: tests/test_build_modes.py#test_compiled_intent_propagates_mypyc_failures
        status: pass
      - kind: integration
        ref: uv run pytest tests/test_build_modes.py tests/test_installed_artifacts.py -x -q -k 'compiled or mypyc or native or pure'
        status: pass
    human_judgment: false
  - id: D2
    description: A bounded sdist archive produces explicit pure and compiled wheels whose installed evidence is tied to one parent filename and SHA-256.
    requirement: REL-07
    verification:
      - kind: integration
        ref: tests/test_build_modes.py#test_sdist_derivation_reuses_installed_wheel_verification
        status: pass
      - kind: integration
        ref: uv run pytest tests/test_build_modes.py tests/test_installed_artifacts.py -x -q -k 'sdist or archive or derivation or lineage'
        status: pass
    human_judgment: false
  - id: D3
    description: Unsafe sdist paths, member types, duplicate destinations, size limits, native residue, and invalid child lineage fail before artifact acceptance.
    requirement: TEST-04
    verification:
      - kind: unit
        ref: tests/test_installed_artifacts.py#test_sdist_archive_rejects_unsafe_members_before_extraction
        status: pass
      - kind: unit
        ref: tests/test_installed_artifacts.py#test_sdist_archive_enforces_member_and_uncompressed_bounds
        status: pass
    human_judgment: false
duration: 20m
completed: 2026-09-05
status: complete
---

# Phase 20 Plan 02: Installed Artifact Parity & Release Proof Summary

**Explicit compiled builds now fail closed, and bounded source archives prove installed pure and compiled child wheels with SHA-256 parent lineage.**

## Performance

- **Duration:** 20m
- **Started:** 2026-09-05T01:13:42Z
- **Completed:** 2026-09-05T01:34:08Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Made explicit `FAST_FSM_BUILD_MODE=compiled` propagate mypyc failures while preserving AUTO fallback and PURE bypass behavior.
- Required platform wheels to contain a native `fast_fsm.core` member before they can be classified as compiled evidence.
- Added safe bounded sdist inspection, explicit offline pure/compiled child derivations, and mandatory installed-wheel verification with parent filename/SHA-256 lineage.

## Task Commits

1. **Task 1: Fail closed on explicit compiled intent and missing native output** — `0e218fe` (RED), `2d27ecf` (GREEN)
2. **Task 2: Verify bounded sdist contract and explicit pure/compiled derivations** — `a1ca8ea` (RED), `047cb4f` (GREEN)

## Files Created/Modified

- `setup.py` — re-raises compiler failures for explicit compiled intent only.
- `MANIFEST.in` — includes the checkout-independent conformance collector in source archives.
- `tools/release_evidence.py` — verifies native core archive membership, bounded sdist contracts, explicit child derivations, and lineage.
- `tests/test_build_modes.py` — covers compiler failures, native-core absence, offline source builds, and installed child proof.
- `tests/test_installed_artifacts.py` — covers sdist traversal/type/duplicate/limit/native-residue rejection and child-lineage failures.

## Decisions Made

- Explicit compiled intent is a release claim, so it cannot silently degrade to a pure wheel when mypyc fails.
- Archive shape never certifies a child wheel by itself: both derived wheels must use the Plan 20-01 exact installed conformance verifier.
- Derived builds use the verifier interpreter and offline, reviewed PEP 517 pins so a local proof cannot switch Python versions or resolve unreviewed packages.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Pinned sdist child builds to the verifier interpreter**
- **Found during:** Task 2
- **Issue:** `uv build` defaulted to CPython 3.13 while the isolated verifier created a CPython 3.12 environment, correctly rejecting the incompatible child wheel.
- **Fix:** Passed the current verifier interpreter explicitly to each derived `uv build` invocation.
- **Files modified:** `tools/release_evidence.py`
- **Verification:** The pure and compiled child derivation integration test passes.
- **Committed in:** `047cb4f`

**2. [Rule 2 - Missing Critical] Forced local artifact builds to stay offline**
- **Found during:** Task 2
- **Issue:** A pinned local build attempted dependency resolution from PyPI, violating the local-only artifact-proof scope and making proof availability depend on external state.
- **Fix:** Added `--offline` to the Plan 20 build paths and regression fixtures; missing reviewed pins now fail closed instead of reaching the network.
- **Files modified:** `tools/release_evidence.py`, `tests/test_build_modes.py`, `tests/test_installed_artifacts.py`
- **Verification:** Full sequential packaging/artifact suite passes with offline child derivations.
- **Committed in:** `047cb4f`

---

**Total deviations:** 2 auto-fixed (1 Rule 2, 1 Rule 3).
**Impact on plan:** Both changes strengthen the planned artifact-proof boundary without broadening scope or adding dependencies.

## Issues Encountered

- The local beads service was unreachable, so no issue-status mutation was attempted. This did not affect implementation or verification.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Later Phase 20 plans can aggregate explicit child evidence knowing every accepted compiled artifact has both native archive and installed-origin proof.
- No hosted CI, tag, publication, or remote action was performed.

## Self-Check: PASSED

---
*Phase: 20-installed-artifact-parity-release-proof*
*Completed: 2026-09-05*
