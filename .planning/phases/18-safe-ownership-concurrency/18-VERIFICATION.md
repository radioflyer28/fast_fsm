---
phase: 18-safe-ownership-concurrency
verified: 2026-09-02T21:03:18Z
status: passed
score: 12/12 must-haves verified
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: passed
  previous_score: 12/12
  gaps_closed:
    - "Non-blocking performance-evidence baseline drift corrected"
  gaps_remaining: []
  regressions: []
---

# Phase 18: Safe Ownership and Concurrency Verification Report

**Phase Goal:** A machine is safe by default under reentrant and concurrent use without global locks or event-loop blocking.
**Verified:** 2026-09-02T21:03:18Z
**Status:** passed
**Re-verification:** Yes — the sole evidence-note warning was corrected by `df5ad25e8b49b5f9b693f667876385dc2baa140d`; all prior passing truths received a regression sanity check
**Audited implementation:** `78650eaf6adcbc1432c9ee9ae970017285ac267b`

## Verification Basis

This report starts from the five ROADMAP success criteria and requirements
`OWN-01` through `OWN-07`. It does not treat any SUMMARY claim as evidence.
Every Phase 18 PLAN, CONTEXT, RESEARCH, SECURITY, and VALIDATION artifact was
read, then checked against the implementation, tests, CI workflow, and generated
evidence. State-transition, cancellation, cleanup, and ordering claims were
accepted only where a behavioral test was run, including in independently
created pure-Python and freshly compiled mypyc exports.

