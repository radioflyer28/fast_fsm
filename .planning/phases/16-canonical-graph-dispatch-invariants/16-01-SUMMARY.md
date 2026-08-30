---
phase: 16-canonical-graph-dispatch-invariants
plan: 01
subsystem: core-runtime
tags: [fsm, topology, mypyc, slots, isolation, pytest]
requires:
  - phase: 15-release-baseline-evidence-harness
    provides: clean pure-source evidence conventions and slots-policy authority
provides:
  - canonical identity-based state registration and atomic topology commits
  - private immutable, versioned graph snapshots for later diagnostic tools
  - asserted pure/compiled temporary-tree verification helper
affects: [16-02, 16-03, 16-04, 16-05, 17-atomic-transition-lifecycle, 19-bounded-diagnostics]
actuals:
  tokens: 12300
  tasks: 3
  commits: 6
tech-stack:
  added: []
  patterns: [canonical endpoint resolution, validate-then-commit topology plans, tuple-backed private snapshots, asserted module-origin verification]
key-files:
  created:
    - tests/test_graph_invariants.py
    - tools/phase16_isolated_verify.py
    - .planning/phases/16-canonical-graph-dispatch-invariants/16-PERFORMANCE-EVIDENCE.md
  modified:
    - src/fast_fsm/core.py
    - tests/test_mypyc_guard.py
    - tests/test_boundary_negative.py
    - .specify/memory/spr-core-api.md
key-decisions:
  - "Keep graph snapshots private, fresh, frozen tuple-backed records that retain canonical State and Condition identities."
  - "Validate all endpoint/guard requests before any dictionary write and advance graph version once per changing public operation."
  - "Use clean committed-HEAD exports plus explicit working-tree overlays to prove pure and compiled module origin."
patterns-established:
  - "Topology mutation: normalize complete request -> compare final entries -> one commit section -> one version advance."
  - "Artifact proof: select build mode before locked setup, assert module origin before semantic work, and never trust developer native shadows."
requirements-completed: [GRAF-01, GRAF-02, GRAF-03, GRAF-08]
coverage:
  - id: D1
    description: Canonical identity registration and atomic endpoint mutation across single, batch, bidirectional, and emergency helpers.
    requirement: GRAF-01
    verification:
      - kind: unit
        ref: tests/test_graph_invariants.py#test_endpoints_must_be_exact_registered_objects_without_mutation
        status: pass
      - kind: unit
        ref: tests/test_graph_invariants.py#test_multi_source_and_batch_validation_are_atomic
        status: pass
    human_judgment: false
  - id: D2
    description: Fresh private graph snapshots preserve declared-initial identity, deterministic rows, structural immutability, and per-machine version lineage.
    requirement: GRAF-03
    verification:
      - kind: unit
        ref: tests/test_graph_invariants.py#test_graph_snapshot_is_fresh_sorted_immutable_and_canonical
        status: pass
      - kind: integration
        ref: tools/phase16_isolated_verify.py --suite graph
        status: pass
    human_judgment: false
  - id: D3
    description: The canonical graph seam remains slot-safe and inside the sole mypyc compilation unit in asserted pure and compiled contexts.
    requirement: GRAF-08
    verification:
      - kind: unit
        ref: tests/test_mypyc_guard.py
        status: pass
      - kind: integration
        ref: tools/phase16_isolated_verify.py --suite graph
        status: pass
    human_judgment: false
duration: 4h 13m
completed: 2026-08-30
status: complete
---

# Phase 16 Plan 01: Canonical Graph Snapshot Tracer Summary

**Canonical identity-safe topology mutation with immutable versioned graph snapshots, plus clean pure/compiled verification that never relies on local native shadows.**

## Performance

- **Duration:** 4h 13m
- **Started:** 2026-08-30T00:22:12-04:00
- **Completed:** 2026-08-30T04:35:37Z
- **Tasks:** 3/3
- **Files modified:** 7
- **Before-change observations:** pure `trigger()` 851,576 ops/s; compiled `trigger()` 1,054,438 ops/s (local CPython 3.12.10 arm64 observations, not new policy thresholds).

## Accomplishments

- Added exact-identity state registration, graph versioning, and fresh frozen `_GraphSnapshot` / `_GraphTransition` projections without changing public `snapshot()` or `to_dict()` schemas.
- Replaced incremental topology mutation with strict endpoint normalization and one all-or-nothing commit path for ordinary, batch, bidirectional, and emergency transitions.
- Added a clean-tree runner that overlays only named task files, asserts `.py` or native module origin before semantic work, and verifies graph contracts in both modes.

