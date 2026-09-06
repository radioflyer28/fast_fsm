---
phase: 15-release-baseline-evidence-harness
plan: 04
subsystem: documentation
tags: [release-evidence, documentation, mypyc, slots-policy, sphinx]
requires:
  - phase: 15-02
    provides: Deterministic pure-source evidence commands and independent mypy/ty gates.
  - phase: 15-07
    provides: Sphinx-clean core docstrings whose source-line movements are included in the next clean baseline regeneration.
provides:
  - Durable README and contributor claims linked to generated release evidence.
  - Agent and sparse-memory policy for pure-source verification, type-check authority, and recursive slots auditing.
affects: [15-03, 15-05, release-evidence, contributor-workflow, agent-instructions]
actuals:
  tokens: 3015
  tasks: 2
  commits: 2
tech-stack:
  added: []
  patterns:
    - Keep exact volatile observations in evidence/release-baseline.json and state only durable contracts in prose.
    - Treat mypy as blocking and ty as separately visible advisory feedback.
    - Describe slots exceptions through the recursive measured registry rather than an inaccurate no-exceptions rule.
key-files:
  created:
    - .planning/phases/15-release-baseline-evidence-harness/15-04-SUMMARY.md
  modified:
    - README.md
    - docs/dev/testing.md
    - docs/dev/contributing.md
    - .github/copilot-instructions.md
    - .specify/memory/spr-core-api.md
key-decisions:
  - "Use 700+ tests and compiled trigger() ≥200,000 ops/sec as durable prose contracts; link exact observations to the tracked evidence manifest."
  - "Document CompiledFuncCondition and TransitionError as the two deliberate native_class=False registry entries with distinct runtime-boundary rationales."
  - "Leave the stale inventory-line evidence refresh to Plan 15-03, which owns the final clean baseline regeneration after Wave 3."
patterns-established:
  - "Evidence writers run an explicit pure-source preflight and review generated diffs; CI only runs the read-only freshness check."
  - "Dirty worktrees require explicitly scoped staging and commits."
requirements-completed: [REL-05, REL-08]
coverage:
  - id: D1
    description: Durable user and contributor evidence guidance replaces volatile test and benchmark prose with the manifest workflow.
    requirement: REL-05
    verification:
      - kind: integration
        ref: uv run pytest tests/test_readme_examples.py -x -q
        status: pass
      - kind: integration
        ref: uv run sphinx-build -b html docs docs/_build/html -W --keep-going
        status: pass
      - kind: integration
        ref: uv run sphinx-build -b doctest docs docs/_build/doctest
        status: pass
    human_judgment: false
  - id: D2
    description: Agent instructions and sparse API memory share the measured two-exception recursive slots policy and mypy/ty authority.
    requirement: REL-08
    verification:
      - kind: unit
        ref: uv run pytest tests/test_mypyc_guard.py tests/test_release_evidence.py -x -q -k "slots or mypyc"
        status: pass
      - kind: other
        ref: uv run python tools/release_evidence.py slots-policy --json
        status: pass
    human_judgment: false
duration: 5m
completed: 2026-08-29
status: complete
---

# Phase 15 Plan 04: Durable Evidence Documentation Summary

**Durable release-evidence, type-check, and measured slots-policy guidance across user docs, contributor docs, agent instructions, and sparse API memory.**

## Performance

- **Duration:** 5 min
- **Started:** 2026-08-29T20:28:00Z
- **Completed:** 2026-08-29T20:33:05Z
- **Tasks:** 2/2
- **Files modified:** 5

## Accomplishments

- Replaced stale test and benchmark headlines with the durable 700+ test claim, the compiled `trigger()` floor, and links to the exact generated evidence manifest.
- Documented clean pure-source evidence collection, explicit build-mode selection, legacy pure-mode compatibility, non-destructive native-shadow handling, and the write/check split.
- Aligned developer and agent policies on blocking mypy, advisory ty, scoped commits in dirty worktrees, and the recursive slots-policy audit.
- Named `CompiledFuncCondition` and `TransitionError` as the two measured `@mypyc_attr(native_class=False)` exceptions, with their distinct interpreted-condition and Python-exception rationales.

## Task Commits

1. **Task 1: Replace volatile user/developer claims with durable evidence links and commands**
   - `96826b7` — `docs(15-04): document durable release evidence`
2. **Task 2: Update the agent contract and sparse memory to the measured policy**
   - `812dd96` — `docs(15-04): align agent evidence policy`

## Files Created/Modified

- `README.md` — durable performance/test claims and a direct evidence-manifest path, with no release-correction warning.
- `docs/dev/testing.md` — canonical pure-source baseline, type-check, and slots-policy workflows.
- `docs/dev/contributing.md` — build-mode, preflight, mypy/ty, and measured-slots contributor policy.
- `.github/copilot-instructions.md` — operational contract for evidence freshness and scoped worktree commits.
- `.specify/memory/spr-core-api.md` — current sparse memory for the two registry exceptions and recursive audit command.

## Decisions Made

- Kept changing observations out of narrative documentation and linked the authoritative generated manifest instead.
- Preserved the stable compiled `trigger()` floor while removing unportable benchmark tables and historical exact test totals.
- Treated the two `native_class=False` classes as deliberate measured boundaries under ADR-003, not as a general relaxation of slots policy.

## Deviations from Plan

None - the documentation and policy work executed as specified.

## Issues Encountered

- The shared checkout's source preflight correctly failed closed on pre-existing native `core` shadows and did not delete them.
- In a clean disposable archive, `task release-baseline-check` reached the manifest comparison but reported the slots inventory stale because Plan 15-07's documentation-only `core.py` edits moved AST line numbers. Per the Phase 15 orchestration decision, Plan 15-03 owns the required clean baseline regeneration after Wave 3. This is not a Plan 15-04 scope expansion or a future-contract blocker.

## Verification

- `uv run pytest tests/test_readme_examples.py -x -q` — passed (10 tests).
- `uv run pytest tests/test_mypyc_guard.py tests/test_release_evidence.py -x -q -k "slots or mypyc"` — passed (7 tests).
- `uv run python tools/release_evidence.py slots-policy --json` — passed; recursively discovered the inventory and measured both registered exceptions.
- `uv run sphinx-build -b html docs docs/_build/html -W --keep-going` — passed.
- `uv run sphinx-build -b doctest docs docs/_build/doctest` — passed (1 test, 0 failures).
- `task release-baseline-check` — shared checkout correctly failed its non-destructive native-shadow preflight; a clean disposable archive reached freshness comparison and reported the expected Plan 15-03 inventory-line refresh requirement.

## Known Stubs

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 15-03 can regenerate the final clean release baseline after all Wave 3 source/doc changes are present.
- The parent Phase 15 orchestrator retains ownership of shared STATE/ROADMAP updates and the open phase bead.

## Self-Check

PASSED — the summary exists, both task commits (`96826b7`, `812dd96`) are in
Git history, the summary has no whitespace errors, and no stub-pattern matches
were found in this plan artifact.

---
*Phase: 15-release-baseline-evidence-harness*
*Plan: 04*
*Completed: 2026-08-29*
