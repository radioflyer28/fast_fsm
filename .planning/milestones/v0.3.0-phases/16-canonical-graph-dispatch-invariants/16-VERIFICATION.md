---
phase: 16-canonical-graph-dispatch-invariants
verified: 2026-09-01T15:29:41Z
status: passed
score: 9/9 must-haves verified
behavior_unverified: 0
overrides_applied: 0
decision_coverage:
  honored: 18
  total: 18
  not_honored: []
gaps: []
human_verification: []
---

# Phase 16: Canonical Graph & Dispatch Invariants Verification Report

**Phase Goal:** Users get one canonical machine topology and equivalent construction and dispatch behavior across sync, async, builder, and declarative APIs.
**Verified:** 2026-09-01T15:29:41Z
**Status:** passed
**Re-verification:** No — initial goal-backward verification

## Goal Achievement

The five roadmap success criteria and twenty more detailed PLAN truth clauses
collapse into the nine requirement-level observable truths below. Each runtime
truth has behavioral evidence in both an asserted pure-source checkout and a
separate checkout containing a freshly built mypyc extension. SUMMARY.md and the
existing review, validation, security, and performance reports were treated as
claims and were not used as substitutes for code or command evidence.

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Invalid, foreign, duplicate, or incomplete transition endpoints are rejected before any topology mutation. | ✓ VERIFIED | `_normalize_transition_request()` resolves every endpoint before `_commit_transition_plan()`; `tests/test_graph_invariants.py` fingerprints registry, transition, version, current-state, and snapshot identity before/after all rejection families. The pure and native matrices passed. |
| 2 | State registration is exact-identity canonical: the same object is idempotent and a distinct same-name object cannot replace it. | ✓ VERIFIED | `_register_state()` checks the existing object with `is` before writing either dictionary; graph and builder publication tests exercise same-object, equality-object, Unicode-name, and conflicting-object cases in both modes. |
| 3 | Tools can obtain a fresh, immutable, deterministically ordered, versioned internal graph snapshot containing the declared initial state. | ✓ VERIFIED | Frozen slot dataclasses `_GraphSnapshot`/`_GraphTransition` are rebuilt from sorted canonical dictionaries; graph tests verify freshness, tuple immutability, identities, initial/current independence, public-schema stability, and topology-only version changes in both modes. |
| 4 | A successful builder freezes every mutator, repeated builds return the same machine, and a failed build remains repairable without a cached partial machine. | ✓ VERIFIED | All eight public mutator/registrar/force paths call `_ensure_mutable()`; `build()` constructs and wires local `candidate` before assigning `_machine`. `TestFSMBuilderPublication` uses staging/topology fingerprints for freeze, repair, cache identity, ordering, and callback non-replay in pure and native runs. |
| 5 | Nested asynchronous requirements, including `unless=` and built-in wrappers, select async mode automatically while explicit sync fails before publication. | ✓ VERIFIED | Builder preflight and runtime evaluation share `_condition_children()`/`_contains_async_requirement()`; tests cover native coroutines, custom and generator-based awaitables, every wrapper edge, cycles, shared DAGs, deep graphs, queued callbacks, declarative guards, explicit modes, and exactly-once awaiting in both artifact modes. |
| 6 | Sync/async `can_trigger*()` and `trigger*()` preserve positional identities and use one fresh filter-then-cap sanitized keyword mapping per guard evaluation. | ✓ VERIFIED | All four paths call `_prepare_transition()`; sync and async machine evaluators propagate the prepared args/mapping. `TestGuardContextParity`, `TestDeclarativeGuardContextParity`, and direct composite tests assert order, identity, fresh copies, caller preservation, one sanitization, and short-circuit behavior in both modes. |
| 7 | Ordinary sync and async declarative dispatch invokes the one canonical source/trigger/target handler exactly once. | ✓ VERIFIED | Ordinary triggers resolve through `_resolve_declarative_handler()` and invoke through one sync/async helper; compatibility methods use the same resolver/invoker. Counter fixtures cover matches, mismatches, normalized results, false/invalid/raising handlers, and exact call counts in both modes. |
| 8 | Internal resolution and dispatch seams stay aligned without splitting the mypyc boundary or removing public symbols/signatures. | ✓ VERIFIED | `setup.py` passes only `src/fast_fsm/core.py` to `mypycify`; interpreted condition classes remain in `conditions.py`/`condition_templates.py`, public exports and typed downstream subclass/callable shapes are guarded, and the native matrix imported `core.cpython-312-darwin.so`. Ruff, strict mypy, Sphinx `-W`, and doctests passed. |
| 9 | History rejects invalid capacities atomically, provides O(1) bounded FIFO eviction, and returns defensive chronological copies. | ✓ VERIFIED | `enable_history()` validates before assignment and creates `deque(maxlen=...)`; transition execution only appends. Sync/async history tests cover non-positive/non-integer/bool rejection, retained prior configuration, reset, capacity one, FIFO order, copies, disabled state, and clone behavior. The native history performance gate passed. |

