# Phase 29: Expected Domain Rejection - Research

**Researched:** 2026-09-17
**Domain:** Bounded pre-commit domain rejection in a priority-aware sync/async Python FSM
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Rejection-Code Contract

- **D-01:** `TransitionRejected(code)` accepts an exact `str`; enums and arbitrary string-convertible objects are rejected. — **Reversibility:** costly — widening the accepted public input later is additive, but narrowing a released contract would require a compatibility cycle.
- **D-02:** Codes are non-empty, at most 64 characters, and match `[a-z][a-z0-9_.-]*` exactly.
- **D-03:** Construction validates eagerly without trimming, case-folding, or other normalization: non-strings raise `TypeError`; empty, oversized, or malformed strings raise `ValueError`.

#### Result and Exception API

- **D-04:** `TransitionResult` stores one comparison-neutral `rejection_code: str | None`; a read-only `rejected` property derives status from that field. Do not store a second boolean or replace the existing result model with a status enum. — **Reversibility:** costly — this becomes the public result contract consumed by application code and later diagnostics.
- **D-05:** A rejected result has `cause=None` and bounded `error="Transition rejected: <code>"`; the validated code, not the error string, is the authoritative identifier.
- **D-06:** `TransitionResult.raise_if_failed()` continues to raise `TransitionError` with the originating result attached. `TransitionRejected` is solely the control signal raised inside eligibility hooks, not the exception emitted when consuming a failed result.
- **D-07:** `rejection_code` uses `compare=False` so legacy result equality remains stable, but stays visible in `repr` for debugging.

#### Condition Composition

- **D-08:** `AndCondition` and `OrCondition` propagate `TransitionRejected` immediately and evaluate no later child. Rejection is terminal regardless of boolean operator.
- **D-09:** `NotCondition` and `NegatedCondition` propagate rejection unchanged; they negate only boolean eligibility.
- **D-10:** The propagation rule applies recursively across synchronous, asynchronous, deferred, and nested composition. Async cancellation remains cancellation and must never become rejection.
- **D-11:** Direct condition evaluation outside an FSM lets `TransitionRejected` propagate normally. Only an approved FSM eligibility boundary converts it into a `TransitionResult`.

#### Observer, Query, and Metadata Behavior

- **D-12:** Trigger operations notify the existing failure-observer family exactly once using its unchanged callback signature and the rejected result. Do not add callback arguments or a parallel listener family.
- **D-13:** `can_trigger()` and `can_trigger_async()` stop selection and return `False` for expected rejection without mutation, observer notification, history, or trace events. Callers use `trigger*()` when they need the code.
- **D-14:** Runtime logging for expected rejection is metadata-only at debug level and may include the validated code; it emits no warning, traceback, or exception representation.
- **D-15:** Rejected results preserve the existing pre-commit failure metadata: source, trigger, lifecycle stage, selected priority, and internal mode. They do not add a history record or expose a new destination field.

### the agent's Discretion

- Exact private helper names, carrier layout, and test-file partitioning are left to research and planning, provided the public and semantic decisions above remain intact.
- The fixed internal constants used for validation and bounded error text may follow established naming conventions.

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope. Richer localized rejection details remain the existing `FUTR-04` future requirement unless stable codes prove insufficient.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| REJECT-01 | Users can signal expected domain rejection during pre-commit eligibility evaluation with public `TransitionRejected(code)`. | Put the validated public control exception beside the existing core result/exception API; catch it only at the three candidate eligibility calls. |
| REJECT-02 | Users receive stable, bounded, payload-safe rejection identifiers rather than arbitrary exception messages or objects. | Use one eager exact-type/length/pattern validator, a read-only code property, revalidation at conversion, fixed bounded result text, and no exception representation in logs. |
| REJECT-03 | Users receive expected-rejection semantics only when rejection originates from transition guards, declarative guards, or state permission checks. | The live selectors expose exactly three narrow catch sites; timing, preparation, lifecycle, handlers, callbacks, observers, and tracing remain outside them. |
| REJECT-04 | Users observe a rejection aborting the complete prioritized candidate group, while an ordinary false condition alone permits fallthrough. | Candidate helpers already use `None` only for group fallthrough and `TransitionResult` for terminal outcomes; rejection should return a terminal result, never `None`. |
| REJECT-05 | Users receive an uncommitted `TransitionResult` with explicit rejection status and code, distinct from unexpected exception causes. | Append `rejection_code` after existing fields with `compare=False`; derive `rejected`; build rejection with `committed=False`, `to_state=None`, `cause=None`, selected priority/mode/stage. |
| REJECT-06 | Users receive false from synchronous and asynchronous `can_trigger` queries for an expected rejection, while trigger operations preserve the structured rejection code. | Both query APIs already map any terminal `TransitionResult` to `False` without finalization; special rejection catches must return a result even where ordinary query exceptions still propagate. |
| REJECT-07 | Users observe existing failure observers exactly once for a rejected trigger without needing a separate rejection listener system. | Reuse `_trigger_owned()` / `_trigger_async_owned()` and `_finalize_failure()`; never finalize inside a selector. |
| REJECT-08 | Users can compose conditions without expected rejection being swallowed or converted to an ordinary false result. | Existing direct, iterative, and deferred combinators do not catch child exceptions; add propagation/no-later-child tests rather than special composition code. |
| REJECT-09 | Users receive ordinary execution-failure semantics when `TransitionRejected` is raised outside pre-commit eligibility evaluation. | Keep all lifecycle catches unchanged so the signal remains the `cause` of an ordinary stage-aware failure after selection; test pre- and post-commit stages. |
</phase_requirements>

## Summary

Phase 29 should be implemented as a narrow extension of the selector’s existing three-valued return protocol: `None` remains local group fallthrough, `_PreparedDispatch` remains successful selection, and a `TransitionResult` remains terminal. A caught `TransitionRejected` should therefore become a terminal result inside `_select_sync_candidate()` / `_select_async_candidate()`, before lifecycle begins; it must never become a new selector carrier or a special outer `trigger()` catch. This preserves priority, observer, and lifecycle ownership already encoded in the runtime. [VERIFIED: `src/fast_fsm/core.py:2771-2864`, `src/fast_fsm/core.py:4991-5079`]

The condition system needs evidence, not a rewrite. `AndCondition`, `OrCondition`, `NotCondition`, `NegatedCondition`, the iterative core evaluators, and deferred awaitable continuations perform boolean conversion or awaiting but contain no exception-to-false catch. A raised control signal already unwinds immediately, prevents later-child evaluation, and is converted only when it reaches an approved selector catch. [VERIFIED: `src/fast_fsm/conditions.py:91-203`, `src/fast_fsm/conditions.py:267-313`, `src/fast_fsm/core.py:443-532`, `src/fast_fsm/core.py:3282-3384`]

