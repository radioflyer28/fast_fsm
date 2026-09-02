---
phase: 18
slug: safe-ownership-concurrency
status: validated
nyquist_compliant: true
wave_0_complete: true
created: 2026-09-01
validated: 2026-09-02
audited_candidate_sha: 78650eaf6adcbc1432c9ee9ae970017285ac267b
execution_branch: fix/phase18-security-gap-20260902195848
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
| 18-01-01 | 01 | 0 | OWN-01–07 | T-18-01–08 | Compile-first native representation and production sync-trigger tracer | native probe + threaded integration | `uv run python tools/phase18_native_probe.py --build-mode compiled --assert-native` plus the focused tracer selection | ✅ | green |
| 18-01-02/03 | 01 | 0 | OWN-01–07 | T-18-01–08 | Complete strict-RED inventory, staged structural/fresh-origin harness, SPR, and tracer performance evidence | contract/structural/performance | `uv run pytest tests/test_ownership_concurrency.py tests/test_mypyc_guard.py tests/test_performance_benchmarks.py -x -q -k 'contract_inventory or staged_writer_inventory or tracer or trigger_min_throughput'` | ✅ | green |
| 18-02-01/02 | 02 | 1 | OWN-01, OWN-02, OWN-05, OWN-06 | T-18-01,02,06,08 | Sync trigger/control ownership and release behavior | threaded integration | `uv run pytest tests/test_ownership_concurrency.py tests/test_transition_lifecycle.py tests/test_advanced_functionality.py -x -q -k 'sync or force or reset or restore'` | ✅ | green |
| 18-03-01/02 | 03 | 2 | OWN-03, OWN-04, OWN-06, OWN-07 | T-18-01–04,07,08 | Loop/task/causal/mixed-mode ownership | async integration | `uv run pytest tests/test_ownership_concurrency.py tests/test_async.py -x -q -k 'same_loop or cross_loop or causal or cancellation or inline'` | ✅ | green |
| 18-04-01/02 | 04 | 3 | OWN-01, OWN-02, OWN-05, OWN-06 | T-18-01,02,05,08 | Complete writer inventory and one-entry enforcement | behavior + structural | `uv run pytest tests/test_ownership_concurrency.py tests/test_mypyc_guard.py tests/test_listeners.py tests/test_builder.py -x -q -k 'write_family or registration or ownership'` | ✅ | green |
| 18-05-01/02 | 05 | 4 | OWN-01, OWN-04, OWN-05, OWN-06 | T-18-01,05–08 | Safe-trigger boundary and context-local declarative marker | conformance/security | `uv run pytest tests/test_ownership_concurrency.py tests/test_boundary_negative.py tests/test_transition_lifecycle.py tests/test_mypyc_guard.py -x -q -k 'safe_trigger or declarative or ownership'` | ✅ | green |
| 18-06-01/02 | 06 | 5 | OWN-01–07 | T-18-01–09 | Public docs, maintainer architecture/testing guidance, and ADR agree | docs/doctest | `uv run sphinx-build -b html docs docs/_build/html -W --keep-going && uv run sphinx-build -b doctest docs docs/_build/doctest` | ✅ | green |
| 18-07-01/02 | 07 | 6 | OWN-01–07 | T-18-01–09 | Pure/native harness, performance, slots, baseline, and CI structure | release conformance | `uv run python tools/phase16_isolated_verify.py --suite phase18` | ✅ | green |
| 18-07-03 | 07 | 6 | OWN-01–07 | T-18-01–09 | Hosted supported-version native ownership matrix for the exact implementation SHA | hosted CI | `uv run python tools/phase18_native_probe.py --assert-hosted-ci-sha 78650eaf6adcbc1432c9ee9ae970017285ac267b` | external | green |
| 18-08-01 | 08 | 7 | OWN-05, OWN-06 | T-18-05 | Production-reachable cross-machine declarative consumption uses independently installed consumer identity and restores both contexts | behavioral + structural | `uv run python tools/phase16_isolated_verify.py --suite phase18` (includes the named sync/async regressions and AST guard in asserted pure and freshly compiled origins) | ✅ | green |
| 18-08-02 | 08 | 7 | OWN-01–07 | T-18-03, T-18-05 | Bounded precheck, reviewed 1,379-test baseline, complete local gate, and exact-SHA hosted native matrix | release conformance + hosted CI | 30-second subprocess precheck; `uv run python tools/phase16_isolated_verify.py --suite phase18`; `uv run python tools/phase18_native_probe.py --assert-hosted-ci-sha 78650eaf6adcbc1432c9ee9ae970017285ac267b` | ✅ + external | green |
| 18-08-03 | 08 | 7 | OWN-01–07 | T-18-03, T-18-05 | Read-only security audit, persisted verdict/SHA equality, and candidate-content integrity | audit/persistence integration | SECURITY exact-SHA/status assertions; `git diff --exit-code 78650eaf6adcbc1432c9ee9ae970017285ac267b -- src/fast_fsm/core.py tests/test_ownership_concurrency.py tests/test_mypyc_guard.py tools/phase16_isolated_verify.py tools/phase18_native_probe.py evidence/release-baseline.json` | ✅ | green |

