---
phase: 15-release-baseline-evidence-harness
plan: 03
subsystem: release-engineering
tags: [release-history, evidence, uv, pure-source, sphinx, pytest]
requires:
  - phase: 15-02
    provides: release evidence commands and pure-source preflight
  - phase: 15-06
    provides: scoped format repair required by the release gate
  - phase: 15-07
    provides: Sphinx-compatible core docstrings
provides:
  - Immutable v0.2.3 metadata correction and local history audit
  - Clean-archive pure-source evidence baseline with exact quality results
  - Maintainer procedure for release, history, and hosted-proof checks
affects: [phase-15-verification, release-publication, release-documentation]
actuals:
  tokens: 5356
  tasks: 2
  commits: 5
tech-stack:
  added: []
  patterns: [immutable-tag audit, clean archive pure-source evidence, baseline write before gate check]
key-files:
  created: [docs/release-corrections/v0.2.3.md, docs/dev/releasing.md]
  modified: [tools/release_evidence.py, tests/test_release_evidence.py, Taskfile.yml, CHANGELOG.md, docs/index.rst, evidence/release-baseline.json]
key-decisions:
  - "Treat v0.2.3 as immutable historical evidence: record its defective metadata additively rather than retagging or altering artifacts."
  - "Generate the authoritative manifest in a clean archive with pure mode set before its locked sync, then prove freshness from a second clean archive."
  - "Keep mypy as the blocking type-check authority; ty remains explicit advisory feedback."
patterns-established:
  - "Release evidence must preflight the pure Python source origin immediately after locked sync and before any quality gate."
  - "Write a regenerated evidence manifest before running the gate that checks its freshness."
requirements-completed: [REL-02, REL-05, REL-08, TEST-02]
coverage:
  - id: D1
    description: "Immutable v0.2.3 tag, historical metadata, changelog, and canonical correction audit"
    requirement: REL-02
    verification:
      - kind: unit
        ref: "tests/test_release_evidence.py#release_history"
        status: pass
      - kind: other
        ref: "task release-history-check"
        status: pass
    human_judgment: false
  - id: D2
    description: "Clean pure-source evidence baseline with recursive slot exception inventory"
    requirement: REL-05
    verification:
      - kind: e2e
        ref: "clean archive: FAST_FSM_BUILD_MODE=pure task release-gate"
        status: pass
      - kind: e2e
        ref: "second clean archive: FAST_FSM_BUILD_MODE=pure task release-baseline-check"
        status: pass
    human_judgment: false
  - id: D3
    description: "Release procedure indexed in strict Sphinx documentation with doctest coverage"
    requirement: TEST-02
    verification:
      - kind: other
        ref: "task docs-check && task docs-test"
        status: pass
    human_judgment: false
duration: 10 min
completed: 2026-08-29
status: complete
---

# Phase 15 Plan 03: Immutable History and Pure Baseline Summary

**Auditable v0.2.3 history correction, clean pure-source release evidence, and an operator runbook that preserves immutable published release identity.**

## Performance

- **Duration:** 10 min
- **Started:** 2026-08-29T20:40:05Z
- **Completed:** 2026-08-29T20:49:45Z
- **Tasks:** 2/2
- **Files modified:** 8
- **Evidence:** 775/775 pure tests passed; 95.75% total and 92.95% `core.py` source coverage; `uv 0.12.6`; `src/fast_fsm/core.py` origin.

## Accomplishments

- Added `verify-history` and `task release-history-check`, which prove the immutable `v0.2.3` target still contains `0.2.2` package metadata while checking the correction and dated changelog facts.
- Reorganized shipped history into dated v0.2.2 and v0.2.3 sections and supplied the canonical additive correction without adding the historical warning to the README.
- Regenerated the tracked evidence baseline from a clean archive after pure-mode locked sync and source-origin preflight, then confirmed it from a second clean archive.
- Added an indexed release runbook covering the exact gate order, recursive slot exceptions (`CompiledFuncCondition` and `TransitionError`), mypy/ty policy, native-shadow handling, hosted Python 3.10–3.14 proof, and immutable GitHub correction process.

