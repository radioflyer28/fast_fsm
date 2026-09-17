---
phase: 29
slug: expected-domain-rejection
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-09-17
---

# Phase 29 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.1 with pytest-asyncio 1.3.0 and Hypothesis |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `uv run pytest tests/test_expected_rejection.py -x -q` |
| **Adjacent regression command** | `uv run pytest tests/test_expected_rejection.py tests/test_priority_selection.py tests/test_condition_interface.py tests/test_transition_lifecycle.py tests/test_async.py tests/test_logging_config.py tests/test_mypyc_guard.py tests/test_release_evidence.py -x -q` |
| **Full suite command** | `uv run pytest tests/ -x -q` |
| **Estimated runtime** | Quick: <15 seconds; adjacent: <60 seconds; full: project-dependent |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/test_expected_rejection.py -x -q` plus the smallest directly affected adjacent suite.
- **After every plan wave:** Run the adjacent regression command; for waves changing Python source, also run Ruff format/check on changed files, blocking mypy, advisory ty, and `uv run python tools/release_evidence.py slots-policy --json`.
- **Before `$gsd-verify-work`:** Run the full sequential suite, blocking mypy, advisory ty, Ruff format followed by check-with-fixes and a clean check on changed Python files, slots policy, a fresh compiled build/native semantic oracle, documentation warnings-as-errors when API reference changes, and the existing singleton benchmark as a regression signal.
- **Max feedback latency:** 60 seconds for task-level and adjacent checks.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 29-01-01 | 01 | 1 | REJECT-01, REJECT-02, REJECT-05 | T-29-01, T-29-03, T-29-04 | Exact bounded ASCII code construction, public imports, result tail/property/equality/repr, fixed error text, hidden cause, and unchanged `raise_if_failed()` exception type | unit + boundary + structural | `uv run pytest tests/test_expected_rejection.py tests/test_mypyc_guard.py -x -q -k "public or construct or validation or payload or result or rejection"` | ❌ W0 central oracle; ✅ structural suite to extend | ⬜ pending |
| 29-01-02 | 01 | 1 | REJECT-03, REJECT-04, REJECT-07 | T-29-02, T-29-03, T-29-06 | Sync transition/declarative/permission rejection is terminal, preserves selected priority/internal metadata, performs no lower-candidate or lifecycle work, and finalizes exactly one observer pass | integration + logging | `uv run pytest tests/test_expected_rejection.py tests/test_priority_selection.py tests/test_transition_lifecycle.py tests/test_logging_config.py -x -q -k "approved_boundary or priority or fallthrough or observer or logging"` | ❌ W0 central oracle; ✅ adjacent suites to extend | ⬜ pending |
| 29-02-01 | 02 | 2 | REJECT-03, REJECT-04, REJECT-06, REJECT-07, REJECT-09 | T-29-02, T-29-03, T-29-06, T-29-08 | Sync/async queries return false without mutation, history, observer, trace, or fallback; async dispatch matches sync terminality and preserves cancellation identity | async integration | `uv run pytest tests/test_expected_rejection.py tests/test_priority_selection.py tests/test_async.py tests/test_transition_lifecycle.py -x -q -k "query or async or cancellation or priority"` | ❌ W0 central oracle; ✅ adjacent suites to extend | ⬜ pending |
| 29-02-02 | 02 | 2 | REJECT-08 | T-29-02, T-29-08 | Direct, nested, deferred, synchronous, asynchronous, AND/OR/NOT/Negated conditions propagate the identical signal and never evaluate a later child | unit + async composition | `uv run pytest tests/test_expected_rejection.py tests/test_condition_interface.py -x -q -k "compos or deferred or nested or negated"` | ❌ W0 central oracle; ✅ condition suite to extend | ⬜ pending |
| 29-03-01 | 03 | 3 | REJECT-02, REJECT-03, REJECT-07, REJECT-09 | T-29-03, T-29-04, T-29-06, T-29-07, T-29-08 | The signal outside eligibility remains an ordinary staged lifecycle failure with original hidden cause and correct commit/history truth; logs disclose no arbitrary payload; cancellation remains cancellation | lifecycle + security + logging | `uv run pytest tests/test_expected_rejection.py tests/test_transition_lifecycle.py tests/test_logging_config.py -x -q -k "outside_boundary or lifecycle or payload or observer or cancellation"` | ❌ W0 central oracle; ✅ adjacent suites to extend | ⬜ pending |
| 29-03-02 | 03 | 3 | REJECT-01–REJECT-09 | T-29-01, T-29-04, T-29-05 | Public/stub/native layouts, four-exception slots-policy authority, bounded cold-path validation, unchanged hot-path structure, and pure/native semantic parity close without dependency or success-path regressions | structural + typing + native + full regression | `uv run pytest tests/test_expected_rejection.py tests/test_mypyc_guard.py tests/test_release_evidence.py -x -q`, bracketed by slots policy, type gates, `task build-check`, native-origin proof, full suite, docs build, and benchmark regression signal | ✅ structural/release suites to extend; ❌ W0 semantic oracle | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_expected_rejection.py` — central requirement-labelled sync/async matrix for REJECT-01 through REJECT-09.
- [ ] Extend `tests/test_mypyc_guard.py` — exact result field/property, exception decorator/layout, stub and package exports, catch-boundary structure, no-sort/no-copy invariants, and pure/native semantic oracle.
- [ ] Extend `tests/test_release_evidence.py` — fourth registered instance-dictionary exception and synchronized policy-authority assertions.
- [ ] Extend `tests/test_logging_config.py` — debug-only rejection metadata with no exception repr, warning, traceback, or query trace evidence.

