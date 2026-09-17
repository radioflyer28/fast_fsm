---
phase: 28-same-state-transition-modes
verified: 2026-09-17T02:13:32Z
status: passed
score: 5/5 must-haves verified
behavior_unverified: 0
overrides_applied: 0
decision_coverage:
  honored: 17
  total: 17
  not_honored: []
---

# Phase 28: Same-State Transition Modes Verification Report

**Phase Goal:** Users can choose whether a self-transition performs external re-entry or an internal logical commit, with identical semantic truth across machine types.
**Verified:** 2026-09-17T02:13:32Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|---|---|---|
| 1 | `internal=True` is an exact per-transition choice valid only for a canonical self-target; omission preserves external behavior and invalid registration is atomic. | ✓ VERIFIED | Exact-bool validation precedes canonical resolution in `StateMachine._normalize_transition_request` (`core.py:1831-1852`); canonical identity is enforced before a prepared transition is returned (`core.py:1864-1870`); complete plans publish only after all requests normalize (`core.py:1945-2015`). Active construction tests cover direct, batch, contention, builder repair, mode identity, clone, and snapshot paths. Focused construction run passed. |
| 2 | An external self-transition runs the complete exit-and-entry lifecycle and resets entry-relative timing. | ✓ VERIFIED | The default branch in `_execute_transition` executes before listeners, source exit surfaces, ordinary commit, destination entry surfaces, declarative work, trigger callbacks, and after listeners (`core.py:3711-3930`). `_commit_transition` resets `_state_entered_at` (`core.py:3585-3605`). `test_default_and_false_self_transitions_keep_the_external_lifecycle` and `test_external_self_transition_restarts_residency_windows` passed. |
| 3 | An internal transition skips every state exit/entry surface while retaining transition-level behavior, one logical commit, result production, history, and appropriate observers. | ✓ VERIFIED | Both runners branch once on `prepared.entry.internal` (`core.py:3728`, `core.py:4620`) into bounded internal runners that retain before/declarative/trigger/after work and return `committed=True, internal=True` without invoking state lifecycle surfaces (`core.py:3932-4058`, `core.py:4846-4979`). History records carry `internal=True` (`core.py:3607-3628`). Sync and async lifecycle tests passed. |
| 4 | Internal transitions preserve the original state-entry timestamp so residency-based conditions remain uninterrupted. | ✓ VERIFIED | `_commit_internal_transition` reads the clock only when history exists and never writes `_state_entered_at` (`core.py:3607-3628`), while ordinary external commit resets it. The three focused timing tests for history clock behavior, uninterrupted internal residency, and external restart passed. |
| 5 | Synchronous and asynchronous machines produce matching mode, priority, failure, and cancellation outcomes without collapsing an internal commit into a no-op. | ✓ VERIFIED | Candidate-specific sync and async failures propagate `entry.priority` and `entry.internal` (`core.py:2879-3049`, `core.py:5082-5207`). Async cancellation carries selected mode beside priority and stage, finalizes once, re-raises, and releases ownership in the public boundary (`core.py:5296-5348`). The complete `test_transition_modes.py` behavioral oracle passed, including pre-commit guard cancellation, post-commit declarative cancellation, reuse, selected-mode failure, and mixed-mode priority parity. The structural carrier test and pure/native semantic oracle are active; the fresh pre-dispatch pure/native contract gate passed, and this verification independently reran the pure-source oracle from the asserted `src/fast_fsm/core.py` origin. |