No previous Phase 18 verification report existed, so this is initial
verification rather than gap-closure re-verification.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|---|---|---|
| 1 | Reentrant trigger or mutator calls fail before lock acquisition and before nested declarative preparation, without overwriting the outer transition. | ✓ VERIFIED | `_acquire_sync_ownership()` checks the current owner before acquiring the per-instance lock (`core.py:612-619`, async specialization at `3007-3044`). Behavioral coverage includes `test_sync_reentrant_callback_is_rejected_before_nested_preparation`, lifecycle-stage caught/uncaught reentry tests, direct-control pre-validation rejection, and topology/history pre-mutation rejection. The named critical subset passed in both fresh pure and compiled exports. Covers SC1 and OWN-01. |
| 2 | Independent threads serialize access to one synchronous machine without a global lock, while unrelated machines can progress. | ✓ VERIFIED | The lock and owner are instance slots initialized per machine; no module-level lock registry or `RLock` exists. `test_sync_thread_tracer_serializes_one_machine_without_global_lock` and direct-control thread serialization passed in direct, fresh-pure, and fresh-compiled checks. Covers SC2 and OWN-02. |
| 3 | Independent tasks on one asynchronous machine serialize on the same loop without blocking the event loop. | ✓ VERIFIED | `_async_ownership_lock` is a per-machine `asyncio.Lock`; ownership is installed only after awaited acquisition. `test_async_same_loop_tasks_serialize_without_blocking_heartbeat` proves both serialization and heartbeat progress and passed in pure and compiled representations. Covers SC2 and OWN-03. |
| 4 | A machine binds permanently to one event loop and cross-loop access fails explicitly before foreign work is prepared. | ✓ VERIFIED | `_bind_or_check_async_loop()` records one loop/thread and raises on mismatch (`core.py:3053-3070`). `test_async_machine_binds_one_loop_before_preparing_foreign_work` passed in fresh pure and compiled exports. The bound-machine sync-writer policy is separately exercised. Covers SC3 and OWN-04. |
| 5 | Trigger, force/reset/restore, graph, history, and registrar writers all enter one ownership policy exactly once and do not bypass it through public-to-public delegation. | ✓ VERIFIED | Manual inspection and the `D14_WRITER_ENTRY_POINTS` AST inventory account for 21 public writer entries. The structural test requires exactly one acquire/release pair per entry and rejects public writer delegation; topology/history and async registrar behavior tests also passed. Covers SC4 and OWN-05. |
| 6 | Synchronous ownership remains held through failure/finalizer observation and is released after ordinary exceptions and `BaseException`, leaving the documented pre- or post-commit boundary coherent. | ✓ VERIFIED | All acquired sync paths release in `finally`. `test_sync_release_tracer_reuses_machine_after_every_throwable`, `test_sync_finalizer_holds_ownership_until_baseexception_observer_returns`, direct-control `BaseException`/validation tests, and lifecycle-stage assertions passed in both representations. Covers SC4 and OWN-06. |
| 7 | Async cancellation while waiting or owning cleans up ownership and leaves the machine reusable at the exact documented lifecycle boundary. | ✓ VERIFIED | `_acquire_async_ownership()` does not install ownership before lock acquisition and its callers release in `finally`. `test_async_waiting_and_owning_cancellation_release_for_reuse`, lifecycle cancellation parameter cases, deferred-cancellation cleanup, and subsequent reuse passed in pure and compiled exports. Covers SC4 and OWN-06. |
| 8 | Causally inherited child-task reentry is rejected immediately, without deadlocking, while an unrelated machine remains able to progress. | ✓ VERIFIED | The async owner/root check precedes the awaited lock (`core.py:3072+`). `test_async_causal_child_reentry_rejects_without_blocking_other_machine` passed directly and in the isolated pure/compiled subsets. Covers the causal-reentry part of SC1/SC2/SC4. |
| 9 | Synchronous callbacks execute inline on the event-loop thread; async callbacks are awaited; the implementation does not imply or perform automatic thread offload. | ✓ VERIFIED | `test_sync_callbacks_run_inline_on_event_loop_thread` passed in both representations. Source and docs contain no `asyncio.to_thread` or `run_in_executor` ownership/callback path. README, Quick Start, architecture, testing guide, ADR-005, and SPR state the contract and non-promises. Covers SC5 and OWN-07. |
| 10 | Safe-trigger admission errors stay outside ordinary exception conversion, are redacted, and release ownership for reuse. | ✓ VERIFIED | `safe_trigger()` performs admission before its conversion scope (`core.py:2841+`). Strict AST and behavioral tests cover direct admission, a busy async machine, secret-log redaction, ordinary post-admission conversion, and reuse. The tests passed directly and in both isolated representations. |
| 11 | Declarative preparation is context-local and machine-qualified at the consumer boundary, including shared-State cross-machine sync and async cases. | ✓ VERIFIED | Producer marker `_prepared_declarative_guard` and independent consumer `_declarative_consumer_machine_id` are ContextVars (`core.py:56-64`); `_has_prepared_declarative_guard()` requires identity equality (`134-145`). All five public dispatch boundaries set/reset the consumer marker. Structural, nested-context, thread/task isolation, cancellation, and shared-State cross-machine tests passed in pure and compiled checks. |
| 12 | The safety contract holds in both shipped representations, remains slot-protected and performant, and is enforced on every supported native Python version at the exact audited commit. | ✓ VERIFIED | Fresh pure import resolved to `src/fast_fsm/core.py`; fresh compiled import resolved to `core.cpython-312-darwin.so`; the same 11 critical ownership tests passed in each. The native standalone probe and CI contract checks passed. Hosted CI run `33678546626` completed successfully at exact SHA `78650e...`, with successful native jobs for Python 3.10, 3.11, 3.12, 3.13, and 3.14. Slots policy passed. Fresh compiled `test_trigger_min_throughput` and `test_sync_ownership_tracer_throughput` passed. The isolated baseline independently produced 1,379/1,379 passing tests, 97.89% total coverage, and 97.28% `core.py` coverage. |

**Score:** 12/12 truths verified (0 present-but-behavior-unverified)

### Roadmap Success-Criteria Disposition

