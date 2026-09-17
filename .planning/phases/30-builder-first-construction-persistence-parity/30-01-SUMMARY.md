---
phase: 30-builder-first-construction-persistence-parity
plan: 01
subsystem: core-construction
tags: [fsm-builder, declarative-state, canonical-transaction, mypyc, typing]
requires:
  - phase: 29-expected-domain-rejection
    provides: selected-entry lifecycle and declarative guard execution seams
provides:
  - Decorator-authored internal transitions through FSMBuilder's canonical transaction
  - Immutable mode-aware declarative carrier records and a synchronized public stub
  - Structural proof that declaration import remains construction-only
affects: [30-02, 30-04, 30-06, declarative-construction, persistence-parity]
actuals:
  tokens: 8094
  tasks: 2
  commits: 5
tech-stack:
  added: []
  patterns:
    - Build-time derivation of topology-complete declarative rows
    - State-owned declarative guards with mode-aware selected-entry matching
    - AST-backed cold-path and runtime/stub boundary assertions
key-files:
  created:
    - tests/test_construction_parity.py
  modified:
    - src/fast_fsm/core.py
    - src/fast_fsm/core.pyi
    - tests/test_builder.py
    - tests/test_graph_invariants.py
    - tests/test_mypyc_guard.py
    - .specify/memory/spr-core-api.md
key-decisions:
  - Declarative topology is derived afresh during build and never added to reusable builder staging.
  - Declarative guards remain handler-owned; generated canonical rows carry topology scalars only.
requirements-completed: [BUILD-02, BUILD-06]
coverage:
  - id: D1
    description: Topology-complete declarative states build an internal edge with one guard and handler execution.
    requirement: BUILD-02
    verification:
      - kind: integration
        ref: tests/test_construction_parity.py#test_declarative_builder_internal_transition_executes_exactly_once
        status: pass
      - kind: unit
        ref: tests/test_builder.py#test_declarative_transition_internal_is_exact_and_metadata_is_immutable
        status: pass
    human_judgment: false
  - id: D2
    description: Invalid declarative final and non-self internal rows preserve builder staging and cache while canonical validation rejects them.
    requirement: BUILD-06
    verification:
      - kind: integration
        ref: tests/test_construction_parity.py#test_declarative_builder_failure_keeps_staging_and_cache_unchanged
        status: pass
    human_judgment: false
  - id: D3
    description: Declarative metadata, typed public contract, one publication seam, and dispatch exclusions remain structurally enforced.
    requirement: BUILD-06
    verification:
      - kind: unit
        ref: tests/test_graph_invariants.py#test_declarative_builder_derives_into_one_canonical_transaction
        status: pass
      - kind: unit
        ref: tests/test_mypyc_guard.py#test_declarative_transition_mode_contract_keeps_raw_runtime_input
        status: pass
    human_judgment: false
  - id: D4
    description: Declarative rejection remains terminal for both builder-imported internal rows and compatible legacy manual internal rows.
    requirement: BUILD-06
    verification:
      - kind: integration
        ref: tests/test_construction_parity.py#test_declarative_builder_rejection_is_terminal_for_internal_candidate
        status: pass
      - kind: unit
        ref: tests/test_expected_rejection.py#test_reject_03_approved_boundaries_abort_priority_groups
        status: pass
    human_judgment: false
duration: 9 min
completed: 2026-09-17
status: complete
---

# Phase 30 Plan 01: Declarative Builder Tracer Summary

**FSMBuilder now converts a complete `@transition` declaration into one canonical internal edge while preserving state-owned guard and handler execution.**

## Performance

- **Duration:** 9 min
- **Started:** 2026-09-17T19:08:45Z
- **Completed:** 2026-09-17T19:18:01Z
- **Tasks:** 2/2
- **Files modified:** 7

## Accomplishments

- Added keyword-only exact-boolean `internal` mode to frozen/slotted declaration metadata, bound handler records, and the PEP 561 stub.
- Made `FSMBuilder.build()` derive each applicable destination-bearing declaration into a fresh unguarded `_TransitionRequest` and submit it with explicit rows through its existing single transaction.
- Added behavior, atomicity, carrier-layout, static-boundary, and hot-path structural evidence for the new construction seam.
- Restored terminal `TransitionRejected` handling for a legacy manually registered internal edge and added the corresponding builder-imported rejection regression.

