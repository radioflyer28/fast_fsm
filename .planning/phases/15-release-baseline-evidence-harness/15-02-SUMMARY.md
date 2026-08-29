---
phase: 15-release-baseline-evidence-harness
plan: 02
subsystem: release-tooling
tags: [uv, release-evidence, github-actions, coverage, mypy, mypyc]
requires:
  - phase: 15-01
    provides: source-origin, wheel-inspection, and slots-policy evidence primitives
provides:
  - deterministic schema-v1 release baseline with explicit write/check modes
  - exact locked release-build provenance and hermetic supported-Python sdist proof
  - independently visible CI/release quality categories with mypy blocking and ty advisory
affects: [phase-15-release-baseline-evidence-harness, phase-20-universal-wheel-publication, release-ci]
actuals:
  tokens: 20350
  tasks: 3
  commits: 15
tech-stack:
  added: []
  patterns:
    - "Canonical standard-library evidence collector with deterministic JSON comparison"
    - "Pure source preflight immediately follows locked environment synchronization"
    - "PEP 517 proof uses an isolated backend constrained to reviewed exact pins"
key-files:
  created:
    - evidence/release-baseline.json
  modified:
    - tools/release_evidence.py
    - tests/test_release_evidence.py
    - tests/test_build_modes.py
    - pyproject.toml
    - uv.lock
    - Taskfile.yml
    - .github/workflows/ci.yml
    - .github/workflows/docs.yml
    - .github/workflows/release.yml
key-decisions:
  - "Use only evidence --write for intentional manifest regeneration; CI's --check path is read-only."
  - "Resolve exact PEP 517 build provenance from uv.lock and constrain isolated builds rather than exposing build tools as runtime dependencies."
  - "Keep mypy authoritative and blocking while leaving ty separately visible and advisory."
  - "Keep universal pure wheels as temporary evidence only; Phase 20 remains responsible for publication."
patterns-established:
  - "Every clean evidence job establishes FAST_FSM_BUILD_MODE=pure before sync and runs source-origin preflight immediately after."
  - "Each quality category gets an independently named CI job rather than an opaque aggregate shell chain."
requirements-completed: [REL-04, REL-05, REL-06, REL-08, TEST-02]
coverage:
  - id: D1
    description: "Schema-v1 manifest records deterministic source, test, coverage, wheel, slots, and toolchain evidence."
    requirement: REL-04
    verification:
      - kind: unit
        ref: "tests/test_release_evidence.py"
        status: pass
      - kind: integration
        ref: "task release-baseline-check"
        status: pass
    human_judgment: false
  - id: D2
    description: "Exact locked build inputs and isolated pure sdist-to-wheel builds work on every supported locally installed Python."
    requirement: REL-06
    verification:
      - kind: integration
        ref: "uv lock --check"
        status: pass
      - kind: integration
        ref: "task supported-python-build-matrix-local (CPython 3.10, 3.11, 3.12, 3.13, 3.14)"
        status: pass
    human_judgment: false
  - id: D3
    description: "CI and release workflows expose independent quality categories, use uv 0.12.6, and retain pure-wheel non-publication."
    requirement: REL-08
    verification:
      - kind: unit
        ref: "tests/test_release_evidence.py -k 'workflow_contract or setup_uv or supported_python'"
        status: pass
      - kind: other
        ref: "PyYAML parse of ci.yml, docs.yml, and release.yml"
        status: pass
    human_judgment: false
  - id: D4
    description: "Mypy is a blocking local gate and ty is independently callable advisory feedback."
    requirement: TEST-02
    verification:
      - kind: integration
        ref: "task typecheck-mypy"
        status: pass
      - kind: integration
        ref: "task typecheck-ty"
        status: pass
    human_judgment: false
  - id: D5
    description: "The aggregate release gate reports every blocking category without concealing failures."
    requirement: REL-05
    verification:
      - kind: integration
        ref: "task release-gate"
        status: unknown
    human_judgment: true
    rationale: "The aggregate gate is intentionally pending Phase 15-06's Ruff fixes and a scoped REL-05 documentation gap fix; focused 15-02 evidence and matrix checks are green."
