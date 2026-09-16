---
phase: 27-explicit-final-states
verified: 2026-09-16T03:24:01Z
status: passed
score: 16/16 must-haves verified
behavior_unverified: 0
overrides_applied: 0
decision_coverage:
  honored: 12
  total: 12
  not_honored: []
human_verification: []
---

# Phase 27: Explicit Final States Verification Report

**Phase Goal:** Users can represent intentional completion directly and rely on termination truth across construction, execution, and control operations.
**Verified:** 2026-09-16T03:24:01Z
**Status:** passed
**Re-verification:** No — initial goal-backward verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Every explicit State construction surface exposes one exact keyword-only final boolean with a `False` default and getter-only public access. | ✓ VERIFIED | `State` owns slotted `_final`, validates `type(final) is bool`, and exposes only `final` at `src/fast_fsm/core.py:850-867`; `State.create` and `CallbackState` forward it at lines 870-900 and 939-955, while `DeclarativeState` forwards it at 5337-5352 and async declarative construction inherits that path. `TestStateFinalMetadata` and `TestFinalConstructionSurfaces` passed in the fresh focused run; `core.pyi:160-196` presents `final: bool` to consumers. |
| 2 | Sync and async machines report termination through one O(1) read of the canonical current State, including at initialization. | ✓ VERIFIED | `StateMachine.is_terminated` is exactly `return self._current_state.final` at `src/fast_fsm/core.py:2354-2360`; `AsyncStateMachine` does not override it. Initial-final, inherited-async, and incoming-final tests passed; the AST guard in `test_final_state_metadata_and_termination_query_keep_one_truth_source` passed. |
| 3 | Explicit finality, not dead-end topology, determines termination. | ✓ VERIFIED | `test_non_final_sink_is_not_terminated` passed and asserts an empty trigger set with `is_terminated is False`; the same direct query reports `True` for an explicitly final sink. No transition scan appears in the query body. |
| 4 | A final State remains legal as an initial State and as an incoming transition target. | ✓ VERIFIED | `test_initial_final_state_is_terminated` and `test_incoming_transition_to_final_state_is_terminated` passed. The normalizer checks only canonical sources at `core.py:1852-1861` and resolves the target afterward without a final-target rejection at line 1862. |
| 5 | Triggering while final retains ordinary missing-transition behavior with no completion event or special exception. | ✓ VERIFIED | `test_trigger_from_final_uses_ordinary_missing_transition_result` passed, asserting the existing unsuccessful `resolution` result, unchanged current State, and retained termination. Source inspection finds no finality branch in runtime selection/lifecycle regions; the structural guard in `test_final_source_validation_lives_only_in_canonical_normalization` passed. |
| 6 | One real Phase 27 Beads item governs execution and remains open until verifier closure. | ✓ VERIFIED | Fresh `bd show fast_fsm-7xh --json` reports title `Implement Phase 27 explicit final states`, status `in_progress`, priority 1, assignee `radioflyer28`; all three summaries carry the same identifier. |
| 7 | Every retained transition-producing surface rejects outgoing canonical final sources, including self, grouped, priority, helper, factory, builder, declarative, clone, generated, and async paths. | ✓ VERIFIED | The single production rejection is at `core.py:1853-1855`. Fresh tests passed across `TestFinalSourceConstructionInvariant`, graph helper/declarative/clone cases, builder repair, Hypothesis reordered batches, and async registration. The 601-test focused command exercised all seven linked test modules. |
| 8 | Final-source rejection happens before publication, preserving topology, graph version, current State, and reusable builder staging even for a late invalid request. | ✓ VERIFIED | `_apply_transition_requests_owned()` prepares every request into a local list at `core.py:1977-1996` and calls `_commit_transition_plan()` only once at line 1997; publication and version increment happen only at `core.py:1950-1952`. Mixed-batch, multi-source, helper, builder repair, and generated ordering tests passed with identity-sensitive rollback assertions. |
| 9 | Canonical resolution precedes final-source inspection, so foreign endpoint metadata cannot override the registered State. | ✓ VERIFIED | `_resolve_canonical_state(raw_source, role="source")` is called at `core.py:1853` before `source.final` at line 1854. `test_registered_final_source_wins_over_same_name_input_forms` and the structural ordering assertion passed. |
| 10 | Final-source errors are fixed and bounded, and dictionary construction preserves exact transition-row context. | ✓ VERIFIED | Production raises the constant `ValueError("final state cannot be a transition source")` at `core.py:1855`; contextual wrapping uses the indexed caller-owned context at `core.py:1993-1996`. `test_from_dict_reports_the_final_source_row_without_a_candidate_escape` passed with the exact `transition[0]` message. |
| 11 | Entering a final State makes termination visible at commit and every later sync failure or async cancellation leaves committed finality intact. | ✓ VERIFIED | `_commit_transition()` assigns `_current_state` at `core.py:3572`; sync destination work begins only at 3756 and async destination work only after the commit at 4517-4533. The tracer, nine-stage sync lifecycle matrix, declarative failure test, and four-boundary event-handshake cancellation matrix all passed, including in-entry `is_terminated`, history, cause/stage, committed flag, and observer-count assertions. |
| 12 | Reset, force-state, and snapshot-v1 restore derive termination solely from the resulting canonical State in either direction. | ✓ VERIFIED | `_force_state_owned()` routes controls through the shared commit at `core.py:3377-3384`; reset and restore call it at 3396-3400 and 3435-3451. Snapshot remains exactly state plus version at 3402-3417. `test_controls_and_snapshot_v1_derive_termination_from_current_state` passed. |
| 13 | Clone preserves canonical State identities/final markers, owns independent topology, resets to the initial State, and retains async machine type. | ✓ VERIFIED | `_clone_owned()` constructs through `self.__class__`, reuses the exact state dictionary, creates fresh transition dictionaries, and republishes requests at `core.py:3483-3514`; async clone asserts and returns the inherited async instance at 4402-4414. Both final/non-final initial clone tests, graph identity/isolation tests, and async dict/clone test passed. |
| 14 | Dictionary persistence emits deterministic sorted `final_states`, defaults legacy omission to all non-final, and rejects malformed, duplicate, excessive, or unknown names before a machine escapes. | ✓ VERIFIED | Input parsing/defaulting and bounded validation are at `core.py:1509-1527`; canonical states receive the marker at 1529-1536; output sorts explicit names at 1635-1642. Round-trip, legacy omission, all invalid-shape cases, exact schema, and async deserialization tests passed. |
| 15 | `from_dict` builds marked canonical States before one contextual transition transaction, so an outgoing final-source row fails atomically with its row index. | ✓ VERIFIED | Canonical states are constructed at `core.py:1529-1536`, all requests are accumulated at 1561-1591, and exactly one contextual apply occurs at 1593-1598. The outgoing-final dictionary regression passed with exact row context; incoming-final round-trip passed. |
| 16 | Sync/async, source/native, and restored pure-source behavior agree, with no generated native shadow left in the source package. | ✓ VERIFIED | Fresh `task pure-source-check` reports `src/fast_fsm/core.py`; no `core*.so` or `core*.pyd` exists under `src/fast_fsm`. The current pure-source focused suite passed. The clean convergence review independently records passing compiled final-state/typing tests and a pure-wheel check, while Plan 27-03's ordered native gate and validation audit record compiled behavior followed by exact shadow relocation and restored source execution. |

