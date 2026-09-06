# Phase 21: Priority Contract & Atomic Registration - Research

**Researched:** 2026-09-06  
**Domain:** Python/mypyc transition-topology design and atomic registrar semantics  
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

### One coherent transition API
- **D-01:** Evolve `add_transition()` with a keyword-only `priority` argument;
  do not introduce a candidate-specific registration API. Priority is a normal
  attribute of a transition, so a second API would create two competing models.
  — **Reversibility:** one-way — changing a published registration API would
  require a compatibility migration.
- **D-02:** `priority` accepts only exact non-boolean integers. It defaults to
  `0`; lower numbers have higher precedence; signed values and gaps are valid.
  Reject `bool`, numeric subclasses, floats, strings, and other coercible
  values rather than normalizing them.

### Deterministic candidate identity
- **D-03:** Registration order never participates in semantics. Distinct
  candidates with equal source, trigger, and priority fail before any topology
  is changed. An exact duplicate—same canonical source, trigger, target,
  condition object identity, and priority—is a no-op.
- **D-04:** Preserve the singleton fast path: a slot with one candidate stores
  a direct slotted `TransitionEntry`; only competing candidates promote the
  slot to a private immutable, priority-sorted group. Published groups are
  replacement values, never mutable lists. — **Reversibility:** costly — this
  representation is the contract consumed by runtime selection and all later
  topology projections.

### Atomic fan-out registration
- **D-05:** Normalize and validate the complete operation before publishing it.
  `add_transition` multi-source, `add_transitions`, bidirectional, emergency,
  and builder registration must either publish all affected candidate groups
  with one graph-version increment or leave every group and graph version
  unchanged.
- **D-06:** Clones retain the same entry/group values at clone time but have
  independent outer and per-source tables. Later registration on either
  machine must replace only its own slot and never mutate a group visible to
  the other clone.

### Contract honesty and scope separation
- **D-07:** Amend the blanket O(1)/one-transition claim in the project policy
  before adding candidate iteration. Lookup and singleton dispatch remain
  O(1); local group construction and eventual selection are O(k), with no
  unrelated graph scan or dispatch-time sorting. The runtime selection
  behavior itself belongs to Phase 22.
- **D-08:** Helpers that accept a priority carry it unchanged; their candidate
  resolution, declarative mapping, serialization, output, and telemetry use
  remain intentionally deferred to their roadmap phases.

### the agent's Discretion
- Names and private helper boundaries may follow existing `core.py` and mypyc
  conventions, provided they preserve the locked public semantics above.

### Deferred Ideas (OUT OF SCOPE)

None — dynamic priorities, equal-priority tie breaks, runtime candidate
mutation, parallel async guard evaluation, serialization parity, and telemetry
event routing are already assigned to later or future scope.
</user_constraints>

The constraints above are copied verbatim from the phase context. [VERIFIED: .planning/phases/21-priority-contract-atomic-registration/21-CONTEXT.md:17-73]

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PRIO-01 | “A library consumer can register multiple transitions for one `(source state, trigger)` through `add_transition(..., priority=...)` without a second registration API.” | Extend the existing registrar and its prepared-plan seam; retain the direct singleton representation. [VERIFIED: .planning/REQUIREMENTS.md:14-17; src/fast_fsm/core.py:1329-1461] |
| PRIO-02 | “Candidate selection is independent of registration order: priorities are exact non-boolean integers, lower values win, conflicting ties fail atomically, and exact duplicate registrations remain idempotent.” | Validate before mypyc integer coercion, merge into immutable sorted replacement values, and test every conflict/no-op path. [VERIFIED: .planning/REQUIREMENTS.md:18-20; .planning/phases/21-priority-contract-atomic-registration/21-CONTEXT.md:25-40] |
| PRIO-03 | “Batch, multi-source, bidirectional, emergency, and builder registration preserve complete candidate groups, graph-version correctness, and clone isolation.” | Replace last-write collapse with a staged slot merge; route every helper through one commit and protect clone capture with the ownership lock. [VERIFIED: .planning/REQUIREMENTS.md:21-22; src/fast_fsm/core.py:1409-1661,2469-2500,4651-4705,4837-4910] |
</phase_requirements>

## Summary

Phase 21 should change topology construction, not dispatch. The existing code already has the correct transaction boundary: `_normalize_transition_request()` builds immutable `_PreparedTransition` values and `_commit_transition_plan()` is the sole publication point for all public registrars. Its current implementation is the precise seam to replace because it collapses requests into one entry per `(source, trigger)` with last-write-wins semantics. [VERIFIED: src/fast_fsm/core.py:627-635,1329-1428]

Use a storage union: a slot is either the existing public, slotted `TransitionEntry` singleton or a private frozen/slotted group containing a tuple sorted by ascending priority. Build every replacement off-table, merge repeated keys against the already-staged replacement, reject an equal-priority conflict before writing anything, then publish all changed slot values and increment `_graph_version` once. Do not copy the whole graph and do not mutate a published group. [VERIFIED: .planning/phases/21-priority-contract-atomic-registration/21-CONTEXT.md:31-51]

