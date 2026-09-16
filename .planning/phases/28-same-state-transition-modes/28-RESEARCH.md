# Phase 28: Same-State Transition Modes - Research

**Researched:** 2026-09-16
**Domain:** High-performance flat-FSM transition topology, lifecycle specialization, timing, and sync/async parity
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

The following constraints are copied verbatim from the phase context. [VERIFIED: `.planning/phases/28-same-state-transition-modes/28-CONTEXT.md:14-46,110-117`]

### Locked Decisions

### Transition Mode Model
- **D-01:** `internal` is immutable metadata on each canonical transition entry, exposed as a keyword-only exact built-in boolean with a backward-compatible `False` default. It is not a machine-wide compatibility switch. — **Reversibility:** costly — changing ownership or default semantics later would alter registration signatures, immutable carrier layouts, and existing self-transition behavior.
- **D-02:** `internal=True` is valid only when every canonical source is the identical canonical target object. A multi-source request with any non-self expansion is rejected atomically before publication, and a final source remains invalid under Phase 27 even for an internal self-transition.
- **D-03:** Mode participates in immutable candidate identity. Re-registering an otherwise identical equal-priority candidate with a different mode is a semantic conflict, not an idempotent no-op.

### Lifecycle Boundary
- **D-04:** External self-transitions retain the complete existing order: resolution/timing/guards/permission; before-transition listeners; all source exit surfaces; commit/history with entry-time reset; all destination entry surfaces; declarative transition handler; trigger callbacks; after-transition listeners.
- **D-05:** Internal self-transitions retain resolution, timing, guards, state permission, before-transition listeners, one logical commit/history operation, declarative handler, trigger callbacks, after-transition listeners, result production, tracing, and failure observation.
- **D-06:** Internal self-transitions skip every state lifecycle surface together: `State.on_exit`, registered synchronous and asynchronous source-exit callbacks, exit-state listeners, `State.on_enter`, registered synchronous and asynchronous destination-entry callbacks, and enter-state listeners. The branch occurs once at the lifecycle seam after canonical selection; mode is never inferred from source/target equality.
- **D-07:** Direct-control APIs (`force_state`, `reset`, and `restore`) keep their existing external control lifecycle and do not gain an `internal` option. Internal mode belongs only to registered event transitions.

### Commit, Timing, and Observable Truth
- **D-08:** A successful internal transition is a real logical commit with `committed=True`, the same canonical source and destination, the selected priority, one optional history record, and explicit comparison-neutral `internal=True` metadata in `TransitionResult` and `TransitionRecord`. It is not a guard-only or action-only no-op.
- **D-09:** Internal commit preserves `_state_entered_at`. If history is disabled, it need not read the clock merely to reassign the same state; if history is enabled, the record timestamp describes event commit time without becoming a new entry epoch.
- **D-10:** External self-transition commit continues to reassign the canonical state and reset `_state_entered_at`; therefore `after=` and `within=` eligibility restart only on external re-entry. Repeated internal events cannot extend or restart a residency deadline.
- **D-11:** Mode metadata is observable without being injected into callback keyword arguments, avoiding collision with application payload. Existing callback positional and keyword conventions remain unchanged.

### Failure, Cancellation, and Machine Parity
- **D-12:** A failure in an internal before-transition listener is pre-commit and suppresses the commit, history, and all later work. Failures in retained declarative handlers, trigger callbacks, or after-transition listeners are post-commit and preserve state/history/mode truth exactly as for other transitions.
- **D-13:** Synchronous and asynchronous machines use the same selected mode, priority, stage, committed flag, result, history, and timing rules. Async exit/entry callbacks are skipped for internal transitions at the same lifecycle slots as their synchronous counterparts.
- **D-14:** Cancellation retains the established lifecycle-stage and commit-truth contract: cancellation before the internal commit is uncommitted; cancellation in retained post-commit work is committed; skipped state lifecycle stages cannot originate internal-transition failures or cancellation.
- **D-15:** Guard evaluation and priority fallthrough are mode-neutral. Internal and external candidates resolve in the existing deterministic priority order, and the mode of only the selected immutable entry controls execution.

### Construction Scope for This Phase
- **D-16:** Phase 28 adds the canonical `internal` scalar to `TransitionEntry`, `_TransitionRequest`, `_PreparedTransition`, selected dispatch state, graph transition snapshots, clone replay, and the primary direct/builder registration surfaces needed to author and execute the behavior. — **Reversibility:** costly — these private carrier layouts form the semantic spine consumed by later adapter, persistence, and diagnostic phases.
- **D-17:** Phase 30 remains responsible for proving and completing parity across every retained batch/factory/helper/declarative/deserialization adapter and dictionary round trip. Phase 28 must leave one canonical normalization and lifecycle seam for that fan-out rather than introducing adapter-specific behavior.

### the agent's Discretion

- Exact private helper names and whether the internal lifecycle is expressed as one specialized runner or a tightly bounded branch inside the existing runner, provided the default external path pays at most one predictable boolean branch.
- Additive constructor parameter ordering beyond the locked keyword-only public spelling, bounded error wording, test-file organization, and internal stage bookkeeping.
- Whether `TransitionResult` and `TransitionRecord` always store explicit `False` or use an equivalent comparison-neutral default representation, provided public truth, typing, and backward-compatible positional/equality behavior are preserved.

### Deferred Ideas (OUT OF SCOPE)

- Complete propagation through every retained construction adapter, declarative reconstruction path, clone/dictionary persistence contract, and builder-first deprecation guidance — Phase 30.
- Diagnostic validation facts, JSON projection, Mermaid, and PlantUML distinction between internal and external self-transitions — Phase 31.
- Progressive drone tutorial, public documentation, installed-wheel proof, and feature-local performance evidence — Phase 32.
- Expected domain rejection and priority-abort semantics — Phase 29.
- Targetless internal transitions, hierarchical descendant semantics, deferred event queues, and machine-wide mode switches remain outside the v0.5.0 flat-FSM scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

The requirement descriptions below are quoted verbatim from the milestone requirements. [VERIFIED: `.planning/REQUIREMENTS.md:17-24`]