| Roadmap criterion | Covered by truths | Result |
|---|---|---|
| Reentry fails before locking/preparation and cannot overwrite outer work. | 1, 8, 11 | ✓ VERIFIED |
| Per-machine threads and same-loop tasks serialize without event-loop blocking. | 2, 3 | ✓ VERIFIED |
| Cross-loop access fails explicitly. | 4 | ✓ VERIFIED |
| Every writer uses the policy and releases after exceptions, `BaseException`, or cancellation at a coherent boundary. | 5, 6, 7, 10 | ✓ VERIFIED |
| Sync callbacks stay inline and no implicit offload is introduced. | 9 | ✓ VERIFIED |

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `src/fast_fsm/core.py` | Per-machine sync/async ownership, loop affinity, reentry, cleanup, declarative qualification | ✓ VERIFIED | Substantive implementation inspected at ownership acquisition/release, all public dispatch boundaries, and declarative hook consumers; exercised by behavioral and AST tests. |
| `tests/test_ownership_concurrency.py` | OWN-01..OWN-07 contract inventory and adversarial behavior | ✓ VERIFIED | Inventory accounts for every requirement and eight proof groups. No Phase 18 requirement case remains xfailed; behavioral assertions exercise mutation boundaries, ordering, cleanup, cancellation, reentry, and reuse. |
| `tests/test_async_machine.py` | Established async lifecycle behavior under new ownership policy | ✓ VERIFIED | Included in native CI and isolated representation verification. |
| `tests/test_transition_lifecycle.py` | Pre-/post-commit failure and cancellation coherence | ✓ VERIFIED | Named lifecycle cancellation/failure paths passed; assertions inspect state/history/stage rather than symbol presence. |
| `tests/test_mypyc_guard.py` | Representation, slots, and throughput guards | ✓ VERIFIED | Native-origin and slot protection guards pass; compiled trigger and ownership tracer floors pass. The one platform capability skip is unrelated to the Phase 18 ownership contract. |
| `tools/phase18_native_probe.py` | Exact native CI/probe contract and hosted-run SHA validation | ✓ VERIFIED | `--check-ci`, `--assert-hosted-ci-sha`, and standalone `--build-mode compiled --assert-native` all returned exit 0. |
| `tools/phase16_isolated_verify.py` | Fresh export construction and baseline checking | ✓ VERIFIED | Used to create and exercise isolated pure and compiled exports and to run an independent baseline check. |
| `.github/workflows/ci.yml` | Required compiled native job on Python 3.10–3.14 | ✓ VERIFIED | `ownership_native_probe` matrix declares all five versions, checks the CI contract, asserts compiled core origin, runs ownership/lifecycle tests, and executes the standalone native probe. Hosted run confirms all five jobs succeeded. |
| `evidence/release-baseline.json` | Current full-suite/coverage baseline | ✓ VERIFIED | Generated evidence records 1,379 collected/passed, 0 failures/errors, 97.89% total and 97.28% core coverage; independently regenerated with a passing baseline-check. |
| `18-PERFORMANCE-EVIDENCE.md` | Environment-labelled performance proof | ✓ VERIFIED | Current throughput evidence is substantive and the named compiled floors independently passed. The corrected final paragraph now matches the authoritative baseline exactly: 1,379 passing tests, 97.89% total coverage, and 97.28% `core.py` coverage, explicitly including the Plan 18-08 marker-isolation paths. |
| README, Quick Start, architecture/testing docs, ADR-005, SPR | User-visible ownership/callback contract and explicit non-promises | ✓ VERIFIED | Documentation consistently states immediate reentry failure, per-instance serialization, permanent loop binding, cleanup boundaries, inline sync callbacks, and exclusions such as fairness, timeout, queue, loop transfer, and automatic offload. |
| `18-SECURITY.md` | Independent threat audit | ✓ VERIFIED | Verdict `SECURED`; 9/9 threats closed, zero open; sign-off ties to the exact audited candidate. |
| `18-VALIDATION.md` | Nyquist and test-quality audit | ✓ VERIFIED | Verdict `validated`, `nyquist_compliant: true`, Wave 0 complete, Plan 18-08 rows green, exact candidate recorded. |

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| Every sync writer | Per-machine sync ownership | `_acquire_sync_ownership` / private owned body / `finally` release | ✓ WIRED | AST inventory and behavioral tests prove the link for 21 public entries. |
| Every async writer | Permanent loop and async ownership | `_bind_or_check_async_loop`, causal-root check, awaited lock, `finally` release | ✓ WIRED | Same-loop, cross-loop, causal child, registrar, cancellation, and reuse tests pass. |
| Public dispatch boundaries | Declarative guard consumer | `_declarative_consumer_machine_id.set/reset(id(self))` | ✓ WIRED | `can_trigger`, `trigger`, `safe_trigger`, `can_trigger_async`, and `trigger_async` all participate; AST test enforces the set. |
| Declarative producer marker | State/Declarative consumer | identity-qualified `_has_prepared_declarative_guard` | ✓ WIRED | Shared-State cross-machine sync/async tests prove no producer-marker confusion. |
| `safe_trigger` | Ownership admission and exception conversion | admission outside conversion scope | ✓ WIRED | Structural and behavioral tests prove ownership errors are not converted while ordinary post-admission failures are. |
| Ownership implementation | Pure and compiled artifacts | isolated export + origin assertion + same named tests | ✓ WIRED | Both source and native extension representations execute the critical contract. |
| CI native job | Phase 18 tests and compiled artifact | five-version matrix, core-native assertion, exact test list, standalone probe | ✓ WIRED | Static CI checker passes and hosted run `33678546626` succeeds at the audited SHA. |
| Release baseline | Current repository tests/coverage | isolated `baseline-check` regeneration | ✓ WIRED | Regeneration exactly matches authoritative JSON counts and thresholds. |