## Task Commits

Each task was committed atomically:

1. **Task 1: Audit immutable v0.2.3 history and correction** - `d1ac4c2` (test), `a8b4a1c` (feat)
2. **Task 2: Create runbook and clean-checkout evidence baseline** - `515afe4` (docs), `eb1db0f` (docs)

## Files Created/Modified

- `tools/release_evidence.py` - Adds local immutable-history verification using safe argument-array Git commands.
- `tests/test_release_evidence.py` - Covers valid and invalid history/correction evidence.
- `Taskfile.yml` - Exposes the pure `release-history-check` command.
- `CHANGELOG.md` - Separates dated shipped v0.2.2 and v0.2.3 records.
- `docs/release-corrections/v0.2.3.md` - Provides the canonical additive correction paragraph.
- `docs/dev/releasing.md` and `docs/index.rst` - Publish the strict evidence and release procedure in the documentation tree.
- `evidence/release-baseline.json` - Captures the clean pure-source 775-test baseline and updated recursive slot locations.

## Decisions Made

- Kept the v0.2.3 tag and published artifacts unchanged; v0.3.0, not retrospective rewriting, carries corrected package metadata.
- Used a clean committed archive rather than a developer checkout, preserving unrelated files and ignored native artifacts while supplying an uncontaminated proof environment.
- Ran independent gates before `release-baseline-write`; only then ran `release-gate`, whose freshness check intentionally consumes the newly written manifest.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Accepted the canonical correction paragraph when Markdown wraps it across physical lines**
- **Found during:** Task 1 (immutable history audit)
- **Issue:** The verifier expected exact facts in one physical line, so `task release-history-check` rejected the valid wrapped Markdown paragraph.
- **Fix:** Normalized correction text whitespace before testing required historical facts and added a regression test.
- **Files modified:** `tools/release_evidence.py`, `tests/test_release_evidence.py`
- **Verification:** `uv run pytest tests/test_release_evidence.py -x -q` and `task release-history-check` passed.
- **Committed in:** `a8b4a1c`

**2. [Rule 3 - Blocking] Committed documentation before building the clean source archive**
- **Found during:** Task 2 (baseline generation)
- **Issue:** The release runbook and documentation index had to be part of the exact committed source surface that the clean archive verifies.
- **Fix:** Split Task 2 into a documentation commit followed by a manifest-only evidence commit.
- **Files modified:** `docs/dev/releasing.md`, `docs/index.rst`
- **Verification:** Strict Sphinx HTML and doctest builds passed in the clean archive.
- **Committed in:** `515afe4`

---

**Total deviations:** 2 auto-fixed (1 Rule 1, 1 Rule 3).
**Impact on plan:** Both changes preserved the plan’s scope and made the immutable-history and clean-commit contracts enforceable.

## Issues Encountered

The sandbox could not access uv's shared cache during the initial clean-archive sync. Re-running the exact command with the approved cache access succeeded; no dependency or source change was required.

## Known Stubs

None. The scan’s `default=[]` and `environment={}` matches are a CLI parser default and an explicit empty-environment test input, not rendering or behavioral placeholders.

## User Setup Required

None - no external service configuration required. The authenticated GitHub release correction and Actions proof remain the explicit scope of the later publication/audit plan.

## Next Phase Readiness

The committed manifest passes from a second clean archive and all local release gates. Plan 15-05 can use the canonical correction and immutable tag facts for its authenticated hosted audit without modifying the tag or published artifacts.

## Self-Check: PASSED

Verified all eight scoped deliverables and this summary exist; task commits `d1ac4c2`, `a8b4a1c`, `515afe4`, and `eb1db0f` are present in Git history.

---
*Phase: 15-release-baseline-evidence-harness*
*Completed: 2026-08-29*