**Score:** 5/5 truths verified (0 present, behavior-unverified)

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `src/fast_fsm/core.py` | Canonical carrier, validation, sync/async lifecycle, timing, failure, cancellation, graph, and clone semantics | ✓ VERIFIED | Substantive implementation at the canonical construction and selected-entry execution seams; all three plan artifact queries passed. |
| `src/fast_fsm/core.pyi` | Public keyword-only mode plus result/history typing | ✓ VERIFIED | `internal: bool = False` is present on direct and builder registration, and on result/history/carrier declarations. Structural parity test passed. |
| `tests/test_transition_modes.py` | Central MODE-01..06 behavioral oracle | ✓ VERIFIED | 833-line active sync/async oracle; complete file passed in pure mode. |
| `tests/test_graph_invariants.py` | Atomicity, identity, snapshot, clone, and contention evidence | ✓ VERIFIED | Phase-linked internal/mode tests passed in focused construction run. |
| `tests/test_hypothesis.py` | Generated invalid-order/no-partial-publication evidence | ✓ VERIFIED | Phase commit adds generated reordered invalid internal request coverage; no disabled phase requirement test found. |
| `tests/test_builder.py` | Primary builder authoring and repair-after-failure evidence | ✓ VERIFIED | Phase-linked internal/mode tests passed in focused construction run. |
| `tests/test_transition_lifecycle.py` | Established lifecycle/failure regression boundary | ✓ VERIFIED | Linked by Plans 02/03; central Phase 28 tests exercise the specialized lifecycle against the established stage contract. |
| `tests/test_transition_timing.py` | Entry epoch and event timestamp evidence | ✓ VERIFIED | Three relevant deterministic fake-clock tests passed. |
| `tests/test_priority_selection.py` | Mode-neutral priority and selected-mode failure evidence | ✓ VERIFIED | Mixed-mode fallthrough and terminal internal guard-error tests passed. |
| `tests/test_async.py` | Existing sync/async machine parity boundary | ✓ VERIFIED | Remains an adjacent regression artifact; Phase 28 cancellation and parity assertions are active in the central oracle. |
| `tests/test_mypyc_guard.py` | Carrier/stub/dispatch structure and pure/native semantic proof | ✓ VERIFIED | Phase 28 structural test passed; semantic probe is written to run unchanged against pure and compiled origins. |
| `.specify/memory/spr-core-api.md` | Living maintainer contract | ✓ VERIFIED | Exists and records settled mode semantics without claiming deferred Phase 30–32 work. |

### Key Link Verification

The automated key-link helper could not interpret the plans' symbolic `from`/`to` labels as file paths, so each declared link was traced manually in source.

| From | To | Via | Status | Details |
|---|---|---|---|---|
| Direct/builder `add_transition` | `_TransitionRequest` → normalization → prepared entry | One exact `internal` scalar | ✓ WIRED | Builder stores the scalar on `_TransitionRequest` (`core.py:6097-6167`); direct registration and batch application forward it into `_normalize_transition_request`, then `_PreparedTransition`, then immutable `TransitionEntry`. |
| `_PreparedDispatch.entry.internal` | Sync/async lifecycle | Single post-selection branch | ✓ WIRED | Exactly one branch in each top-level runner selects the internal specialization (`core.py:3728`, `core.py:4620`); selection itself remains priority/guard driven. |
| `TransitionEntry.internal` | Result, history, graph, clone | Canonical scalar propagation | ✓ WIRED | Internal runners emit result/history mode; graph snapshots and clone replay propagate `entry.internal`; active graph/clone tests and the semantic probe assert continuity. |
| Async selected candidate | Outer cancellation finalizer | Task-local `ContextVar` | ✓ WIRED | `_async_selection_internal.set(entry.internal)` is set during selection and read when cancellation precedes prepared dispatch (`core.py:5082`, `core.py:5340-5345`). |
| Runtime carrier layout | Stub and native proof | AST/slot/signature assertions and dual-origin oracle | ✓ WIRED | `test_phase28_mode_carriers_and_async_selection_keep_one_exact_contract` checks runtime/stub shape; `test_priority_selector_semantic_probe_matches_pure_and_native_core` exercises public behavior in either origin. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|---|---|---|---|---|
| Registration topology | `TransitionEntry.internal` | Exact caller `internal` argument normalized through the immutable request/prepared chain | Yes | ✓ FLOWING |
| Sync/async dispatch | `prepared.entry.internal` | Selected canonical transition entry after priority/guard/permission selection | Yes | ✓ FLOWING |
| Result/history | `TransitionResult.internal`, `TransitionRecord.internal` | Selected entry/internal runner, including failure and cancellation paths | Yes | ✓ FLOWING |
| Residency timing | `_state_entered_at` | External commit clock only; internal history uses a separate event timestamp | Yes | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Complete sync/async mode, failure, cancellation, and reuse oracle | `FAST_FSM_BUILD_MODE=pure uv run pytest tests/test_transition_modes.py -q --disable-warnings` | Exit 0 | ✓ PASS |
| Internal residency preservation and external reset | `FAST_FSM_BUILD_MODE=pure uv run pytest tests/test_transition_timing.py -q --disable-warnings -k 'internal_commit_clock or internal_events or external_self_transition'` | 3 passed | ✓ PASS |
| Atomic construction, identity, builder, graph, and clone mode paths | `FAST_FSM_BUILD_MODE=pure uv run pytest tests/test_graph_invariants.py tests/test_builder.py -q --disable-warnings -k 'internal or mode'` | 42 passed | ✓ PASS |
| Mixed-mode priority, terminal selected-mode failure, and carrier structure | `FAST_FSM_BUILD_MODE=pure uv run pytest tests/test_priority_selection.py tests/test_mypyc_guard.py -q --disable-warnings -k 'mixed_mode or internal_priority_guard_error or phase28_mode_carriers'` | 3 passed | ✓ PASS |
| Pure-source origin | `FAST_FSM_BUILD_MODE=pure uv run python -c '... assert origin == expected ...'` | `/Users/akriz/code/fast_fsm/src/fast_fsm/core.py` | ✓ PASS |

