# Phase 22: Ordered Runtime Selection & Lifecycle Integration - Research

**Researched:** 2026-09-06
**Domain:** Deterministic guarded-transition selection across synchronous and asynchronous FSM lifecycle boundaries
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

### Ordered eligibility and short-circuiting
- **D-01:** For a group, evaluate candidates in their already stored ascending
  numeric priority order. A candidate is eligible only when its transition
  guard, declarative guard (when applicable), and target-state permission all
  pass in that order. The first fully eligible candidate wins; later
  candidates must not be inspected after a winner. — **Reversibility:**
  costly — priority ordering and the three-stage eligibility model are the
  public semantics on which later constructors and diagnostic surfaces depend.
- **D-02:** A normal false/rejection at any eligibility stage falls through to
  the next candidate. Guard/declarative/permission exceptions terminate
  selection immediately using the established pre-commit failure-result path;
  they never fall through to a lower-priority candidate. The async path treats
  cancellation as a bare re-raise and also never evaluates a lower candidate.

### One selection before one lifecycle
- **D-03:** Resolve selection once per `trigger()` / `trigger_async()` attempt,
  before listeners, state callbacks, history, trace, or current-state
  mutation. Only the selected candidate enters the existing lifecycle, so an
  attempt has at most one lifecycle, committed history record, and
  success-observer sequence.
- **D-04:** Thread the selected candidate's priority through the existing
  internal result/history/trace path where Phase 22 owns that metadata, without
  adding a new public topology-inspection API. An exhausted group returns one
  uncommitted `selection`-stage failure and sends failure observers once; a
  missing trigger remains the distinct existing resolution failure.

### Sync/async and performance parity
- **D-05:** `can_trigger()` and `can_trigger_async()` apply the same ordered
  eligibility rules as dispatch but perform no lifecycle work or failure
  observation. Async candidates are awaited sequentially; parallel guard
  evaluation is out of scope because it would violate deterministic
  short-circuiting and user-code side-effect ordering. — **Reversibility:**
  costly — asynchronous ordering and cancellation behavior are an observable
  contract.
- **D-06:** Preserve direct O(1) singleton lookup/dispatch. Group selection is
  explicit local O(k), makes no copy or sort at dispatch time, and has an early
  performance proof separate from the existing singleton throughput floor.

### the agent's Discretion
- Private selection helper names, result-field plumbing, and exact test-file
  placement may follow existing `core.py`/mypyc conventions, provided they
  honor the fixed eligibility ordering, failure boundaries, and Phase 21 slot
  representation.

### Deferred Ideas (OUT OF SCOPE)

None — public construction/declarative/serialization parity is Phase 23;
diagnostics/output is Phase 24; installed-artifact performance proof and drone
guidance are Phase 25. Dynamic priorities, equal-priority tie-breaking, and
parallel async guard evaluation remain out of scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SEL-01 | A synchronous machine selects the first candidate that passes its transition guard, declarative guard, and target-state permission in ascending priority order. | Reuse the immutable, registration-sorted `_TransitionGroup.entries`; evaluate each `TransitionEntry` through the existing three eligibility seams and stop at the first winner. |
| SEL-02 | An asynchronous machine applies the same ordered semantics by awaiting candidates sequentially; ordinary rejection falls through while exceptions and cancellation fail closed. | Mirror the sync selector with one awaited stage at a time; preserve the existing outer `CancelledError` finalizer and never create parallel tasks. |
| SEL-03 | Candidate selection completes before lifecycle callbacks; exactly one selected candidate can enter lifecycle work, history, and success observers. | Return one prepared winner containing the exact entry and target-specific declarative handler, then pass that value once into the existing lifecycle runner. |
| SEL-04 | Group exhaustion returns one truthful, uncommitted selection failure and notifies failure observers once, while missing-trigger resolution failures retain their existing meaning. | Keep lookup failure separate from group exhaustion, and centralize observer notification in the existing `_finalize_failure()` boundary. |
</phase_requirements>

## Summary

Phase 21 already supplies the right runtime input: each `(source, trigger)` slot is either one direct `TransitionEntry` or a frozen tuple-backed `_TransitionGroup`, and group construction sorts once by ascending priority. The Phase 22 implementation should preserve a literal singleton branch and add a local group scan which evaluates transition guard, target-specific declarative guard, and target-state permission in that order. The first fully eligible entry becomes one prepared dispatch; a normal rejection advances only within a group, while exceptions and cancellation terminate the attempt. [VERIFIED: src/fast_fsm/core.py:579-606,1472-1496]

Selection must be a pre-lifecycle operation, not a loop around the lifecycle. The existing commit helper creates at most one history record immediately before changing current state, and the existing failure finalizer snapshots and invokes failure observers once. Feeding those seams one selected candidate preserves the established lifecycle, ownership, listener, history, and cancellation contracts with much less risk than duplicating them inside candidate iteration. [VERIFIED: src/fast_fsm/core.py:2671-2757,2759-2963,3092-3298,3935-4135]

The highest-risk details are metadata and hot-path shape. Add `selection` to the stable lifecycle-stage catalog; carry the selected/evaluated candidate priority through result/history/trace without adding topology inspection; do not smuggle it through public `**kwargs`; and prove that singleton lookup remains direct while group work is proportional only to the winning rank or group length. The current mypyc structural tests explicitly guard slotted field layouts, so every added runtime field needs a deliberate test update. [VERIFIED: src/fast_fsm/core.py:77-142,518-606,670-680; tests/test_mypyc_guard.py:1390-1429]

