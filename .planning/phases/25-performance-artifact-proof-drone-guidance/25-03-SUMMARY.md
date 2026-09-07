---
phase: 25-performance-artifact-proof-drone-guidance
plan: "03"
subsystem: documentation
tags: [drone-example, telemetry, priority-transitions, performance-guidance, sphinx]
requires:
  - phase: 25-01
    provides: truthful singleton-versus-group complexity proof and benchmark observations
  - phase: 25-02
    provides: fresh source/pure/compiled artifact conformance and singleton performance floor
provides:
  - controller-owned one-tick telemetry routing with FSM-owned failsafe priority
  - post-commit aircraft command adapter proof with a replaceable simulation
  - synchronized O(1) singleton versus local O(k) group guidance across public and maintainer surfaces
affects: [phase-gate, documentation, examples, performance-guidance]
actuals:
  tokens: 8115
  tasks: 2
  commits: 4
tech-stack:
  added: []
  patterns:
    - one normalized telemetry observation followed by one telemetry_tick trigger
    - bound destination-entry adapter commands after the FSM commit boundary
    - O(1) lookup/direct-singleton guidance separated from local O(k) immutable-group work
key-files:
  created: []
  modified:
    - examples/drone_failsafes.py
    - tests/test_drone_failsafes_example.py
    - README.md
    - docs/dev/architecture.md
    - docs/examples/index.md
    - .github/copilot-instructions.md
    - .planning/PROJECT.md
key-decisions:
  - "Use one FSM-owned telemetry_tick with fixed guarded candidates instead of controller-side trigger priority routing."
  - "Keep telemetry fact-only and command aircraft only from the selected destination state's post-commit entry callback."
  - "Describe direct singleton dispatch as O(1), and immutable group insertion or ordered selection as local O(k), with exact timings labelled by environment."
patterns-established:
  - "Controller composition owns telemetry, FSM, and a Protocol-shaped side-effect adapter without making the adapter an FSM subclass."
  - "Safety examples retain an explicit deterministic-training, non-certified, non-hardware disclaimer in source and public guidance."
requirements-completed: [PERF-01, DOC-01]
coverage:
  - id: D1
    description: "One observed telemetry sample reaches one owned telemetry_tick, whose fixed guards select the failsafe winner and invoke only the committed destination command."
    requirement: DOC-01
    verification:
      - kind: unit
        ref: "tests/test_drone_failsafes_example.py#test_controller_observes_one_sample_and_dispatches_one_telemetry_tick"
        status: pass
      - kind: unit
        ref: "tests/test_drone_failsafes_example.py#test_critical_fault_wins_simultaneous_failsafes_and_commands_after_commit"
        status: pass
      - kind: e2e
        ref: "UV_CACHE_DIR=/private/tmp/fast-fsm-phase23-uv-cache UV_OFFLINE=1 uv run python examples/drone_failsafes.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Public, architecture, example, maintainer, and project guidance distinguish singleton O(1) behavior from local group O(k) work and retain the simulation disclaimer."
    requirement: PERF-01
    verification:
      - kind: integration
        ref: "UV_CACHE_DIR=/private/tmp/fast-fsm-phase23-uv-cache UV_OFFLINE=1 task docs-check && task docs-test"
        status: pass
      - kind: unit
        ref: "tests/test_readme_examples.py"
        status: pass
    human_judgment: true
    rationale: "Rendered wording is automated, but a maintainer must judge that benchmark observations and the drone disclaimer cannot be misread as a hardware or certification claim."
duration: 12m
completed: 2026-09-07
status: complete
---

# Phase 25 Plan 03: Controller-Owned Drone Guidance Summary

**One normalized drone sample now enters a controller-owned FSM exactly once, while fixed guards choose the failsafe and a committed state entry alone commands a replaceable aircraft adapter.**

## Performance

- **Duration:** 12m
- **Started:** 2026-09-07T06:39:28Z
- **Completed:** 2026-09-07T06:51:23Z
- **Tasks:** 2/2
- **Files modified:** 7

## Accomplishments

- Replaced the external telemetry-trigger loop with one `telemetry_tick`; fixed priority guards select critical fault, link loss, low battery, and local progress facts inside the FSM.
- Kept `DroneController` as the composition root for `TelemetryPolicy`, FSM, and `AircraftCommands`; state-entry actions reach only the selected adapter command after commit.
- Synchronized README, Sphinx architecture/examples, maintainer policy, and project constraints with the O(1) singleton/local O(k) group contract and a prominent educational simulation disclaimer.

## Task Commits

