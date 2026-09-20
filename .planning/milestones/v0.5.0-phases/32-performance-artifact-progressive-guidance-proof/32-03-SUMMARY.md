---
phase: 32-performance-artifact-progressive-guidance-proof
plan: 03
subsystem: performance
tags: [benchmark, mypyc, provenance, trace, taskfile]
requires:
  - phase: 31-trace-semantics-finality
    provides: explicit finality, transition modes, rejection semantics, and disabled-TRACE fast path
provides:
  - Deterministic direct-selector and TRACE-boundary regression proof
  - Environment-labelled final, self-transition, and rejection cost observations
  - Taskfile commands that distinguish active and compiled-native benchmark runs
affects: [release-evidence, artifact-proof, documentation]
actuals:
  tokens: 5505
  tasks: 2
  commits: 4
tech-stack:
  added: []
  patterns:
    - "Optional semantic timing stays in a descriptive benchmark module, outside trigger()."
    - "Compiled benchmark commands assert the observed native loader before timing."
key-files:
  created: []
  modified:
    - benchmarks/performance_demo.py
    - tests/test_performance_benchmarks.py
    - Taskfile.yml
key-decisions:
  - "Keep the installed compiled singleton threshold fixed at 200,000 ops/sec; feature rows are descriptive and non-gating."
  - "Build final-entry machines before each timed sample so construction does not contaminate dispatch timing."
  - "Require an explicit environment label and native loader assertion for the compiled Taskfile command."
patterns-established:
  - "Benchmark rows carry exact runtime provenance, tool version, timing method, sample controls, operation count, and local guard work."
  - "AST and sentinel tests protect the no-feature selector and disabled TRACE boundary without elapsed-time claims."
requirements-completed: [PERF-01, PERF-02, PERF-03]
coverage:
  - id: D1
    description: "Direct singleton dispatch and disabled TRACE remain structurally local and collector-free."
    requirement: PERF-01
    verification:
      - kind: unit
        ref: "tests/test_performance_benchmarks.py#direct singleton, selector, and TRACE regressions"
        status: pass
      - kind: integration
        ref: "task release-installed-performance-check"
        status: pass
    human_judgment: false
  - id: D2
    description: "Four optional semantics emit separate provenance-labelled, non-gating timing rows."
    requirement: PERF-03
    verification:
      - kind: unit
        ref: "tests/test_performance_benchmarks.py#semantic observation and CLI contracts"
        status: pass
      - kind: integration
        ref: "task benchmark && task benchmark-compiled"
        status: pass
    human_judgment: false
status: complete
---

# Phase 32 Plan 03: Performance Artifact Proof Summary

**Direct singleton dispatch remains structurally local and above its fresh installed compiled floor, while optional semantics now produce separate, provenance-labelled observations.**

## Performance

- **Duration:** 8 min
- **Started:** 2026-09-19T23:27:32Z
- **Completed:** 2026-09-19T23:35:19Z
- **Tasks:** 2/2
- **Files modified:** 3

## Accomplishments

- Added structural tests for the two direct registry lookups, local-only grouped work, no reflection in selectors, and the disabled TRACE collector boundary in sync and async execution.
- Added four descriptive `SEMANTIC_OBSERVATION` scenarios: `final_entry`, `internal_self`, `external_self`, and `expected_rejection`; each row records runtime origin/mode, distribution and uv versions, platform, timing method, sample controls, operation count, and guard work.
- Made `task benchmark` label its active runtime and made `task benchmark-compiled` demand an actual compiled-native core before measuring.

## Verification

- `uv run pytest tests/test_performance_benchmarks.py -x -q` — passed (one existing timing-condition deprecation warning).
- `uv run ruff check benchmarks/performance_demo.py tests/test_performance_benchmarks.py` and `uv run mypy benchmarks/performance_demo.py` — passed.
- Fresh native focused selector/reporter regression run — passed; generated native shadows were moved to the recoverable `/private/tmp/fast-fsm-phase32-native.l7K5yX` location, then source origin was re-verified.
- `task benchmark` — passed with `task-active-runtime`, reporting pure-source `src/fast_fsm/core.py` on CPython 3.12.10 / uv 0.12.17.
- `task benchmark-compiled` — passed with `task-compiled-build`, asserting `compiled-native` from `src/fast_fsm/core.cpython-312-darwin.so`.
- `task release-slots-check` — passed.
- `task release-installed-performance-check` — passed: fresh installed compiled-wheel median was **610,721.99 ops/sec**, above the fixed **200,000 ops/sec** floor. Its exact origin was an `ExtensionFileLoader` module in the ephemeral installed-artifact environment.

## Task Commits

1. **Task 1: Lock the unfeatured singleton work shape and native floor** — `578858d` (test)
2. **Task 2: Publish separate descriptive feature-cost observations (RED)** — `e3296cd` (test)
3. **Task 2: Publish separate descriptive feature-cost observations (GREEN)** — `8a64c1a` (feat)

## Files Created/Modified

- `benchmarks/performance_demo.py` — emits labelled priority and optional-semantic observations with loader assertion support.
- `tests/test_performance_benchmarks.py` — covers direct paths, TRACE gating, scenario inventory, provenance, CLI output, and Taskfile contracts.
- `Taskfile.yml` — passes explicit labels and the compiled-native assertion to benchmark commands.

## Decisions Made

- Preserved the production `trigger()` implementation unchanged: benchmark instrumentation is entirely external, and the durable installed-native gate remains owned by release evidence.
- Used a prebuilt machine batch for final-entry samples; self and rejection samples are repeatedly reachable through public FSM transitions only.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Test correctness] Made the loader-mismatch CLI test use the opposite valid mode.**

- **Found during:** Task 2
- **Issue:** The initial test supplied an invalid mode string, exercising argparse validation instead of the planned runtime-loader mismatch path.
- **Fix:** Derive the opposite of the current core mode and assert the reporter's explicit mismatch failure.
- **Files modified:** `tests/test_performance_benchmarks.py`
- **Verification:** Focused CLI and semantic reporter tests passed.
- **Committed in:** `8a64c1a`

**Total deviations:** 1 auto-fixed (Rule 1)

## Issues Encountered

None. The task-created native shadows were deliberately retained outside the repository for recovery, and the checkout was restored to its pure source origin.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

The fixed installed-native performance gate and the descriptive scenario schema are ready for Phase 32's artifact and progressive-guidance work. No tag, publication, or universal speed claim was introduced.

## Self-Check: PASSED

- Confirmed the three modified production/test/config files exist.
- Confirmed task commits `578858d`, `e3296cd`, and `8a64c1a` exist in git history.

---

*Phase: 32-performance-artifact-progressive-guidance-proof*
*Completed: 2026-09-19*