### Probe Execution

No Phase 28 probe script is declared in a plan or summary, and no conventional `scripts/*/tests/probe-*.sh` exists. Step 7c is not applicable.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|---|---|---|---|---|
| MODE-01 | 28-01, 28-03 | Explicit exact internal choice; omitted/false external | ✓ SATISFIED | Exact validation, public/stub defaults, default/false lifecycle test, structural parity test. |
| MODE-02 | 28-01, 28-03 | Canonical self-only internal registration with atomic rejection | ✓ SATISFIED | Canonical identity check, prepare-all/publish-once transaction, construction/property/builder tests. |
| MODE-03 | 28-01, 28-02, 28-03 | Full external exit/re-entry lifecycle and entry-time reset | ✓ SATISFIED | External runner, ordinary commit epoch reset, lifecycle and timing tests. |
| MODE-04 | 28-01, 28-02, 28-03 | Internal skips state surfaces but retains logical transition work and truth | ✓ SATISFIED | Dedicated sync/async internal runners plus ordered lifecycle, result/history, payload, and observer tests. |
| MODE-05 | 28-02, 28-03 | Uninterrupted state residency across internal events | ✓ SATISFIED | Dedicated internal commit leaves entry epoch untouched; deterministic timing tests passed. |
| MODE-06 | 28-02, 28-03 | Sync/async priority, cancellation, and failure equivalence | ✓ SATISFIED | Selected-mode failure propagation, mixed priority test, two handshake cancellation tests, ownership/reuse assertions, dual-origin oracle. |

No Phase 28 requirement is orphaned: MODE-01 through MODE-06 all appear in plan frontmatter and map exactly to Phase 28 in `REQUIREMENTS.md`.

### Decision Coverage

All 17 trackable `28-CONTEXT.md` decisions are honored by shipped artifacts. The decision-coverage gate returned `honored: 17`, `total: 17`, `not_honored: []`.

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
|---|---|---:|---:|---|---|---|
| `tests/test_transition_modes.py` | MODE-01..06 | Yes | 0 | No | Behavioral, multi-step state/history/stage/cancellation assertions | ✓ STRONG |
| `tests/test_graph_invariants.py` / `tests/test_hypothesis.py` / `tests/test_builder.py` | MODE-01, MODE-02 | Yes | Phase-linked tests active | No | Value + mutation-fingerprint + property/invariant assertions | ✓ STRONG |
| `tests/test_transition_timing.py` | MODE-03, MODE-05 | Yes | 0 relevant | No | Exact clock-call, timestamp, epoch, and eligibility values | ✓ STRONG |
| `tests/test_priority_selection.py` | MODE-06 | Yes | 0 relevant | No | Behavioral candidate ordering, selected metadata, and lifecycle assertions | ✓ STRONG |
| `tests/test_mypyc_guard.py` | MODE-01..06 structural/native contract | Yes | One unrelated compiled-priority test conditionally skips outside native origin | No | Exact AST/slot/signature values plus public semantic workflow | ✓ STRONG |

**Disabled tests on requirements:** 0. The skip sites in adjacent files are platform/origin guards for unrelated or native-only cases; no Phase 28 requirement depends solely on a disabled test.
**Circular patterns detected:** 0. File-writing matches in `test_mypyc_guard.py` create isolated test inputs and do not generate expected Phase 28 behavior from the system under test.
**Insufficient assertions:** 0.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---:|---|---|---|
| `src/fast_fsm/core.py` | 698 | String contains “not available” | ℹ️ Info | Stable fail-closed error constant for unsupported priority group resolution, not a placeholder or incomplete implementation. |

No unreferenced `TBD`, `FIXME`, or `XXX` marker exists in Phase 28-modified files. No user-visible placeholder, empty handler, hollow prop, or static-data substitute was found.

### Human Verification Required

N/A — infrastructure/core-library phase with no user-facing visual surface. All lifecycle, timing, failure, cancellation, ownership, and parity criteria have programmatic behavioral evidence; there are no behavior-unverified truths.

### Gaps Summary

No gaps. All five roadmap success criteria and MODE-01 through MODE-06 are implemented, wired, and behaviorally exercised. Later Phase 30–32 adapter/persistence, diagnostics/visualization, installed-artifact, performance, and public-guidance work remains correctly outside the Phase 28 contract and was not used to excuse any Phase 28 truth.

---

_Verified: 2026-09-17T02:13:32Z_
_Verifier: the agent (gsd-verifier)_
