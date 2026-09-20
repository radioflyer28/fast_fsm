# Phase 27: Explicit Final States - Research

**Researched:** 2026-09-15
**Domain:** Immutable flat-FSM completion metadata, atomic topology validation, lifecycle commit truth, and persistence parity
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

### Final-State Model
- **D-01:** `State(..., final=True)` is the single public declaration surface; `final` is a keyword-only immutable boolean with a backward-compatible `False` default. — **Reversibility:** costly — changing the public constructor/property contract later would affect every construction and persistence adapter.
- **D-02:** Finality is explicit domain intent only. A non-final state with no outgoing edges remains a valid sink and does not make the machine terminated; the library never infers finality from graph shape.
- **D-03:** `State.final` is readable but cannot be reassigned after construction. No `FinalState` subclass or mutable machine-side final-state registry is introduced.

### Construction Invariant
- **D-04:** Any outgoing transition whose canonical source State is final is invalid, including self-transitions, multi-source expansion, priority candidates, helpers, factories, builders, declarative reconstruction, clones, and dictionary input.
- **D-05:** Rejection occurs in the Phase 26 canonical normalization/validation transaction before publication. A mixed batch containing one invalid final-source edge publishes nothing, preserves graph version, and leaves reusable builder/factory inputs repairable.
- **D-06:** A final state may be the initial state and may be the destination of any valid incoming transition. Construction must not require a final state to have an incoming edge.

### Runtime and Lifecycle Truth
- **D-07:** `StateMachine.is_terminated` is a read-only O(1) query of the canonical current state's explicit final marker; no topology scan, cache, or separate termination flag is maintained.
- **D-08:** Termination becomes visible at the same commit boundary that changes `current_state` to a final destination. Normal exit/transition/entry/observer lifecycle still runs; failures after commit do not roll back the state or termination truth.
- **D-09:** A trigger attempted while currently final follows the ordinary missing-transition resolution failure because outgoing final-source edges cannot exist. Finality does not introduce an automatic event, exception class, scheduler, or special completion callback.

### Reset, Restore, Clone, and Persistence
- **D-10:** Reset and snapshot restore derive termination solely from the resulting canonical current State. Resetting to a final initial state is terminated; restoring a non-final current state is not.
- **D-11:** Clone preserves the exact canonical State objects and therefore their immutable final markers while retaining Phase 26's independent transition containers.
- **D-12:** Dictionary persistence is additive: serialize explicit final-state names in a bounded deterministic field while older payloads that omit the field default every state to non-final. Deserialization validates names/types before candidate publication and rejects outgoing final-source edges atomically. — **Reversibility:** costly — serialized field semantics become a compatibility contract consumed by Phase 30.

### the agent's Discretion
- Exact private helper names, bounded public error wording, and test-file placement.
- The additive dictionary field's precise spelling and ordering, provided it is deterministic, backward-compatible, and straightforward for Phase 30 to carry across every persistence adapter.
- Whether `is_terminated` is implemented directly on sync base behavior only or explicitly mirrored for async typing, provided both machine types expose identical observable semantics.

### Deferred Ideas (OUT OF SCOPE)

- Internal versus external self-transition lifecycle semantics — Phase 28.
- Structured expected domain rejection — Phase 29.
- Builder-first guidance, compatibility deprecations, and complete persistence-adapter parity — Phase 30.
- Final-state validation findings, JSON diagnostics, Mermaid, and PlantUML styling — Phase 31.
- Progressive drone guidance, installed-artifact proof, and feature-local performance evidence — Phase 32.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| FINAL-01 | Users can declare a state final with an immutable `final=True` property. | Add one private slot plus a getter-only public property to `State`, and thread the keyword-only argument through `State.create`, `CallbackState`, `DeclarativeState`, and inherited async declarative construction. |
| FINAL-02 | Users can query termination in O(1) through `is_terminated`, including when the initial state is final. | Implement one inherited property that returns the current canonical state's final marker; do not inspect transitions. |
| FINAL-03 | Users receive an atomic construction error when any supported construction path would add an outgoing transition to a final state. | Reject after canonical source resolution inside `_normalize_transition_request()`; `_apply_transition_requests_owned()` already prepares the entire request tuple before `_commit_transition_plan()`. |
| FINAL-04 | Users can distinguish a non-final sink state from a terminated final state. | Test two topology-identical states with different explicit markers; termination must depend only on the current marker. |
| FINAL-05 | Users observe the machine as terminated after a transition commits into a final state even if later entry or observer work fails. | Existing sync and async lifecycle runners commit before destination-enter and later observer stages, so a derived property exposes finality immediately without rollback logic. |
| FINAL-06 | Users receive consistent termination semantics after reset, restore, clone, and deserialization operations. | Keep snapshot v1 unchanged, derive truth after control commits, preserve shared State identity in clone, and add deterministic `final_states` topology metadata to dictionary persistence. |
</phase_requirements>

## Summary

Phase 27 should remain a narrow deepening of the existing flat FSM: one exact boolean stored on each canonical `State`, one getter-only `StateMachine.is_terminated` property, and one final-source check in the canonical construction transaction. This implements the locked completion model without adding a termination latch, topology inference, a final-state subclass, completion events, or an async-specific copy of the logic. [VERIFIED: `.planning/phases/27-explicit-final-states/27-CONTEXT.md:17-35`]

