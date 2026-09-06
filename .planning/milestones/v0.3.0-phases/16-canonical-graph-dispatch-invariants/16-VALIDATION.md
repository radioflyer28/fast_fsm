---
phase: 16
slug: canonical-graph-dispatch-invariants
status: validated
nyquist_compliant: true
wave_0_complete: true
created: 2026-08-29
validated: 2026-09-01
---

# Phase 16 — Validation Strategy

> Executed Nyquist validation map for canonical topology, shared dispatch,
> transactional builder publication, declarative invocation, and bounded history.

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.1; pytest-asyncio 1.3.0; Hypothesis 6.138.8; Ruff 0.12.11; mypy/mypyc 1.17.1; Phase 15 release evidence |
| **Config files** | `pyproject.toml`, `Taskfile.yml`, `uv.lock` |
| **Focused source-origin runner** | `uv run python tools/phase16_isolated_verify.py --mode task --build-mode pure\|compiled --include PATH ... -- COMMAND` |
| **Authoritative command** | `uv run python tools/phase16_isolated_verify.py --suite phase16` |
| **Observed result** | Exit 0 on 2026-09-01: pure and freshly compiled Phase 16 semantic matrices green; compiled trigger/history gates green; pure release gate green with 1,221/1,221 tests, 96.64% total coverage, and 95.13% `core.py` coverage |

## Requirement-to-Test Map

Every focused behavior below was executed by the authoritative command in separate
asserted-pure and freshly compiled temporary trees where applicable. The command
also ran the compiled performance selection and the complete pure release gate.

| Requirement | Plan tasks | Behavioral evidence | Type | Command | Status |
|-------------|------------|---------------------|------|---------|--------|
| GRAF-01 | 16-01 T1/T2; 16-05 T3 | `tests/test_graph_invariants.py`: exact/unknown/foreign/null endpoints, empty/duplicate/later-invalid batches, bidirectional second-leg rejection, emergency all-source atomicity, and full graph fingerprints | unit + integration | `uv run python tools/phase16_isolated_verify.py --suite phase16` | green |
| GRAF-02 | 16-01 T1/T2; 16-03 T1; 16-05 T3 | `tests/test_graph_invariants.py` and `tests/test_builder.py#TestFSMBuilderPublication`: same-object idempotence, distinct same-name/equality-object rejection, unchanged staging/cache/eventual topology | unit + integration | `uv run python tools/phase16_isolated_verify.py --suite phase16` | green |
| GRAF-03 | 16-01 T1/T3; 16-05 T3 | `tests/test_graph_invariants.py`: fresh sorted frozen snapshot, canonical identities, declared initial state, topology-only versioning, clone lineage, unchanged public schemas | unit + structural | `uv run python tools/phase16_isolated_verify.py --suite phase16` | green |
| GRAF-04 | 16-03 T1; 16-05 T3 | `tests/test_builder.py#TestFSMBuilderPublication`: every mutator frozen after success, repeated object identity, cache-last publication, failed-build repair, empty/single/ordered staging | integration | `uv run python tools/phase16_isolated_verify.py --suite phase16` | green |
| GRAF-05 | 16-02 T3; 16-03 T2; 16-05 T3 | `tests/test_async.py#TestAsyncWrapperEvaluation`, `tests/test_builder.py#TestFSMBuilderAsyncPreflight`, and `tests/test_condition_templates.py#TestDirectCompositeAwaitableChecks`: all built-in wrappers, native/custom/generator awaitables, left-to-right short-circuiting, cycles, shared DAGs, deep graphs, explicit modes, and exactly-once awaiting | sync/async integration | `uv run python tools/phase16_isolated_verify.py --suite phase16` | green |
| GRAF-06 | 16-02 T1/T2/T3; 16-05 T3 | `tests/test_safety_kwargs.py#TestGuardContextParity`, `TestDeclarativeGuardContextParity`, and positional wrapper tests: four can/do paths, positional identity, filter-before-cap order, fresh mappings, caller preservation, no unnecessary preparation | paired sync/async unit | `uv run python tools/phase16_isolated_verify.py --suite phase16` | green |
| GRAF-07 | 16-04 T1; 16-05 T3 | sync cases in `tests/test_builder.py` and `tests/test_async.py#TestAsyncOrdinaryDeclarativeDispatch`: canonical from/trigger/to matching, helper delegation, successful normalization, and invocation-count-only false/invalid/raising cases | paired integration | `uv run python tools/phase16_isolated_verify.py --suite phase16` | green |
| GRAF-08 | 16-01 T3; 16-02 T2/T3; 16-03 T2; 16-04 T1/T2; 16-05 T1/T3 | `tests/test_mypyc_guard.py`, the complete semantic matrix, slots policy, export/signature guards, one-core-file compilation, asserted pure/native origins, Ruff, mypy, Sphinx, doctests, and baseline freshness | structural + isolated integration | `uv run python tools/phase16_isolated_verify.py --suite phase16` | green |
| LIFE-07 | 16-04 T2; 16-05 T3 | `tests/test_advanced_functionality.py#TestTransitionHistory`, `tests/test_async.py#TestAsyncHistory`, and performance tests: invalid-capacity preservation, reset-on-enable, capacity one, bounded FIFO chronology, defensive copies, disabled/clone behavior, and O(1) steady-state eviction | unit + performance | `uv run python tools/phase16_isolated_verify.py --suite phase16` | green |

