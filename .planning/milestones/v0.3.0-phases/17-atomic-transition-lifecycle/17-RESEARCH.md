# Phase 17: Atomic Transition Lifecycle - Research

**Researched:** 2026-09-01
**Domain:** In-process transition transactions, callback ordering, structured failure results, async cancellation, and committed-only history
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

### Lifecycle Stage Order
- **D-01:** Sync and async dispatch use one authoritative lifecycle stage model. Guard resolution and state permission happen before lifecycle callbacks; callback stages are explicitly classified as pre-commit or post-commit rather than inferred from whether state mutation already happened. — **Reversibility:** costly — changing this after v0.3.0 would reorder user side effects across every callback surface.
- **D-02:** The observable order is: before-transition listeners; source state's `on_exit`; registered source exit callbacks (sync then async at this same slot for async machines); exit-state listeners; **commit** current state and append history; destination state's `on_enter`; registered destination enter callbacks (sync then async at this same slot); enter-state listeners; declarative handler; trigger-specific callbacks; after-transition listeners. Registration order is preserved within each collection. — **Reversibility:** costly — applications may depend on this documented order for resource and persistence work.
- **D-03:** Async lifecycle work is awaited at the equivalent sync lifecycle slot. `trigger_async()` must not run the complete sync lifecycle and then append a second async callback tail.
- **D-04:** The first lifecycle callback failure stops later lifecycle callbacks for that transition. A pre-commit failure leaves the source current; a post-commit failure leaves the destination current. No compensating callback or rollback is attempted.

### Truthful Failure Result
- **D-05:** Keep the established value-returning API. Extend `TransitionResult` additively with `committed: bool`, a stable documented stage identifier, and the original exception as `cause`; do not make ordinary `trigger()`/`trigger_async()` callback failures raise by default. — **Reversibility:** costly — these fields become the public v0.3.0 failure-inspection contract.
- **D-06:** A successful transition has `success=True`, `committed=True`, no failure stage, and no cause. Every failed result has `success=False`; pre-commit failures report `committed=False`, while post-commit failures report `committed=True`.
- **D-07:** Stage identifiers are stable lowercase strings documented as part of the result contract. They distinguish at least resolution, guard, state permission, before-transition, source-exit, commit, destination-enter, declarative-handler, trigger-callback, and after-transition failures; private helper types may organize them internally.
- **D-08:** `TransitionResult.raise_if_failed()` remains the opt-in exception boundary and raises `TransitionError` chained from the stored cause. Error text is concise and stage-aware; raw callback payload values are never added to it or logs.

### Exactly-Once Failure Observation
- **D-09:** Route every failed trigger path through one internal failure finalizer. Each registered `on_failed` observer is invoked exactly once, in registration order, whether failure comes from resolution, a guard, state permission, a lifecycle callback, a declarative handler, or cancellation.
- **D-10:** An exception raised by a failure observer never recursively invokes failure handling and never replaces the transition's original result/cause. Continue to the remaining failure observers once each and emit only redacted diagnostic metadata for observer failures.
- **D-11:** Preserve the existing failure-observer call signature for backward compatibility. Structured stage, commit, and cause information belongs on the returned `TransitionResult`; do not inject new reserved payload keys that could collide with caller kwargs.

### Cancellation and Committed History
- **D-12:** The commit section is non-awaiting and indivisible with respect to the event loop: update current state and append one history record together. History records committed transitions even when a later callback fails, and never records a transition that fails or is cancelled before commit.
- **D-13:** `asyncio.CancelledError` is never converted into an ordinary failed result or swallowed. Notify failure observers once using the reached stage, preserve source/no-history before commit or destination/history after commit, then re-raise the original cancellation.
- **D-14:** Do not shield the lifecycle from cancellation and do not attempt rollback after commit. Cancellation stops at the current awaited callback; all later callbacks remain uncalled.

### the agent's Discretion
- Exact private lifecycle context/result-builder types and helper names, provided `core.py` remains the sole mypyc compilation unit and hot-path objects satisfy the slots policy.
- Exact stable stage-string spelling within the categories above, error-message wording, and test helper organization.
- Whether history append is expressed immediately before or after the current-state assignment inside the non-awaiting commit helper, provided no callback/await can observe an intermediate state and failure/cancellation semantics remain coherent.
- How to minimize unconditional-success overhead while retaining the ≥200,000 compiled `trigger()` operations/sec floor.

### Deferred Ideas (OUT OF SCOPE)
- Reentrant transition rejection and independent-caller serialization remain Phase 18.
- Redacted trace payloads, logging-handler ownership, and bounded diagnostics remain Phase 19.
- Installed wheel lifecycle parity across the final release matrix remains Phase 20.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| LIFE-01 | “A user observes one documented callback order with explicit pre-commit, commit, and post-commit stages in both sync and async machines.” [VERIFIED: .planning/REQUIREMENTS.md:31-34] | One stage catalog, paired runners, an order recorder, and documentation generated from the same contract. |
| LIFE-02 | “A pre-commit callback failure preserves the source state and returns or raises a failure that identifies the failed stage and original cause.” [VERIFIED: .planning/REQUIREMENTS.md:31-35] | Fail-fast pre-commit runner, original-cause retention, and `raise_if_failed()` chaining tests. |
| LIFE-03 | “A post-commit callback failure preserves the destination state, reports `committed=True`, and never reports the transition as successful.” [VERIFIED: .planning/REQUIREMENTS.md:31-36] | Non-awaiting commit helper plus post-commit failure matrix. |
| LIFE-04 | “Each failed transition notifies failure observers exactly once without swallowing the callback exception or recursively re-entering failure handling.” [VERIFIED: .planning/REQUIREMENTS.md:31-37] | One finalizer, registration-order observer loop, observer-error isolation, and cardinality assertions for every failure family. |
| LIFE-05 | “Transition history records only committed transitions and remains coherent when callbacks fail or async work is cancelled.” [VERIFIED: .planning/REQUIREMENTS.md:31-38] | Commit-owned history append and pre/post-commit failure/cancellation tests. |
| LIFE-06 | “Sync and async transitions expose equivalent state, result, callback-order, guard-context, and failure semantics.” [VERIFIED: .planning/REQUIREMENTS.md:31-39] | One scenario table executed against sync and async machines in asserted pure and freshly compiled contexts. |
</phase_requirements>

## Summary

Phase 17 should replace the current best-effort callback chain with one explicit transition transaction. The present sync executor catches and logs each callback exception, continues through later callbacks, mutates current state midway, records history only after all post-commit callbacks, and then reports success. [VERIFIED: src/fast_fsm/core.py:1992-2130] The async path first runs that complete sync executor, then invokes the declarative handler and appends async exit/enter callbacks as a second tail. [VERIFIED: src/fast_fsm/core.py:2496-2642] Those facts directly explain the accepted Phase 16 risk: “Lifecycle failure ordering” was accepted only because Phase 17 owns its repair. [VERIFIED: .planning/phases/16-canonical-graph-dispatch-invariants/16-SECURITY.md:32-49,55-61]

The implementation should retain `_PreparedDispatch`, direct dictionary resolution, the existing callback registries, and bounded `deque` history, but make stage and commit state explicit from guard evaluation through the final observer notification. [VERIFIED: src/fast_fsm/core.py:334-353,458-539,1481-1515,1992-2250] Use separate sync and async runners because a sync API cannot share an `async def` runner without event-loop or coroutine overhead; keep them aligned through one stage catalog, shared result/finalizer/commit helpers, and the same table-driven behavioral matrix. [ASSUMED]

The public evolution is additive: keep the first five `TransitionResult` fields and their positional order exactly as “`success`, `from_state`, `to_state`, `trigger`, `error`,” append `committed`, `stage`, and `cause` with defaults, and keep ordinary triggers value-returning. [VERIFIED: src/fast_fsm/core.py:243-265; .planning/phases/17-atomic-transition-lifecycle/17-CONTEXT.md:22-26] Store `cause` without including it in the dataclass representation, because direct access is required but an exception representation may contain callback payload data. [ASSUMED]