The largest non-obvious planning consequence is native-layout policy. A public exception class inherits an instance dictionary from `BaseException` even if it declares slots, and `core.py` is the sole mypyc compilation unit. The project currently registers exactly these three instance-dictionary exceptions: `"fast_fsm.conditions.CompiledFuncCondition"`, `"fast_fsm.core.TransitionError"`, and `"fast_fsm._diagnostics.DiagnosticBudgetExceeded"`; its tests assert that exact set. `TransitionRejected` should be an explicit non-native core exception, and the registry, release-evidence assertions, project instructions, and SPR must move atomically to four named exceptions. [VERIFIED: `setup.py:16-39`, `tools/release_evidence.py:128-140`, `tests/test_release_evidence.py:794-844`, `.github/copilot-instructions.md:40-50`] [CITED: https://mypyc.readthedocs.io/en/stable/native_classes.html]

**Primary recommendation:** Build one synchronous tracer first around the public signal/result contract and the three selector catches, then close async/composition/cancellation parity, and finish with post-selection classification plus pure/native/slots/performance proof. [VERIFIED: `.planning/phases/29-expected-domain-rejection/29-CONTEXT.md:90-112`]

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Code validation and public signal | API / Backend (library core) | — | The reusable library owns exact construction validation before application data becomes runtime metadata. [VERIFIED: `.planning/phases/29-expected-domain-rejection/29-CONTEXT.md:27-38`] |
| Rejection classification | API / Backend (selectors) | — | Only the machine-owned eligibility boundary has source, stage, selected priority, and mode together. [VERIFIED: `src/fast_fsm/core.py:2851-3051`, `src/fast_fsm/core.py:5066-5209`] |
| Composition propagation | API / Backend (condition layer) | — | Boolean wrappers own evaluation order but not FSM result conversion. [VERIFIED: `src/fast_fsm/conditions.py:149-203`, `src/fast_fsm/conditions.py:267-313`] |
| Failure observation | API / Backend (public trigger finalizer) | — | `_finalize_failure()` snapshots the existing observer family and invokes it exactly once per failed trigger boundary. [VERIFIED: `src/fast_fsm/core.py:3687-3709`, `src/fast_fsm/core.py:4228-4236`] |
| Query projection | API / Backend (query entry points) | — | `can_trigger*()` returns a boolean from selector output and never owns failure finalization. [VERIFIED: `src/fast_fsm/core.py:2671-2696`, `src/fast_fsm/core.py:4974-4989`] |
| Native-layout evidence | Build / Release tooling | API / Backend | The source exception lives in core, while audit tooling and structural tests prove pure/native policy alignment. [VERIFIED: `setup.py:16-39`, `tools/release_evidence.py:128-140`] |

## Project Constraints (from AGENTS.md)

- Use the active GSD phase artifacts as the execution plan; do not create or update GitHub Issues unless explicitly requested. [VERIFIED: `AGENTS.md:9-17`]
- Use `uv` for Python/package/test commands; never invoke bare `python`, `pip`, or `python -m pytest`. [VERIFIED: `.github/copilot-instructions.md:32-38`]
- Preserve O(1) source/trigger lookup and direct singleton dispatch; candidate groups remain local O(k), with no dispatch-time sort or unrelated topology scan. [VERIFIED: `.github/copilot-instructions.md:40-58`]
- All condition and callback signatures continue to accept `*args, **kwargs`; public changes are additive and removals require a deprecation cycle. [VERIFIED: `.github/copilot-instructions.md:60-63`]
- Run targeted tests during implementation and the full sequential suite once before push. [VERIFIED: `.github/copilot-instructions.md:65-71`]
- For Python changes, run Ruff formatting/fix/validation, blocking `task typecheck-mypy`, advisory `task typecheck-ty`, targeted tests, and the full suite. [VERIFIED: `.github/copilot-instructions.md:105-119`]
- `core.py` alone is compiled by mypyc; `conditions.py` and condition templates remain interpreted so users can subclass conditions. Pure and compiled behavior must match. [VERIFIED: `setup.py:16-39`, `.github/copilot-instructions.md:238-245`]
- A public API/behavior change requires the relevant SPR update in the same commit. [VERIFIED: `.github/copilot-instructions.md:340-362`]
- Intended work must be committed, safely rebased/pulled, pushed, and verified up to date; unrelated user files must not be staged. [VERIFIED: `AGENTS.md:19-30`, `.github/copilot-instructions.md:120-129`]

## Standard Stack

### Core

| Library / Facility | Version | Purpose | Why Standard |
|--------------------|---------|---------|--------------|
| Python standard library (`Exception`, `re`, `dataclasses`, `asyncio`) | Python `>=3.10` | Signal validation, result carrier, sync/async exception taxonomy | The feature requires no new runtime dependency; the project already targets Python `>=3.10`. [VERIFIED: `pyproject.toml:1-9`] |
| Fast FSM core | repository source | Public exception/result plus selector conversion | The selector, lifecycle, result, observer, and cancellation seams already live together in `core.py`. [VERIFIED: `src/fast_fsm/core.py:535-590`, `src/fast_fsm/core.py:2771-3051`, `src/fast_fsm/core.py:4991-5348`] |
| mypy/mypyc | `1.17.1` release pin | Type/native-layout validation | The build system pins and compiles only `src/fast_fsm/core.py`. [VERIFIED: `pyproject.toml:22-25`, `setup.py:31-39`] |
| pytest / pytest-asyncio | `8.4.1` / `1.3.0` lock | Behavioral and async cancellation oracle | The active lock and pytest configuration already support sequential async tests. [VERIFIED: `uv.lock:1414-1416`, `uv.lock:1432-1434`, `pyproject.toml:54-73`] |

### Supporting

| Facility | Version | Purpose | When to Use |
|----------|---------|---------|-------------|
| Project slots-policy audit | repository tool | Detect unregistered instance dictionaries and policy drift | Run after adding the new exception and after registry/instruction/SPR updates. [VERIFIED: `tools/release_evidence.py:128-140`, `tests/test_release_evidence.py:794-844`] |
| Task type gates | repository Taskfile | Blocking implementation/stub mypy plus advisory ty | Run after `core.py`, `core.pyi`, or exports change. [VERIFIED: `Taskfile.yml:105-125`] |
| mypyc build check | repository Taskfile | Fresh compiled import/behavior smoke | Run before phase closure and native semantic oracle. [VERIFIED: `Taskfile.yml:185-203`] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Terminal `TransitionResult` from candidate helper | New selector outcome/carrier | Rejected: it duplicates a terminal channel the selector already owns and expands hot-path/native layout. [VERIFIED: `src/fast_fsm/core.py:2771-2864`] |
| Narrow selector catches | Outer `trigger*()` catch | Rejected: an outer catch cannot distinguish approved eligibility rejection from the same signal raised after selection. [VERIFIED: `src/fast_fsm/core.py:4228-4236`, `src/fast_fsm/core.py:5274-5348`] |
| Existing failure observers | New rejection listener family | Rejected by locked decision D-12 and unnecessary because `_finalize_failure()` already owns one observer pass. [VERIFIED: `.planning/phases/29-expected-domain-rejection/29-CONTEXT.md:47-52`, `src/fast_fsm/core.py:3687-3709`] |

**Installation:** No packages are added or upgraded in this phase. [VERIFIED: `.planning/REQUIREMENTS.md:85-97`]

## Architecture Patterns

### System Architecture Diagram

```text
trigger / can_trigger
        |
        v
one source+trigger slot lookup (singleton O(1) or stored local group O(k))
        |
        v
candidate timing ---- false ----> next candidate (group only)
        |
        v
transition guard ---- false ----> next candidate
        | raises TransitionRejected(code)
        +------------------------------+
        v                              |
declarative guard -- false --> next    |
        | raises TransitionRejected    |
        v                              |
state permission --- false --> next    |
        | raises TransitionRejected    |
        v                              v
 _PreparedDispatch              rejected TransitionResult
        |                              |
        v                              +--> can_trigger*: False, no finalization
lifecycle runner                       |
        |                              +--> trigger*: one _finalize_failure pass
        v
success or ordinary staged failure
```

The three approved stages are the existing exact strings `"guard"` and `"state-permission"`; both transition and declarative guards use `"guard"`. [VERIFIED: `src/fast_fsm/core.py:110-124`] The conversion must occur before `_execute_transition*()` so lifecycle-raised signals stay ordinary failures. [VERIFIED: `src/fast_fsm/core.py:4228-4236`, `src/fast_fsm/core.py:5298-5317`]

### Recommended Project Structure

```text
src/fast_fsm/
├── core.py                 # public signal/result; sync/async selector conversion
├── core.pyi                # exact public type/field/property contract
├── conditions.py           # unchanged propagation machinery; no FSM conversion
└── __init__.py             # package-root export
tests/
├── test_expected_rejection.py  # central REJECT-01..09 behavioral tracer
├── test_mypyc_guard.py          # field order, exception/native/export structure
├── test_release_evidence.py     # fourth registered exception policy
└── test_logging_config.py       # metadata-only/no-repr logging proof
tools/
└── release_evidence.py          # registered slots exception inventory
```

This partition keeps the behavioral matrix cohesive while extending existing structural authorities instead of copying them. [VERIFIED: `.planning/phases/29-expected-domain-rejection/29-CONTEXT.md:90-112`]

### Pattern 1: Terminal Result at the Candidate Boundary

**What:** Catch `TransitionRejected` immediately around each approved user hook and return a rejection result. Return `None` only for ordinary false inside a group. [VERIFIED: `src/fast_fsm/core.py:2851-3051`, `src/fast_fsm/core.py:5066-5209`]

**When to use:** Transition guard, resolved declarative guard, and state permission only. [VERIFIED: `.planning/phases/29-expected-domain-rejection/29-CONTEXT.md:9-15`]

**Example skeleton:**

```python
try:
    eligible = evaluate_hook(...)
except TransitionRejected as signal:
    return build_rejection_result(
        signal,
        stage=stage,
        priority=entry.priority,
        internal=entry.internal,
    )
except Exception as cause:
    return build_unexpected_failure(cause, ...)

if not eligible:
    return None if scan_group else build_ineligible_result(...)
```

The required rejection result literals are `cause=None`, `error="Transition rejected: <code>"`, `committed=False`, and no destination. [VERIFIED: `.planning/phases/29-expected-domain-rejection/29-CONTEXT.md:33-38`, `.planning/phases/29-expected-domain-rejection/29-CONTEXT.md:47-52`]

### Pattern 2: One Validated Scalar, Two Checks

**What:** Validate eagerly in `TransitionRejected.__init__`, expose a read-only code, and defensively re-check the scalar at selector conversion before copying it into result/log metadata. [VERIFIED: `.planning/phases/29-expected-domain-rejection/29-CONTEXT.md:27-31`] The second check is rejection-path-only and protects the output invariant from mutated or subclass-crafted exception objects without charging success dispatch. [VERIFIED: `.planning/phases/29-expected-domain-rejection/29-CONTEXT.md:100-104`]

**Exact accepted language:** `"[a-z][a-z0-9_.-]*"`, length `1..64`, with no normalization. [VERIFIED: `.planning/phases/29-expected-domain-rejection/29-CONTEXT.md:29-31`]

**Classification rule:** If a caught object no longer carries a valid exact string, classify it as the existing unexpected guard/permission failure with the signal as hidden cause; never copy an invalid value into `error`, logs, or `rejection_code`. [VERIFIED: `.planning/phases/29-expected-domain-rejection/29-CONTEXT.md:35-36`, `.planning/phases/29-expected-domain-rejection/29-CONTEXT.md:51-52`]

### Pattern 3: Additive Result Tail

**What:** Append `rejection_code` after the current exact field sequence `"success", "from_state", "to_state", "trigger", "error", "committed", "stage", "cause", "priority", "internal"`; keep `compare=False`, retain default repr visibility, and derive `rejected`. [VERIFIED: `src/fast_fsm/core.py:554-590`, `tests/test_mypyc_guard.py:2156-2167`] [CITED: https://docs.python.org/3.13/library/dataclasses.html]

**Why:** Appending preserves legacy positional construction, while `compare=False` preserves equality. The existing `cause` is already `repr=False`; `rejection_code` must not copy that setting. [VERIFIED: `src/fast_fsm/core.py:558-570`]

### Pattern 4: Finalize Only at Trigger Boundaries

**What:** Selector helpers construct but do not observe failures. `_trigger_owned()` and `_trigger_async_owned()` finalize a terminal rejection once; query methods only test whether selection returned a result. [VERIFIED: `src/fast_fsm/core.py:3631-3709`, `src/fast_fsm/core.py:4228-4236`, `src/fast_fsm/core.py:5298-5317`]

**Why:** This automatically satisfies unchanged observer signature/cardinality and observer-free queries. [VERIFIED: `tests/test_transition_lifecycle.py:526-573`, `tests/test_priority_selection.py:994-1027`]

### Pattern 5: Protect Composition by Non-Interference

**What:** Do not add catch/re-raise code to condition combinators. Assert that synchronous, asynchronous, nested, deferred, and negated shapes propagate the identical signal and stop later children. [VERIFIED: `src/fast_fsm/conditions.py:91-203`, `src/fast_fsm/conditions.py:267-313`, `src/fast_fsm/core.py:443-532`]

**Why:** The current `finally` cleanup in iterative evaluation already clears traversal state, and deferred wrappers already consume each awaitable once. Special handling would add more exception/cancellation surface without changing correct semantics. [VERIFIED: `src/fast_fsm/core.py:460-532`, `tests/test_condition_interface.py:87-98`]

### Anti-Patterns to Avoid

- **Catch in `trigger*()`:** misclassifies entry/action/listener/observer rejection as expected. [VERIFIED: `src/fast_fsm/core.py:3711-4058`, `src/fast_fsm/core.py:4598-4972`]
- **Return `None` for rejection:** permits unsafe lower-priority fallback. [VERIFIED: `src/fast_fsm/core.py:2814-2834`, `src/fast_fsm/core.py:5029-5049`]
- **Store both `rejected` and `rejection_code`:** creates two sources of truth and violates D-04. [VERIFIED: `.planning/phases/29-expected-domain-rejection/29-CONTEXT.md:35-38`]
- **Use `str(code)` or normalize:** admits objects/Unicode/casing the locked contract rejects. [VERIFIED: `.planning/phases/29-expected-domain-rejection/29-CONTEXT.md:27-31`]
- **Log `repr(signal)` or traceback:** makes expected control flow look like a defect and weakens payload policy. [VERIFIED: `.planning/phases/29-expected-domain-rejection/29-CONTEXT.md:49-52`]
- **Unify existing query exception behavior:** ordinary transition-guard/permission query exceptions currently propagate while declarative query exceptions return terminal false; Phase 29 should special-case rejection without refactoring that compatibility boundary. [VERIFIED: `src/fast_fsm/core.py:2928-2945`, `src/fast_fsm/core.py:2969-2994`, `src/fast_fsm/core.py:3020-3037`, `tests/test_priority_selection.py:1030-1133`]
- **Add a rejection ContextVar:** async selection already carries stage, priority, and internal mode task-locally; the caught rejection can be converted synchronously at the await site. [VERIFIED: `src/fast_fsm/core.py:82-103`, `src/fast_fsm/core.py:5080-5083`, `src/fast_fsm/core.py:5290-5348`]

## Tracer-First Plan Decomposition

### Plan 29-01 — Public contract and synchronous rejection tracer

1. Add failing tests first for exact code construction, public imports, result tail/property/equality/repr, `raise_if_failed()`, and sync transition/declarative/permission rejection for singleton and priority-group paths. [VERIFIED: `tests/test_boundary_negative.py:175-254`, `tests/test_priority_selection.py:670-834`, `tests/test_priority_selection.py:920-991`]
2. Add `TransitionRejected`, central validation/error constants, `TransitionResult.rejection_code`, `rejected`, the rejection result helper, and the three sync catch sites. [VERIFIED: `src/fast_fsm/core.py:535-590`, `src/fast_fsm/core.py:2851-3051`]
3. Prove one failure-observer pass, no history/mutation/lifecycle/lower-candidate work, selected priority/internal metadata, `cause=None`, and metadata-only debug behavior. [VERIFIED: `src/fast_fsm/core.py:3631-3709`, `tests/test_transition_lifecycle.py:526-573`]

### Plan 29-02 — Query, composition, and async parity

1. Add query tests showing rejection returns `False`, stops the group, and produces no observer/history/trace event while ordinary exception compatibility stays unchanged. [VERIFIED: `src/fast_fsm/core.py:2671-2696`, `src/fast_fsm/core.py:4974-4989`, `tests/test_priority_selection.py:994-1133`]
2. Add direct/composed/nested/deferred tests for all four wrapper families, asserting identical signal identity and zero later-child calls; leave production composition code unchanged unless a test proves a gap. [VERIFIED: `tests/test_condition_interface.py:55-98`, `src/fast_fsm/conditions.py:91-203`]
3. Add the three async selector catches and parity tests for sync leaves, `AsyncCondition`, callable-backed awaitables, declarative guards, async state permissions, internal/external candidates, and group abort. [VERIFIED: `src/fast_fsm/core.py:4991-5209`, `tests/test_priority_selection.py:287-356`]
4. Re-run handshake-based cancellation tests to prove `CancelledError` remains observer-visible cancellation and is re-raised, never converted to rejection. [VERIFIED: `tests/test_priority_selection.py:359-553`, `tests/test_transition_lifecycle.py:1166-1267`] [CITED: https://docs.python.org/3/library/asyncio-exceptions.html]

### Plan 29-03 — Boundary classification, native layout, and fast-path closure

1. Parameterize pre-commit and post-commit lifecycle hooks so the same signal outside eligibility remains an ordinary staged failure with `cause is signal`, correct commit/history truth, and one observer pass. [VERIFIED: `tests/test_transition_lifecycle.py:422-485`, `tests/test_transition_lifecycle.py:948-1053`]
2. Extend stub/export/AST/runtime-field/pure-native semantic tests and add `TransitionRejected` to the measured exception registry. Update `.github/copilot-instructions.md` and `.specify/memory/spr-core-api.md` in the same commit so all slots-policy authorities name the same four exceptions. [VERIFIED: `tests/test_mypyc_guard.py:1884-1940`, `tests/test_mypyc_guard.py:2102-2268`, `tests/test_release_evidence.py:794-844`]
3. Add minimal API reference exposure without the Phase 32 tutorial/example expansion. [VERIFIED: `docs/api/core.md:65-84`, `docs/api/conditions.md:1-59`]
4. Run focused tests, slots policy, blocking/advisory type gates, fresh compiled build/native oracle, full suite, and the existing singleton benchmark as a regression signal. Phase 32 remains responsible for durable installed-artifact performance evidence. [VERIFIED: `.github/copilot-instructions.md:40-81`, `Taskfile.yml:105-125`, `Taskfile.yml:185-203`]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Selector outcome algebra | New enum/carrier hierarchy | Existing `None` / `_PreparedDispatch` / `TransitionResult` protocol | It already distinguishes local fallthrough from terminal failure and selection. [VERIFIED: `src/fast_fsm/core.py:2771-2864`] |
| Failure observation | Rejection callback registry | `_finalize_failure()` | It snapshots observers, isolates `BaseException`, and preserves the original result. [VERIFIED: `src/fast_fsm/core.py:3687-3709`] |
| Condition traversal | Recursive rejection-aware evaluator | Existing iterative/deferred evaluators | They already preserve ordering, short-circuiting, await ownership, cycle cleanup, and exception propagation. [VERIFIED: `src/fast_fsm/core.py:443-532`, `src/fast_fsm/core.py:3282-3384`] |
| Cancellation classification | Convert cancellation into result-valued rejection | Existing `CancelledError` public-boundary finalizer and bare re-raise | Cancellation is a `BaseException` and should almost always be re-raised. [VERIFIED: `src/fast_fsm/core.py:5318-5348`] [CITED: https://docs.python.org/3/library/asyncio-exceptions.html] |
| Payload normalization | Generic serialization/stringification | Exact ASCII allow-list and length check | Positive validation and logical limits are the applicable secure-input pattern. [VERIFIED: `.planning/phases/29-expected-domain-rejection/29-CONTEXT.md:27-31`] [CITED: https://cornucopia.owasp.org/taxonomy/asvs-5.0/02-validation-and-business-logic/02-input-validation] |

**Key insight:** Rejection is an input at three user-code calls and an ordinary terminal result everywhere afterward; widening either side creates ambiguity at the commit boundary. [VERIFIED: `.planning/phases/29-expected-domain-rejection/29-CONTEXT.md:9-20`]

## Common Pitfalls

### Pitfall 1: Broad Catch at the Public Trigger Boundary

**What goes wrong:** `TransitionRejected` raised by source exit, destination enter, declarative action, trigger callback, or after listener is mislabeled expected and loses stage/commit truth. [VERIFIED: `src/fast_fsm/core.py:3711-4058`]

**Why it happens:** The public trigger sees both selection and execution exceptions but no longer knows which user-code seam originated them. [VERIFIED: `src/fast_fsm/core.py:4228-4236`]

**How to avoid:** Catch only immediately around the three eligibility invocations. [VERIFIED: `.planning/phases/29-expected-domain-rejection/29-CONTEXT.md:106-112`]

**Warning signs:** A `TransitionRejected` name appears in `_execute_transition*()`, `_trigger_owned()`, `_trigger_async_owned()` outside selector handling, or a post-commit test has `rejected is True`. [VERIFIED: `.planning/phases/29-expected-domain-rejection/29-CONTEXT.md:9-15`]

### Pitfall 2: Query Rejection Escapes Like an Ordinary Guard Error

**What goes wrong:** `can_trigger*()` raises instead of returning `False`. [VERIFIED: `.planning/phases/29-expected-domain-rejection/29-CONTEXT.md:49-50`]

**Why it happens:** Current sync/async transition-guard and permission paths re-raise ordinary query exceptions. [VERIFIED: `src/fast_fsm/core.py:2928-2930`, `src/fast_fsm/core.py:3020-3022`, `src/fast_fsm/core.py:5139-5141`, `src/fast_fsm/core.py:5186-5188`]

**How to avoid:** Put the specific `TransitionRejected` catch before the existing general `Exception` branch and return a terminal result for both trigger and query modes. [VERIFIED: `src/fast_fsm/core.py:2671-2696`, `src/fast_fsm/core.py:4974-4989`]

**Warning signs:** Tests need `pytest.raises(TransitionRejected)` around `can_trigger*()` or a lower candidate executes after rejection. [VERIFIED: `.planning/REQUIREMENTS.md:31-35`]

### Pitfall 3: Treating Rejection as False in Composition

**What goes wrong:** `OrCondition` evaluates a fallback child, `NotCondition` turns rejection into true, or a group selects a lower candidate. [VERIFIED: `.planning/phases/29-expected-domain-rejection/29-CONTEXT.md:40-45`]

**Why it happens:** A helper catches exceptions and returns `False`, or code applies boolean coercion after swallowing the signal. [VERIFIED: `src/fast_fsm/conditions.py:91-203`]

**How to avoid:** Keep wrappers catch-free and test identical signal propagation before/after an await boundary. [VERIFIED: `src/fast_fsm/conditions.py:149-203`]

**Warning signs:** A new `except TransitionRejected: return False` appears in `conditions.py`, or a later-child sentinel fires. [VERIFIED: `.planning/REQUIREMENTS.md:35-36`]

### Pitfall 4: Leaking an Invalid or Mutable Signal Payload

**What goes wrong:** A subclass-crafted/mutated code bypasses construction validation and enters result/error/log output. [VERIFIED: `.planning/phases/29-expected-domain-rejection/29-CONTEXT.md:27-36`]

**Why it happens:** Selector conversion trusts the exception attribute without re-checking the bounded language. [CITED: https://cornucopia.owasp.org/taxonomy/asvs-5.0/02-validation-and-business-logic/02-input-validation]

**How to avoid:** Keep the property read-only and revalidate on the cold rejection path; invalid caught objects become unexpected failures with hidden cause. [VERIFIED: `.planning/phases/29-expected-domain-rejection/29-CONTEXT.md:35-36`]

**Warning signs:** Result/log formatting calls `str(signal)` or `repr(signal)`, or tests can inject uppercase, whitespace, Unicode, or >64-character output by mutating/subclassing the signal. [VERIFIED: `.planning/phases/29-expected-domain-rejection/29-CONTEXT.md:29-31`]

### Pitfall 5: Slots-Policy Drift

**What goes wrong:** The implementation passes behavior tests but fails release evidence, or documentation still claims exactly three registered exceptions. [VERIFIED: `tests/test_release_evidence.py:794-844`]

**Why it happens:** Built-in exceptions retain an instance dictionary, and the audit requires every such class to be explicitly registered. [VERIFIED: `tools/release_evidence.py:128-140`]

**How to avoid:** Update runtime registry, its exact-set tests, `.github/copilot-instructions.md`, and SPR in one plan/commit; use `@mypyc_attr(native_class=False)` for consistent pure/native exception behavior. [VERIFIED: `src/fast_fsm/core.py:535-550`, `.github/copilot-instructions.md:40-50`] [CITED: https://mypyc.readthedocs.io/en/stable/native_classes.html]

**Warning signs:** `slots-policy --json` reports an unregistered class or authority-name mismatch. [VERIFIED: `tests/test_release_evidence.py:794-844`]

### Pitfall 6: Cancellation Falls into Rejection Handling

**What goes wrong:** Cancellation returns a rejection result instead of re-raising the identical cancellation after one observer pass. [VERIFIED: `src/fast_fsm/core.py:5318-5348`]

**Why it happens:** Catching `BaseException` or adding generic translation around awaitable helpers. [CITED: https://docs.python.org/3/library/asyncio-exceptions.html]

**How to avoid:** `TransitionRejected` must subclass `Exception`; retain the dedicated `except asyncio.CancelledError` public boundary and no `BaseException` catch in selectors/combinators. [VERIFIED: `src/fast_fsm/core.py:5318-5348`]

**Warning signs:** cancellation tests return normally, observer count changes, or lower candidates run after a cancelled guard. [VERIFIED: `tests/test_priority_selection.py:359-553`]

## Code Examples

Verified planning patterns; final names remain at the implementer’s discretion.

### Public control signal and result tail

```python
@mypyc_attr(native_class=False)
class TransitionRejected(Exception):
    def __init__(self, code: str) -> None:
        validated = _validate_rejection_code(code)
        self._code = validated
        super().__init__(validated)

    @property
    def code(self) -> str:
        return self._code


@dataclass(slots=True)
class TransitionResult:
    # existing fields remain in their current order
    rejection_code: Optional[str] = field(default=None, compare=False)

    @property
    def rejected(self) -> bool:
        return self.rejection_code is not None
```

The public result’s current ordered tail is `"committed", "stage", "cause", "priority", "internal"`; append `"rejection_code"` after it. [VERIFIED: `src/fast_fsm/core.py:558-570`, `tests/test_mypyc_guard.py:2156-2167`] `field(compare=False)` excludes the value from generated equality while leaving repr enabled by default. [CITED: https://docs.python.org/3.13/library/dataclasses.html]

### Narrow conversion that preserves query semantics

```python
try:
    condition_result = self._evaluate_condition_sync(condition, args, safe_kwargs)
except TransitionRejected as signal:
    return self._build_rejection_result(
        current_name,
        trigger,
        signal,
        stage=_LIFECYCLE_STAGE_GUARD,
        priority=entry.priority,
        internal=entry.internal,
    )
except Exception as cause:
    if for_query:
        raise
    return self._build_failure_result(..., cause=cause)
```

The exact stage values used here are `"guard"` and `"state-permission"`. [VERIFIED: `src/fast_fsm/core.py:112-113`] The specific catch must precede `for_query` re-raise logic so rejection returns a result and the query maps it to `False`. [VERIFIED: `src/fast_fsm/core.py:2671-2696`, `src/fast_fsm/core.py:2928-2945`]

### Ordinary post-selection failure remains ordinary

```python
try:
    callback(...)
except Exception as cause:
    return self._build_lifecycle_failure(
        old_state,
        to_state,
        trigger,
        stage,
        cause,
        committed=committed,
        priority=prepared.entry.priority,
        internal=prepared.entry.internal,
    )
```

No rejection-specific branch belongs here; existing lifecycle catches already retain the original exception as hidden `cause`. [VERIFIED: `src/fast_fsm/core.py:3662-3685`, `src/fast_fsm/core.py:3711-4058`]

## State of the Art

| Old Approach | Current Approach for Phase 29 | When Changed | Impact |
|--------------|-------------------------------|--------------|--------|
| Boolean eligibility only | False remains fallthrough; validated `TransitionRejected` is terminal expected rejection; other exceptions remain defects | Phase 29 contract | Adds a third semantic outcome without adding a validator family. [VERIFIED: `.planning/phases/29-expected-domain-rejection/29-CONTEXT.md:9-20`] |
| Any terminal pre-commit exception represented only by hidden `cause` | Expected rejection stores a bounded scalar code and no cause | Phase 29 contract | Applications get stable machine-readable domain outcomes without exposing arbitrary exception payload. [VERIFIED: `.planning/phases/29-expected-domain-rejection/29-CONTEXT.md:33-38`] |
| Three registered instance-dictionary exceptions | Four, adding the public control exception | Phase 29 implementation consequence | Keeps slots-policy complete and explicit rather than silently exempting a class. [VERIFIED: `tools/release_evidence.py:128-140`, `tests/test_release_evidence.py:794-844`] |

**Deprecated/outdated:** Do not add validator callbacks, rejection listeners, status enums, rich payload objects, rollback, queues, or statechart behavior; all are outside this phase. [VERIFIED: `.planning/phases/29-expected-domain-rejection/29-CONTEXT.md:17-20`, `.planning/phases/29-expected-domain-rejection/29-CONTEXT.md:35-52`]

## Closest Existing Test Patterns

| Concern | Closest Test | Reuse Pattern |
|---------|--------------|---------------|
| False fallthrough vs terminal exception | `test_sync_group_rejections_fall_through_each_eligibility_stage`, `test_sync_group_guard_exception_is_terminal_and_finalized_once` | Replace raised `RuntimeError` with `TransitionRejected` and assert terminal code/no cause. [VERIFIED: `tests/test_priority_selection.py:670-834`] |
| Declarative/permission boundaries | `test_sync_group_declarative_and_permission_exceptions_stop_selection` | Parameterize approved seam and expected stage. [VERIFIED: `tests/test_priority_selection.py:920-991`] |
| Query compatibility | `test_can_trigger_does_not_advance_after_a_condition_or_permission_exception`, `test_can_trigger_treats_a_declarative_exception_as_terminal_false` | Add rejection-specific false/no-observer cases without changing ordinary exception outcomes. [VERIFIED: `tests/test_priority_selection.py:1030-1133`] |
| Async group terminality | `test_async_group_terminal_exception_and_exhaustion_finalize_once` | Assert no speculative/lower candidate and one observer pass. [VERIFIED: `tests/test_priority_selection.py:287-356`] |
| Async cancellation | priority cancellation and lifecycle cancellation handshake tests | Reuse event handshakes; never sleep. [VERIFIED: `tests/test_priority_selection.py:359-553`, `tests/test_transition_lifecycle.py:1166-1267`] |
| Composition/deferred ownership | `test_operators_construct_canonical_wrappers_and_short_circuit`, `test_deferred_compound_guard_result_has_single_await_ownership` | Add raising leaf and later-child sentinel in direct and awaited shapes. [VERIFIED: `tests/test_condition_interface.py:55-98`] |
| Observer cardinality/isolation | precommit and observer isolation tests | Assert exactly one rejected-trigger pass and unchanged snapshot/reentry behavior. [VERIFIED: `tests/test_transition_lifecycle.py:526-666`] |
| Post-selection classification | destination-enter tracer and declarative failure tests | Raise the signal at uncommitted and committed stages and assert ordinary cause/stage truth. [VERIFIED: `tests/test_transition_lifecycle.py:422-485`, `tests/test_transition_lifecycle.py:1018-1053`] |
| Trace/output safety | default metadata-only and redactor-failure tests | Use hostile repr and caplog/capture records; assert no exception repr/traceback/warning. [VERIFIED: `tests/test_logging_config.py:359-480`, `tests/test_logging_config.py:805-940`] |
| Stub/native field order | Phase 28 carrier structural/native oracle | Append the result field, add public exception/export assertions, run in pure and compiled origins. [VERIFIED: `tests/test_mypyc_guard.py:2102-2268`, `tests/test_mypyc_guard.py:2324-2395`] |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| — | None. All recommendations are grounded in locked decisions, live repository source/tests, or cited official documentation. | — | — |

## Open Questions

No user decision is missing. The only implementation discretion—private helper names, exact carrier placement, and test partitioning—can be resolved by the prescriptive structure above without changing the public contract. [VERIFIED: `.planning/phases/29-expected-domain-rejection/29-CONTEXT.md:54-57`]

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| `uv` | all Python/test/build commands | ✓ | `0.12.12` | None; project mandates uv. [VERIFIED: local command `uv --version`, 2026-09-17] |
| `task` | typecheck/build/source gates | ✓ | `3.53.1` | Direct uv commands only when an exact task has no equivalent; prefer Taskfile. [VERIFIED: local command `task --version`, 2026-09-17] |
| Node.js | GSD seams only | ✓ | `v22.23.2` | Not required by implementation/tests. [VERIFIED: local command `node --version`, 2026-09-17] |
| Apple clang | mypyc native build | ✓ | `21.0.0` | Pure-source tests remain available, but native closure is required. [VERIFIED: local command `cc --version`, 2026-09-17] |
| mypy/mypyc | compiled core/type gate | ✓ via lock | `1.17.1` | None for release/native proof. [VERIFIED: `uv.lock:991-1000`] |
| pytest / pytest-asyncio | semantic validation | ✓ via lock | `8.4.1` / `1.3.0` | None. [VERIFIED: `uv.lock:1414-1416`, `uv.lock:1432-1434`] |

**Missing dependencies with no fallback:** None. [VERIFIED: local environment audit, 2026-09-17]

**Missing dependencies with fallback:** None. [VERIFIED: local environment audit, 2026-09-17]

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest `8.4.1` + pytest-asyncio `1.3.0` [VERIFIED: `uv.lock:1414-1434`] |
| Config file | `pyproject.toml` with sequential `-x -q --tb=short --strict-markers` and `asyncio_mode="auto"` [VERIFIED: `pyproject.toml:54-73`] |
| Quick run command | `uv run pytest tests/test_expected_rejection.py -x -q` |
| Adjacent regression command | `uv run pytest tests/test_priority_selection.py tests/test_condition_interface.py tests/test_transition_lifecycle.py tests/test_mypyc_guard.py -x -q` |
| Full suite command | `uv run pytest tests/ -x -q` [VERIFIED: `.github/copilot-instructions.md:65-71`] |
| Structural/layout command | `uv run python tools/release_evidence.py slots-policy --json` [VERIFIED: `.github/copilot-instructions.md:40-50`] |
| Type commands | `task typecheck-mypy` (blocking), `task typecheck-ty` (advisory) [VERIFIED: `Taskfile.yml:105-118`] |
| Native command | `task build-check`, followed by the focused semantic oracle from a confirmed native origin [VERIFIED: `Taskfile.yml:185-203`] |

The current adjacent suite (`test_priority_selection.py`, `test_condition_interface.py`, `test_transition_lifecycle.py`, `test_mypyc_guard.py`) passed on 2026-09-17; six existing tests were skipped by their established platform/origin guards. [VERIFIED: local `uv run pytest ...`, 2026-09-17]

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| REJECT-01 | public signal, valid construction, package/core imports | unit + typing | `uv run pytest tests/test_expected_rejection.py -k 'public or construct' -x -q` | ❌ Wave 0 |
| REJECT-02 | exact type, empty/65-char/malformed/Unicode rejection, bounded text, hostile repr/subclass defense | boundary/security | `uv run pytest tests/test_expected_rejection.py -k 'validation or payload' -x -q` | ❌ Wave 0 |
| REJECT-03 | conversion only at transition guard, declarative guard, permission; timing/lifecycle remain ordinary | integration | `uv run pytest tests/test_expected_rejection.py -k 'approved_boundary or outside_boundary' -x -q` | ❌ Wave 0 |
| REJECT-04 | group abort vs false fallthrough, selected priority/internal, no lower candidate | integration | `uv run pytest tests/test_expected_rejection.py -k 'priority or fallthrough' -x -q` | ❌ Wave 0 |
| REJECT-05 | result fields/property/equality/repr/cause/error/raise_if_failed | unit + structural | `uv run pytest tests/test_expected_rejection.py tests/test_mypyc_guard.py -k 'result or rejection' -x -q` | ❌ Wave 0 + ✅ extend |
| REJECT-06 | sync/async queries false, no mutation/history/observer/trace | integration | `uv run pytest tests/test_expected_rejection.py -k 'query' -x -q` | ❌ Wave 0 |
| REJECT-07 | one unchanged failure-observer pass; observer exceptions isolated | integration | `uv run pytest tests/test_expected_rejection.py -k 'observer' -x -q` | ❌ Wave 0 |
| REJECT-08 | direct/sync/async/deferred/nested AND/OR/NOT/Negated propagation | unit + async | `uv run pytest tests/test_expected_rejection.py tests/test_condition_interface.py -k 'compos' -x -q` | ❌ Wave 0 + ✅ extend |
| REJECT-09 | ordinary pre/post-commit lifecycle failure, hidden cause, cancellation unchanged | integration + async | `uv run pytest tests/test_expected_rejection.py -k 'lifecycle or cancellation' -x -q` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `uv run pytest tests/test_expected_rejection.py -x -q` plus the closest modified authority (`test_priority_selection.py`, `test_condition_interface.py`, `test_logging_config.py`, `test_mypyc_guard.py`, or `test_release_evidence.py`). [VERIFIED: `.github/copilot-instructions.md:65-71`]
- **Per wave merge:** `uv run pytest tests/test_expected_rejection.py tests/test_priority_selection.py tests/test_condition_interface.py tests/test_transition_lifecycle.py tests/test_async.py tests/test_logging_config.py tests/test_mypyc_guard.py tests/test_release_evidence.py -x -q`. [VERIFIED: `.github/copilot-instructions.md:185-196`]
- **Phase gate:** Ruff on changed Python files, `task typecheck-mypy`, visible `task typecheck-ty`, slots policy, fresh compiled/native semantic proof, full suite, docs warnings-as-errors if API reference changes, and benchmark regression signal. [VERIFIED: `.github/copilot-instructions.md:105-120`, `.github/copilot-instructions.md:199-226`]

### Wave 0 Gaps

- [ ] `tests/test_expected_rejection.py` — central requirement-labelled sync/async matrix for REJECT-01..09.
- [ ] Extend `tests/test_mypyc_guard.py` — exact result field/property, exception decorator/layout, stub, package export, catch-boundary, no-sort/no-copy, and pure/native semantic oracle.
- [ ] Extend `tests/test_release_evidence.py` — fourth registered exception plus synchronized policy authorities.
- [ ] Extend `tests/test_logging_config.py` — debug-only rejection and TRACE/no-repr/no-warning/no-trace-query evidence.
- [ ] No test framework/config/fixture install gap; existing pytest and async handshake patterns are sufficient. [VERIFIED: `pyproject.toml:54-73`, `tests/test_priority_selection.py:359-553`]

## Security Domain

Security enforcement is enabled because `.planning/config.json` does not set `security_enforcement` to `false`. [VERIFIED: `.planning/config.json:1-38`]

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | No identity/authentication surface is added. [VERIFIED: `.planning/phases/29-expected-domain-rejection/29-CONTEXT.md:6-20`] |
| V3 Session Management | no | No session/cookie/token state exists in this phase. [VERIFIED: `.planning/phases/29-expected-domain-rejection/29-CONTEXT.md:6-20`] |
| V4 Access Control | no as an enforcement layer | State permission hooks are domain policy callbacks, not application authorization; preserve their exception truth without claiming an access-control system. [VERIFIED: `src/fast_fsm/core.py:3016-3051`] |
| V5 / ASVS 5.0 V2 Validation and Business Logic | yes | Exact type plus positive ASCII pattern and `1..64` length; reject, never normalize. [VERIFIED: `.planning/phases/29-expected-domain-rejection/29-CONTEXT.md:27-31`] [CITED: https://cornucopia.owasp.org/taxonomy/asvs-5.0/02-validation-and-business-logic/02-input-validation] |
| V7 / ASVS 5.0 V16 Logging and Error Handling | yes | Fixed bounded public error, no arbitrary exception repr/traceback, metadata-only debug/trace, hidden unexpected cause. [VERIFIED: `.planning/phases/29-expected-domain-rejection/29-CONTEXT.md:35-36`, `.planning/phases/29-expected-domain-rejection/29-CONTEXT.md:49-52`] [CITED: https://cornucopia.owasp.org/taxonomy/asvs-5.0/16-security-logging-and-error-handling/02-general-logging] |
| V6 Cryptography | no | No cryptographic material or operation is introduced. [VERIFIED: `.planning/phases/29-expected-domain-rejection/29-CONTEXT.md:6-20`] |

### Plan-Time STRIDE Threat Register

| Threat | STRIDE | Attack / Failure Mode | Required Mitigation | Verification Gate |
|--------|--------|-----------------------|---------------------|-------------------|
| Code spoofing | Spoofing | Unicode confusables, uppercase aliases, enums, or string-convertible objects impersonate a stable code | `type(code) is str`; exact ASCII allow-list; no normalization; constructor and conversion checks | Boundary matrix including `str` subclass, `Enum`, whitespace, uppercase, Unicode, empty, 65 chars. [VERIFIED: `.planning/phases/29-expected-domain-rejection/29-CONTEXT.md:27-31`] |
| Priority tampering | Tampering / Elevation of Privilege | Rejection is coerced to false and a lower-priority behavior executes | Return terminal result, never `None`; later-candidate sentinel remains untouched | Sync/async group test at guard, declarative, and permission seams. [VERIFIED: `.planning/REQUIREMENTS.md:30-35`] |
| Classification ambiguity | Repudiation | Expected rejection, defect, and cancellation collapse into one outcome | `rejection_code` + `cause=None`; defects retain cause; cancellation re-raises identical object after staged observer finalization | Three-way matrix and cancellation identity test. [VERIFIED: `src/fast_fsm/core.py:5318-5348`] [CITED: https://docs.python.org/3/library/asyncio-exceptions.html] |
| Payload disclosure | Information Disclosure | Exception message/object repr or caller payload leaks to result/log/trace | Fixed bounded error derived only from validated code; no repr/traceback; existing metadata-only trace; hostile-repr tests | `caplog`/record capture at DEBUG and TRACE; assert no warning, traceback, raw object, or invalid code. [VERIFIED: `tests/test_logging_config.py:359-480`, `tests/test_logging_config.py:805-940`] |
| Unbounded validation/work | Denial of Service | Oversized codes, group rescans, sorting, reflection, speculative async evaluation, or per-success allocation amplify work | Reject length >64 before pattern scan; one local candidate pass; no sort/copy/task fan-out; no new success carrier | AST selector gate, boundary length test, async sequential sentinel, benchmark regression. [VERIFIED: `tests/test_mypyc_guard.py:1943-2012`] |
| Observer multiplication | Denial of Service / Repudiation | Selector finalizes and trigger finalizes again; observer exception recurses or suppresses later observers | Construct only in selector; finalize once at public trigger; snapshot observer tuple; isolate `BaseException` | Exact observer-count tests with multiple/failing/reentrant observers; queries assert zero. [VERIFIED: `src/fast_fsm/core.py:3687-3709`, `tests/test_transition_lifecycle.py:578-666`] |
| Post-commit relabeling | Tampering / Repudiation | A lifecycle-raised signal is mislabeled uncommitted expected rejection | No outer rejection catch; existing stage/commit/history/cause path remains authoritative | Parameterize source-exit, destination-enter, declarative-handler, trigger, after stages. [VERIFIED: `src/fast_fsm/core.py:3711-4058`] |
| Cancellation swallowing | Denial of Service | `CancelledError` is caught by rejection/general exception path and the task cannot cancel | Catch `Exception`, never `BaseException`; retain dedicated cancellation boundary and bare raise | Existing event-handshake tests plus rejection adjacency. [VERIFIED: `tests/test_priority_selection.py:359-553`, `tests/test_transition_lifecycle.py:1166-1267`] |

## Performance and Fast-Path Risks

- A new trailing `TransitionResult` slot increases result instance size for all outcomes; this is the unavoidable locked public-model cost. Do not add a second boolean/status field or per-dispatch carrier. [VERIFIED: `.planning/phases/29-expected-domain-rejection/29-CONTEXT.md:33-38`]
- Rejection-code validation and error formatting must execute only when constructing/handling the signal. No regex match, code scan, or string formatting belongs on successful dispatch. [VERIFIED: `.planning/phases/29-expected-domain-rejection/29-CONTEXT.md:98-104`]
- Specific `except TransitionRejected` clauses add no success-path allocation. Keep direct singleton and group branches structurally unchanged: one source/trigger lookup, no `_transition_entries()`, `sorted()`, `list()`, `tuple()`, reflection, or task fan-out. [VERIFIED: `tests/test_mypyc_guard.py:1943-2012`]
- No rejection ContextVar or machine slot is needed; async metadata already exists task-locally for stage/priority/internal cancellation truth. [VERIFIED: `src/fast_fsm/core.py:82-103`, `src/fast_fsm/core.py:5290-5348`]
- Do not establish a new Phase 29 throughput floor. Run the existing singleton benchmark as a regression signal; Phase 32 owns installed-artifact and feature-local evidence. [VERIFIED: `.planning/ROADMAP.md:141-155`, `.github/copilot-instructions.md:51-58`]

## Sources

### Primary (HIGH confidence)

- `.planning/phases/29-expected-domain-rejection/29-CONTEXT.md` — locked public/semantic decisions and integration constraints.
- `.planning/REQUIREMENTS.md` — REJECT-01 through REJECT-09.
- `src/fast_fsm/core.py`, `core.pyi`, `conditions.py`, `__init__.py` — live selectors, result/error types, composition/deferred helpers, lifecycle, observers, query, cancellation, and export boundaries.
- `tests/test_priority_selection.py`, `test_transition_lifecycle.py`, `test_condition_interface.py`, `test_async.py`, `test_logging_config.py`, `test_mypyc_guard.py`, `test_release_evidence.py` — closest behavioral, safety, structural, and native patterns.
- `setup.py`, `pyproject.toml`, `Taskfile.yml`, `tools/release_evidence.py` — compilation, test, type, slots, and release-evidence authorities.
- `.github/copilot-instructions.md`, `AGENTS.md`, `.specify/memory/spr-core-api.md` — project constraints and living runtime contract.

### Secondary (MEDIUM confidence)

- [mypyc native classes](https://mypyc.readthedocs.io/en/stable/native_classes.html) — compiled/native defaults and explicit `native_class=False` boundary.
- [Python dataclasses](https://docs.python.org/3.13/library/dataclasses.html) — `compare=False`, repr default, and slots semantics.
- [Python asyncio exceptions](https://docs.python.org/3/library/asyncio-exceptions.html) — `CancelledError` hierarchy and re-raise guidance.
- [OWASP ASVS 5.0 input validation](https://cornucopia.owasp.org/taxonomy/asvs-5.0/02-validation-and-business-logic/02-input-validation) — positive allow-list and logical limit control.
- [OWASP ASVS 5.0 logging](https://cornucopia.owasp.org/taxonomy/asvs-5.0/16-security-logging-and-error-handling/02-general-logging) — sensitive-data-safe logging control.

### Tertiary (LOW confidence)

- None.

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — unchanged and repository-pinned. [VERIFIED: `pyproject.toml:1-43`, `uv.lock:991-1043`]
- Architecture: HIGH — all conversion/finalization/lifecycle seams were read directly in live source. [VERIFIED: `src/fast_fsm/core.py:2671-3384`, `src/fast_fsm/core.py:3631-4236`, `src/fast_fsm/core.py:4974-5348`]
- Pitfalls: HIGH — each maps to an existing catch boundary or active regression test. [VERIFIED: `tests/test_priority_selection.py:287-553`, `tests/test_priority_selection.py:670-1180`, `tests/test_transition_lifecycle.py:422-1310`]
- Native layout: HIGH for repository impact, MEDIUM for external mypyc guidance — local audit/tests establish the exact project constraint; official docs establish the supported non-native mechanism. [VERIFIED: `tools/release_evidence.py:128-140`, `tests/test_release_evidence.py:794-844`] [CITED: https://mypyc.readthedocs.io/en/stable/native_classes.html]

**Research date:** 2026-09-17
**Valid until:** 2026-10-17 (repository-local architecture is stable; re-check mypyc/Python docs if toolchain versions change)
