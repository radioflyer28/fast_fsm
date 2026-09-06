---
phase: 15-release-baseline-evidence-harness
plan: 01
subsystem: release-tooling
tags: [build-mode, mypyc, pure-python, wheel-evidence, slots-policy]
requires:
  - phase: 14
    provides: Existing optional core.py-only mypyc boundary and package source layout.
provides:
  - Explicit auto, pure, and compiled build-mode selection with a legacy pure alias.
  - Non-destructive source-origin and wheel-identity verification tooling.
  - Recursive slots-policy inventory with measured deliberate exceptions.
affects: [15-02, 15-03, 15-04, 15-05, 15-06, release-workflow]
actuals:
  tokens: 10361
  tasks: 3
  commits: 6
tech-stack:
  added: []
  patterns:
    - Standard-library-only maintainer CLI under tools/.
    - Fail-closed evidence classification before imports or artifact publication.
    - AST inventory plus runtime measurement for slots-policy exceptions.
key-files:
  created:
    - tools/__init__.py
    - tools/build_modes.py
    - tools/release_evidence.py
    - MANIFEST.in
    - tests/test_build_modes.py
    - tests/test_release_evidence.py
  modified:
    - setup.py
key-decisions:
  - "FAST_FSM_BUILD_MODE accepts auto, pure, and compiled; FAST_FSM_PURE_PYTHON=1 remains the pure-mode alias."
  - "Release evidence reads paths and wheel archives without extracting or deleting developer artifacts."
  - "CompiledFuncCondition and TransitionError are the only measured slots-policy exceptions."
patterns-established:
  - "Keep maintainer evidence tooling outside fast_fsm's public runtime API."
  - "Use recursive AST discovery to prevent future production classes silently bypassing policy audits."
requirements-completed: [REL-04, REL-06, REL-08, TEST-02]
coverage:
  - id: D1
    description: Build-mode parsing, setup integration, legacy alias compatibility, and pure-sdist reproduction.
    requirement: REL-04
    verification:
      - kind: integration
        ref: uv run --no-sync pytest tests/test_build_modes.py -x -q
        status: pass
      - kind: unit
        ref: Python 3.10 BuildMode import check
        status: pass
    human_judgment: false
  - id: D2
    description: Non-destructive native-shadow preflight and deterministic pure/compiled wheel identity evidence.
    requirement: TEST-02
    verification:
      - kind: integration
        ref: uv run --no-sync pytest tests/test_release_evidence.py -x -q -k 'shadow or source_origin or wheel'
        status: pass
      - kind: other
        ref: tools/release_evidence.py verify-source against current native shadows
        status: pass
    human_judgment: false
  - id: D3
    description: Recursive slots-policy classification and live measurements for both intentional exceptions.
    requirement: REL-08
    verification:
      - kind: integration
        ref: uv run --no-sync pytest tests/test_release_evidence.py -x -q -k slots
        status: pass
    human_judgment: false
duration: 16 min
completed: 2026-08-29
status: complete
---

# Phase 15 Plan 01: Build and Artifact Evidence Primitives Summary

**Explicit build modes, non-destructive pure-source/wheel evidence, and a recursive measured slots-policy audit for the Phase 15 release baseline.**

## Performance

- **Duration:** 16 min
- **Started:** 2026-08-29T18:55:45Z
- **Completed:** 2026-08-29T19:12:18Z
- **Tasks:** 3/3
- **Files modified:** 7

## Accomplishments

- Added Python-3.10-compatible `BuildMode` parsing for auto/pure/compiled intent, preserving `FAST_FSM_PURE_PYTHON=1` and the `core.py`-only mypyc seam.
- Added a standard-library release-evidence CLI that preflights native shadows before import and independently classifies repeated wheel archives from filename tags, WHEEL/METADATA headers, and native members.
- Added a recursive AST slots inventory that classifies every top-level production class and measures the two deliberate `native_class=False` exceptions.