**Score:** 16/16 truths verified (0 present, behavior-unverified)

All four ROADMAP success criteria are covered: truths 1-2 prove explicit declaration/query, truths 3-10 prove the construction/dead-end distinction, truth 11 proves commit/failure semantics, and truths 12-16 prove control and persistence continuity.

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `src/fast_fsm/core.py` | State marker, termination query, canonical rejection, lifecycle/control/clone, and persistence implementation | ✓ VERIFIED | 6,485 lines; substantive implementations at lines 840-967, 1509-1643, 1823-1997, 2354-2360, 3377-3573, and sync/async lifecycle runners. Imported and exercised by all linked tests. |
| `src/fast_fsm/core.pyi` | PEP 561 public final-state typing surface | ✓ VERIFIED | 466 lines; exposes `final: bool` on every constructor and `is_terminated: bool`; blocking mypy and strict downstream regressions pass. |
| `tests/test_final_states.py` | Central FINAL-01 through FINAL-06 behavioral oracle | ✓ VERIFIED | 395 lines, 35 collected tests; declaration, construction, controls, clone, persistence, legacy, invalid input, and async cases all active and passing. |
| `tests/test_mypyc_guard.py` | Slots, AST shape, consumer typing, native, and artifact guards | ✓ VERIFIED | 3,047 lines, 145 collected tests; final-state structural/typing guards pass. Native-only and platform-only skips are conditional rather than disabled requirement tests. |
| `tests/test_graph_invariants.py` | Atomic topology, schema, canonical-resolution, helper, declarative, and clone proof | ✓ VERIFIED | 1,071 lines, 45 collected tests; final-source transaction and source-only validation guards pass. |
| `tests/test_builder.py` | Builder staging/cache repair proof | ✓ VERIFIED | 2,794 lines, 235 collected tests; final-source failed-build repair test passes. |
| `tests/test_hypothesis.py` | Generated final-source atomicity/property proof | ✓ VERIFIED | 279 lines, 11 collected tests; reordered invalid batches and current-marker equivalence pass. |
| `tests/test_async.py` | Async construction/clone parity | ✓ VERIFIED | 1,356 lines, 83 collected tests; async final-source registration and clone cases pass. |
| `tests/test_transition_lifecycle.py` | Post-commit sync failure and async cancellation truth | ✓ VERIFIED | 1,380 lines, 47 collected tests; entry-time visibility and deterministic pre/post-commit matrices pass. |
| `.specify/memory/spr-core-api.md` | Living public final-state contract | ✓ VERIFIED | 75 substantive contract bullets; lines 8-10, 14, 52, 65, and 69 record declaration, construction, runtime, control, clone, and dictionary semantics. |

