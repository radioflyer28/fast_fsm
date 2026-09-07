---
phase: 23-construction-declarative-serialization-parity
plan: 01
subsystem: core topology serialization and query parity
tags: [python, mypyc, priority, serialization, clone, graph-snapshot]
requires:
  - phase: 22-ordered-runtime-selection-lifecycle-integration
    provides: ordered immutable candidate groups and direct singleton/group selectors
provides:
  - scalar condition-reference candidate identity and JSON-safe topology round-trips
  - candidate-complete immutable graph snapshots, target queries, and clone proofs
affects: [23-02, 23-03, 24-candidate-aware-diagnostics]
actuals:
  tokens: 8865
  tasks: 2
  commits: 5
tech-stack:
  added: []
  patterns:
    - cold candidate-sequence projection separate from dispatch selectors
    - validate-resolve-publish deserialization through one atomic registrar
key-files:
  created:
    - .planning/phases/23-construction-declarative-serialization-parity/23-01-SUMMARY.md
  modified:
    - src/fast_fsm/core.py
    - tests/test_advanced_functionality.py
    - tests/test_graph_invariants.py
    - tests/test_state_machine_utils.py
    - tests/test_async.py
key-decisions:
  - "condition_ref is a trailing optional opaque scalar carried by candidate, prepared, and graph records."
  - "Cold projections flatten immutable slots while Phase 22 selectors retain their direct singleton and local group branches."
patterns-established:
  - "Candidate projections use _transition_entries() only outside sync/async dispatch."
  - "Serialized construction validates and resolves every row before one atomic _commit_transition_plan() call."
requirements-completed: [PAR-02, PAR-03]
coverage:
  - id: D1
    description: "Candidate-complete JSON-safe topology round-trips retain priority and candidate-specific opaque condition references."
    requirement: PAR-03
    verification:
      - kind: integration
        ref: "tests/test_advanced_functionality.py::TestPrioritySerialization"
        status: pass
    human_judgment: false
  - id: D2
    description: "Snapshots, target queries, and sync/async clones preserve every candidate without entering selector cold projections."
    requirement: PAR-02
    verification:
      - kind: integration
        ref: "tests/test_graph_invariants.py tests/test_state_machine_utils.py tests/test_async.py tests/test_priority_selection.py -k priority-or-candidate-or-clone-or-snapshot-or-reachable-or-transition_exists-or-selection"
        status: pass
    human_judgment: false
duration: 10 min
completed: 2026-09-06
status: complete
---

# Phase 23 Plan 01: Candidate-Complete Construction Projection Summary

**Priority candidate groups now round-trip through a callable-safe scalar schema and remain complete in topology snapshots, target queries, and sync/async clone views.**

## Performance

- **Duration:** 10 min
- **Started:** 2026-09-06T22:12:04-04:00
- **Completed:** 2026-09-06T22:21:38-04:00
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Added optional opaque `condition_ref` identity to transition, prepared-plan, and immutable graph records without exposing it through callbacks.
- Reworked `from_dict()` to validate fields, expand cardinality, resolve external guards, and submit one complete atomic topology plan; `to_dict()` now emits one deterministic JSON-native record per candidate.
- Promoted cold projections to immutable candidate sequences for graph snapshots and target queries while preserving selector fast paths and clone value sharing.

## Task Commits

1. **Task 1: Round-trip one guarded candidate group through one atomic publication** — `39a5b6a` (RED tests), `65f1665` (implementation)
2. **Task 2: Apply the promoted candidate sequence to snapshots, queries, and clones** — `2cef91f` (RED tests), `ffc2fa5` (implementation), `f5a296c` (native-safe source assertion)

## Files Created/Modified

- `src/fast_fsm/core.py` — condition-reference identity, atomic callable-safe reconstruction, scalar exports, candidate snapshots, and complete target queries.
- `tests/test_advanced_functionality.py` — priority/reference serialization, ambiguity, malformed-record, and atomic-registration coverage.
- `tests/test_graph_invariants.py` — candidate snapshot, clone identity, and selector-boundary coverage.
- `tests/test_state_machine_utils.py` — grouped reachability and target-existence assertions.
- `tests/test_async.py` — async clone/reference and native-safe selector-structure coverage.

## Decisions Made

- `condition_ref` is serialized only when non-empty; live conditions remain exclusively caller-owned registry values.
- Legacy bare trigger keys work only for a single expanded candidate, preventing unsafe guard fan-out across a candidate group.
- `_transition_entries()` is a cold projection helper; selectors keep their Phase 22 direct singleton and `slot.entries` branches.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Type compatibility] Narrowed serialized source row typing for mypy invariance**
- **Found during:** Task 2 type gate
- **Issue:** A `list[str]` row was not assignable to the existing invariant `list[str | State]` registrar input.
- **Fix:** Preserved the validated source names while explicitly widening only the private prepared-row type.
- **Files modified:** `src/fast_fsm/core.py`
- **Verification:** `task typecheck-mypy`, `task typecheck-ty`, and focused pure/native tests passed.
- **Committed in:** `ffc2fa5`

**2. [Rule 1 - Native test compatibility] Replaced descriptor inspection with source-file assertions**
- **Found during:** Task 2 compiled smoke
- **Issue:** mypyc exposes selector methods as descriptors, so `inspect.getsource()` cannot read them in compiled mode.
- **Fix:** Read the checked-in selector source text to retain the same no-cold-helper structural proof in pure and native modes.
- **Files modified:** `tests/test_graph_invariants.py`, `tests/test_async.py`
- **Verification:** Focused compiled and pure suites passed.
- **Committed in:** `f5a296c`

**Total deviations:** 2 auto-fixed Rule 1 compatibility corrections. No API, architecture, or phase-boundary scope changed.

## Issues Encountered

- Pre-existing ignored in-place native shadows would have imported stale Phase 22 code in pure tests. They were recoverably moved to `/private/tmp/fast-fsm-phase23-native-shadows`; the project pure-source preflight passed before and after a fresh compiled smoke build.
- Beads' local Dolt server was unavailable during commits. Git commits completed; no beads or remote mutation was attempted.

## User Setup Required

None - no external service configuration required.

## Verification

- Pure Task 1 serialization/snapshot selection: 44 passed.
- Pure and compiled Task 2 query/clone/selector selection: 41 passed in each mode (compiled run had only existing asyncio deprecation warnings).
- `task pure-source-check`, Ruff, `task typecheck-mypy`, `task typecheck-ty`, and the slots-policy audit: passed.

## Next Phase Readiness

Wave 2 can consume immutable candidate references and complete declarative handler plurality without changing candidate storage, selector shape, or the callable-safe serialization boundary. No Wave 1 blocker remains.

## Self-Check: PASSED

- Summary exists, and task commits `39a5b6a`, `65f1665`, `2cef91f`, `ffc2fa5`, and `f5a296c` are present in local history.

---
*Phase: 23-construction-declarative-serialization-parity*
*Completed: 2026-09-06*
