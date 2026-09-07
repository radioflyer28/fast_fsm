---
phase: 21-priority-contract-atomic-registration
verified: 2026-09-06T22:49:59Z
status: passed
score: 6/6 must-haves verified
behavior_unverified: 0
overrides_applied: 0
decision_coverage:
  honored: 8
  total: 8
  not_honored: []
---

# Phase 21: Priority Contract & Atomic Registration Verification Report

**Phase Goal:** Library consumers can construct immutable, finite, deterministically ordered candidate groups through the existing transition API without partial topology mutation.
**Verified:** 2026-09-06T22:49:59Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | One existing `add_transition(..., *, priority=...)` API creates direct singleton or immutable ordered candidate topology; this phase adds no public candidate inspection API. | VERIFIED | `core.py:579-624,1498-1536` has keyword-only `priority`, direct `TransitionEntry`, and private frozen `_TransitionGroup`; `test_priority_registration_keeps_singletons_direct_and_groups_immutable` passed in pure and compiled checks. |
| 2 | Exact non-boolean integer priorities are deterministic; lower values sort first; tie conflicts are atomic; exact normalized duplicates are no-ops. | VERIFIED | `core.py:620-624,1447-1496` validates with `type(priority) is int`, stages all replacements, and sorts only during registration. Pure and native exact-type/rollback/property tests passed; an additional direct same-`Condition` identity spot-check passed. |
| 3 | Batch, multi-source, bidirectional, emergency, and builder registrations carry priority unchanged and publish all affected topology or none, with one graph-version increment. | VERIFIED | `core.py:1538-1750,4783-5063` normalizes fan-out before `_commit_transition_plan`; `test_priority_helpers_transport_atomic_fanout_without_interpreting_winners` and builder tests passed in both modes. |
| 4 | Clones capture immutable slot values while owning independent transition dictionaries, graph versions, and locks. | VERIFIED | `core.py:2590-2650` copies outer/inner mappings under the ownership read boundary; `test_clone_capture_waits_for_a_topology_owner_and_copies_mutable_tables` plus direct grouped-clone isolation spot-check passed. |
| 5 | The project contract preserves O(1) lookup/singleton dispatch while finite group construction and future selection are local O(k), with no dispatch-time sort. | VERIFIED | Constitution §I, SPR core API, and ADR-007 state the split; `test_priority_singleton_trigger_keeps_direct_constant_lookup` passed pure and compiled. |
| 6 | The explicit singleton-or-group union remains mypyc-safe, and compiled singleton dispatch meets the 200,000 ops/sec gate. | VERIFIED | `core.py:599-606,839`, AST/native guards, `task typecheck-mypy`, slots audit, compiled build smoke test, and compiled targeted suite all passed. |

