---
phase: 15-release-baseline-evidence-harness
plan: 08
subsystem: ci
tags: [github-actions, task, yaml, supply-chain, release-gate]
requires:
  - phase: 15-03
    provides: clean-archive pure-source release-gate proof pattern
provides:
  - Pinned Task 3.53.1 provisioning before every Taskfile-consuming CI job
  - YAML-structural mutation coverage for Task runner discovery, pins, and ordering
  - Local clean-archive proof ready for Plan 15-05's exact-SHA remote rerun
affects: [plan-15-05, github-actions, release-gate, rel-05, rel-06]
actuals:
  tokens: 7325
  tasks: 1
  commits: 6
tech-stack:
  added: []
  patterns:
    - "Use YAML structure to discover CI command consumers; reserve raw text only for adjacent provenance comments."
    - "Prove pure-source gates in a clean committed archive when local native shadows are deliberately preserved."
key-files:
  created:
    - .planning/phases/15-release-baseline-evidence-harness/15-08-SUMMARY.md
  modified:
    - tests/test_release_evidence.py
    - .github/workflows/ci.yml
    - .beads/issues.jsonl
key-decisions:
  - "Pin arduino/setup-task at c0bc642852239c2689f73f4ea6459c29405f3c52 with the adjacent v3.0.0 provenance comment and Task version 3.53.1."
  - "Keep fast_fsm-6yg open until Plan 15-05 records terminal exact-SHA GitHub Actions success."
patterns-established:
  - "Task runner setup must immediately follow setup-uv and precede every Taskfile command in the same parsed CI job."
requirements-completed: [REL-05, REL-06]
coverage:
  - id: D1
    description: "Every current Taskfile-consuming CI job has a structurally verified, exact, ordered Task bootstrap."
    requirement: REL-05
    verification:
      - kind: unit
        ref: "uv run pytest tests/test_release_evidence.py -x -q -k task_runner"
        status: pass
      - kind: other
        ref: "YAML parser and mutation-backed Task runner contract"
        status: pass
    human_judgment: false
  - id: D2
    description: "The locally committed CI repair preserves the release evidence contract in an uncontaminated pure-source environment."
    requirement: REL-06
    verification:
      - kind: e2e
        ref: "clean committed archive: FAST_FSM_BUILD_MODE=pure task release-gate"
        status: pass
    human_judgment: false
duration: 9m
completed: 2026-08-29
status: complete
---

# Phase 15 Plan 08: Pinned Task Runner CI Repair Summary

**A structural CI contract and exact action pin make all nine independent Taskfile-based GitHub Actions gates executable on their existing operating-system and Python matrices.**

## Performance

- **Duration:** 9m
- **Started:** 2026-08-29T21:12:34Z
- **Completed:** 2026-08-29T21:21:29Z
- **Tasks:** 1/1
- **Files modified:** 4

## Accomplishments

- Added `arduino/setup-task@c0bc642852239c2689f73f4ea6459c29405f3c52 # v3.0.0` with exact `version: "3.53.1"` immediately after `astral-sh/setup-uv@v5` in `format`, `lint`, `typecheck_mypy`, `typecheck_ty`, `test`, `supported_python_build`, `evidence`, `docs_html`, and `docs_doctest`.
- Added YAML-structural tests that inspect every parsed job/step/run scalar, detect plain, block-scalar, multiline, and environment-prefixed `task` execution, and reject missing, late, floating, wrong-version, or unaccounted setup.
- Proved the final committed source in a clean pure-source archive: Ruff, lint, mypy, 775 tests, strict Sphinx HTML/doctest, and evidence freshness all passed without modifying the developer checkout's native artifacts.

## Task Commits

1. **RED: add failing structural Task-runner contract** — `6ee004f` (`test`)
2. **Correct the named-step source-comment matcher and mutation fixture** — `154fe05` (`fix`)
3. **Format the new contract test** — `061db16` (`style`)
4. **GREEN: provision pinned Task runner in CI** — `9f54cad` (`fix`)
5. **Require immediate setup-uv adjacency as well as invocation ordering** — `5dc1191` (`test`)

**Plan metadata and bead tracking:** recorded in the follow-up summary commit.

## Files Created/Modified

- `tests/test_release_evidence.py` — YAML traversal, shell-form detection, exact pin/comment checks, setup ordering, and negative mutations.
- `.github/workflows/ci.yml` — nine identical cross-platform Task runner setup steps; no matrix, uv, pure-mode, preflight, compiled-smoke, or benchmark command changed.
- `.beads/issues.jsonl` — `fast_fsm-6yg` claimed and kept in progress for the remote proof handoff.
- `.planning/phases/15-release-baseline-evidence-harness/15-08-SUMMARY.md` — RED/GREEN evidence and Plan 15-05 handoff.

## Verification

