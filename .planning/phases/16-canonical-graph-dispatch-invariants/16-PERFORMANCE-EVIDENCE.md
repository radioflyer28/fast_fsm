---
phase: 16
plan: 01
status: before-change
---

# Phase 16 Plan 01 — Before-Change Performance Evidence

This record captures environment-labelled observations before canonical graph
semantics change. Each observation is collected by
`tools/phase16_isolated_verify.py` from a fresh export of committed `HEAD` plus
only the listed working-tree overlays. The developer checkout's native shadows
are not imported, deleted, or used as evidence.

## Environment

- Collected: 2026-08-30
- Committed baseline tree: `31f90e5` (`docs(16): create phase plan`)
- Python: CPython 3.12.10 (arm64 macOS)
- Runner: `tools/phase16_isolated_verify.py` task mode, with only this evidence
  record and the runner overlaid onto the exported committed tree.

## Observations

| Build mode | Asserted `fast_fsm.core` origin | Targeted transition baseline | `trigger()` observation | History disabled |
| --- | --- | --- | ---: | --- |
| pure | `src/fast_fsm/core.py` | pass | 851,576 ops/s | yes |
| compiled | `src/fast_fsm/core.cpython-312-darwin.so` | pass | 1,054,438 ops/s | yes |

The two-state `quick_build()` toggle was warmed for 1,000 transitions and then
measured across 100,000 alternating `trigger()` calls. These are labelled local
observations, not a new policy threshold. The selected contexts created distinct
temporary repositories; the developer checkout's native artifacts were neither
deleted nor imported.
