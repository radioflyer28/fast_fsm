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
| **Quick run command** | `uv run python tools/phase16_isolated_verify.py --mode task --build-mode pure --include src/fast_fsm/core.py --include src/fast_fsm/conditions.py --include src/fast_fsm/condition_templates.py --include tests/test_graph_invariants.py --include tests/test_builder.py --include tests/test_async.py --include tests/test_safety_kwargs.py --include tests/test_condition_templates.py --include tests/test_advanced_functionality.py --include tests/test_mypyc_guard.py -- uv run pytest tests/test_graph_invariants.py tests/test_builder.py tests/test_async.py tests/test_safety_kwargs.py tests/test_condition_templates.py tests/test_advanced_functionality.py tests/test_mypyc_guard.py -x -q` |
| **Full suite command** | `uv run python tools/phase16_isolated_verify.py --suite phase16` |
| **Estimated runtime** | targeted checks <30 seconds; full clean release gate environment-dependent |

## Sampling Rate

- **After every Python-changing task commit:** run `uv run ruff format <owned-python-files>`, then `uv run ruff check --fix <owned-python-files>`, then `uv run ruff check <owned-python-files>`; run the narrowest requirement-linked semantic command below through helper task mode with every current task source/test file explicitly included, and run blocking `task typecheck-mypy` for any `core.py` change.
- **After every plan wave:** run all Phase 16 targeted files sequentially through helper task mode; the helper creates a shadow-free asserted-pure temporary context from committed HEAD plus the explicit current-working-tree overlays.
- **Before goal verification:** run `uv run python tools/phase16_isolated_verify.py --suite phase16` and blocking `task typecheck-mypy`. The separately named advisory type-check evidence is collected only by Plan 16-05 Task 3 with stdout, stderr, and exit status recorded without gating completion.
- **Max local feedback latency:** target <30 seconds for task checks; full pure/compiled gates are explicit wave/final exceptions.

## Requirement Verification Map

| Requirement | Expected Secure/Observable Behavior | Test Type | Automated Command | File Exists | Status |
|-------------|-------------------------------------|-----------|-------------------|-------------|--------|
| GRAF-01 | Unknown/foreign endpoints, batches, bidirectional second-leg failures, and emergency all-source additions are preflighted atomically without graph/version/current-state drift. | unit + property sequence | `uv run python tools/phase16_isolated_verify.py --mode task --build-mode pure --include src/fast_fsm/core.py --include tests/test_graph_invariants.py -- uv run pytest tests/test_graph_invariants.py -x -q -k "endpoint or atomic or batch or bidirectional or emergency"` | ❌ Wave 0 | ⬜ pending |
| GRAF-02 | Runtime and builder staging treat the same object idempotently; a distinct same-name object raises ValueError without staged/cache/eventual-topology mutation. | unit + property sequence | `uv run python tools/phase16_isolated_verify.py --mode task --build-mode pure --include src/fast_fsm/core.py --include tests/test_graph_invariants.py --include tests/test_builder.py -- uv run pytest tests/test_graph_invariants.py tests/test_builder.py -x -q -k "registry or same_name or staging_identity"` | ❌ Wave 0 + extend builder | ⬜ pending |
| GRAF-03 | One fresh snapshot exposes declared initial state, canonical endpoints, stable sorting, structural immutability, and monotonic graph version. | unit | `uv run python tools/phase16_isolated_verify.py --mode task --build-mode pure --include src/fast_fsm/core.py --include tests/test_graph_invariants.py -- uv run pytest tests/test_graph_invariants.py -x -q -k snapshot` | ❌ Wave 0 | ⬜ pending |
| GRAF-04 | Successful build freezes every mutator, repeated build returns the same object, and failed build remains repairable with no partial cache. | unit | `uv run python tools/phase16_isolated_verify.py --mode task --build-mode pure --include src/fast_fsm/core.py --include tests/test_builder.py -- uv run pytest tests/test_builder.py -x -q -k "freeze or repair or idempotent"` | ✅ extend | ⬜ pending |
| GRAF-05 | Nested async leaves under built-in wrappers are detected and awaited with short-circuit/cycle safety; explicit sync fails. | sync/async unit | `uv run python tools/phase16_isolated_verify.py --mode task --build-mode pure --include src/fast_fsm/core.py --include src/fast_fsm/conditions.py --include src/fast_fsm/condition_templates.py --include tests/test_builder.py --include tests/test_async.py -- uv run pytest tests/test_builder.py tests/test_async.py -x -q -k "nested or wrapper or cycle"` | ✅ extend | ⬜ pending |
| GRAF-06 | `*args` and filter-then-cap sanitized kwargs match across sync/async `can_trigger*()` and `trigger*()` paths without caller mutation. | paired sync/async unit | `uv run python tools/phase16_isolated_verify.py --mode task --build-mode pure --include src/fast_fsm/core.py --include src/fast_fsm/conditions.py --include src/fast_fsm/condition_templates.py --include tests/test_safety_kwargs.py --include tests/test_async.py -- uv run pytest tests/test_safety_kwargs.py tests/test_async.py -x -q -k "guard or sanit"` | ✅ extend | ⬜ pending |
| GRAF-07 | Ordinary sync/async dispatch invokes matched declarative handlers exactly once, including count-only false/invalid/raising cases that assert no Phase 17 outcome/state/order/history/commit semantics. | paired integration | `uv run python tools/phase16_isolated_verify.py --mode task --build-mode pure --include src/fast_fsm/core.py --include tests/test_builder.py --include tests/test_async.py -- uv run pytest tests/test_builder.py tests/test_async.py -x -q -k "declarative and (exactly_once or invocation_only)"` | ✅ extend | ⬜ pending |
| GRAF-08 | Shared private seams retain public symbols, one `core.py` compilation unit, and pure/compiled semantic compatibility. | structural + isolated integration | `uv run python tools/phase16_isolated_verify.py --suite phase16` plus blocking `task typecheck-mypy`; advisory type-check output is recorded separately by Plan 16-05 and is not part of this gate | ❌ Wave 0 helper | ⬜ pending |
| LIFE-07 | Non-positive capacity fails before mutation; bounded FIFO eviction is O(1), chronological, reset-on-enable, and copy-on-read. | unit + performance | `uv run python tools/phase16_isolated_verify.py --mode task --build-mode compiled --include src/fast_fsm/core.py --include tests/test_advanced_functionality.py --include tests/test_performance_benchmarks.py -- uv run pytest tests/test_advanced_functionality.py tests/test_performance_benchmarks.py -x -q -k history` | ✅ extend | ⬜ pending |

