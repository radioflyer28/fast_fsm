---
phase: 15-release-baseline-evidence-harness
plan: 09
subsystem: release-evidence
tags: [python-toolchain, freshness, clean-archive, pure-source, ci-gap]
requires:
  - phase: 15-08
    provides: pinned Task CI contract and the diagnostic 782-test hosted inventory
provides:
  - Fail-closed Python major.minor freshness projection with exact patch audit retention
  - Exact 794-test clean pure-source baseline and second-archive freshness proof
  - Local corrective evidence ready for Plan 15-05's exact-SHA hosted rerun
affects: [plan-15-05, github-actions, release-gate, rel-05, rel-06, test-02]
actuals:
  tokens: 1567.25
  tasks: 2
  commits: 5
tech-stack:
  added: []
  patterns: [deep-copy stable projection, fail-closed Python identity parsing, two-clean-archive baseline proof]
key-files:
  created: [.planning/phases/15-release-baseline-evidence-harness/15-09-SUMMARY.md]
  modified: [tools/release_evidence.py, tests/test_release_evidence.py, evidence/release-baseline.json]
key-decisions:
  - "Compare only the copied toolchain.python major.minor identity while retaining exact patch observations in serialized evidence."
  - "Keep exact test inventory, coverage regression validation, tool/package pins, source/artifact identity, and slots evidence strict."
  - "Keep fast_fsm-bhn and fast_fsm-6yg open until Plan 15-05 records successful terminal exact-SHA Actions evidence."
patterns-established:
  - "Release evidence may normalize only a documented stable projection; serialized audit data and caller dictionaries remain unchanged."
  - "A baseline write requires a committed clean pure archive, an independently measured suite count, reviewed diff, and a second read-only archive proof."
requirements-completed: [REL-05, REL-06, TEST-02]
coverage:
  - id: D1
    description: "Python patch portability preserves exact audit versions while minor and malformed identities remain blocking"
    requirement: REL-06
    verification:
      - kind: unit
        ref: "tests/test_release_evidence.py#manifest_freshness"
        status: pass
      - kind: other
        ref: "uv run pytest tests/test_release_evidence.py -x -q -k 'python and (toolchain or manifest or freshness)'"
        status: pass
    human_judgment: false
  - id: D2
    description: "Exact 794-test pure-source release baseline remains fresh without relaxing strict fields"
    requirement: REL-05
    verification:
      - kind: e2e
        ref: "clean archive 8aeedec: FAST_FSM_BUILD_MODE=pure task release-baseline-write"
        status: pass
      - kind: e2e
        ref: "clean archive e4d801a: FAST_FSM_BUILD_MODE=pure task release-baseline-check && task release-gate"
        status: pass
    human_judgment: false
  - id: D3
    description: "Pure source-origin evidence is collected before every clean-archive quality gate"
    requirement: TEST-02
    verification:
      - kind: e2e
        ref: "both clean archives: FAST_FSM_BUILD_MODE=pure uv run python tools/release_evidence.py verify-source --json"
        status: pass
    human_judgment: false
duration: 5 min
completed: 2026-08-29
status: complete
---

# Phase 15 Plan 09: Portable Python Freshness Summary

**Python patch-version portability now compares only the copied major.minor identity while exact audit patches, 794-test inventory, coverage, pins, source, artifact, and slots evidence remain strict.**

## Performance

- **Duration:** 5 min
- **Started:** 2026-08-29T21:39:08Z
- **Completed:** 2026-08-29T21:44:22Z
- **Tasks:** 2/2
- **Files modified:** 3
- **Clean baseline:** 794 collected/passed; 0 failed/errors/skipped; total source coverage 95.75%; `core.py` coverage 92.95%; uv 0.12.6; Python 3.12.10.

## Diagnostic and Outcome

GitHub Actions run `33276055108` at exact SHA
`8d1a4dca82c25cb107dee505002b559221099cab` reached terminal conclusions for
all 29 jobs, but its pure evidence freshness job failed because the tracked
baseline contained 775 tests and Python 3.12.10 while the hosted runner
observed 782 tests and Python 3.12.3. This plan preserves the exact patch
observations for audit, treats only numeric Python major.minor as portable for
freshness, and records the exact current 794-test inventory from committed
source. It does not claim hosted corrective success.

## Accomplishments

- Added TDD coverage that accepts 3.12.10/3.12.3 without mutating or rewriting either serialized manifest, while rejecting different minors and malformed or incomplete identities with `toolchain.python` evidence errors.
- Preserved field-level staleness for exact test counts/outcomes, uv pins, and all other stable fields, and preserved two-decimal total/core coverage regression failures even across a portable Python patch change.
- Regenerated the baseline from clean committed archive `8aeedec646e7379c18f360c8b8751698c99df37d` after immediate pure-source preflight and independent 794-test JUnit collection.
- Proved the baseline at `e4d801a2649991b1d79d64e67547bd260d251672` from a second clean archive: read-only check passed, manifest bytes stayed at SHA-256 `70d17dfa68520f65f1a5117abead3c8dc6fd902a95a4b78daf359c16cedca765`, and the complete release gate passed.

