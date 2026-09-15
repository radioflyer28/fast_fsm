---
phase: 26-canonical-construction-evidence-contract
plan: 03
subsystem: construction
tags: [atomicity, builder, clone, adapters, topology]
requires:
  - phase: 26-01
    provides: immutable transition request carrier and canonical machine-owned transaction
provides:
  - Canonical request delegation for retained transition-producing adapters
  - Independent request-based sync and async clone topology reconstruction
  - Immutable named FSMBuilder request staging and endpoint-bound publication
  - Full failed-build retryability and cache-preservation coverage
affects: [27-final-states, 28-transition-modes, 29-domain-rejection, 30-builder-persistence]
actuals:
  tokens: 16800
  tasks: 2
  commits: 6
tech-stack:
  added: []
  patterns:
    - immutable adapter request collections published once per complete operation
    - private candidate construction before builder or factory publication
    - clone topology reconstruction with shallow collaborator identity and independent containers
key-files:
  created: []
  modified:
    - src/fast_fsm/core.py
    - tests/test_graph_invariants.py
    - tests/test_builder.py
    - tests/test_async.py
    - tests/test_mypyc_guard.py
    - tests/test_ownership_concurrency.py
key-decisions:
  - "Retained tuple and dictionary adapters parse their own input language, then submit one immutable request collection to the canonical transaction."
  - "Clones preserve canonical State, Condition, callback, and listener identity while rebuilding transition entries, groups, and tables independently."
  - "FSMBuilder remains mutable and single-owner before publication, but each staged transition is an immutable named request whose source collection is copied at the boundary."
patterns-established:
  - "Adapter atomicity: parse complete input, freeze requests, then publish once through _apply_transition_requests_owned."
  - "Builder retryability: bind immutable staging into a private candidate and publish machine type/cache only after topology and callback wiring succeed."
requirements-completed: [BUILD-04, BUILD-05]
coverage:
  - id: D1
    description: Every retained transition-producing adapter delegates through the canonical immutable request transaction.
    requirement: BUILD-04
    verification:
      - kind: unit
        ref: tests/test_graph_invariants.py#test_retained_transition_adapters_use_the_canonical_request_transaction
        status: pass
      - kind: integration
        ref: tests/test_builder.py#test_builder_build_submits_one_endpoint_bound_request_transaction
        status: pass
      - kind: regression
        ref: tests/test_mypyc_guard.py#test_phase23_construction_projection_and_callback_probe_is_mode_invariant
        status: pass
    human_judgment: false
  - id: D2
    description: Failed factory, clone, registration, and builder attempts expose no partial topology and remain repairable.
    requirement: BUILD-05
    verification:
      - kind: unit
        ref: tests/test_graph_invariants.py#test_clone_reconstruction_failure_preserves_source_and_retryability
        status: pass
      - kind: unit
        ref: tests/test_builder.py#test_builder_stages_immutable_named_transition_requests
        status: pass
      - kind: integration
        ref: tests/test_ownership_concurrency.py#test_clone_capture_waits_for_a_topology_owner_and_copies_mutable_tables
        status: pass
    human_judgment: false
duration: 16min
completed: 2026-09-15
status: complete
---

# Phase 26 Plan 03: Canonical Adapter and Builder Construction Summary

**Every retained transition-producing adapter, clone, and builder now reaches one immutable request transaction without exposing partial topology.**

## Performance

- **Duration:** 16 min
- **Started:** 2026-09-15T18:16:00Z
- **Completed:** 2026-09-15T18:32:00Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- Routed quick construction, dictionary reconstruction, bidirectional helpers, and emergency helpers through complete `_TransitionRequest` collections and one `_apply_transition_requests_owned()` call.
- Rebuilt sync and async clone topology through the canonical transaction, preserving State/Condition collaborators while making transition tables, slots, and entries independent.
- Replaced positional builder tuples with frozen, slotted request values; build attempts bind canonical endpoints into fresh requests without mutating staging.
- Preserved immediate builder validation, async classification, failed-build retryability, and successful machine caching.

## Task Commits

1. **RED: Define canonical adapter and clone contracts** — `999e001` (test)
2. **GREEN: Canonicalize retained adapter topology** — `89c67fb` (feat)
3. **RED: Define immutable builder request staging** — `dd54a65` (test)
4. **GREEN: Stage immutable builder requests** — `5591e5f` (feat)
5. **Artifact contract alignment** — `9d86daa` (test)
6. **Concurrent clone contract alignment** — `6ae4218` (test)

**Plan metadata:** this summary commit

## Files Created/Modified

- `src/fast_fsm/core.py` — Request parsing, adapter publication, clone reconstruction, and builder staging/publication.
- `tests/test_graph_invariants.py` — Adapter seam, clone identity, failure, and retryability contracts.
- `tests/test_builder.py` — Immutable request staging and endpoint-bound build contracts.
- `tests/test_async.py` — Async clone independent-container parity.
- `tests/test_mypyc_guard.py` — Pure/compiled construction projection parity under independent clone topology.
- `tests/test_ownership_concurrency.py` — Owned clone capture with independent reconstructed entries.

## Decisions Made

- Adapter-specific input validation remains outside the semantic transaction, while topology normalization and publication remain exclusively machine-owned.
- Builder staging is deliberately immutable per transition but the builder itself remains a single-owner mutable construction workspace; no locking contract was added.

## Deviations from Plan

- Two existing cross-cutting clone tests outside the plan's initial file list asserted shared immutable slot identity. They were updated when the full suite proved that assumption conflicted with BUILD-05's explicit independent-entry requirement.

## Issues Encountered

- The first dictionary carrier conversion used `tuple(sources)`, which split a singleton string into characters. The adapter was corrected to use the shared source-freezing helper before the GREEN commit.
- Full-suite runs found two stale clone identity assertions; both now assert independent topology with preserved target identity.

## User Setup Required

None.

## Next Phase Readiness

- Plan 26-04 is the required blocking human checkpoint for exact external competitor package provenance.
- After approval, plan 26-05 can generate adjacent locks and wire the manual isolated comparison workflow.

## Self-Check: PASSED

- Full repository suite passes.
- Ruff, mypy, and ty pass for changed production/test files.
- Slots-policy inventory confirms `_TransitionRequest` and all touched hot-path classes remain slot-protected.

---
*Phase: 26-canonical-construction-evidence-contract*
*Completed: 2026-09-15*