## Per-Task Verification Map

| Task ID | Requirements | Focused artifact/behavior | Automated command | Status |
|---------|--------------|---------------------------|-------------------|--------|
| 16-01-T1 | GRAF-01, GRAF-02, GRAF-03, GRAF-08 | Canonical registration through immutable versioned snapshot | `uv run python tools/phase16_isolated_verify.py --suite graph` | green |
| 16-01-T2 | GRAF-01, GRAF-02 | Complete endpoint/batch/helper preflight and atomic commit | `uv run python tools/phase16_isolated_verify.py --suite phase16` | green |
| 16-01-T3 | GRAF-03, GRAF-08 | Frozen slot records, private exports, one mypyc unit, pure/native origin | `uv run python tools/phase16_isolated_verify.py --suite graph` | green |
| 16-02-T1 | GRAF-06, GRAF-08 | Shared four-path guard preparation and filter-then-cap context | `uv run python tools/phase16_isolated_verify.py --suite phase16` | green |
| 16-02-T2 | GRAF-06, GRAF-08 | Interpreted condition positional forwarding and sync short-circuiting | `uv run python tools/phase16_isolated_verify.py --suite phase16` | green |
| 16-02-T3 | GRAF-05, GRAF-06, GRAF-08 | Recursive machine evaluation plus direct composite awaitable ownership | `uv run python tools/phase16_isolated_verify.py --suite phase16` | green |
| 16-03-T1 | GRAF-02, GRAF-04, GRAF-08 | Builder identity staging, cache-last publication, freeze, and repair | `uv run python tools/phase16_isolated_verify.py --suite phase16` | green |
| 16-03-T2 | GRAF-04, GRAF-05, GRAF-08 | Nested async preflight, explicit modes, cycles/DAGs, real async execution | `uv run python tools/phase16_isolated_verify.py --suite phase16` | green |
| 16-04-T1 | GRAF-07, GRAF-08 | Canonical declarative matching and exactly-once invocation | `uv run python tools/phase16_isolated_verify.py --suite phase16` | green |
| 16-04-T2 | GRAF-08, LIFE-07 | Validated bounded deque history and compiled performance | `uv run python tools/phase16_isolated_verify.py --suite phase16` | green |
| 16-05-T1 | GRAF-01–08, LIFE-07 | Maintainer contract and deferred-scope documentation | `uv run python tools/phase16_isolated_verify.py --suite phase16` | green |
| 16-05-T2 | GRAF-08 | Reviewed asserted-pure baseline and read-only freshness | `uv run python tools/phase16_isolated_verify.py --suite baseline-check` | green |
| 16-05-T3 | GRAF-01–08, LIFE-07 | Final pure/native semantic parity, performance, and release gate | `uv run python tools/phase16_isolated_verify.py --suite phase16` | green |

## Wave 0 Completion

- [x] `tests/test_graph_invariants.py` and `graph_fingerprint()` cover canonical registry, atomic mutation, graph version, immutable snapshot, and rejection non-mutation.
- [x] `builder_staging_fingerprint()` covers staged identities, modes, cache, and eventual topology.
- [x] Recording/short-circuit condition fixtures cover argument identity, call order, and cardinality without mocking dispatch.
- [x] Wrapper cycle and shared-DAG fixtures cover every supported built-in edge.
- [x] Declarative invocation counters and the Phase 17 outcome-discard helper isolate exactly-once behavior without leaking deferred lifecycle semantics.
- [x] `tools/phase16_isolated_verify.py` provides fail-closed pure/compiled task and suite modes with explicit overlays and pre-import origin assertions.
- [x] Structural guards retain slots, public exports, interpreted condition modules, and `core.py` as the sole mypyc input.

## Manual-Only Verifications

None. All Phase 16 requirements have executable local evidence. Phase 17 lifecycle
ordering, Phase 18 ownership/concurrency, Phase 19 diagnostic migration/output, and
Phase 20 installed-artifact parity remain explicit later-phase scope, not validation
gaps in Phase 16.

## Validation Sign-Off

- [x] Every Phase 16 task and requirement maps to behavioral automated evidence.
- [x] Every referenced test file exists and exercises observable behavior rather than symbol presence alone.
- [x] Pure and compiled semantic matrices passed in separate temporary trees with asserted module origins.
- [x] Compiled trigger/history performance gates passed, including the 200,000 operations/second trigger floor.
- [x] The pure release gate passed Ruff, blocking mypy, 1,221/1,221 pytest tests, Sphinx warnings-as-errors, three doctests, and baseline freshness.
- [x] No implementation file was modified by this audit.
- [x] No genuine automated gap remained, so no new test file was created.

**Approval:** Nyquist audit passed on 2026-09-01.

## Validation Audit 2026-09-01

| Metric | Count |
|--------|-------|
| Requirements audited | 9 |
| Covered | 9 |
| Partial | 0 |
| Missing | 0 |
| Gaps found | 0 |
| Resolved with new tests | 0 |
| Escalated | 0 |

Authoritative audit command:

```bash
uv run python tools/phase16_isolated_verify.py --suite phase16
```

Observed exit status: `0`.