The highest-risk seam is construction, not dispatch. `_apply_transition_requests_owned()` currently normalizes every immutable request before calling `_commit_transition_plan()`, and `_commit_transition_plan()` builds replacement slots off-table before publishing and incrementing `_graph_version`. Therefore, checking `source.final` immediately after `_resolve_canonical_state()` gives direct, batch, multi-source, helper, builder, factory, clone, and dictionary paths the same all-or-nothing behavior without touching the trigger hot path. [VERIFIED: `src/fast_fsm/core.py:1739-1800`; `src/fast_fsm/core.py:1867-1935`]

Lifecycle truth is already aligned with the requirement. Both sync and async runners call `_commit_transition()` before destination entry and later callbacks/listeners; `_commit_transition()` writes history, then `_current_state`, then `_state_entered_at`. A property derived from `_current_state.final` will consequently read `True` inside final-state entry work and remain `True` after a post-commit error or cancellation. [VERIFIED: `src/fast_fsm/core.py:3671-3729`; `src/fast_fsm/core.py:3483-3503`; `src/fast_fsm/core.py:4447-4516`]

**Primary recommendation:** Implement finality only in `State`, the canonical transition normalizer, the current-state query, and additive dictionary serialization; reuse all existing commit/control/clone machinery and prove the contract in pure and compiled modes.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Final-state declaration | Public state model (`State`) | State subclasses/factory | Finality is immutable state identity metadata, not machine registry state. [VERIFIED: CONTEXT D-01 through D-03] |
| Final-source invariant | Canonical construction transaction | Construction adapters | `_normalize_transition_request()` owns canonical endpoint validation; adapters already converge through `_apply_transition_requests_owned()`. [VERIFIED: `src/fast_fsm/core.py:1739-1935`] |
| Termination query | Runtime read surface (`StateMachine`) | Inherited async API | `_current_state` is already the canonical current object, so the query needs one attribute chain. [VERIFIED: `src/fast_fsm/core.py:2287-2295`] |
| Commit-time visibility | Shared lifecycle commit seam | Sync/async lifecycle runners | Both runners invoke `_commit_transition()` before entry and observer work. [VERIFIED: `src/fast_fsm/core.py:3671-3729`; `src/fast_fsm/core.py:4447-4516`] |
| Reset/restore continuity | Direct-control transition seam | Snapshot v1 | `reset()` and `restore()` both route to `_force_state_owned()`, which commits through the shared control lifecycle. [VERIFIED: `src/fast_fsm/core.py:3307-3381`; `src/fast_fsm/core.py:3800-3863`] |
| Clone continuity | Clone reconstruction | Canonical transaction | Clone reuses exact State objects but reconstructs independent transition containers through the canonical transaction. [VERIFIED: `src/fast_fsm/core.py:3413-3444`] |
| Persistence continuity | `to_dict()` / `from_dict()` | Canonical transaction | The topology format already has deterministic state and transition collections and one row-context-aware transaction. [VERIFIED: `src/fast_fsm/core.py:1264-1583`] |
| Contract proof | Pytest + native build | Slots/source guards | Existing lifecycle, graph, builder, async, Hypothesis, and mypyc tests provide adjacent coverage seams. [VERIFIED: `.github/copilot-instructions.md:65-71` and test inventory inspection] |

## Project Constraints (from AGENTS.md)

- Use `bd` with `--json` for all work tracking; do not create a parallel Markdown task list. [VERIFIED: `AGENTS.md:17-106`]
- Use `uv` for every Python/package/test command; direct `python` and `pip` invocations are forbidden. [VERIFIED: `.github/copilot-instructions.md:36-38`]
- Preserve hot-path `__slots__`. The registered exceptions are quoted verbatim as `CompiledFuncCondition`, `TransitionError`, and `DiagnosticBudgetExceeded`; `State` is not an exception. [VERIFIED: `.github/copilot-instructions.md:40-50`]
- Preserve O(1) source/trigger lookup, direct singleton dispatch, and `add_state()`; candidate work remains local O(k), and fresh installed compiled singleton dispatch must remain at least 200,000 operations/second. [VERIFIED: `.github/copilot-instructions.md:51-58`]
- Preserve callback and condition `*args, **kwargs` signatures and use a deprecation cycle before removing public symbols. [VERIFIED: `.github/copilot-instructions.md:60-63`]
- Run targeted tests incrementally and the full sequential suite once before push. The full command is quoted verbatim as `uv run pytest tests/ -x -q`. [VERIFIED: `.github/copilot-instructions.md:65-71`]
- Update public docstrings and relevant documentation for a public API change; update the living core SPR in the same commit that changes its behavior. [VERIFIED: `.github/copilot-instructions.md:123-126`; `.github/copilot-instructions.md:404-445`]
- Keep `core.py` as the mypyc compilation unit and verify both interpreted and compiled behavior. `setup.py` passes exactly `"src/fast_fsm/core.py"` to `mypycify`. [VERIFIED: `setup.py:16-39`]
- Preserve unrelated work, stage only explicit task paths, and never use `git add .` or `git add -A`. [VERIFIED: `.github/copilot-instructions.md:123-126`]
- Before session completion, update issue state, rebase/sync, push, and verify the branch is current with origin. [VERIFIED: `AGENTS.md:108-129`]

## Standard Stack

### Core

