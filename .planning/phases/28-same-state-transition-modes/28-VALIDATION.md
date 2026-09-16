---
phase: 28
slug: same-state-transition-modes
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-09-16
---

# Phase 28 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.1 with pytest-asyncio 1.3.0 and Hypothesis |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `uv run pytest tests/test_transition_modes.py -x -q` |
| **Adjacent regression command** | `uv run pytest tests/test_transition_modes.py tests/test_transition_lifecycle.py tests/test_transition_timing.py tests/test_priority_selection.py tests/test_graph_invariants.py tests/test_builder.py tests/test_async.py -x -q` |
| **Full suite command** | `uv run pytest tests/ -x -q` |
| **Estimated runtime** | Quick: <15 seconds; adjacent: <60 seconds; full: project-dependent |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/test_transition_modes.py -x -q` plus the smallest directly affected adjacent suite.
- **After every plan wave:** Run the adjacent regression command; for waves changing `core.py` or `core.pyi`, also run `uv run ruff format` on changed Python files, `uv run ruff check --fix` on the same files, a clean `uv run ruff check`, blocking mypy, advisory ty, and `uv run python tools/release_evidence.py slots-policy --json`.
- **Before `$gsd-verify-work`:** Run the full sequential suite, blocking mypy, advisory ty, Ruff format followed by check-with-fixes and a clean check on changed Python files, slots policy, and ordered pure/native semantic parity with the source origin restored afterward.
- **Max feedback latency:** 60 seconds for task-level and adjacent checks.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 28-01-01 | 01 | 1 | MODE-01, MODE-03, MODE-04 | T-28-01, T-28-03, T-28-05 | Leading red-first tracer proves omitted/false external behavior and one complete internal logical commit on the same canonical State without callback-payload collision | integration + structural | `uv run pytest tests/test_transition_modes.py tests/test_transition_lifecycle.py -x -q -k "mode or self_transition or lifecycle"` | ❌ `tests/test_transition_modes.py` Wave 0; ✅ lifecycle suite | ⬜ pending |
| 28-01-02 | 01 | 1 | MODE-01, MODE-02 | T-28-01, T-28-02, T-28-04 | Exact canonical validation, idempotent/conflicting identity, interrupted/parallel ownership, builder repair, graph snapshot, clone, and atomic publication | unit + invariant + property | `uv run pytest tests/test_transition_modes.py tests/test_graph_invariants.py tests/test_hypothesis.py tests/test_builder.py -x -q -k "internal or mode or atomic or ownership or clone or snapshot"` | ❌ central oracle Wave 0; ✅ adjacent suites | ⬜ pending |
| 28-02-01 | 02 | 2 | MODE-03, MODE-04, MODE-05 | T-28-06, T-28-07, T-28-08, T-28-09 | External reset and internal retained/suppressed lifecycle, history-off/on clock truth, direct-control boundary, and uninterrupted residency | lifecycle + deterministic timing | `uv run pytest tests/test_transition_modes.py tests/test_transition_lifecycle.py tests/test_transition_timing.py -x -q` | ❌ central oracle Wave 0; ✅ adjacent suites | ⬜ pending |
| 28-02-02 | 02 | 2 | MODE-02, MODE-04, MODE-06 | T-28-02, T-28-06, T-28-07, T-28-08, T-28-10 | Candidate identity includes mode; priorities remain deterministic; pre/post-commit failure truth is mode-complete and bounded | unit + integration + property | `uv run pytest tests/test_transition_modes.py tests/test_priority_selection.py tests/test_graph_invariants.py tests/test_hypothesis.py -x -q` | ❌ central oracle Wave 0; ✅ adjacent suites | ⬜ pending |
| 28-03-01 | 03 | 3 | MODE-04, MODE-05, MODE-06 | T-28-06, T-28-07, T-28-13, T-28-14 | Async lifecycle skips matching state surfaces, cancellation preserves mode/stage/commit truth, and ownership remains reusable | async integration | `uv run pytest tests/test_transition_modes.py tests/test_async.py tests/test_transition_lifecycle.py -x -q -k "internal or cancellation or ownership"` | ❌ central oracle Wave 0; ✅ adjacent suites | ⬜ pending |
| 28-03-02 | 03 | 3 | MODE-01–MODE-06 | T-28-01, T-28-02, T-28-03, T-28-05, T-28-11, T-28-12, T-28-15 | Slotted/mypyc-safe carrier layouts, bounded metadata, direct dispatch complexity, and identical pure/native behavior without source-shadow residue | structural + typing + native + full regression | Task 2's executable block: Ruff format → check with fixes → clean check; typing/slots; asserted pure origin + focused pure probe; fresh native build + asserted extension origin + focused compiled probe; exact recoverable shadow relocation; asserted pure origin + full pure suite | ✅ structural/native harnesses; ❌ mode probe additions | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_transition_modes.py` — central MODE-01 through MODE-06 oracle for direct/builder construction, lifecycle, timing, result/history, priority, failures, and async cancellation.
- [ ] `tests/test_mypyc_guard.py` additions — appended carrier/result/record slots and fields, stub signatures, exact-bool boundary, direct singleton representation, and pure/native semantic parity.
- [ ] `tests/test_graph_invariants.py` additions — mode identity, invalid fan-out atomicity, graph snapshot scalar, clone replay, and graph-version neutrality.
- [ ] `tests/test_hypothesis.py` additions — valid and invalid self/non-self mode requests and ordering without partial publication.

No new test framework, configuration, dependency, or shared fixture module is required. Reproduce the existing `FakeClock` and event-handshake patterns locally in the central phase oracle rather than importing test modules.

---

## Required Validation Matrices

1. **Construction:** direct and builder omitted/false/true mode; invalid exact-bool values; canonical string/object endpoints; final self; mixed multi-source; duplicate same mode; equal-priority different mode; unchanged topology, graph version, and builder repairability after failure.
2. **Lifecycle:** external self visits every existing state and transition surface; internal visits only before, logical commit/history, declarative handler, trigger callback, after listener, result/trace, and failure observer.
3. **Failure:** internal before-listener and commit failures are uncommitted; declarative/trigger/after failures are committed, mode-true, history-retaining, suffix-stopping, and finalized exactly once; skipped state surfaces cannot originate failures.
4. **Timing:** history-disabled internal transition makes no commit clock read; history-enabled internal transition records event time but preserves entry epoch; external self resets entry epoch; repeated internal events do not extend `after=` or `within=`.
5. **Async:** guard cancellation before commit; retained async declarative cancellation after commit; skipped async exit/entry sentinels; one observer pass; identical cancellation re-raise; released ownership; successful subsequent reuse.
6. **Native:** exact field/slot order, `core.pyi` signatures, exact-bool rejection before mutation, and direct singleton storage; then a fail-closed pure-start → fresh build → asserted native origin → focused compiled semantic probe → exact recoverable shadow relocation → asserted pure origin → full pure-suite sequence, with no lingering source-tree native shadow even when an intermediate native gate fails.

---

## Manual-Only Verifications

All Phase 28 behaviors have automated verification routes.

---

## Validation Sign-Off

- [ ] All planned tasks have an `<automated>` verification route or Wave 0 dependency.
- [ ] Sampling continuity has no three consecutive tasks without automated verification.
- [ ] Wave 0 covers all missing references.
- [ ] Commands use no watch-mode flags.
- [ ] Task-level feedback latency target is below 60 seconds.
- [ ] `nyquist_compliant: true` is set in frontmatter after validation succeeds.

**Approval:** pending