## Task Commits

Each task was committed atomically:

1. **Task 1: Define and implement portable Python toolchain freshness** - `46dcde4` (RED test), `30e61d6` (required test formatting), `8aeedec` (GREEN fix)
2. **Task 2: Refresh and prove the exact post-test baseline in two clean archives** - `e4d801a` (baseline)

## Files Created/Modified

- `tools/release_evidence.py` - Parses an exact three-component numeric Python version into a fail-closed `major.minor` value only on the deep stable comparison copy.
- `tests/test_release_evidence.py` - Proves same-minor portability, mutation/serialization retention, minor and malformed rejection, strict test inventory and pins, and coverage-regression preservation.
- `evidence/release-baseline.json` - Records the exact clean 794-test inventory while retaining Python 3.12.10 and all unchanged strict evidence fields.

## Decisions Made

- Retained `toolchain.python` and `measurement_environment.python_version` as exact serialized audit context; neither value is rewritten to a coarse Python version.
- Required exactly three numeric Python version components for the portable comparison helper, so missing patch/minor data and nonnumeric identities fail closed instead of silently bypassing freshness.
- Did not change recursive comparison, schema, lockfile, Taskfile, source-origin policy, coverage validator, artifact evidence, slots registry, or performance contract.

## Verification

- RED: the same-minor test failed before production changes with `toolchain.python: expected "3.12.10", observed "3.12.3"`.
- GREEN: `uv run pytest tests/test_release_evidence.py -x -q -k "python and (toolchain or manifest or freshness)"` passed (9 tests); full `tests/test_release_evidence.py` passed (52 tests); Ruff format/check and `uv run mypy tools/release_evidence.py` passed.
- First clean archive: pure locked sync and immediate `verify-source` preflight passed before independent JUnit collection. The suite reported exactly 794 tests with zero failures, errors, and skips; `task release-baseline-write` recorded the same values.
- Baseline review: the generated diff changed only `quality_baseline.tests.collected` and `.passed` from 775 to 794. Coverage, exact Python 3.12.10, uv/package pins, source/artifact identity, slots inventory, registered exceptions, and performance fields were unchanged.
- Second clean archive: pure locked sync and immediate preflight passed; `task release-baseline-check` preserved manifest bytes; `task release-gate` passed Ruff, lint, mypy, 794 tests, strict Sphinx HTML, doctest, and read-only release evidence freshness.
- The developer checkout preflight correctly failed closed on its known `core.cpython-312-darwin.so` and `core__mypyc.cpython-312-darwin.so` shadows without deleting, moving, or certifying either file. Both authoritative proofs used clean archives instead.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Quality] Formatted the newly added RED contract tests before GREEN verification**
- **Found during:** Task 1 (GREEN verification)
- **Issue:** Ruff reported that the new test-only RED diff required formatting.
- **Fix:** Applied Ruff formatting and committed the mechanical test-only change separately so the source-only GREEN commit remained scoped.
- **Files modified:** `tests/test_release_evidence.py`
- **Verification:** Focused/full evidence tests, Ruff format/check, and mypy passed.
- **Committed in:** `30e61d6`

---

**Total deviations:** 1 auto-fixed (1 Rule 1).
**Impact on plan:** The correction is mechanical and preserves the requested RED test-only and GREEN source-only boundaries.

## Issues Encountered

The first clean-archive validation assertion initially used the wrong qualified-name module for `CompiledFuncCondition`. Inspection confirmed the existing registry is correctly `fast_fsm.core.CompiledFuncCondition`; the assertion was corrected and the generated manifest remained unchanged. No repository file was changed for this command-level validation fix.

## Known Stubs

None. The scan’s `default=[]` and `environment={}` matches are respectively a CLI argument default and deliberate empty-environment test input, not behavioral placeholders.

## Authentication Gates

None. This plan intentionally did not push, dispatch, or inspect a new hosted run.

## Next Phase Readiness

- `fast_fsm-bhn` remains **in progress** and `fast_fsm-6yg` remains **in progress**. Neither is closed by local evidence.
- Plan 15-05 must push the exact reviewed head, obtain a terminal GitHub Actions job table for that exact SHA, and close both beads only after every required job succeeds.
- The parent bead `fast_fsm-lw2` remains **in progress** for root orchestration and final phase verification.

## Self-Check: PASSED

All three scoped implementation/evidence files and this summary exist. Git history contains scoped RED, style, GREEN, and baseline commits `46dcde4`, `30e61d6`, `8aeedec`, and `e4d801a`; their file scopes were reviewed before this summary was written.

---
*Phase: 15-release-baseline-evidence-harness*
*Plan: 09*
*Completed: 2026-08-29*