**Score:** 9/9 truths verified (0 present-but-behavior-unverified)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/fast_fsm/core.py` | Canonical topology, shared dispatch, transactional builder, declarative invocation, bounded history | ✓ VERIFIED | Substantive implementation; every private seam is called from its public path and exercised in both modes. |
| `src/fast_fsm/conditions.py` | Interpreted guard API and awaitable-safe negation/continuation | ✓ VERIFIED | Public classes remain interpreted; deferred owners preserve ordering, ownership, closure, and exactly-once awaiting. |
| `src/fast_fsm/condition_templates.py` | Awaitable-safe And/Or/Not composites | ✓ VERIFIED | Direct checks delegate to the shared compound/negation helpers; sync and async branches are exercised. |
| `tests/test_graph_invariants.py` | Canonical registry, atomicity, snapshot/version proof | ✓ VERIFIED | Active value/identity/behavior assertions; no skips or generated oracle. |
| `tests/test_builder.py` | Builder lifecycle and sync declarative proof | ✓ VERIFIED | Active state-transition and exact-call-count assertions. |
| `tests/test_async.py` | Async wrapper, dispatch, declarative, and history parity | ✓ VERIFIED | Active awaited behavioral assertions in the pure/native matrix. |
| `tests/test_safety_kwargs.py` | Four-path guard-context proof | ✓ VERIFIED | Active identity, cardinality, ordering, mutation, filter/cap, and logging assertions. |
| `tests/test_condition_templates.py` | Direct composite awaitable contract | ✓ VERIFIED | Covers native/custom/generator awaitables, closure, errors, ordering, continuation, and short-circuiting. |
| `tests/test_advanced_functionality.py` | History capacity/FIFO/copy/clone proof | ✓ VERIFIED | Active behavioral assertions including failure non-mutation. |
| `tests/test_mypyc_guard.py` | Slots, exports, compilation boundary, and evidence-integrity proof | ✓ VERIFIED | AST/runtime/typed-downstream and fail-closed runner assertions passed. |
| `tests/test_performance_benchmarks.py` | Compiled trigger floor and bounded-history cost | ✓ VERIFIED | Native-selected tests enforce `>= 200,000` trigger ops/sec and `<= 2x` history degradation. |
| `tools/phase16_isolated_verify.py` | Origin-safe pure/native harness | ✓ VERIFIED | Exports `HEAD`, overlays an explicit inventory, rejects unsafe paths/native pure shadows, asserts origin before execution, and completed exit 0. |
| `docs/dev/architecture.md`, `docs/dev/testing.md`, `.specify/memory/spr-core-api.md` | Maintainer contract and verification procedure | ✓ VERIFIED | Match actual private/public boundaries; HTML warnings-as-errors and three doctests passed. |
| `evidence/release-baseline.json` | Current pure-source quality evidence | ✓ VERIFIED | Independent freshness check reports 1,221/1,221 passing, 96.64% total and 95.13% core coverage, pure `.py` origin. |
| `16-PERFORMANCE-EVIDENCE.md` | Environment-labelled before/after and review-remediation evidence | ✓ VERIFIED | Records origins, inventory, commands, historic exact observations, and separates measured observations from durable floors. |

**Artifacts:** 16/16 unique required artifacts verified at existence, substance, and wiring levels.

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `add_state` / transition constructors | `_states`, `_transitions`, `_graph_version` | Canonical resolve, complete normalization, then `_commit_transition_plan()` | ✓ WIRED | No write occurs in endpoint resolution; compound helpers commit complete prepared tuples. |
| `_graph_snapshot()` | canonical dictionaries and `_initial_state` | Fresh sorted tuple projection | ✓ WIRED | No cache or public serialization path intervenes. |
| Four can/do APIs | `_prepare_transition()` | One direct dictionary lookup and optional sanitized copy | ✓ WIRED | Calls at `core.py` lines 1462, 1987, 2147, 2448, and 2508 cover public and supporting dispatch paths. |
| Wrapper classifier | builder preflight and async evaluator | `_condition_children()` / `_contains_async_requirement()` | ✓ WIRED | Construction classification and runtime evaluation recognize the same exact built-in edges. |
| Every builder mutator | `_ensure_mutable()` | First operational guard | ✓ WIRED | Eight mutator/registrar/force paths invoke the freeze check. |
| `FSMBuilder.build()` | machine classes and `_machine` | Preflight, local candidate wiring, cache assignment last | ✓ WIRED | `_machine = candidate` occurs only after all state, transition, and callback wiring. |
| Ordinary and compatibility dispatch | declarative metadata | Shared resolver plus one sync/async invoker | ✓ WIRED | Trigger methods invoke once after successful ordinary dispatch; helpers use the same boundary. |
| `enable_history()` / transition execution | `collections.deque` | Validated `maxlen` plus append-only eviction | ✓ WIRED | No `pop(0)` or unbounded enabled buffer remains. |
| Phase 16 suites | pure and native core artifacts | Isolated export, explicit overlay, pre-import origin assertion | ✓ WIRED | Independent command observed `.py` and fresh `.so` origins before their matrices. |
| Maintainer docs | runtime and harness | Exact internal names, boundaries, and commands | ✓ WIRED | Documentation build and doctests passed against the overlaid source. |

**Wiring:** 10/10 critical connection groups verified.

### Data-Flow Trace (Level 4)

This is an internal library phase rather than a rendered-data phase. The relevant
state flow still terminates in real authoritative containers rather than static
fixtures.

| Artifact | Data | Source | Produces real state | Status |
|----------|------|--------|---------------------|--------|
| `_graph_snapshot()` | states/transitions/version/initial | Live `_states`, `_transitions`, `_graph_version`, `_initial_state` | Yes | ✓ FLOWING |
| `_prepare_transition()` | selected entry and guard context | Current canonical state plus `_transitions` and caller input | Yes | ✓ FLOWING |
| `FSMBuilder.build()` | published machine | Staged canonical objects/transitions/callbacks | Yes, after complete wiring | ✓ FLOWING |
| Declarative dispatch | selected handler | Live source-state `_handlers` metadata and canonical target | Yes | ✓ FLOWING |
| `history` | chronological records | Live bounded deque appended by transition execution | Yes, returned as a new list | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Asserted pure Phase 16 semantics | `uv run python tools/phase16_isolated_verify.py --suite phase16` | Pure `.py` origin asserted; semantic matrix passed | ✓ PASS |
| Fresh compiled semantic parity | same authoritative command | Fresh mypyc `.so` origin asserted; identical semantic matrix passed | ✓ PASS |
| Compiled throughput/history contract | native performance selection inside the authoritative command | Three tests passed; `test_trigger_min_throughput` enforces `ops_per_sec >= 200_000` and history enforces degradation `<= 2.0x` | ✓ PASS |
| Full pure quality/release gate | pure release segment inside the authoritative command | 1,221/1,221 tests; 96.64% total / 95.13% core coverage; Ruff, mypy, docs, doctests, freshness all green | ✓ PASS |

The performance test intentionally reports its measured rate only on failure, so
this verifier does not invent an exact current number. Its passing native assertion
is direct evidence that the measured rate was at least 200,000 operations/second.

### Probe Execution

No `probe-*.sh` path is declared by a Phase 16 PLAN/SUMMARY and no conventional
Phase 16 shell probe exists. The explicitly declared executable verification
surface is the Python isolation harness above, which was run independently.

### Requirements Coverage

| Requirement | Source Plans | Description | Status | Evidence |
|-------------|--------------|-------------|--------|----------|
| GRAF-01 | 16-01, 16-05 | Invalid endpoints reject atomically | ✓ SATISFIED | Resolver/normalize/commit separation plus graph-fingerprint rejection matrix in pure/native runs. |
| GRAF-02 | 16-01, 16-03, 16-05 | Same-name objects cannot replace canonical state | ✓ SATISFIED | Exact `is` checks in machine and builder; identity/non-mutation tests passed. |
| GRAF-03 | 16-01, 16-05 | Immutable deterministic versioned snapshot | ✓ SATISFIED | Frozen tuple records and comprehensive snapshot/version tests passed. |
| GRAF-04 | 16-03, 16-05 | Builder freeze, repair, idempotent build | ✓ SATISFIED | All-mutator freeze and publish-last failure/repair tests passed. |
| GRAF-05 | 16-02, 16-03, 16-05 | Recursive async detection including `unless=` | ✓ SATISFIED | Shared classifier plus complete wrapper/awaitable/cycle/force-mode behavioral matrix passed. |
| GRAF-06 | 16-02, 16-05 | Positional and sanitized keyword parity | ✓ SATISFIED | Four-path recording fixtures and direct wrapper propagation assertions passed. |
| GRAF-07 | 16-04, 16-05 | Declarative handlers execute exactly once | ✓ SATISFIED | Sync/async invocation counters and compatibility-boundary cases passed. |
| GRAF-08 | 16-01 through 16-05 | Shared seams and one mypyc compilation unit | ✓ SATISFIED | Source wiring, structural guards, public API checks, native build, type/docs/release gates all passed. |
| LIFE-07 | 16-04, 16-05 | Positive capacity, O(1) eviction, copies | ✓ SATISFIED | Validated deque implementation plus sync/async behavior and native performance tests passed. |

**Coverage:** 9/9 requirements satisfied. No Phase 16 requirement is orphaned from the plans.

### Test Quality Audit

| Test Area | Linked Requirements | Active evidence | Disabled-only or circular? | Assertion strength | Verdict |
|-----------|---------------------|-----------------|----------------------------|-------------------|---------|
| Graph invariants | GRAF-01/02/03/08 | Pure + native | No | Identity/value plus multi-step non-mutation | ✓ STRONG |
| Builder and declarative | GRAF-02/04/05/07/08 | Pure + native | No | Cache identity, staging fingerprints, state/type, exact call count | ✓ STRONG |
| Guard/async/composites | GRAF-05/06/08 | Pure + native | No | Ordering, object identity, await/close counts, exceptions, short-circuit state | ✓ STRONG |
| History/performance | LIFE-07/GRAF-08 | Pure + native selection | No | FIFO values/timestamps/copies plus timed threshold and ratio | ✓ STRONG |
| Evidence/mypyc boundary | GRAF-08 | Full pure gate + fresh native contexts | No circular oracle | AST/runtime origin, typed downstream compile, byte-preservation, explicit negative cases | ✓ STRONG |

The only skip mechanism in linked files is a compiler-availability guard for a
native-only release-evidence fixture. A C compiler was available here, the fresh
native builds succeeded, and the full result reported 1,221/1,221 passed with no
skipped count. File-writing matches in release-evidence tests create isolated
adversarial fixtures; they do not generate expected values from the system under
test.

### Negative Contract / Prohibition Review

The PLAN frontmatter contains legacy string-form `[UNVERIFIED — no SPEC]`
prohibitions rather than structured `{statement, verification}` entries. They
were therefore not silently treated as deterministically enforced prohibitions;
the verifier inspected each family directly. All are honored: no public graph
snapshot/export was added, no locks/ownership/runtime graph dependency appeared,
condition modules remain interpreted, raw payload values were not added to logs,
builders do not warn-and-drop async behavior or cache failed candidates, and the
docs do not claim Phase 17 lifecycle, Phase 18 concurrency, Phase 19 public tool
migration, or Phase 20 installed-artifact parity.

### Anti-Patterns Found

| File set | Pattern | Severity | Impact |
|----------|---------|----------|--------|
| 22 implementation/test/doc/evidence files reviewed for Phase 16 | `TBD`, `FIXME`, `XXX` | None | No blocker debt markers found. |
| Same scope | `TODO`, `HACK`, `PLACEHOLDER`, stub returns, coming-soon text | None | No incomplete implementation marker found. |
| Requirement-linked tests | disabled-only tests, circular expected-value generation, weak existence-only assertions | None | No test-quality blocker or warning found. |

### Decision Coverage

`check.decision-coverage-verify` reported all 18 trackable decisions in
`16-CONTEXT.md` honored by shipped artifacts (18/18, no omissions). This is a
non-blocking heuristic gate; the concrete evidence above independently verifies
the resulting behavior.

### Disconfirmation Pass

The adversarial pass specifically looked for: (1) a partial requirement hidden by
successful task completion, (2) a passing but weak/misleading requirement test,
and (3) an uncovered Phase 16 error path. It rechecked later-invalid batch writes,
foreign same-name state identity, builder cache publication after failed wiring,
wrapper cycles and deferred awaitable ownership, unsafe-key cap starvation,
declarative mismatch/failure cardinality, invalid history reconfiguration, and
native-origin performance selection. None produced a Phase 16 gap. Lifecycle
failure atomicity, concurrency ownership, diagnostics migration, and installed
wheel parity are explicitly owned by Phases 17–20 and were not misclassified as
Phase 16 failures.

### Human Verification Required

N/A — infrastructure/core-library phase with no user-facing elements. Every
behavior-dependent Phase 16 truth has a passing automated behavioral test in both
asserted pure and freshly compiled contexts.

### Gaps Summary

**No gaps found.** All roadmap criteria, all nine assigned requirements, all
required artifacts, and all critical wiring paths are verified. Later milestone
work remains deferred by the roadmap rather than missing from this phase.

---

_Verified: 2026-09-01T15:29:41Z_
_Verifier: the agent (gsd-verifier)_