**Primary recommendation:** Implement a low-allocation staged transaction in `core.py`, route every trigger failure through one finalizer, prove each stage with a single sync/async scenario table, and freeze the design only after fresh pure/compiled semantic and throughput gates pass. [ASSUMED]

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Transition resolution and guard evaluation | In-process API/backend-equivalent runtime | Interpreted condition layer | `_prepare_transition()` already owns one canonical O(1) lookup and guard-context preparation; conditions remain outside the compiled module. [VERIFIED: src/fast_fsm/core.py:1481-1515; .specify/decisions/ADR-003-mypyc-compilation-boundary.md:26-42] |
| Lifecycle order and stage tracking | In-process API/backend-equivalent runtime | User callback boundary | `StateMachine` and `AsyncStateMachine` own execution; callback code is caller supplied and may fail or cancel. [VERIFIED: src/fast_fsm/core.py:1992-2250,2355-2642] |
| Commit and transition history | In-process runtime state/storage | Public history copy boundary | Current state and bounded history are machine-owned memory; `history` returns a defensive list. [VERIFIED: src/fast_fsm/core.py:458-536,844-881,2120-2126] |
| Failure inspection | Public result API | Opt-in exception boundary | `TransitionResult` is returned by default and `raise_if_failed()` creates `TransitionError`. [VERIFIED: src/fast_fsm/core.py:227-265; .specify/decisions/ADR-002-trigger-result-not-exception.md:29-46] |
| Failure observation | In-process observer boundary | Redacted logging | `on_failed` currently stores callbacks with the signature “`fn(trigger, from_state, error, **kwargs)`.” [VERIFIED: src/fast_fsm/core.py:1361-1367] |
| Pure/native proof | Developer evidence tooling | mypyc build boundary | The Phase 16 harness exports fresh trees and asserts `.py` or native origin before semantic commands. [VERIFIED: tools/phase16_isolated_verify.py:1-7,181-210] |

## Project Constraints (from AGENTS.md)

- Use `uv` for every Python/package/test command; direct `python`, `pip`, and `python -m pytest` are forbidden. [VERIFIED: .github/copilot-instructions.md:32-38]
- The hot-path policy requires `__slots__`; the exact compiled throughput floor is “`200,000 ops/sec`,” and the four exact core operations “`trigger()`, `can_trigger()`, `add_state()`, `add_transition()`” must remain “`O(1)`.” [VERIFIED: .github/copilot-instructions.md:40-48]
- Preserve the verbatim callback/condition call shape “`*args, **kwargs`,” do not remove public symbols, and keep new behavior additive. [VERIFIED: .github/copilot-instructions.md:50-53]
- Run targeted tests during development, sequentially, then the full command “`uv run pytest tests/ -x -q`” once before integration. [VERIFIED: .github/copilot-instructions.md:55-61]
- Ruff formatting/lint and mypy are blocking; `ty` remains independently visible and advisory. [VERIFIED: .github/copilot-instructions.md:206-221]
- Pure evidence must use the non-destructive source-origin preflight; native shadows are reported and must not be deleted implicitly. [VERIFIED: .github/copilot-instructions.md:63-71]
- Only `core.py` compiles; `conditions.py` and `condition_templates.py` remain interpreted for user subclassing. [VERIFIED: .github/copilot-instructions.md:287-302; setup.py:16-39]
- Update the relevant SPR in the same commit as significant behavior changes; ADRs are append-only and an accepted ADR must not be edited in place. [VERIFIED: .github/copilot-instructions.md:308-380]
- Use `bd` for all work tracking, pass `--json` for programmatic calls, and do not create Markdown task tracking. [VERIFIED: AGENTS.md:18-99]
- Preserve unrelated dirty work; stage only explicit task paths and never use `git add .` or `git add -A`. [VERIFIED: .github/copilot-instructions.md:112-116]

## Current-State Diagnosis

| Area | Current behavior | Planning consequence |
|------|------------------|----------------------|
| Result object | `TransitionResult` is a slotted dataclass with exactly “`success`, `from_state`, `to_state`, `trigger`, `error`”; `raise_if_failed()` raises without chaining a stored cause because no cause exists. [VERIFIED: src/fast_fsm/core.py:243-265] | Append fields at the end, keep old constructor calls valid, and add cause chaining without changing default trigger behavior. [ASSUMED] |
| Failure notification | Sync and async triggers duplicate five separate observer loops each. [VERIFIED: src/fast_fsm/core.py:2132-2240,2496-2603] | Replace every loop with one `_finalize_failure`-equivalent helper. [ASSUMED] |
| Callback failure | Sync callbacks catch `Exception`, log the exception text, continue, and report success. [VERIFIED: src/fast_fsm/core.py:1992-2130] | Remove stage-local swallowing; first failure returns a redacted failed result and stops the transaction. [ASSUMED] |
| Async lifecycle | The docstring promises async callbacks fire “after all synchronous callbacks,” and code executes them only after sync execution and the declarative handler. [VERIFIED: src/fast_fsm/core.py:2355-2365,2496-2642] | Update code, tests, docstrings, README, quick start, maintainer docs, and SPR to the same-slot rule. [ASSUMED] |
| Declarative outcome | Ordinary triggers invoke the handler but ignore its returned `TransitionResult`; the helper catches exceptions and loses the original exception object. [VERIFIED: src/fast_fsm/core.py:2242-2249,2605-2612,2709-2808] | Ordinary lifecycle must inspect normalized handler failure while preserving exactly-once invocation and original cause. [ASSUMED] |
| History timing | `_current_state` changes before post-commit callbacks, but history appends only after after-listeners and trigger callbacks. [VERIFIED: src/fast_fsm/core.py:2055-2126] | Move history append into the same non-awaiting commit helper as current-state assignment. [ASSUMED] |
| Failure logging | Callback and observer logs interpolate `str(exception)`, which may contain payload values. [VERIFIED: src/fast_fsm/core.py:2001-2118,2147-2237] | Log stage/type/index metadata only; expose the object solely through `result.cause`. [ASSUMED] |
| Legacy tests | Existing tests assert callback exceptions still succeed, later listeners run after an earlier listener crashes, and async exit/enter callbacks run after sync enter. [VERIFIED: tests/test_advanced_functionality.py:320-350,1177-1244; tests/test_listeners.py:308-350; tests/test_async.py:828-891] | These are expected RED tests under the locked safe-default contract and must be rewritten, not preserved as compatibility evidence. [ASSUMED] |
| Existing success invariants | Phase 16 proved guard context parity, declarative exactly once, and bounded history in pure and native modes. [VERIFIED: .planning/phases/16-canonical-graph-dispatch-invariants/16-VERIFICATION.md:36-44,118-145] | Phase 17 tests must extend those paths without reopening topology/builder/guard decisions. [ASSUMED] |

## Standard Stack

### Core

| Component | Version / Shape | Purpose | Why Standard |
|-----------|-----------------|---------|--------------|
| Python | `>=3.10` [VERIFIED: pyproject.toml:1-9] | Runtime language, exception chaining, asyncio cancellation, dataclasses, deque | This is the shipped language floor; no new runtime dependency is needed. [ASSUMED] |
| `src/fast_fsm/core.py` | Sole mypyc unit [VERIFIED: setup.py:16-39] | Results, sync/async lifecycle, callbacks, history | The locked compilation boundary requires all lifecycle orchestration to remain here. [VERIFIED: .planning/phases/17-atomic-transition-lifecycle/17-CONTEXT.md:38-42] |
| `dataclasses.dataclass(slots=True)` and `field` | Standard library [VERIFIED: src/fast_fsm/core.py:30,243-244] | Additive result fields with no instance dictionary | Extends the existing result representation while retaining slots. [ASSUMED] |
| `collections.deque(maxlen=...)` | Standard library [VERIFIED: src/fast_fsm/core.py:15-17,844-881] | O(1) bounded committed history | LIFE-07 already established this storage and Phase 17 changes only append placement. [VERIFIED: .planning/REQUIREMENTS.md:39] |
| `asyncio` | Standard library [VERIFIED: src/fast_fsm/core.py:31,2355-2642] | Awaited lifecycle work and cancellation propagation | Async dispatch already depends on it; no shielding or alternate scheduler is allowed. [VERIFIED: .planning/phases/17-atomic-transition-lifecycle/17-CONTEXT.md:33-36] |

### Supporting

