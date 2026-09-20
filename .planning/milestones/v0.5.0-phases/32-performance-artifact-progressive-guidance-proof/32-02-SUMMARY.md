---
phase: 32-performance-artifact-progressive-guidance-proof
plan: 02
subsystem: release-evidence
tags: [artifacts, conformance, provenance, coverage, release-evidence]
requires:
  - phase: 32-01
    provides: strict conformance oracle and source/native artifact contract
  - phase: 32-03
    provides: finality and transition-mode conformance rows
  - phase: 32-05
    provides: expected-rejection conformance row
provides:
  - exact-origin strict-oracle parity coverage for fresh native and installed artifacts
  - fail-closed, narrowly guarded release-baseline refreshes
  - refreshed local, non-authorizing release evidence
affects: [release verification, artifact conformance, performance evidence]
actuals:
  tokens: 12000
  tasks: 2
  commits: 13
tech-stack:
  added: []
  patterns:
    - disposable artifact children scrub parent pytest-cov controls
    - baseline writes compare regenerated canonical facts and remove only explicit refresh paths
key-files:
  created: []
  modified:
    - tests/test_installed_artifacts.py
    - tests/test_release_evidence.py
    - tools/release_evidence.py
    - evidence/release-baseline.json
key-decisions:
  - "Fresh native evidence is built in an isolated copy, with extension shadows moved only to a recoverable constrained backup before pure-source restoration."
  - "The baseline writer permits only regenerated Phase 32 conformance/slots facts and a non-decreasing core coverage floor; all other stable fields remain immutable."
requirements-completed: [PERF-04]
coverage:
  - id: D1
    description: "Fresh native, pure-wheel, compiled-wheel, and local release-intent artifacts prove exact origin/build mode before matching the strict conformance oracle."
    requirement: PERF-04
    verification:
      - kind: integration
        ref: "tests/test_installed_artifacts.py"
        status: pass
      - kind: other
        ref: "task release-installed-artifacts-check"
        status: pass
    human_judgment: false
  - id: D2
    description: "The release baseline refresh is constrained, reviewed, and remains fresh under read-only validation."
    requirement: PERF-04
    verification:
      - kind: unit
        ref: "tests/test_release_evidence.py -k 'phase32_guarded_refresh or guarded_release_baseline'"
        status: pass
      - kind: other
        ref: "task release-baseline-check"
        status: pass
    human_judgment: false
  - id: D3
    description: "A local release candidate retains explicit non-authorizing scope and the installed compiled performance floor."
    requirement: PERF-04
    verification:
      - kind: other
        ref: "task release-evidence-local-check"
        status: pass
      - kind: other
        ref: "task release-installed-performance-check"
        status: pass
    human_judgment: false
metrics:
  duration: "4h 30m"
  completed: 2026-09-19
status: complete
---

# Phase 32 Plan 02: Performance Artifact Progressive Guidance Proof Summary

**Fresh native and installed artifacts now prove exact provenance before matching the strict semantic oracle, with a guarded, read-only-verified local evidence baseline.**

## Performance

- **Tasks:** 2/2 complete
- **Files modified:** 4 implementation/test/evidence files, plus plan record and summary
- **Installed compiled performance:** 619,518 median ops/s; the fixed 200,000 ops/s floor passed.
- **Baseline source coverage:** 97.05% core and 97.81% total.

## Accomplishments

- Added a fresh, isolated native-core probe to the clean-source/pure-wheel/compiled-wheel parity matrix. It validates extension origin and loader, temporarily moves only local native shadows to a recoverable constrained backup, and restores pure source afterward.
- Added origin contradiction, shadow, local-scope, malformed coverage-child, and baseline-refresh regressions that fail closed without changing protected baseline bytes.
- Refreshed `evidence/release-baseline.json` only after reviewing its 123-addition/38-deletion diff: regenerated Phase 32 semantic facts, slots inventory, test counts, toolchain value, performance observation, and a strengthened core coverage floor from 97.01% to 97.05%.
- Confirmed local release evidence remains `local-non-authorizing` with `authorizes_release=false`; no tag, hosted Release, or PyPI publication was created.

## Task Commits

1. **Task 1: Assert the same strict oracle in all fresh local runtime modes** - `767d4c1`, `46d96fb`, `6f822ac`, `8260929`, `451afd6`, `68c5b70`, `b844d33`, `bd40d2c`, `3d455bf`, `a811d82`.
2. **Task 2: Refresh and enforce the reviewed release baseline** - `ece2c25`, `3886671`, `8608364`.