### Data-Flow Trace (Level 4)

Phase 18 is a library concurrency/control phase and does not render dynamic user
data. The relevant flow is ownership state through mutation boundaries:

| Artifact | Data/state | Source | Reaches real behavior | Status |
|---|---|---|---|---|
| `StateMachine` | owner thread id and per-instance lock | runtime caller thread | gates all sync public writers and is released in `finally` | ✓ FLOWING |
| `AsyncStateMachine` | bound loop, task/root identity, async lock, sync reservation | running loop/task and runtime callers | gates async/sync writer admission and cancellation cleanup | ✓ FLOWING |
| Declarative hooks | preparation tuple plus consumer machine identity | actual transition preparation/dispatch | determines whether real declarative handlers are reused or recomputed | ✓ FLOWING |
| Lifecycle state/history | transition commit/failure stages | actual transition execution | assertions observe coherent state/history after reentry, throwable, and cancellation cases | ✓ FLOWING |

No static fallback, mock-only terminal, hollow prop, or disconnected data path
was found.

### Behavioral Spot-Checks

| Behavior | Command/check | Result | Status |
|---|---|---|---|
| Sync reentry, thread serialization, and `BaseException` finalizer ownership | Named Phase 18 pytest selection | Selected tests passed | ✓ PASS |
| Loop affinity, same-loop heartbeat serialization, cancellation cleanup, causal child rejection | Named async Phase 18 pytest selection | Selected tests passed | ✓ PASS |
| All-writer AST inventory, safe-trigger admission, inline callback | Named ownership/mypyc selection | Selected tests passed | ✓ PASS |
| Shared-State cross-machine declarative qualification | Named sync/async marker tests plus AST guard | Selected tests passed | ✓ PASS |
| Fresh pure representation | Isolated pure export, origin assertion, 11 critical named tests | All passed; origin was `src/fast_fsm/core.py` | ✓ PASS |
| Fresh compiled representation | Fresh mypyc export, native-origin assertion, same 11 critical tests | All passed; origin was `core.cpython-312-darwin.so` | ✓ PASS |
| Compiled performance floors | `TestAdvancedPerformance::test_trigger_min_throughput` and `::test_sync_ownership_tracer_throughput` in fresh compiled export | Both passed | ✓ PASS |
| Full baseline | `uv run python tools/phase16_isolated_verify.py --suite baseline-check` | 1,379 passed; 97.89% total, 97.28% core | ✓ PASS |
| Root workspace suite | `uv run pytest -q --tb=short` (orchestrator run, corroborated by independent baseline) | 1,379 passed | ✓ PASS |