| Component | Version | Purpose | When to Use |
|-----------|---------|---------|-------------|
| pytest | `8.4.1` [VERIFIED: local `uv run pytest --version` probe on 2026-09-01] | Table-driven lifecycle and result tests | Every implementation task; run targeted selections. [ASSUMED] |
| pytest-asyncio | Existing lower bound `>=1.3.0` [VERIFIED: pyproject.toml:11-20] | Deterministic async cancellation tests | Use event synchronization, not sleeps. [VERIFIED: .planning/phases/17-atomic-transition-lifecycle/17-CONTEXT.md:92-97] |
| mypy/mypyc | `1.17.1` [VERIFIED: pyproject.toml:21-25,42-44; local probe on 2026-09-01] | Type and compiled-boundary gate | Run after each private type/result-shape change. [ASSUMED] |
| Ruff | `0.12.11` [VERIFIED: local `uv run ruff --version` probe on 2026-09-01] | Format/lint | Run on exact changed Python files before tests. [VERIFIED: .github/copilot-instructions.md:206-218] |
| Sphinx | `9.1.0` [VERIFIED: local `uv run sphinx-build --version` probe on 2026-09-01] | Public stage/result documentation | Build HTML with warnings as errors and doctests after public docs change. [VERIFIED: .github/copilot-instructions.md:254-275] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Paired explicit sync/async runners | One generic coroutine runner | A generic coroutine would force sync dispatch through event-loop/coroutine machinery and threaten the hot-path floor; paired runners need exhaustive parity tests to prevent drift. [ASSUMED] |
| Shared result/finalizer/commit helpers | Exception subclasses per stage | Stage-specific exceptions would conflict with the locked value-returning default and add public surface. [VERIFIED: .specify/decisions/ADR-002-trigger-result-not-exception.md:29-46] |
| Stable string stage field | Public enum | A new enum/export is unnecessary; the locked contract explicitly requires stable lowercase strings and permits private organization. [VERIFIED: .planning/phases/17-atomic-transition-lifecycle/17-CONTEXT.md:22-26] |
| Direct ordered calls | Middleware/event-bus framework | Extra abstraction and dependency layers would add allocation/dispatch overhead and violate the minimal-runtime posture. [VERIFIED: .planning/PROJECT.md:101-125; pyproject.toml:1-9] |

**Installation:** None. Phase 17 should add no package and should retain the one runtime dependency shown verbatim as “`mypy-extensions>=1.0`.” [VERIFIED: pyproject.toml:1-9]

## Package Legitimacy Audit

Not applicable: the recommended implementation installs no package. [VERIFIED: pyproject.toml:1-9] No package-legitimacy gate is required unless planning introduces a dependency contrary to this research. [ASSUMED]

## Architecture Patterns

### System Architecture Diagram

```text
trigger / trigger_async
        |
        v
canonical lookup (_PreparedDispatch)
        | missing ---------------------------> failure finalizer -> failed result
        v
guard evaluation
        | false / exception -----------------> failure finalizer -> failed result
        v
state permission
        | false / exception -----------------> failure finalizer -> failed result
        v
PRE-COMMIT
  before listeners
  source.on_exit
  registered source callbacks [sync, then awaited async in async runner]
  exit-state listeners
        | first failure ----------------------> failure finalizer -> source/no history
        v
COMMIT (no await, no user callback)
  current_state = destination + optional history append
        v
POST-COMMIT
  destination.on_enter
  registered destination callbacks [sync, then awaited async in async runner]
  enter-state listeners
  declarative handler
  trigger callbacks
  after-transition listeners
        | first failure ----------------------> failure finalizer -> destination/history
        v
success result (success=True, committed=True, stage=None, cause=None)

At any async await:
  CancelledError -> failure finalizer once -> re-raise original cancellation
```

This flow is the locked D-01 through D-14 contract expressed as a planning diagram. [VERIFIED: .planning/phases/17-atomic-transition-lifecycle/17-CONTEXT.md:16-42]

### Recommended Project Structure

```text
src/fast_fsm/core.py                        # result fields, stage model, finalizer, commit, paired runners
tests/test_transition_lifecycle.py          # new table-driven sync/async stage and failure matrix
tests/test_async.py                         # existing async callback/declarative regressions updated
tests/test_advanced_functionality.py        # existing result/history/callback tests updated
tests/test_listeners.py                     # fail-fast listener and registration-order tests updated
tests/test_builder.py                       # builder/declarative exactly-once compatibility regressions
tests/test_boundary_negative.py             # additive constructor/result/error compatibility
tests/test_mypyc_guard.py                    # slots/public shape/compiled boundary guards
tests/test_performance_benchmarks.py         # compiled floor and lifecycle overhead selection
tools/phase16_isolated_verify.py             # preserve old interface; add explicit Phase 17 suite/inventory
docs/QUICK_START.md                          # public order, commit, failure, cancellation usage
README.md                                    # result fields and lifecycle summary
docs/dev/architecture.md                     # maintainer stage/commit contract
docs/dev/testing.md                          # Phase 17 pure/native matrix
.specify/memory/spr-core-api.md              # living runtime contract
.specify/decisions/ADR-004-*.md              # append-only lifecycle decision record
evidence/release-baseline.json               # reviewed final pure-source write only
```

The file mapping follows current source-to-test policy and the Context requirement that docs, ADR/SPR memory, release evidence, and pure/native tests agree. [VERIFIED: .github/copilot-instructions.md:235-251; .planning/phases/17-atomic-transition-lifecycle/17-CONTEXT.md:84-88] The exact new test and ADR filenames are recommendations. [ASSUMED]

### Pattern 1: One Stage Catalog, Two Execution Strategies

**What:** Define private stable stage constants once, then have explicit sync and async runners advance the same semantic cursor in the same order. Share commit, success-result, failed-result, and failure-finalizer helpers; do not append an async callback tail. [ASSUMED]

**Recommended public stage strings:** `resolution`, `guard`, `state-permission`, `before-transition`, `source-exit`, `source-exit-callback`, `exit-state-listener`, `commit`, `destination-enter`, `destination-enter-callback`, `enter-state-listener`, `declarative-handler`, `trigger-callback`, `after-transition`. [ASSUMED]

The locked minimum categories are quoted verbatim as “resolution, guard, state permission, before-transition, source-exit, commit, destination-enter, declarative-handler, trigger-callback, and after-transition.” [VERIFIED: .planning/phases/17-atomic-transition-lifecycle/17-CONTEXT.md:22-26] The additional callback/listener strings make every observable slot identifiable without separating sync and async variants. [ASSUMED]

### Pattern 2: One Non-Recursive Failure Finalizer

**What:** Construct one failed result, then call one finalizer exactly once with the original source and raw caller kwargs. The finalizer invokes all registered observers in order with the unchanged call signature, catches observer failures locally, logs only observer index/type plus transition stage, and returns the original result unchanged. [ASSUMED]

**Why:** Current trigger methods duplicate observer loops at resolution, guard false, guard exception, declarative rejection, and state rejection. [VERIFIED: src/fast_fsm/core.py:2132-2240,2496-2603] A finalizer that calls itself after an observer exception would violate D-10; observer errors must terminate only that observer call. [VERIFIED: .planning/phases/17-atomic-transition-lifecycle/17-CONTEXT.md:28-31]

**Exception boundary:** Catch `BaseException` only inside this narrow observer-isolation loop so an observer-raised `CancelledError`, `KeyboardInterrupt`, or `SystemExit` cannot replace the transition's original result/cause; continue to remaining observers. [ASSUMED] Do not apply that broad catch to ordinary lifecycle callbacks, where `Exception` becomes a failed result, original `CancelledError` is separately finalized/re-raised, and unrelated control-flow `BaseException` behavior remains unchanged. [ASSUMED]

### Pattern 3: Commit Owns Current State and History

**What:** The commit helper must execute no callback and no `await`; it updates `_current_state` and appends one `TransitionRecord` when history is enabled. Set the local committed flag only after this helper completes. [ASSUMED]

**When to use:** Exactly once after all pre-commit stages pass and before any destination/post-commit stage starts. [VERIFIED: .planning/phases/17-atomic-transition-lifecycle/17-CONTEXT.md:16-20,33-36]

