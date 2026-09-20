---
phase: 32-performance-artifact-progressive-guidance-proof
plan: 06
subsystem: documentation
tags: [sphinx, tutorial, examples, api, FSMBuilder, finality, transition-modes, expected-rejection]
requires:
  - phase: 32-04
    provides: "Deterministic controller-owned drone tutorial with finality, modes, and rejection"
  - phase: 32-05
    provides: "Builder-first public entry guides and migration wording"
provides:
  - "Executable progressive Sphinx learning path from FSMBuilder through flat-FSM semantics"
  - "Accurate deterministic drone gallery with independent smoke-test provenance"
  - "API-level doctest contrasts for finality, self-transition mode, and selection outcomes"
affects: [documentation, examples, release-proof, UAT]
actuals:
  tokens: 8211
  tasks: 2
  commits: 2
tech-stack:
  added: []
  patterns:
    - "Use MyST testcode/testoutput pairs for field-level public semantic claims."
    - "Treat literalinclude as source display; retain an independent runnable smoke test as execution proof."
key-files:
  created: []
  modified:
    - docs/TUTORIAL.md
    - docs/examples/index.md
    - docs/api/core.md
key-decisions:
  - "Replace the broad level-based tutorial with a builder-first semantic sequence that defers advanced construction to its distinct supported roles."
  - "Use TransitionResult fields and lifecycle callback observations, not diagrams or equal endpoint names, to teach finality, mode, and outcome semantics."
  - "Keep the drone training-only disclaimer adjacent to its gallery entry and identify the independent smoke test explicitly."
requirements-completed: [DOC-01, DOC-02, DOC-03, DOC-04]
coverage:
  - id: D1
    description: "Sphinx tutorial and gallery teach the builder-first, controller-owned drone path with priority, both self modes, final landings, expected rejection, and post-commit commands."
    requirements: [DOC-01, DOC-02, DOC-03]
    verification:
      - kind: docs
        ref: task docs-check
        status: pass
      - kind: unit
        ref: tests/test_readme_examples.py tests/test_drone_failsafes_example.py
        status: pass
      - kind: smoke
        ref: uv run python examples/drone_failsafes.py
        status: pass
    human_judgment: false
  - id: D2
    description: "API documentation executes exact result-field contrasts for finality, self-transition modes, false guards, expected rejection, and unexpected failure."
    requirements: [DOC-04]
    verification:
      - kind: doctest
        ref: task docs-test
        status: pass
      - kind: unit
        ref: tests/test_final_states.py tests/test_transition_modes.py tests/test_expected_rejection.py
        status: pass
    human_judgment: false
duration: 18min
completed: 2026-09-19
status: complete
---

# Phase 32 Plan 06: Progressive Sphinx Guidance Summary

**Sphinx now presents one executable builder-first flat-FSM learning path, from a small machine to precise finality, self-transition, and rejection contracts.**

## Accomplishments

- Replaced the former broad tutorial-level tour with a focused progression: builder construction, guards and priority, same-state mode, explicit finality, selection outcomes, diagnostics, the drone integration, advanced paths, migration, and artifact proof.
- Expanded the gallery's drone entry around the real script behavior: one controller-owned telemetry event, FSM-owned precedence, fact-only telemetry policy, both self modes, explicit final landing, command-free rejection, and post-commit adapter commands.
- Added executable API examples that contrast a non-final sink with explicit finality, internal update with external re-entry lifecycle, and false guard with expected rejection and unexpected failure.
- Kept all four deprecated-convenience migrations and the v0.5.x / no-earlier-than-v0.6.0 timing exact without deprecating direct constructors, `from_dict()`, or declarative APIs.

## Task Commits

1. **Task 1: Teach the progressive workflow and point the gallery to its runnable drone story** — `d162a9f` (`docs`)
2. **Task 2: Make API semantic distinctions executable in Sphinx** — `379e267` (`docs`)

## Verification

- `task docs-check` — passed (warnings-as-errors HTML build).
- `task docs-test` — passed (13 Sphinx doctests, including 6 tutorial and 4 core API examples).
- `uv run pytest tests/test_readme_examples.py tests/test_drone_failsafes_example.py -x -q` — passed (47 tests).
- `uv run pytest tests/test_final_states.py tests/test_transition_modes.py tests/test_expected_rejection.py -x -q` — passed (117 tests).
- `uv run python examples/drone_failsafes.py` — passed; printed internal update, external re-entry, terminal expected rejection, and distinct normal/emergency final landings.

## Decisions Made

- Each tutorial concept is executable before the next concept is introduced; direct, async, serialization, and declarative paths appear later as supported specialized roles.
- API examples prove behavior with `success`, `committed`, `rejected`, `rejection_code`, `cause`, `stage`, `internal`, and `is_terminated` rather than relying on implied topology.
- The gallery calls out that `literalinclude` displays source only; the dedicated pytest smoke test and direct script invocation demonstrate execution.

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None.

## Self-Check: PASSED

- All three planned documentation files exist and both task commits are reachable in Git history.
- No task commit deleted tracked files.
- `git diff --check` passed for the completed documentation changes.
- The changed files contain no TODO, FIXME, placeholder, or similar stub markers.

---
*Phase: 32-performance-artifact-progressive-guidance-proof*
*Completed: 2026-09-19*