**Primary recommendation:** Implement paired private sync/async selection helpers that consume a captured source plus direct slot, return exactly one `_PreparedDispatch` or terminal failure, and let only that prepared winner enter the existing lifecycle.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Slot lookup and singleton/group branching | Core runtime resolution | Phase 21 topology storage | Runtime consumes the already-published slot without altering registration. |
| Ordered eligibility | Core runtime selection | Existing condition/declarative/state policy seams | Selection orchestrates existing checks; it does not redefine their semantics. |
| Lifecycle, history, and observers | Existing lifecycle runner | Selection metadata plumbing | Lifecycle accepts one winner; selection never invokes callbacks or commits state. |
| Async ordering and cancellation | Async runtime boundary | Existing ownership/failure finalizer | One candidate stage is awaited at a time; cancellation is finalized and re-raised at the owned public boundary. |
| Result/history/trace priority metadata | Existing public runtime records | Logging redaction | Runtime records the selected candidate without exposing graph topology. |
| Performance proof | Tests and benchmark harness | mypyc structural guard | Tests protect dictionary operation count, no runtime sorting, slots, and compiled behavior. |

## Project Constraints (from AGENTS.md and Copilot Instructions)

- Use `uv` for every Python, test, build, and dependency command; direct `python`, `pip`, and `python -m pytest` are forbidden. [VERIFIED: .github/copilot-instructions.md:32-39]
- Hot-path production classes must use `__slots__`; `core.py` remains the sole selectively compiled module and `conditions.py` stays interpreted to preserve Python subclassing. [VERIFIED: .github/copilot-instructions.md:40-53; .specify/memory/spr-core-api.md:39]
- The compiled `trigger()` floor is at least 200,000 operations/second, while source/trigger lookup and singleton dispatch remain O(1); group construction and selection are local O(k), with no unrelated topology scan or dispatch-time sort. [VERIFIED: .github/copilot-instructions.md:40-53; .specify/decisions/ADR-007-priority-topology.md:42-50]
- Conditions and callbacks continue accepting `*args, **kwargs`; constructor behavior and existing public symbols cannot be silently broken. [VERIFIED: .github/copilot-instructions.md:55-59]
- Tests run sequentially; use targeted tests while implementing and the full suite once at the phase gate. Mypy is blocking for mypyc compatibility and ty remains advisory. [VERIFIED: .github/copilot-instructions.md:60-67,211-220]
- Public API changes require documentation updates. Stage/result/history/trace metadata are public runtime surfaces even though topology inspection remains deferred. [VERIFIED: .github/copilot-instructions.md:109-118; src/fast_fsm/__init__.py:7-32,67-99]
- Stage and commit only explicit task paths in a dirty worktree; never use `git add .` or `git add -A`. [VERIFIED: .github/copilot-instructions.md:115-118]
- Use `bd` for issue tracking and do not create a parallel Markdown task system. [VERIFIED: AGENTS.md:12-61; .github/copilot-instructions.md:137-181]

## Standard Stack

### Core

| Library/tool | Verified version | Purpose | Why standard here |
|--------------|------------------|---------|-------------------|
| Python | 3.12.10 | Runtime and async semantics | Project interpreter resolved by the locked `uv` environment. [VERIFIED: local `uv run --offline python --version`, 2026-09-06] |
| Fast FSM core | in-repo | Slot lookup, selection, lifecycle, ownership, history, and trace | The phase is an internal extension of the existing core; no third-party selector is appropriate. [VERIFIED: src/fast_fsm/core.py:77-142,518-680,2063-2271,2671-3298,3882-4135] |
| Fast FSM conditions | in-repo | Sync/awaitable guard contracts | Existing `Condition`, `FuncCondition`, and async evaluation seams already cover candidate guard execution. The public aliases are exactly `GuardResult = bool | Awaitable[bool]` and `GuardCallable = Callable[..., GuardResult]`. [VERIFIED: src/fast_fsm/conditions.py:28-33,205-335] |
| pytest | 8.4.1 | Unit/integration contract tests | Existing suite and fixtures cover lifecycle, async, logging, mypyc structure, and performance. [VERIFIED: local `uv run --offline pytest --version`, 2026-09-06] |
| mypy/mypyc | 1.17.1 | Static and compiled-boundary validation | Core compilation and slot-shape guards are existing release requirements. [VERIFIED: local `uv run --offline mypy --version` and `mypyc --version`, 2026-09-06] |

### Supporting

| Tool | Verified version | Purpose | When to use |
|------|------------------|---------|-------------|
| pytest-asyncio | 1.3.0 | Deterministic async guard/cancellation tests | Use event handshakes to prove sequential awaits and cancellation boundaries. [VERIFIED: local package metadata, 2026-09-06; tests/test_transition_lifecycle.py:925-1033] |
| Ruff | 0.12.11 | Formatting and lint validation | Run on changed Python files before type checks. [VERIFIED: local `uv run --offline ruff --version`, 2026-09-06] |
| Task | 3.53.1 | Repository quality-gate orchestration | Use `task typecheck-mypy` as blocking and retain ty output independently. [VERIFIED: local `task --version`, 2026-09-06; .github/copilot-instructions.md:100-108] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Direct tuple iteration | Copy or sort candidates at dispatch | Rejected by D-06 and ADR-007; it adds allocation/work to every grouped attempt. |
| Paired sequential selectors | A single polymorphic generator/awaitable pipeline | Avoid: generator/coroutine abstraction adds hot-path allocation and obscures mypyc narrowing and cancellation stages. |
| One prepared winner | Re-run eligibility inside lifecycle | Avoid: duplicates user-code side effects and permits state-dependent disagreement between selection and commit. |
| Outer cancellation finalizer | Catch `CancelledError` per candidate | Avoid: risks treating cancellation as rejection or observing it multiple times. |