| Library / runtime | Version | Purpose | Why Standard |
|-------------------|---------|---------|--------------|
| Python | Project contract `>=3.10`; local `3.12.10` | Public runtime and descriptor/property semantics | The package metadata quotes `requires-python = ">=3.10"`; Phase 27 needs no language-level feature beyond that floor. [VERIFIED: `pyproject.toml:1-9`; local `uv run python --version`, 2026-09-15] |
| Fast FSM core | Project `0.4.0` baseline | State model, construction, runtime, control, persistence | The package metadata quotes `version = "0.4.0"`, and all required seams already live in `src/fast_fsm/core.py`. [VERIFIED: `pyproject.toml:1-9`; codebase inspection] |
| `mypy-extensions` | Project `>=1.0` | Existing mypyc attributes | It is the only runtime dependency and is already declared; Phase 27 adds no dependency. [VERIFIED: `pyproject.toml:7-9`] |

### Supporting

| Library / tool | Version | Purpose | When to Use |
|----------------|---------|---------|-------------|
| pytest | Project `>=8.4.1`; local `8.4.1` | Unit, integration, lifecycle, persistence, and source-shape tests | Run targeted Phase 27 tests per implementation task and the complete suite at the phase gate. [VERIFIED: `pyproject.toml:11-20`; local command output] |
| pytest-asyncio | Project `>=1.3.0` | Deterministic post-commit cancellation tests | Use event handshakes rather than timing sleeps for async cancellation at destination-entry. [VERIFIED: `pyproject.toml:11-20`; `tests/test_transition_lifecycle.py:1146-1256`] |
| Hypothesis | Project `>=6.136.6` | Generated final/non-final topology and operation sequences | Use for combinatorial atomicity and final-source invariants after focused examples are green. [VERIFIED: `pyproject.toml:11-20`] |
| mypy/mypyc | Project `>=1.17`; release/build `1.17.1`; local `1.17.1` | Static and compiled-boundary validation | Run after changing `State` slots, constructors, properties, or serialization. [VERIFIED: `pyproject.toml:11-25`; local command output] |
| Ruff | Project `>=0.12.11`; local `0.12.11` | Formatting and linting | Run on changed Python files before the full suite. [VERIFIED: `pyproject.toml:11-20`; local command output] |
| ty | Project `>=0.0.1a19`; local `0.0.1-alpha.19` | Advisory typing feedback | Keep visible but secondary to mypy/mypyc compatibility. [VERIFIED: `pyproject.toml:11-20`; local command output] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Private `_final` slot plus getter-only property | Frozen `State` dataclass | Freezing the entire state would also alter the existing writable `name` behavior and subclass construction surface, exceeding D-01/D-03. [VERIFIED: `src/fast_fsm/core.py:838-906`; CONTEXT D-01/D-03] |
| Derive `is_terminated` from current State | Store a machine `_terminated` flag | A second mutable truth source would need synchronization in constructor, commit, reset, restore, clone, and force-state flows, contrary to D-07/D-10. [VERIFIED: CONTEXT D-07/D-10] |
| Validate at `_normalize_transition_request()` | Validate in every public adapter | Adapter-local checks can disagree and can miss helper expansion; all adapters already converge on the canonical transaction. [VERIFIED: `src/fast_fsm/core.py:1978-2280`; `src/fast_fsm/core.py:5911-5971`] |
| Top-level `final_states` list in dictionaries | Change `states` strings into state objects | Replacing the existing string-list shape is a breaking format change; an additive sorted list preserves legacy payloads. [VERIFIED: `src/fast_fsm/core.py:1279-1291`; CONTEXT D-12] |

**Installation:** No new package is required. Use the existing locked environment with `uv sync --locked --all-groups`. [VERIFIED: `.github/copilot-instructions.md:73-78`]

## Package Legitimacy Audit

Not applicable. Phase 27 installs no external package and uses only the existing locked project stack. [VERIFIED: phase scope and proposed architecture]

## Architecture Patterns

### System Architecture Diagram

```text
Public construction input
  State(name, final=bool)
  transition request(s)
          |
          v
State registry -----> canonical endpoint resolution
                           |
                           v
                  source.final decision
                    /             \
             true /               \ false
                 v                 v
       fixed bounded error    prepare all requests
                 |                 |
                 |                 v
                 +--------> publish nothing OR publish all slots once

Runtime event -> select edge -> exit lifecycle -> COMMIT current State
                                                 |
                                                 +-> is_terminated == current.final
                                                 |
                                                 v
                                    entry / observer / async work
                                    (failure does not undo commit)

Control: reset / restore / force_state -> same commit seam -> derived truth
Persistence: to_dict(final_states) -> validate names/types -> State(final=...)
             -> canonical transition transaction
```

This flow preserves construction-time validation outside dispatch and makes the existing current-state commit the only runtime truth boundary. [VERIFIED: CONTEXT D-05/D-07/D-08; `src/fast_fsm/core.py:1867-1935`; `src/fast_fsm/core.py:3483-3503`]

### Recommended Project Structure

```text
src/fast_fsm/core.py                    # State flag, property, invariant, persistence
tests/test_final_states.py              # Phase contract and cross-surface behavior
tests/test_graph_invariants.py          # canonical transaction and schema assertions
tests/test_transition_lifecycle.py      # post-commit failure/cancellation truth
tests/test_builder.py                   # builder retryability and subclass construction
tests/test_async.py                     # inherited async semantics
tests/test_hypothesis.py                # generated invariant sequences
tests/test_mypyc_guard.py               # slots/source-shape/native compatibility guards
.specify/memory/spr-core-api.md          # living runtime contract update
```

The files above match the repository's documented source-to-test mapping and public API memory policy. [VERIFIED: `.github/copilot-instructions.md:176-190`; `.github/copilot-instructions.md:404-445`]

### Pattern 1: Immutable Public Flag on a Slotted Base State

