---
phase: 23-construction-declarative-serialization-parity
verified: 2026-09-07T03:07:04Z
status: passed
score: 8/8 must-haves verified
behavior_unverified: 0
overrides_applied: 0
decision_coverage:
  honored: 8
  total: 8
  not_honored: []
---

# Phase 23: Construction, Declarative & Serialization Parity Verification Report

**Phase Goal:** Every supported construction, declarative, clone, query, and serialization path preserves complete candidate identity and priority-aware behavior.
**Verified:** 2026-09-07T03:07:04Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Builders, declarative handlers, factories, quick builders, helper APIs, and deserialization construct the same ordered candidate groups as direct registration without trigger-key or handler overwrite. | ✓ VERIFIED | `quick_build()` collects complete 3/4/5-field rows and makes exactly one `add_transitions(transition_rows)` call; `quick_fsm()` delegates to it. `FSMBuilder.build()` normalizes staged rows into one batch. `test_all_constructors_preserve_the_same_priority_candidate_fingerprint` proves direct, batch, builder, quick-build, quick-fsm, declarative, and dictionary forms have identical ordered candidate fingerprints; `test_priority_helpers_transport_atomic_fanout_without_interpreting_winners` covers existing helper transport. |
| 2 | Failed builder or factory input is unpublished and retryable; malformed, tied, and async-incompatible candidates do not create a partial public topology. | ✓ VERIFIED | `quick_build()` holds its machine locally until batch registration returns; `from_dict()` validates/resolves all records before its single `_commit_transition_plan(tuple(plans))`; `FSMBuilder.build()` assigns `_machine` only after candidate registration and callback wiring. Pure probes passed for late factory rejection and repairable builder conflict; native exact-priority rejection also passed. |
| 3 | Plural declarative metadata keeps source/trigger/target/priority identity, and sync/async machine dispatch invokes only the selected handler rather than using decorator or discovery order. | ✓ VERIFIED | `_DeclarativeHandlerMetadata` and `_DeclarativeHandler` are frozen/slotted; discovery publishes `Dict[str, Tuple[_DeclarativeHandler, ...]]`. Both selector paths call `_resolve_declarative_handler(source, trigger, entry.to_state, entry.priority)`. Pure sync/async tests prove reversed attribute order, same-target priority identity, direct ambiguity failure without invocation, and one selected lifecycle handler. |
| 4 | `to_dict()`/`from_dict()` preserve every candidate and numeric priority, including same-source/trigger/target multiplicity, while serializing no callable. | ✓ VERIFIED | `to_dict()` flattens every slot through `_transition_entries()` and emits only `trigger`, `from`, `to`, `priority`, and optional scalar `condition_ref` in source/trigger/stored-priority order. `TestPrioritySerialization` passed JSON round-trip, two same-target candidates, preserved winner priority, and absence of callable representations. |
| 5 | Deserialization attaches guards through explicit opaque candidate references; ambiguous legacy bare-trigger keys fail before publication. | ✓ VERIFIED | `from_dict()` validates scalar references and expanded trigger cardinality before creating the machine; it rejects an unknown reference or a bare trigger registry key when expanded count is not one. The active serialization tests prove repeated explicit references preserve live guard identity and an ambiguous legacy mapping makes zero registrar calls in pure mode; the native Phase 23 probe proves real late tie rejection through its compiled path. |
| 6 | `can_trigger*()`, result/history/trace metadata, snapshots, cloning, and query helpers retain coherent candidate-complete behavior without changing callback payloads. | ✓ VERIFIED | Candidate-complete cold paths use `_transition_entries()` in `to_dict()`, `_graph_snapshot_owned()`, reachability, and target lookup; sync/async selectors retain direct singleton/group branches. Clone copies tables but shares immutable slots. Pure probes passed grouped query deduplication/completeness, sync/async clone isolation, selected priority metadata, callback `priority="caller-owned"` preservation, and Phase-22 lifecycle behavior. |
| 7 | The promoted representation remains slotted/type-clean and equivalent in pure and compiled `core.py`; selectors retain the Phase 22 direct singleton/local-group shape. | ✓ VERIFIED | Ruff, mypy, ty, and slots-policy checks passed. AST guards assert exact record fields, frozen/slotted records, explicit `_TransitionSlot`, no cold helper in selectors, and sole `core.py` mypyc source. A fresh native build/smoke test plus 8 compiled behavioral probes passed, then native shadows were recoverably moved from `src/fast_fsm/` and `task pure-source-check` passed. |
| 8 | Phase 23 supplies the stable construction/projection boundary without prematurely doing Phase 24 diagnostics/output or Phase 25 artifacts, benchmarks, public docs, or drone guidance. | ✓ VERIFIED | The Phase 23 code diff is confined to `core.py`, tests, and the living core SPR. No renderer, validator, benchmark, example, package/export, README/Sphinx, wheel, or release-evidence change was introduced. |