## Files Created/Modified

- `tests/test_installed_artifacts.py` - exact-origin fresh native parity and isolated coverage-child regressions.
- `tests/test_release_evidence.py` - fail-closed canonical refresh, core-coverage improvement, regression, and immutable-path tests.
- `tools/release_evidence.py` - canonical Phase 32 evidence validation plus numeric, non-decreasing core coverage validation.
- `evidence/release-baseline.json` - reviewed source evidence, test inventory, slots inventory, and performance observations.

## Decisions Made

- Preserve the current `add_transition`/artifact semantics; test all supported local modes against one fixed oracle rather than duplicating behavior rules per build mode.
- Treat pytest-cov controls as parent-only process state. Disposable build/probe children remove those controls so child coverage fragments cannot corrupt the parent evidence run.
- Permit a baseline core-coverage increase only when it is numeric and never below the prior protected value. The writer still rejects total-coverage movement, lower coverage, and all unrelated stable/raw changes.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Coverage process isolation] Disposable artifact subprocesses inherited pytest-cov controls.**
- **Found during:** Task 1
- **Issue:** Child Python processes could create incompatible coverage fragments during the parent release-evidence collection.
- **Fix:** Scrub coverage-control variables from disposable source/native/wheel build and probe environments; add focused tests for the isolation behavior.
- **Files modified:** `tests/test_installed_artifacts.py`
- **Verification:** Full baseline collection completed with 97.05% core coverage and read-only validation passed.
- **Committed in:** `6f822ac`, `bd40d2c`

**2. [Rule 3 - Guarded source-fact refresh] The older writer could not recognize the newly reviewed semantic and slots evidence.**
- **Found during:** Task 2
- **Issue:** A legitimate Phase 32 source-evidence refresh would be rejected before its explicit canonical facts could be checked.
- **Fix:** Added a narrow canonical conformance/slots allowlist and fail-closed tests; amended the plan's execution deviation to record this authority.
- **Files modified:** `tools/release_evidence.py`, `tests/test_release_evidence.py`, `32-02-PLAN.md`
- **Verification:** Canonical values pass; altered digest/inventory values retain baseline bytes and fail.
- **Committed in:** `451afd6`, `8260929`

**3. [Approved narrow coverage-floor strengthening] The refreshed collection improved core coverage from 97.01% to 97.05%.**
- **Found during:** Task 2
- **Issue:** The original stable-path rule rejected any coverage change, including a proven improvement.
- **Fix:** Permit only a numeric, non-decreasing `quality_baseline.coverage.core_percent`; lower values and unrelated stable paths are still rejected.
- **Files modified:** `tools/release_evidence.py`, `tests/test_release_evidence.py`, `32-02-PLAN.md`
- **Verification:** Focused guard tests, baseline write, and subsequent read-only check passed.
- **Committed in:** `ece2c25`, `3886671`, `8608364`

**Total deviations:** 2 auto-fixed (Rule 1 and Rule 3), plus one explicitly approved narrow coverage-floor strengthening.

## Verification

- PASS — `uv run pytest tests/test_installed_artifacts.py -x -q` (28 passed)
- PASS — `task release-installed-artifacts-check`
- PASS — `task release-installed-performance-check` (619,518 median ops/s)
- PASS — `task release-evidence-local-check` (`local-non-authorizing`, `authorizes_release=false`)
- PASS — `task release-baseline-check` (2206/2212 pure tests; core 97.05%, total 97.81%)
- PASS — `uv run pytest tests/test_competitor_benchmark_contract.py -x -q` (28 passed)
- PASS — `task typecheck-mypy`
- ADVISORY FAILURE — `task typecheck-ty` cannot resolve existing relative imports `._construction_compat` and `.conditions` in `src/fast_fsm/core.py`; no Plan 02 source behavior was altered to mask that separate checker limitation.

## Next Phase Readiness

Artifact parity, local evidence, and performance proof are complete for this plan. The recorded evidence is explicitly local and non-authorizing; hosted release/tag/PyPI authorization remains outside this plan.

## Self-Check: PASSED

- Required implementation/test/evidence files exist and task commits `767d4c1`, `46d96fb`, `6f822ac`, `8260929`, `451afd6`, `68c5b70`, `b844d33`, `bd40d2c`, `3d455bf`, `a811d82`, `ece2c25`, `3886671`, and `8608364` exist in Git history.