| ID | Description | Research Support |
|----|-------------|------------------|
| MODE-01 | Users can select explicit internal transition semantics with `internal=True`, while omitted or false values retain existing external semantics. | Extend the immutable carrier chain, direct registrar, builder, result, record, stub, and structural/native tests. [VERIFIED: `.planning/phases/28-same-state-transition-modes/28-CONTEXT.md:17,28,40`]. |
| MODE-02 | Users can register internal transitions only when source and destination are the same state, with invalid registration rejected atomically. | Validate exact Boolean input and canonical identity inside `_normalize_transition_request()` before the existing prepare-all/publish-once commit. [VERIFIED: `src/fast_fsm/core.py:1823-1862,1954-1997`]. |
| MODE-03 | Users observe the complete exit-and-reentry lifecycle and reset state-entry timing for external self-transitions. | Preserve the current external runner and `_commit_transition()` behavior as the `False` path. [VERIFIED: `src/fast_fsm/core.py:3652-3868`; the exact current commit assignments are `"self._current_state = to_state"` and `"self._state_entered_at = timestamp"` at `src/fast_fsm/core.py:3572-3573`]. |
| MODE-04 | Users observe internal transitions without state exit or entry hooks and listeners, while non-state transition behavior, logical commit, results, history, and appropriate observers remain intact. | Branch once after selection into a dedicated internal runner that retains before/declarative/trigger/after/finalization and uses a dedicated logical-commit seam. [VERIFIED: `.planning/phases/28-same-state-transition-modes/28-CONTEXT.md:22-25,28,34`]. |
| MODE-05 | Users observe uninterrupted state-residency timing across internal transitions. | Preserve `_state_entered_at`; with history off, avoid the commit clock read; with history on, timestamp only the record. [VERIFIED: `.planning/phases/28-same-state-transition-modes/28-CONTEXT.md:29-30`; current timing reads `"elapsed = now - self._state_entered_at"` at `src/fast_fsm/core.py:2842-2846,4762-4766`]. |
| MODE-06 | Users receive equivalent internal and external transition behavior across synchronous and asynchronous machines, prioritized selection, cancellation, and failure handling. | Mirror the lifecycle branch in both runners, propagate candidate mode like priority, and retain the outer async cancellation finalizer and bare re-raise. [VERIFIED: `src/fast_fsm/core.py:4416-4652,4946-5015`; `.specify/decisions/ADR-004-atomic-transition-lifecycle.md:25-58`]. |
</phase_requirements>

## Summary

Phase 28 should be planned as a semantics-spine change inside `core.py`, not as an adapter or documentation sweep. The existing code already has the right boundaries: immutable transition carriers, canonical endpoint normalization, prepare-all/publish-once topology mutation, direct singleton versus local priority-group selection, a selected `_PreparedDispatch`, paired sync/async lifecycle runners, one no-user-code commit seam, and additive result/history metadata. [VERIFIED: `src/fast_fsm/core.py:614-644,686-712,759-837,1823-2038,2748-2868,3652-3868,4416-4652`].

The pivotal implementation detail is that `_commit_transition()` currently always reads the clock, optionally creates history, reassigns current state, and resets `_state_entered_at`. Reusing it unchanged would violate MODE-05. [VERIFIED: the exact current body is `"timestamp = self._read_clock()"`, optional `"history.append(record)"`, `"self._current_state = to_state"`, and `"self._state_entered_at = timestamp"` at `src/fast_fsm/core.py:3553-3573`]. The lowest-risk plan is therefore: carry `internal` through the canonical topology first; preserve the external runner and commit unchanged; then add a dedicated internal lifecycle/commit path whose history-disabled commit performs no clock read or state-entry assignment.

The other planning hotspot is cancellation truth. The async selector already carries the currently evaluated priority through the task-local `_async_selection_priority` so cancellation before selection completes can still be finalized accurately. Mode needs the same task-local treatment, or an equivalent closed scalar mechanism, so sync and async candidate-specific failures/cancellations do not lose `internal` truth. [VERIFIED: `_async_selection_priority` is declared and defaults to `None` at `src/fast_fsm/core.py:90-95`; it is read during cancellation at `src/fast_fsm/core.py:4991-5009`].

**Primary recommendation:** implement immutable mode propagation and exact canonical validation first, then a dedicated internal runner/commit path with one external-path branch, then the sync/async lifecycle, timing, failure, cancellation, slots, typing, and native-parity oracle. [VERIFIED: `.planning/phases/28-same-state-transition-modes/28-CONTEXT.md:16-46,88-99`].

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Public `internal=` authoring and exact validation | API / Backend library | — | `StateMachine.add_transition()` and `FSMBuilder.add_transition()` own the public boundary; adapters must converge on canonical normalization. [VERIFIED: `src/fast_fsm/core.py:2040-2091,5764-5839`]. |
| Immutable mode topology and candidate identity | Database / in-process storage | API / Backend library | `TransitionEntry` or `_TransitionGroup` is the authoritative stored slot, and `_merge_transition_slot()` decides duplicate/conflict identity before publication. [VERIFIED: `src/fast_fsm/core.py:614-644,686-712,1999-2038`]. |
| Candidate selection | API / Backend library | Database / in-process storage | Selectors read one source/trigger slot and return one `_PreparedDispatch`; mode must not change guard order or fallthrough. [VERIFIED: `src/fast_fsm/core.py:2748-2826`; locked D-15 at `.planning/phases/28-same-state-transition-modes/28-CONTEXT.md:37`]. |
| Internal versus external lifecycle | API / Backend library | — | The execution runners own callback ordering, stage truth, and the single specialization branch. [VERIFIED: `src/fast_fsm/core.py:3652-3868,4416-4652`]. |
| Logical commit, residency time, and history | API / Backend library | Database / in-process storage | Commit owns state/history coherence; the internal variant must timestamp only history and preserve entry epoch. [VERIFIED: `src/fast_fsm/core.py:3553-3573`; locked D-08–D-10 at `.planning/phases/28-same-state-transition-modes/28-CONTEXT.md:28-30`]. |
| Results, failure, and cancellation | API / Backend library | — | Public results and the outer async boundary own truthful mode/stage/commit/cause observation. [VERIFIED: `src/fast_fsm/core.py:547-581,3575-3650,4909-5015`]. |
| Browser / Frontend / CDN | — | — | No browser, SSR, or static-delivery capability exists in this Python library phase. [VERIFIED: phase boundary `.planning/phases/28-same-state-transition-modes/28-CONTEXT.md:7-9`]. |

## Project Constraints (from AGENTS.md)

