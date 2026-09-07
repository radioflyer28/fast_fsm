---
phase: 24-candidate-aware-diagnostics-output
plan: 01
subsystem: candidate diagnostics and validation
tags: [python, diagnostics, validation, priority, snapshots, mypyc]
requires:
  - phase: 21-priority-contract-atomic-registration
    provides: ordered finite candidate groups with exact integer priorities
  - phase: 22-ordered-runtime-selection-lifecycle-integration
    provides: priority-ordered runtime selection without diagnostic policy execution
  - phase: 23-construction-declarative-serialization-parity
    provides: candidate-complete immutable graph snapshots
provides:
  - frozen static-unconditional snapshot evidence and priority-bearing scalar diagnostic edges
  - strict priority validation with candidate-specific malformed-topology records
  - conservative proved-versus-possible candidate-shadow findings and evidence-matched issues
affects: [24-02, 24-03, validation, diagnostics, visualization]
actuals:
  tokens: 5242
  tasks: 2
  commits: 5
tech-stack:
  added: []
  patterns:
    - capture candidate identity once in a frozen core snapshot, then validate only scalar graph edges
    - classify candidate shadowing from exact static evidence without evaluating caller policy
key-files:
  created:
    - .planning/phases/24-candidate-aware-diagnostics-output/24-01-SUMMARY.md
  modified:
    - src/fast_fsm/core.py
    - src/fast_fsm/_diagnostics.py
    - src/fast_fsm/validation.py
    - tests/test_graph_invariants.py
    - tests/test_validation.py
key-decisions:
  - "Only an unguarded exact base State is snapshot-proven unconditional; subclasses and declarative states remain conservative observations."
  - "Malformed candidate priorities use fixed reason codes and safe scalar priority values rather than caller-object representations."
patterns-established:
  - "Contiguous source/trigger edge groups preserve the snapshot's canonical priority order without consulting runtime singleton-or-group storage."
  - "Validation reserves the shared diagnostic ledger before every candidate inspection and emitted candidate finding."
requirements-completed: [DIAG-01]
coverage:
  - id: D1
    description: "Immutable graph snapshots retain each candidate's priority, guard presence, and narrow exact-base-State unconditional fact without evaluating caller policy."
    requirement: DIAG-01
    verification:
      - kind: integration
        ref: "tests/test_graph_invariants.py::test_graph_snapshot_captures_only_narrow_static_unconditional_evidence"
        status: pass
      - kind: integration
        ref: "tests/test_validation.py::TestFSMValidator::test_priority_candidates_remain_ordered_deterministic_and_single_captured"
        status: pass
    human_judgment: false
  - id: D2
    description: "Validation accepts strictly ordered candidate groups and reports malformed priorities plus proved or possible shadows in deterministic candidate order."
    requirement: DIAG-01
    verification:
      - kind: integration
        ref: "tests/test_validation.py::TestFSMValidator::test_candidate_priority_errors_are_scalar_stable_and_budgeted"
        status: pass
      - kind: integration
        ref: "tests/test_validation.py::TestFSMValidator::test_candidate_shadow_certainty_and_enhanced_issue_severity_are_conservative"
        status: pass
      - kind: integration
        ref: "tests/test_validation.py::TestFSMValidator::test_guarded_candidate_does_not_establish_shadowing"
        status: pass
    human_judgment: false
duration: 45m
completed: 2026-09-07
status: complete
---

# Phase 24 Plan 01: Candidate Validation Projection Summary

**Candidate-aware diagnostics now preserve immutable priority and eligibility evidence from core snapshot capture through strict determinism and conservative shadow validation.**

## Performance

- **Duration:** 45m
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Extended frozen graph snapshots and scalar diagnostic edges with priority, guard presence, and the exact-base-State static-unconditional proof.
- Replaced target-cardinality determinism with one ordered source/trigger candidate scan that accepts valid same- or different-target groups.
- Added bounded malformed-priority, proved-shadow, possible-shadow, and evidence-specific enhanced-validator issue reporting without invoking guards or state permissions.

## Task Commits

