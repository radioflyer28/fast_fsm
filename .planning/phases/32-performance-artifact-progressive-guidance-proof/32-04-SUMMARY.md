---
phase: 32-performance-artifact-progressive-guidance-proof
plan: 04
subsystem: documentation-example
tags: [fsm-builder, telemetry, final-states, transition-modes, expected-rejection]
requires:
  - phase: 30-deprecation-builder-first
    provides: Builder-first flat-FSM transition semantics
  - phase: 31-flat-fsm-semantics
    provides: Explicit finality, self-transition modes, and expected rejection
provides:
  - Deterministic controller-owned drone tutorial with one FSM telemetry event
  - Observable finality, self-transition, priority, and rejection behavior
affects: [examples, documentation, UAT]
actuals:
  tokens: 5026
  tasks: 2
  commits: 4
tech-stack:
  added: []
  patterns:
    - One normalized telemetry sample maps to one FSM trigger.
    - Aircraft commands are bound to committed destination entry callbacks.
key-files:
  created: []
  modified:
    - examples/drone_failsafes.py
    - tests/test_drone_failsafes_example.py
key-decisions:
  - "Use priority 40 for terminal navigation-conflict after safety failsafes and before routine Mission self candidates."
  - "Represent normal and emergency touchdown as separate explicit final states; a new controller starts a second flight."
patterns-established:
  - "Tutorial controller pattern: own FSM, fact-only policy, replaceable command adapter."
  - "Tutorial rejection pattern: print only the bounded public rejection code, never arbitrary exception data."
requirements-completed: [DOC-01]
coverage:
  - id: D1
    description: Progressive deterministic drone tutorial covers one-event telemetry, priority failsafes, both self modes, final landings, and bounded rejection.
    requirement: DOC-01
    verification:
      - kind: unit
        ref: tests/test_drone_failsafes_example.py
        status: pass
      - kind: integration
        ref: uv run python examples/drone_failsafes.py
        status: pass
    human_judgment: false
duration: 3min
completed: 2026-09-19
status: complete
---

# Phase 32 Plan 04: Progressive Drone Semantics Summary

**A deterministic, builder-first drone controller now demonstrates FSM-owned telemetry priority, self-transition modes, final landing states, and committed adapter commands.**

## Performance

- **Duration:** 3 min
- **Started:** 2026-09-19T23:40:18Z
- **Completed:** 2026-09-19T23:43:25Z
- **Tasks:** 2/2
- **Files modified:** 2

## Accomplishments

- Kept one `telemetry_tick` per normalized sample while moving all state-specific eligibility and precedence into ordered builder transitions.
- Added Mission internal update and external re-entry candidates, with fake-clock smoke coverage proving their distinct residency and command behavior.
- Made normal and emergency touchdowns separate explicit final states, requiring a new controller for a second simulated flight.
- Added the terminal `navigation-conflict` rejection path, including false-guard fallthrough, safety precedence, bounded reporting, and no uncommitted aircraft effects.

## Task Commits

1. **Task 1: Teach final landings and both mission self-transition modes** - `ee38cec` (test), `5995a72` (feat)
2. **Task 2: Contrast false guard fallthrough with expected rejection** - `ae9b1f2` (test), `64fe683` (feat)

## Files Created/Modified

- `examples/drone_failsafes.py` - Controller-owned, deterministic tutorial with final-state, transition-mode, priority, and rejection beats.
- `tests/test_drone_failsafes_example.py` - Smoke proof for one-event dispatch, committed command order, both self modes, finality, fallthrough, and rejection.

## Decisions Made

- The external Mission self candidate has priority 50 and the internal update priority 60, following the safety candidates at 0, 10, and 20.
- The `navigation-conflict` guard is priority 40: ordinary absence returns false, while a present conflict raises the fixed public `TransitionRejected("navigation-conflict")` signal and prevents lower candidates.
- The script stays deterministic training software and explicitly disclaims real hardware, certification, and flight-control use.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- `task typecheck-ty` ran as the configured advisory gate but reports two existing unresolved relative-import diagnostics in `src/fast_fsm/core.py`; `task typecheck-mypy` passed and the focused tutorial suite passed.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- The runnable tutorial is ready for the public README/Sphinx progressive-guidance work and automated UAT classification.
- No implementation blocker remains for this plan.

## Self-Check: PASSED

- Both modified tutorial files exist and all four task commits are reachable in Git history.
- `uv run pytest tests/test_drone_failsafes_example.py -k 'mode or final or critical or telemetry_tick' -x -q` passed (4 tests).
- `uv run pytest tests/test_drone_failsafes_example.py -x -q` passed (12 tests).
- `uv run python examples/drone_failsafes.py` produced distinct internal, external, rejected, normal-final, and emergency-final transcript beats.

---
*Phase: 32-performance-artifact-progressive-guidance-proof*
*Completed: 2026-09-19*