**Implication:** A source-exit failure or cancellation produces no record; destination-enter, declarative, trigger-callback, and after-transition failure/cancellation leave one record and the destination current. [VERIFIED: .planning/phases/17-atomic-transition-lifecycle/17-CONTEXT.md:18-20,33-36]

### Pattern 4: Preserve Cause Without Accidental Disclosure

**What:** Store the exact exception object by identity in `cause`, but exclude it from `TransitionResult.__repr__` and avoid `str(cause)` in error/log text. Build concise messages from stage plus safe machine metadata; `raise_if_failed()` raises `TransitionError` using `raise error from result.cause`. [ASSUMED]

**Why:** The locked contract requires both original-cause access and no raw callback payload values in error text/logs. [VERIFIED: .planning/phases/17-atomic-transition-lifecycle/17-CONTEXT.md:22-26] A dataclass field defaults to representation inclusion unless configured otherwise, so this needs an explicit regression assertion. [ASSUMED]

### Pattern 5: Declarative Invocation Is a Lifecycle Stage, Not a Detached Side Effect

**What:** Keep `_resolve_declarative_handler()` and exactly-once selection, but split raw invocation from compatibility normalization so ordinary dispatch can observe false/raising/invalid outcomes and retain the original exception. [ASSUMED] Direct `handle_event()` / `handle_event_async()` remain compatibility helpers without machine commit state. [ASSUMED]

**Outcome normalization recommendation:** `None`, `True`, and `TransitionResult(success=True)` allow the lifecycle to continue; `False`, `TransitionResult(success=False)`, an invalid return type, or an exception fail the overall transaction at `declarative-handler`. [ASSUMED] The Phase 16 tests deliberately left those exact failure forms for Phase 17. [VERIFIED: tests/test_builder.py:414-497; tests/test_async.py:935-1028]

### Component Responsibilities

| Component / Symbol | Responsibility After Phase 17 |
|--------------------|-------------------------------|
| `TransitionResult` | Backward-compatible data carrier with truthful `committed`, `stage`, and hidden-from-repr `cause`. [ASSUMED] |
| `TransitionError` / `raise_if_failed()` | Opt-in exception with `.result` and direct `__cause__` identity when a cause exists. [VERIFIED: .planning/phases/17-atomic-transition-lifecycle/17-CONTEXT.md:22-26] |
| `_prepare_transition()` | Canonical lookup and sanitized guard preparation only; missing resolution returns a staged failure for finalization. [ASSUMED] |
| Guard/state-permission orchestration | Convert false to cause-less failed result, retain raised `Exception` as cause, and never start lifecycle callbacks on failure. [ASSUMED] |
| Sync lifecycle runner | Execute every sync-visible slot explicitly and fail fast. [ASSUMED] |
| Async lifecycle runner | Execute the same slots, awaiting registered async exit/enter callbacks at their matching slots. [VERIFIED: .planning/phases/17-atomic-transition-lifecycle/17-CONTEXT.md:16-20] |
| Commit helper | Mutate current state and append history with no callback/await. [VERIFIED: .planning/phases/17-atomic-transition-lifecycle/17-CONTEXT.md:33-36] |
| Failure finalizer | Notify every observer once in registration order, isolate observer failures, return the original result. [VERIFIED: .planning/phases/17-atomic-transition-lifecycle/17-CONTEXT.md:28-31] |
| `force_state` / `reset` / `restore` | Preserve existing public signatures and synthetic-force behavior; Phase 17's structured ordinary-trigger failure API must not silently expand to these control mutators. [ASSUMED] |

### Anti-Patterns to Avoid

- **Catch-and-continue per callback:** It creates a successful result after partial lifecycle failure. [VERIFIED: src/fast_fsm/core.py:1992-2130]
- **Run `_execute_transition()` then await async callbacks:** It makes async exit happen after sync enter and after commit. [VERIFIED: src/fast_fsm/core.py:2496-2642]
- **Append history at function return:** A post-commit callback can fail or cancel before history reaches the authoritative commit. [VERIFIED: src/fast_fsm/core.py:2055-2126]
- **Use current state to infer commit:** Post-commit callbacks and future Phase 18 ownership can mutate context; carry an explicit local committed flag. [ASSUMED]
- **Inject stage/result data into observer kwargs:** It can collide with user payload keys and breaks D-11. [VERIFIED: .planning/phases/17-atomic-transition-lifecycle/17-CONTEXT.md:28-31]
- **Log the exception message or result cause:** Callback exceptions can embed secrets; log only redacted metadata. [ASSUMED]
- **Shield async lifecycle:** It contradicts cancellation semantics and can run callbacks after the caller has cancelled. [VERIFIED: .planning/phases/17-atomic-transition-lifecycle/17-CONTEXT.md:33-36]
- **Add locks/reentrancy flags now:** Ownership and serialization are Phase 18 responsibilities. [VERIFIED: .planning/phases/17-atomic-transition-lifecycle/17-CONTEXT.md:101-106]
- **Change installed-wheel release jobs:** Installed-artifact parity remains Phase 20. [VERIFIED: .planning/phases/17-atomic-transition-lifecycle/17-CONTEXT.md:101-106]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Failure outcome transport | Stage-specific exception hierarchy | Existing slotted `TransitionResult` plus `TransitionError` | The established result-value contract is explicit and faster on expected failures. [VERIFIED: .specify/decisions/ADR-002-trigger-result-not-exception.md:29-84] |
| Bounded history | Ring buffer or list-front deletion | Existing `deque(maxlen=...)` | LIFE-07 already proved O(1) FIFO eviction and defensive read copies. [VERIFIED: src/fast_fsm/core.py:844-881; .planning/phases/16-canonical-graph-dispatch-invariants/16-VERIFICATION.md:43-44] |
| Cancellation control | Shielding, custom cancellation token, rollback | Native `CancelledError` propagation and reached-stage finalization | The locked contract explicitly forbids shielding and rollback. [VERIFIED: .planning/phases/17-atomic-transition-lifecycle/17-CONTEXT.md:33-36] |
| Callback pipeline | Event bus/middleware framework | Direct registry iteration in documented order | Existing lists preserve registration order and the hot path must stay shallow. [VERIFIED: src/fast_fsm/core.py:519-532,1255-1378] |
| Async/sync unification | `asyncio.run()` or thread offload | Explicit paired runners | Automatic offload and cross-loop policy are deferred or out of scope. [VERIFIED: .planning/REQUIREMENTS.md:43-49,81-88] |
| Failure-observer recursion protection | Retry/recursive notification framework | Local one-pass finalizer that never calls itself | D-10 requires remaining observers to continue without replacing cause. [VERIFIED: .planning/phases/17-atomic-transition-lifecycle/17-CONTEXT.md:28-31] |

**Key insight:** The transaction boundary is a semantic order plus one commit point, not a rollback engine. [VERIFIED: .planning/phases/17-atomic-transition-lifecycle/17-CONTEXT.md:16-20,33-36]

## Runtime State Inventory

This phase is a runtime refactor, so repository files are not the only state considered. [ASSUMED]

| Category | Items Found | Action Required |
|----------|-------------|-----------------|
| Stored data | No external datastore is configured for FSM current state/history; the authoritative values are per-instance `_current_state` and optional in-memory `_history`. [VERIFIED: src/fast_fsm/core.py:458-536,844-881] | No data migration. Existing live Python processes must be restarted/reloaded to obtain new class behavior. [ASSUMED] |
| Live service config | None found for lifecycle order, callbacks, or history; Fast FSM is an in-process library rather than a service. [VERIFIED: .planning/codebase/ARCHITECTURE.md:9-39] | No dashboard/API patch. [ASSUMED] |
| OS-registered state | None found; the phase changes no service, task, daemon, or OS registration. [VERIFIED: .planning/phases/17-atomic-transition-lifecycle/17-CONTEXT.md:6-10] | No OS re-registration. [ASSUMED] |
| Secrets/env vars | No rename or new variable. The exact existing build selectors are “`FAST_FSM_BUILD_MODE`” and “`FAST_FSM_PURE_PYTHON`.” [VERIFIED: setup.py:23-29] | Preserve selectors; do not place callback payloads in new diagnostic output. [VERIFIED: .planning/phases/17-atomic-transition-lifecycle/17-CONTEXT.md:22-31] |
| Build artifacts / installed packages | Four checkout-native shadows exist: `core.cpython-310-darwin.so`, `core.cpython-312-darwin.so`, `core__mypyc.cpython-310-darwin.so`, and `core__mypyc.cpython-312-darwin.so`. [VERIFIED: local `find src/fast_fsm` artifact inventory on 2026-09-01] | Do not delete them implicitly. Use fresh exported pure/native contexts; rebuild native code after `core.py` edits. Installed-wheel parity remains Phase 20. [VERIFIED: .github/copilot-instructions.md:63-71; .planning/phases/17-atomic-transition-lifecycle/17-CONTEXT.md:101-106] |

