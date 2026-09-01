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
- **Before `$gsd-verify-work`:** Run the Phase 18 fresh pure/compiled suite, cross-version compile checks, full sequential suite, Ruff, mypy, docs, doctests, slots, performance floors, and baseline freshness.
- **Max feedback latency:** 30 seconds for the targeted ownership loop.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 18-01-01 | 01 | 0 | OWN-01–07 | T-18-01–08 | Deterministic matrix covers reentry, serialization, loop binding, every write family, cleanup, and inline callbacks | unit/integration | `uv run pytest tests/test_ownership_concurrency.py -x -q` | ❌ W0 | ⬜ pending |
| 18-02-01 | 02 | 1 | OWN-01, OWN-02, OWN-05, OWN-06 | T-18-01–04 | Per-machine sync ownership rejects same-owner calls and releases through every throwable | threaded integration | `uv run pytest tests/test_ownership_concurrency.py tests/test_transition_lifecycle.py -x -q -k 'reentrant or thread or release or write_family'` | mixed | ⬜ pending |
| 18-03-01 | 03 | 2 | OWN-03, OWN-04, OWN-06, OWN-07 | T-18-02, T-18-05–07 | Loop-native task serialization never blocks the loop and rejects causal/cross-loop misuse | async integration | `uv run pytest tests/test_ownership_concurrency.py tests/test_async.py -x -q -k 'same_loop or cross_loop or cancellation or callback'` | mixed | ⬜ pending |
| 18-04-01 | 04 | 3 | OWN-01–07 | T-18-01–08 | Shared marker removal, safe-trigger preconditions, docs, slots, types, and fresh origins agree | conformance/security | `uv run python tools/phase16_isolated_verify.py --suite phase18` | ❌ W0 | ⬜ pending |

Task identifiers are provisional until the planner writes executable plans; the planner must preserve equivalent coverage when assigning final IDs.

---

## Wave 0 Requirements

- [ ] `tests/test_ownership_concurrency.py` — authoritative OWN-01 through OWN-07 matrix using `threading.Event`, barriers, `asyncio.Event`, and explicit task handshakes; no timing sleeps.
- [ ] `tools/phase16_isolated_verify.py` — backward-compatible Phase 18 suite with explicit ownership overlay inventory and asserted pure/freshly compiled origins.
- [ ] `tests/test_performance_benchmarks.py` — uncontended ownership overhead plus retained compiled `trigger()` floor of 200,000 operations/second.
- [ ] `tests/test_mypyc_guard.py` — ownership slots, no shared mutable registry, one-entry/private-body structure, and supported Python/mypyc compilation guards.
- [ ] Compatibility updates in `tests/test_transition_lifecycle.py`, `tests/test_advanced_functionality.py`, `tests/test_listeners.py`, `tests/test_builder.py`, `tests/test_async.py`, and `tests/test_boundary_negative.py` for ownership admission and `safe_trigger()`.

No new test framework, runtime dependency, timing sleeps, or worker-thread callback fixture is required.

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

All Phase 18 behavior is automatable. Platform-wide Python 3.10–3.14 compiled compatibility is enforced by CI/build commands rather than manual inspection.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verification or Wave 0 dependencies.
- [ ] Sampling continuity: no three consecutive tasks without automated verification.
- [ ] Wave 0 covers every missing test/harness reference.
- [ ] No watch-mode flags or timing sleeps.
- [ ] Pure and compiled origins are asserted before ownership semantics run.
- [ ] Cross-loop tests use isolated loop threads and deterministic handshakes.
- [ ] Compiled `trigger()` remains at or above 200,000 operations/second.
- [ ] `nyquist_compliant: true` is set only after validation audit.

**Approval:** pending
