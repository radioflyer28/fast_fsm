---
phase: 25-performance-artifact-proof-drone-guidance
plan: "01"
subsystem: performance
tags: [priority-transitions, complexity, mypyc, benchmarks, pytest]
requires:
  - phase: 21-priority-contract-atomic-registration
    provides: immutable singleton-or-group priority transition slots
  - phase: 22-ordered-runtime-selection-lifecycle-integration
    provides: direct singleton and ordered local candidate selection
provides:
  - one-pass immutable local insertion for priority transition groups
  - structural O(1)/local O(k) regression proof in pure and compiled modes
  - environment-labelled priority-group benchmark observations
affects: [25-02-artifact-proof, 25-03-drone-guidance, performance-documentation]
actuals:
  tokens: 9168
  tasks: 2
  commits: 5
tech-stack:
  added: []
  patterns:
    - one forward immutable tuple scan plus a single tuple splice
    - environment-labelled descriptive timings backed by deterministic counters
key-files:
  created: []
  modified:
    - src/fast_fsm/core.py
    - tests/test_priority_selection.py
    - tests/test_performance_benchmarks.py
    - benchmarks/performance_demo.py
    - Taskfile.yml
    - .specify/memory/spr-core-api.md
key-decisions:
  - "Keep priority-group mutation to one ordered local scan and one immutable splice while preserving duplicate identity and batch atomicity."
  - "Treat priority-group timing as environment-labelled observation; retain the release floor only for installed compiled singleton dispatch."
patterns-established:
  - "Structural complexity tests assert ranked guard work and topology-independent registry access instead of timing ratios."
  - "Native mypyc tests parse checked-in source for AST contracts and account for direct native mapping access."
requirements-completed: [PERF-01]
coverage:
  - id: D1
    description: One-pass immutable priority-group insertion preserves sorted dispatch, duplicate identity, and atomic conflicts.
    requirement: PERF-01
    verification:
      - kind: unit
        ref: tests/test_priority_selection.py#test_out_of_order_group_registration_preserves_order_dispatch_identity_and_atomicity
        status: pass
      - kind: unit
        ref: tests/test_performance_benchmarks.py#test_transition_slot_merge_uses_one_local_immutable_scan_without_sorting
        status: pass
      - kind: integration
        ref: FAST_FSM_BUILD_MODE=compiled uv run pytest tests/test_priority_selection.py tests/test_performance_benchmarks.py -x -q
        status: pass
    human_judgment: false
  - id: D2
    description: The benchmark task reports representative local-group observations with complete runtime labels.
    requirement: PERF-01
    verification:
      - kind: unit
        ref: tests/test_performance_benchmarks.py#test_priority_group_reporter_labels_each_environmental_observation
        status: pass
      - kind: integration
        ref: task benchmark
        status: pass
    human_judgment: false
duration: 14m
completed: 2026-09-07
status: complete
---

# Phase 25 Plan 01: Performance, Artifact Proof & Drone Guidance Summary

**Priority-group registration now uses a one-pass immutable insertion, with deterministic local-work proofs and a runnable environment-labelled timing matrix.**

## Performance

- **Duration:** 14m
- **Started:** 2026-09-07T05:35:36Z
- **Completed:** 2026-09-07T05:49:53Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- Replaced per-registration comparison sorting with one ordered local scan and one immutable tuple splice, preserving singleton representation, exact duplicate identity, ascending priority order, graph-version behavior, and batch conflict atomicity.
- Added public-API, AST, counted-registry, and ranked-guard tests for 36 representative group-depth/winner/topology cases; both clean pure source and fresh mypyc builds pass the focused suite.
- Replaced the blanket performance demo with `task benchmark`, which emits 36 descriptive JSON rows that identify runtime origin, mode, platform, group shape, guard work, samples, and observed rate.

## Task Commits

