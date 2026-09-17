---
phase: 28-same-state-transition-modes
plan: 01
subsystem: fsm-runtime
tags: [python, fsm, transition-mode, lifecycle, builder, atomic-construction]
requires:
  - phase: 27-explicit-final-states
    provides: canonical State finality and transaction-time source validation
provides:
  - Explicit immutable internal-mode metadata on direct transition entries
  - Synchronous external versus internal self-transition lifecycle specialization
  - Canonical self-only validation, builder propagation, and graph/clone continuity
affects: [28-02, 28-03, 30-construction-and-persistence-parity, 31-diagnostics, 32-docs-and-release]
actuals:
  tokens: 7919
  tasks: 2
  commits: 4
tech-stack:
  added: []
  patterns:
    - Selected-entry transition mode controls one lifecycle specialization.
    - Internal commits record history without resetting state residency timing.
    - Canonical construction validates fully before publishing topology.
key-files:
  created:
    - tests/test_transition_modes.py
  modified:
    - src/fast_fsm/core.py
    - src/fast_fsm/core.pyi
    - tests/test_graph_invariants.py
    - tests/test_hypothesis.py
    - tests/test_builder.py
key-decisions:
  - "Internal mode stays on the selected immutable entry; it is never inferred from endpoint equality."
  - "Internal logical commits append optional history while preserving the existing state-entry epoch."
  - "The primary builder carries the immutable scalar into the canonical transaction rather than creating a second registration path."
patterns-established:
  - "External mode keeps the legacy lifecycle path; internal mode skips all state lifecycle surfaces as one bounded branch."
  - "Mode participates in same-priority duplicate identity and cold graph/clone projection."
requirements-completed: [MODE-01, MODE-02, MODE-03, MODE-04]
coverage:
  - id: D1
    description: Direct transitions support default external and explicit internal self-transition behavior with truthful results and history.
    requirement: MODE-01
    verification:
      - kind: integration
        ref: "uv run pytest tests/test_transition_modes.py tests/test_transition_lifecycle.py -x -q -k 'mode or self_transition or lifecycle'"
        status: pass
    human_judgment: false
  - id: D2
    description: Canonical construction rejects invalid internal topology atomically and retains mode through builder, graph, and clone paths.
    requirement: MODE-02
    verification:
      - kind: integration
        ref: "uv run pytest tests/test_transition_modes.py tests/test_graph_invariants.py tests/test_hypothesis.py tests/test_builder.py -x -q -k 'internal or mode or atomic or ownership or clone or snapshot'"
        status: pass
    human_judgment: false
  - id: D3
    description: External self-transitions preserve legacy lifecycle while internal events commit without state exit or re-entry surfaces.
    requirement: MODE-03
    verification:
      - kind: integration
        ref: "uv run pytest tests/test_transition_modes.py tests/test_graph_invariants.py tests/test_hypothesis.py tests/test_builder.py tests/test_transition_lifecycle.py -x -q"
        status: pass
    human_judgment: false
status: complete
---

# Phase 28 Plan 01: Same-State Transition Modes Summary

**Explicit per-entry internal self-transitions now perform a truthful in-state commit while preserving the original external self-transition lifecycle as the default.**

## Performance

- **Duration:** 7 min
- **Started:** 2026-09-17T00:18:16Z
- **Completed:** 2026-09-17T00:25:43Z
- **Tasks:** 2/2
- **Files modified:** 6

## Accomplishments

- Added the slotted immutable `internal` scalar to direct transition carriers, results, and history records.
- Established the sync lifecycle split: internal events retain transition-level callbacks and logical commit while skipping all state exit/entry hooks, callbacks, and listeners.
- Enforced exact-bool and canonical self-only registration, mode-aware candidate identity, all-or-nothing publication, builder repairability, and graph/clone propagation.

## Task Commits

1. **Task 1: Trace one State through explicit external and internal self-transitions** — `1ef328a` (RED test) and `54aaa61` (feature)
2. **Task 2: Harden canonical validation, mode identity, builder staging, and graph continuity** — `7298336` (RED test) and `7822615` (feature)

## Files Created/Modified

- `src/fast_fsm/core.py` — mode carriers, direct registration, sync execution, atomic validation, graph snapshot, clone, and builder propagation.
- `src/fast_fsm/core.pyi` — public result/history and direct/builder mode typing.
- `tests/test_transition_modes.py` — independent Wave 0 sync lifecycle oracle.
- `tests/test_graph_invariants.py` — exact validation, conflict identity, snapshot/clone, and deterministic ownership evidence.
- `tests/test_hypothesis.py` — reordered invalid internal request transaction property.
- `tests/test_builder.py` — builder authoring and repairability coverage.

## Decisions Made

- A selected `TransitionEntry.internal` is the sole runtime source of lifecycle mode.
- Internal commits do not reassign state or reset residency; history timestamps the event only when enabled.
- Existing ownership and prepare-all/publish-once topology mechanics remain the one construction boundary.

## Deviations from Plan

None — plan executed as specified.

## Issues Encountered

- `task typecheck-ty` remains advisory and reports its existing relative-import resolution diagnostic for `src/fast_fsm/core.py`; blocking mypy and the slot audit both passed.

## User Setup Required

None — no external service configuration is required.

## Next Phase Readiness

The canonical mode carrier and synchronous construction/runtime path are ready for Plan 02's timing, priority, failure, and lifecycle-depth matrix. Async/cancellation and native parity remain intentionally owned by Plan 03.

## Self-Check: PASSED

- All six planned source/test artifacts exist and the four task commits are present in Git history.
- Focused sync, construction, property, builder, lifecycle, blocking mypy, Ruff, and slots-policy checks passed.

---
*Phase: 28-same-state-transition-modes*
*Completed: 2026-09-17*