No new test framework, configuration, dependency, or shared fixture module is required. Reuse existing async event handshakes and local fixtures; do not add timing sleeps.

---

## Required Validation Matrices

1. **Signal and result:** exact `str`, ASCII grammar, 1–64 length, no normalization, hostile subclass/mutation defense, public exports, result equality/repr, derived `rejected`, fixed error, `cause=None`, and existing `TransitionError` escalation.
2. **Eligibility boundaries:** transition guard, declarative guard, and state permission in singleton and grouped sync/async paths; false falls through while rejection terminates with selected priority/internal metadata.
3. **Queries and observers:** `can_trigger*()` returns false and performs no mutation, history, observer, trace, or lower-candidate work; real dispatch finalizes one unchanged failure-observer pass even when observers fail or reenter.
4. **Composition:** direct, nested, deferred, AND/OR/NOT/Negated sync and async wrappers propagate signal identity, stop later children, and retain single await ownership.
5. **Lifecycle classification:** timing and every pre/post-commit lifecycle surface treat the same signal as an ordinary failure with accurate stage, cause, commit, and history truth.
6. **Cancellation and native closure:** `CancelledError` identity/re-raise and ownership recovery remain intact; pure and compiled origins expose identical slots, stub, export, selector, and semantic behavior.

---

## Threat Register

| ID | Threat | Required control |
|----|--------|------------------|
| T-29-01 | Code spoofing | Require exact `str`, positive ASCII allow-list, 1–64 length, no normalization, and revalidate at the conversion boundary. |
| T-29-02 | Priority tampering | Represent rejection as a terminal result rather than false/`None`; never evaluate a lower-priority candidate. |
| T-29-03 | Classification ambiguity | Keep expected rejection, unexpected defects, and cancellation as distinct outcomes with exact stage/cause truth. |
| T-29-04 | Payload disclosure | Derive bounded public text only from validated code; never log exception repr, traceback, or caller payload. |
| T-29-05 | Unbounded validation/work | Reject oversized codes before pattern scanning and preserve one-pass, no-sort/no-copy/no-task-fan-out selection. |
| T-29-06 | Observer multiplication | Build in the selector, finalize once at the public trigger, snapshot observers, and isolate observer failures. |
| T-29-07 | Post-commit relabeling | Catch only at the three eligibility calls; lifecycle-raised signals retain ordinary staged failure semantics. |
| T-29-08 | Cancellation swallowing | Catch `Exception`, not `BaseException`; preserve dedicated cancellation finalization and identical re-raise. |

---

## Manual-Only Verifications

All Phase 29 behaviors have automated verification routes.

---

## Validation Sign-Off

- [ ] All planned tasks have an `<automated>` verification route or Wave 0 dependency.
- [ ] Sampling continuity has no three consecutive tasks without automated verification.
- [ ] Wave 0 covers all missing references.
- [ ] Commands use no watch-mode flags.
- [ ] Task-level feedback latency target is below 60 seconds.
- [ ] `nyquist_compliant: true` is set in frontmatter after validation succeeds.

**Approval:** pending