The most important implementation trap is mypyc: in a compiled function, annotating the incoming value as `int` can coerce `True` before `type(priority) is int` executes. A local probe compiled with the project-pinned mypyc 1.17.1 reproduced this behavior; an implementation parameter annotated `object`, followed by the exact-type check and then a cast, rejected `True`. [VERIFIED: pinned mypyc 1.17.1 compiled probe; pyproject.toml:43-45] Mypyc documents native integer representation and its semantic differences from interpreted Python, while Python documents that `bool` is a subclass of `int`. [CITED: https://mypyc.readthedocs.io/en/stable/differences_from_python.html] [CITED: https://docs.python.org/3.10/library/stdtypes.html#boolean-type-bool]

**Primary recommendation:** plan three ordered work units: amend the performance policy/ADR; implement the immutable slot union and one staged atomic registrar; then propagate priority through in-scope helpers/builders and prove atomicity, clone isolation, slots, mypyc, and compiled exact-int behavior. [VERIFIED: .planning/phases/21-priority-contract-atomic-registration/21-CONTEXT.md:43-65]

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|--------------|----------------|-----------|
| Priority validation and canonical candidate identity | Library API / core model | — | Registration owns validation before a topology value exists. [VERIFIED: src/fast_fsm/core.py:1329-1407] |
| Immutable candidate-slot representation | Library core storage | mypyc compilation boundary | `_transitions` and all prepared records live in the sole selectively compiled module. [VERIFIED: src/fast_fsm/core.py:579-635,751-807; setup.py:16-39] |
| Atomic fan-out publication and graph version | Library transaction layer | Ownership lock | The registrar commits while holding one machine ownership envelope. [VERIFIED: src/fast_fsm/core.py:842-856,1409-1661] |
| Builder priority transport | Builder staging | Core registrar | The builder stages transitions, then materializes them into a local machine. [VERIFIED: src/fast_fsm/core.py:4490-4705,4857-4942] |
| Runtime winner selection | Phase 22, not this phase | Sync/async dispatch | The phase boundary explicitly defers winner selection. [VERIFIED: .planning/phases/21-priority-contract-atomic-registration/21-CONTEXT.md:9-12,54-58] |
| Serialization, diagnostics, and output flattening | Phases 23–24, not this phase | `_GraphSnapshot` | Later phases own projection parity; this phase only establishes storage. [VERIFIED: .planning/ROADMAP.md:69-111; .planning/phases/21-priority-contract-atomic-registration/21-CONTEXT.md:59-61,122-128] |

## Project Constraints (from AGENTS.md)

- Use `bd` for all issue tracking, use `--json` for programmatic calls, link discovered work with `discovered-from`, and do not create a second markdown or external task tracker. [VERIFIED: AGENTS.md:9-78]
- Use `uv`; do not invoke `python`, `pip`, or `python -m pytest` directly. Tests run sequentially, targeted during development, with `uv run pytest tests/ -x -q` once before push. [VERIFIED: .github/copilot-instructions.md:34-38,65-70,228-246]
- Hot-path production classes use `__slots__`; the exact registered exceptions are “CompiledFuncCondition, TransitionError, and DiagnosticBudgetExceeded”. Run `uv run python tools/release_evidence.py slots-policy --json`. [VERIFIED: .github/copilot-instructions.md:40-50]
- Preserve callback/condition `*args, **kwargs`, do not remove a public symbol without deprecation, keep conveniences additive, and document a changed public API. [VERIFIED: .github/copilot-instructions.md:54-58,255-282]
- Keep `core.py` as the only compiled module; do not split the priority storage into a new runtime module or add a runtime dependency. [VERIFIED: .planning/REQUIREMENTS.md:61-63; setup.py:16-39]
- Ruff runs in fix-then-validate phases; `task typecheck-mypy` is blocking and `task typecheck-ty` remains advisory. [VERIFIED: .github/copilot-instructions.md:184-202]
- Architecture decisions are append-only: add a new ADR and update the living SPR in the same commit. [VERIFIED: .github/copilot-instructions.md:291-314]
- Stage explicit paths only in a dirty worktree; session completion includes successful pull/rebase, beads sync, push, and a clean/up-to-date status. [VERIFIED: AGENTS.md:80-106; .github/copilot-instructions.md:102-105]

## Standard Stack

### Core

| Library/tool | Version | Purpose | Why standard here |
|--------------|---------|---------|-------------------|
| Python | “>=3.10” | Public library runtime and exact-type validation | Existing supported runtime; no new dependency. [VERIFIED: pyproject.toml:6-10] |
| mypyc | “1.17.1” | Compile `src/fast_fsm/core.py` | Build pin and sole native boundary already established. [VERIFIED: pyproject.toml:43-45; setup.py:16-39] |
| pytest | “>=8.0.0” (environment 8.4.1) | Behavioral and invariant tests | Existing dev dependency and detected runner. [VERIFIED: pyproject.toml:13-25; `uv run pytest --version`] |
| mypy | “>=1.10.0” (environment 1.17.1) | Compiled-core type compatibility | Existing blocking authority. [VERIFIED: pyproject.toml:13-25; .github/copilot-instructions.md:184-202] |
| Hypothesis | “>=6.0.0” | Registration-order/permutation properties | Already in the dev stack; the current strategy exercises transition topology. [VERIFIED: pyproject.toml:13-25; tests/test_hypothesis.py:34-58] |

### Supporting

| Tool | Version | Purpose | When to use |
|------|---------|---------|-------------|
| Ruff | 0.12.11 | Format/lint changed Python files | Every Python implementation task. [VERIFIED: `uv run ruff --version`; .github/copilot-instructions.md:184-202] |
| release-evidence slots audit | repository tool | Enforce slotted production classes | After changing `TransitionEntry` or adding the group class. [VERIFIED: .github/copilot-instructions.md:40-50] |

### Alternatives Considered

| Instead of | Could use | Tradeoff |
|------------|-----------|----------|
| Direct singleton plus private immutable group | Always store a group/list | Contradicts the locked singleton fast path and adds singleton indirection. [VERIFIED: .planning/phases/21-priority-contract-atomic-registration/21-CONTEXT.md:35-40] |
| Registration-time sorted tuple | Dispatch-time sorting | Contradicts the locked no-dispatch-sort cost contract. [VERIFIED: .planning/phases/21-priority-contract-atomic-registration/21-CONTEXT.md:54-58] |
| Local staged replacements | Whole-graph copy | Scans unrelated topology and violates the local O(k) contract. [VERIFIED: .planning/phases/21-priority-contract-atomic-registration/21-CONTEXT.md:54-58] |

**Installation:** none. This phase uses the existing standard-library/runtime and development stack. [VERIFIED: pyproject.toml:6-25]

## Package Legitimacy Audit

Not applicable: Phase 21 installs no external package. [VERIFIED: pyproject.toml:6-25; .planning/REQUIREMENTS.md:61-63]

## Architecture Patterns

### System Architecture Diagram

```text
public registrar/helper/builder
          |
          v
owner envelope -> normalize all requests -> validate exact priority
                                           |
                                           v
existing/staged slot -> merge locally -> direct entry OR sorted frozen group
                                           |
                           conflict? -------+------ no change/no-op?
                              |                         |
                       raise before write          return, no version
                              |
                              +---- otherwise publish every replacement
                                                   |
                                                   v
                                      graph_version += exactly once
```

This flow is derived from the established owner/normalize/commit seams and D-03 through D-06. [VERIFIED: src/fast_fsm/core.py:842-856,1329-1661; .planning/phases/21-priority-contract-atomic-registration/21-CONTEXT.md:31-51]

### Recommended Project Structure

```text
src/fast_fsm/core.py                 # entry, private group, prepared plan, registrar, helpers, builder
.specify/memory/constitution.md      # corrected complexity policy/version
docs/adr/ADR-007-*.md                # append-only priority topology decision
docs/spr-core-api.md                 # living API/complexity contract
tests/test_graph_invariants.py       # identity, ordering, rollback, version, clone tests
tests/test_ownership_concurrency.py  # serialization and clone capture
tests/test_builder.py                # staging/materialization atomicity
tests/test_mypyc_guard.py            # slots, visibility, sole-core, compiled exact-int guard
tests/test_hypothesis.py             # permutation property; no grouped dispatch yet
```

These paths are the canonical Phase 21 seams named by the phase context and project policy. [VERIFIED: .planning/phases/21-priority-contract-atomic-registration/21-CONTEXT.md:105-128; .github/copilot-instructions.md:291-314]

### Pattern 1: Immutable slot union with singleton fast path

Extend `TransitionEntry` without removing its existing constructor behavior: its current exact slots are `("to_state", "condition")` and constructor is `TransitionEntry(to_state, condition=None)`; add `priority` with default `0`. [VERIFIED: src/fast_fsm/core.py:579-592] Keep the competing representation private, frozen, slotted, and tuple-backed. Frozen/slotted dataclasses and tuple-typed unions compiled successfully in the pinned mypyc probe. [VERIFIED: pinned mypyc 1.17.1 compiled probe] Mypyc documents native classes without an instance dictionary and partial dataclass support. [CITED: https://mypyc.readthedocs.io/en/stable/native_classes.html]

The merge helper should return an existing value for an exact duplicate, raise for a same-priority nonduplicate, and otherwise return a new direct entry/group sorted at registration time. It must never expose or append to a mutable candidate list. [VERIFIED: .planning/phases/21-priority-contract-atomic-registration/21-CONTEXT.md:31-40]

### Pattern 2: Validate-plan-publish transaction

Change `_PreparedTransition` from the exact fields `“trigger”, “sources”, “target”, “condition”` to include validated priority. [VERIFIED: src/fast_fsm/core.py:627-635] `_commit_transition_plan()` must maintain a temporary map keyed by canonical `(source.name, trigger)`, use the staged value as the base for subsequent requests to the same key, and defer all writes until every merge succeeds. This eliminates the current last-write collapse in `final_entries`. [VERIFIED: src/fast_fsm/core.py:1409-1428]

Publish only affected slots. Increment `_graph_version` once only if at least one replacement differs by identity; all-duplicate input leaves values and version unchanged, while a mixed duplicate/new plan publishes the new work and increments once. [VERIFIED: .planning/phases/21-priority-contract-atomic-registration/21-CONTEXT.md:31-51]

### Pattern 3: Exact-int boundary before mypyc coercion

Keep the public static contract readable through overloads if necessary, but annotate the implementation input `priority: object`, run `type(priority) is int`, then cast/narrow. Never use `isinstance`, `int(priority)`, or an implementation parameter already annotated `int`. The latter accepted `True` in a compiled probe even though the same source check rejects it interpreted. [VERIFIED: pinned mypyc 1.17.1 compiled probe] Python's official type documentation says `bool` is a subclass of `int`. [CITED: https://docs.python.org/3.10/library/stdtypes.html#boolean-type-bool]

### Pattern 4: Helper transport, not downstream interpretation

Add a five-field batch form `(trigger, from_state, to_state, condition, priority)` while retaining the existing three- and four-field forms, add separate keyword-only priorities for both bidirectional legs, carry one priority through emergency registration, and add builder priority staging. The existing accepted batch forms are exactly “3-tuple `(trigger, from_state, to_state)`” and “4-tuple `(trigger, from_state, to_state, condition)`”. [VERIFIED: src/fast_fsm/core.py:1463-1537] Builder staging currently stores exactly `(trigger, from_state, to_state, condition)` and both preflight and build unpack that shape. [VERIFIED: src/fast_fsm/core.py:4651-4705,4837-4845,4887-4910]

Materialize all builder-staged transitions through one batch commit after states are installed in the local candidate machine; retain the existing rule that `_machine` is published only after construction succeeds. [VERIFIED: src/fast_fsm/core.py:4857-4942] Do not extend declarative handlers, quick factories, serialization, output, diagnostics, history, or runtime selection in this phase. [VERIFIED: .planning/phases/21-priority-contract-atomic-registration/21-CONTEXT.md:9-12,54-61]

### Pattern 5: Clone under ownership, share immutable values only

The current `clone()` copies the outer transition mapping and every per-source mapping while preserving entry values. [VERIFIED: src/fast_fsm/core.py:2469-2500] Preserve that structure for group values, but make clone capture owner-aware: a public lock-taking wrapper plus an owned internal snapshot/copy body avoids observing a commit between inner-dictionary copies and avoids self-deadlock when the current owner needs a clone. This recommendation follows the existing non-reentrant owner check and graph-snapshot locking pattern. [VERIFIED: src/fast_fsm/core.py:842-856,1256-1303,2469-2500]

### Component Responsibilities

| Symbol | Planned responsibility | Boundary |
|--------|------------------------|----------|
| `TransitionEntry` | Public/direct candidate value with target, guard, priority | Keep constructor backward compatible and slotted. [VERIFIED: src/fast_fsm/core.py:579-592; src/fast_fsm/__init__.py:7-16,67-77] |
| Private group + slot alias | Immutable sorted tuple for two or more candidates | Do not export. [VERIFIED: .planning/phases/21-priority-contract-atomic-registration/21-CONTEXT.md:35-40] |
| `_normalize_transition_request` | Canonicalize states/guard and validate priority | No topology mutation. [VERIFIED: src/fast_fsm/core.py:1329-1407] |
| `_commit_transition_plan` | Merge all affected slots, then publish once | No guard evaluation or runtime winner selection. [VERIFIED: src/fast_fsm/core.py:1409-1428; .planning/phases/21-priority-contract-atomic-registration/21-CONTEXT.md:43-47] |
| Registrar helpers | Acquire ownership once and carry priority unchanged | No nested public registrar calls. [VERIFIED: src/fast_fsm/core.py:1430-1661] |
| `FSMBuilder` | Stage priority and construct through one transition batch | Do not publish `_machine` after failure. [VERIFIED: src/fast_fsm/core.py:4651-4705,4857-4942] |

### Anti-Patterns to Avoid

- **Last-write wins:** the present `final_entries[(source, trigger)] = ...` silently erases same-slot requests; merge each request into its staged slot instead. [VERIFIED: src/fast_fsm/core.py:1409-1417]
- **Annotating unvalidated priority as `int`:** compiled coercion can erase the distinction between `True` and `1`. [VERIFIED: pinned mypyc 1.17.1 compiled probe]
- **Mutable published list:** breaks clone isolation and permits order-dependent semantics. [VERIFIED: .planning/phases/21-priority-contract-atomic-registration/21-CONTEXT.md:31-40,48-51]
- **Sorting during dispatch:** moves registration work onto the hot path and contradicts D-07. [VERIFIED: .planning/phases/21-priority-contract-atomic-registration/21-CONTEXT.md:54-58]
- **Calling public registrars from an owned helper:** the lock is deliberately non-reentrant and rejects same-thread reacquisition. [VERIFIED: src/fast_fsm/core.py:842-856]
- **Accidental Phase 22 behavior:** treating a group as its first candidate in `trigger()` would publish untested winner semantics early. Narrow explicitly and fail closed until the consuming phase updates that path. [ASSUMED]

## Don't Hand-Roll

| Problem | Don't build | Use instead | Why |
|---------|-------------|-------------|-----|
| Transaction rollback | Undo log after mutating `_transitions` | Existing prepared-plan seam plus off-table replacement map | Conflicts can be detected before any observable mutation. [VERIFIED: src/fast_fsm/core.py:1329-1428] |
| Immutability | Custom mutable wrapper/freeze flag | Frozen slotted record plus tuple | Tuple is an immutable sequence and this shape compiles in the pinned probe. [CITED: https://docs.python.org/3.10/library/stdtypes.html#tuple] [VERIFIED: pinned mypyc 1.17.1 compiled probe] |
| Exact integer coercion | Numeric conversion or `isinstance` rules | Exact built-in-type check on an `object` input | The contract rejects subclasses and coercibles. [VERIFIED: .planning/phases/21-priority-contract-atomic-registration/21-CONTEXT.md:25-28] |
| New registrar API | `add_transition_candidate()` | Existing `add_transition(..., priority=...)` | A second API is explicitly out of scope. [VERIFIED: .planning/REQUIREMENTS.md:52-54] |
| New runtime module/dependency | Priority container package | Existing `core.py` and standard-library types | The one-file mypyc/runtime constraint is explicit. [VERIFIED: .planning/REQUIREMENTS.md:61-63] |

## Common Pitfalls

### Pitfall 1: Partial publication after a late conflict

**What goes wrong:** an earlier source or helper leg changes before a later equal-priority conflict raises. **Why:** merge and publication are interleaved. **Avoidance:** normalize all requests, merge all replacements, and only then write; compare slot identities to decide one version increment. **Warning signs:** changed `_graph_version`, changed slot identity, or new source edges after an expected exception. [VERIFIED: .planning/phases/21-priority-contract-atomic-registration/21-CONTEXT.md:31-51]

### Pitfall 2: Losing repeated same-key requests inside one batch

**What goes wrong:** only the final candidate survives. **Why:** the current dict assignment collapses each key. **Avoidance:** base each new merge on `staged.get(key, existing_slot)` rather than independently on existing storage. **Warning sign:** permutations of one batch produce different topology or candidate counts. [VERIFIED: src/fast_fsm/core.py:1409-1417]

### Pitfall 3: Wrong duplicate identity for callable guards

**What goes wrong:** repeated registration of the same raw callable may be mistaken for the same stored condition. **Why:** normalization wraps a callable in a fresh `FuncCondition`; `unless` creates fresh `FuncCondition`/`NegatedCondition` wrappers. [VERIFIED: src/fast_fsm/core.py:1376-1394; src/fast_fsm/conditions.py:261-295,337-363] **Recommendation:** interpret D-03 literally as identity of the canonical stored `Condition` object (or `None`); repeated raw callables are not exact duplicates after normalization unless the design deliberately adds an identity token. [ASSUMED]

### Pitfall 4: Clone snapshot is structurally isolated but temporally torn

**What goes wrong:** a concurrent registration can land between per-source copies, producing a topology that never existed at one version. **Why:** current clone copies without the read ownership used by `_graph_snapshot`. **Avoidance:** capture clone topology/version under one owner-aware read envelope. **Warning sign:** clone version disagrees with the candidate groups it contains under concurrent stress. [VERIFIED: src/fast_fsm/core.py:1256-1303,2469-2500]

### Pitfall 5: Singular consumers break or silently lie

`to_dict`, `_graph_snapshot`, reachability/query helpers, prepared dispatch, and debug/completeness logic dereference a singular `TransitionEntry`. [VERIFIED: src/fast_fsm/core.py:1127-1159,1277-1303,1907-1954,1995-2032,3229-3286] This phase should make union handling explicit without implementing later projection or selection semantics; do not suppress the mismatch with `Any`. [ASSUMED]

### Pitfall 6: Policy and benchmark drift

The constitution currently says “Core operations (`trigger()`, `can_trigger()`, `add_state()`, `add_transition()`) MUST be O(1)” and “Transition dispatch MUST remain a single dict lookup, not a loop over candidates.” [VERIFIED: .specify/memory/constitution.md:41-47,117] Amend these before candidate iteration: O(1) source/trigger lookup and singleton dispatch, O(k) local group construction/selection, no unrelated scan or dispatch-time sort; retain the compiled singleton floor of `>=200,000 ops/sec`. [VERIFIED: .planning/phases/21-priority-contract-atomic-registration/21-CONTEXT.md:54-58; .planning/REQUIREMENTS.md:4-6]

## Code Examples

### Exact-type validation shape

```python
# Implementation sketch. The object boundary is required by the compiled probe.
def _normalize_priority(priority: object) -> int:
    if type(priority) is not int:
        raise TypeError("priority must be an exact int")
    return cast(int, priority)
```

The literals/types in this sketch come from D-02's exact phrase “only exact non-boolean integers” and from the probe; the exact error text is intentionally non-normative. [VERIFIED: .planning/phases/21-priority-contract-atomic-registration/21-CONTEXT.md:25-28; pinned mypyc 1.17.1 compiled probe]

### Staged merge/publication shape

```python
# Pseudocode: concrete private names remain at the agent's discretion.
for request in plans:
    for source in request.sources:
        key = (source.name, request.trigger)
        base = replacements.get(key, transitions[source.name].get(request.trigger))
        replacements[key] = merge(base, request)

# No writes occur above. Publish below only after every merge succeeds.
for (source_name, trigger), slot in replacements.items():
    transitions[source_name][trigger] = slot
```

This is a design skeleton, not copied source; it instantiates the locked normalize-before-publish and replacement-value rules. [ASSUMED]

## State of the Art

| Old approach | Phase 21 approach | Impact |
|--------------|-------------------|--------|
| One `TransitionEntry` per `(source, trigger)` and last-write collapse | Direct singleton or immutable priority-sorted group | Preserves the singleton path while allowing deterministic candidate topology. [VERIFIED: src/fast_fsm/core.py:805-807,1409-1428; .planning/phases/21-priority-contract-atomic-registration/21-CONTEXT.md:31-40] |
| Blanket O(1)/one-transition policy | O(1) slot lookup/singleton dispatch; O(k) local group work | Makes the contract truthful before Phase 22 adds candidate iteration. [VERIFIED: .specify/memory/constitution.md:41-47,117; .planning/phases/21-priority-contract-atomic-registration/21-CONTEXT.md:54-58] |
| Builder calls `add_transition` once per staged edge | One batch transition materialization | A builder build becomes one transition-registration transaction. [VERIFIED: src/fast_fsm/core.py:4887-4910; .planning/phases/21-priority-contract-atomic-registration/21-CONTEXT.md:43-47] |

## Assumptions Log

| # | Claim | Section | Risk if wrong |
|---|-------|---------|---------------|
| A1 | Duplicate identity should use the post-normalization stored `Condition` identity, so repeated raw callables at the same priority conflict rather than no-op. | Common Pitfalls | If users expect raw-callable identity, `_PreparedTransition` needs an additional canonical identity/polarity token and tests. |
| A2 | Until Phases 22–24 update singular consumers, grouped values should be explicitly narrowed and fail closed rather than selecting or flattening implicitly. | Anti-Patterns / Common Pitfalls | A different integration strategy may be needed to keep intermediate milestone tests green. |
| A3 | The pseudocode helper/private symbol names are illustrative; exact names may follow local mypyc conventions. | Code Examples | No semantic risk if the locked behavior is preserved. |

## Open Questions

1. **What does “condition object identity” mean for a raw callable?** The code converts raw callables and `unless` inputs to fresh wrapper objects during every normalization. [VERIFIED: src/fast_fsm/core.py:1376-1394] Recommendation: lock stored canonical `Condition` identity for Phase 21; if raw-callable idempotence is intended, add an explicit normalized identity token rather than comparing wrapper internals. [ASSUMED]
2. **How should intermediate grouped values behave in consumers owned by later phases?** Those consumers currently assume a direct entry. [VERIFIED: src/fast_fsm/core.py:1127-1159,1277-1303,1907-1954,1995-2032,3229-3286] Recommendation: add explicit private narrowing and fail-closed branches now; do not silently pick the first candidate or implement projection parity early. [ASSUMED]

Neither question blocks planning; both recommendations preserve the phase boundary and make later work explicit. [ASSUMED]

## Environment Availability

| Dependency | Required by | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| `uv` | All project commands | yes | 0.12.9 | none needed. [VERIFIED: `uv --version`] |
| Python via `uv` | Source/tests/probe | yes | 3.12.10 | Project supports “>=3.10”. [VERIFIED: `uv run python --version`; pyproject.toml:6-10] |
| mypy/mypyc | Type/compiled checks | yes | 1.17.1 | none needed. [VERIFIED: `uv run mypy --version`; pyproject.toml:43-45] |
| pytest | Behavioral tests | yes | 8.4.1 | none needed. [VERIFIED: `uv run pytest --version`] |
| Ruff | Formatting/lint | yes | 0.12.11 | none needed. [VERIFIED: `uv run ruff --version`] |
| C compiler | mypyc probe/artifact build | yes | Apple clang 21.0.0 | project build task. [VERIFIED: `cc --version`] |
| Task | Repository quality commands | yes | 3.53.1 | invoke underlying `uv` commands if a task is unavailable. [VERIFIED: `task --version`] |
| bd | Required issue tracking | yes | 1.0.4 | none permitted. [VERIFIED: `bd --version`; AGENTS.md:9-78] |

No missing dependency blocks execution. [VERIFIED: environment probes above]

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.4.1 with Hypothesis >=6.0.0 [VERIFIED: `uv run pytest --version`; pyproject.toml:13-25] |
| Config file | `pyproject.toml` [VERIFIED: pyproject.toml:47-89] |
| Quick run | `uv run pytest tests/test_graph_invariants.py tests/test_ownership_concurrency.py tests/test_builder.py tests/test_mypyc_guard.py -x -q` [VERIFIED: .github/copilot-instructions.md:228-246] |
| Full suite | `uv run pytest tests/ -x -q` [VERIFIED: .github/copilot-instructions.md:65-70] |

The quick baseline passed before implementation, as did `uv run mypy src/fast_fsm/core.py` and `uv run python tools/release_evidence.py slots-policy --json`. [VERIFIED: local command execution 2026-09-06]

### Phase Requirements → Test Map

| Req | Behavior | Test type | Automated command | File exists? |
|-----|----------|-----------|-------------------|--------------|
| PRIO-01 | Same slot accepts multiple priority candidates; singleton remains direct and default is `0` | unit/invariant | `uv run pytest tests/test_graph_invariants.py -x -q` | yes; new cases required. [VERIFIED: tests/test_graph_invariants.py:75-212] |
| PRIO-02 | Exact-int rejection, sorted topology, conflict rollback, idempotent duplicate, permutation independence | unit/property/compiled probe | `uv run pytest tests/test_graph_invariants.py tests/test_hypothesis.py tests/test_mypyc_guard.py -x -q` | yes; new cases required. [VERIFIED: tests/test_hypothesis.py:34-58; tests/test_mypyc_guard.py:382-434,721-753,1305-1336] |
| PRIO-03 | Helper/builder one-commit behavior, concurrent serialization, clone isolation | unit/concurrency | `uv run pytest tests/test_graph_invariants.py tests/test_ownership_concurrency.py tests/test_builder.py -x -q` | yes; new cases required. [VERIFIED: tests/test_graph_invariants.py:75-212; tests/test_builder.py:122-169; tests/test_ownership_concurrency.py:1-260] |

### Required Test Cases

- Direct singleton/default `0`; signed priorities and gaps; immutable sorted group for two and three candidates; registration-order permutations yield the same ordered identities. [VERIFIED: .planning/phases/21-priority-contract-atomic-registration/21-CONTEXT.md:25-40]
- Reject `bool`, `float`, `str`, `IntEnum`, an `int` subclass, and a coercible object before mutation in both pure and compiled core. [VERIFIED: .planning/phases/21-priority-contract-atomic-registration/21-CONTEXT.md:25-28; pinned mypyc 1.17.1 compiled probe]
- Exact duplicate retains the same slot object and graph version; same-priority different target/condition raises; same target/condition at another priority is allowed. [VERIFIED: .planning/phases/21-priority-contract-atomic-registration/21-CONTEXT.md:31-40]
- Conflict rollback for existing slots, repeated keys within a batch, multi-source, bidirectional, emergency, and builder; mixed duplicate/new input increments once. [VERIFIED: .planning/phases/21-priority-contract-atomic-registration/21-CONTEXT.md:43-47]
- Clone owns distinct outer/inner dicts, initially shares immutable slot/group values, and replaces only its own slot/version after later registration in either direction; concurrent clone capture is not torn. [VERIFIED: .planning/phases/21-priority-contract-atomic-registration/21-CONTEXT.md:48-51]
- Builder five-field staging/fingerprint, invalid-priority staging rollback, grouped materialization, repair after failed build, and one transition commit. [VERIFIED: src/fast_fsm/core.py:4651-4705,4837-4942; tests/test_builder.py:122-169]
- Guard tests enforce the exact `TransitionEntry` slots, the new private frozen/slotted group, no export, sole compiled `core.py`, preserved ownership wrappers, and compiled `bool` rejection. [VERIFIED: tests/test_mypyc_guard.py:382-434,721-753,1305-1336]

### Sampling Rate

- **Per task commit:** the smallest listed target file(s), always sequential. [VERIFIED: .github/copilot-instructions.md:65-70,228-246]
- **Per wave merge:** quick run plus blocking `task typecheck-mypy` and slots audit. [VERIFIED: .github/copilot-instructions.md:40-50,184-202]
- **Phase gate:** full suite once, compiled/pure relevant parity, and singleton performance evidence. [VERIFIED: .github/copilot-instructions.md:40-70]

### Wave 0 Gaps

- Extend existing files; no new framework/config is required. [VERIFIED: test map above]
- Adjust the current Hypothesis strategy so legacy runtime-state tests do not accidentally generate grouped slots before Phase 22; add a registration-only permutation property separately. [VERIFIED: tests/test_hypothesis.py:34-58; .planning/phases/21-priority-contract-atomic-registration/21-CONTEXT.md:54-58]
- Add a compiled exact-int regression because interpreted tests alone cannot expose mypyc's early coercion. [VERIFIED: pinned mypyc 1.17.1 compiled probe]

## Security Domain

This is an in-process library topology mutation with no authentication, session, network, persistence, or cryptographic boundary. [VERIFIED: .planning/REQUIREMENTS.md:14-22,61-63; src/fast_fsm/core.py:1329-1661]

### Applicable ASVS Categories

| ASVS category | Applies | Standard control |
|---------------|---------|------------------|
| V2 Authentication | no | No identity boundary in phase scope. [VERIFIED: .planning/REQUIREMENTS.md:14-22] |
| V3 Session Management | no | No session state in phase scope. [VERIFIED: .planning/REQUIREMENTS.md:14-22] |
| V4 Access Control | no | No authorization decision in phase scope. [VERIFIED: .planning/REQUIREMENTS.md:14-22] |
| V5 Input Validation / ASVS 5.0 V2.1–V2.2 | yes | Exact positive type validation plus documented business limits. [CITED: https://github.com/OWASP/ASVS/blob/master/5.0/docs_en/OWASP_Application_Security_Verification_Standard_5.0.0_en.flat.json] |
| Atomic business transaction / ASVS 5.0 V2.3.3 | yes | Validate-plan-publish under one ownership envelope. [CITED: https://github.com/OWASP/ASVS/blob/master/5.0/docs_en/OWASP_Application_Security_Verification_Standard_5.0.0_en.flat.json] |
| V6 Cryptography | no | No cryptographic operation in phase scope. [VERIFIED: .planning/REQUIREMENTS.md:14-22] |

### Known Threat Patterns

| Pattern | STRIDE | Mitigation |
|---------|--------|------------|
| Coercible/boolean priority bypass | Tampering | Exact built-in type check before compiled narrowing. [VERIFIED: pinned mypyc 1.17.1 compiled probe] |
| Partial topology after conflict | Tampering | Off-table plan and one publication boundary. [VERIFIED: .planning/phases/21-priority-contract-atomic-registration/21-CONTEXT.md:43-47] |
| Order-dependent equal-priority winner | Tampering | Reject every distinct equal-priority candidate. [VERIFIED: .planning/phases/21-priority-contract-atomic-registration/21-CONTEXT.md:31-34] |
| Mutable group shared by clone | Tampering | Frozen tuple group and replacement-only updates. [VERIFIED: .planning/phases/21-priority-contract-atomic-registration/21-CONTEXT.md:35-51] |

## Sources

### Primary (HIGH confidence)

- `.planning/phases/21-priority-contract-atomic-registration/21-CONTEXT.md` — locked scope and semantics. [VERIFIED: lines 9-73]
- `.planning/REQUIREMENTS.md` and `.planning/ROADMAP.md` — PRIO requirements and phase boundary. [VERIFIED: REQUIREMENTS.md:14-22; ROADMAP.md:57-67]
- `src/fast_fsm/core.py`, `src/fast_fsm/conditions.py`, and named test files — storage, transaction, wrapper, builder, clone, and guard seams. [VERIFIED: cited line ranges throughout]
- Project configuration/policy files — build pin, sole compiled module, workflow and complexity policy. [VERIFIED: pyproject.toml:1-45; setup.py:16-39; .github/copilot-instructions.md:34-70,184-314; .specify/memory/constitution.md:41-47,117,159-164,316]
- Compiled temporary probe using the repository's pinned mypyc 1.17.1 — dataclass/union compatibility and exact-int coercion behavior. [VERIFIED: local compiled execution 2026-09-06]

### Secondary (MEDIUM confidence)

- Mypyc native-class, annotation, and semantic-difference documentation. [CITED: https://mypyc.readthedocs.io/en/stable/native_classes.html] [CITED: https://mypyc.readthedocs.io/en/stable/using_type_annotations.html] [CITED: https://mypyc.readthedocs.io/en/stable/differences_from_python.html]
- Python standard type documentation for `bool`, `int`, and tuple immutability. [CITED: https://docs.python.org/3.10/library/stdtypes.html]
- OWASP ASVS 5.0 JSON for validation and atomic business transaction categories. [CITED: https://github.com/OWASP/ASVS/blob/master/5.0/docs_en/OWASP_Application_Security_Verification_Standard_5.0.0_en.flat.json]

### Tertiary (LOW confidence)

- None used as authority. [VERIFIED: research source log]

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — read from repository pins and probed locally. [VERIFIED: pyproject.toml:1-45; environment probes]
- Architecture: HIGH — locked design mapped directly to the existing transaction/ownership seams and compiled experimentally. [VERIFIED: CONTEXT and core citations throughout]
- Pitfalls: HIGH for last-write, clone, singular-consumer, and mypyc issues; MEDIUM for the recommended raw-callable identity interpretation. [VERIFIED: source/probe citations throughout] [ASSUMED]
- Validation: HIGH — existing tests and commands were inspected and the targeted baseline passed. [VERIFIED: local command execution 2026-09-06]

**Research date:** 2026-09-06  
**Valid until:** 2026-10-06; the repository and pinned compiler are stable inputs, but re-run the compiled probe if the mypyc pin changes. [ASSUMED]

## RESEARCH COMPLETE