**Installation:** No new package is required or permitted for this phase. [VERIFIED: .specify/decisions/ADR-007-priority-topology.md:9-16]

## Package Legitimacy Audit

Not applicable: Phase 22 installs no external package.

## Architecture Patterns

### System Architecture Diagram

```text
trigger / trigger_async / can_trigger / can_trigger_async
                         |
             capture source + direct slot lookup
                         |
                  +------v-------+
                  | slot missing? |---- yes ----> resolution failure / False
                  +------+-------+
                         | no
              +----------v-----------+
              | singleton or group?  |
              +-----+-----------+----+
                    |           |
            singleton direct    group tuple, ascending priority
                    |           |
                    +-----+-----+
                          v
       transition guard -> declarative guard -> target permission
             | false             | exception/cancellation
             v                   v
       next group candidate   terminal failure / bare cancellation
             |
       first full pass
             v
     one prepared winner (entry + source + handler + sanitized guard context)
             |
             +---- can_trigger* ----> True, no lifecycle/observer work
             |
             +---- trigger* --------> existing single lifecycle
                                      -> at most one commit/history record
                                      -> one success or failure observation
```

### Recommended Project Structure

```text
src/fast_fsm/
├── core.py                    # selection, lifecycle, metadata, ownership; sole mypyc unit
└── conditions.py              # unchanged interpreted condition strategies
tests/
├── test_priority_selection.py # new focused sync/async ordered-selection contract
├── test_transition_lifecycle.py
├── test_async.py
├── test_logging_config.py
├── test_mypyc_guard.py
└── test_performance_benchmarks.py
```

The Phase 22 context names `tests/test_lifecycle_results.py`, but that path does not exist; the current lifecycle contract is in `tests/test_transition_lifecycle.py`. [VERIFIED: repository file inventory and tests/test_transition_lifecycle.py:1-22]

### Pattern 1: Direct singleton branch, local group scan

**What:** Perform the two dictionary lookups once. Keep the singleton slot as a direct `TransitionEntry`; only an actual `_TransitionGroup` enters tuple iteration. The group tuple is already ascending by priority because registration publishes `tuple(sorted(..., key=lambda entry: entry.priority))`. [VERIFIED: src/fast_fsm/core.py:838-840,1472-1496,2102-2153]

**When to use:** Every sync and async eligibility query.

**Implementation guidance:**

```python
# Illustrative private shape; exact helper names are agent discretion.
slot = source_slots.get(trigger) if source_slots is not None else None
if isinstance(slot, TransitionEntry):
    return evaluate_single_candidate(slot, singleton_semantics=True)
for entry in slot.entries:
    outcome = evaluate_single_candidate(entry, singleton_semantics=False)
    if outcome.is_terminal or outcome.is_selected:
        return outcome
return selection_exhausted()
```

Do not normalize the singleton to a one-element tuple, call `sorted()`, or build a list/generator. D-06's “makes no copy” applies to the candidate container; the existing fresh sanitized keyword mapping for guarded calls remains a required safety boundary. `_sanitize_condition_kwargs` copies only bounded safe keys and retains value identity. [VERIFIED: .planning/phases/22-ordered-runtime-selection-lifecycle-integration/22-CONTEXT.md:48-52; src/fast_fsm/core.py:2102-2153; .specify/memory/spr-core-api.md:40]

### Pattern 2: Three-stage candidate evaluation with a terminal outcome

**What:** For each candidate, evaluate exactly: transition condition, target-specific declarative condition, then current-state permission. A false result is “continue” only when scanning a group. An ordinary exception is a terminal pre-commit result carrying the existing stage/cause. [VERIFIED: src/fast_fsm/core.py:2063-2100,2155-2271,3092-3298,3882-4135]

**When to use:** Selection for `trigger*` and eligibility for `can_trigger*`.

The existing declarative resolver accepts `source_state`, `trigger`, and optional `target_state`, and filters both endpoint metadata before returning a handler; selection must resolve it per candidate and retain the winner's exact handler. [VERIFIED: src/fast_fsm/core.py:4178-4199]

For `can_trigger*`, share the order and short-circuit semantics but preserve its observer-free contract. Existing `can_trigger()` and `can_trigger_async()` simply return false for preparation/rejection and do not call `_finalize_failure()`. Transition/state-policy exceptions currently propagate; the base declarative evaluator returns false unless its trigger path explicitly requests `raise_on_error=True`. [VERIFIED: src/fast_fsm/core.py:2063-2100,2155-2271,3882-3908; tests/test_async.py:571-611,1205-1301]

### Pattern 3: Select once, execute once