**Canonical answer:** after repository edits, loaded processes, checkout-native extensions, and previously installed packages can retain old lifecycle code; no database, service configuration, OS registration, or secret-name migration is required. [ASSUMED]

## Common Pitfalls

### Pitfall 1: Stage identifiers are too coarse or drift between runners
**What goes wrong:** A registered callback failure reports only `source-exit`, or async reports a different string than sync for the same slot. [ASSUMED]
**Why it happens:** Stage names are assigned ad hoc at catch sites. [ASSUMED]
**How to avoid:** Define one private catalog and a test mapping every injection point to one expected public string. [ASSUMED]
**Warning signs:** Duplicate string literals in sync/async runner bodies or untested stage values. [ASSUMED]

### Pitfall 2: Observer notification happens twice
**What goes wrong:** A guard helper finalizes a failure, then the public trigger finalizes the returned result again. [ASSUMED]
**Why it happens:** Failure construction and observation are mixed at multiple layers, as they are today. [VERIFIED: src/fast_fsm/core.py:2132-2240,2496-2603]
**How to avoid:** Lower helpers construct/raise; only the public trigger/cancellation boundary calls the finalizer. [ASSUMED]
**Warning signs:** One trigger increments an observer counter twice. [ASSUMED]

### Pitfall 3: Original cause is lost or leaked
**What goes wrong:** Code stores `str(exc)` only, or dataclass repr/error/log text exposes the cause message. [ASSUMED]
**Why it happens:** Current helpers normalize exceptions into strings and current logs interpolate them. [VERIFIED: src/fast_fsm/core.py:1992-2118,2194-2205,2749-2754,2792-2796]
**How to avoid:** Retain object identity in `cause`, use `repr=False`, and test a secret-bearing exception across result/error/exception/log channels. [ASSUMED]
**Warning signs:** `result.cause is not original` or a sentinel secret appears in `repr(result)`, `str(TransitionError)`, or `caplog.text`. [ASSUMED]

### Pitfall 4: History and state split at cancellation
**What goes wrong:** Destination becomes current but history is empty because cancellation lands before the old tail append. [VERIFIED: src/fast_fsm/core.py:2496-2642]
**Why it happens:** Commit and history are separated by awaitable callbacks. [VERIFIED: src/fast_fsm/core.py:2055-2126,2614-2640]
**How to avoid:** Put both operations in one no-await helper before destination callbacks. [VERIFIED: .planning/phases/17-atomic-transition-lifecycle/17-CONTEXT.md:33-36]
**Warning signs:** `committed=True` with no record when history is enabled. [ASSUMED]

### Pitfall 5: Cancellation is converted to a failed result
**What goes wrong:** `except BaseException` around the lifecycle catches `CancelledError` and returns normally. [ASSUMED]
**How to avoid:** Catch `CancelledError` separately, finalize an observer-only failure record, then use bare `raise` to preserve the original object/traceback. [ASSUMED]
**Warning signs:** The awaiting caller receives a `TransitionResult` instead of cancellation. [VERIFIED: .planning/phases/17-atomic-transition-lifecycle/17-CONTEXT.md:33-36]

### Pitfall 6: Sync callbacks are accidentally treated as cancellation points
**What goes wrong:** Tests expect cancellation to interrupt inline sync callback code. [ASSUMED]
**Why it happens:** Task cancellation is delivered at an await boundary; Phase 17 does not offload sync callbacks. [ASSUMED]
**How to avoid:** Synchronize tests at real awaited async callbacks/guards/handlers and document that sync callbacks remain inline. [VERIFIED: .planning/REQUIREMENTS.md:49,85-88]
**Warning signs:** Timing sleeps or thread offload in lifecycle tests. [ASSUMED]

### Pitfall 7: Declarative failure is invoked once but ignored
**What goes wrong:** Invocation count remains one while the outer trigger still returns its earlier success result. [VERIFIED: src/fast_fsm/core.py:2242-2249,2605-2612]
**How to avoid:** Make normalized handler outcome control the transaction before trigger/after callbacks. [ASSUMED]
**Warning signs:** False/raising handler leaves `result.success=True`. [ASSUMED]

### Pitfall 8: Legacy force/reset behavior changes accidentally
**What goes wrong:** Refactoring `_execute_transition()` changes `force_state()` return/raising/history behavior despite no Phase 17 decision. [ASSUMED]
**Why it happens:** `force_state()` currently delegates to that helper. [VERIFIED: src/fast_fsm/core.py:1840-1874,1992-2130]
**How to avoid:** Add force/reset/restore regressions and keep ordinary-trigger structured failure scope explicit. [ASSUMED]
**Warning signs:** Existing `force_state()` tests change without a requirement reference. [ASSUMED]

### Pitfall 9: Pure tests execute a stale native shadow
**What goes wrong:** Source coverage and semantics describe an old `.so`. [VERIFIED: .github/copilot-instructions.md:63-71]
**How to avoid:** Use fresh export/origin assertions before both matrices and never use checkout-native artifacts as evidence. [VERIFIED: tools/phase16_isolated_verify.py:1-7,181-210]
**Warning signs:** Pure `fast_fsm.core.__file__` ends in `.so`/`.pyd`. [VERIFIED: tools/phase16_isolated_verify.py:154-163]

### Pitfall 10: Performance is checked only after design freeze
**What goes wrong:** A context object, callback descriptor list, or generic runner allocates on every successful trigger and causes a late rewrite. [ASSUMED]
**How to avoid:** Capture before-change pure/compiled observations, measure after the first shared runner, and enforce the compiled floor again at the phase gate. [ASSUMED]
**Warning signs:** New tuple/list/coroutine creation in the unconditional success path. [ASSUMED]

## Code Examples

The examples below are implementation sketches, not existing API; recommended private names and exact stage spellings are therefore `[ASSUMED]`.

### Additive Result Shape and Cause Chaining

```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass(slots=True)
class TransitionResult:
    success: bool
    from_state: Optional[str] = None
    to_state: Optional[str] = None
    trigger: Optional[str] = None
    error: str = ""
    committed: bool = False
    stage: Optional[str] = None
    cause: Optional[BaseException] = field(
        default=None,
        repr=False,
        compare=False,
    )

    def raise_if_failed(self) -> "TransitionResult":
        if not self.success:
            failure = TransitionError(self)
            if self.cause is not None:
                raise failure from self.cause
            raise failure
        return self
```

The first five fields above quote the current source order exactly. [VERIFIED: src/fast_fsm/core.py:243-252] The three appended fields implement D-05/D-06, while the exact field name `stage` and repr/equality policy are recommendations. [VERIFIED: .planning/phases/17-atomic-transition-lifecycle/17-CONTEXT.md:22-26] [ASSUMED]

### Non-Recursive Failure Finalizer

```python
def _finalize_failure(
    self,
    result: TransitionResult,
    kwargs: Dict[str, Any],
) -> TransitionResult:
    for observer_index, observer in enumerate(self._on_failed_callbacks):
        try:
            observer(
                result.trigger,
                result.from_state,
                result.error,
                **kwargs,
            )
        except BaseException as observer_error:
            self._logger.warning(
                "%s: failure observer failed stage=%s index=%d type=%s",
                self._name,
                result.stage,
                observer_index,
                type(observer_error).__name__,
            )
    return result
```

This sketch preserves the exact current observer argument order “`trigger, from_state, error, **kwargs`.” [VERIFIED: src/fast_fsm/core.py:1361-1367] The helper name, log wording, and narrow `BaseException` policy are recommendations. [ASSUMED]

