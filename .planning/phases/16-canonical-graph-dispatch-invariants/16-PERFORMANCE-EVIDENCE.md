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

## Post-Semantic Clean Pure Baseline

- Collected: 2026-08-30
- Committed tree: `07b655e` (`fix(16-05): isolate full phase evidence inventory`)
- Context: a committed-HEAD export with the explicit Phase 16 overlay inventory
  in `tools/phase16_isolated_verify.py`: `core.py`, interpreted condition
  modules, graph/builder/async/guard/template/history/performance/mypyc tests,
  the core SPR, both maintainer guides, baseline manifest, and this evidence
  record.
- Build intent and asserted origin: `FAST_FSM_BUILD_MODE=pure` selected before
  locked setup; `fast_fsm.core` resolved to `src/fast_fsm/core.py` before
  release evidence collection.

### Commands and Results

```bash
uv run python tools/phase16_isolated_verify.py \
  --suite baseline-write --manifest-output evidence/release-baseline.json
uv run python tools/phase16_isolated_verify.py --suite baseline-check
```

The write suite completed from the asserted pure temporary archive and copied
only the generated manifest back atomically. The second command created a new
asserted-pure archive, overlaid the committed manifest, and passed read-only
freshness without changing it.

| Observation | Result |
| --- | --- |
| Pure semantic inventory | 985 collected / 985 passed / 0 failed / 0 errors / 0 skipped |
| Source coverage | 96.01% total; 93.94% `core.py` |
| Source origin | `src/fast_fsm/core.py` |
| Wheel evidence | `fast_fsm-0.2.2-py3-none-any.whl`; pure tags only; no native members |
| Slots audit | Passed; added slot-protected `_GraphTransition`, `_GraphSnapshot`, `_PreparedTransition`, and `_PreparedDispatch` to the reviewed inventory |
| Pure trigger observation | 795,843.04 ops/s across 40,000 operations after 2,000 warmups (CPython 3.12.10, arm64 macOS) |

### Reviewed Manifest Delta

Compared with the prior Phase 15 baseline, the exact suite grew from 879 to
985 passing tests and coverage moved from 95.75% total / 92.95% core to
96.01% total / 93.94% core. The pure source origin, wheel identity,
schema, package/build pins, zero failures/errors, and 200,000 ops/s compiled
policy floor stayed unchanged. The timing observation changed only as an
environment-labelled measurement, from 951,787.04 to 795,843.04 ops/s; it is
not a freshness field.

### Evidence-Integrity Correction

Plan text referred to `--export-baseline`, but the committed helper exposes
`--manifest-output`; the current interface was used. During this task the
helper was also corrected to overlay both Phase 16 maintainer guides and the
baseline manifest during isolated collection. This closes the working-tree
docs/evidence provenance gap without importing or deleting developer native
shadows.