**What:** Extend the private prepared-dispatch value so it is a complete handoff to lifecycle: exact `TransitionEntry`, captured source identity/name, trigger and arguments, optional bounded condition kwargs, and exact target-specific declarative handler. `_PreparedDispatch` currently has the verbatim fields `“entry”, “current_name”, “trigger”, “args”, “condition_kwargs”, “declarative_handler”`. [VERIFIED: src/fast_fsm/core.py:670-680]

**When to use:** After candidate eligibility succeeds and before any callback, listener, trace result, history append, or state mutation.

Pass the prepared selection as an internal positional object or another collision-proof typed value. Do not add an internal `priority=` keyword beside application `**kwargs`: a caller is already allowed to supply arbitrary callback/condition keywords, including `priority`, and an internal keyword collision would become a behavior regression. [VERIFIED: .github/copilot-instructions.md:55-58; src/fast_fsm/core.py:3289-3295,4112-4120]

The lifecycle runner must not re-evaluate guards or re-resolve declarative metadata. `_commit_transition()` already constructs the optional record before appending it and only then changes current state, providing the one-commit boundary. [VERIFIED: src/fast_fsm/core.py:2671-2684]

### Pattern 4: Sequential async mirror with one outer cancellation boundary

**What:** Await candidate stage 1, then 2, then 3; only after a false result advance to the next tuple entry. Never create tasks or use `gather()`. Let `asyncio.CancelledError` leave the candidate helper and reach the existing owned trigger boundary, which finalizes one cancellation result and uses a bare `raise`. [VERIFIED: src/fast_fsm/core.py:2478-2490,3935-4135]

**When to use:** `can_trigger_async()` and `trigger_async()`.

The trigger path's outer stage tracker must identify the candidate stage active at cancellation; lower candidates remain untouched. For `can_trigger_async()`, cancellation should propagate without failure observation because that method currently binds/checks the loop, evaluates eligibility, and returns a boolean without acquiring trigger ownership or calling the failure finalizer. [VERIFIED: src/fast_fsm/core.py:3421-3571,3882-3908,3935-4135]

Capture the source state and slot before awaiting and carry that captured source through all candidate permission checks. The frozen group tuple gives a stable local candidate set without claiming that `can_trigger_async()` has the trigger writer's cross-field ownership guarantee. [VERIFIED: src/fast_fsm/core.py:599-606,3421-3571]

### Pattern 5: Explicit runtime metadata semantics

**What:** Add nullable priority to the existing runtime records, preserving legacy positional/equality behavior where applicable:

- `TransitionResult` currently exposes verbatim `“success”, “from_state”, “to_state”, “trigger”, “error”, “committed”, “stage”, “cause”`; append `priority: Optional[int] = field(default=None, compare=False)`. [VERIFIED: src/fast_fsm/core.py:518-552]
- `TransitionRecord` currently has verbatim slots `“from_state”, “trigger”, “to_state”, “timestamp”`; append a priority slot and constructor argument used by the single commit helper. [VERIFIED: src/fast_fsm/core.py:555-576]
- `FSMTraceEvent` currently has verbatim fields `“operation”, “stage”, “result”, “trigger”, “source_state”, “destination_state”, “positional_args”, “keyword_args”, “error”`; append nullable priority and expose only a scalar `trace_priority` on the default path/allowed redactor output. [VERIFIED: src/fast_fsm/core.py:118-142,247-303]

Recommended meaning:

| Outcome | `priority` |
|---------|------------|
| Selected candidate lifecycle success or failure | selected entry priority |
| Candidate guard/declarative/permission exception | evaluated candidate priority |
| Terminal singleton rejection | singleton entry priority |
| Group exhaustion | `None` — no candidate selected |
| Missing trigger | `None` — no candidate resolved |

This preserves auditability without presenting a public topology enumeration. Phase 23 must extend all construction/query/serialization paths consistently; it should not be required to retrofit the Phase 22 runtime truth. [VERIFIED: .planning/phases/22-ordered-runtime-selection-lifecycle-integration/22-CONTEXT.md:35-44,64-67]

### Anti-Patterns to Avoid

- **Looping the lifecycle:** A rejected or failed selected lifecycle must never fall back to another candidate; only pre-lifecycle ordinary eligibility rejection can continue.
- **Failure observation per rejected candidate:** Rejection is local scan control, not a public failed attempt. Observe only the final exhausted/exception/lifecycle failure.
- **Using `_require_singleton_entry()` for runtime:** It intentionally rejects groups for projections. Runtime must branch on `_TransitionSlot`; projections keep failing closed until Phase 23. [VERIFIED: src/fast_fsm/core.py:607-617; tests/test_graph_invariants.py:299-315]
- **Re-reading `_current_state` after awaits:** It can mix a captured slot with a later source object in the observer-free async query. Carry the source used for lookup.
- **Catching `BaseException`:** Existing failure observers isolate their own `BaseException`, but candidate evaluation should catch ordinary `Exception`; cancellation must remain the special bare re-raise path. [VERIFIED: src/fast_fsm/core.py:2727-2757,4124-4135]
- **Tracing every candidate:** Emit one attempt result, not condition payloads, object reprs, or one log record per rejection. The default trace guard precedes event allocation and maps only bounded metadata. [VERIFIED: src/fast_fsm/core.py:247-303]

## Don't Hand-Roll