## Task Commits

1. **Task 1: Wave 0 tracer — canonical registration to immutable snapshot**
   - `c908f3f` — RED graph contract tests
   - `01bf633` — canonical snapshot implementation, isolated runner, SPR, and evidence
2. **Task 2: Expand endpoint normalization and multi-source atomic rejection**
   - `4b0ee34` — RED atomicity tests
   - `9626205` — canonical endpoint resolution and atomic helpers
   - `50170d1` — Ruff formatting for the graph contract module
3. **Task 3: Lock the compiled record and single-unit topology boundary**
   - `cee742b` — structural mypyc guards, runner hardening, and compiled semantic proof

## Files Created/Modified

- `src/fast_fsm/core.py` — private graph records, versioning, exact resolver, prepared transaction commit path.
- `tests/test_graph_invariants.py` — real-object snapshot, identity, version, and atomic-rejection contracts.
- `tests/test_mypyc_guard.py` — AST guards for private record slots, exports, and mypyc input boundary.
- `tests/test_boundary_negative.py` — D-01-compatible duplicate state regression expectation.
- `tools/phase16_isolated_verify.py` — fail-closed clean-tree pure/compiled suite runner.
- `.specify/memory/spr-core-api.md` — canonical topology and graph snapshot behavior.
- `16-PERFORMANCE-EVIDENCE.md` — labelled before-change pure/compiled observations.

## Decisions Made

- Graph snapshots remain a private structural contract: tuple collections and frozen records prevent replacement while canonical referenced State/Condition objects remain identity-bearing.
- Exact endpoint resolution occurs before all dictionary writes; final topology comparison suppresses no-op version advances.
- The isolation runner requires repository-relative overlays and an asserted module origin before any behavior or performance command.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Isolation runner] Normalized temporary-root comparison before archive extraction.**

- **Found during:** Task 1
- **Issue:** macOS `/var` versus `/private/var` canonical paths made a safe `git archive` entry appear to escape its temporary destination.
- **Fix:** Compared resolved destination paths before extraction.
- **Files modified:** `tools/phase16_isolated_verify.py`
- **Verification:** pure and compiled task contexts both asserted their expected module origins.
- **Committed in:** `01bf633`

**2. [Rule 1 - Regression expectation] Updated the old same-name state overwrite test to D-01.**

- **Found during:** Task 2
- **Issue:** the historical test asserted silent replacement of a canonical state, contradicting the locked Phase 16 requirement.
- **Fix:** Asserted `ValueError`, canonical identity preservation, and unchanged graph snapshot instead.
- **Files modified:** `tests/test_boundary_negative.py`
- **Verification:** focused pure regression command passed 130 tests.
- **Committed in:** `9626205`

**3. [Rule 1 - Compiled boundary] Preserved invalid-list endpoint rejection under mypyc.**

- **Found during:** Task 3
- **Issue:** mypyc enforced the inner list's union annotation before the canonical resolver could produce its deterministic rejection.
- **Fix:** Kept public signatures intact while passing internal source-list elements as `Any` to the resolver; contract tests assert failure-before-mutation for invalid values in both modes.
- **Files modified:** `src/fast_fsm/core.py`, `tests/test_graph_invariants.py`
- **Verification:** `tools/phase16_isolated_verify.py --suite graph` passed under asserted pure and native origins.
- **Committed in:** `cee742b`

---

**Total deviations:** 3 auto-fixed Rule 1 issues.
**Impact on plan:** All fixes were required for the planned fail-closed isolation and canonical-mutation contracts; no public topology format, dependency, lock, or compilation boundary was added.

## Issues Encountered

- The sandbox could not read the existing shared `uv` cache for mypy. The same read-only `task typecheck-mypy` command passed when run with approved cache access.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Plans 16-02 through 16-05 can rely on `_resolve_canonical_state`, `_normalize_transition_request`, `_commit_transition_plan`, `_graph_snapshot`, and the clean-tree runner. The public runtime snapshot remains unchanged; tool migration is still deliberately deferred to Phase 19.

## Self-Check: PASSED

- All seven implementation, test, evidence, SPR, and summary artifacts exist.
- All six task commits are present in repository history.
- The changed files contain no plan-blocking stubs; scanner matches are ordinary
  runtime defaults or diagnostic formatting, not placeholder behavior.

---
*Phase: 16-canonical-graph-dispatch-invariants*
*Plan: 01*
*Completed: 2026-08-30*
