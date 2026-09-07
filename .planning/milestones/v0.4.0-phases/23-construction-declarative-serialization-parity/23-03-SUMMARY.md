---
phase: 23-construction-declarative-serialization-parity
plan: 03
subsystem: core construction and native parity
tags: [python, mypyc, priority, constructors, serialization, declarative]
requires:
  - phase: 23-01
    provides: candidate-complete serialization, snapshots, queries, and clone topology
  - phase: 23-02
    provides: plural declarative candidate identity and builder preflight
provides:
  - canonical 3/4/5-row quick-factory construction through one atomic registrar batch
  - native-safe structural and behavioral proof for promoted candidate topology
  - living construction, reference, declarative, clone, and callback contract
affects: [24-candidate-aware-diagnostics, 25-artifacts-performance-and-guidance]
actuals:
  tokens: 11071
  tasks: 2
  commits: 6
tech-stack:
  added: []
  patterns:
    - adapters collect complete rows and delegate one batch to the canonical registrar
    - compiled proof pairs source-structural checks with real behavior instead of monkeypatch interception
key-files:
  created:
    - .planning/phases/23-construction-declarative-serialization-parity/23-03-SUMMARY.md
  modified:
    - src/fast_fsm/core.py
    - tests/test_builder.py
    - tests/test_mypyc_guard.py
    - .specify/memory/spr-core-api.md
key-decisions:
  - "A private `_TransitionRow` union keeps quick/factory rows aligned with the canonical batch registrar."
  - "Native tests prove private publication seams through AST/source structure plus real rejection behavior, not monkeypatched compiled calls."
patterns-established:
  - "Quick construction preserves supplied State identity and publishes one complete candidate batch."
  - "Cold candidate projection and direct selector shape are separately guarded in pure and compiled modes."
requirements-completed: [PAR-01, PAR-02, PAR-03]
coverage:
  - id: D1
    description: "All direct, batch, builder, quick, factory, declarative, and dictionary construction paths preserve the ordered candidate fingerprint."
    requirement: PAR-01
    verification:
      - kind: integration
        ref: "tests/test_builder.py::TestConvenienceFunctions::test_all_constructors_preserve_the_same_priority_candidate_fingerprint"
        status: pass
    human_judgment: false
  - id: D2
    description: "Quick/factory rows are atomic, preserve State and guard identity, and leave builder staging retryable on a conflict."
    requirement: PAR-01
    verification:
      - kind: integration
        ref: "tests/test_builder.py::TestConvenienceFunctions::test_quick_factories_keep_state_guard_and_priority_rows_in_one_batch"
        status: pass
      - kind: integration
        ref: "tests/test_builder.py::TestConvenienceFunctions::test_builder_tie_failure_stays_unpublished_and_is_repairable"
        status: pass
    human_judgment: false
  - id: D3
    description: "Promoted candidate/declarative layouts, queries, snapshots, clones, callback payloads, and callable-safe atomic reconstruction agree in pure and native core."
    requirement: PAR-02
    verification:
      - kind: integration
        ref: "tests/test_mypyc_guard.py::test_phase23_construction_projection_and_callback_probe_is_mode_invariant"
        status: pass
      - kind: integration
        ref: "FAST_FSM_BUILD_MODE=compiled task build-check plus focused native candidate suite"
        status: pass
    human_judgment: false
  - id: D4
    description: "Candidate serialization retains scalar priority/reference identity without exposing it through caller callbacks."
    requirement: PAR-03
    verification:
      - kind: integration
        ref: "tests/test_mypyc_guard.py::test_private_graph_records_are_frozen_slot_dataclasses"
        status: pass
    human_judgment: false
duration: 1h 05m
completed: 2026-09-07
status: complete
---

# Phase 23 Plan 03: Construction and Native Parity Summary

**Quick factories now publish complete priority-bearing candidate batches atomically, while native-safe structural and behavioral checks lock the full construction-to-projection contract.**

## Performance

- **Duration:** 1h 05m
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Extended `quick_build()` and `quick_fsm()` to accept canonical 3/4/5 transition rows, preserve supplied State/guard identity, and delegate exactly one batch to `add_transitions()`.
- Added cross-constructor fingerprint, failure/retry, exact layout, selector, cold-projection, callback-payload, and native semantic probes.
- Updated the core SPR for candidate references, plural declarative identity, atomic factory construction, scalar round-trips, clone/query topology, and selector/callback boundaries.