| Problem | Don't build | Use instead | Why |
|---------|-------------|-------------|-----|
| Guard invocation | New callable classification/reflection | `_evaluate_condition_sync()` / `_evaluate_condition_async()` | Existing evaluators cover wrapper graphs, awaitable policy, cycles, and interpreted subclass boundaries. [VERIFIED: src/fast_fsm/core.py:2386-2490; src/fast_fsm/conditions.py:205-335] |
| Declarative filtering | Trigger-only handler lookup | `_resolve_declarative_handler(source, trigger, target)` | It already applies canonical source and target metadata. [VERIFIED: src/fast_fsm/core.py:4178-4199] |
| Failure dispatch | Per-candidate observer loops | `_build_failure_result()` then `_finalize_failure()` once | Existing finalizer snapshots observers and isolates observer faults. [VERIFIED: src/fast_fsm/core.py:2686-2757] |
| State/history mutation | Candidate-specific commit logic | `_commit_transition()` | Existing helper creates one record and owns the mutation order. [VERIFIED: src/fast_fsm/core.py:2671-2684] |
| Async cancellation protocol | Shielding, compensation, or task fan-out | Existing owned trigger cancellation boundary | It records the reached stage/commit state, finalizes once, releases ownership in `finally`, and bare re-raises. [VERIFIED: src/fast_fsm/core.py:3935-4135] |
| Candidate ordering | Heap, ordered map, runtime sort | Frozen registration-sorted tuple | Groups are finite and already ordered. [VERIFIED: src/fast_fsm/core.py:599-606,1472-1496] |

**Key insight:** Phase 22 is orchestration over established seams, not a second condition engine or lifecycle implementation.

## Common Pitfalls

### Pitfall 1: Treating every false as group fallthrough

**What goes wrong:** A singleton's existing false result silently changes stage/diagnostic meaning, or a lifecycle failure incorrectly activates a lower-priority edge.

**Why it happens:** “Try next candidate” is implemented as a general transition retry instead of a group-only eligibility outcome.

**How to avoid:** Preserve the direct singleton contract and represent group rejection separately from terminal failure and selected success.

**Warning signs:** A singleton false returns `selection`; a lower guard runs after a winner's callback fails; more than one failure observer call occurs.

### Pitfall 2: Declarative handler identity is resolved too late

**What goes wrong:** Selection checks one candidate but lifecycle invokes a handler resolved from another target or overwrites singular trigger metadata.

**Why it happens:** Current declarative storage is singular per trigger and broader declarative parity is deliberately Phase 23.

**How to avoid:** Resolve target-specific metadata while evaluating each candidate and retain the winner's exact handler in the prepared dispatch. Do not redesign decorator storage here.

**Warning signs:** Handler lookup occurs inside lifecycle after the candidate loop, or Phase 22 edits public decorator signatures.

### Pitfall 3: Async false/exception/cancellation collapse into one branch

**What goes wrong:** Exceptions fall through, cancellation selects a lower edge, or cancellation is wrapped instead of re-raised identically.

**Why it happens:** A broad exception handler surrounds the scan.

**How to avoid:** Model ordinary false as scan control, ordinary `Exception` as terminal failure, and let cancellation reach the existing outer bare re-raise boundary.

**Warning signs:** `except BaseException`, `asyncio.gather`, a lower-candidate event after cancellation, or a cancellation returned as a normal `TransitionResult`.

### Pitfall 4: Priority metadata collides with application kwargs

**What goes wrong:** A valid `trigger(..., priority=...)` payload raises a duplicate-keyword error or stops reaching callbacks unchanged.

**Why it happens:** Internal metadata is passed as a named keyword beside `**kwargs`.

**How to avoid:** Carry priority on a private slotted prepared selection or as a collision-proof positional internal parameter.

**Warning signs:** Lifecycle calls contain both `priority=entry.priority` and `**kwargs`.

### Pitfall 5: Structural mypyc regressions hide behind pure-Python tests

**What goes wrong:** New union outcomes, dataclass fields, or generator abstractions pass normal tests but fail compiled import/build or weaken slots.

**Why it happens:** `core.py` is selectively compiled and tests assert exact dataclass/slot structure.

**How to avoid:** Keep outcome values explicit and slotted, extend AST expectations deliberately, typecheck early, and run a targeted compiled behavior test before broad integration.

**Warning signs:** implicit union narrowing, dynamic attributes, iterator-heavy helpers, or an unchanged exact-field assertion after adding priority.

### Pitfall 6: Runtime changes accidentally unlock Phase 23 projections

**What goes wrong:** `to_dict`, graph snapshots, `transition_exists(..., to_state=...)`, or other consumers silently flatten a group.

**Why it happens:** `_require_singleton_entry()` is globally relaxed to make dispatch work.

**How to avoid:** Add runtime selection beside the projection guard. Replace only the current grouped-runtime fail-closed expectation; keep projection failure coverage.

**Warning signs:** The fixed projection error disappears or graph output chooses one candidate.

## Code Examples

The examples below are implementation skeletons derived from the verified in-repo seams; private helper names are illustrative.

### Sync selection outcome feeding one lifecycle

```python
prepared = self._select_transition_sync(trigger, args, kwargs)
if isinstance(prepared, TransitionResult):
    return self._finalize_failure(prepared, kwargs)

# Eligibility is complete. This is the only transition allowed into lifecycle.
result = self._execute_prepared_transition(prepared, kwargs)
if not result.success:
    return self._finalize_failure(result, kwargs)
return result
```

