---
phase: 16-canonical-graph-dispatch-invariants
reviewed: 2026-08-30T13:54:27Z
depth: standard
files_reviewed: 17
files_reviewed_list:
  - .specify/memory/spr-core-api.md
  - docs/dev/architecture.md
  - docs/dev/testing.md
  - evidence/release-baseline.json
  - src/fast_fsm/condition_templates.py
  - src/fast_fsm/conditions.py
  - src/fast_fsm/core.py
  - tests/test_advanced_functionality.py
  - tests/test_async.py
  - tests/test_boundary_negative.py
  - tests/test_builder.py
  - tests/test_condition_templates.py
  - tests/test_graph_invariants.py
  - tests/test_mypyc_guard.py
  - tests/test_performance_benchmarks.py
  - tests/test_safety_kwargs.py
  - tools/phase16_isolated_verify.py
findings:
  critical: 4
  warning: 3
  info: 0
  total: 7
status: issues_found
---

# Phase 16: Code Review Report

**Reviewed:** 2026-08-30T13:54:27Z
**Depth:** standard
**Files Reviewed:** 17
**Status:** issues_found

## Summary

Phase 16 does not yet satisfy its canonical guard-dispatch contract. The ordinary transition-entry path uses the new shared classifier, evaluator, and sanitizer, but declarative decorator guards still use an independent state-owned path. That split produces two shipping blockers: nested async declarative guards are detected during builder preflight but not awaited at runtime, and declarative guards receive raw private/unbounded keyword data. Builder validation is also non-atomic, and recursive wrapper traversal remains vulnerable to valid deep graphs. The verification harness and architecture documentation contain three additional coverage/robustness defects.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: Nested async declarative guards are detected but never recursively awaited

**Classification:** BLOCKER

**File:** `/Users/akriz/code/fast_fsm/src/fast_fsm/core.py:2573-2579`

**Issue:** Builder detection recursively identifies async leaves in declarative handler metadata (`_detect_async_requirements()` at lines 2736-2745), so auto mode correctly selects `AsyncStateMachine`. Runtime evaluation does not use that same classifier/evaluator: `AsyncDeclarativeState.can_transition_async()` awaits only a direct `AsyncCondition`, then invokes every wrapped `Condition` synchronously via `condition.check()`. A supported wrapper such as `NotCondition(AsyncCondition(...))` therefore reaches `AsyncCondition.check()` inside the running event loop, attempts `asyncio.run()`, is caught as a failed guard, and leaves the machine in its source state. A direct reproduction selected `AsyncStateMachine` but returned `False`, left the state at `source`, and never called the async leaf (with a `RuntimeWarning` for the un-awaited coroutine). This violates GRAF-05 and the documented promise that builder preflight and runtime share one recursive classifier/evaluator.

**Fix:** Move declarative guard evaluation behind the machine-owned `_evaluate_condition_async()` seam (and the corresponding sync seam) after resolving the canonical handler. Do not call wrapper `.check()` directly from `AsyncDeclarativeState`. Add pure and compiled tests using each supported wrapper around an async leaf on `@transition(condition=...)`, asserting both `can_trigger_async()` and `trigger_async()` await the leaf and agree.

### CR-02: Declarative decorator guards bypass keyword sanitization

**Classification:** BLOCKER

**File:** `/Users/akriz/code/fast_fsm/src/fast_fsm/core.py:2486-2512`

**Issue:** `_prepare_transition()` sanitizes kwargs only when the canonical `TransitionEntry` itself has a condition (lines 1290-1314). Decorator conditions instead run later in `DeclarativeState.can_transition()` and `AsyncDeclarativeState.can_transition_async()` with the original raw `*args, **kwargs`. A reproduction with a declarative guard observed `{'safe': 1, '_secret': 2}` verbatim. Private, non-string, overlong, and over-budget keys therefore reach user guard code on both sync and async declarative paths, contradicting D-12 through D-14, GRAF-06, GRAF-08, and the architecture page's claim that all can/do paths share one prepared context. This is also an avoidable sensitive-data exposure boundary.

**Fix:** Resolve the applicable declarative handler during `_prepare_transition()` (or extend the prepared dispatch object) and produce one sanitized fresh mapping whenever either the transition entry or its selected handler has a guard. Evaluate both through the same machine-owned sync/async helper. Keep raw kwargs only for callbacks/handlers. Add sync and async declarative tests with more than 50 valid keys plus private/overlong keys, and assert can/do receive equivalent fresh sanitized mappings while the handler still receives its intended raw payload.

### CR-03: Failed builder validation leaves invalid state and transition staging behind

**Classification:** BLOCKER