1. **Task 1: Route one telemetry sample through FSM-owned priority and post-commit commands**
   - `2e6e801` — `test(25-03): add failing one-tick drone tests`
   - `3c2acb5` — `feat(25-03): route drone telemetry through FSM priority`
   - `b0c6ee4` — `test(25-03): prove drone adapter composition`
2. **Task 2: Synchronize public complexity and safe drone guidance**
   - `296c431` — `docs(25-03): document priority telemetry guidance`

## Files Created/Modified

- `examples/drone_failsafes.py` — single-event guarded failsafe model with explicit operator actions and post-commit adapter commands.
- `tests/test_drone_failsafes_example.py` — one-observation/one-trigger, precedence, composition, fact-only, and command-timing proof.
- `README.md` — runnable drone link, safety disclaimer, and truthful singleton/group complexity table.
- `docs/dev/architecture.md` — private singleton-or-group topology and dispatch/mutation complexity contract.
- `docs/examples/index.md` — literalincluded runnable drone walkthrough with explicit safety framing.
- `.github/copilot-instructions.md` and `.planning/PROJECT.md` — maintainer and project-level performance constraints reconciled with priority groups.

## Decisions Made

- Retained operator actions as explicit FSM calls so telemetry handling can always observe once and issue exactly one `telemetry_tick`.
- Used priority `0`, `10`, and `20` for critical fault, link loss, and low battery; state-local normal telemetry facts follow at priority `30`.
- Treated the ≥200,000 ops/sec requirement as a fresh installed compiled singleton floor only; other exact rates are environment-labelled observations.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Lint formatting] Formatted the revised drone example.**
- **Found during:** Task 1
- **Issue:** Ruff reported the rewritten example needed formatting.
- **Fix:** Applied the repository Ruff formatter before final focused validation.
- **Files modified:** `examples/drone_failsafes.py`
- **Verification:** Ruff format/check and 6 focused example tests passed.
- **Committed in:** `3c2acb5`

---

**Total deviations:** 1 auto-fixed Rule 1 issue.
**Impact on plan:** Formatting-only correction; no runtime scope, package, or hardware integration was added.

## Issues Encountered

- The full pure suite initially stopped at `tests/test_build_modes.py::test_pure_sdist_contains_selector_and_can_build_wheel_in_isolation` because the phase-local offline cache lacked pinned isolated-build requirements. The exact isolated-build test passed with network disabled against the existing local cache. A later full-suite invocation returned only partial progress from the execution harness, so no full-suite pass is claimed here.
- Git's pre-commit Beads export warned that its local Dolt server was unavailable. Each normal local Git commit still completed; no issue state was changed and no remote operation was attempted.

## Verification

- `UV_CACHE_DIR=/private/tmp/fast-fsm-phase23-uv-cache UV_OFFLINE=1 FAST_FSM_BUILD_MODE=pure uv run pytest tests/test_drone_failsafes_example.py -x -q` — passed (6 tests).
- `UV_CACHE_DIR=/private/tmp/fast-fsm-phase23-uv-cache UV_OFFLINE=1 uv run python examples/drone_failsafes.py` — passed.
- Ruff format/check on both changed Python files — passed.
- `UV_CACHE_DIR=/private/tmp/fast-fsm-phase23-uv-cache UV_OFFLINE=1 task docs-check` and `task docs-test` — passed.
- `UV_CACHE_DIR=/private/tmp/fast-fsm-phase23-uv-cache UV_OFFLINE=1 FAST_FSM_BUILD_MODE=pure uv run pytest tests/test_readme_examples.py tests/test_drone_failsafes_example.py -x -q` — passed (17 tests).
- `UV_CACHE_DIR=/private/tmp/fast-fsm-phase23-uv-cache UV_OFFLINE=1 task typecheck-mypy` and `task typecheck-ty` — passed.
- `UV_CACHE_DIR=/private/tmp/fast-fsm-phase23-uv-cache UV_OFFLINE=1 task benchmark` — passed; all emitted rows identify pure-Python source origin, platform, group shape, and observed rate as environment-labelled observations.
- Full pure suite — unrun to a conclusive final result because the phase-local offline cache lacked required isolated-build packages and the allowed local-cache retry returned partial harness progress; exact previously blocked isolated-build test passed from local cache.

## User Setup Required

None - no external service configuration or hardware setup is required.

## Next Phase Readiness

- The user-facing drone guidance and performance contract are ready for phase verification.
- The final phase gate should run the full suite from an environment with all reviewed isolated-build requirements available offline (or otherwise explicitly authorized package access); no source change is indicated by the cache-only failure.

## Self-Check: PASSED

All seven changed deliverables and the summary exist; all four task commits are
present in Git history.

---
*Phase: 25-performance-artifact-proof-drone-guidance*
*Completed: 2026-09-07*