This preserves the current terminal finalization pattern around `_execute_transition()`. [VERIFIED: src/fast_fsm/core.py:3092-3298]

### Async ordered evaluation without task fan-out

```python
for entry in group.entries:
    transition_ok = await self._evaluate_condition_async_for_entry(entry, context)
    if not transition_ok:
        continue
    declarative_ok = await self._evaluate_declarative_condition_async_for_entry(
        entry, context
    )
    if not declarative_ok:
        continue
    permission_ok = await self._evaluate_permission_async_for_entry(entry, context)
    if not permission_ok:
        continue
    return prepared_winner(entry, context)
return selection_exhausted(context)
```

The actual implementation should reuse the current condition/declarative/permission methods rather than create the illustrative wrappers shown here. Existing async evaluation awaits the effective condition result, and current trigger cancellation is finalized then bare re-raised. [VERIFIED: src/fast_fsm/core.py:2478-2490,3882-4135]

### One failure finalization for exhaustion

```python
return self._finalize_failure(
    self._build_failure_result(
        source.name,
        trigger,
        GROUP_EXHAUSTED_ERROR,
        stage=_LIFECYCLE_STAGE_SELECTION,
    ),
    kwargs,
)
```

The exact new fixed error wording is implementation discretion; it must remain redacted, stable in tests, `committed=False`, `to_state=None`, `cause=None`, and `priority=None`.

## State of the Art

| Previous repository state | Phase 22 target | Impact |
|---------------------------|-----------------|--------|
| One direct `TransitionEntry` per source/trigger slot | Direct singleton or immutable ordered group (Phase 21) | Topology can retain finite conflicts without penalizing singleton storage. [VERIFIED: src/fast_fsm/core.py:579-606] |
| Grouped runtime dispatch returns fixed resolution failure | Runtime scans the stored group with deterministic eligibility | External telemetry dispatch logic is no longer needed for simple ordered guarded conflicts. [VERIFIED: src/fast_fsm/core.py:607-617,2102-2153; tests/test_graph_invariants.py:299-315] |
| Eligibility and lifecycle are interleaved for the resolved singleton | Selection completes before one lifecycle | Rejected candidates have no callback/history/observer side effects. [VERIFIED: src/fast_fsm/core.py:3092-3298,3966-4135] |
| Trace/result/history do not carry priority | Selected runtime edge carries nullable priority | Failures and committed history identify the chosen/evaluated candidate without graph inspection. [VERIFIED: src/fast_fsm/core.py:123-142,518-576] |

**Deprecated/outdated for this phase:** `_PRIORITY_GROUP_RUNTIME_ERROR = "Priority candidate resolution is not available"` is removed from runtime dispatch once ordered selection lands; `_PRIORITY_GROUP_PROJECTION_ERROR = "Priority candidate groups are not supported by this projection"` remains until Phase 23. [VERIFIED: src/fast_fsm/core.py:607-617]

## Assumptions Log

| # | Claim | Section | Risk if wrong |
|---|-------|---------|---------------|
| A1 | Private helper and outcome names in code skeletons are illustrative. [ASSUMED] | Architecture Patterns / Code Examples | None to public behavior; planner may choose mypyc-friendlier names/shapes. |
| A2 | Exact fixed text for the new group-exhaustion error is not locked. [ASSUMED] | Code Examples | Tests and docs must agree on the chosen redacted wording. |

## Open Questions

1. **Which private result shape best satisfies mypyc?**
   - What we know: hot-path values must be slotted, and `_PreparedDispatch` already provides a frozen slotted handoff. [VERIFIED: src/fast_fsm/core.py:670-680; .github/copilot-instructions.md:40-53]
   - What's unclear: whether extending `_PreparedDispatch` alone or adding one small slotted terminal-outcome type produces the clearest mypy narrowing.
   - Recommendation: extend `_PreparedDispatch` with captured source/priority context and use `TransitionResult` for terminal failure unless typecheck evidence requires a dedicated private outcome.

2. **What fixed error string should group exhaustion expose?**
   - What we know: D-04 locks stage `selection`, one uncommitted failure, and one observer notification, but not the text.
   - What's unclear: exact redacted phrasing.
   - Recommendation: choose one concise fixed string in core and assert it without embedding candidate count, priorities, state names beyond the existing result fields, or condition representations.

There is no planning blocker; both questions are explicitly within agent discretion.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| uv | All Python/test/build commands | Yes | 0.12.9 | None; required by project policy. |
| Python | Runtime/tests | Yes | 3.12.10 | Project locked environment. |
| pytest | Contract tests | Yes | 8.4.1 | None needed. |
| pytest-asyncio | Async/cancellation tests | Yes | 1.3.0 | None needed. |
| Ruff | Format/lint | Yes | 0.12.11 | None needed. |
| mypy/mypyc | Type/compiled checks | Yes | 1.17.1 | None needed. |
| Task | Quality gates | Yes | 3.53.1 | Invoke individual `uv` commands only if task orchestration itself fails. |
| Apple clang | Native extension build | Yes | 21.0.0 | Pure-source tests remain available, but compiled proof requires the compiler. |
| git | Atomic phase commits | Yes | 2.55.0 | None needed. |
| bd | Project issue tracking | Yes | 1.0.4 | Local planning can continue if its Dolt service is unavailable; do not invent Markdown tracking. |