duration: 29m
completed: 2026-08-29
status: complete
---

# Phase 15 Plan 02: Deterministic Baseline and Visible Gates Summary

**Deterministic pure-source release evidence with exact uv/build provenance, independent CI categories, and a hermetic five-version sdist-to-wheel proof.**

## Performance

- **Duration:** 29m
- **Started:** 2026-08-29T19:18:43Z
- **Completed:** 2026-08-29T19:48:10Z
- **Tasks:** 3/3
- **Files modified:** 10

## Accomplishments

- Added a schema-versioned, standard-library evidence collector that writes only on explicit request, reports stable-field diffs, records test/coverage/source-origin/toolchain/slot and multi-wheel facts, and requires uv 0.12.6.
- Pinned release-producing build tools in `pyproject.toml` and `uv.lock`, added pure-mode local evidence commands, and checked the resulting baseline in a disposable locked worktree.
- Reworked CI, docs, and release workflows into independent gates with a reusable release prerequisite, exact setup-uv provenance, pure preflight ordering, and a Python 3.10–3.14 sdist/unpacked-wheel matrix.

## Task Commits

1. **Task 1: Add deterministic manifest logic and pin its release-producing toolchain**
   - `0d941eb` test: failing manifest evidence coverage
   - `0021409` feat: deterministic release evidence collector
   - `9c3f4f9` test: evidence write and freshness coverage
   - `ade82fa` feat: read-only manifest freshness
   - `5477f24` fix: locked isolated build-tool provenance
   - `7fc0998` test: locked release build provenance
   - `b5a3c5e` fix: exact release build toolchain
2. **Task 2: Generate the tracked clean baseline and expose canonical local gate commands**
   - `aeb7ca1` feat: release-baseline task commands
   - `4e21b52` chore: initial evidence baseline
   - `289427a` fix: advisory ty outside local aggregate gate
   - `7f7e548` fix: exact constrained isolated supported-Python build proof
   - `508f23c` fix: regenerate the locked pure coverage baseline
3. **Task 3: Make every required PR and release failure category independently visible**
   - `1107c87` test: failing CI workflow contracts
   - `c7b5416` feat: independent release quality gates

## Files Created/Modified

- `tools/release_evidence.py` — deterministic evidence CLI, stable comparison, coverage regression protection, and lock-derived provenance.
- `tests/test_release_evidence.py` — TDD coverage for manifest semantics and workflow contracts.
- `tests/test_build_modes.py` — hermetic isolated pure sdist rebuild proof constrained to the exact reviewed toolchain.
- `evidence/release-baseline.json` — authoritative schema-v1 pure-source baseline.
- `pyproject.toml` and `uv.lock` — exact reviewed PEP 517 build-tool pins.
- `Taskfile.yml` — named local baseline, source, typecheck, and supported-Python commands.
- `.github/workflows/ci.yml`, `.github/workflows/docs.yml`, `.github/workflows/release.yml` — independent pure-mode PR/release gates with uv 0.12.6 provenance.

## Decisions Made

- Chose deterministic JSON with sorted keys and a final newline; measurements that legitimately vary by host remain labeled context rather than stable comparison inputs.
- Kept build dependencies out of runtime requirements: their resolved versions come from `uv.lock`, and the isolated sdist proof receives exact temporary build constraints.
- Kept ty visible and callable but excluded it from the local blocking aggregate, matching the advisory CI job.
- Did not upload or publish a universal pure wheel; generated wheels are temporary local evidence only.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Resolved PEP 517 build-tool provenance from the reviewed lock.**
- **Found during:** Task 1 and Task 2.
- **Issue:** `setuptools`, `wheel`, and `mypy[mypyc]` are isolated build requirements and cannot reliably be queried as installed runtime distributions.
- **Fix:** Added exact release dependency-group/pin provenance and a lock parser that reads the reviewed resolved versions without adding runtime dependencies.
- **Files modified:** `tools/release_evidence.py`, `pyproject.toml`, `uv.lock`.
- **Verification:** `uv lock --check`, focused evidence tests, and clean `task release-baseline-check` passed.
- **Committed in:** `5477f24`, `7fc0998`, `b5a3c5e`.