## Task Commits

1. **Task 1: Wire one build-mode selection path from environment to setup behavior**
   - `4244535` — `test(15-01): add failing build mode selector coverage`
   - `75f0c17` — `feat(15-01): add explicit build mode selection`
2. **Task 2: Prove pure-source and wheel identity non-destructively**
   - `714aed8` — `test(15-01): add failing release evidence coverage`
   - `f673901` — `feat(15-01): verify pure source and wheel identity`
3. **Task 3: Recursively inventory and measure the registered slots-policy exceptions**
   - `2c33e03` — `test(15-01): add failing slots policy coverage`
   - `842981f` — `feat(15-01): audit slots policy recursively`

## Files Created/Modified

- `tools/build_modes.py` — Build intent parser shared by packaging commands.
- `tools/release_evidence.py` — Maintainer-only source, wheel, and slots evidence CLI.
- `setup.py` — Uses the shared selector and imports it safely from unpacked sdists.
- `MANIFEST.in` — Includes setup-time tool modules in source distributions.
- `tests/test_build_modes.py` — Selector matrix and pure-sdist integration coverage.
- `tests/test_release_evidence.py` — Shadow, wheel identity, and recursive slots regression coverage.

## Decisions Made

- New `FAST_FSM_BUILD_MODE` configuration rejects invalid or contradictory values before the optional mypyc fallback; `compiled` records intent but retains Phase 15's existing non-strict fallback.
- A source verifier reports exact native shadow paths and cleanup guidance without mutating files; the current checkout's two native artifacts were detected and their SHA-1 hashes remained unchanged.
- The slots registry intentionally contains only `fast_fsm.core.CompiledFuncCondition` and `fast_fsm.core.TransitionError`, each with a distinct rationale and live size/`__dict__` measurement.

## Verification

- `FAST_FSM_BUILD_MODE=pure uv run --no-sync pytest tests/test_build_modes.py tests/test_release_evidence.py -x -q` — 30 passed.
- `uv run --no-sync mypy tools/build_modes.py tools/release_evidence.py` — passed.
- `uv run --no-sync ruff format --check ...` and `uv run --no-sync ruff check ...` on all Plan 01 Python files — passed.
- `uv run --no-sync --python 3.10 --no-project python -c "from tools.build_modes import BuildMode, resolve_build_mode; ..."` — passed.
- The live `verify-source` command failed closed on both existing native artifacts and left their before/after SHA-1 hashes identical.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Made the selector importable during PEP 517 sdist builds**

- **Found during:** Task 1
- **Issue:** `setuptools.build_meta` executed `setup.py` without the unpacked source root on `sys.path`, so `tools.build_modes` could not be imported from the intentional pure sdist.
- **Fix:** Added the resolved setup directory to `sys.path` before importing the bundled selector.
- **Files modified:** `setup.py`, `tests/test_build_modes.py`
- **Verification:** The pure sdist contains both tool modules and an unpacked archive builds a wheel successfully.
- **Committed in:** `75f0c17`

---

**Total deviations:** 1 auto-fixed (1 Rule 1 bug).
**Impact on plan:** Required for the promised source-distribution behavior; no scope expansion or public API change.

## Issues Encountered

- The sandbox cannot synchronize uv's cache during test execution, so checks used the existing locked environment through `uv run --no-sync`. The planned tests, type check, formatting, and lint all completed successfully.

## Known Stubs

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 02 can build the deterministic evidence manifest and canonical quality-gate wrappers on the new selector and verification CLI.
- The current checkout deliberately retains two detected native shadows; future clean-checkout collection must use the new preflight rather than silently treating this worktree as pure source.

## Self-Check: PASSED

All seven Plan 01 implementation files and all six task commits are present on the execution branch.

---
*Phase: 15-release-baseline-evidence-harness*
*Plan: 01*
*Completed: 2026-08-29*