**Score:** 6/6 truths verified (0 present, behavior-unverified)

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `src/fast_fsm/core.py` | Typed singleton-or-group topology, atomic registrar, helpers, clone boundary | VERIFIED | Substantive implementation at the registration, helper, clone, dispatch, and builder seams. |
| `.specify/decisions/ADR-007-priority-topology.md` | Persistent topology decision | VERIFIED | Accepted ADR records D-01 through D-08 and downstream deferrals. |
| `.specify/memory/constitution.md` | Honest complexity contract | VERIFIED | Explicit O(1) singleton/O(k) finite-group rule. |
| `.specify/memory/spr-core-api.md` | Living API/compiled-boundary contract | VERIFIED | Documents exact priority, storage, atomicity, builder, and deferral boundaries. |
| `tests/test_graph_invariants.py` / `tests/test_hypothesis.py` | Registration, identity, ordering, immutability, rollback proof | VERIFIED | Active value- and behavior-level assertions; no disabling markers. |
| `tests/test_builder.py` / `tests/test_ownership_concurrency.py` | Builder fan-out and clone ownership proof | VERIFIED | Active construction/repair/ownership assertions. |
| `tests/test_mypyc_guard.py` / `tests/test_performance_benchmarks.py` | Native typing/layout and singleton path proof | VERIFIED | AST checks plus native execution and counted lookup/throughput tests. |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- |
| `StateMachine.add_transition` | `_normalize_transition_request` | Object-typed keyword priority reaches exact normalizer before `_PreparedTransition` | WIRED | Calls at `core.py:1508-1517`; normalizer at `1365-1445`; validation at `620-624`. |
| `_commit_transition_plan` | `_transitions` | Merge every local replacement before any publish and version once | WIRED | `core.py:1447-1470` stages all slots, then writes identity-changing values. |
| `TransitionEntry` | `_TransitionGroup` | Second distinct priority promotes to a sorted tuple-backed immutable group | WIRED | `core.py:1473-1496`; tested under registration-order permutations. |
| Helpers and `FSMBuilder` | `_commit_transition_plan` | Complete fan-out becomes one batch publication | WIRED | Helpers prepare all rows before commit; builder calls `candidate.add_transitions(transition_rows)` once. |
| `clone` | `_transitions` | Owner-aware table copy shares immutable values only | WIRED | `core.py:2590-2650`; concurrency regression and grouped spot-check exercise it. |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| Pure topology, atomicity, helper, clone, union, and singleton lookup | `FAST_FSM_BUILD_MODE=pure uv run pytest ... -k 'priority or candidate or atomic or clone_capture_waits or constant_lookup' -x -q` | 22 passed, 6 compiled-only skips | PASS |
| Same-Condition duplicate idempotence and grouped clone isolation | Local `uv run python -c` spot-check | `condition-identity and clone-isolation: OK` | PASS |
| Compiled native build | `FAST_FSM_BUILD_MODE=compiled task build-check` | Native extension built; `Compiled smoke test: OK` | PASS |
| Compiled priority/atomic/helper/clone/throughput behavior | `FAST_FSM_BUILD_MODE=compiled uv run pytest ... -k 'priority or candidate or atomic or clone_capture_waits or constant_lookup or test_trigger_min_throughput' -x -q -s -p no:cov` | 29 passed; `fast_fsm.core` resolved to the generated `.so` during the run | PASS |
| Type, lint, and layout contracts | `uv run ruff check ...`; `task typecheck-mypy`; `task typecheck-ty`; `uv run python tools/release_evidence.py slots-policy --json` | All passed | PASS |

The full pure suite was started once, but the command runner detached before an exit result could be captured. It is deliberately not counted as verification evidence; all phase-specific behavior above was independently exercised successfully.

### Requirements Coverage

| Requirement | Source Plans | Status | Evidence |
| --- | --- | --- | --- |
| PRIO-01 | 21-01, 21-02 | SATISFIED | Repeated priority-aware registration through the existing public API, direct singleton and private group storage, helper and builder transport. |
| PRIO-02 | 21-01, 21-02 | SATISFIED | Exact-type native/pure rejection, registration-order property, sorted groups, conflict rollback, and duplicate identity no-op. |
| PRIO-03 | 21-02 | SATISFIED | Atomic helper/builder fan-out, graph-version behavior, owner-safe clone copy, and compiled proof. |

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| `test_graph_invariants.py`, `test_hypothesis.py` | PRIO-01, PRIO-02 | Yes | No | No | Value/behavioral/property | PASS |
| `test_builder.py`, `test_ownership_concurrency.py` | PRIO-03 | Yes | No | No | Behavioral | PASS |
| `test_mypyc_guard.py`, `test_performance_benchmarks.py` | PRIO-02, PRIO-03 | Yes | Pure-mode compiled test skips only; native run passed | No | AST/value/behavioral | PASS |

No requirement-linked disabled test is relied upon. The compiled-only test skips under pure import by design and was executed successfully against a freshly built native core.

### Decision Coverage

All 8 trackable CONTEXT.md decisions are honored by shipped artifacts. This is a non-blocking coverage check.

### Anti-Patterns Found

No blocker debt markers or implementation stubs found in Phase 21 source, policy, ADR, or test artifacts. The fixed string `Priority candidate resolution is not available` is the intentional fail-closed Phase 21 grouped-runtime boundary, not a placeholder.

## Human Verification

N/A — infrastructure/foundation phase with no user-facing elements. All Phase 21 acceptance criteria were exercised programmatically. Runtime winner selection, public inspection/serialization parity, diagnostics, and drone guidance remain deliberately deferred to Phases 22–25.

---

_Verified: 2026-09-06T22:49:59Z_
_Verifier: the agent (gsd-verifier)_