**Score:** 8/8 truths verified (0 present, behavior-unverified)

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `src/fast_fsm/core.py` | Canonical construction, plural declarations, candidate-complete projection, safe reconstruction | ✓ VERIFIED | Substantive 5,900-line core implementation; all Phase 23 hooks are wired to existing atomic registration and selectors. |
| `tests/test_advanced_functionality.py` | Serialization, reference, ambiguity, and atomicity proof | ✓ VERIFIED | Active value/behavioral tests cover JSON records, explicit/repeated/legacy guard references, malformed records, and one-plan conflict handling. |
| `tests/test_graph_invariants.py`, `tests/test_state_machine_utils.py` | Snapshot/clone/query completeness | ✓ VERIFIED | Active identity-sensitive tests assert one snapshot row per candidate, clone table isolation, all-target reachability, and deduplicated triggers. |
| `tests/test_builder.py`, `tests/test_transition_lifecycle.py`, `tests/test_async.py` | Construction and sync/async declarative behavior | ✓ VERIFIED | Active real-FSM tests cover canonical fingerprints, atomic/retryable failures, exact handler selection, lifecycle cardinality, async preflight, and async clone behavior. |
| `tests/test_mypyc_guard.py` | Typed layout and native parity proof | ✓ VERIFIED | Active AST/layout tests plus pure/native semantic probes assert record layouts, selector restrictions, native import origin, and caller payload compatibility. |
| `.specify/memory/spr-core-api.md` | Living API contract | ✓ VERIFIED | Documents canonical 3/4/5 construction rows, condition-reference ambiguity policy, plural declaration identity, candidate-complete cold projections, and unchanged callback payloads. |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| `quick_build()` / `quick_fsm()` | `StateMachine.add_transitions()` | one complete normalized adapter batch | ✓ WIRED | `core.py:1129` calls `fsm.add_transitions(transition_rows)` exactly once; the quick-factory test source-checks absence of adapter `add_transition()` calls. |
| `from_dict()` records | `_commit_transition_plan()` | validate → resolve → normalize → one publication | ✓ WIRED | `core.py:1378` calls `_commit_transition_plan(tuple(plans))` after all record/reference validation; the compiled probe asserts exactly that one call site and rejects a late priority tie. |
| `TransitionEntry.condition_ref` | serialization and graph snapshots | scalar candidate metadata | ✓ WIRED | `condition_ref` is carried by `TransitionEntry`, `_PreparedTransition`, `_GraphTransition`, `to_dict()`, and `_graph_snapshot_owned()`. |
| plural declarative metadata | Phase 22 selected entry | exact source/trigger/target/priority resolver | ✓ WIRED | Both sync/async preparation paths pass `entry.to_state` and `entry.priority` to `_resolve_declarative_handler()`, which exact-matches the plural tuple. |
| plural declarative metadata | `FSMBuilder` detection/preflight | nested loop over every declaration | ✓ WIRED | `_detect_async_requirements()` and `_preflight_async_requirements()` iterate every handler in each trigger tuple before machine publication. |
| immutable slot storage | snapshot/query/clone cold consumers | `_transition_entries()` flattening only outside dispatch | ✓ WIRED | Snapshot, serialization, reachability, and target existence flatten complete groups; AST/source tests prove neither sync nor async selector invokes the cold helper. |

### Data-Flow Trace

