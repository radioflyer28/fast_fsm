---
phase: 18-safe-ownership-concurrency
plan: 04
subsystem: writer-ownership
tags: [concurrency, topology, history, listeners, callbacks, mypyc]
requires:
  - phase: 18-03
    provides: per-machine sync/async ownership admission and causal async reentry protection
provides:
  - Atomic ownership envelopes for all topology and history writes
  - Ownership-safe sync and async callback/listener/failure-observer registration
  - Full D-14 public-writer structural inventory and independent construction metadata
affects: [18-05, safe-trigger, declarative-guards, phase18-verification]
tech-stack:
  added: []
  patterns: [public-entry-private-owned-body, one-entry-ast-guard, fresh-origin-verification]
key-files:
  created: []
  modified:
    - src/fast_fsm/core.py
    - tests/test_ownership_concurrency.py
    - tests/test_mypyc_guard.py
    - tests/test_listeners.py
    - tests/test_builder.py
    - tests/test_transition_lifecycle.py
    - .specify/memory/spr-core-api.md
decisions:
  - "All public topology, history, and registrar writes enter ownership once and delegate only to private already-owned bodies."
  - "Callback-time registration fails before mutation; registrations after completion remain ordered for the next defensive snapshot pass."
  - "Factories, builders, and clones initialize distinct ownership primitives and cleared async ownership metadata."
requirements-completed: [OWN-01, OWN-02, OWN-03, OWN-04, OWN-05, OWN-06, OWN-07]
coverage:
  - deliverable: Atomic topology and history ownership
    verification:
      - kind: command
        ref: fresh pure and compiled ownership/graph/history selections
        status: pass
    human_judgment: false
  - deliverable: Ownership-safe registrar and observer behavior
    verification:
      - kind: command
        ref: fresh pure and compiled listener/observer/lifecycle selections
        status: pass
    human_judgment: false
  - deliverable: Independent builder, factory, and clone ownership metadata
    verification:
      - kind: command
        ref: tests/test_builder.py#TestOwnershipConstructionIndependence
        status: pass
    human_judgment: false
  - deliverable: Complete structural public-writer admission guard
    verification:
      - kind: command
        ref: tests/test_mypyc_guard.py#test_d14_writers_enter_and_release_once_without_public_delegation
        status: pass
    human_judgment: false
metrics:
  duration: 13m
  completed: 2026-09-02
  tasks: 2
  files: 7
actuals:
  tokens: 6671
  tasks: 2
  commits: 4
status: complete
---

# Phase 18 Plan 04: Complete Public Writer Ownership Summary

**Every remaining topology, history, listener, callback, and failure-observer write now uses a single per-machine ownership envelope without weakening construction or snapshot contracts.**

## Accomplishments

- Wrapped `add_state`, every transition graph writer, and history enable/disable around validation through commit, using private already-owned bodies to retain atomic batch and bidirectional behavior.
- Wrapped all six synchronous registrars plus the two async registrars; callback-time writes now fail before registry mutation while post-operation registration remains order-preserving for the next defensive tuple snapshot.
- Added deterministic callback-reentry, topology/history atomicity, observer-order, construction/clone independence, and complete D-14 AST enforcement coverage.
- Updated the maintained API contract to distinguish owned machine writes from unowned builder staging and read-only access.

## Task Commits

1. **Task 1: Own every topology and history mutation as one atomic public operation** — `1a91706` (RED), `c0439ab` (GREEN)
2. **Task 2: Own all registrars and prove builder, factory, and clone independence** — `2d5ef79` (RED), `afea489` (GREEN)

## Verification

- Fresh pure-source topology/history, graph invariant, advanced functionality, and structural ownership selections passed; mypy passed.
- Fresh pure-source listener, observer, builder, clone, lifecycle, and slots-policy checks passed; mypy passed.
- Freshly compiled temporary-artifact selection passed for ownership, topology/history, graph, listener, observer, builder, clone, lifecycle, and AST checks.
- Ruff formatting and lint checks passed for all touched Python files.

## Decisions Made

- Every D-14 public write has exactly one auditable entry/release pair and never delegates to another acquiring public write.
- Async registrar calls use the existing bound-loop mixed-writer admission seam; an async-owned callback cannot mutate either async registrar.
- Builder staging remains outside machine ownership, while publication and cloning produce independent primitives and empty live ownership state.

## Deviations from Plan

None — the Phase 17 observer regression was updated as the Task 2 action explicitly requires, preserving its snapshot guarantee only for registrations made after the prior operation finishes.

## Known Stubs

None.

## Self-Check: PASSED

All seven required source/test/contract files and the summary exist. Task commits `1a91706`, `c0439ab`, `2d5ef79`, and `afea489` exist in git history.

## Next Phase Readiness

Plan 18-05 can now address the remaining `safe_trigger()` and declarative-marker compatibility seams without a public-writer ownership bypass.
