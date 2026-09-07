---
phase: 24-candidate-aware-diagnostics-output
plan: 03
subsystem: diagnostic parity and maintainer contract
tags: [python, mypyc, diagnostics, validation, visualization, priority]
requires:
  - phase: 24-candidate-aware-diagnostics-output
    provides: candidate-complete scalar edges, strict-priority validation, and priority-bearing output sinks
  - phase: 23-construction-declarative-serialization-parity
    provides: frozen candidate-complete core snapshots
provides:
  - pure/native structural and real-machine candidate diagnostic parity coverage
  - documented immutable projection, conservative shadowing, priority-complete outputs, and bounded diagnostic contract
affects: [25-artifacts-performance-and-guidance, diagnostics, mypyc, validation, visualization]
actuals:
  tokens: 3810
  tasks: 2
  commits: 3
tech-stack:
  added: []
  patterns:
    - one mode-invariant real-machine oracle spans candidate diagnostics and preserves caller callback data
    - generated native extensions are moved recoverably before pure-source proof
key-files:
  created:
    - .planning/phases/24-candidate-aware-diagnostics-output/24-03-SUMMARY.md
  modified:
    - tests/test_mypyc_guard.py
    - .specify/memory/spr-core-api.md
key-decisions:
  - "Compiled parity is proven with real public results and static source assertions, not private-method monkeypatching."
  - "The living SPR records candidate semantics without widening the runtime, public documentation, or Phase 25 scope."
patterns-established:
  - "Candidate diagnostics preserve one snapshot-derived scalar row through validation, paths, adjacency, JSON, diagrams, and Markdown."
  - "Pure-source gates run before and after a fresh compiled build whose in-place shadows are recoverably relocated."
requirements-completed: [DIAG-01, DIAG-02]
coverage:
  - id: D1
    description: "Frozen/slotted candidate records, cold projection boundaries, and no-user-code validation remain equivalent under pure and freshly compiled core."
    requirement: DIAG-01
    verification:
      - kind: integration
        ref: "tests/test_mypyc_guard.py::test_phase24_diagnostic_projection_stays_scalar_and_cold"
        status: pass
      - kind: integration
        ref: "tests/test_mypyc_guard.py::test_phase24_candidate_diagnostic_oracle_is_mode_invariant"
        status: pass
    human_judgment: false
  - id: D2
    description: "Candidate multiplicity and numeric priority remain visible in validation, adjacency, paths, JSON, diagrams, and Markdown with explicit budget exhaustion."
    requirement: DIAG-02
    verification:
      - kind: integration
        ref: "tests/test_mypyc_guard.py::test_phase24_candidate_diagnostic_oracle_is_mode_invariant"
        status: pass
      - kind: integration
        ref: "FAST_FSM_BUILD_MODE=compiled focused Phase 24 diagnostics suite"
        status: pass
    human_judgment: false
duration: 1h 10m
completed: 2026-09-07
status: complete
---

# Phase 24 Plan 03: Native Diagnostic Parity Summary

**Candidate-aware diagnostics now have one real-machine oracle proving identical pure and freshly compiled behavior from immutable snapshot facts through bounded outputs.**

## Performance

- **Duration:** 1h 10m
- **Started:** 2026-09-07T03:24:00Z
- **Completed:** 2026-09-07T04:34:04Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Locked frozen/slotted `_GraphTransition` and interpreted `_DiagnosticEdge` layouts, cold projection ordering, no diagnostics import in core, and no guard or permission evaluation in determinism analysis.
- Added a pure/native mode-invariant real-machine oracle covering same-target candidates, strict priorities, proved/possible shadows, adjacency, paths, JSON, Mermaid, PlantUML, Markdown, explicit budget exhaustion, callbacks, and history priority.
- Updated maintainer memory with the one-snapshot scalar projection, exact-base static evidence, candidate-complete output shapes, and candidate-level budget behavior.

## Task Commits

1. **Task 1: Prove structural and semantic parity across pure and compiled core** — `ba694b7` (stale layout guard correction), `1a52cf2` (parity oracle)
2. **Task 2: Record the living contract and close with clean pure/native quality gates** — `28f45d1` (SPR update)

## Files Created/Modified

- `tests/test_mypyc_guard.py` — AST/slot boundary checks and a mode-invariant candidate diagnostic semantic oracle.
- `.specify/memory/spr-core-api.md` — candidate snapshot, strict-shadowing, output, and budget contract.
- `.planning/phases/24-candidate-aware-diagnostics-output/24-03-SUMMARY.md` — execution evidence and native-shadow locations.

## Decisions Made

- The proof inspects source structure for compiled-private seams and exercises behavior through real machines, avoiding monkeypatch interception of native private dispatch.
- The only proof artifacts moved from the checkout were the generated `core.cpython-312-darwin.so` and `core__mypyc.cpython-312-darwin.so` files; tracked source remains the final import origin.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Stale test expectation] Included the planned static-unconditional field in the private graph-layout guard.**
- **Found during:** Task 1 preflight.
- **Issue:** Wave 1 correctly added `_GraphTransition.statically_unconditional`, but the exact compiled-layout assertion still described the pre-Phase-24 field set.
- **Fix:** Added the missing field to the frozen/slotted layout expectation.
- **Files modified:** `tests/test_mypyc_guard.py`
- **Verification:** Focused guard, pure-source preflight, Ruff, full pure suite, and compiled focused diagnostics passed.
- **Committed in:** `ba694b7`

**Total deviations:** 1 Rule 1 test-correctness fix. No runtime, public API, selector, callback, or output behavior changed in this plan.

## Issues Encountered

- The phase offline cache lacks pinned isolated-build requirements. `tests/test_build_modes.py` and `tests/test_installed_artifacts.py` passed under the host cache; every remaining pure-source test passed offline (one existing duplicate ZIP-member warning only).
- The local Beads Dolt service was unavailable during commits. Git commits succeeded; no tracker or remote action was attempted.

## Verification

- `task pure-source-check`: passed before pure proof and after native-shadow cleanup.
- Focused pure diagnostics: passed.
- Ruff format/check, blocking mypy, advisory ty, and recursive slots-policy audit: passed.
- Full pure suite: passed as host-cache isolated-build/artifact files plus the remaining offline source suite.
- Fresh `FAST_FSM_BUILD_MODE=compiled task build-check`: passed; native core origin was asserted.
- Focused compiled diagnostics: passed.
- Generated native shadows preserved at `/private/tmp/fast-fsm-phase24-guard-shadows.76UvqE` and `/private/tmp/fast-fsm-phase24-native-shadows.ivT44P`; final preflight confirmed `src/fast_fsm/core.py` origin.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Phase 24 is clean in pure and compiled modes, with DIAG-01 and DIAG-02 automatically evidenced. Phase 25 can consume the completed diagnostics contract without changing selector, callback, public-documentation, artifact, or performance scope retroactively.

## Self-Check: PASSED

- Verified this summary and all task commits (`ba694b7`, `1a52cf2`, `28f45d1`) exist locally.
- Verified the final source-origin preflight reports `src/fast_fsm/core.py`.

---
*Phase: 24-candidate-aware-diagnostics-output*
*Completed: 2026-09-07*