- Use `uv` for every Python/package/test command; do not call `python`, `pip`, or `python -m pytest` directly. [VERIFIED: `.github/copilot-instructions.md:36-38`].
- All hot-path production classes remain slotted; the authoritative audit command is `uv run python tools/release_evidence.py slots-policy --json`. [VERIFIED: `.github/copilot-instructions.md:40-50`].
- Keep direct singleton lookup/dispatch O(1), candidate-group work local O(k), and do not add unrelated scans, dispatch-time sorting, reflection, or per-dispatch context allocation. [VERIFIED: `.github/copilot-instructions.md:51-58`; `.specify/decisions/ADR-007-priority-topology.md:31-45`].
- Preserve every condition and callback `*args, **kwargs` convention and do not inject mode into application kwargs. [VERIFIED: `.github/copilot-instructions.md:60-63`; locked D-11 at `.planning/phases/28-same-state-transition-modes/28-CONTEXT.md:31`].
- Keep `core.py` as the only mypyc compilation unit; `conditions.py` and `condition_templates.py` remain interpreted. [VERIFIED: `.github/copilot-instructions.md:318-336`; `.specify/memory/constitution.md:92-109`].
- Run targeted tests during implementation, the full sequential suite once before merge, blocking mypy, advisory ty, Ruff format/check, and the slots audit. [VERIFIED: `.github/copilot-instructions.md:65-71,108-119,237-264,318-334`].
- Use Beads for task tracking and do not create Markdown TODO/task lists. `bd ready --json` currently cannot open the database because its configured Dolt port is occupied; execution must repair that environment before claiming/closing the Phase 28 item. [VERIFIED: `AGENTS.md:19-21,74-99`; local `bd ready --json` on 2026-09-16].
- Public narrative/tutorial and installed release evidence remain Phase 32 work per the explicit phase boundary. Phase 28 should update code docstrings and `core.pyi` needed for an accurate API, but must not pull README/Sphinx tutorial or installed-wheel evidence forward. [VERIFIED: `.planning/phases/28-same-state-transition-modes/28-CONTEXT.md:9,113-117`; user-provided Phase 32 boundary].

## Standard Stack

### Core

| Library / Runtime | Version | Purpose | Why Standard |
|-------------------|---------|---------|--------------|
| Python | Project contract `>=3.10`; local `3.12.10` | Runtime, dataclasses, asyncio, monotonic timing | The package declares `requires-python = ">=3.10"`; the active uv environment reports Python 3.12.10. [VERIFIED: `pyproject.toml:1-9`; local `uv run python --version` on 2026-09-16]. |
| Fast FSM core | `0.4.0` source baseline | Transition topology, selection, lifecycle, history, timing | Phase 28 changes the existing semantic spine in `src/fast_fsm/core.py`; no second runtime layer is appropriate. [VERIFIED: `pyproject.toml:1-4`; `.planning/phases/28-same-state-transition-modes/28-CONTEXT.md:79-99`]. |
| `mypy-extensions` | Declared `>=1.0` | Existing `@mypyc_attr` compilation annotations | It is the sole runtime dependency and already imported by core; Phase 28 adds no dependency. [VERIFIED: `pyproject.toml:7-9`; `src/fast_fsm/core.py:35-38`]. |

### Supporting

| Library / Tool | Version | Purpose | When to Use |
|----------------|---------|---------|-------------|
| uv | `0.12.12` local | Locked environment and all Python commands | Every test, typecheck, build, and audit command. [VERIFIED: local `uv --version` on 2026-09-16; `.github/copilot-instructions.md:36-38`]. |
| pytest | Declared `>=8.4.1`; local `8.4.1` | Behavioral, structural, and regression tests | Targeted per task and full suite at phase gate. [VERIFIED: `pyproject.toml:11-20,54-70`; local `uv run pytest --version` on 2026-09-16]. |
| pytest-asyncio | Declared `>=1.3.0`; local `1.3.0` | Async lifecycle and deterministic cancellation tests | MODE-06 parity and cancellation matrices. [VERIFIED: `pyproject.toml:11-20,70`; local uv import on 2026-09-16]. |
| mypy / mypyc | Declared `>=1.17`; local `1.17.1` compiled | Blocking typing and native compatibility | After each carrier/stub slice and at final native gate. [VERIFIED: `pyproject.toml:11-26,41-43`; local `uv run mypy --version` on 2026-09-16]. |
| Ruff | Declared `>=0.12.11`; local `0.12.11` | Formatting and linting | Changed Python files before merge. [VERIFIED: `pyproject.toml:11-20`; local `uv run ruff --version` on 2026-09-16]. |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Exact per-entry Boolean | Enum, strategy object, machine-wide switch | Rejected by locked D-01 and the one-branch hot-path constraint; it widens storage/dispatch without additional valid states. [VERIFIED: `.planning/phases/28-same-state-transition-modes/28-CONTEXT.md:17,44`; `.planning/research/ARCHITECTURE.md:634-643`]. |
| Dedicated internal commit | Reuse `_commit_transition()` unchanged | Rejected because the current helper always reads the clock and resets entry epoch. [VERIFIED: `src/fast_fsm/core.py:3553-3573`; locked D-09 at `.planning/phases/28-same-state-transition-modes/28-CONTEXT.md:29`]. |
| One selected-entry lifecycle branch | Infer mode from `source is target` | Rejected because a single state may have both external and internal self-events. [VERIFIED: locked D-06 and D-15 at `.planning/phases/28-same-state-transition-modes/28-CONTEXT.md:24,37`]. |

**Installation:** no new package installation is planned. Refresh the existing locked environment only with `uv sync --locked --all-groups`. [VERIFIED: `.github/copilot-instructions.md:73-78`; `.planning/REQUIREMENTS.md:92` quotes `"New runtime dependencies or compiler upgrades solely for these features"` as out of scope].

**Version verification:** `uv lock --check` resolved the existing 76-package lock successfully on 2026-09-16. Registry publish-date verification is not applicable because Phase 28 adds no package. [VERIFIED: local `uv lock --check`; `pyproject.toml:1-43`].

## Package Legitimacy Audit

Not triggered. Phase 28 installs no external package and retains the existing dependency boundary. [VERIFIED: `.planning/REQUIREMENTS.md:92`; `pyproject.toml:7-9`].

**Packages removed due to SLOP verdict:** none.
**Packages flagged as suspicious SUS:** none.

## Architecture Patterns

### System Architecture Diagram

```text
StateMachine.add_transition(..., internal=...) / FSMBuilder.add_transition(...)
                                  |
                                  v
                  immutable _TransitionRequest tuple
                                  |
                                  v
          exact bool validation + canonical endpoint resolution
                                  |
                  +---------------+----------------+
                  | final source / non-self internal|
                  | invalid -> bounded error         |
                  +---------------+----------------+
                                  v
                    _PreparedTransition tuple
                                  |
                                  v
             off-table local merge (mode in identity)
                                  |
                                  v
            publish all changed slots once + version
                                  |
                                  v
    trigger / trigger_async -> direct singleton OR local priority group
                                  |
            timing -> guards -> permission -> _PreparedDispatch
                                  |
                     branch on entry.internal
                         /                    \
                        v                      v
        existing external lifecycle     internal lifecycle
        exit -> external commit -> entry before -> logical commit
                        \                      /
                         v                    v
             declarative -> trigger callbacks -> after
                                  |
                                  v
                TransitionResult + optional history

External services: none. Diagnostics/serialization fan-out is deferred to Phases 30-31.
```