---

## Wave 0 Requirements

- [x] `tests/test_ownership_concurrency.py` — authoritative OWN-01 through OWN-07 inventory, including the Plan 18-08 sync/async cross-machine public-dispatch regressions.
- [x] `tools/phase18_native_probe.py` — native representation, CI contract, and exact-SHA hosted assertion.
- [x] `.github/workflows/ci.yml` — Python 3.10–3.14 native ownership matrix; candidate `78650eaf6adcbc1432c9ee9ae970017285ac267b` passed.
- [x] `tools/phase16_isolated_verify.py` — Phase 18 suite with asserted pure and freshly compiled origins.
- [x] `tests/test_performance_benchmarks.py` — uncontended ownership evidence and compiled `trigger()` floor of 200,000 operations/second.
- [x] `tests/test_mypyc_guard.py` — complete writer, marker-consumer, public-hook signature, mypyc-unit, and supported-matrix structural guards.
- [x] Legacy lifecycle, graph, listener, builder, async, boundary, documentation, type, and release-baseline coverage passes in the authoritative suite.

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

- [x] All tasks have automated verification or completed Wave 0 dependencies.
- [x] Sampling continuity: no three consecutive tasks lack automated verification.
- [x] Wave 0 covers every test/harness reference and Plan 18-08 closes the post-security gap.
- [x] No watch-mode flags or timing sleeps establish correctness.
- [x] Pure and compiled origins are asserted before ownership semantics run.
- [x] Cross-loop tests use isolated loop threads and deterministic handshakes.
- [x] Compiled `trigger()` remains at or above 200,000 operations/second.
- [x] Exact candidate `78650eaf6adcbc1432c9ee9ae970017285ac267b` passed the hosted Python 3.10–3.14 native ownership matrix.
- [x] `nyquist_compliant: true` was set after the independent validation audit.

**Approval:** validated — no automated coverage gaps remain.

---

## Validation Audit 2026-09-02

| Metric | Count |
|--------|-------|
| Coverage gaps found | 0 |
| New Plan 18-08 task rows mapped | 3 |
| Escalated | 0 |

- Bounded precheck: 4 tests passed in 0.38 seconds, within the 30-second limit.
- Fresh targeted origins: 8/8 passed in asserted pure source and 8/8 passed after a fresh mypyc compilation.
- Authoritative Phase 18 suite: passed; release evidence reports 1,379/1,379 tests, 97.89% total coverage, and 97.28% `core.py` coverage.
- Hosted proof: the exact candidate SHA passed all required native ownership jobs for Python 3.10 through 3.14.
- Audit persistence: `18-SECURITY.md` records `status: verified`, `threats_open: 0`, closed T-18-03/T-18-05, and the identical audited candidate SHA.
- Candidate integrity: candidate `78650eaf6adcbc1432c9ee9ae970017285ac267b` is an ancestor of the security persistence commit and candidate-owned implementation, test, harness, probe, and baseline paths are byte-identical. At audit time the remote execution-branch tip equals the candidate; the local branch is one documentation-only security commit ahead pending the orchestrator's exact-path validation commit and landing push.
