---
phase: 16
slug: canonical-graph-dispatch-invariants
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-08-29
---

# Phase 16 — Validation Strategy

> Per-phase validation contract for fast feedback while canonical topology and dispatch seams change.

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.1; pytest-asyncio 1.3+; Hypothesis 6.136+; Ruff; mypy/mypyc; Phase 15 release evidence |
| **Config file** | `pyproject.toml`, `Taskfile.yml`, `uv.lock` |
| **Quick run command** | `uv run pytest tests/test_graph_invariants.py tests/test_builder.py tests/test_async.py tests/test_safety_kwargs.py tests/test_advanced_functionality.py -x -q` |
| **Full suite command** | `FAST_FSM_BUILD_MODE=pure task release-gate` |
| **Estimated runtime** | targeted checks <30 seconds; full clean release gate environment-dependent |

## Sampling Rate

- **After every task commit:** run the narrowest requirement-linked command below; any `core.py` change also runs `task typecheck-mypy`.
- **After every plan wave:** run all Phase 16 targeted files sequentially and the pure-source origin preflight.
- **Before goal verification:** run the full pure release gate, then the planned compiled build/behavior/performance comparison from a clean artifact context.
- **Max local feedback latency:** target <30 seconds for task checks; full pure/compiled gates are explicit wave/final exceptions.

## Requirement Verification Map

| Requirement | Expected Secure/Observable Behavior | Test Type | Automated Command | File Exists | Status |
|-------------|-------------------------------------|-----------|-------------------|-------------|--------|
| GRAF-01 | Unknown/foreign endpoints and invalid multi-source additions reject atomically without graph/version/current-state drift. | unit + property sequence | `uv run pytest tests/test_graph_invariants.py -x -q -k endpoint` | ❌ Wave 0 | ⬜ pending |
| GRAF-02 | Same-object registration is idempotent; a different object with the same name fails without mutation. | unit + property sequence | `uv run pytest tests/test_graph_invariants.py -x -q -k registry` | ❌ Wave 0 | ⬜ pending |
| GRAF-03 | One fresh snapshot exposes declared initial state, canonical endpoints, stable sorting, structural immutability, and monotonic graph version. | unit | `uv run pytest tests/test_graph_invariants.py -x -q -k snapshot` | ❌ Wave 0 | ⬜ pending |
| GRAF-04 | Successful build freezes every mutator, repeated build returns the same object, and failed build remains repairable with no partial cache. | unit | `uv run pytest tests/test_builder.py -x -q -k "freeze or repair or idempotent"` | ✅ extend | ⬜ pending |
| GRAF-05 | Nested async leaves under built-in wrappers are detected and awaited with short-circuit/cycle safety; explicit sync fails. | sync/async unit | `uv run pytest tests/test_builder.py tests/test_async.py -x -q -k "nested or wrapper or cycle"` | ✅ extend | ⬜ pending |
| GRAF-06 | `*args` and filter-then-cap sanitized kwargs match across sync/async `can_trigger*` and `trigger*`, without caller mutation. | paired sync/async unit | `uv run pytest tests/test_safety_kwargs.py tests/test_async.py -x -q -k "guard or sanit"` | ✅ extend | ⬜ pending |
| GRAF-07 | Ordinary sync/async dispatch invokes the matched declarative handler exactly once and compatibility helpers do not duplicate it. | paired integration | `uv run pytest tests/test_builder.py tests/test_async.py -x -q -k declarative` | ✅ extend | ⬜ pending |
| GRAF-08 | Shared private seams retain public symbols, one `core.py` compilation unit, and pure/compiled semantic compatibility. | structural + integration | `uv run pytest tests/test_mypyc_guard.py tests/test_graph_invariants.py -x -q` plus `task typecheck-mypy` | partial; graph file Wave 0 | ⬜ pending |
| LIFE-07 | Non-positive capacity fails before mutation; bounded FIFO eviction is O(1), chronological, reset-on-enable, and copy-on-read. | unit + performance | `uv run pytest tests/test_advanced_functionality.py tests/test_performance_benchmarks.py -x -q -k history` | ✅ extend | ⬜ pending |

## Wave 0 Requirements

- [ ] `tests/test_graph_invariants.py` — canonical registry, endpoint transaction, graph version, immutable snapshot, and graph-fingerprint regression coverage for GRAF-01/02/03/08.
- [ ] Test-only graph fingerprint helper — records registry object identities, transition endpoint/guard identities, version, current state, and snapshot so rejected calls prove non-mutation.
- [ ] Recording sync/async condition fixtures — accept `*args, **kwargs` and expose received identity/order without mocking dispatch.
- [ ] Cycle fixtures for supported built-in condition wrappers — constructed privately in tests without creating a public wrapper protocol.
- [ ] Compiled structural guards for any new hot-path record/container type while retaining only `core.py` as the mypyc source input.

## Manual-Only Verifications

None. Every Phase 16 behavior, compilation boundary, and performance contract must have automated local or hosted evidence.

## Validation Sign-Off

- [ ] Every final plan task maps to a focused automated command or an explicit Wave 0 prerequisite.
- [ ] No three consecutive implementation tasks lack automated feedback.
- [ ] Wave 0 creates every missing graph/fixture reference before dependent implementation.
- [ ] Sync/async parity cases exercise both `can_trigger*()` and `trigger*()` with positional and sanitized keyword context.
- [ ] Pure and compiled gates establish module origin before behavior/performance collection.
- [ ] `nyquist_compliant: true` is set only after post-execution validation audit.

**Approval:** pending plan checker and post-execution `$gsd-validate-phase 16`