**What:** Add `_final` to `State.__slots__`, accept `final` as a keyword-only exact boolean, and expose only a getter. Thread the same keyword through callback and declarative subclass constructors; `AsyncDeclarativeState` inherits it. `State` currently has exactly `__slots__ = ("name",)`, and its callback/declarative subclasses have their own slots and explicit constructors. [VERIFIED: `src/fast_fsm/core.py:838-878`; `src/fast_fsm/core.py:909-925`; `src/fast_fsm/core.py:5251-5277`]

**When to use:** Every State construction surface, including `State.create`, `CallbackState`, `DeclarativeState`, and `AsyncDeclarativeState`.

**Recommended shape:**

```python
# Planned from CONTEXT D-01 and D-03; exact private naming is discretionary.
class State:
    __slots__ = ("name", "_final")

    def __init__(self, name: str, *, final: bool = False):
        if type(final) is not bool:
            raise TypeError("final must be an exact built-in bool")
        self.name = name
        self._final = final

    @property
    def final(self) -> bool:
        return self._final
```

Using exact built-in validation mirrors the compiled-boundary discipline already used by `_normalize_priority()`, which quotes `if type(priority) is not int` and rejects coercion before narrowing. [VERIFIED: `src/fast_fsm/core.py:715-719`]

### Pattern 2: One Canonical Final-Source Check

**What:** After each raw source resolves to its registered canonical State, reject it if `source.final` is true, before target/guard/timing preparation and before any topology publication. [VERIFIED: `src/fast_fsm/core.py:1739-1808`; CONTEXT D-04/D-05]

**When to use:** Only inside `_normalize_transition_request()`; do not duplicate it in direct, batch, helper, builder, clone, or dictionary adapters.

**Recommended shape:**

```python
source = self._resolve_canonical_state(raw_source, role="source")
if source.final:
    raise ValueError("final state cannot be a transition source")
```

A fixed message is bounded and avoids echoing arbitrary user-controlled state names; `from_dict()` already adds the exact row context supplied in `error_contexts`. [VERIFIED: `src/fast_fsm/core.py:1892-1935`; `src/fast_fsm/core.py:1536-1541`]

### Pattern 3: Derived Termination Truth

**What:** Add a getter-only property on `StateMachine` that returns `self._current_state.final`. Because `AsyncStateMachine` subclasses `StateMachine`, inheritance gives both classes the same observable and typing surface unless a typing check proves an explicit mirror is necessary. [VERIFIED: `src/fast_fsm/core.py:940-1003`; `src/fast_fsm/core.py:4107`; CONTEXT discretion]

**When to use:** Controller-loop completion checks and callback observation; never cache it.

```python
@property
def is_terminated(self) -> bool:
    return self._current_state.final
```