## Task Commits

1. **Task 1: Trace one internal declarative transition from decorator through builder to dispatch** — `0bf89c9` (RED test), `d07b910` (implementation)
2. **Task 2: Lock declaration layout, canonical publication, and hot-path absence** — `5c673e1` (structural proof)
3. **Auto-fix: Narrow declarative source metadata for static checking** — `e5b6ed1`
4. **Regression fix: Preserve declarative rejection compatibility** — `cdfc485`

## Files Created/Modified

- `src/fast_fsm/core.py` — immutable declaration mode, build-time request derivation, and mode-aware resolution.
- `src/fast_fsm/core.pyi` — public decorator mode contract.
- `tests/test_construction_parity.py` — first reusable Phase 30 observable-semantics tracer and atomic-failure oracle.
- `tests/test_builder.py` — exact decorator input, immutable source, and direct-handler compatibility checks.
- `tests/test_graph_invariants.py` — canonical-publication and hot-path absence assertions.
- `tests/test_mypyc_guard.py` — frozen/slotted carrier and runtime/stub contract checks.
- `.specify/memory/spr-core-api.md` — living construction-contract update.

## Decisions Made

- Derive declaration rows only while constructing the private candidate. This leaves staged builder data untouched after a failed attempt and preserves cached success semantics.
- Keep decorator guards on the handler record rather than copying them to `TransitionEntry`; selected machine dispatch evaluates the policy exactly once.
- Preserve the old external-declaration-to-manual-internal compatibility direction while refusing the unsafe reverse internal-declaration-to-external binding.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Static type defect] Corrected declarative candidate identity and source narrowing**
- **Found during:** Task 2 verification
- **Issue:** Adding mode to declaration identity left the private tuple annotation stale; the new immutable source normalization also needed an explicit static narrowing for `ty`.
- **Fix:** Added the trailing boolean to the identity tuple type and used explicit casts only after the runtime list-copy branch.
- **Files modified:** `src/fast_fsm/core.py`
- **Verification:** Focused tests, Ruff, and `task typecheck-mypy` pass; the new `ty` assignment diagnostic is gone.
- **Committed in:** `e5b6ed1`

**2. [Rule 1 - Compatibility regression] Restored terminal declarative rejection on legacy manual internal rows**
- **Found during:** Post-wave full-suite verification
- **Issue:** New exact mode matching skipped a default declarative guard attached to a manually registered internal edge, allowing priority fallthrough and a committed result.
- **Fix:** Added a narrow one-way legacy fallback for one external-mode declaration to guard an internal manual edge; internal declarations still cannot bind external manual edges.
- **Files modified:** `src/fast_fsm/core.py`, `tests/test_construction_parity.py`
- **Verification:** Focused Phase 29 rejection suite, Plan 30 focused suites, mypy, and the full sequential suite pass.
- **Committed in:** `cdfc485`

**Total deviations:** 2 auto-fixed (2 Rule 1 correctness defects).
**Impact on plan:** Both changes preserve the locked canonical transaction and exactly-once guard ownership; no alternate registrar or dispatch-time import work was added.

## Issues Encountered

The post-wave full suite exposed a mode-aware declarative rejection regression; it is fixed in `cdfc485` and the full sequential suite now passes. The visible advisory `task typecheck-ty` result still reports its pre-existing unresolved relative import `.conditions`; after the earlier type-boundary fix it reports no Task 01-specific diagnostic. Mypy remains the blocking authority and passes.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Plan 02 can extend source/target applicability, collision, async, repair, and broader adapter-parity coverage from the established builder derivation seam.

## Self-Check: PASSED

- Required tracer and structural test files exist.
- Task commits `0bf89c9`, `d07b910`, `5c673e1`, `e5b6ed1`, and `cdfc485` exist in git history.
- Focused Phase 29/30 verification, mypy, and the full sequential suite pass; `ty` retains only the documented non-blocking import advisory.

---
*Phase: 30-builder-first-construction-persistence-parity*
*Completed: 2026-09-17*
