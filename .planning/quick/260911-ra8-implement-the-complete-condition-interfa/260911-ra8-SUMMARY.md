---
phase: 260911-ra8
plan: 01
subsystem: core-api
tags: [conditions, transition-timing, deprecation, mypyc, sphinx]
requires: []
provides:
  - "Canonical condition composition with `&`, `|`, and `~`"
  - "Immutable entry-relative `after`/`within` transition timing"
  - "Deprecated compatibility shims and deterministic domain-condition recipes"
affects: [conditions, transition-selection, async-dispatch, serialization, documentation]
actuals:
  tokens: 23801.25
  tasks: 3
  commits: 8
tech-stack:
  added: []
  patterns:
    - "Interpreted public condition algebra with a compiled-core invocation bridge"
    - "One injected monotonic clock sample for each timed local selection"
    - "Entry-relative immutable timing metadata rather than mutable timer guards"
key-files:
  created:
    - .specify/decisions/ADR-008-condition-composition-and-transition-timing.md
    - examples/custom_conditions.py
    - tests/test_condition_interface.py
    - tests/test_transition_timing.py
  modified:
    - src/fast_fsm/conditions.py
    - src/fast_fsm/condition_templates.py
    - src/fast_fsm/core.py
    - README.md
    - docs/api/conditions.md
key-decisions:
  - "Use canonical NotCondition for every new negation while retaining deprecated NegatedCondition construction."
  - "Model timing as immutable transition-entry metadata with an injectable monotonic clock."
  - "Keep legacy templates importable with targeted warnings until no earlier than the next major release."
patterns-established:
  - "Use small named domain conditions instead of extending a generic validation-template DSL."
  - "Apply timing before guards and sample the clock once per direct entry or priority group."
requirements-completed: [QUICK-260911-RA8]
coverage:
  - id: D1
    description: "Focused condition algebra, compatibility deprecations, and entry-relative timing across sync and async paths."
    requirement: QUICK-260911-RA8
    verification:
      - kind: unit
        ref: "tests/test_condition_interface.py and tests/test_transition_timing.py"
        status: pass
      - kind: integration
        ref: "task test (pure source suite)"
        status: pass
      - kind: other
        ref: "task build-check (compiled extension smoke)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Progressive documentation and deterministic condition examples."
    requirement: QUICK-260911-RA8
    verification:
      - kind: integration
        ref: "tests/test_examples_smoke.py and tests/test_readme_examples.py"
        status: pass
      - kind: other
        ref: "task docs-check and task docs-test"
        status: pass
    human_judgment: false
duration: 32min
completed: 2026-09-12
status: complete
---

# Phase 260911-ra8 Plan 01: Complete Condition Interface Summary

**A focused six-type condition algebra, transition-owned deterministic timing, and a deprecated compatibility path backed by executable domain recipes.**

## Performance

- **Duration:** 32 min
- **Started:** 2026-09-11T23:50:01Z
- **Completed:** 2026-09-12T00:22:24Z
- **Tasks:** 3/3 complete
- **Files modified:** 15

## Accomplishments

- Established canonical `AndCondition`, `OrCondition`, and `NotCondition` composition through `&`, `|`, and `~`, with `unless=` normalized to the same canonical negation.
- Added immutable `[after, within)` entry-relative eligibility to direct, priority, sync, async, builder, declarative, helper, clone, factory, and serialization paths using one validated injected-clock sample.
- Preserved public legacy condition symbols as deprecating shims, recorded the contract in ADR-008 and SPR memory, and replaced template-first documentation with deterministic focused and custom-condition examples.

## Task Commits

1. **Task 1: Establish the focused condition algebra and one timed dispatch path**
   - `36bbf4d` `test(260911-ra8-01): add focused condition interface contract`
   - `3a31c54` `feat(260911-ra8-01): establish condition algebra and timed dispatch`
2. **Task 2: Complete deterministic transition timing across every construction and runtime path**
   - `9031780` `test(260911-ra8-01): add deterministic transition timing contract`
   - `c9f239c` `feat(260911-ra8-01): complete transition timing model`
3. **Task 3: Replace the mixed-template story with progressive documentation and runnable domain recipes**
   - `c88447f` `docs(260911-ra8-01): guide focused condition design`
   - `d306420` `docs(260911-ra8-01): add condition migration table`
   - `f930696` `docs(260911-ra8-01): clarify condition timing guidance`
4. **Hosted CI correction: Preserve strict typed compatibility imports**
   - `34ff064` `fix: explicitly re-export condition combinators`

## Files Created/Modified

- `src/fast_fsm/conditions.py` — canonical boolean wrappers and deprecated public compatibility constructors.
- `src/fast_fsm/condition_templates.py` — re-exported composition wrappers and targeted migration warnings for legacy leaves/timers.
- `src/fast_fsm/core.py` — validated clock/timing metadata, selection, commit timestamping, and all construction/serialization routes.
- `tests/test_condition_interface.py` and `tests/test_transition_timing.py` — focused fake-clock and compatibility contracts.
- `.specify/decisions/ADR-008-condition-composition-and-transition-timing.md`, `.specify/memory/spr-core-api.md`, and `docs/dev/architecture.md` — durable design rationale and architecture constraints.
- `README.md`, `docs/api/conditions.md`, and `docs/examples/index.md` — progressive current interface and migration guidance.
- `examples/condition_toolkit.py` and `examples/custom_conditions.py` — deterministic runnable composition/timing and domain-condition recipes.