1. **Task 1: Trace one ordered candidate group through the immutable validation projection** — `37a62c8` (RED tests), `01d968d` (implementation)
2. **Task 2: Classify malformed priorities and proved-versus-possible shadowing conservatively** — `a888240` (RED tests), `3ebfe76` (implementation), `58ce931` (native-safe fixture correction)

## Files Created/Modified

- `src/fast_fsm/core.py` — captures the frozen `statically_unconditional` fact only for an unguarded exact base `State`.
- `src/fast_fsm/_diagnostics.py` — projects priority, guard presence, and static evidence into one scalar edge per snapshot candidate.
- `src/fast_fsm/validation.py` — validates strict priority order and reports candidate-specific error, proved-shadow, and possible-shadow findings.
- `tests/test_graph_invariants.py` — proves the narrow static fact remains false for guarded, subclass, and declarative sources.
- `tests/test_validation.py` — covers capture count, valid groups, malformed scalar priorities, budgets, conservative shadowing, and issue severities.

## Decisions Made

- Validation treats a priority group as deterministic when its exact built-in integer priorities are strictly increasing, regardless of target multiplicity.
- A non-integer or Boolean malformed value is reported through a fixed reason and `priority: null`; exact malformed integers remain visible as numeric values without leaking caller objects.
- Shadow certainty is snapshot evidence, not a runtime prediction: only an earlier statically unconditional row proves a later shadow.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Native test compatibility] Kept malformed-priority fixtures at the scalar diagnostic boundary.**
- **Found during:** Task 2 compiled focused probe.
- **Issue:** mypyc converts a handcrafted Boolean in the typed `_GraphTransition.priority` field to native integer `1` before the validator sees it, making a pure-only invalid-snapshot fixture assert the wrong condition in compiled mode.
- **Fix:** Constructed malformed `_DiagnosticEdge` fixtures after a valid immutable snapshot projection, which is the validator's actual scalar input boundary and preserves Boolean/non-integer values in both modes.
- **Files modified:** `tests/test_validation.py`
- **Verification:** Pure focused validation suite and compiled-focused candidate suite passed.
- **Committed in:** `58ce931`

**Total deviations:** 1 Rule 1 test-compatibility correction. No public API, runtime selector, callback, or storage change.

## Issues Encountered

- The temporary offline cache lacks pinned isolated-build requirements. Build-mode and installed-artifact tests completed under the host cache; the remainder of the pure suite passed offline to 100% with only the existing duplicate ZIP-member warning.
- The final pure suite initially exposed the Plan 24-03-owned frozen-layout expectation missing `statically_unconditional`. That scoped correction landed as `ba694b7`; this plan intentionally did not edit `tests/test_mypyc_guard.py`.
- A shared Wave 3 native-shadow cleanup removed generated extensions before this plan could make an independent compiled-origin assertion. The compiled-focused cases passed after the fresh build; authoritative native-origin proof remains Plan 24-03-owned.
- The local Beads Dolt service was unavailable during scoped commits. Git commits succeeded; no issue-tracker or remote mutation was attempted.

## User Setup Required

None - no external service configuration required.

## Verification

- `task pure-source-check`, focused pure graph/validation tests, Ruff, `task typecheck-mypy`, `task typecheck-ty`, and `tools/release_evidence.py slots-policy --json`: passed.
- Full pure suite: host-cache build/artifact isolation segment completed without failure; all remaining tests passed offline to 100% after the Wave 3 layout correction (one existing duplicate-zip-name warning).
- Fresh `setup.py build_ext --inplace` completed; compiled-focused candidate tests passed. Native-origin proof is recorded as Plan 24-03 work because its shared shadow cleanup raced this wave's origin assertion.

## Next Phase Readiness

Plan 24-02 can consume a candidate-complete scalar graph with stable priority, guard, and static-evidence fields. It must preserve this edge order and shared budget accounting in adjacency, path, JSON, diagram, and Markdown output.

## Self-Check: PASSED

- Verified the scoped summary file exists.
- Verified task commits `37a62c8`, `01d968d`, `a888240`, `3ebfe76`, and `58ce931` exist in local history.

---
*Phase: 24-candidate-aware-diagnostics-output*
*Completed: 2026-09-07*