**2. [Rule 1 - Bug] Kept ty advisory outside the local aggregate verdict.**
- **Found during:** Task 2.
- **Issue:** The initial aggregate command would make an advisory ty failure block the local release verdict, contradicting the required CI authority split.
- **Fix:** Retained `task typecheck-ty` as an independently callable command and removed it from `task release-gate`; CI records ty with job-level `continue-on-error`.
- **Files modified:** `Taskfile.yml`.
- **Verification:** `task typecheck-mypy` and `task typecheck-ty` both passed independently.
- **Committed in:** `289427a`.

**3. [Rule 1 - Bug; authorized scope expansion] Replaced a non-isolated sdist rebuild with exact constrained PEP 517 isolation.**
- **Found during:** Task 2 supported-Python matrix.
- **Issue:** The prior `uv build --no-build-isolation` invocation could not import `setuptools` in uv's build backend on CPython 3.10, weakening the intended isolated proof.
- **Fix:** Added temporary exact `--build-constraints` for setuptools 80.9.0, wheel 0.45.1, and mypy[mypyc] 1.17.1 to both the sdist and unpacked-wheel build steps. The proof remains isolated and runs no install outside uv.
- **Files modified:** `tests/test_build_modes.py`.
- **Verification:** The focused test and `task supported-python-build-matrix-local` passed on locally available CPython 3.10, 3.11, 3.12, 3.13, and 3.14.
- **Committed in:** `7f7e548`.

**4. [Rule 1 - Bug] Regenerated an incorrect initial total-coverage baseline from a clean locked worktree.**
- **Found during:** final Task 2 baseline freshness validation.
- **Issue:** The initial tracked evidence recorded total coverage as 47.88%, while a clean locked pure-source collector run deterministically measured 95.75% with the same core coverage (92.95%).
- **Fix:** Regenerated only the tracked baseline value in a disposable clean worktree and confirmed the read-only check passes at 95.75%.
- **Files modified:** `evidence/release-baseline.json`.
- **Verification:** clean `task release-baseline-check` passed with 770/770 tests.
- **Committed in:** `508f23c`.

**Total deviations:** 4 auto-fixed Rule 1 corrections.

## Issues Encountered

- `task release-gate` correctly stops at a known Phase 15-06 Ruff format blocker in `src/fast_fsm/visualization.py`; it was not modified by this plan.
- Independent `task lint` reports the Phase 15-06 Ruff F841 blocker at `tests/test_advanced_functionality.py:1488` (unused `fsm`); it was not modified by this plan.
- `task docs-check` is a REL-05 gap requiring a separate documentation-only follow-up: Sphinx `-W --keep-going` reports nine docstring warnings/errors in `src/fast_fsm/core.py`, including an unexpected indentation for `condition_builder`. The full remediation remains outside 15-02; no source docstrings were changed here.

## Known Stubs

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- The deterministic evidence harness, exact build provenance, and CI structure are ready for the remaining Phase 15 plans and for a post-push matrix run.
- Authoritative aggregate baseline collection remains pending the scoped Phase 15-06 Ruff cleanup and the REL-05 documentation gate fix above. The phase bead `fast_fsm-lw2` remains open and in progress.

## Self-Check

PASSED — all ten implementation artifacts and this summary exist; all fourteen task commits are present in Git history. Stub-pattern scan found only the intentional repeatable-argument default (`default=[]`) and no product stubs.

---
*Phase: 15-release-baseline-evidence-harness*
*Completed: 2026-08-29*