### Cancellation Boundary

```python
stage = "source-exit-callback"
try:
    await callback(to_state, trigger, **kwargs)
except asyncio.CancelledError as cancellation:
    cancelled_result = _failure_result(
        from_state=old_state.name,
        trigger=trigger,
        committed=committed,
        stage=stage,
        cause=cancellation,
    )
    self._finalize_failure(cancelled_result, kwargs)
    raise
```

The required semantics are verified from D-13/D-14; the chosen stage spelling and helper name are recommendations. [VERIFIED: .planning/phases/17-atomic-transition-lifecycle/17-CONTEXT.md:33-36] [ASSUMED]

## Detailed Lifecycle Test Matrix

| Injection Point | Expected Stage | Committed | State | History | Later Lifecycle Calls |
|-----------------|----------------|-----------|-------|---------|-----------------------|
| Missing transition | `resolution` [ASSUMED] | `False` | source | 0 | none |
| Entry/declarative guard false | `guard` [ASSUMED] | `False` | source | 0 | none |
| Guard exception | `guard` [ASSUMED] | `False` | source | 0 | none; `cause is exception` |
| State permission false/exception | `state-permission` [ASSUMED] | `False` | source | 0 | none |
| Before listener | `before-transition` [ASSUMED] | `False` | source | 0 | none after first failure |
| Source state `on_exit` | `source-exit` [ASSUMED] | `False` | source | 0 | no registered exit/listener/commit |
| Registered sync/async source callback | `source-exit-callback` [ASSUMED] | `False` | source | 0 | no later callback/listener/commit |
| Exit-state listener | `exit-state-listener` [ASSUMED] | `False` | source | 0 | no commit |
| Commit semantics | `None` on success [VERIFIED: .planning/phases/17-atomic-transition-lifecycle/17-CONTEXT.md:23-25] | `True` | destination | 1 if enabled | continue post-commit |
| Destination state `on_enter` | `destination-enter` [ASSUMED] | `True` | destination | 1 if enabled | no later post-commit call |
| Registered sync/async destination callback | `destination-enter-callback` [ASSUMED] | `True` | destination | 1 if enabled | no later post-commit call |
| Enter-state listener | `enter-state-listener` [ASSUMED] | `True` | destination | 1 if enabled | no handler/trigger/after |
| Declarative false/invalid/exception | `declarative-handler` [ASSUMED] | `True` | destination | 1 if enabled | no trigger/after |
| Trigger callback | `trigger-callback` [ASSUMED] | `True` | destination | 1 if enabled | no remaining trigger/after |
| After listener | `after-transition` [ASSUMED] | `True` | destination | 1 if enabled | no remaining after listener |

Every row follows the locked pre/post commit order and fail-fast rule; only the exact recommended strings are assumed. [VERIFIED: .planning/phases/17-atomic-transition-lifecycle/17-CONTEXT.md:16-26,33-36]

### Cancellation Matrix

| Awaited Point | Expected State/History | Observer | Caller Outcome |
|---------------|------------------------|----------|----------------|
| Async guard | source / 0 | once at guard | original `CancelledError` re-raised |
| Async registered source-exit callback | source / 0 | once at source-exit-callback | original `CancelledError` re-raised |
| Async registered destination-enter callback | destination / 1 if enabled | once at destination-enter-callback | original `CancelledError` re-raised |
| Async declarative handler | destination / 1 if enabled | once at declarative-handler | original `CancelledError` re-raised |

The state/history/propagation cells are locked; exact stage strings are recommended. [VERIFIED: .planning/phases/17-atomic-transition-lifecycle/17-CONTEXT.md:33-36] [ASSUMED]

## State of the Art

| Old Approach | Current Phase 17 Approach | When Changed | Impact |
|--------------|---------------------------|--------------|--------|
| Catch/log/continue every callback | First failure stops the transaction and produces a truthful staged outcome | v0.3.0 Phase 17 [VERIFIED: .planning/ROADMAP.md:134-147] | Prevents successful reports after required side effects fail. [ASSUMED] |
| State mutation midway, history at return | One non-awaiting current-state/history commit | v0.3.0 Phase 17 [VERIFIED: .planning/ROADMAP.md:134-147] | Makes post-commit failure and cancellation observable without history drift. [ASSUMED] |
| Sync lifecycle plus async tail | Async work awaited at the matching lifecycle slot | v0.3.0 Phase 17 [VERIFIED: .planning/phases/17-atomic-transition-lifecycle/17-CONTEXT.md:16-20] | Gives sync/async callback-order parity. [ASSUMED] |
| Repeated failure-observer loops | One finalizer with exact-once cardinality | v0.3.0 Phase 17 [VERIFIED: .planning/phases/17-atomic-transition-lifecycle/17-CONTEXT.md:28-31] | Prevents duplicate/recursive notification. [ASSUMED] |
| String-only callback errors | Stable stage, commit flag, and original cause object | v0.3.0 Phase 17 [VERIFIED: .planning/phases/17-atomic-transition-lifecycle/17-CONTEXT.md:22-26] | Supports structured inspection and exception chaining. [ASSUMED] |

**Deprecated/outdated:**
- Documentation stating async callbacks fire “after all synchronous callbacks” is outdated under D-03. [VERIFIED: src/fast_fsm/core.py:2355-2365]
- Tests asserting callback/listener exceptions do not abort and later callbacks still execute are outdated under D-04. [VERIFIED: tests/test_advanced_functionality.py:320-350,1177-1244; tests/test_listeners.py:308-350]
- SPR text saying callback exceptions are “caught and logged as warnings” is outdated once Phase 17 ships. [VERIFIED: .specify/memory/spr-core-api.md:36-37]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Use the fourteen recommended exact stage strings, including callback/listener-specific variants. | Architecture Patterns | Public v0.3.0 string contract and tests would need revision. |
| A2 | Append `stage` as the public field name and hide `cause` from repr/equality while preserving direct identity access. | Result Pattern | Public inspection or compatibility expectations could differ. |
| A3 | Catch `BaseException` only inside failure-observer isolation so no observer failure can replace the original outcome. | Failure Finalizer | Control-flow exceptions from observers would otherwise escape contrary to D-10. |
| A4 | Treat invalid declarative return values as `declarative-handler` failure during ordinary dispatch. | Declarative Pattern | Existing direct-helper normalization currently treats invalid values as success-with-error. |
| A5 | Preserve `force_state`/`reset`/`restore` signatures and keep their failure policy outside the ordinary trigger result contract. | Component Responsibilities | A broader interpretation of “transition lifecycle” would require an explicit public contract decision. |
| A6 | Extend the existing isolation harness with a backward-compatible Phase 17 suite instead of adding a package or replacing the harness. | Validation Architecture | A later generalization may choose a different tool boundary. |
| A7 | No new package is required. | Standard Stack | Introducing a package would require legitimacy and runtime-dependency review. |

These assumptions are recommended resolutions within the agent's discretion or an unexpanded phase boundary; none changes a locked D-01 through D-14 decision. [ASSUMED]

## Open Questions

No blocking research question remains. [ASSUMED] The planner should make A4 and A5 explicit truth/prohibition clauses so declarative compatibility helpers and force/reset/restore cannot drift accidentally. [ASSUMED]

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| `uv` | All Python/test/build commands | ✓ | `0.12.6` [VERIFIED: local probe on 2026-09-01] | None; required by project policy. |
| Python via uv | Runtime/tests | ✓ | `3.12.10` [VERIFIED: local probe on 2026-09-01] | Project floor is `>=3.10`. [VERIFIED: pyproject.toml:1-9] |
| pytest | Lifecycle tests | ✓ | `8.4.1` [VERIFIED: local probe on 2026-09-01] | None for merge gate. |
| mypy/mypyc | Core type/compile gate | ✓ | `1.17.1` [VERIFIED: local probe on 2026-09-01] | None for native proof. |
| Ruff | Format/lint | ✓ | `0.12.11` [VERIFIED: local probe on 2026-09-01] | None for quality gate. |
| Sphinx | Public docs | ✓ | `9.1.0` [VERIFIED: local probe on 2026-09-01] | None for warnings-as-errors docs gate. |
| Task | Gate orchestration | ✓ | `3.53.1` [VERIFIED: local probe on 2026-09-01] | Run documented underlying `uv` commands if wrapper use is unsuitable. [ASSUMED] |
| C compiler | Fresh mypyc build | ✓ | Apple clang `21.0.0` [VERIFIED: local probe on 2026-09-01] | Pure-only proof is insufficient for this performance-sensitive core phase. [ASSUMED] |