- RED: `uv run pytest tests/test_release_evidence.py -x -q -k task_runner` failed as required with `format: missing pinned Task setup` before `.github/workflows/ci.yml` changed.
- GREEN: `uv run pytest tests/test_release_evidence.py -x -q -k "task_runner or workflow_contract or setup_uv or supported_python"` passed (9 tests).
- `uv run python -c '<yaml.safe_load ci.yml assertion>'` passed and reported 11 CI jobs.
- The exact full-SHA action plus `# v3.0.0` provenance comment appears exactly nine times; commit `9f54cad` contains only `.github/workflows/ci.yml` and inserts 36 lines.
- `uv run pytest tests/test_release_evidence.py -x -q` passed (40 tests).
- The non-destructive in-place pure-source preflight correctly failed before import on the two deliberate native shadows in `src/fast_fsm/`; it did not remove or relocate either artifact.
- In a fresh clean archive of final commit `5dc1191`, `FAST_FSM_BUILD_MODE=pure uv sync --locked --all-groups`, source-origin preflight, and `FAST_FSM_BUILD_MODE=pure task release-gate` all passed. The gate included Ruff, lint, mypy, 775 tests, strict Sphinx HTML, doctest, and release-baseline freshness.
- The final focused contract, workflow parse, native-shadow existence, commit-scope, and whitespace checks passed.

## Decisions Made

- Used the official cross-platform Task setup action at a full immutable commit SHA instead of a tag, installer script, package-manager branch, or checked-in binary.
- Enforced setup immediately after uv provisioning and before each Task command, preventing both order drift and accidental job additions from silently failing with exit 127.
- Kept remote evidence distinct: local proof establishes the repair, while GitHub Actions for the exact pushed SHA remains the authority for the hosted result.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Test harness] Corrected the source-comment matcher for named action steps.**
- **Found during:** Task 1 GREEN verification.
- **Issue:** The initial source-comment regex expected a shorthand `- uses:` step, while the valid workflow uses a named step followed by `uses:`.
- **Fix:** Matched the indented `uses:` line directly while retaining the adjacent full-SHA and `# v3.0.0` contract.
- **Files modified:** `tests/test_release_evidence.py`.
- **Verification:** Focused structural suite passed.
- **Committed in:** `154fe05`.

**2. [Rule 1 - Test harness] Kept mutation fixtures valid after the real workflow gained setup steps.**
- **Found during:** Task 1 GREEN verification.
- **Issue:** The synthetic fixture inserted a second setup action when run against the corrected workflow, masking the intended late-setup mutation.
- **Fix:** Remove any existing Task setup from the deep-copied fixture before inserting one canonical setup step.
- **Files modified:** `tests/test_release_evidence.py`.
- **Verification:** Missing, late, wrong-SHA, wrong-version, and invocation-form mutations pass with their intended failure reason.
- **Committed in:** `154fe05`.

**3. [Rule 1 - Quality] Applied required Ruff formatting only to the new contract test.**
- **Found during:** First clean-archive release gate.
- **Issue:** `ruff format --check` reported the newly added test file would be reformatted.
- **Fix:** Ran Ruff formatting and lint only on `tests/test_release_evidence.py`.
- **Files modified:** `tests/test_release_evidence.py`.
- **Verification:** Final clean-archive release gate passed.
- **Committed in:** `061db16`.

**4. [Rule 2 - Missing critical] Made the task setup's required adjacency to uv setup executable.**
- **Found during:** Final contract review.
- **Issue:** The initial structural contract required setup before `task` but did not prove the plan's required immediate placement after `setup-uv`.
- **Fix:** Added an exact same-job adjacency assertion and a late-setup mutation expectation.
- **Files modified:** `tests/test_release_evidence.py`.
- **Verification:** Focused structural suite and final clean-archive release gate passed.
- **Committed in:** `5dc1191`.

---

**Total deviations:** 4 auto-fixed (3 Rule 1, 1 Rule 2).
**Impact on plan:** The corrections strengthen the requested supply-chain and ordering guarantees without expanding CI behavior or changing application code.

## Issues Encountered

- The developer checkout intentionally contains `core.cpython-312-darwin.so` and `core__mypyc.cpython-312-darwin.so`. Its pure-source preflight failed closed and reported both paths without deleting or relocating them. All pure-source and release-gate proof therefore ran in fresh clean committed archives, as required by the phase's non-destructive policy.

## Authentication Gates

None. This plan intentionally did not push or dispatch the corrective hosted run.

## User Setup Required

None - no new external service configuration is required for the local repair.

## Next Phase Readiness

- `fast_fsm-6yg` remains **in progress**. Plan 15-05 must push the corrective branch, watch the GitHub Actions run for its exact head SHA, record every job conclusion, and close this bead only after terminal success.
- Parent Phase 15 bead `fast_fsm-lw2` remains **in progress** for the root verifier.
- Plan 15-05 must not treat this local clean-archive evidence as a substitute for hosted exact-SHA proof.

## Self-Check

PASSED — summary exists; each RED/fix/style/contract commit contains only `tests/test_release_evidence.py`; the GREEN commit `9f54cad` contains only the 36 inserted workflow setup lines; and the scoped diff whitespace check passed.

---
*Phase: 15-release-baseline-evidence-harness*
*Plan: 08*
*Completed: 2026-08-29*