### Probe Execution

| Probe | Command | Result | Status |
|---|---|---|---|
| CI contract | `uv run python tools/phase18_native_probe.py --check-ci .github/workflows/ci.yml` | Contract accepted Python 3.10–3.14 matrix and required steps | PASS |
| Standalone native representation | `uv run python tools/phase18_native_probe.py --build-mode compiled --assert-native` | Built and imported a native `ownership_probe_runtime...so` artifact | PASS |
| Hosted exact-SHA proof | `uv run python tools/phase18_native_probe.py --assert-hosted-ci-sha 78650eaf6adcbc1432c9ee9ae970017285ac267b` | Hosted matrix verified | PASS |
| Hosted API cross-check | `gh run view 33678546626 ...` | CI conclusion `success`, exact candidate SHA, five successful native jobs for 3.10–3.14 | PASS |
| Slots policy | `uv run python tools/release_evidence.py slots-policy --json` | StateMachine/AsyncStateMachine/runtime classes slot-protected; only registered exceptions permitted | PASS |

### Requirements Coverage

| Requirement | Source plans | Description | Status | Evidence |
|---|---|---|---|---|
| OWN-01 | 18-01, 18-03, 18-05 | Immediate owner reentry failure before locking/mutation | ✓ SATISFIED | Truths 1 and 8; direct behavioral and lifecycle assertions in pure and compiled representations. |
| OWN-02 | 18-01, 18-03, 18-05 | Per-machine thread serialization without global lock | ✓ SATISFIED | Truth 2; per-instance implementation plus thread tracer/direct-control behavior. |
| OWN-03 | 18-01, 18-04, 18-05 | Same-loop task serialization without loop blocking | ✓ SATISFIED | Truth 3; heartbeat/serialization behavior passed. |
| OWN-04 | 18-01, 18-04, 18-05 | Explicit cross-loop failure | ✓ SATISFIED | Truth 4; bind-before-foreign-preparation behavior passed. |
| OWN-05 | 18-01, 18-02, 18-03, 18-04, 18-05 | One ownership policy for every state/topology writer | ✓ SATISFIED | Truth 5; complete 21-entry AST inventory and mutator tests. |
| OWN-06 | 18-01, 18-02, 18-03, 18-04, 18-05 | Cleanup after exception, `BaseException`, cancellation at coherent boundary | ✓ SATISFIED | Truths 6 and 7; throwable, failure-stage, waiting/owning cancellation, deferred cleanup, and reuse assertions passed. |
| OWN-07 | 18-01, 18-04, 18-05, 18-06 | Inline sync callback and event-loop-safe async contract, no implied offload | ✓ SATISFIED | Truth 9; thread-identity behavior, source scan, and public documentation. |

All Phase 18 requirements mapped in `REQUIREMENTS.md` are claimed by Phase 18
plans and verified above. No orphaned Phase 18 requirement was found.

### Prohibition Checks

The plans' negative constraints were checked against enforcement evidence rather
than accepted as prose:

| Prohibition | Enforcement evidence | Status |
|---|---|---|
| No global lock, fairness, timeout, or queued-lock contract | Per-instance fields and concurrency tests; explicit documentation non-promises | ✓ VERIFIED |
| No event-loop rebinding or sync callback offload | Cross-loop rejection and inline-thread tests; no offload call sites | ✓ VERIFIED |
| No secret disclosure through safe-trigger admission/errors | Redaction and secret-log behavioral tests | ✓ VERIFIED |
| No swallowed cancellation or blanket rollback | Waiting/owning/lifecycle cancellation tests assert propagation and exact coherent boundary | ✓ VERIFIED |
| No mutable module registry or public hook signature widening for declarative identity | ContextVar-based identity plus AST source guards | ✓ VERIFIED |

### Test Quality Audit