## Task Commits

1. **Task 1: Make quick and factory construction canonically atomic and equivalent** — `a5a2d68` (RED tests), `64641dc` (implementation)
2. **Task 2: Lock the promoted topology and callback contract in pure and compiled core** — `6a89448`, `e1a3ec5`, `35ac9d0` (native-safe tests), `166dcca` (SPR)

## Files Created/Modified

- `src/fast_fsm/core.py` — shared transition-row annotation and one-batch quick/factory registration.
- `tests/test_builder.py` — constructor fingerprints, identity, late-failure, retryability, and native-safe one-batch guard.
- `tests/test_mypyc_guard.py` — exact promoted layout, selector shape, pure/native semantic, atomic-deserialization, and trace metadata checks.
- `.specify/memory/spr-core-api.md` — living Phase 23 construction and candidate-parity contract.

## Decisions Made

- Quick adapters keep no priority, duplicate, merge, or graph-version policy; the canonical registrar owns all of it.
- Native proof uses static seams plus real public behavior because mypyc dispatch cannot be reliably intercepted with Python monkeypatches.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Native test compatibility] Replaced compiled-unobservable monkeypatch assertions**
- **Found during:** Task 2 compiled focused suite.
- **Issue:** mypyc bypasses monkeypatched Python methods, making call-count assertions report zero despite correct native behavior.
- **Fix:** Used source-structural assertions plus real quick-factory and `from_dict()` late-conflict behavior; preserved the same atomic-publication guarantee in pure and compiled runs.
- **Files modified:** `tests/test_builder.py`, `tests/test_mypyc_guard.py`
- **Verification:** Fresh compiled build/import and focused native candidate suite passed.
- **Committed in:** `6a89448`, `35ac9d0`

**2. [Rule 1 - Stale structural expectation] Included Phase 22 trace priority in the legacy AST guard**
- **Found during:** Task 2 final pure suite.
- **Issue:** One existing `FSMTraceEvent` expected-field list omitted the established `priority` field.
- **Fix:** Restored the exact current layout assertion.
- **Files modified:** `tests/test_mypyc_guard.py`
- **Verification:** Focused guard and final pure suite passed.
- **Committed in:** `e1a3ec5`

**Total deviations:** 2 Rule 1 test-compatibility corrections. No public API, compilation boundary, or phase scope changed.

## Issues Encountered

- The sandbox’s isolated cache lacks pinned build requirements used by wheel/sdist tests. Those build-mode and installed-artifact modules passed through the host dependency cache; the remaining full pure suite passed offline.
- The focused native command deselected the Wave 1-owned monkeypatch-only serialization test after replacing its required atomicity coverage with the native-safe owned probe above. The stale Wave 1 grouped-projection expectation was independently corrected in `89e032b` before final pure verification.
- The local Beads Dolt service was unavailable during commits. Every scoped Git commit succeeded; no remote or issue-tracker mutation was attempted.

## User Setup Required

None - no external service configuration required.

## Verification

- `task pure-source-check`, Ruff, `task typecheck-mypy`, `task typecheck-ty`, and `tools/release_evidence.py slots-policy --json`: passed.
- Full pure suite: build-mode and installed-artifact modules passed with the host cache; all remaining tests passed offline to 100% (one existing duplicate-zip-name warning).
- `FAST_FSM_BUILD_MODE=compiled task build-check`: passed with native core import smoke test.
- Focused compiled candidate suite and the owned Phase 23 semantic/atomicity probes: passed (existing asyncio deprecation warnings only).
- Generated `core.cpython-312-darwin.so` and `core__mypyc.cpython-312-darwin.so` were moved recoverably to `/private/tmp/fast-fsm-phase23-native-shadows/wave3-final/`; post-native `task pure-source-check` passed.

## Next Phase Readiness

All Phase 23 construction, declarative, serialization, query, clone, callback, pure, and compiled parity seams are ready for Phase 24 diagnostics without altering the direct singleton selector path.

## Self-Check: PASSED

- Verified all scoped source, test, SPR, and summary files exist.
- Verified task commits `a5a2d68`, `64641dc`, `6a89448`, `166dcca`, `e1a3ec5`, and `35ac9d0` exist in local history.

---
*Phase: 23-construction-declarative-serialization-parity*
*Completed: 2026-09-07*