**Missing dependencies with no fallback:** None found. [VERIFIED: local environment probes on 2026-09-01]

**Missing dependencies with fallback:** None found. [VERIFIED: local environment probes on 2026-09-01]

## Validation Architecture

Validation is enabled by the exact configuration value “`"nyquist_validation": true`.” [VERIFIED: .planning/config.json:13-23]

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest `8.4.1`, pytest-asyncio lower bound `>=1.3.0` [VERIFIED: local probe on 2026-09-01; pyproject.toml:11-20] |
| Config file | `pyproject.toml`; exact values include `testpaths = ["tests"]`, `python_files = ["test_*.py"]`, and `asyncio_mode = "auto"`. [VERIFIED: pyproject.toml:55-73] |
| Quick run command | `uv run pytest tests/test_transition_lifecycle.py -x -q` [ASSUMED] |
| Full suite command | `uv run pytest tests/ -x -q` [VERIFIED: .github/copilot-instructions.md:55-61] |
| Pure/native command | `uv run python tools/phase16_isolated_verify.py --suite phase17` [ASSUMED] |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| LIFE-01 | Exact full order, registration order, pre/commit/post classification, async same-slot order | parameterized unit/integration | `uv run pytest tests/test_transition_lifecycle.py -x -q -k order` [ASSUMED] | ❌ Wave 0 |
| LIFE-02 | Every pre-commit failure preserves source, stage, cause identity, and chaining | parameterized unit | `uv run pytest tests/test_transition_lifecycle.py tests/test_advanced_functionality.py -x -q -k precommit` [ASSUMED] | ❌ Wave 0 + extend existing |
| LIFE-03 | Every post-commit failure preserves destination/history and reports failed+committed | parameterized unit | `uv run pytest tests/test_transition_lifecycle.py -x -q -k postcommit` [ASSUMED] | ❌ Wave 0 |
| LIFE-04 | One observer pass for resolution/guard/permission/all lifecycle/declarative/cancellation; observer errors continue without recursion | parameterized unit | `uv run pytest tests/test_transition_lifecycle.py tests/test_advanced_functionality.py -x -q -k observer` [ASSUMED] | ❌ Wave 0 + extend existing |
| LIFE-05 | Success/post-commit failure/cancel record once; pre-commit failure/cancel records zero | unit + async integration | `uv run pytest tests/test_transition_lifecycle.py tests/test_async.py tests/test_advanced_functionality.py -x -q -k history` [ASSUMED] | ❌ Wave 0 + extend existing |
| LIFE-06 | Same scenario table against sync/async and asserted pure/native origins | conformance | `uv run python tools/phase16_isolated_verify.py --suite phase17` [ASSUMED] | ❌ Wave 0 harness extension |

### Required Scenario Families

- Full successful order with two callbacks/listeners per collection, proving registration order and trigger-before-after ordering. [ASSUMED]
- Every row in the Detailed Lifecycle Test Matrix, asserting result fields, exact stage, state, history, callback suffix not called, and observer count. [ASSUMED]
- Guard false/raise, declarative guard false/raise, state permission false/raise, and missing resolution through the same finalizer. [ASSUMED]
- Declarative `None`/`True`/successful result plus `False`/failed result/invalid/raise, all invoked exactly once. [ASSUMED]
- Original-cause identity, `TransitionError.__cause__`, success chaining, legacy positional constructor calls, and no cause leakage through repr/error/logs. [ASSUMED]
- Observer order with multiple observers where early observers raise `RuntimeError` and `CancelledError`; later observers still run once, original result/cause is unchanged, and logs contain no payload sentinel. [ASSUMED]
- Event-synchronized cancellation at guard, source-exit async callback, destination-enter async callback, and async declarative handler; no timing sleeps. [VERIFIED: .planning/phases/17-atomic-transition-lifecycle/17-CONTEXT.md:92-97]
- Regression coverage for `force_state`, `reset`, `restore`, direct declarative compatibility helpers, builder callback registration, clone callback lists, and Phase 16 guard-context invariants. [ASSUMED]

### Pure/Compiled Evidence Design

Extend the existing fresh-export harness without weakening its path validation, explicit overlay inventory, no-native-pure check, locked environment setup, or origin assertion. [ASSUMED] The current verified sequence is export `HEAD`, overlay explicit paths, reject pure native artifacts, `uv sync --locked --all-groups`, optionally build compiled, then assert origin before the child command. [VERIFIED: tools/phase16_isolated_verify.py:94-105,181-210]

The Phase 17 suite should execute the same lifecycle/result/observer/history/declarative matrix in both asserted origins, then the compiled performance selection, then the asserted-pure full release gate. [ASSUMED] This is source-tree parity only; installed wheel parity remains Phase 20. [VERIFIED: .planning/phases/17-atomic-transition-lifecycle/17-CONTEXT.md:101-106]

### Sampling Rate

- **Per task commit:** `uv run pytest tests/test_transition_lifecycle.py -x -q` plus the exact touched legacy module. [ASSUMED]
- **After result/core shape changes:** `task typecheck-mypy` and `uv run pytest tests/test_mypyc_guard.py -x -q`. [ASSUMED]
- **Per lifecycle integration wave:** fresh pure and compiled targeted task contexts through the isolation harness. [ASSUMED]
- **Per wave merge:** `uv run pytest tests/test_transition_lifecycle.py tests/test_advanced_functionality.py tests/test_listeners.py tests/test_builder.py tests/test_async.py tests/test_boundary_negative.py -x -q`. [ASSUMED]
- **Phase gate:** full Phase 17 asserted pure/native suite, compiled `>=200000` trigger floor, slots audit, Ruff, blocking mypy, advisory ty, full sequential tests, Sphinx HTML `-W`, doctests, and read-only release-baseline freshness after one reviewed write. [VERIFIED: .github/copilot-instructions.md:40-71,206-275]

### Performance Evidence

The current durable manifest quotes `compiled_trigger_ops_per_sec_min: 200000`, a pure observation of `649247.89`, and a pure quality baseline of `1221` collected / `1221` passed / `0` failed / `0` errors / `0` skipped with `96.64` total and `95.13` core coverage. [VERIFIED: evidence/release-baseline.json:39-73] These are environment-labelled evidence values, not a new Phase 17 target. [VERIFIED: evidence/release-baseline.json:39-56]

Record three checkpoints: before-change pure/compiled observations, after the first staged runner/finalizer integration, and final pure/compiled phase gate. [ASSUMED] Keep the direct lookup O(1), avoid generic callback descriptor allocation on the no-listener success path, and preserve the disabled-history single `None` branch. [ASSUMED]

### Wave 0 Gaps

- `tests/test_transition_lifecycle.py` — new authoritative stage/order/failure/cancellation scenario table. [ASSUMED]
- Phase 17 suite/inventory in `tools/phase16_isolated_verify.py` — fresh pure/native origin proof. [ASSUMED]
- Lifecycle-specific compiled performance selection in `tests/test_performance_benchmarks.py`. [ASSUMED]
- Structural/API guards for appended slotted result fields and hidden cause representation in `tests/test_mypyc_guard.py` / `tests/test_boundary_negative.py`. [ASSUMED]
- Rewrite legacy success-after-callback-error and async-tail tests in `tests/test_advanced_functionality.py`, `tests/test_listeners.py`, and `tests/test_async.py`. [VERIFIED: tests/test_advanced_functionality.py:320-350,1177-1244; tests/test_listeners.py:308-350; tests/test_async.py:828-891]

No new test framework or shared `tests/conftest.py` fixture is needed. [ASSUMED]

## Security Domain