The default user uv cache is sandbox-restricted in this worktree; `UV_CACHE_DIR=/tmp/fast-fsm-phase22-uv-cache uv run --offline ...` successfully uses the locked environment. This is an execution-environment fallback, not a project dependency gap. [VERIFIED: local commands, 2026-09-06]

**Missing dependencies with no fallback:** None.

**Missing dependencies with fallback:** None.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.4.1 + pytest-asyncio 1.3.0 |
| Config file | `pyproject.toml` |
| Quick run command | `UV_CACHE_DIR=/tmp/fast-fsm-phase22-uv-cache FAST_FSM_BUILD_MODE=pure uv run --offline pytest tests/test_priority_selection.py tests/test_transition_lifecycle.py tests/test_async.py -x -q` |
| Full suite command | `UV_CACHE_DIR=/tmp/fast-fsm-phase22-uv-cache FAST_FSM_BUILD_MODE=pure uv run --offline pytest tests/ -x -q` |

The existing focused baseline spanning grouped fail-closed behavior, lifecycle failure finalization, and effective async condition subclass policy passes: 9 tests passed. [VERIFIED: local targeted pytest run, 2026-09-06]

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated command | File exists? |
|--------|----------|-----------|-------------------|--------------|
| SEL-01 | Sync ascending scan; strict three-stage eligibility; first winner; later candidates untouched | Unit/integration | `uv run pytest tests/test_priority_selection.py -k 'sync' -x -q` | No — Wave 0 |
| SEL-02 | Async sequential awaits; false fallthrough; exception/cancellation terminal | Async integration | `uv run pytest tests/test_priority_selection.py -k 'async' -x -q` | No — Wave 0 |
| SEL-03 | Selection precedes callbacks; one lifecycle/history/success sequence; lifecycle failure never falls back | Integration | `uv run pytest tests/test_transition_lifecycle.py -k 'priority or selection' -x -q` | Existing file, new cases needed |
| SEL-04 | Exhaustion yields one selection failure/observer; missing trigger and singleton stages remain distinct | Unit/integration | `uv run pytest tests/test_priority_selection.py -k 'exhaust or missing or singleton' -x -q` | No — Wave 0 |

### Required Test Matrix

- **Ordered sync:** register priorities out of order; reject separately at transition guard, declarative guard, and target permission; select the first fully passing candidate; assert later side-effect counters stay zero.
- **Terminal sync exceptions:** raise at each eligibility stage; assert lower candidates untouched, `committed=False`, exact stage/cause, unchanged state/history, and one failure observer.
- **Exhaustion vs missing:** all candidates false produces one `selection` failure with no target/priority; an absent trigger remains `resolution`; singleton false retains its established `guard` or `state-permission` meaning.
- **Observer-free queries:** `can_trigger()` and `can_trigger_async()` use identical order but perform no callbacks, history, success/failure observation, or state mutation; preserve established exception behavior.
- **Ordered async:** record start/end events and an active-count maximum of one; no sleeps are needed. Event-gate the active candidate, cancel it, assert lower candidate untouched and identical cancellation re-raised; trigger observers run once, can-query observers never run.
- **Lifecycle boundary:** one event ledger proves every candidate eligibility event precedes `before_transition`, source exit, listeners, commit, destination enter, declarative handler, trigger callbacks, and after listeners. A failure after selection never evaluates another candidate.
- **Metadata:** verify priority on success, candidate exception, committed post-callback failure, history, default trace, and redactor event; verify `None` for missing/exhaustion. Ensure callback application kwargs are unchanged.
- **Performance/structure:** preserve the current singleton `<= 2` counted dict operations; add a group call-count proof proportional to winner rank and independent of unrelated topology; AST-guard absence of dispatch-time `sorted`; update exact slot/dataclass tests; run a targeted compiled selection test.
- **Projection boundary:** split the Phase 21 grouped-consumer test so runtime now selects while `to_dict`/projection still fails closed. [VERIFIED: tests/test_graph_invariants.py:299-315]

Existing async lifecycle cancellation tests use event handshakes and assert source-side versus committed destination-side behavior; extend that pattern rather than time-based sleeps. [VERIFIED: tests/test_transition_lifecycle.py:925-1033]

### Sampling Rate

- **Per task commit:** focused file/test node in under 30 seconds.
- **After selection seam changes:** sync + async selection files, then `task typecheck-mypy` and advisory `task typecheck-ty`.
- **After runtime metadata changes:** logging, lifecycle, mypyc guard, and performance test files together.
- **Phase gate:** pure full suite; compiled build/import and targeted behavior; slots-policy audit; singleton/group performance proof.

### Wave 0 Gaps

- Create `tests/test_priority_selection.py` for the dedicated ordered-resolution matrix.
- Add Phase 22 cases to `tests/test_transition_lifecycle.py`, `tests/test_async.py`, `tests/test_logging_config.py`, `tests/test_mypyc_guard.py`, and `tests/test_performance_benchmarks.py`.
- Correct the stale context reference from nonexistent `tests/test_lifecycle_results.py` to the actual lifecycle test module in plan task paths; the context decision itself does not need rewriting.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard control |
|---------------|---------|------------------|
| V2 Authentication | No | Library has no authentication boundary in this phase. |
| V3 Session Management | No | Async ownership is concurrency control, not an application session. |
| V4 Access Control | No | State permission is domain transition policy, not user authorization. |
| V5 Input Validation | Yes | Reuse normalized canonical topology and bounded sanitized condition kwargs; never log payload values. [VERIFIED: src/fast_fsm/core.py:620-624,2102-2153; .specify/memory/spr-core-api.md:40] |
| V6 Cryptography | No | No cryptographic operation or secret storage is introduced. |

