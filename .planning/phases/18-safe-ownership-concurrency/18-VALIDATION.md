---
phase: 18
slug: safe-ownership-concurrency
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-09-01
---

# Phase 18 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.1 with pytest-asyncio |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `uv run pytest tests/test_ownership_concurrency.py -x -q` |
| **Full suite command** | `uv run python tools/phase16_isolated_verify.py --suite phase18` |
| **Estimated runtime** | Targeted ownership suite under 30 seconds; fresh pure/compiled gate several minutes |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/test_ownership_concurrency.py -x -q` plus the exact touched legacy module.
- **After ownership layout or public-write changes:** Run `uv run pytest tests/test_ownership_concurrency.py tests/test_mypyc_guard.py tests/test_transition_lifecycle.py -x -q` and `task typecheck-mypy`.
- **After every plan wave:** Run the ownership, lifecycle, async, advanced, listener, builder, boundary, slots, and performance selection.
- **Before `$gsd-verify-work`:** Run the Phase 18 fresh pure/compiled suite, full sequential suite, Ruff, mypy, docs, doctests, slots, performance floors, and baseline freshness, then require an exact implementation-SHA hosted Python 3.10–3.14 native ownership matrix to finish successfully. A queued or running workflow is not success.
- **Max feedback latency:** 30 seconds for the targeted ownership loop.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 18-01-01 | 01 | 0 | OWN-01–07 | T-18-01–08 | Compile-first native representation and production sync-trigger tracer | native probe + threaded integration | `uv run python tools/phase18_native_probe.py --build-mode compiled --assert-native` plus the focused tracer selection | ❌ W0 | ⬜ pending |
| 18-01-02/03 | 01 | 0 | OWN-01–07 | T-18-01–08 | Complete strict-RED inventory, staged structural/fresh-origin harness, SPR, and tracer performance evidence | contract/structural/performance | `uv run pytest tests/test_ownership_concurrency.py tests/test_mypyc_guard.py tests/test_performance_benchmarks.py -x -q -k 'contract_inventory or staged_writer_inventory or tracer or trigger_min_throughput'` | ❌ W0 | ⬜ pending |
| 18-02-01/02 | 02 | 1 | OWN-01, OWN-02, OWN-05, OWN-06 | T-18-01,02,06,08 | Remove Plan 02 strict xfails, prove RED, then implement sync trigger/control ownership | threaded integration | `uv run pytest tests/test_ownership_concurrency.py tests/test_transition_lifecycle.py tests/test_advanced_functionality.py -x -q -k 'sync or force or reset or restore'` | mixed | ⬜ pending |
| 18-03-01/02 | 03 | 2 | OWN-03, OWN-04, OWN-06, OWN-07 | T-18-01–04,07,08 | Remove Plan 03 strict xfails, prove RED, then implement loop/task/causal/mixed-mode ownership | async integration | `uv run pytest tests/test_ownership_concurrency.py tests/test_async.py -x -q -k 'same_loop or cross_loop or causal or cancellation or inline'` | mixed | ⬜ pending |
| 18-04-01/02 | 04 | 3 | OWN-01, OWN-02, OWN-05, OWN-06 | T-18-01,02,05,08 | Remove Plan 04 strict xfails and tighten staged writer inventory into full one-entry AST enforcement | behavior + structural | `uv run pytest tests/test_ownership_concurrency.py tests/test_mypyc_guard.py tests/test_listeners.py tests/test_builder.py -x -q -k 'write_family or registration or ownership'` | mixed | ⬜ pending |
| 18-05-01/02 | 05 | 4 | OWN-01, OWN-04, OWN-05, OWN-06 | T-18-01,05–08 | Remove final strict xfails, preserve safe-trigger boundary, and replace declarative marker | conformance/security | `uv run pytest tests/test_ownership_concurrency.py tests/test_boundary_negative.py tests/test_transition_lifecycle.py tests/test_mypyc_guard.py -x -q -k 'safe_trigger or declarative or ownership'` | mixed | ⬜ pending |
| 18-06-01/02 | 06 | 5 | OWN-01–07 | T-18-01–09 | Public docs, maintainer architecture/testing guidance, and ADR agree | docs/doctest | `uv run sphinx-build -b html docs docs/_build/html -W --keep-going && uv run sphinx-build -b doctest docs docs/_build/doctest` | ✅ | ⬜ pending |
| 18-07-01/02 | 07 | 6 | OWN-01–07 | T-18-01–09 | Final pure/native harness, performance, slots, baseline, and CI structure pass | release conformance | `uv run python tools/phase16_isolated_verify.py --suite phase18` | mixed | ⬜ pending |
| 18-07-03 | 07 | 6 | OWN-01–07 | T-18-01–09 | Hosted supported-version native ownership matrix succeeds for the exact implementation SHA | hosted CI | `gh run view <run-id> --json headSha,conclusion,jobs` with exact SHA and `success` assertions | external | ⬜ pending |

---

## Wave 0 Requirements

- [ ] `tests/test_ownership_concurrency.py` — authoritative OWN-01 through OWN-07 case inventory. Implemented tracer rows run normally; every Plan 18-02 through 18-05 row is an executable `xfail(strict=True)` RED contract whose reason names its owning plan.
- [ ] `tools/phase18_native_probe.py` — minimal proposed lock/slot/loop/task/root/ContextVar/admission-gate representation compiled and imported natively on the current interpreter before production representation expansion.
- [ ] `.github/workflows/ci.yml` — Python 3.10–3.14 native-probe matrix contract; hosted success is deferred only as evidence, not treated as passed in Wave 0.
- [ ] `tools/phase16_isolated_verify.py` — backward-compatible Phase 18 suite with explicit ownership overlay inventory and asserted pure/freshly compiled origins.
- [ ] `tests/test_performance_benchmarks.py` — uncontended ownership overhead plus retained compiled `trigger()` floor of 200,000 operations/second.
- [ ] `tests/test_mypyc_guard.py` — tracer ownership slots/private body, no shared mutable registry, complete writer-name/owner-plan inventory, single mypyc unit, and supported-Python matrix/probe guards. Full writer-body one-entry enforcement is activated in Plan 18-04.
- [ ] Compatibility behavior for `tests/test_transition_lifecycle.py`, `tests/test_advanced_functionality.py`, `tests/test_listeners.py`, `tests/test_builder.py`, `tests/test_async.py`, and `tests/test_boundary_negative.py` is represented by strict RED rows; each owning plan removes only its markers, observes RED, and implements GREEN.

No new test framework, runtime dependency, timing sleeps, or worker-thread callback fixture is required.

### Strict RED Removal Protocol

1. Wave 0 asserts every future case has exactly one owner in Plans 18-02 through 18-05 and is marked `xfail(strict=True, reason="RED until Plan 18-0N")`; an XPASS is a failure.
2. At the start of each owning task, remove only that task's markers and run its focused selection. The run must fail on the behavior assertion before production changes.
3. Implement until that focused selection passes, leaving later plans' strict-xfail rows intact.
4. Plan 18-04 replaces the staged writer-name inventory with full public-writer admission/delegation enforcement. Plan 18-05 must end with no remaining strict-xfail ownership rows.

---

## Required Scenario Families

- Direct and callback-originated reentry for every public write family, with admission rejected before preparation and no nested mutation.
- Two independent sync threads on one machine serialize a full lifecycle; two machines do not share a lock; all release paths admit the next caller.
- Independent same-loop tasks serialize while a heartbeat proves loop responsiveness; callback-created child tasks reject causally instead of deadlocking.
- First-use loop binding, same-loop reuse, foreign-loop and closed-loop rejection, and cancellation both while waiting and while owning.
- State/history truth at every Phase 17 pre/post-commit exception, `KeyboardInterrupt`, `SystemExit`, and cancellation boundary.
- `safe_trigger()` preserves ordinary exception conversion but lets ownership precondition `RuntimeError` escape.
- Declarative prepared-guard markers are context-local and machine-qualified across concurrent threads, tasks, and independent machines.
- Synchronous async-machine callbacks execute on the loop thread inline; asynchronous callbacks retain the locked Phase 17 slots; no implicit executor or `to_thread` path exists.
- One parameterized scenario table runs against asserted pure and freshly compiled origins, with slots, O(1), and throughput evidence.

---

## Manual-Only Verifications

All Phase 18 behavior is automatable. Platform-wide Python 3.10–3.14 compiled compatibility is enforced by CI/build commands and an exact-SHA `gh` status assertion rather than manual inspection; pending, queued, cancelled, skipped, or stale-SHA runs fail the phase gate.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verification or Wave 0 dependencies.
- [ ] Sampling continuity: no three consecutive tasks without automated verification.
- [ ] Wave 0 covers every missing test/harness reference.
- [ ] No watch-mode flags or timing sleeps.
- [ ] Pure and compiled origins are asserted before ownership semantics run.
- [ ] Cross-loop tests use isolated loop threads and deterministic handshakes.
- [ ] Compiled `trigger()` remains at or above 200,000 operations/second.
- [ ] The exact implementation SHA has a successful hosted Python 3.10–3.14 native ownership matrix; pending is not accepted.
- [ ] `nyquist_compliant: true` is set only after validation audit.

**Approval:** pending