The flow above follows the existing registrar, selector, and lifecycle boundaries; the only new dispatch decision is the selected entry mode. [VERIFIED: `src/fast_fsm/core.py:1954-2038,2748-2868,3652-3868`; locked D-06 at `.planning/phases/28-same-state-transition-modes/28-CONTEXT.md:24`].

### Recommended Project Structure

```text
src/fast_fsm/
├── core.py                    # carriers, canonical validation, sync/async lifecycle
└── core.pyi                   # additive public parameter/result/history typing
tests/
├── test_transition_modes.py   # new MODE-01..06 behavioral oracle
├── test_graph_invariants.py   # atomicity, identity, graph snapshot, clone
├── test_transition_timing.py  # deterministic residency-clock proof
├── test_transition_lifecycle.py # ordered hooks, failure, cancellation
├── test_priority_selection.py # mixed-mode candidate selection
├── test_builder.py            # immutable staging and repairability
├── test_async.py              # machine-type parity
└── test_mypyc_guard.py        # slots, field order, stubs, native semantic probe
```

This is a planning allocation: the source and adjacent test files exist today except the recommended new `tests/test_transition_modes.py`, which is a Wave 0 gap. [VERIFIED: codebase `rg --files tests` and source files opened on 2026-09-16].

### Pattern 1: Canonical Scalar Propagation

**What:** append `internal` with a `False` default to `TransitionEntry`, `_TransitionRequest`, `_PreparedTransition`, `_GraphTransition`, clone replay, direct registration, builder staging/replay, results, history, and public stubs. `_PreparedDispatch.entry.internal` is already the selected scalar, so do not add a redundant field unless mypyc evidence requires it. [VERIFIED: current carrier definitions at `src/fast_fsm/core.py:614-644,722-837`; locked D-16 at `.planning/phases/28-same-state-transition-modes/28-CONTEXT.md:40`].

**When to use:** every canonical construction and selected execution path in this phase; defer tuple-row, decorator, dictionary, and every legacy adapter's public authoring contract to Phase 30. [VERIFIED: locked D-16–D-17 at `.planning/phases/28-same-state-transition-modes/28-CONTEXT.md:40-41`].

**Example (illustrative; private helper and error text remain discretionary):**

```python
# Source contract: 28-CONTEXT D-01, D-02, D-16.
if type(internal) is not bool:
    raise TypeError(_BOUNDED_INTERNAL_TYPE_ERROR)

target = self._resolve_canonical_state(to_state, role="target")
if internal and any(source is not target for source in sources):
    raise ValueError(_BOUNDED_INTERNAL_TARGET_ERROR)
```

The identity check must follow canonical resolution, and the prepared tuple must still be fully built before `_commit_transition_plan()` publishes anything. [VERIFIED: current resolve/prepare/publish order at `src/fast_fsm/core.py:1850-1862,1918-1952,1977-1997`; locked D-02 at `.planning/phases/28-same-state-transition-modes/28-CONTEXT.md:18`].

### Pattern 2: Mode in Candidate Identity

**What:** include `entry.internal == candidate.internal` in the exact-duplicate branch. Same priority plus different mode must take the existing conflict path; same complete identity remains version-neutral. [VERIFIED: current exact duplicate predicate and conflict at `src/fast_fsm/core.py:2018-2031`; locked D-03 at `.planning/phases/28-same-state-transition-modes/28-CONTEXT.md:19`].

**When to use:** only during off-table registration merge. Selection order stays based solely on existing priority. [VERIFIED: `.specify/decisions/ADR-007-priority-topology.md:26-38`; locked D-15 at `.planning/phases/28-same-state-transition-modes/28-CONTEXT.md:37`].

### Pattern 3: Dedicated Internal Lifecycle and Commit

**What:** preserve the external lifecycle body and `_commit_transition()` unchanged. Add one predictable `if prepared.entry.internal` branch after selection that routes to a specialized internal runner. Its logical commit appends history only when enabled and never reassigns current state or `_state_entered_at`. [VERIFIED: locked D-04–D-10 and discretion at `.planning/phases/28-same-state-transition-modes/28-CONTEXT.md:22-30,44`].

**Why this shape:** it charges the default external path one branch, keeps all six skipped state surfaces together, and prevents an accidental clock reset. [VERIFIED: locked D-06 and discretion at `.planning/phases/28-same-state-transition-modes/28-CONTEXT.md:24,44`].

**Example (illustrative skeleton):**

```python
# Source contract: 28-CONTEXT D-08 and D-09.
def _commit_internal_transition(old_state, to_state, trigger, *, priority):
    history = self._history
    if history is None:
        return  # no state reassignment and no clock read
    timestamp = self._read_clock()
    record = TransitionRecord(
        old_state.name,
        trigger,
        to_state.name,
        timestamp,
        priority,
        internal=True,
    )
    history.append(record)
```

The helper must construct/read before append so a clock or record failure remains an uncommitted `"commit"` failure, matching the accepted atomic lifecycle contract. [VERIFIED: the exact stage value `"commit"` is defined at `src/fast_fsm/core.py:102-116`; `.specify/decisions/ADR-004-atomic-transition-lifecycle.md:37-58`].

### Pattern 4: Additive, Comparison-Neutral Observation

**What:** append `internal` after all existing public positional/default fields. `TransitionResult` should use a defaulted `compare=False` field; `TransitionRecord` should add a trailing slot and trailing defaulted constructor parameter. Preserve the first five result fields verbatim: `"success", "from_state", "to_state", "trigger", "error"`. [VERIFIED: `src/fast_fsm/core.py:546-561`; structural guard at `tests/test_mypyc_guard.py:1870-1899`; locked D-08 at `.planning/phases/28-same-state-transition-modes/28-CONTEXT.md:28`].