### Known Threat Patterns for the Python FSM Runtime

| Pattern | STRIDE | Standard mitigation |
|---------|--------|---------------------|
| User condition/callback payload leaks through trace | Information Disclosure | Keep default trace metadata-only, preserve disabled guard before allocation, allow only bounded scalar redactor output, and never render condition/error reprs. [VERIFIED: src/fast_fsm/core.py:114-142,247-303] |
| Malicious/buggy guard mutates shared kwargs | Tampering | Reuse the existing fresh sanitized guard mapping per attempt; pass application kwargs unchanged to lifecycle callbacks. [VERIFIED: src/fast_fsm/core.py:2102-2153; .specify/memory/spr-core-api.md:40] |
| Parallel async evaluation reorders side effects | Tampering | Await one candidate and stage at a time; never fan out tasks. |
| Observer exception hides original selection failure | Repudiation | `_finalize_failure()` isolates observer exceptions and retains the original truthful result. [VERIFIED: src/fast_fsm/core.py:2727-2757] |
| Unbounded group work scans unrelated topology | Denial of Service | Iterate only the immutable local tuple, short-circuit on the winner, and retain direct singleton dispatch. [VERIFIED: .specify/decisions/ADR-007-priority-topology.md:42-45] |

Security enforcement is enabled because `.planning/config.json` does not set `security_enforcement` to false. [VERIFIED: .planning/config.json:1-29] The phase adds no network, persistence, authentication, session, cryptographic, or external-input parser boundary. [VERIFIED: .planning/phases/22-ordered-runtime-selection-lifecycle-integration/22-CONTEXT.md:5-14]

## Phase Exclusions

Do not include any of the following in Phase 22 plans:

- Public constructor/factory/builder/decorator/deserialization parity, multi-handler declarative storage, clone/query/serialization topology parity — Phase 23.
- Diagnostics, validators, graph output, logging presentation beyond the priority metadata needed on the existing trace path — Phase 24.
- Installed-artifact throughput oracle, broader release evidence, benchmark claims, drone example/controller guidance — Phase 25.
- Dynamic priorities, equal-priority tie-breaking, parallel async guards, rollback/compensation, topology scans, or a new public inspection API.

These exclusions are locked by Phase 22 context and ADR-007. [VERIFIED: .planning/phases/22-ordered-runtime-selection-lifecycle-integration/22-CONTEXT.md:152-158; .specify/decisions/ADR-007-priority-topology.md:46-50]

## Sources

### Primary (HIGH confidence)

- `.planning/phases/22-ordered-runtime-selection-lifecycle-integration/22-CONTEXT.md` — locked semantics, discretion, exclusions.
- `.planning/ROADMAP.md` and `.planning/REQUIREMENTS.md` — Phase 22 goal, success criteria, SEL-01 through SEL-04.
- `.planning/phases/21-priority-contract-atomic-registration/21-CONTEXT.md`, `21-RESEARCH.md`, `21-VERIFICATION.md`, `21-01-SUMMARY.md`, and `21-02-SUMMARY.md` — verified input topology and deliberate grouped-runtime fail-closed boundary.
- `.specify/decisions/ADR-007-priority-topology.md` — accepted representation, complexity, and phase boundaries.
- `.specify/memory/constitution.md` and `.specify/memory/spr-core-api.md` — performance, slots, mypyc, lifecycle, logging, and compatibility contracts.
- `src/fast_fsm/core.py` and `src/fast_fsm/conditions.py` — current runtime source of truth.
- `tests/test_graph_invariants.py`, `tests/test_transition_lifecycle.py`, `tests/test_async.py`, `tests/test_logging_config.py`, `tests/test_mypyc_guard.py`, and `tests/test_performance_benchmarks.py` — current executable contracts and extension seams.
- `.github/copilot-instructions.md` and `AGENTS.md` — project workflow and quality constraints.

### Secondary (MEDIUM confidence)

- None; no web or secondary source was required.

### Tertiary (LOW confidence)

- Only the two explicitly logged implementation-discretion assumptions.

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — versions and commands were verified in the locked local environment; no package is added.
- Architecture: HIGH — based on current core source, accepted ADR-007, Phase 21 verification, and locked Phase 22 decisions.
- Failure/cancellation semantics: HIGH — traced through sync/async implementations and executable lifecycle/async tests.
- Performance/mypyc hazards: HIGH — grounded in repository constraints, AST tests, counted-lookup tests, and the sole compiled-unit contract.
- Exact private helper shape/error wording: LOW — deliberately left to agent discretion and logged as assumptions.

**Research date:** 2026-09-06
**Valid until:** 2026-10-06 (stable in-repository architecture; re-check if Phase 21/22 source changes)

## RESEARCH COMPLETE

Phase 22 can be planned as a focused runtime integration: dedicated selection tests first, paired sync/async candidate selection second, and lifecycle/metadata/performance/mypyc integration last. There is no unresolved user decision or external dependency blocker.