| Artifact | Data Variable | Source | Produces Real Data | Status |
| --- | --- | --- | --- | --- |
| `from_dict()` / `to_dict()` | candidate `condition_ref` and priority | caller config + caller-owned condition registry → prepared transition → immutable entry | One scalar record per actual stored candidate; registry callable is retained only as a live guard | ✓ FLOWING |
| `quick_build()` | transition rows | caller rows → `add_transitions()` → `_commit_transition_plan()` → `_TransitionSlot` | Real canonical slot/group used by dispatch, snapshot, clone, and queries | ✓ FLOWING |
| declarative dispatch | selected handler | decorator metadata → immutable per-trigger tuple → selected entry identity → `_PreparedDispatch` | Exactly one matched handler receives the original caller args/kwargs | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| Pure construction, serialization, clone/query, sync/async declarative, lifecycle, and callback payload contract | `FAST_FSM_BUILD_MODE=pure uv run --offline pytest` on 10 selected Phase 23 tests | 19 passed | ✓ PASS |
| Existing priority helpers, grouped query semantics, metadata, async clone, and later declarative preflight | `FAST_FSM_BUILD_MODE=pure uv run --offline pytest` on 5 named regression tests | 5 passed | ✓ PASS |
| Static/type/layout contract | Ruff format/check; `task typecheck-mypy`; `task typecheck-ty`; slots policy | all passed | ✓ PASS |
| Fresh compiled core semantics | `FAST_FSM_BUILD_MODE=compiled task build-check` plus 3 named native probes | native smoke passed; 8 passed | ✓ PASS |
| Full pure suite | `UV_CACHE_DIR=/tmp/fast-fsm-phase23-uv-cache task test` | Reached 20% then the isolated pure-sdist build test could not resolve pinned `setuptools`, `wheel`, and `mypy` from that offline cache | ℹ️ ENVIRONMENT LIMITATION — not a product assertion failure; not used as passing evidence. |

### Requirements Coverage

| Requirement | Source Plans | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| PAR-01 | 23-02, 23-03 | Declarative handlers, factories, quick builders, and deserialization preserve candidate identity and priority without singular overwrite. | ✓ SATISFIED | Cross-constructor fingerprint, one-batch quick factory, plural sync/async declarative identity, and retryable builder tests. |
| PAR-02 | 23-01, 23-02, 23-03 | Queries, result/history/tracing, clone, and snapshot behavior remain coherent with unchanged callback signatures. | ✓ SATISFIED | Candidate-complete graph/query/clone tests, lifecycle/metadata regression, callback payload probe, and selector AST/native tests. |
| PAR-03 | 23-01, 23-03 | Serialization round-trips candidate topology and candidate-specific guard attachment without callables. | ✓ SATISFIED | JSON scalar round-trip, same-target multiplicity, explicit/repeated reference, legacy ambiguity, malformed reference, and native construction probes. |

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| `test_advanced_functionality.py` | PAR-03 | Yes | No | No | Behavioral/value | PASS |
| `test_builder.py`, `test_transition_lifecycle.py`, `test_async.py` | PAR-01–02 | Yes | No | No | Behavioral/value | PASS |
| `test_graph_invariants.py`, `test_state_machine_utils.py` | PAR-02 | Yes | No | No | Behavioral/value | PASS |
| `test_mypyc_guard.py` | PAR-01–03 | Yes | Compiled-only priority-rejection case skips only when no native core is loaded; it passed in this verification's compiled run. | No | AST + behavioral/value | PASS |

Expected values are explicit source/target/priority/reference tuples and event ledgers, not output captured from the implementation. No disabled test is the sole proof of a phase requirement.

### Decision Coverage

All 8 trackable Phase 23 CONTEXT decisions are honored by shipped artifacts. This is a non-blocking coverage check.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- |
| `src/fast_fsm/core.py` | 1470 | `return []` when history is disabled | ℹ️ Info | Existing documented empty-history API behavior; it is not a Phase 23 stub and no Phase 23 data path writes to it. |

No `TBD`, `FIXME`, `XXX`, placeholder, empty implementation, disabled requirement-only test, runtime selector sorting/copying, or phase-boundary violation was found in Phase 23 source, tests, or SPR changes.

## Human Verification

N/A — infrastructure/foundation phase with no user-facing elements. All behavior-dependent construction, ordering, atomicity, cloning, callback-payload, and compiled-core invariants were exercised programmatically.

## Gaps Summary

**No gaps found.** The Phase 23 goal is achieved. The one full-suite command could not complete its isolated artifact-build test because its explicitly selected offline cache lacks pinned build requirements; this is an environment/cache limitation, not a failing implementation assertion, and installed-artifact proof remains deliberately owned by Phase 25.

---

_Verified: 2026-09-07T03:07:04Z_
_Verifier: the agent (gsd-verifier)_