## Decisions Made

- `NotCondition` is the one canonical stored negation. `NegatedCondition` remains constructible and preserves its `_inner` compatibility seam, but is no longer used by `unless=`.
- Timing belongs to immutable transition entries, measured from a committed source-state entry with `[after, within)` semantics; it is not a stateful condition or cooldown abstraction.
- A timed candidate group takes one pre-guard clock snapshot. Timing rejection falls through only to the next local priority candidate; clock/guard failures retain redacted existing failure behavior.
- Application payload interpretation stays in small application-owned conditions; Fast FSM keeps only the guard algebra and lifecycle policy.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Preserve the slots policy while canonicalizing `unless=` negation**
- **Found during:** Task 2 quality gates.
- **Issue:** A compatibility metaclass used to make canonical `NotCondition` instances satisfy an old `NegatedCondition` instance assertion introduced an unregistered instance dictionary and failed the mandatory slot audit.
- **Fix:** Kept the deprecated `NegatedCondition` constructor and `_inner` behavior, removed the metaclass, and updated the legacy assertion to require canonical `NotCondition` for `unless=`.
- **Files modified:** `src/fast_fsm/conditions.py`, `tests/test_condition_templates.py`
- **Verification:** `uv run python tools/release_evidence.py slots-policy --json`; focused and full tests.
- **Committed in:** `c9f239c`

**2. [Rule 1 - Bug] Retain legacy FSMBuilder staged-row compatibility**
- **Found during:** Task 2 builder regression tests.
- **Issue:** Existing in-memory builder rows with the previous five-field shape were unpacked as though all staged rows carried new timing metadata.
- **Fix:** Accepted the legacy prefix and supplied absent `after`/`within` values only when the new sixth and seventh fields are present.
- **Files modified:** `src/fast_fsm/core.py`
- **Verification:** `tests/test_builder.py`, `tests/test_transition_timing.py`, and the full suite.
- **Committed in:** `c9f239c`

**3. [Rule 2 - Missing critical functionality] Complete the required migration and lifecycle teaching story**
- **Found during:** Final Task 3 plan-to-document audit.
- **Issue:** The initial documentation rewrite omitted the required per-symbol migration table and did not explicitly state query observation, destination entry-time, and async pre-await clock-capture guarantees. The toolkit also needed to name each canonical wrapper as well as demonstrate operators.
- **Fix:** Added the complete compact migration table, lifecycle semantics, and named `AndCondition`, `OrCondition`, and `NotCondition` usage to the runnable example.
- **Files modified:** `README.md`, `examples/condition_toolkit.py`
- **Verification:** `tests/test_readme_examples.py`, `tests/test_examples_smoke.py`, direct example run, and Ruff.
- **Committed in:** `d306420`, `f930696`

**Total deviations:** 3 auto-fixed issues (2 Rule 1 bugs, 1 Rule 2 documentation-completeness correction).

**Impact on plan:** Both fixes were necessary to preserve the specified deprecation and compatibility guarantees without widening the public surface.

## Verification

- `uv run pytest tests/test_condition_interface.py -q` — pass (14 tests).
- Targeted timing, condition, async, priority, builder, template, and utility regressions — pass.
- `task pure-source-check` — pass after temporarily relocating generated extension artifacts; source resolved to `src/fast_fsm/core.py`.
- `task test` — pass, full pure-source suite reached 100% with exit code 0.
- `task typecheck-mypy` — pass.
- `task typecheck-ty` — pass (advisory).
- `uv run python tools/release_evidence.py slots-policy --json` — pass.
- `task docs-check` and `task docs-test` — pass; HTML warning-as-error build and 4 doctests succeeded.
- `task build-check` — pass; rebuilt mypyc extension and completed compiled smoke test.
- Direct deterministic runs of `examples/condition_toolkit.py` and `examples/custom_conditions.py`, plus `tests/test_examples_smoke.py` — pass.
- Final README/example audit: `uv run pytest tests/test_readme_examples.py tests/test_examples_smoke.py -q` — pass (23 tests).

## Issues Encountered

- During execution, the Beads Dolt server could not accept connections because a two-day-old orphan process retained its configured database port. The orchestrator verified and terminated that process, restarted Dolt, and recorded the completed work as closed issue `fast_fsm-b1j`.
- The pure-source gate intentionally fails closed when native core artifacts shadow `core.py`. Generated artifacts were moved recoverably to `/private/tmp` for pure checks, then the current extension was rebuilt and the pre-existing CPython 3.10 artifacts were restored.
- The first exact-SHA hosted matrix found that the legacy `fast_fsm.condition_templates` combinator imports were implicit after canonicalization. Clean strict-mypy clients therefore rejected `AndCondition`, `OrCondition`, and `NotCondition` even though runtime imports worked. Commit `34ff064` changed them to explicit self-alias re-exports; the exact failing downstream test, Ruff, and blocking mypy gate then passed locally before the replacement push.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

The focused public condition vocabulary, deterministic timing model, migration guides, and runnable examples are ready for review. The planning documents remain intentionally uncommitted for the orchestrator to own.

## Self-Check: PASSED

- Confirmed created ADR, example, and focused test files exist.
- Confirmed all seven task commits exist in the repository history.

---
*Phase: 260911-ra8*
*Completed: 2026-09-12*