Python 3.10 dataclasses support `slots=True`, defaulted fields, and excluding a field from generated equality with `compare=False`. [CITED: https://docs.python.org/3.10/library/dataclasses.html].

Candidate-specific sync failures and async cancellation finalization should propagate evaluated/selected mode alongside priority; missing resolution and exhausted groups retain the default because no entry was selected. This matches the existing priority metadata pattern and the locked sync/async failure/cancellation parity. [VERIFIED: current priority propagation at `src/fast_fsm/core.py:2778-2920,4760-4826,4962-5009`; locked D-13–D-15 at `.planning/phases/28-same-state-transition-modes/28-CONTEXT.md:35-37`].

### Pattern 5: Preserve the Outer Cancellation Boundary

**What:** do not catch cancellation in the new internal runner. Pass the same mutable `lifecycle_stage` and `committed` cells through it; update `committed[0]` immediately after the internal logical commit. Add task-local mode bookkeeping equivalent to `_async_selection_priority` so guard-time cancellation remains truthful before `_PreparedDispatch` returns. [VERIFIED: `src/fast_fsm/core.py:4416-4425,4517-4530,4946-5015`; locked D-14 at `.planning/phases/28-same-state-transition-modes/28-CONTEXT.md:36`].

Python documents `asyncio.CancelledError` as a `BaseException` that should normally be re-raised after cleanup; keep the existing bare `raise`. [CITED: https://docs.python.org/3.10/library/asyncio-exceptions.html].

### Anti-Patterns to Avoid

- **Branching on `old_state is to_state`:** equality describes graph shape, not lifecycle intent; it would make external self-transition impossible. [VERIFIED: locked D-06 at `.planning/phases/28-same-state-transition-modes/28-CONTEXT.md:24`].
- **Sprinkling mode checks around each hook list:** it risks skipping only some state surfaces and adds multiple branches to the default path. Use one specialized internal runner. [VERIFIED: locked D-06 and discretion at `.planning/phases/28-same-state-transition-modes/28-CONTEXT.md:24,44`].
- **Reusing `_commit_transition()` unchanged:** it resets residency and always reads the clock. [VERIFIED: `src/fast_fsm/core.py:3553-3573`].
- **Adding mode to callback kwargs:** it can collide with caller payload and breaks the locked callback contract. [VERIFIED: locked D-11 at `.planning/phases/28-same-state-transition-modes/28-CONTEXT.md:31`].
- **Extending dictionary/decorator/diagram/tutorial contracts now:** those are explicitly owned by Phases 30-32. [VERIFIED: `.planning/phases/28-same-state-transition-modes/28-CONTEXT.md:9,41,113-117`].

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Transition mode model | Public enum, strategy hierarchy, global compatibility flag | Exact built-in `bool` on `TransitionEntry` | The closed domain has two values and is already locked per edge. [VERIFIED: `.planning/phases/28-same-state-transition-modes/28-CONTEXT.md:17`]. |
| Atomic registration | New internal-only registrar | Existing `_TransitionRequest` → `_normalize_transition_request()` → `_commit_transition_plan()` transaction | It already prepares every request before one publication. [VERIFIED: `src/fast_fsm/core.py:1954-1997`]. |
| Selected mode transport | Re-resolve source/target in lifecycle | `prepared.entry.internal` | `_PreparedDispatch` already retains the selected canonical entry. [VERIFIED: `src/fast_fsm/core.py:827-837,2868-2876`]. |
| Residency timing | New timer or deadline store | Existing `_state_entered_at` and injected monotonic clock | Timing windows already subtract one entry epoch; internal mode only preserves it. [VERIFIED: `src/fast_fsm/core.py:1027-1032,2842-2846,4762-4766`]. |
| Failure observation | New internal-transition observer family | Existing staged result and `_finalize_failure()` | Exactly-once failure observation is already accepted architecture. [VERIFIED: `.specify/decisions/ADR-004-atomic-transition-lifecycle.md:48-58`]. |
| Async cancellation | Shielding, compensation, local swallow, secondary finalizer | Existing outer cancellation finalizer and bare re-raise | Current ownership and commit truth depend on that single boundary. [VERIFIED: `src/fast_fsm/core.py:4991-5015`]. |

**Key insight:** this feature is new immutable data plus one execution specialization; introducing new public abstractions would widen the API and hot path without solving an additional requirement. [VERIFIED: `.planning/research/ARCHITECTURE.md:273-311,668-678`].

## Common Pitfalls

### Pitfall 1: Internal Becomes a No-op

**What goes wrong:** guard succeeds but there is no history, committed result, declarative handler, trigger callback, after listener, trace attempt, or failure finalization. [VERIFIED: required retained surfaces in `.planning/phases/28-same-state-transition-modes/28-CONTEXT.md:23,28,34`].

**How to avoid:** give internal transitions a real logical commit and reuse the retained transition-level suffix. Test result/history and every retained callback explicitly.

**Warning signs:** `committed=False` on success, empty history when enabled, or internal code returns immediately after selection.

### Pitfall 2: Partial State-Lifecycle Suppression

**What goes wrong:** `State.on_exit` is skipped but registered exit callbacks, async exit callbacks, exit listeners, entry hooks, or entry listeners still run. [VERIFIED: the six skipped families are quoted in locked D-06 at `.planning/phases/28-same-state-transition-modes/28-CONTEXT.md:24`].

**How to avoid:** one specialized runner and sentinel callbacks that would fail the test if any skipped surface executes.

### Pitfall 3: Internal Commit Resets Residency

**What goes wrong:** `_commit_transition()` resets `_state_entered_at`, making repeated internal refreshes restart `after=` and `within=` windows. [VERIFIED: current reset at `src/fast_fsm/core.py:3572-3573`; locked prohibition at `.planning/phases/28-same-state-transition-modes/28-CONTEXT.md:29-30`].

**How to avoid:** separate internal commit; use deterministic `FakeClock` tests and assert history timestamp changes while entry epoch does not. Python's monotonic clock is unaffected by system clock updates and only differences are meaningful. [CITED: https://docs.python.org/3.10/library/time.html].

### Pitfall 4: Mode Is Missing From Duplicate Identity or Clone

**What goes wrong:** different modes at equal priority collapse as duplicates, or a clone silently becomes external. [VERIFIED: locked D-03 and D-16 at `.planning/phases/28-same-state-transition-modes/28-CONTEXT.md:19,40`].

**How to avoid:** include mode in `_merge_transition_slot()` equality and every clone/request replay; compare graph fingerprints and independent slot identity after clone.

### Pitfall 5: External Self-Transition Regresses

**What goes wrong:** a broad refactor suppresses existing exit/entry hooks or stops resetting the clock for the default `False` mode. [VERIFIED: locked D-04 and D-10 at `.planning/phases/28-same-state-transition-modes/28-CONTEXT.md:22,30`].

**How to avoid:** keep the external runner and commit body structurally unchanged; add an exact ordered external-self oracle before implementing internal behavior.

### Pitfall 6: Async Cancellation Loses Mode or Leaks Ownership

**What goes wrong:** cancellation in an internal guard or retained async declarative handler reports the wrong commit/mode, skips failure observation, or leaves the machine busy. [VERIFIED: locked D-13–D-14 at `.planning/phases/28-same-state-transition-modes/28-CONTEXT.md:35-36`; current release occurs in `finally` at `src/fast_fsm/core.py:4941-4944`].

**How to avoid:** event/barrier handshakes, task-local mode bookkeeping, one observer pass, identical cancellation re-raise identity, and a successful reuse trigger after cancellation.

### Pitfall 7: Additive Fields Break Compatibility or mypyc

**What goes wrong:** inserting a required field changes positional construction/equality, or a hot-path class loses slots/native field declaration. [VERIFIED: existing structural contracts at `src/fast_fsm/core.py:546-561,584-605`; `tests/test_mypyc_guard.py:1870-1899,2028-2068`].

**How to avoid:** append defaulted fields, use `compare=False` for `TransitionResult`, update `core.pyi`, AST/slots tests, strict consumer typing, and the pure/native semantic probe together.

### Pitfall 8: Phase Boundary Creep

**What goes wrong:** tuple schemas, dictionary round trips, diagrams, public tutorials, expected rejection, or installed-wheel benchmarks expand the phase and duplicate later work. [VERIFIED: `.planning/phases/28-same-state-transition-modes/28-CONTEXT.md:9,41,113-117`].

**How to avoid:** land only the canonical scalar, primary direct/builder authoring, graph snapshot/clone continuity, runtime semantics, result/history, typing, and source/native proof needed for MODE-01..06.

## Code Examples

Verified planning patterns from the current source and locked phase contract:

### One Default-Path Branch

```python
# Illustrative only; helper naming is delegated by 28-CONTEXT.
def _execute_transition(self, prepared, kwargs):
    if prepared.entry.internal:
        return self._execute_internal_transition(prepared, kwargs)
    # Existing external body remains the compatibility path.
```

This is the prescriptive shape because the existing sync runner already receives `_PreparedDispatch`, while `_PreparedDispatch` contains `entry`. [VERIFIED: `src/fast_fsm/core.py:827-837,3652-3667`; `.planning/phases/28-same-state-transition-modes/28-CONTEXT.md:24,44`].

### Candidate Identity Extension

```python
# Existing predicate plus one locked identity scalar.
if (
    entry.to_state is candidate.to_state
    and entry.condition is candidate.condition
    and entry.condition_ref == candidate.condition_ref
    and entry.after == candidate.after
    and entry.within == candidate.within
    and entry.internal == candidate.internal
):
    return existing
```

The first five comparisons are the current exact predicate; `internal` is the locked addition. [VERIFIED: `src/fast_fsm/core.py:2018-2028`; `.planning/phases/28-same-state-transition-modes/28-CONTEXT.md:19`].

### Deterministic Residency Oracle

```python
# Planning test shape, using the existing FakeClock pattern.
clock.now = 2
result = machine.trigger("refresh_internal")
assert result.internal is True
assert machine._state_entered_at == 0
assert machine.history[-1].timestamp == 2

clock.now = 3
assert machine.can_trigger("after_three_seconds")
```

The existing test clock has exact fields `"calls"` and `"now"`, and current timing is half-open and observational. [VERIFIED: `tests/test_transition_timing.py:21-30,51-61`; locked D-09–D-10 at `.planning/phases/28-same-state-transition-modes/28-CONTEXT.md:29-30`].

### Async Cancellation Oracle

```python
pending = asyncio.create_task(machine.trigger_async("refresh_internal"))
await asyncio.wait_for(started.wait(), timeout=5)
pending.cancel()
with pytest.raises(asyncio.CancelledError):
    await asyncio.wait_for(pending, timeout=5)

assert machine._async_owner_task is None
assert not machine._async_ownership_lock.locked()
```

Use event handshakes, never sleeps; the existing cancellation tests use this exact pattern and exact ownership assertions. [VERIFIED: `tests/test_transition_lifecycle.py:1166-1267`; `.planning/phases/28-same-state-transition-modes/28-CONTEXT.md:93`].

## State of the Art

| Old / Current Approach | Phase 28 Approach | When Changed | Impact |
|------------------------|-------------------|--------------|--------|
| Same-state transitions always use the ordinary external lifecycle; no `internal` field exists in current `TransitionEntry`, result, record, request, prepared, graph, or stub shapes. | Exact per-transition `internal=False` default with canonical self-only validation. | Phase 28 | Existing callers retain external behavior; new callers opt into in-state logical commits. [VERIFIED: current fields at `src/fast_fsm/core.py:547-644,722-837`; locked D-01–D-02]. |
| `_commit_transition()` always reads the clock and resets entry time. | External commit unchanged; internal commit records event time only when history is enabled and preserves entry epoch. | Phase 28 | `after=` / `within=` remain residency-relative across internal events. [VERIFIED: `src/fast_fsm/core.py:3553-3573`; locked D-09–D-10]. |
| Async cancellation carries stage and candidate priority through task-local bookkeeping. | Carry mode through the equivalent task-local/candidate result path. | Phase 28 | MODE-06 can assert matching failure/cancellation truth. [VERIFIED: `src/fast_fsm/core.py:82-95,4962-5015`; locked D-13–D-14]. |
| Full adapter/dictionary/diagnostic/tutorial parity is not yet present. | Leave settled scalar seams for later fan-out. | Phases 30-32 | Avoids duplicated adapter logic and premature output contracts. [VERIFIED: `.planning/phases/28-same-state-transition-modes/28-CONTEXT.md:40-41,113-117`]. |

**Deprecated/outdated:** treating equal source/target identity as sufficient to infer lifecycle mode is explicitly invalid for v0.5.0. [VERIFIED: locked D-06 at `.planning/phases/28-same-state-transition-modes/28-CONTEXT.md:24`].

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| — | No low-confidence assumptions were used; recommendations are derived from locked context, opened source-of-truth files, active tests, or official Python documentation. | All | — |

## Open Questions

No user decision blocks planning. The only undecided items are explicitly delegated: private helper names, bounded error wording, test-file organization, internal stage bookkeeping, and explicit-`False` representation details. [VERIFIED: `.planning/phases/28-same-state-transition-modes/28-CONTEXT.md:43-46`].

**Research recommendation for those discretion areas:** use a specialized internal runner and dedicated internal commit; append explicit `False` default fields; use bounded messages that mention `internal` and canonical self-target without echoing objects; centralize new tests in `tests/test_transition_modes.py` with structural/native extensions in existing files. [VERIFIED: this follows locked D-01–D-16 and the existing source/test seams cited above].

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| uv | All Python/test/build commands | ✓ | `0.12.12` | None permitted by project workflow. [VERIFIED: local probe; `.github/copilot-instructions.md:36-38`]. |
| Python | Runtime and tests | ✓ | `3.12.10` local; project `>=3.10` | Supported matrix covers Python 3.10+. [VERIFIED: local probe; `pyproject.toml:6`]. |
| pytest / pytest-asyncio | Validation | ✓ | `8.4.1` / `1.3.0` | None needed. [VERIFIED: local uv probes; `pyproject.toml:15-17`]. |
| mypy / mypyc | Typing and native boundary | ✓ | `1.17.1` | None; blocking authority. [VERIFIED: local uv probe; `pyproject.toml:14,25,42`]. |
| Ruff | Formatting/linting | ✓ | `0.12.11` | None needed. [VERIFIED: local uv probe; `pyproject.toml:19`]. |
| Task | Project quality commands | ✓ | `3.53.1` | Direct documented uv commands where a task wrapper is unnecessary. [VERIFIED: local `task --version`; `.github/copilot-instructions.md:27`]. |
| Apple Clang | Fresh native extension build | ✓ | `21.0.0` | Pure-source tests still run, but native parity remains a phase gate. [VERIFIED: local `clang --version`; `.github/copilot-instructions.md:318-336`]. |
| Beads/Dolt database | Required project tracking | ✗ | CLI present; configured DB unavailable | No alternate tracker is allowed; repair the occupied Dolt port before execution. [VERIFIED: local `bd ready --json`; `AGENTS.md:19-21,91-99`]. |

**Missing dependencies with no fallback:** Beads database connectivity blocks the required claim/update/close workflow until its local Dolt port conflict is resolved. [VERIFIED: local `bd ready --json` on 2026-09-16].

**Missing dependencies with fallback:** none.

## Validation Architecture

Nyquist validation is enabled: the exact configuration value is `"nyquist_validation": true`. [VERIFIED: `.planning/config.json:15-20`].

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest `8.4.1` with pytest-asyncio `1.3.0`. [VERIFIED: local uv probes; `pyproject.toml:15-17`]. |
| Config file | `pyproject.toml`; exact discovery values are `"testpaths = [\"tests\"]"`, `"python_files = [\"test_*.py\"]"`, `"python_classes = [\"Test*\"]"`, `"python_functions = [\"test_*\"]"`, and `"asyncio_mode = \"auto\""`. [VERIFIED: `pyproject.toml:54-70`]. |
| Quick run command | `uv run pytest tests/test_transition_modes.py -x -q` (new Wave 0 file). |
| Adjacent regression command | `uv run pytest tests/test_transition_modes.py tests/test_transition_lifecycle.py tests/test_transition_timing.py tests/test_priority_selection.py tests/test_graph_invariants.py tests/test_builder.py tests/test_async.py -x -q`. |
| Full suite command | `uv run pytest tests/ -x -q`. [VERIFIED: `.github/copilot-instructions.md:65-71,237-246`]. |
| Current adjacent baseline | Existing lifecycle/timing/priority/graph/builder/async suite passes under uv on 2026-09-16. [VERIFIED: local targeted pytest run]. |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MODE-01 | Exact keyword-only bool, default external, carrier/stub/result/history shape | Unit + structural + typing | `uv run pytest tests/test_transition_modes.py tests/test_mypyc_guard.py -x -q` | ❌ `test_transition_modes.py` Wave 0; ✅ structural file |
| MODE-02 | Canonical same-object validation, final-source precedence, multi-source/batch atomicity, mode identity | Unit + property/invariant | `uv run pytest tests/test_transition_modes.py tests/test_graph_invariants.py tests/test_hypothesis.py -x -q` | ❌ central oracle Wave 0; ✅ adjacent files |
| MODE-03 | External self full ordered lifecycle and entry-time reset | Integration/unit | `uv run pytest tests/test_transition_modes.py tests/test_transition_lifecycle.py tests/test_transition_timing.py -x -q` | ❌ central oracle Wave 0; ✅ adjacent files |
| MODE-04 | Internal skipped state surfaces, retained transition surfaces, logical commit, result/history/failure observer | Integration/unit | `uv run pytest tests/test_transition_modes.py tests/test_transition_lifecycle.py -x -q` | ❌ central oracle Wave 0; ✅ adjacent file |
| MODE-05 | Preserved residency, history event timestamp, no clock read when history disabled | Deterministic unit | `uv run pytest tests/test_transition_modes.py tests/test_transition_timing.py -x -q` | ❌ central oracle Wave 0; ✅ adjacent file |
| MODE-06 | Sync/async parity, mixed-mode priorities, candidate failures, pre/post-commit cancellation, reuse | Async integration + native probe | `uv run pytest tests/test_transition_modes.py tests/test_priority_selection.py tests/test_async.py tests/test_transition_lifecycle.py tests/test_mypyc_guard.py -x -q` | ❌ central/native additions Wave 0; ✅ adjacent files |

### Required Validation Matrices

1. **Construction matrix:** direct and builder `False`/omitted/`True`; invalid exact-bool values; canonical string/object endpoints; final self; mixed multi-source; duplicate same mode; equal-priority different mode; graph version/topology/cache unchanged on failure. [VERIFIED: locked D-01–D-03, D-16; existing invariant patterns at `tests/test_graph_invariants.py:628-674,694-827`; builder repair pattern at `tests/test_builder.py:243-285`].
2. **Lifecycle matrix:** external self visits every established state and transition surface; internal visits only before, commit/history, declarative, trigger, after, result, trace, and failure observer. The exact lifecycle stage catalog is `"resolution", "selection", "guard", "state-permission", "before-transition", "source-exit", "source-exit-callback", "exit-state-listener", "commit", "destination-enter", "destination-enter-callback", "enter-state-listener", "declarative-handler", "trigger-callback", "after-transition"`. [VERIFIED: `src/fast_fsm/core.py:98-133`; `tests/test_transition_lifecycle.py:168-186,832-931`].
3. **Failure matrix:** internal before-listener and commit failures are uncommitted; declarative/trigger/after failures are committed, mode-true, history-retaining, suffix-stopping, and finalized once. Skipped exit/entry surfaces cannot be failure origins. [VERIFIED: locked D-12 at `.planning/phases/28-same-state-transition-modes/28-CONTEXT.md:34`; current stage matrix pattern at `tests/test_transition_lifecycle.py:934-1053`].
4. **Timing matrix:** untimed internal with history disabled makes no selection/commit clock read; history-enabled internal records event time but preserves entry time; external self resets entry time; repeated internal events do not extend `after` or `within`. [VERIFIED: locked D-09–D-10; current clock assertions at `tests/test_transition_timing.py:51-98,188-213,255-307`].
5. **Async matrix:** guard cancellation before commit, retained async declarative cancellation after internal commit, skipped async exit/entry sentinels, one observer pass, same cancellation object re-raised, ownership released, and subsequent reuse succeeds. [VERIFIED: locked D-13–D-14; current handshake/ownership assertions at `tests/test_transition_lifecycle.py:1156-1267`].
6. **Native matrix:** field/slot order, `core.pyi`, exact Boolean rejection before mutation, direct singleton storage, semantic pure/native probe, and no lingering source-tree native shadow. [VERIFIED: `.github/copilot-instructions.md:40-50,318-336`; current structural/native patterns at `tests/test_mypyc_guard.py:1870-2085`].

### Sampling Rate

- **Per task commit:** `uv run pytest tests/test_transition_modes.py -x -q`, plus the directly affected adjacent file.
- **Per wave merge:** run the adjacent regression command above, blocking mypy, Ruff validation, and slots audit for waves that change `core.py` or `core.pyi`. [VERIFIED: `.github/copilot-instructions.md:108-119,318-334`].
- **Phase gate:** full suite green, blocking mypy green, advisory ty recorded, Ruff green, slots policy green, pure/native semantic probe green, and source origin restored before `$gsd-verify-work`. [VERIFIED: `.github/copilot-instructions.md:40-84,108-119,318-336`].

### Wave 0 Gaps

| Gap | Purpose |
|-----|---------|
| `tests/test_transition_modes.py` | Central MODE-01..06 oracle for direct/builder, lifecycle, timing, result/history, priority, failure, and async cancellation. |
| `tests/test_mypyc_guard.py` additions | Assert appended carrier/result/record slots and fields, stub signatures, exact bool boundary, direct singleton representation, and pure/native semantic parity. |
| `tests/test_graph_invariants.py` additions | Prove mode identity, atomic invalid fan-out, snapshot scalar, clone replay, and version neutrality. |
| `tests/test_hypothesis.py` additions | Generate valid/invalid self versus non-self mode requests and request orderings without partial publication. |

No test framework installation or new shared fixture module is needed; `FakeClock` and event-handshake patterns already exist and should be reproduced locally in the phase oracle rather than importing test modules. [VERIFIED: `tests/test_transition_timing.py:21-30`; `tests/test_transition_lifecycle.py:1166-1267`; `pyproject.toml:11-20`].

## Security Domain

Security enforcement is active because `.planning/config.json` contains no `security_enforcement: false` override. [VERIFIED: complete config opened; `.planning/config.json:1-37`].

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | Phase 28 has no identity/authentication boundary; do not add one. [VERIFIED: phase boundary `.planning/phases/28-same-state-transition-modes/28-CONTEXT.md:7-9`]. |
| V3 Session Management | no | Machine ownership is in-process dispatch ownership, not an application session mechanism. [VERIFIED: `src/fast_fsm/core.py:1061-1065,4909-4944`]. |
| V4 Access Control | no | Transition guards/state permission remain existing application policy; mode must not bypass their evaluation. [VERIFIED: locked D-15 at `.planning/phases/28-same-state-transition-modes/28-CONTEXT.md:37`]. |
| V5 Input Validation | yes | Exact built-in bool, canonical object identity, final-source invariant, complete prepare-before-publish transaction, bounded errors. [VERIFIED: locked D-01–D-03; existing canonical boundary `src/fast_fsm/core.py:1823-1997`]. |
| V6 Cryptography | no | No cryptographic primitive or secret-storage feature is introduced; package runtime dependencies remain unchanged. [VERIFIED: `.planning/REQUIREMENTS.md:92`; `pyproject.toml:7-9`]. |

### Known Threat Patterns for the Python/mypyc Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Truthy/coercible mode weakens compiled invariants | Tampering | Keep the public boundary object-typed until `type(internal) is bool` passes, before mutation. [VERIFIED: locked D-01; analogous priority boundary at `src/fast_fsm/core.py:715-719`]. |
| Invalid late row partially publishes topology | Tampering | Normalize every immutable request, merge off-table, publish only the complete plan, increment graph version once. [VERIFIED: `src/fast_fsm/core.py:1929-1997`]. |
| Mode injected into callback kwargs collides with caller payload | Tampering / Information disclosure | Store mode only in topology/result/history; preserve caller args/kwargs unchanged. [VERIFIED: locked D-11]. |
| Raw object/error details enter bounded messages or trace | Information disclosure | Fixed bounded validation text; do not interpolate object representations; preserve existing metadata-only trace boundary. [VERIFIED: `.github/copilot-instructions.md:320-334`; locked D-11]. |
| Cancellation swallowed or ownership leaked | Denial of service | One outer cancellation finalizer, bare re-raise, release ownership in `finally`, reuse test. The current boundary is verified in `src/fast_fsm/core.py:4909-5015`; the re-raise rule is documented by Python. [VERIFIED: `src/fast_fsm/core.py:4909-5015`] [CITED: https://docs.python.org/3.10/library/asyncio-exceptions.html]. |
| Optional semantics add unrelated topology scans | Denial of service | Store one scalar on direct entries and branch only after local selection; no diagnostics/serialization work in dispatch. [VERIFIED: `.specify/decisions/ADR-007-priority-topology.md:31-45`; locked D-15]. |

## Sources

### Primary (HIGH confidence)

- `.planning/phases/28-same-state-transition-modes/28-CONTEXT.md` — locked mode, lifecycle, commit, timing, failure, cancellation, scope, and discretion decisions.
- `.planning/REQUIREMENTS.md` and `.planning/ROADMAP.md` — MODE-01..06 and five success criteria.
- `src/fast_fsm/core.py` and `src/fast_fsm/core.pyi` — current authoritative carrier, registrar, selector, lifecycle, commit, result/history, builder, graph, clone, and type surfaces.
- `tests/test_transition_lifecycle.py`, `tests/test_transition_timing.py`, `tests/test_priority_selection.py`, `tests/test_graph_invariants.py`, `tests/test_builder.py`, `tests/test_async.py`, and `tests/test_mypyc_guard.py` — current active evidence patterns.
- `.specify/decisions/ADR-004-atomic-transition-lifecycle.md` — accepted stage/order/commit/failure/cancellation contract.
- `.specify/decisions/ADR-007-priority-topology.md` — accepted direct singleton, identity, atomic merge, and local-complexity contract.
- `.github/copilot-instructions.md`, `AGENTS.md`, `.planning/config.json`, and `pyproject.toml` — workflow, toolchain, test, slots, typing, and validation constraints.

### Secondary (MEDIUM confidence)

- `https://docs.python.org/3.10/library/dataclasses.html` — slotted dataclass/default/compare field behavior.
- `https://docs.python.org/3.10/library/asyncio-exceptions.html` — `CancelledError` inheritance and re-raise guidance.
- `https://docs.python.org/3.10/library/time.html` — monotonic elapsed-time semantics.

### Tertiary (LOW confidence)

- None.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — existing project manifest and local uv environment verified; no new package.
- Architecture: HIGH — locked phase decisions map directly onto opened source boundaries and accepted ADRs.
- Pitfalls: HIGH — each risk has a current source seam and active adjacent test pattern.
- Validation: HIGH — Nyquist is enabled, existing framework/config is active, and the adjacent baseline passes.

**Research date:** 2026-09-16
**Valid until:** 2026-10-16, or earlier if `src/fast_fsm/core.py`, `core.pyi`, Phase 28 context, ADR-004, or ADR-007 changes.

**Knowledge graph:** not used; `.planning/graphs/graph.json` is absent and graphify is disabled, so all relationships were traced directly through source, tests, phase context, and accepted ADRs. [VERIFIED: local graph status on 2026-09-16].