The official Python descriptor documentation confirms that a property without a setter is a managed read-only public attribute, while `__slots__` supplies descriptor-backed instance storage without automatically adding `__dict__`. [CITED: https://docs.python.org/3.12/howto/descriptor.html] [CITED: https://docs.python.org/3.12/reference/datamodel.html#object.__slots__]

### Pattern 4: Additive Deterministic Dictionary Field

**What:** Use `"final_states"` as a top-level list of sorted unique state names. Always emit it (including `[]`) so current output is canonical; on input, omission means `[]`. Validate that the value is a list, every item is a non-empty string, there are no duplicates, and every name belongs to the discovered state set before constructing the private machine candidate. This spelling was already recommended in the milestone research and is the clearest continuation for Phase 30. [VERIFIED: `.planning/research/FEATURES.md:137-144`; CONTEXT D-12]

**When to use:** `to_dict()` and `from_dict()` only. Snapshot format remains exactly `{"state": <current_state_name>, "version": 1}`. [VERIFIED: `src/fast_fsm/core.py:3332-3347`; CONTEXT D-10]

```python
payload = {
    "name": self._name,
    "initial": self._initial_state.name,
    "states": sorted(self._states),
    "final_states": sorted(
        state.name for state in self._states.values() if state.final
    ),
    "transitions": transitions,
}
```

Deserialization should instantiate canonical States with `State(name, final=name in final_names)` and then submit the full request tuple once. It must instantiate through `cls(...)` for the machine so `AsyncStateMachine.from_dict()` remains an async machine. [VERIFIED: current classmethod shape at `src/fast_fsm/core.py:1264-1271`; canonical apply at `src/fast_fsm/core.py:1536-1542`]

### Pattern 5: Reuse the Existing Commit Boundary

**What:** Do not modify `_commit_transition()` to maintain a termination flag. The existing assignment `self._current_state = to_state` is sufficient. Reset, restore, and force-state already reuse the same control commit; clone already reuses State identity. [VERIFIED: `src/fast_fsm/core.py:3307-3464`; `src/fast_fsm/core.py:3483-3503`; `src/fast_fsm/core.py:3800-3863`]

**When to use:** Normal sync/async transitions, administrative control operations, and clone tests.

### Anti-Patterns to Avoid

- **Topology-derived termination:** A state with no outgoing row may be an accidental or intentional non-final sink; D-02 requires it to remain non-terminated. [VERIFIED: CONTEXT D-02]
- **Sticky `_terminated` machine state:** It duplicates current-state truth and creates reset/restore/clone synchronization bugs. [VERIFIED: CONTEXT D-07/D-10]
- **A `FinalState` subclass or final-state registry:** Both are explicitly excluded and would complicate identity and serialization. [VERIFIED: CONTEXT D-03]
- **Dispatch-time final checks:** They would charge the hot path for an invariant construction must already guarantee and would turn invalid topology into runtime behavior. [VERIFIED: CONTEXT D-04/D-05; performance constraints]
- **Silently skipping final states in multi-source/emergency helpers:** The operation must fail atomically; silently pruning sources changes user-authored topology. [VERIFIED: CONTEXT D-04/D-05]
- **Special trigger behavior while final:** Ordinary missing-transition resolution must remain the only outcome. [VERIFIED: CONTEXT D-09]
- **Changing snapshot v1:** Snapshot remains state-only; finality comes from the receiving machine's canonical State. [VERIFIED: CONTEXT D-10; `src/fast_fsm/core.py:3332-3379`]
- **Adding final markers to graph/JSON/diagram diagnostics now:** Diagnostic projection and styling are explicitly Phase 31 work. [VERIFIED: CONTEXT deferred ideas]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Termination tracking | Mutable machine latch/cache | `current_state.final` | One source of truth automatically covers initialization, commit, reset, restore, and force-state. [VERIFIED: CONTEXT D-07/D-10] |
| Cross-adapter topology validation | Checks in every public constructor/helper | `_normalize_transition_request()` inside `_apply_transition_requests_owned()` | The existing transaction prepares all requests before publication. [VERIFIED: `src/fast_fsm/core.py:1763-1935`] |
| Async termination implementation | Separate async flag/property | Inherited base property | `AsyncStateMachine` already inherits base state/control behavior and shares `_commit_transition()`. [VERIFIED: `src/fast_fsm/core.py:4107-4118`; `src/fast_fsm/core.py:4447-4460`] |
| Completion orchestration | Automatic completion events or callback family | Existing entry, trigger, after, and failure observation surfaces | Completion events and schedulers are excluded by D-09. [VERIFIED: CONTEXT D-09] |
| Persistence object encoding | Serialized `State` objects or callable metadata | Sorted JSON-native `final_states` names | Existing topology uses JSON-native names/rows and external condition registries. [VERIFIED: `src/fast_fsm/core.py:1279-1322`; `src/fast_fsm/core.py:1544-1583`] |
| Native parity harness | New build/test runner | Existing `task build-check`, source preflight, and mypyc guards | The repository already compiles `core.py` and verifies source mode separately. [VERIFIED: `Taskfile.yml:119-129`; `Taskfile.yml:189-202`] |

**Key insight:** This feature becomes safer and faster when represented as immutable graph metadata plus one canonical construction invariant; every extra mutable mechanism would duplicate facts the machine already owns.

## Common Pitfalls

### Pitfall 1: Making Only `State` Accept `final`

**What goes wrong:** `State.create(...)`, `CallbackState(...)`, and `DeclarativeState(...)` reject or lose the marker even though they are public State construction surfaces.

**Why it happens:** All three currently define explicit constructor/factory signatures and forward only `name` plus callback/logger arguments. [VERIFIED: `src/fast_fsm/core.py:847-878`; `src/fast_fsm/core.py:917-925`; `src/fast_fsm/core.py:5267-5277`]

**How to avoid:** Add one keyword-only `final` parameter to each explicit surface and forward it by keyword to `super().__init__`/`CallbackState`.

**Warning signs:** Pure `State(final=True)` passes while callback or declarative variants fail constructor tests.

### Pitfall 2: Boolean Coercion Weakens the Compiled Contract

**What goes wrong:** Values such as `1`, truthy strings, or custom objects are accepted and then behave differently across interpreted and compiled code.

**Why it happens:** `bool(value)` normalizes arbitrary input rather than validating the public boolean contract.

**How to avoid:** Check `type(final) is bool` before assigning the slotted field, mirroring the exact-value validation style at the mypyc boundary. [VERIFIED: `src/fast_fsm/core.py:715-719`]

**Warning signs:** Tests pass `final=1` without a `TypeError`, or native behavior differs from pure mode.

### Pitfall 3: Validating Before Canonical Resolution or After Publication

**What goes wrong:** A same-name foreign State can evade the marker check, or a mixed batch can publish a valid prefix before encountering a final source.

**Why it happens:** The raw endpoint is inspected instead of the registered object, or mutation occurs per row.

**How to avoid:** Resolve the canonical source, inspect its final marker, prepare the complete batch, then publish once. [VERIFIED: `src/fast_fsm/core.py:1739-1800`; `src/fast_fsm/core.py:1867-1935`]

**Warning signs:** `_graph_version` changes after a rejected batch, or a foreign object with a matching name affects validation.

### Pitfall 4: Emergency and Bidirectional Helpers Quietly Change Meaning

**What goes wrong:** `add_emergency_transition()` silently excludes finals, or `add_bidirectional_transition()` publishes one allowed direction while rejecting the final-source reverse direction.

**Why it happens:** Helper-specific filtering bypasses the canonical transaction.

**How to avoid:** Let the existing full source tuple / two-request tuple reach the one normalizer; any final source rejects the entire helper call. The current helpers already submit exactly one transaction. [VERIFIED: `src/fast_fsm/core.py:2109-2280`]

**Warning signs:** An emergency transition exists on some states after a failure, or graph version advances on a failed bidirectional operation.

### Pitfall 5: Post-Commit Failure Is Mistaken for Rollback

**What goes wrong:** A result is unsuccessful because destination entry or an observer failed, and a test incorrectly expects `is_terminated` to be false.

**Why it happens:** Result success and commit truth are conflated.

**How to avoid:** Assert the existing `committed` boundary and current State independently. Destination-enter and later sync failures are already marked `committed=True`; async cancellation after commit also retains destination State/history. [VERIFIED: `tests/test_transition_lifecycle.py:932-997`; `tests/test_transition_lifecycle.py:1146-1248`]

**Warning signs:** Code attempts to clear termination or restore the source after an entry/observer error.

### Pitfall 6: Persistence Infers or Invents States

**What goes wrong:** A typo in `final_states` silently creates an isolated final State, duplicates are accepted, or a missing legacy field fails deserialization.

**Why it happens:** The final-name set is merged into discovered topology instead of validated against it.

**How to avoid:** Parse the optional list with default `[]`, reject invalid/duplicate/unknown names, then construct States from the already-discovered state set. [VERIFIED: CONTEXT D-12]

**Warning signs:** `from_dict({..., "final_states": ["typo"]})` succeeds when `typo` is absent from `states`, `initial`, and transition endpoints.

### Pitfall 7: Source-Shape Tests Become Stale

**What goes wrong:** Runtime behavior passes but slots, subclassability, exact schema, or canonical-adapter structural guards fail.

**Why it happens:** The project intentionally has AST/source assertions for mypyc boundaries and exact dictionary shapes. [VERIFIED: `tests/test_mypyc_guard.py:241-259`; `tests/test_graph_invariants.py:395-410`]

**How to avoid:** Update exact expected slots/schema assertions deliberately, while keeping the test that all retained adapters call `_apply_transition_requests_owned()`.

**Warning signs:** Focused behavioral tests pass but `test_mypyc_guard.py` or `test_graph_invariants.py` fails.

## Code Examples

Verified/planned patterns from locked project decisions and existing seams:

### Initial Final State and Non-Final Sink

```python
done = State("done", final=True)
terminated = StateMachine(done)
assert terminated.is_terminated is True

sink = State("sink")
not_terminated = StateMachine(sink)
assert not_terminated.is_terminated is False
```

The values `final=True`, a backward-compatible `False` default, and the topology-independent distinction are locked in D-01/D-02. [VERIFIED: `.planning/phases/27-explicit-final-states/27-CONTEXT.md:17-20`]

### Atomic Mixed-Batch Rejection

```python
source = State("source")
done = State("done", final=True)
machine = StateMachine(source)
machine.add_state(done)

before = machine.to_dict()
try:
    machine.add_transitions([
        ("finish", source, done),
        ("invalid", done, source),
    ])
except ValueError:
    pass

assert machine.to_dict() == before
```

`add_transitions()` already converts the whole list to an immutable request tuple and calls `_apply_transition_requests_owned()` once. [VERIFIED: `src/fast_fsm/core.py:2031-2107`]

### Post-Commit Failure Remains Terminated

```python
def fail_entry(*args, **kwargs):
    raise RuntimeError("entry failed")

source = State("source")
done = CallbackState("done", on_enter=fail_entry, final=True)
machine = StateMachine(source)
machine.add_state(done)
machine.add_transition("finish", source, done)

result = machine.trigger("finish")
assert result.success is False
assert result.committed is True
assert machine.current_state is done
assert machine.is_terminated is True
```

The callback signatures retain `*args, **kwargs`, and existing lifecycle code marks destination-enter failures committed after current-state assignment. [VERIFIED: `.github/copilot-instructions.md:60-63`; `src/fast_fsm/core.py:3671-3697`]

### Backward-Compatible Dictionary Input

```python
legacy = {
    "initial": "idle",
    "states": ["idle", "done"],
    "transitions": [{"trigger": "finish", "from": "idle", "to": "done"}],
}
assert StateMachine.from_dict(legacy).is_terminated is False

current = {**legacy, "final_states": ["done"]}
machine = StateMachine.from_dict(current)
assert machine.trigger("finish").committed is True
assert machine.is_terminated is True
```

Legacy omission defaults all states to non-final, while the additive field carries explicit names. [VERIFIED: CONTEXT D-12]

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Check a flat machine's `current_state.final` | Expose `is_terminated` as the completion query | `python-statemachine` 3.0 upgrade guidance | The competitor's new query also supports compound/parallel topology; Fast FSM remains flat and can implement the query as one current-State read. [CITED: https://python-statemachine.readthedocs.io/en/develop/releases/upgrade_2x_to_3.html] |
| Treat any dead end as completion | Declare final intent explicitly and treat dead-end non-finals separately | Current `python-statemachine` validation vocabulary | The official docs distinguish final states from non-final trap states and prohibit outgoing final transitions. Fast FSM adopts the distinction but deliberately permits non-final sinks. [CITED: https://python-statemachine.readthedocs.io/en/latest/states.html] [CITED: https://python-statemachine.readthedocs.io/en/latest/validations.html] |
| Maintain completion separately from active state | Derive termination from canonical active-state metadata | Phase 27 locked design | This avoids a second mutable truth source and keeps flat-machine lookup O(1). [VERIFIED: CONTEXT D-07] |

**Deprecated/outdated:** No symbol is deprecated by Phase 27. Builder-first deprecations are explicitly deferred to Phase 30. [VERIFIED: CONTEXT deferred ideas]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| — | None. Locked semantics come from CONTEXT.md; codebase claims were read from source; the `final_states` spelling is a recommendation within delegated discretion, not an external factual assumption. | — | — |

## Open Questions (RESOLVED)

1. **Does the getter-only `_final` property compile identically under mypyc on all supported interpreters? — RESOLVED as a mandatory execution-time validation requirement.**
   - What we know: `State` is compiled and explicitly allows interpreted subclasses; the project already requires native proof for core changes. [VERIFIED: `src/fast_fsm/core.py:838-839`; `setup.py:16-39`]
   - What's unclear: Source inspection cannot prove generated native behavior.
   - Planning resolution: Plan 27-03 Task 2 must run `task build-check`, assert a native `fast_fsm.core` origin, execute focused compiled Phase 27 behavioral tests, restore pure-source import resolution through constrained recoverable relocation of only the exact preflight-reported shadows, and rerun the full source suite. Any failure in this native parity sequence blocks Phase 27 acceptance.

No user decision is required before planning; all semantic choices are locked or delegated.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| `uv` | Every Python/test/build command | ✓ | 0.12.12 | None; project requires uv. [VERIFIED: local `uv --version`, 2026-09-15] |
| Python | Runtime/tests | ✓ | 3.12.10 | Use any supported `>=3.10` interpreter. [VERIFIED: local command; `pyproject.toml:6`] |
| pytest | Focused/full validation | ✓ | 8.4.1 | None needed. [VERIFIED: local command] |
| mypy/mypyc | Type/native boundary | ✓ | 1.17.1, compiled | None needed. [VERIFIED: local command] |
| Ruff | Formatting/lint | ✓ | 0.12.11 | None needed. [VERIFIED: local command] |
| ty | Advisory typing | ✓ | 0.0.1-alpha.19 | Mypy remains blocking if advisory ty differs. [VERIFIED: local command; project policy] |
| PowerShell | SPR aggregation helper | ✗ | — | Update `spr-core-api.md` directly; aggregation is not needed to implement or validate Phase 27. [VERIFIED: local `command -v pwsh`, 2026-09-15] |

**Missing dependencies with no fallback:** None.

**Missing dependencies with fallback:** PowerShell is unavailable, but it does not block code, tests, native build, or direct SPR maintenance.

## Validation Architecture

Nyquist validation is enabled; the configuration quotes `"nyquist_validation": true`. [VERIFIED: `.planning/config.json:15-20`]

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.4.1 with pytest-asyncio and Hypothesis [VERIFIED: local command; `pyproject.toml:11-20`] |
| Config file | `pyproject.toml` [VERIFIED: `pyproject.toml:54-73`] |
| Quick run command | `uv run pytest tests/test_final_states.py tests/test_graph_invariants.py tests/test_transition_lifecycle.py tests/test_builder.py tests/test_async.py -x -q` |
| Full suite command | `uv run pytest tests/ -x -q` [VERIFIED: `.github/copilot-instructions.md:65-71`] |
| Native gate | `task build-check`, followed by focused Phase 27 tests against the compiled import and explicit pure-source restoration [VERIFIED: `Taskfile.yml:189-202`; project release-evidence policy] |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FINAL-01 | Exact keyword-only bool, false default, read-only property, subclass/factory propagation, slots intact | unit + source/native | `uv run pytest tests/test_final_states.py tests/test_mypyc_guard.py -x -q` | `test_final_states.py`: Wave 0; guard file exists |
| FINAL-02 | Initial final and transitioned final report via direct current-State read; async inherits same query | unit + structural | `uv run pytest tests/test_final_states.py tests/test_async.py -x -q` | Wave 0 additions |
| FINAL-03 | Direct, batch, multi-source, priority, bidirectional, emergency, builder, quick-build, dict, and async construction reject final sources without version/topology change | unit + property | `uv run pytest tests/test_final_states.py tests/test_graph_invariants.py tests/test_builder.py tests/test_hypothesis.py -x -q` | Wave 0 additions; adjacent files exist |
| FINAL-04 | Non-final sink stays non-terminated while explicit final sink is terminated | unit | `uv run pytest tests/test_final_states.py -x -q` | Wave 0 |
| FINAL-05 | Sync entry/listener failure and async destination-entry cancellation remain committed and terminated | lifecycle/async | `uv run pytest tests/test_transition_lifecycle.py tests/test_final_states.py -x -q` | Existing lifecycle matrix; Phase 27 assertions needed |
| FINAL-06 | Reset, force, restore snapshot v1, clone identity/independence, current/legacy dictionary roundtrip | integration + unit | `uv run pytest tests/test_final_states.py tests/test_advanced_functionality.py tests/test_graph_invariants.py tests/test_async.py -x -q` | Wave 0 additions |

### Required Test Matrix

| Dimension | Cases |
|-----------|-------|
| State kinds | `State`, `CallbackState`, `DeclarativeState`, `AsyncDeclarativeState`, `State.create` |
| Machine kinds | sync and async |
| Construction shapes | direct, batch, multi-source, priority group, bidirectional helper, emergency helper, quick build, builder, dictionary |
| Runtime position | initially final, incoming final, non-final sink, trigger attempted while final |
| Failure boundary | before commit, destination entry, enter listener, trigger callback, after listener, async cancellation after commit |
| Control/persistence | reset to final initial, force/restore into and out of final, clone, current dict, legacy dict |
| Artifact mode | pure source and native compiled core |

Every helper failure must assert transition tables, graph version, current State, and builder cache/staging remain unchanged; every post-commit failure must assert result/cancellation semantics, current State identity, history count, and `is_terminated`. [VERIFIED: Phase 26 transaction contract and existing lifecycle test style]

### Sampling Rate

- **Per task commit:** Run the smallest affected Phase 27 test file plus one adjacent existing suite.
- **Per wave merge:** Run the quick Phase 27 command above, Ruff on changed Python, mypy, advisory ty, and the slots policy.
- **Phase gate:** Run the full sequential suite, `task build-check`, focused tests against the native import, clean generated native shadows explicitly, then run `task pure-source-check` and the full pure-source suite.

### Wave 0 Gaps

| Gap | Required coverage |
|-----|-------------------|
| `tests/test_final_states.py` does not exist | Central FINAL-01 through FINAL-06 behavioral oracle across State kinds, machine kinds, control, and persistence. |
| Existing exact `to_dict()` assertions omit `final_states` | Update canonical schema expectations and add legacy-input/default tests. [VERIFIED: `tests/test_graph_invariants.py:395-410`] |
| Existing lifecycle matrices do not assert termination | Add final destinations and `is_terminated` assertions at post-commit sync and async failure/cancellation boundaries. [VERIFIED: `tests/test_transition_lifecycle.py:932-997`; `tests/test_transition_lifecycle.py:1146-1248`] |
| Existing source guards do not assert `_final` slot or derived query shape | Extend mypyc/AST guards to prevent a machine-side termination field or transition scan. |
| Existing artifact conformance has no Phase 27 family | Do not expand the release artifact oracle in this phase; installed-artifact proof is deferred to Phase 32. Use `task build-check` plus focused native tests now. [VERIFIED: CONTEXT deferred ideas] |

## Security Domain

Security enforcement is enabled because `.planning/config.json` does not set `security_enforcement` to false. [VERIFIED: `.planning/config.json:1-37`]

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | Library has no authentication boundary in this phase. [VERIFIED: phase scope] |
| V3 Session Management | no | Library owns no user session. [VERIFIED: phase scope] |
| V4 Access Control | no | Library does not authorize principals. [VERIFIED: phase scope] |
| V5 Input Validation | yes | Exact built-in bool validation, strict JSON-native `final_states` parsing, canonical registered endpoint resolution, and fail-before-publication transaction. [VERIFIED: CONTEXT D-01/D-05/D-12] |
| V6 Cryptography | no | No secret, token, signature, or cryptographic operation is introduced. [VERIFIED: phase scope] |

### Known Threat Patterns for Python Configuration Libraries

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Truthy/coercible objects weaken an exact public flag | Tampering | Require `type(final) is bool`; never call user coercion hooks. [VERIFIED: analogous project boundary at `src/fast_fsm/core.py:715-719`] |
| Malformed or contradictory dictionary topology partially publishes | Tampering | Validate final names and prepare every transition before one publication. [VERIFIED: `src/fast_fsm/core.py:1892-1935`; CONTEXT D-12] |
| User-controlled State name leaks through unbounded error text | Information disclosure / resource exhaustion | Use a fixed bounded final-source message; retain only row index/field context for dictionaries. [VERIFIED: discretion granted in CONTEXT; existing context hook at `src/fast_fsm/core.py:1536-1541`] |
| Oversized duplicate final-name input causes needless later work | Denial of service | Validate list/item shape and duplicates in one linear pass before constructing the candidate; do not perform graph scans. |
| Dynamic attributes bypass the public immutability contract | Tampering | Keep `State` slotted and expose no setter for `final`. [CITED: https://docs.python.org/3.12/reference/datamodel.html#object.__slots__] |

The phase introduces no network, file, subprocess, authentication, cryptographic, or deserialization-of-code boundary. Dictionary input remains plain data and live conditions remain caller-supplied separately. [VERIFIED: `src/fast_fsm/core.py:1264-1322`; phase scope]

## Sources

### Primary (HIGH confidence)

- `.planning/phases/27-explicit-final-states/27-CONTEXT.md` — locked public model, construction invariant, lifecycle truth, control/persistence behavior, and deferred scope.
- `.planning/REQUIREMENTS.md` — FINAL-01 through FINAL-06 verbatim requirement contract.
- `src/fast_fsm/core.py` — State/subclass constructors, canonical construction transaction, runtime queries, sync/async commit order, control operations, clone, and dictionary persistence.
- `tests/test_graph_invariants.py`, `tests/test_transition_lifecycle.py`, `tests/test_builder.py`, `tests/test_async.py`, `tests/test_mypyc_guard.py` — active adjacent test contracts.
- `pyproject.toml`, `setup.py`, `Taskfile.yml`, `AGENTS.md`, `.github/copilot-instructions.md` — stack, build, validation, and workflow constraints.

### Secondary (MEDIUM confidence)

- [Python 3.12 Descriptor Guide](https://docs.python.org/3.12/howto/descriptor.html) — getter-only property behavior.
- [Python 3.12 Data Model: `__slots__`](https://docs.python.org/3.12/reference/datamodel.html#object.__slots__) — slot storage and `__dict__` behavior.
- [python-statemachine States](https://python-statemachine.readthedocs.io/en/latest/states.html) — explicit final marker and completion query.
- [python-statemachine Validations](https://python-statemachine.readthedocs.io/en/latest/validations.html) — outgoing-final prohibition and trap-state distinction.
- [python-statemachine 2.x to 3.0 Upgrade](https://python-statemachine.readthedocs.io/en/develop/releases/upgrade_2x_to_3.html) — `is_terminated` migration vocabulary.

### Tertiary (LOW confidence)

- None.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — read from project configuration and verified against local locked commands.
- Architecture: HIGH — traced through the exact current code and direct Phase 26 verification prerequisite.
- Pitfalls: HIGH — derived from locked decisions, current adapter/lifecycle code, and active regression tests.
- External comparison: MEDIUM — official documentation was reached through web search because the configured `jina`/Context7 providers were unavailable to this agent.

**Research date:** 2026-09-15
**Valid until:** 2026-10-15 (stable internal architecture; re-run if Phase 26 seams or Phase 27 CONTEXT change)