Security enforcement is enabled because `.planning/config.json` does not set `security_enforcement` to `false`. [VERIFIED: .planning/config.json:1-38]

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | In-process library exposes no authentication boundary. [VERIFIED: .planning/codebase/ARCHITECTURE.md:359-378] |
| V3 Session Management | no | No session/token store exists in the runtime. [VERIFIED: src/fast_fsm/core.py:458-536] |
| V4 Access Control | no | The library executes caller-registered code and defines no authorization policy. [VERIFIED: src/fast_fsm/core.py:1255-1378] |
| V5 Input Validation | yes | Validate callback/handler outcomes into one staged result; preserve sanitized guard context; reject/normalize invalid handler results. [ASSUMED] |
| V6 Cryptography | no | No cryptographic operation or secret-storage feature is in Phase 17. [VERIFIED: .planning/phases/17-atomic-transition-lifecycle/17-CONTEXT.md:6-10] |

### Known Threat Patterns for the Lifecycle Core

| Threat ID | Pattern | STRIDE | Standard Mitigation |
|-----------|---------|--------|---------------------|
| T-17-01 | Callback side effect fails but transition reports success | Tampering / Repudiation | Fail fast with stage, committed flag, and cause identity. [VERIFIED: .planning/phases/17-atomic-transition-lifecycle/17-CONTEXT.md:16-26] |
| T-17-02 | State/history disagree after callback failure or cancellation | Tampering | Non-awaiting commit owns both current state and record. [VERIFIED: .planning/phases/17-atomic-transition-lifecycle/17-CONTEXT.md:33-36] |
| T-17-03 | Observer error triggers recursive or duplicate notification | Denial of Service / Tampering | One non-recursive pass; isolate each observer and preserve original cause. [VERIFIED: .planning/phases/17-atomic-transition-lifecycle/17-CONTEXT.md:28-31] |
| T-17-04 | Callback exception or payload appears in result repr/error/log | Information Disclosure | `cause` direct access with `repr=False`; stage-only redacted messages; secret-sentinel tests. [ASSUMED] |
| T-17-05 | Cancellation is swallowed or later callbacks run after cancel | Denial of Service / Tampering | Finalize once, no shield, bare re-raise, assert later callbacks absent. [VERIFIED: .planning/phases/17-atomic-transition-lifecycle/17-CONTEXT.md:33-36] |
| T-17-06 | Sync/async stage drift | Tampering | One catalog and identical scenario table in pure/native contexts. [ASSUMED] |
| T-17-07 | Stale native shadow spoofs lifecycle evidence | Spoofing | Fresh export, explicit overlay, origin assertion, fresh native build. [VERIFIED: tools/phase16_isolated_verify.py:1-7,181-210] |
| T-17-08 | New hot-path allocations violate service availability/performance contract | Denial of Service | Before/intermediate/final benchmarks and compiled floor gate. [VERIFIED: .github/copilot-instructions.md:40-48] |
| T-17-09 | Reentrant/concurrent callback mutates outer operation | Tampering | Transfer explicitly to Phase 18; do not claim mitigation in Phase 17. [VERIFIED: .planning/phases/17-atomic-transition-lifecycle/17-CONTEXT.md:101-106] |
| T-17-10 | Installed artifact differs from source-tree proof | Spoofing / Tampering | Transfer explicitly to Phase 20. [VERIFIED: .planning/phases/17-atomic-transition-lifecycle/17-CONTEXT.md:101-106] |

The planner should carry this register into plan frontmatter/tasks, close T-17-01 through T-17-08 with executable evidence, and record T-17-09/T-17-10 as transfers rather than Phase 17 gaps. [ASSUMED]

## Recommended Plan Decomposition

| Order | Deliverable | Depends On | Exit Proof |
|------:|-------------|------------|------------|
| 0 | Wave 0 lifecycle scenario table, legacy contradiction inventory, result compatibility tests, and before-change pure/compiled observations | — | New failure/order tests fail for the reproduced current semantics; baseline is origin-labelled. [ASSUMED] |
| 1 | Additive result fields, stable stage catalog, redacted `TransitionError`, cause chaining, and one failure finalizer across resolution/guard/permission | 0 | LIFE-02/LIFE-04 result and observer selections pass in pure and compiled contexts. [ASSUMED] |
| 2 | Sync pre/commit/post runner, fail-fast callbacks, commit-owned history, declarative outcome integration, and legacy listener/result rewrites | 1 | Full sync matrix, history, exactly-once declarative, builder/direct-helper regressions pass. [ASSUMED] |
| 3 | Async same-slot runner and event-synchronized cancellation across pre/post commit | 2 | Identical sync/async matrix plus cancellation matrix passes in pure and compiled contexts. [ASSUMED] |
| 4 | Public docs, new append-only lifecycle ADR, SPR, maintainer docs, harness suite, intermediate/final performance proof, reviewed baseline write/check | 1-3 | Full release-quality Phase 17 gate passes and evidence is internally consistent. [ASSUMED] |

Most implementation tasks touch `core.py`; execute these waves sequentially rather than assigning concurrent edits to that file. [ASSUMED] Independent docs/test fixture preparation may run in parallel only when it does not edit the same paths. [ASSUMED]

## Sources

### Primary (HIGH confidence)

- `.planning/phases/17-atomic-transition-lifecycle/17-CONTEXT.md` — locked lifecycle, result, observer, cancellation, history, scope, and discretion decisions. [VERIFIED: .planning/phases/17-atomic-transition-lifecycle/17-CONTEXT.md]
- `.planning/REQUIREMENTS.md` — LIFE-01 through LIFE-06 acceptance requirements and Phase 18/20 boundaries. [VERIFIED: .planning/REQUIREMENTS.md]
- `src/fast_fsm/core.py` — current result, prepared dispatch, sync/async callback execution, declarative normalization, failure observer, and history implementation. [VERIFIED: src/fast_fsm/core.py]
- `.planning/phases/16-canonical-graph-dispatch-invariants/16-VERIFICATION.md` and `16-SECURITY.md` — inherited executable guarantees and accepted lifecycle risk. [VERIFIED: .planning/phases/16-canonical-graph-dispatch-invariants/16-VERIFICATION.md]
- `.specify/decisions/ADR-002-trigger-result-not-exception.md` and `ADR-003-mypyc-compilation-boundary.md` — public result and compilation decisions. [VERIFIED: .specify/decisions/ADR-002-trigger-result-not-exception.md]
- `.github/copilot-instructions.md`, `AGENTS.md`, `pyproject.toml`, `Taskfile.yml`, `setup.py` — project workflow, performance, compatibility, test, dependency, and build constraints. [VERIFIED: .github/copilot-instructions.md]
- `tests/test_advanced_functionality.py`, `tests/test_listeners.py`, `tests/test_async.py`, `tests/test_builder.py`, `tests/test_boundary_negative.py` — current expectations, inherited exactly-once coverage, and legacy contradictions. [VERIFIED: tests/test_advanced_functionality.py]
- `tools/phase16_isolated_verify.py`, `evidence/release-baseline.json` — origin-safe evidence pattern and current durable baseline. [VERIFIED: tools/phase16_isolated_verify.py]

### Secondary (MEDIUM confidence)

- `.planning/codebase/ARCHITECTURE.md`, `CONCERNS.md`, and `TESTING.md` — 2026-08-29 assessment used only to locate concerns; current source and Phase 16 verification supersede stale implementation details. [VERIFIED: .planning/codebase/ARCHITECTURE.md]

### Tertiary (LOW confidence)

- None. No external web source or training-only package claim is used. [VERIFIED: research-plan seam returned an empty fetch plan on 2026-09-01]

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new dependency; versions and boundaries were read from project configuration and probed locally. [VERIFIED: pyproject.toml:1-45]
- Architecture: HIGH — locked order/commit/cancellation decisions were checked against current source and the Phase 16 accepted-risk record. [VERIFIED: .planning/phases/17-atomic-transition-lifecycle/17-CONTEXT.md:7-44]
- Pitfalls: HIGH — the main failure modes are directly present in current callback, async-tail, history, and observer code. [VERIFIED: src/fast_fsm/core.py:1992-2808]
- Exact recommended stage strings and unexpanded force/direct-helper scope: MEDIUM — these are explicitly within discretion or not otherwise locked and are recorded in the Assumptions Log. [ASSUMED]

**Research date:** 2026-09-01
**Valid until:** 2026-10-01, or until `src/fast_fsm/core.py` lifecycle code / Phase 17 CONTEXT changes. [ASSUMED]