**Artifacts:** 10/10 verified at existence, substance, and wiring levels.

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| `State.__init__` | `State.final` | private slotted `_final` plus getter-only property | ✓ WIRED | `core.py:850-867`; behavioral immutability/slots tests and slots audit pass. |
| State factories/subclasses | `State.__init__` | keyword-only `final=final` forwarding | ✓ WIRED | `core.py:870-900`, `939-955`, `5337-5352`; async declarative inheritance tested. |
| `StateMachine.is_terminated` | canonical current State | direct `_current_state.final` read | ✓ WIRED | `core.py:2354-2360`; AST guard proves one attribute chain and no machine latch. |
| `_normalize_transition_request` | `_resolve_canonical_state` | resolve then inspect `source.final` | ✓ WIRED | `core.py:1852-1855`; structural ordering and foreign-object tests pass. |
| Retained adapters | `_apply_transition_requests_owned` | immutable request tuples | ✓ WIRED | Adapter source guards plus direct/batch/helper/factory/builder/declarative/clone/async behavior tests pass. |
| `_apply_transition_requests_owned` | `_commit_transition_plan` | prepare complete tuple, then publish once | ✓ WIRED | `core.py:1977-1997`; rollback/property tests pass. |
| `_commit_transition` | `is_terminated` | authoritative current-State assignment before destination work | ✓ WIRED | `core.py:3553-3573`, `3741-3758`, `4517-4534`; lifecycle tests observe finality inside entry. |
| reset / force / restore | `_force_state_owned` | shared control transition and derived read | ✓ WIRED | `core.py:3377-3451`; bidirectional control test passes. |
| `to_dict` | `from_dict` | sorted JSON-native `final_states`, omission default | ✓ WIRED | `core.py:1509-1536`, `1635-1642`; exact round-trip and legacy tests pass. |
| `from_dict` | canonical request transaction | marked States plus one `error_contexts` apply | ✓ WIRED | `core.py:1529-1598`; exact row-context rejection test passes. |