1. **Task 1: Prove and implement one end-to-end linear grouped insertion path**
   - `26fc3a2` — `test(25-01): add linear insertion regression coverage`
   - `87eb4d4` — `feat(25-01): use linear immutable priority insertion`
2. **Task 2: Characterize representative local group work with truthful environment labels**
   - `b8dce6f` — `test(25-01): add priority group benchmark matrix`
   - `cc8beb5` — `feat(25-01): report labelled priority group observations`
   - `89eaaca` — `fix(25-01): support native complexity test instrumentation`

## Files Created/Modified

- `src/fast_fsm/core.py` — one-pass tuple insertion plus truthful sync/async complexity docstrings.
- `tests/test_priority_selection.py` — end-to-end ordering, history metadata, identity, and atomicity coverage.
- `tests/test_performance_benchmarks.py` — AST proof, 36 structural matrix cases, reporter coverage, and native-compatible counters.
- `benchmarks/performance_demo.py` — descriptive priority-group timing reporter with complete runtime labels.
- `Taskfile.yml` — benchmark and compiled-benchmark targets invoke the reporter.
- `.specify/memory/spr-core-api.md` — living O(1)/local O(k) contract now names one-scan immutable mutation.

## Decisions Made

- Use one forward scan and one tuple splice for an already ascending frozen candidate group; duplicates return the original published slot and conflicts occur before publication.
- Use structural counters for complexity guarantees and label all group timing observations by the actual runtime; no grouped timing becomes a release floor.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Test compatibility] Made AST and counted-map proof runnable against mypyc.**
- **Found during:** Plan-level compiled focused verification.
- **Issue:** `inspect.getsource()` cannot inspect a mypyc method, and native dictionary access bypasses the Python test mapping wrapper.
- **Fix:** Parse the checked-in `core.py` source for the AST contract and make counted-map expectations explicitly reflect pure versus native access paths.
- **Files modified:** `tests/test_performance_benchmarks.py`
- **Verification:** Fresh compiled build/smoke test and focused priority/performance suite passed.
- **Committed in:** `89eaaca`

**2. [Rule 1 - Lint error] Removed an unused benchmark import.**
- **Found during:** Task 2 Ruff validation.
- **Issue:** The focused reporter no longer needed `sys`.
- **Fix:** Removed the unused import.
- **Files modified:** `benchmarks/performance_demo.py`
- **Verification:** Ruff check and focused performance tests passed.
- **Committed in:** `cc8beb5`

**Total deviations:** 2 auto-fixed Rule 1 issues. No runtime scope expanded beyond D-01.

## Issues Encountered

- The initial `task benchmark` inherited uv's default cache location, which is outside this sandbox. Re-running the unchanged task with the existing writable `UV_CACHE_DIR` succeeded.
- Each fresh mypyc build produced two source-tree native shadows. Per the plan, they were recoverably moved to `/private/tmp/fast-fsm-phase25-01-native-recovery/`; a final pure-source check confirmed `src/fast_fsm/core.py` was authoritative.

## Verification

- `FAST_FSM_BUILD_MODE=pure uv run pytest tests/test_priority_selection.py tests/test_performance_benchmarks.py -x -q` — 84 passed.
- `FAST_FSM_BUILD_MODE=compiled task build-check` and the same focused suite — 84 passed; compiled smoke test passed.
- `task pure-source-check`, `task typecheck-mypy`, `task typecheck-ty`, and `uv run python tools/release_evidence.py slots-policy --json` — passed; the slots audit retained exactly the established three registered exceptions.
- `task benchmark` — passed, producing 36 environment-labelled descriptive observations.

## Next Phase Readiness

Plan 25-02 can use the corrected priority behavior and source/native test evidence for artifact parity work. Plan 25-03 can reference the established public complexity guidance without changing selection semantics.

## Self-Check: PASSED

All six changed deliverables and all five task commits were present in the repository history.

---
*Phase: 25-performance-artifact-proof-drone-guidance*
*Completed: 2026-09-07*