**File:** `/Users/akriz/code/fast_fsm/src/fast_fsm/core.py:2749-2766`

**Issue:** `FSMBuilder.add_state()` inserts into `_states` before recursive async/cycle validation, and `add_transition()` appends to `_transitions` before that validation (lines 2809-2813). A supported wrapper cycle raises `ValueError` only after the mutation. In an asserted-pure reproduction, a failed `add_transition()` changed the staged transition count from 0 to 1 (`ValueError 0 1 True`). The caller cannot repair this through the public builder API; a later build retains the request that was explicitly rejected. A declarative state whose metadata contains a cycle has the same problem in `_states`. This violates the phase's validate-before-mutation and failed-build-repairability invariants and risks publishing topology the caller believes was rejected.

**Fix:** Normalize `unless`, run `_detect_async_requirements()`, and compute any machine-type upgrade into locals before mutating `_transitions`, `_states`, or `_machine_type`. Commit all staging changes only after validation succeeds. Add identity assertions that every supported cycle leaves the state registry, transition list, machine type, and cached machine exactly unchanged for both mutators.

### CR-04: Valid deep condition graphs crash at Python's recursion limit

**Classification:** BLOCKER

**File:** `/Users/akriz/code/fast_fsm/src/fast_fsm/core.py:1376-1402`

**Issue:** `_contains_async_requirement()` recursively visits every wrapper, and both runtime evaluators recursively descend the same graph (lines 1404-1504). A valid acyclic chain of 1,200 `NotCondition` nodes raises `RecursionError` during `add_transition()` in an asserted-pure checkout. Phase 16 explicitly treats adversarial depth as a high-severity denial-of-service threat and specifies iterative/guarded identity traversal; testing only 24 levels does not establish that mitigation. Valid supported graphs should either terminate deterministically or be rejected with a deliberate documented bound, not crash at an interpreter-global implementation limit.

**Fix:** Replace classifier recursion with an explicit stack and active/completed identity states. Implement runtime evaluation with explicit frames that preserve And/Or short-circuit order, or enforce a documented deterministic wrapper-depth limit before evaluation and raise a domain `ValueError`. Add pure/compiled tests above the Python recursion limit as well as deep cycles and shared DAGs.

## Warnings

### WR-01: Child-command validation does not contain commands to the temporary checkout

**Classification:** WARNING

**File:** `/Users/akriz/code/fast_fsm/tools/phase16_isolated_verify.py:134-146`

**Issue:** `_validate_child_command()` checks whether each argv token is itself an absolute or `..` path, but subprocesses can still escape through code strings, shell commands, environment-derived paths, symlinks, or executables that accept embedded paths. For example, `sh -c 'cd /absolute/path && ...'` passes because the complete code string is not an absolute `Path`. The helper and Phase 16 plan claim child commands cannot escape the temporary repository, which this check cannot guarantee.

**Fix:** Treat arbitrary task commands as trusted and remove the containment claim, or execute them inside an actual OS/container sandbox with the temporary tree as the only writable mount. If task mode is meant only for fixed verification commands, replace arbitrary argv with an allowlisted suite/action selector.

### WR-02: The compiled semantic parity suite omits a changed Phase 16 boundary test file

**Classification:** WARNING

**File:** `/Users/akriz/code/fast_fsm/tools/phase16_isolated_verify.py:26-43`

**Issue:** `tests/test_boundary_negative.py` is a Phase 16 review/change file but is absent from `PHASE16_INVENTORY`, and the fixed `phase16` semantic command at lines 290-303 does not run it. The final pure release gate may cover the file, but no compiled run proves its canonical duplicate-state and negative-boundary semantics. The phase's primary parity harness can therefore pass while the native extension disagrees on changed boundary behavior.

**Fix:** Add `tests/test_boundary_negative.py` to `PHASE16_INVENTORY` and to the semantic pytest tuple executed in both pure and compiled modes. Regenerate the recorded Phase 16 evidence after the expanded fixed suite passes.

### WR-03: The documented FSMBuilder example cannot run against the actual API

**Classification:** WARNING

**File:** `/Users/akriz/code/fast_fsm/docs/dev/architecture.md:130-138`

**Issue:** The example constructs `FSMBuilder("my_fsm")`, but the constructor requires an initial `State`; it then calls `.set_initial("idle")`, which does not exist. This is the central contributor-facing example in the section documenting the newly tightened builder contract, so it directs maintainers and agents to a nonexistent API.

**Fix:** Use the actual constructor and fluent surface, for example `FSMBuilder(idle, name="my_fsm").add_state(running).add_transition(...).build()`, and add a documentation example check or doctest so public API examples cannot drift silently.

---

_Reviewed: 2026-08-30T13:54:27Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