**Wiring:** 10/10 connections verified manually. The generic key-link query could not interpret symbol names as filesystem paths, so its zero score was not treated as implementation evidence; each semantic link was traced directly instead.

### Data-Flow Trace (Level 4)

N/A — Phase 27 is a core-library semantics phase with no rendered values, API-to-database path, or dynamic UI data source. Runtime truth flows directly from the canonical `State._final` slot through `StateMachine._current_state.final`, and persistence flow is covered above.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| Pure-source origin | `task pure-source-check` | `core_origin: src/fast_fsm/core.py`, version `0.4.0` | ✓ PASS |
| Phase 27 behavior and adjacent invariants | `uv run pytest tests/test_final_states.py tests/test_graph_invariants.py tests/test_transition_lifecycle.py tests/test_builder.py tests/test_async.py tests/test_hypothesis.py tests/test_mypyc_guard.py -x -q --disable-warnings` | Exit 0; all 601 collected cases completed, with six expected conditional skips | ✓ PASS |
| Lint | `uv run ruff check` on implementation/stub and seven linked test modules | `All checks passed!` | ✓ PASS |
| Blocking typing | `task typecheck-mypy` | 7 package files and explicit `core.py` both report no issues | ✓ PASS |
| Slots policy | `uv run python tools/release_evidence.py slots-policy --json` | Exit 0; `State` and `StateMachine` slot-protected, only registered exceptions retain dictionaries | ✓ PASS |
| Lock freshness | `uv lock --check` | 76 packages resolved, exit 0 | ✓ PASS |
| API docs | `uv run sphinx-build -b html docs docs/_build/html -W --keep-going` | Build succeeded with warnings treated as errors | ✓ PASS |

### Probe Execution

No phase probe is declared in any Phase 27 PLAN/SUMMARY, and this core-library feature is not a probe-driven migration/tooling phase. Step 7c is not applicable.

### Requirements Coverage

| Requirement | Source Plans | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| FINAL-01 | 27-01 | Immutable `final=True` declaration | ✓ SATISFIED | Truth 1; exact validation, slots, read-only property, construction propagation, consumer typing, active unit/structural tests. |
| FINAL-02 | 27-01 | O(1) termination query including initial-final | ✓ SATISFIED | Truth 2; direct query body and sync/async behavioral tests. |
| FINAL-03 | 27-02, 27-03 | Atomic error for every outgoing-final construction path | ✓ SATISFIED | Truths 7-10 and 15; one canonical branch, complete prepare-before-publish transaction, adapter/property tests, dictionary row context. |
| FINAL-04 | 27-01 | Non-final sink differs from final completion | ✓ SATISFIED | Truth 3; equal dead-end topology with differing explicit marker behavior. |
| FINAL-05 | 27-03 | Termination survives post-commit entry/observer/cancellation failure | ✓ SATISFIED | Truth 11; source ordering plus sync and async behavioral matrices. |
| FINAL-06 | 27-03 | Reset, restore, clone, async, and deserialization continuity | ✓ SATISFIED | Truths 12-16; control, clone, persistence, class-identity, native/pure evidence. |

All six Phase 27 IDs appear in PLAN frontmatter, REQUIREMENTS.md, and the ROADMAP mapping. No Phase 27 requirement is orphaned.

### Decision Coverage

`check.decision-coverage-verify` reports **12/12 honored**, with no missing CONTEXT.md decision. This gate is advisory and did not need to alter the passing status.

### Test Quality Audit