| Area | Active evidence | Skip/xfail/circularity assessment | Assertion quality |
|---|---|---|---|
| Contract inventory | Test enumerates OWN-01..OWN-07 and eight proof groups | Strict-red source constructor leaves no current Phase 18 contract case xfailed | Structural + behavioral ownership |
| Sync concurrency/reentry | Thread barriers, lifecycle observers, reentry callbacks, reusable-machine checks | Active; no implementation-derived oracle | State, history, ordering, exception type/message |
| Async concurrency/cancellation | Heartbeat, competing tasks, cross-loop thread, cancellation at waiting/owning stages | Active; no event-loop sleep used as sole proof | Progress, prompt rejection, cleanup, reuse, coherent boundary |
| Declarative marker | Nested ContextVars, independent threads/tasks, cancellation, shared-State machines | Active; tests deliberately reuse object identities to expose collision | Exact handler-call counts and marker reset |
| Compiled parity | Fresh native build, origin assertion, same critical behavioral subset | Active on local compiled export and hosted 3.10–3.14 matrix | Runtime behavior plus native representation |
| Performance/slots | Compiled minimum-throughput tests and slots policy | Platform-specific descriptor capability skip is outside the ownership contract | Threshold and structural policy assertions |

### Decision Coverage

The 16 locked Phase 18 CONTEXT decisions are all reflected by implementation,
tests, and/or public documentation: one `RuntimeError` boundary, pre-lock reentry,
per-instance sync serialization, permanent async loop binding, same-loop awaited
serialization, causal-child rejection, idle bound-machine sync policy,
all-writer coverage, no public API widening, exact cleanup boundaries, inline
sync callbacks, declarative identity qualification, pure/compiled parity,
evidence-labelled performance, explicit exclusions, and documentation placement.
No missing, contradictory, or undocumented replacement decision was found.

### Candidate Integrity and Independent Gates

`HEAD` is `df5ad25e8b49b5f9b693f667876385dc2baa140d`. The only paths changed from
candidate `78650eaf6adcbc1432c9ee9ae970017285ac267b` to `HEAD` are Phase 18
SUMMARY, SECURITY, VALIDATION, and PERFORMANCE-EVIDENCE documents. A byte
comparison for the audited implementation and generated evidence paths
(`core.py`, ownership/mypyc tests, isolated verifier, native probe, and release
baseline) remains clean.

- Security: `SECURED`, 9/9 threats closed, 0 open.
- Nyquist: `validated`, compliant, Wave 0 complete.
- Hosted native proof: CI run `33678546626`, exact candidate SHA, Python
  3.10–3.14 all successful.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---:|---|---|---|
| Fresh compiled test output | N/A | Python warns that the legacy three-argument generator `throw(type, exc, tb)` form is deprecated. | ℹ️ Info | Not introduced by or specific to the ownership contract; no Phase 18 test failure or behavioral gap. Tracked outside this verification. |

No `TBD`, `FIXME`, or `XXX` debt marker, placeholder implementation, hollow
writer, global-lock registry, automatic-offload path, or user-visible stub was
found in Phase 18 implementation-owned files. `core.py`'s isolated `return []`
is a legitimate empty read result, not a stub.

### Human Verification Required

None. This is a library concurrency/foundation phase: all roadmap outcomes,
including ordering, reentry, exception cleanup, cancellation, loop affinity,
heartbeat progress, and representation parity, have automated behavioral proof.
There is no visual, external-service, performance-feel, or ambiguous runtime item
requiring subjective UAT.

### Deferred Items

None. Later roadmap phases cover diagnostics and installed-artifact parity, but
no failed Phase 18 truth was moved forward. Fairness, timeouts, explicit queues,
loop transfer, snapshot/restore of ownership internals, and automatic callback
offload are explicit Phase 18 non-promises rather than missing deliverables.

### Gaps Summary

No gaps or verification warnings remain. The machine is safe by default under
the specified sync and async ownership model, every behavior-dependent truth is
exercised in both fresh pure and compiled representations, and the corrected
performance evidence matches the authoritative generated baseline while naming
the Plan 18-08 marker-isolation scope.

---

_Verified: 2026-09-02T21:03:18Z_
_Verifier: the agent (gsd-verifier)_