## Wave 0 Requirements

- [ ] `tests/test_graph_invariants.py` — canonical registry, endpoint transaction, graph version, immutable snapshot, and graph-fingerprint regression coverage for GRAF-01/02/03/08.
- [ ] `graph_fingerprint()` — records registry object identities, transition endpoint/guard identities, version, current state, and snapshot so rejected calls prove non-mutation.
- [ ] `builder_staging_fingerprint()` — records staged state/transition/callback identities, builder mode/cache, and eventual machine topology for GRAF-02/D-01 builder rejection checks.
- [ ] `RecordingCondition`, `RecordingAsyncCondition`, and `ShortCircuitCondition` — accept `*args, **kwargs` and expose received identity/order/call count without mocking dispatch.
- [ ] `make_negated_cycle()`, `make_and_cycle()`, `make_or_cycle()`, `make_not_cycle()`, and `make_shared_condition_dag()` — private cycle/DAG fixtures with ValueError cycle behavior.
- [ ] `DeclarativeInvocationCounter`, `AsyncDeclarativeInvocationCounter`, and `_invoke_and_ignore_phase17_outcome()` — count-only false/invalid/raising handler coverage with all Phase 17 result/state/order/history/commit observations discarded.
- [ ] `tools/phase16_isolated_verify.py` — created before the first semantic import; task mode exports committed HEAD, overlays explicitly named current-working-tree files including uncommitted changes, selects pure or compiled mode before locked setup, asserts `.py` or native origin, and runs the caller command only inside the temporary context. Fixed graph/baseline-write/baseline-check/phase16 suites add fail-closed native build, shared semantics, compiled trigger/history gates, isolated baseline freshness, and the full pure release gate.
- [ ] Compiled structural guards for any new hot-path record/container type while retaining only `core.py` as the mypyc source input.

## Manual-Only Verifications

None. Every Phase 16 behavior, compilation boundary, and performance contract must have automated local or hosted evidence.

## Validation Sign-Off

- [ ] Every final plan task maps to a focused automated command or an explicit Wave 0 prerequisite.
- [ ] No three consecutive implementation tasks lack automated feedback.
- [ ] Wave 0 creates every missing graph/fixture reference before dependent implementation.
- [ ] Sync/async parity cases exercise both `can_trigger*()` and `trigger*()` with positional and sanitized keyword context.
- [ ] Pure and compiled gates use separate temporary contexts, overlay the exact task/current Phase 16 working-tree files, and establish module origin before behavior/performance collection.
- [ ] Every Python-changing task runs Ruff format, Ruff check --fix, Ruff validation, focused tests, and blocking mypy where core/signatures change; final advisory ty remains separate.
- [ ] `nyquist_compliant: true` is set only after post-execution validation audit.

**Approval:** pending plan checker and post-execution `$gsd-validate-phase 16`