| Test File / Area | Linked Requirements | Active | Skipped | Circular | Strongest Assertion | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| `tests/test_final_states.py` | FINAL-01–FINAL-06 | 35 collected | 0 | No | Multi-step behavioral, identity, exact error, round-trip | ✓ PASS |
| `tests/test_graph_invariants.py` | FINAL-03, FINAL-06 | 45 collected | 2 conditional private-injection skips under native only; active in source mode | No | Identity fingerprint, version, topology, exact schema | ✓ PASS |
| `tests/test_builder.py` | FINAL-03 | 235 collected | 0 requirement-specific skips | No | Staging fingerprint, cache absence, repair/retry | ✓ PASS |
| `tests/test_hypothesis.py` | FINAL-02, FINAL-03 | 11 collected/property-generated | 0 | No | Generated ordering and all-or-nothing behavior | ✓ PASS |
| `tests/test_async.py` | FINAL-03, FINAL-06 | 83 collected | 0 requirement-specific skips | No | Type/identity/version/rollback behavior | ✓ PASS |
| `tests/test_transition_lifecycle.py` | FINAL-05 | 47 collected | 0 | No | Stage-by-stage commit, state, history, cancellation, observer behavior | ✓ PASS |
| `tests/test_mypyc_guard.py` | FINAL-01, FINAL-02, native parity | 145 collected | native/platform conditions only | No — file writes create independent temporary consumer/source fixtures | AST, strict typing, artifact/native structure | ✓ PASS |

**Disabled tests on requirements:** 0. Conditional skips do not disable requirement coverage: pure-source private injection ran in this verification, while native behavior is covered by public semantic tests and the clean review's compiled gate.  
**Circular patterns detected:** 0. Temporary files in `test_mypyc_guard.py` are independently authored invalid/consumer fixtures, not expected values generated by the system under test.  
**Insufficient assertions:** 0.

### Review, Security, Regression, and UI Gates

| Gate | Status | Evidence |
| --- | --- | --- |
| Code review | ✓ PASS | `27-REVIEW.md` is clean after convergence: 11 files reviewed, 0 critical/warning/info findings. It records blocking mypy, stubtest, Ruff, focused pure/native tests, and pure-wheel contents. |
| Nyquist validation | ✓ PASS | `27-VALIDATION.md` is `validated`, `nyquist_compliant: true`, with all six requirement routes green and audit `Gaps found: 0`. |
| Security | ✓ PASS | `27-SECURITY.md` is `verified`, ASVS L1, 13/13 threats disposed, `threats_open: 0`; exact input, transaction, bounded-error, lifecycle, and native-shadow mitigations correspond to passing tests/source. |
| UI | N/A | `27-UI-REVIEW.md` correctly records no frontend, visual component, dev server, or `UI-SPEC.md`; Phase 27 is a Python runtime/API phase. |
| Phase 26 prerequisite/regression | ✓ PASS | `26-VERIFICATION.md` passed 24/24 and established the canonical transaction. Current source still uses the verified prepare-all/publish-once seam, and fresh Phase 27 graph/builder/async/property regressions passed against it. |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| None | — | No unreferenced `TBD`, `FIXME`, `XXX`, TODO/HACK/placeholder implementation, or generated native source shadow in Phase 27 files | — | No blocker or warning. |

The sole textual `not available` hit is an existing fixed runtime error constant unrelated to a Phase 27 stub. Empty-return patterns inspected in `core.py` are established control/helper behavior, not placeholder implementations.

## Human Verification

N/A — infrastructure/core-library phase with no user-facing visual or external-service behavior. All state-transition, cancellation, ordering, construction, control, persistence, typing, documentation, and source-origin claims have active programmatic evidence; no behavior-dependent truth remains unverified.

## Gaps Summary

**No gaps found.** Phase 27 achieves its goal, all six FINAL requirements are satisfied, all four roadmap success criteria are behaviorally proven, and no human-only check remains.

---

_Verified: 2026-09-16T03:24:01Z_  
_Verifier: the agent (gsd-verifier)_
