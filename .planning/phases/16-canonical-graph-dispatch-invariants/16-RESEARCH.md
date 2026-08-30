# Phase 16: Canonical Graph & Dispatch Invariants - Research

**Researched:** 2026-08-29
**Domain:** Canonical in-memory graph topology, sync/async dispatch parity, transactional builder materialization, and bounded history
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

### Canonical State Registry and Atomic Topology Mutation
- **D-01:** State names identify canonical registered objects. Registering the exact same object again is an idempotent no-op; registering a different object with an existing name raises `ValueError` and leaves the registry, transitions, graph version, and current state unchanged.
- **D-02:** Every transition source and target—whether supplied as a string or `State` object—must resolve to the canonical registry before any mutation. A `State` object with a matching name but different identity is not accepted as an endpoint.
- **D-03:** Multi-source transition additions validate and normalize the complete endpoint set, guard configuration, and duplicate sources before inserting any entry. One invalid endpoint rejects the whole call without partial transitions.
- **D-04:** Existing convenience constructors may collect/register their complete declared state set before adding transitions, but ordinary `add_transition()` never implicitly registers an endpoint.

### Immutable Graph Snapshot and Version
- **D-05:** Maintain a monotonic per-machine graph version. It advances once for each successful topology-changing public operation, does not advance for rejection or idempotent same-object registration, and never tracks runtime current-state changes.
- **D-06:** Provide one private/internal immutable graph snapshot for library tools. It contains the graph version, machine name, declared initial state, canonical state objects/names, and canonical transition endpoints/guards in deterministic state-name/trigger order.
- **D-07:** The snapshot is a tool-facing internal contract, not a new public serialization compatibility promise. `to_dict()` and the existing runtime `snapshot()` keep their public roles; Phase 19 migrates validation/visualization to consume the internal graph snapshot.
- **D-08:** Preserve the declared initial state independently from the mutable current state so all later tools can reason from construction identity rather than execution position.

### Builder Freeze and Async Detection
- **D-09:** A builder freezes only after a completely successful build. Every builder mutator, callback registrar, and force-mode method then raises `RuntimeError` immediately; a failed build remains repairable and does not cache a partial machine.
- **D-10:** Repeated successful `build()` calls return the same cached machine object. Build materialization must use local state until all registration and wiring succeeds, assigning the cache only at the end.
- **D-11:** Auto mode recursively detects asynchronous requirements through `unless=`/`NegatedCondition`, supported condition wrappers, declarative handlers, and queued async callbacks, with identity-based cycle protection. Explicit async mode remains authoritative; explicit sync mode fails at build time when any nested async requirement exists rather than warning and dropping behavior.

### Shared Resolution and Guard Context
- **D-12:** Sync/async `can_trigger*()` and `trigger*()` use the same internal transition-resolution and guard-context seams so “can” and “do” cannot disagree because they prepared different inputs.
- **D-13:** Guards receive positional arguments unchanged and one freshly copied, deterministic sanitized keyword mapping on all four paths. Apply the existing safety policy consistently: remove private/dunder and overlong keys, then cap the retained insertion-ordered entries; never mutate the caller's mapping.
- **D-14:** Sanitization is performed once per guard evaluation and the resulting context is passed to every wrapper layer. Raw payload values must not be introduced into logs by this refactor; Phase 19 owns broader trace-redaction policy.

### Declarative Ordinary Dispatch
- **D-15:** A matched declarative transition handler participates in ordinary sync/async trigger dispatch exactly once through the shared dispatch seam. Compatibility helpers must delegate to that seam rather than invoking the handler independently.
- **D-16:** Phase 16 proves one invocation and sync/async parity but does not lock the handler's precise pre-commit/post-commit position or callback-failure result model; Phase 17 defines that lifecycle atomically.

### Bounded History
- **D-17:** `enable_history(max_entries)` raises `ValueError` immediately for zero or negative capacity and, for a valid capacity, replaces any existing buffer with an empty bounded FIFO buffer.
- **D-18:** Eviction is O(1), chronological order is preserved, history remains disabled at zero steady-state cost, and the public `history` property continues to return a defensive `list` copy.

### the agent's Discretion
- Exact private snapshot/container types, private seam names, and internal type annotations, provided snapshot contents cannot be mutated through returned references and compile under mypyc.
- Exact graph-version starting value and whether compound convenience constructors expose one or several internal increments; externally observable requirements are monotonicity, rejection/idempotence stability, and snapshot freshness.
- The registry/snapshot test layout and helper organization within existing flat test modules or a focused new `test_graph_invariants.py` module.
- The private recursive-condition traversal protocol for built-in wrappers, provided it is cycle-safe and does not create a new public wrapper API.

### Deferred Ideas (OUT OF SCOPE)
- Exact declarative/callback lifecycle order, commit boundary, and failure semantics — Phase 17.
- Reentrant/concurrent mutation ownership and locking around topology/version changes — Phase 18.
- Migration of validators, comparison, JSON, and visualization onto the graph snapshot, including budgets — Phase 19.
- A public versioned topology snapshot format — future requirement FUTR-05; Phase 16 creates only the internal contract.
- Compiled/pure installed-artifact parity and final performance proof — Phase 20.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| GRAF-01 | “A user cannot add a transition whose source or target is absent from the canonical state registry, and a rejected addition leaves the graph unchanged.” [VERIFIED: .planning/REQUIREMENTS.md:22] | Preflight/commit topology transaction and identity-canonical endpoint resolver. |
| GRAF-02 | “A user cannot replace a registered state with a different object using the same name; idempotent registration of the same object remains safe.” [VERIFIED: .planning/REQUIREMENTS.md:23] | Three-way registration result: inserted, same-object no-op, conflicting-identity error. |
| GRAF-03 | “Runtime tools can consume one immutable graph snapshot containing canonical endpoints, declared initial state, deterministic ordering, and a graph version.” [VERIFIED: .planning/REQUIREMENTS.md:24] | Private tuple-shaped snapshot, deterministic traversal, declared-initial reference, monotonic version. |
| GRAF-04 | “After `FSMBuilder.build()`, every builder mutator fails immediately while repeated `build()` calls remain idempotent.” [VERIFIED: .planning/REQUIREMENTS.md:25] | One freeze guard on every mutator plus cache assignment only after successful materialization. |
| GRAF-05 | “`FSMBuilder` recursively detects asynchronous conditions through `unless=` and condition wrappers and builds the correct machine type.” [VERIFIED: .planning/REQUIREMENTS.md:26] | Cycle-safe condition graph traversal plus runtime recursive async evaluation. |
| GRAF-06 | “Guards receive positional arguments and one consistently sanitized keyword context across sync/async `can_trigger*()` and `trigger*()` paths.” [VERIFIED: .planning/REQUIREMENTS.md:27] | One context-preparation seam and paired sync/async evaluators that preserve `*args`. |
| GRAF-07 | “Declarative transition handlers execute exactly once during ordinary sync and async trigger dispatch.” [VERIFIED: .planning/REQUIREMENTS.md:28] | One state-level declarative-handler resolution/invocation seam shared by ordinary dispatch and compatibility helpers. |
| GRAF-08 | “Shared internal resolution and dispatch seams keep sync, async, builder, and declarative behavior aligned without splitting the mypyc `core.py` compilation unit.” [VERIFIED: .planning/REQUIREMENTS.md:29] | Keep dispatch orchestration in `core.py`; keep interpreted condition subclasses and wrapper definitions outside it. |
| LIFE-07 | “History rejects non-positive capacities and uses O(1) bounded eviction while preserving copy-on-read behavior.” [VERIFIED: .planning/REQUIREMENTS.md:39] | Validate before assignment, then use `collections.deque(maxlen=...)` internally and `list(...)` at the property boundary. |
</phase_requirements>

## Summary

Phase 16 should be planned as a convergence refactor around four private seams, not as independent patches to each public API: (1) canonical state/endpoint resolution plus a validate-then-commit topology path, (2) common trigger lookup/context preparation plus paired sync/async guard evaluators, (3) a single declarative handler selection/invocation boundary, and (4) a transactional builder preflight/materialization path. The current implementation has the exact split-brain risks this design removes: state registration overwrites by name, transition insertion creates missing source buckets and accepts unregistered `State` targets, and async “can”/“do” paths duplicate the sync preparation logic. [VERIFIED: src/fast_fsm/core.py:603-751,1110-1181,1792-1954]

The highest-risk interaction is recursive async support. Detecting an `AsyncCondition` under `NegatedCondition`, `AndCondition`, `OrCondition`, or `NotCondition` is insufficient unless runtime evaluation also recurses and awaits async leaves while retaining boolean short-circuit behavior. The current wrappers call their children synchronously, while `NegatedCondition.check()` invokes its inner condition through a synchronous path; therefore builder classification and runtime evaluation must be delivered and tested together. [VERIFIED: src/fast_fsm/conditions.py:75-158; src/fast_fsm/condition_templates.py:118-160]

The graph snapshot should be a fresh, private, structurally immutable tuple-shaped view, not a replacement graph store and not a public serializer. Preserve the O(1) dictionaries as the mutation/dispatch source of truth; assemble sorted immutable records only when a tool asks for the snapshot. [VERIFIED: .planning/phases/16-canonical-graph-dispatch-invariants/16-CONTEXT.md:27-31,92-105] The recommended record shape and the interpretation of “immutable” as structural rather than deep immutability are planner recommendations that require the contract test described below. [ASSUMED]

**Primary recommendation:** Plan one contract-first vertical sequence: canonical topology → shared guard evaluation → transactional builder → declarative integration → deque history → pure/compiled conformance gates. [ASSUMED]

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Canonical state topology and version | In-process core runtime | Tool-facing snapshot | `_states`/`_transitions` remain the O(1) authority; snapshot traversal is off the hot path. [VERIFIED: .planning/phases/16-canonical-graph-dispatch-invariants/16-CONTEXT.md:92-105] |
| Guard context and dispatch resolution | In-process core runtime | Interpreted condition modules | `core.py` owns dispatch while condition bases must remain interpreted and user-subclassable. [VERIFIED: .specify/decisions/ADR-003-mypyc-compilation-boundary.md:26-42,158-177] |
| Builder freeze/materialization | Construction API | Core runtime | `FSMBuilder` stages definitions and caches a machine in `core.py`. [VERIFIED: src/fast_fsm/core.py:2278-2686] |
| Declarative handler invocation | Core dispatch seam | Declarative state metadata | Handler metadata and helper invocation currently live on declarative state classes, while ordinary dispatch lives on machines. [VERIFIED: src/fast_fsm/core.py:2016-2275] |
| Bounded history | In-process core runtime | Public copy boundary | Records are appended during commit and exposed through a defensive list property. [VERIFIED: src/fast_fsm/core.py:603-632,1488-1496] |

## Project Constraints (from AGENTS.md)

- Use `uv` for every Python/package/test command; direct `python`, `pip`, and `python -m pytest` are forbidden. [VERIFIED: .github/copilot-instructions.md:32-39]
- Hot-path production classes require `__slots__`; compiled `trigger()` must remain at least `200,000 ops/sec`; `trigger()`, `can_trigger()`, `add_state()`, and `add_transition()` must remain O(1). The quoted values are “`200,000 ops/sec`” and “`O(1)`.” [VERIFIED: .github/copilot-instructions.md:40-48]
- All condition and callback signatures accept the verbatim form “`*args, **kwargs`”; public symbol removal requires deprecation. [VERIFIED: .github/copilot-instructions.md:50-53]
- Run targeted tests during implementation, sequentially, and the full suite once before integration. [VERIFIED: .github/copilot-instructions.md:55-61]
- Mypy is the blocking mypyc-compatibility authority; ty is advisory. [VERIFIED: .github/copilot-instructions.md:206-221]
- Pure evidence must use the non-destructive source-origin preflight; reported native shadows are not to be deleted implicitly. [VERIFIED: .github/copilot-instructions.md:63-71]
- Work tracking uses `bd`; do not create Markdown TODO/task-list tracking. [VERIFIED: AGENTS.md:8-52]

## Current-State Diagnosis

| Area | Current behavior | Planning consequence |
|------|------------------|----------------------|
| Registry | `_register_state` assigns `self._states[state.name] = state` without an identity conflict check. [VERIFIED: src/fast_fsm/core.py:634-638] | Introduce a single canonical registration primitive before snapshot/version work. |
| Transition endpoints | Object sources become names, string targets are looked up, object targets are accepted directly, and missing source buckets are created during insertion. [VERIFIED: src/fast_fsm/core.py:649-751] | Normalize all endpoints to canonical objects before any dictionary write. |
| Multi-source atomicity | The insertion loop mutates each source bucket as it goes. [VERIFIED: src/fast_fsm/core.py:728-751] | Validate sources, duplicate names, target, and guard into an immutable plan first. |
| Graph identity | Constructor stores declared initial and current state separately but has no graph-version slot. [VERIFIED: src/fast_fsm/core.py:273-341] | Retain `_initial_state`; add `_graph_version` without coupling it to current state. |
| Public runtime snapshot | Existing `snapshot()` emits runtime state with the literal schema version `1`. [VERIFIED: src/fast_fsm/core.py:1219-1234] | Do not overload or change it; add a private graph snapshot. |
| Sync/async guards | Sync sanitizes keyword context; async paths evaluate against raw keyword arguments. [VERIFIED: src/fast_fsm/core.py:1110-1181,1792-1954] | Centralize context creation and make evaluation strategy the only sync/async difference. |
| Sanitizer ordering | It slices the first 50 raw items before filtering private, non-string, and overlong keys. The verbatim cap is `max_items = 50`, and the key-length limit is `100`. [VERIFIED: src/fast_fsm/core.py:1136-1181] | Filter first, then cap retained insertion order as D-13 requires. |
| Builder transaction | `build()` assigns `_machine` before all states/transitions/callbacks are installed. [VERIFIED: src/fast_fsm/core.py:2605-2686] | Build into a local candidate and cache only at the final line. |
| Builder async detection | Detection checks direct async conditions and declarative metadata but does not traverse built-in wrapper edges. [VERIFIED: src/fast_fsm/core.py:2362-2390] | Add a cycle-safe graph walk and explicit-sync preflight. |
| Declarative dispatch | Declarative `handle_event` invokes its handler directly, separate from ordinary machine trigger execution. [VERIFIED: src/fast_fsm/core.py:2096-2159,2215-2275] | Route both through one private handler seam; assert exactly once only. |
| History | History uses a list; full buffers execute `del self._history[0]`, and `enable_history` does not reject a non-positive capacity. [VERIFIED: src/fast_fsm/core.py:603-632,1488-1496] | Replace storage with a bounded deque after validating capacity. |

## Standard Stack

### Core

| Component | Version / shape | Purpose | Why Standard |
|-----------|-----------------|---------|--------------|
| Python | `>=3.10` [VERIFIED: pyproject.toml:1-9] | Runtime language and standard containers | This is the shipped project floor; do not introduce syntax above it. |
| Existing dictionaries | `dict[str, State]` plus per-source trigger dictionaries [VERIFIED: src/fast_fsm/core.py:273-341,634-751] | O(1) registry and dispatch | Preserves the project hot-path contract. [VERIFIED: .github/copilot-instructions.md:40-48] |
| `typing.NamedTuple` or equivalently tuple-backed private records | Private only [ASSUMED] | Structurally immutable graph snapshot rows | Prefer tuple-backed fields over a mutable dict/list export; compile-check the exact chosen form. |
| `collections.deque` | Standard library, bounded with `maxlen` [CITED: https://docs.python.org/3.10/library/collections.html#collections.deque] | O(1) history eviction | Python documents approximately O(1) appends/pops at either end and bounded opposite-end discard. |
| pytest / pytest-asyncio / Hypothesis | Existing lower bounds are respectively `>=8.4.1`, `>=1.3.0`, and `>=6.136.6`. [VERIFIED: pyproject.toml:11-20] | Contract, async parity, and sequence/stateful tests | They are already in the development stack; no runtime dependency is needed. |
| mypy/mypyc | Release pin `1.17.1` [VERIFIED: pyproject.toml:21-25,42-44] | Compilation-boundary verification | The release build deliberately pins this version. |

### Supporting

| Component | Purpose | When to Use |
|-----------|---------|-------------|
| Existing release evidence harness | Pure-source import, slots, quality, and benchmark evidence. [VERIFIED: evidence/release-baseline.json:39-73] | Final phase gate; do not rewrite benchmark policy in Phase 16. |
| Existing `Taskfile.yml` release gate | Orders pure preflight, format/lint, mypy, tests, docs, and evidence checks. [VERIFIED: Taskfile.yml:281-291] | End-of-phase validation in a reviewed clean environment. |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Tuple-shaped snapshot records | Frozen slotted dataclasses | Python states that `frozen=True` only emulates immutability and that `slots=True` generates slots; mypyc documents only partial dataclass support, so this shape adds avoidable compile risk in `core.py`. [CITED: https://docs.python.org/3.10/library/dataclasses.html] [CITED: https://mypyc.readthedocs.io/en/stable/native_classes.html#dataclasses] |
| Existing dictionaries | A graph library | Rejected by the locked O(1) hot-path and no-new-runtime-dependency posture. [VERIFIED: .planning/phases/16-canonical-graph-dispatch-invariants/16-CONTEXT.md:92-105; pyproject.toml:1-9] |
| `deque(maxlen=...)` | Manual ring buffer | The standard library already supplies bounded O(1) endpoint operations. [CITED: https://docs.python.org/3.10/library/collections.html#collections.deque] |

**Installation:** None. Phase 16 needs no new package. [ASSUMED]

## Architecture Patterns

### System Architecture Diagram

```text
Public construction call
  ├─ add_state ────────────────┐
  ├─ add_transition ──┐        │
  └─ builder.build ───┴─> preflight/normalize
                              │ valid complete plan?
                         no ──┴──> raise; no graph/cache mutation
                         yes
                              v
                    canonical commit dictionaries
                              │
                    advance graph version once
                              │
            private snapshot request ─> sorted tuple-shaped view

Public can/trigger call
  -> common trigger lookup
  -> copy/filter/cap kwargs once + preserve args
  -> sync evaluator OR recursive async evaluator
  -> state/declarative guard decision
  -> ordinary dispatch
  -> matched declarative handler seam (exactly once)
  -> existing lifecycle execution (exact ordering deferred to Phase 17)
  -> bounded deque history append
```

This diagram is a recommended decomposition derived from the locked decisions. [ASSUMED]

### Recommended Project Structure

```text
src/fast_fsm/
├── core.py                  # canonical graph, dispatch seams, builder, declarative integration, history
├── conditions.py            # interpreted base/leaf/negation conditions; propagate *args
└── condition_templates.py   # interpreted built-in wrapper edges; propagate *args
tests/
├── test_graph_invariants.py # focused new registry/version/snapshot/atomicity contracts
├── test_builder.py          # freeze, transaction, recursive async, declarative integration
├── test_safety_kwargs.py    # shared guard-context contract
├── test_async.py            # async parity and recursive await behavior
└── test_advanced_functionality.py # history and convenience-constructor regression coverage
```

The repository currently uses this flat source/test layout, and CONTEXT explicitly permits a focused `test_graph_invariants.py`. [VERIFIED: .github/copilot-instructions.md:15-27; .planning/phases/16-canonical-graph-dispatch-invariants/16-CONTEXT.md:51-55]

### Pattern 1: Normalize, Validate, Commit

**What:** Separate a mutation into an immutable normalized plan and a short commit. Resolve every source and target to the exact object in `_states`, normalize condition/unless once, reject duplicate source names, and compute whether any entry actually changes before writing. [ASSUMED]

**Required invariants:**

1. `_register_state` returns “inserted” for a new name, “unchanged” for identical object identity, and raises `ValueError` for a conflicting identity. [ASSUMED]
2. Endpoint resolution accepts a name only when registered, and accepts a `State` object only when `registry[state.name] is state`. [ASSUMED]
3. Multi-source input is fully materialized before validation so a later invalid endpoint cannot follow an earlier write. [ASSUMED]
4. The commit advances `_graph_version` once if and only if the public operation changes topology. Re-adding an exactly identical transition entry is best treated as no topology change. [ASSUMED]

**Recommended skeleton:**

```python
# Recommended private skeleton; names and exact types are discretionary. [ASSUMED]
normalized = _normalize_transition_request(source, target, condition, unless)
changes = _transition_changes(normalized)
if changes:
    _commit_transition_plan(normalized)
    self._graph_version += 1
```

Convenience constructors should first register their complete declared state set, then invoke transition mutation; ordinary `add_transition` must never register an endpoint. [VERIFIED: .planning/phases/16-canonical-graph-dispatch-invariants/16-CONTEXT.md:21-25]

### Pattern 2: Fresh Deterministic Internal Snapshot

**What:** Create a fresh private top-level record on request with scalar metadata, an initial-state pair, a tuple of `(name, canonical State)` rows sorted by name, and transition records sorted by `(source_name, trigger)`. Each transition row should include source name/object, trigger, target name/object, and guard reference. [ASSUMED]

**Why fresh:** A fresh traversal makes snapshot freshness depend only on the authoritative dictionaries/version and avoids cache invalidation. Snapshot creation is a tool operation, not a dispatch hot-path operation. [ASSUMED]

**Structural immutability test:** assignment to record fields must fail, collection fields must expose tuples rather than lists/dicts, and mutation attempts must not change later snapshots or machine topology. Canonical `State` and `Condition` references are intentionally identity-bearing; deep-freezing those user-extensible objects would conflict with the requirement to include them. This interpretation should be stated in the private docstring and contract test. [ASSUMED]

**Version semantics:** Start at `0`, treat constructor registration of the declared initial state as baseline rather than a public topology operation, copy the version on `clone()`, and increment once per topology-changing public operation. The starting value and compound-operation increment exposure are discretionary, while monotonicity and rejection stability are locked. [VERIFIED: .planning/phases/16-canonical-graph-dispatch-invariants/16-CONTEXT.md:27-31,51-55] [ASSUMED]

### Pattern 3: One Preparation Seam, Two Evaluators

**What:** Trigger resolution should produce one prepared record containing the selected transition, source/target, unchanged positional tuple, and a freshly copied sanitized keyword dictionary. Then call either a synchronous evaluator or an asynchronous recursive evaluator. [ASSUMED]

**Sanitization algorithm:** Iterate caller keyword items in insertion order; retain only string keys that do not start with `_` and whose length is at most `100`; stop after `50` retained entries. These quoted existing limits are `100` and `50`, while the filter-before-cap ordering is locked. [VERIFIED: src/fast_fsm/core.py:1136-1181; .planning/phases/16-canonical-graph-dispatch-invariants/16-CONTEXT.md:38-41]

**Condition signatures:** Update `Condition`, `FuncCondition`, `CompiledFuncCondition`, `NegatedCondition`, `AsyncCondition`, and the And/Or/Not templates to accept and propagate `*args, **kwargs`; their current definitions accept keyword-only payloads. [VERIFIED: src/fast_fsm/conditions.py:16-158; src/fast_fsm/condition_templates.py:118-160] This is required by the repository's verbatim compatibility rule “`*args, **kwargs`.” [VERIFIED: .github/copilot-instructions.md:50-53]

**Async recursion:** The async evaluator must recognize the exact built-in wrapper edges:

- `NegatedCondition._inner` [VERIFIED: src/fast_fsm/conditions.py:121-158]
- `AndCondition.conditions` and `OrCondition.conditions` [VERIFIED: src/fast_fsm/condition_templates.py:118-147]
- `NotCondition.condition` [VERIFIED: src/fast_fsm/condition_templates.py:150-160]

It should await `AsyncCondition` leaves, call synchronous leaves normally, preserve And/Or short-circuit order, invert Not/Negated results, and pass the same prepared args/kwargs object through all levels. [ASSUMED] Detection and evaluation should share one private child-edge classifier so they cannot disagree about supported wrappers. [ASSUMED]

### Pattern 4: Transactional Builder with Freeze Guard

**What:** Put `_ensure_mutable()` at the start of every state/transition mutator, callback registrar, and force-mode method. `build()` should: return the cache when present; preflight async requirements; choose a type; create a local candidate; install all staged state/transition/callback data; assign `_machine = candidate` only after the final successful step. [ASSUMED]

Current mutator and callback methods continue to modify staging after a successful build, while only some force methods check the cache. [VERIFIED: src/fast_fsm/core.py:2278-2686] Existing explicit-sync behavior warns/drops async callbacks; D-11 requires build-time failure instead. [VERIFIED: src/fast_fsm/core.py:2605-2686; .planning/phases/16-canonical-graph-dispatch-invariants/16-CONTEXT.md:33-36]

**Cycle-safe async scan:** Use identity keys (`id(condition)`) in an iterative work list. Mark a node before following children. A detected wrapper cycle should fail closed with `ValueError` during build rather than being classified as synchronous; this exact error choice is a recommendation. [ASSUMED]

**Preflight sources:** staged transition conditions, nested built-in wrappers, declarative handler `is_async`, declarative handler conditions, and queued async callbacks. Explicit async mode bypasses type selection but still validates; explicit sync mode raises before allocating a candidate when any async requirement is present. [VERIFIED: .planning/phases/16-canonical-graph-dispatch-invariants/16-CONTEXT.md:33-36]

### Pattern 5: Declarative Exactly-Once Integration Boundary

**What:** Add one private state-level handler resolver keyed by ordinary dispatch's source state, trigger, and canonical target. Add one invocation seam that normalizes sync/async handler execution. The compatibility `handle_event` helpers delegate to that seam rather than calling method metadata independently. [ASSUMED]

Current declarative metadata contains the verbatim keys `"method"`, `"from"`, `"to"`, `"condition"`, and `"is_async"`; handler helpers directly invoke the stored method. [VERIFIED: src/fast_fsm/core.py:2016-2033,2096-2159,2171-2275] The integration must honor handler from/to matching rather than selecting on trigger alone. [ASSUMED]

**Phase boundary:** Phase 16 tests exactly one successful invocation and sync/async parity. Do not assert whether invocation is pre-commit or post-commit, callback-relative order, handler-exception result shape, cancellation semantics, or history behavior on handler failure; those are explicitly deferred to Phase 17. [VERIFIED: .planning/phases/16-canonical-graph-dispatch-invariants/16-CONTEXT.md:43-45,126-133]

### Pattern 6: Bounded Deque History

**What:** Validate `max_entries > 0` before changing any fields, then assign an empty `deque(maxlen=max_entries)`. Keep `None` as disabled, append records normally, and return `list(self._history)` from `history`. [ASSUMED]

Python documents deque endpoint appends/pops as approximately O(1), list front operations as O(n), and bounded deques as discarding the opposite-end item when full. [CITED: https://docs.python.org/3.10/library/collections.html#collections.deque] This removes the current `del self._history[0]` path. [VERIFIED: src/fast_fsm/core.py:1488-1496]

### Anti-Patterns to Avoid

- **Validate while mutating:** It permits a later bad source to leave earlier transition entries behind. [VERIFIED: src/fast_fsm/core.py:728-751]
- **Canonicalize by name only:** A same-name foreign object must not become an endpoint; compare identity against the registry object. [VERIFIED: .planning/phases/16-canonical-graph-dispatch-invariants/16-CONTEXT.md:21-25]
- **Cache a builder candidate early:** Any later registration/callback error would turn a failed build into a partially cached “successful” repeated build. [VERIFIED: src/fast_fsm/core.py:2605-2686]
- **Detect nested async without recursively evaluating it:** A wrapper will still call an async leaf through a synchronous method. [VERIFIED: src/fast_fsm/conditions.py:121-158; src/fast_fsm/condition_templates.py:118-160]
- **Sanitize independently in every layer:** It risks different contexts and multiple copies. Prepare once and propagate. [VERIFIED: .planning/phases/16-canonical-graph-dispatch-invariants/16-CONTEXT.md:38-41]
- **Deep-copy canonical state/guard objects into snapshots:** It destroys the canonical identity the snapshot must expose. [ASSUMED]
- **Lock declarative lifecycle order in Phase 16 tests:** That would steal Phase 17 decisions. [VERIFIED: .planning/phases/16-canonical-graph-dispatch-invariants/16-CONTEXT.md:43-45,126-133]
- **Add locks for graph/version atomicity:** Concurrency/reentrancy ownership is Phase 18, not Phase 16. [VERIFIED: .planning/phases/16-canonical-graph-dispatch-invariants/16-CONTEXT.md:126-133]
- **Delete native shadows to prove pure mode:** The project requires a non-destructive source-origin preflight and reviewed cleanup only. [VERIFIED: .github/copilot-instructions.md:63-71]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Bounded FIFO | Manual index/ring buffer | `collections.deque(maxlen=...)` | Standard bounded O(1) endpoint behavior is documented. [CITED: https://docs.python.org/3.10/library/collections.html#collections.deque] |
| Graph traversal store | Parallel graph package/model | Existing dict authority plus fresh sorted tuple snapshot | Avoids synchronization drift and new dependency. [ASSUMED] |
| Async wrapper API | New public wrapper protocol | Private exact built-in edge classifier | D-11/D-discretion explicitly limits this to a private protocol. [VERIFIED: .planning/phases/16-canonical-graph-dispatch-invariants/16-CONTEXT.md:33-36,51-55] |
| Transaction rollback | Undo log after partial build | Local candidate, publish cache at end | No shared builder state needs rollback when nothing is published early. [ASSUMED] |
| New serializer | Public versioned graph JSON | Private immutable graph snapshot | Public topology format is FUTR-05 and deferred. [VERIFIED: .planning/phases/16-canonical-graph-dispatch-invariants/16-CONTEXT.md:126-133] |

**Key insight:** The safe unit of change is the prepared operation, not each dictionary assignment or callback registration. [ASSUMED]

## Runtime State Inventory

This is a behavioral refactor rather than a rename or persisted-schema migration, but the five runtime-state categories were audited explicitly because stale compiled artifacts can mask source changes. [VERIFIED: .planning/phases/16-canonical-graph-dispatch-invariants/16-CONTEXT.md:6-14]

| Category | Items Found | Action Required |
|----------|-------------|-----------------|
| Stored data | None — the Phase 16 topology/history objects are in-memory, and no database/datastore dependency or adapter was found in the project/runtime surfaces scanned for this phase. [VERIFIED: local repository scan of `pyproject.toml`, `src/`, `tests/`, `Taskfile.yml`, PROJECT, ROADMAP, and REQUIREMENTS on 2026-08-29] | No data migration. Validate new behavior with fresh machine instances. |
| Live service config | None — no external service owns the state registry, transition graph, builder cache, guard context, declarative metadata, or history buffer. [VERIFIED: local repository scan of the same Phase 16 surfaces on 2026-08-29] | No API/dashboard patch. |
| OS-registered state | None — Phase 16 changes no process/service/task registration name or format. [VERIFIED: .planning/phases/16-canonical-graph-dispatch-invariants/16-CONTEXT.md:6-14,126-133] | No OS re-registration. |
| Secrets/env vars | No Phase 16 secret or environment-variable rename. Existing build selectors are verbatim `FAST_FSM_BUILD_MODE` and `FAST_FSM_PURE_PYTHON`; they remain build/evidence inputs, not graph state. [VERIFIED: setup.py:23-24; tools/build_modes.py:17-29] | No secret migration; preserve selectors for pure/compiled checks. |
| Build artifacts / installed packages | Native extension shadows for CPython 3.10 and 3.12 are present in the source package directory. [VERIFIED: local `rg --files --hidden -g '*.so'` artifact inventory on 2026-08-29] | Do not delete them implicitly. Prove pure mode in a clean archive/worktree, and rebuild compiled artifacts after `core.py` changes so stale machine code cannot mask results. [VERIFIED: .github/copilot-instructions.md:63-71] |

**Canonical answer:** after source edits, only compiled/build artifacts can retain the old implementation; no stored data, service configuration, OS registration, or secret-key migration is part of Phase 16. [VERIFIED: local runtime-state audit on 2026-08-29]

## Mypyc and Compilation Boundary

Only `core.py` is compiled; `conditions.py` and condition templates stay interpreted so users can subclass condition bases. The ADR's verbatim decision is “Compile `src/fast_fsm/core.py` only” and its interpreted modules include “`conditions.py`” and “`condition_templates.py`.” [VERIFIED: .specify/decisions/ADR-003-mypyc-compilation-boundary.md:26-42] `setup.py` passes only `src/fast_fsm/core.py` to `mypycify`. [VERIFIED: setup.py:16-39]

Planning implications:

- Keep orchestration seams and private snapshot types in `core.py`; keep wrapper class changes in their existing interpreted modules. [ASSUMED]
- New hot-path classes must use slots or a tuple-backed representation and must pass the recursive slots-policy audit. [VERIFIED: .github/copilot-instructions.md:40-45]
- Do not use runtime monkey-patching, dynamic attribute creation, or a new abstract inheritance layer across compiled/interpreted boundaries. [ASSUMED]
- Compile-test the exact private record choice early, before other tasks depend on it. Mypyc's documented native classes have restrictions; interpreted subclasses require `@mypyc_attr(native_class=False)`, and dataclass support is partial. [CITED: https://mypyc.readthedocs.io/en/stable/native_classes.html]
- Preserve `State` subclassability decorators and the measured `CompiledFuncCondition` exception exactly as the ADR specifies. The verbatim opt-out is `@mypyc_attr(native_class=False)`. [VERIFIED: .specify/decisions/ADR-003-mypyc-compilation-boundary.md:158-177]

## Performance Measurement Strategy

Phase 15 recorded a pure-source observation of `951787.04` trigger ops/sec over `40000` operations against a compiled floor of `200000`; these are evidence observations, not a new Phase 16 target. [VERIFIED: evidence/release-baseline.json:39-56] It also recorded `879` passed, `0` failed, `0` errors, and `0` skipped in the baseline manifest. [VERIFIED: evidence/release-baseline.json:58-73]

The inherited harness has also been proven in hosted execution: Phase 15's exact-SHA run completed `29/29` jobs, including `15` OS/Python matrix tests and `5` pure-sdist jobs, while the local clean evidence remained source-origin checked. [VERIFIED: .planning/phases/15-release-baseline-evidence-harness/15-VERIFICATION.md:39-49,110-118] Phase 16 should reuse those gates and update observations only through the reviewed evidence workflow, not invent an ad hoc performance proof. [ASSUMED]

Plan two performance checkpoints:

1. **Targeted pure microbenchmark after shared dispatch refactor:** run the existing benchmark from a clean pure-source context and compare to the checked-in observation/environment. Report deltas; do not rewrite evidence during development. [ASSUMED]
2. **Compiled gate after all core changes:** build with the pinned release toolchain, confirm imported source origin, run existing compiled trigger threshold and history-overhead tests, then the release evidence check. [ASSUMED]

Snapshot sorting and recursive builder scans must remain off `trigger()`/`can_trigger()` steady-state paths. Guard sanitation necessarily remains per guard evaluation, but it should create only one new dict per evaluation. History disabled must retain the existing `None` branch and allocate no deque. [ASSUMED]

Use a clean archive/worktree for pure and compiled proof because the current development checkout may contain legitimate native shadows; do not remove them as setup. [VERIFIED: .github/copilot-instructions.md:63-71]

## Common Pitfalls

### Pitfall 1: Partial topology mutation
**What goes wrong:** One source is inserted before a later source/target/guard error. [VERIFIED: src/fast_fsm/core.py:728-751]
**Why it happens:** Validation and assignment are interleaved. [VERIFIED: src/fast_fsm/core.py:728-751]
**How to avoid:** Materialize and validate a complete immutable plan, then commit. [ASSUMED]
**Warning signs:** Graph version changed on rejection; snapshot differs; a source bucket appears after failure. [ASSUMED]

### Pitfall 2: Name equality mistaken for canonical identity
**What goes wrong:** A foreign `State("same-name")` becomes a target/source while the registry points elsewhere. [ASSUMED]
**Why it happens:** Current object sources are reduced to names and object targets bypass registry lookup. [VERIFIED: src/fast_fsm/core.py:649-751]
**How to avoid:** Require `registry[obj.name] is obj`. [ASSUMED]
**Warning signs:** Snapshot endpoint object differs from its state-row object. [ASSUMED]

### Pitfall 3: Builder freezes after failure
**What goes wrong:** A bad staged item leaves `_machine` assigned, so repair and retry cannot work. [VERIFIED: src/fast_fsm/core.py:2605-2686]
**How to avoid:** Cache only at complete success; freeze is represented by successful cache presence. [ASSUMED]
**Warning signs:** Second `build()` returns an incomplete object after first call raised. [ASSUMED]

### Pitfall 4: Cycle protection silently classifies a cycle as sync
**What goes wrong:** Traversal terminates but an invalid cyclic wrapper reaches runtime. [ASSUMED]
**How to avoid:** Separate “visited” from “active/invalid cycle” semantics or reject any repeated active identity deterministically. [ASSUMED]
**Warning signs:** Explicit sync build succeeds for a self-referential wrapper. [ASSUMED]

### Pitfall 5: Async detection/evaluation drift
**What goes wrong:** Builder chooses `AsyncStateMachine`, but outer sync wrapper produces a coroutine truthiness result or calls `asyncio.run` in an event loop. [ASSUMED]
**Why it happens:** Current wrappers own synchronous child calls. [VERIFIED: src/fast_fsm/conditions.py:121-158; src/fast_fsm/condition_templates.py:118-160]
**How to avoid:** Share wrapper-edge recognition between detector and recursive evaluator. [ASSUMED]

### Pitfall 6: Cap before filter
**What goes wrong:** Private/invalid keys occupy the first 50 positions and starve later safe keys. [ASSUMED]
**Why it happens:** Current sanitizer slices before filtering. [VERIFIED: src/fast_fsm/core.py:1136-1181]
**How to avoid:** Filter in insertion order, increment retained count only for accepted keys, stop at 50 retained. [ASSUMED]

### Pitfall 7: Declarative double invocation
**What goes wrong:** Ordinary dispatch invokes a handler, then a compatibility helper invokes it again. [ASSUMED]
**How to avoid:** Both routes call one invocation seam; ordinary integration owns the single call. [ASSUMED]
**Warning signs:** Side-effect counter is 2 after one trigger. [ASSUMED]

### Pitfall 8: Phase 17 semantics leak into Phase 16
**What goes wrong:** Tests codify handler/callback ordering or failure results prematurely. [VERIFIED: .planning/phases/16-canonical-graph-dispatch-invariants/16-CONTEXT.md:43-45]
**How to avoid:** Assert invocation count, matched identity, and parity only on successful transitions. [ASSUMED]

### Pitfall 9: New record shape passes Python but fails compiled build
**What goes wrong:** Pure tests pass while pinned mypyc rejects or changes the native layout. [ASSUMED]
**How to avoid:** Add compile/slots proof immediately after the snapshot seam, not only at phase end. [ASSUMED]

## Code Examples

These are implementation sketches, not existing API. Exact private names/types are discretionary and therefore tagged `[ASSUMED]`.

### Tuple-Shaped Graph Records

```python
from typing import NamedTuple

class _GraphTransition(NamedTuple):  # [ASSUMED]
    source_name: str
    source: State
    trigger: str
    target_name: str
    target: State
    guard: Condition | None

class _GraphSnapshot(NamedTuple):  # [ASSUMED]
    version: int
    machine_name: str
    initial_name: str
    initial_state: State
    states: tuple[tuple[str, State], ...]
    transitions: tuple[_GraphTransition, ...]
```

On Python 3.10, use `Optional[Condition]` rather than the `|` syntax only if the module's annotation/runtime conventions require it; the project already targets Python `>=3.10`. [VERIFIED: pyproject.toml:1-9] The exact type must be validated under pinned mypyc. [ASSUMED]

### Cycle-Safe Built-In Condition Traversal

```python
def _contains_async_condition(root: Condition) -> bool:  # [ASSUMED]
    pending = [root]
    seen: set[int] = set()
    while pending:
        node = pending.pop()
        identity = id(node)
        if identity in seen:
            continue
        seen.add(identity)
        if isinstance(node, AsyncCondition):
            return True
        pending.extend(_builtin_condition_children(node))
    return False
```

The production design should distinguish a harmless DAG revisit from an active cycle if cycles are to be rejected, rather than using this minimal reachability sketch alone. [ASSUMED]

### Filter-Then-Cap Context

```python
def _sanitize_guard_kwargs(kwargs: Mapping[str, object]) -> dict[str, object]:  # [ASSUMED]
    safe: dict[str, object] = {}
    for key, value in kwargs.items():
        if not isinstance(key, str) or key.startswith("_") or len(key) > 100:
            continue
        safe[key] = value
        if len(safe) == 50:
            break
    return safe
```

The quoted limits `100` and `50` come from the current policy. [VERIFIED: src/fast_fsm/core.py:1136-1181]

## Concrete Failure-Mode Test Matrix

| Scenario | Expected invariant |
|----------|--------------------|
| Unknown string source/target | `ValueError`; registry, transitions, version, current state byte-for-byte/identity unchanged. [VERIFIED: .planning/phases/16-canonical-graph-dispatch-invariants/16-CONTEXT.md:21-25] |
| Same-name foreign `State` source/target | `ValueError`; no implicit registration or partial bucket. [VERIFIED: .planning/phases/16-canonical-graph-dispatch-invariants/16-CONTEXT.md:21-25] |
| Multi-source with valid first and invalid later source | Entire call rejected; neither source receives an entry. [VERIFIED: .planning/phases/16-canonical-graph-dispatch-invariants/16-CONTEXT.md:21-25] |
| Duplicate sources in one request | Rejected before commit. [VERIFIED: .planning/phases/16-canonical-graph-dispatch-invariants/16-CONTEXT.md:21-25] |
| Same object re-registration | No-op; same registry identity and version. [VERIFIED: .planning/phases/16-canonical-graph-dispatch-invariants/16-CONTEXT.md:21-29] |
| Conflicting object re-registration | `ValueError`; transitions/version/current unchanged. [VERIFIED: .planning/phases/16-canonical-graph-dispatch-invariants/16-CONTEXT.md:21-29] |
| Current-state transition/reset | Graph version unchanged; snapshot initial stays declared initial. [VERIFIED: .planning/phases/16-canonical-graph-dispatch-invariants/16-CONTEXT.md:27-31] |
| Snapshot mutation attempt | Tuple/field mutation fails and later snapshot/machine graph remains unchanged. [ASSUMED] |
| Failed builder wiring | `build()` raises; staged builder remains mutable/repairable; no cache. [VERIFIED: .planning/phases/16-canonical-graph-dispatch-invariants/16-CONTEXT.md:33-36] |
| Any mutator after successful build | Immediate `RuntimeError`; repeated build returns identical machine object. [VERIFIED: .planning/phases/16-canonical-graph-dispatch-invariants/16-CONTEXT.md:33-36] |
| Nested async under each built-in wrapper | Auto builds async; explicit sync build raises before materialization. [VERIFIED: .planning/phases/16-canonical-graph-dispatch-invariants/16-CONTEXT.md:33-36] |
| Self/cyclic wrapper | Traversal terminates deterministically; recommended result is `ValueError`. [ASSUMED] |
| Unsafe kwargs precede safe kwargs | Private/overlong keys removed before the 50-retained cap; later safe keys survive. [VERIFIED: .planning/phases/16-canonical-graph-dispatch-invariants/16-CONTEXT.md:38-41] |
| Positional guard payload | Same object identities/order on sync/async can/do paths; caller kwargs unchanged. [VERIFIED: .planning/phases/16-canonical-graph-dispatch-invariants/16-CONTEXT.md:38-41] |
| Ordinary declarative dispatch | Successful matched handler counter increments exactly once for sync and async. [VERIFIED: .planning/phases/16-canonical-graph-dispatch-invariants/16-CONTEXT.md:43-45] |
| History capacity `0` or negative | Immediate `ValueError`; existing history configuration remains unchanged. [VERIFIED: .planning/phases/16-canonical-graph-dispatch-invariants/16-CONTEXT.md:47-49] |
| History overflow | Oldest evicted, chronological defensive list returned, internal buffer unaffected by caller list mutation. [VERIFIED: .planning/phases/16-canonical-graph-dispatch-invariants/16-CONTEXT.md:47-49] |

## Recommended Plan Decomposition

| Order | Deliverable | Depends on | Exit proof |
|------:|-------------|------------|------------|
| 0 | Contract tests for canonical identity, version, snapshot shape, and atomic rejection | — | New tests fail for reproduced current behavior. [ASSUMED] |
| 1 | Canonical registry resolver, validate/commit transition plan, version, declared-initial snapshot | 0 | Graph tests pass in pure mode; compile/slots smoke passes. [ASSUMED] |
| 2 | `*args` condition propagation, filter-then-cap context, shared lookup/preparation, paired sync/recursive-async evaluators | 1 | Four-path context matrix and wrapper tests pass. [ASSUMED] |
| 3 | Builder freeze guard, recursive preflight, explicit-mode semantics, local-candidate transaction | 1, 2 | Freeze/repair/repeat/nested-async tests pass. [ASSUMED] |
| 4 | Declarative resolver/invocation seam and ordinary sync/async integration | 2, 3 | Exactly-once successful invocation parity passes without lifecycle-order assertions. [ASSUMED] |
| 5 | `deque` history validation/storage | 1 | Capacity/copy/order/overflow tests and history overhead check pass. [ASSUMED] |
| 6 | Public regression, docs/examples if behavior is user-visible, pure/compiled/slots/performance gates | 1-5 | Targeted suite, blocking mypy, full suite once, clean pure and compiled evidence checks. [ASSUMED] |

Although history is conceptually independent, most deliverables touch `core.py`; execute in this order rather than parallel edits to reduce merge conflict and compiled-boundary integration risk. [ASSUMED]

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| `uv` | All Python/test/build commands | ✓ | `0.12.6` [VERIFIED: local `uv --version` probe on 2026-08-29] | None; required by project rules. |
| Python via locked uv environment | Pure tests and tooling | ✓ | `3.12.10` [VERIFIED: local `uv run python --version` probe on 2026-08-29] | Project supports `>=3.10`. [VERIFIED: pyproject.toml:1-9] |
| mypy/mypyc | Compile compatibility | ✓ | `1.17.1` [VERIFIED: local environment probe and pyproject.toml:21-25,42-44] | None for release proof. |
| Task | Quality/release orchestration | ✓ | `3.53.1` [VERIFIED: local `task --version` probe on 2026-08-29] | Invoke underlying `uv` commands only if task wrapper is unavailable. [ASSUMED] |
| C compiler | Compiled artifact build | ✓ | Apple clang `21` [VERIFIED: local compiler probe on 2026-08-29] | Pure-mode test only is insufficient for phase completion. [ASSUMED] |

**Missing dependencies with no fallback:** None found. [VERIFIED: local environment probes on 2026-08-29]

**Missing dependencies with fallback:** None found. [VERIFIED: local environment probes on 2026-08-29]

## Validation Architecture

Validation is enabled: the verbatim setting is `"nyquist_validation": true`. [VERIFIED: .planning/config.json:15-23]

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest `>=8.4.1`, pytest-asyncio `>=1.3.0`, Hypothesis `>=6.136.6` [VERIFIED: pyproject.toml:11-20] |
| Config file | `pyproject.toml`; test path `"tests"`, files `"test_*.py"`, asyncio mode `"auto"`. [VERIFIED: pyproject.toml:55-73] |
| Quick run command | `uv run pytest tests/test_graph_invariants.py -x -q` [ASSUMED] |
| Full suite command | `uv run pytest tests/ -x -q` [VERIFIED: .github/copilot-instructions.md:55-61] |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| GRAF-01 | Unknown/foreign endpoints and atomic multi-source rejection | unit + property sequence | `uv run pytest tests/test_graph_invariants.py -x -q -k endpoint` [ASSUMED] | ❌ Wave 0 |
| GRAF-02 | Identity-canonical registration and stable rejection | unit + property sequence | `uv run pytest tests/test_graph_invariants.py -x -q -k registry` [ASSUMED] | ❌ Wave 0 |
| GRAF-03 | Snapshot contents/order/immutability/version/initial | unit | `uv run pytest tests/test_graph_invariants.py -x -q -k snapshot` [ASSUMED] | ❌ Wave 0 |
| GRAF-04 | Full builder freeze, failed-build repair, repeated identity | unit | `uv run pytest tests/test_builder.py -x -q -k 'freeze or repair or idempotent'` [ASSUMED] | ✅ extend existing [VERIFIED: tests/test_builder.py:1-977] |
| GRAF-05 | Nested async detection/evaluation and cycle safety | sync/async unit | `uv run pytest tests/test_builder.py tests/test_async.py -x -q -k 'nested or wrapper or cycle'` [ASSUMED] | ✅ extend existing [VERIFIED: tests/test_builder.py:1-977; tests/test_async.py:1-594] |
| GRAF-06 | Args and sanitized kwargs parity across four paths | paired sync/async unit | `uv run pytest tests/test_safety_kwargs.py tests/test_async.py -x -q -k 'guard or sanit'` [ASSUMED] | ✅ extend existing [VERIFIED: tests/test_safety_kwargs.py:1-245; tests/test_async.py:1-520] |
| GRAF-07 | Declarative successful handler exactly once | paired sync/async integration | `uv run pytest tests/test_builder.py tests/test_async.py -x -q -k declarative` [ASSUMED] | ✅ extend existing [VERIFIED: tests/test_builder.py:1-977; tests/test_async.py:1-594] |
| GRAF-08 | Shared seam regression and compiled-core boundary | structural + integration | `uv run pytest tests/test_mypyc_guard.py tests/test_graph_invariants.py -x -q` [ASSUMED] | partial; graph file Wave 0 [VERIFIED: tests/test_mypyc_guard.py:1-168] |
| LIFE-07 | Invalid capacity, bounded order, copy-on-read, overhead | unit + slow performance | `uv run pytest tests/test_advanced_functionality.py tests/test_performance_benchmarks.py -x -q -k history` [ASSUMED] | ✅ extend existing [VERIFIED: tests/test_advanced_functionality.py:1532-1625; tests/test_performance_benchmarks.py:379-492] |

### Sampling Rate

- **Per task commit:** Run only the directly affected command from the table plus `task typecheck-mypy` for compiled-core/type changes. [VERIFIED: .github/copilot-instructions.md:95-109]
- **Per wave merge:** Run all Phase 16 targeted files sequentially. [ASSUMED]
- **Phase gate:** Run `task typecheck-mypy`, advisory `task typecheck-ty`, the full suite once, then clean pure and compiled evidence/performance gates. [VERIFIED: .github/copilot-instructions.md:95-109,206-221]

### Wave 0 Gaps

- Create `tests/test_graph_invariants.py` for GRAF-01/02/03 and graph portions of GRAF-08. [ASSUMED]
- Add a reusable graph fingerprint helper that captures registry object identities, transition endpoint/guard identities, version, current state, and snapshot so rejection tests prove no mutation. Keep it in test code, not a public runtime API. [ASSUMED]
- Add a recording sync/async condition fixture accepting `*args, **kwargs` to assert object identity, ordering, sanitization, and no caller mutation. [ASSUMED]
- Add wrapper-cycle fixtures constructed without creating a new public wrapper protocol. [ASSUMED]
- Extend compiled structural guards to cover any new hot-path record/class slots and preserve the single `core.py` mypyc input. [ASSUMED]

## Formal Threat Considerations

| Threat | STRIDE | Abuse/failure path | Required mitigation / plan proof |
|--------|--------|--------------------|----------------------------------|
| Same-name foreign state spoofing | Spoofing / Tampering | Caller supplies a distinct object whose name matches a canonical state. [VERIFIED: src/fast_fsm/core.py:649-751] | Identity-canonical resolver; negative source and target tests; no mutation/version change. [ASSUMED] |
| Partial multi-source commit | Tampering | Later invalid endpoint leaves earlier writes. [VERIFIED: src/fast_fsm/core.py:728-751] | Complete preflight then short commit; graph fingerprint before/after failure. [ASSUMED] |
| Wrapper cycle or adversarial depth | Denial of Service | Recursive detection loops or overflows. [ASSUMED] | Iterative identity-tracked traversal; deterministic cycle rejection; no public recursive protocol. [ASSUMED] |
| Oversized/private keyword flood | Denial of Service / Information Disclosure | Invalid keys consume cap or sensitive/private values reach new logs. [VERIFIED: src/fast_fsm/core.py:1136-1181] | Filter before retained cap; fresh bounded mapping; add no raw-value logging; parity tests. [ASSUMED] |
| Version lies about rejected mutation | Repudiation / Tampering | Tool observes a version advance without topology change or misses a successful change. [ASSUMED] | Advance in commit only; snapshot/version matrix over success, no-op, rejection, and current-state changes. [ASSUMED] |
| Double declarative side effect | Tampering | Helper and ordinary dispatch both invoke a handler. [ASSUMED] | One invocation seam and counter-based exactly-once tests. [ASSUMED] |
| Partial builder publication | Tampering | Failed build is cached and later returned. [VERIFIED: src/fast_fsm/core.py:2605-2686] | Local candidate, publish cache last, repair/retry identity tests. [ASSUMED] |
| Concurrency race | Tampering | Two owners mutate graph/version concurrently. [ASSUMED] | Explicitly defer locks/ownership to Phase 18; Phase 16 must not claim thread safety or add an incompatible lock seam. [VERIFIED: .planning/phases/16-canonical-graph-dispatch-invariants/16-CONTEXT.md:126-133] |

Threat-model boundary: untrusted state names, triggers, condition wrappers, args, and kwargs are in scope as in-process inputs. Authentication, network sessions, authorization, storage, and cryptographic boundaries are absent from this phase's in-process library path. [ASSUMED]

## Security Domain

OWASP identifies ASVS `5.0.0` as the latest stable release, and recommends version-qualified requirement identifiers. [CITED: https://owasp.org/www-project-application-security-verification-standard/]

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No [ASSUMED] | No authentication boundary in this in-process phase. |
| V3 Session Management | No [ASSUMED] | No session/token lifecycle in scope. |
| V4 Access Control | No [ASSUMED] | No principal/permission model in scope. |
| V5 Input Validation | Yes [ASSUMED] | Canonical endpoint validation, guard normalization, bounded sanitized kwargs, fail-before-mutation. |
| V6 Cryptography | No [ASSUMED] | No secrets or cryptographic operation introduced. |

For ASVS 5 taxonomy, the materially relevant themes are validation/business logic, secure coding/architecture, and security logging/error handling; broader web controls are not directly exercised. [CITED: https://cornucopia.owasp.org/taxonomy/asvs-5.0]

### Known Threat Patterns for the Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Object-identity confusion | Spoofing/Tampering | Resolve to registry and compare object identity before commit. [ASSUMED] |
| Inconsistent validation across sync/async APIs | Tampering | Shared preparation seam and paired conformance tests. [ASSUMED] |
| Algorithmic complexity from cycles/front deletion | Denial of Service | Identity-cycle guard and bounded deque. [ASSUMED] [CITED: https://docs.python.org/3.10/library/collections.html#collections.deque] |
| Sensitive payload logging during refactor | Information Disclosure | Introduce no new raw payload logs; broader redaction remains Phase 19. [VERIFIED: .planning/phases/16-canonical-graph-dispatch-invariants/16-CONTEXT.md:38-41,126-133] |

## State of the Art

| Old Approach | Current Recommendation | Impact |
|--------------|------------------------|--------|
| Interleaved endpoint validation/insertion [VERIFIED: src/fast_fsm/core.py:649-751] | Complete normalize/validate plan, then commit [ASSUMED] | Atomic rejection and coherent version. |
| Separate sync/async context preparation [VERIFIED: src/fast_fsm/core.py:1110-1181,1792-1954] | Shared preparation plus strategy-specific evaluator [ASSUMED] | Four-path parity without forcing sync code to await. |
| Direct-only async classification [VERIFIED: src/fast_fsm/core.py:2362-2390] | Cycle-safe built-in wrapper graph traversal [ASSUMED] | Correct auto/explicit machine selection. |
| Early builder cache assignment [VERIFIED: src/fast_fsm/core.py:2605-2686] | Publish-on-success transaction [ASSUMED] | Repairable failures and trustworthy repeated build. |
| List front deletion [VERIFIED: src/fast_fsm/core.py:1488-1496] | Bounded deque [CITED: https://docs.python.org/3.10/library/collections.html#collections.deque] | O(1) eviction. |

**Deprecated/outdated:** No public symbol should be deprecated or removed in Phase 16. [VERIFIED: .github/copilot-instructions.md:50-53]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | “Immutable snapshot” means structurally immutable containers; canonical `State` and guard references are not deep-frozen. | Summary / Snapshot | If the user intended deep immutability, D-06 conflicts with exposing identity-bearing mutable objects and needs clarification before planning. |
| A2 | Re-adding an identical transition entry is a topology no-op and does not advance the version. | Normalize/Commit | Different version semantics would change tests but not data shape. |
| A3 | Graph version starts at `0`, constructor initial registration is baseline, and clone copies the version. | Snapshot | Starting/compound semantics are discretionary, but planners should lock one. |
| A4 | Built-in wrapper cycles fail closed with `ValueError` rather than merely terminating detection. | Builder / Threats | Error type/acceptance behavior is not locked. |
| A5 | Tuple-backed private records are the lowest-risk mypyc-compatible snapshot representation. | Standard Stack | Exact pinned mypyc behavior must be proven early. |
| A6 | Declarative from/to metadata participates in ordinary handler matching. | Declarative | Trigger-only matching could invoke a wrong handler if metadata and machine transition diverge. |
| A7 | No new external package is required. | Standard Stack | A newly introduced dependency would require legitimacy audit and violate the current recommendation. |

## Open Questions

1. **How deep is snapshot immutability?**
   - What we know: D-06 requires canonical state objects and guards and says returned snapshot contents cannot be mutated through returned references. [VERIFIED: .planning/phases/16-canonical-graph-dispatch-invariants/16-CONTEXT.md:27-31,51-55]
   - What's unclear: User-extensible `State`/`Condition` objects are themselves mutable, so literal deep immutability is incompatible with returning canonical references. [ASSUMED]
   - Recommendation: Lock structural immutability of snapshot records/collections and explicitly exclude mutation of the referenced runtime objects from the snapshot contract. [ASSUMED]

2. **What is the exact cycle failure contract?**
   - What we know: traversal must have identity-based cycle protection. [VERIFIED: .planning/phases/16-canonical-graph-dispatch-invariants/16-CONTEXT.md:33-36]
   - What's unclear: Context does not prescribe accept/ignore/reject behavior for an actual cyclic built-in wrapper graph. [ASSUMED]
   - Recommendation: Reject at registration/build with `ValueError`; never silently classify it as synchronous. [ASSUMED]

3. **Does clone preserve graph version or begin a new version lineage?**
   - What we know: Version is per-machine and clone currently reproduces topology but disables history. [VERIFIED: .planning/phases/16-canonical-graph-dispatch-invariants/16-CONTEXT.md:27-31; src/fast_fsm/core.py:1264-1315]
   - What's unclear: Context gives discretion over starting value but does not mention clone lineage. [ASSUMED]
   - Recommendation: Copy the source version because the clone's initial snapshot describes the same topology; later versions diverge independently. [ASSUMED]

These are narrow planner decisions, not blockers; the recommendations are consistent with the locked outcomes. [ASSUMED]

## Sources

### Primary (HIGH confidence)

- `.planning/phases/16-canonical-graph-dispatch-invariants/16-CONTEXT.md` — locked Phase 16 decisions and deferrals. [VERIFIED: .planning/phases/16-canonical-graph-dispatch-invariants/16-CONTEXT.md:1-140]
- `.planning/REQUIREMENTS.md` and `.planning/ROADMAP.md` — requirement text and observable phase goal. [VERIFIED: .planning/REQUIREMENTS.md:20-39; .planning/ROADMAP.md:108-121]
- `src/fast_fsm/core.py`, `conditions.py`, and `condition_templates.py` — present registry, transition, dispatch, builder, wrapper, declarative, and history behavior. [VERIFIED: src/fast_fsm/core.py:273-2686; src/fast_fsm/conditions.py:1-158; src/fast_fsm/condition_templates.py:118-160]
- `.specify/decisions/ADR-003-mypyc-compilation-boundary.md` and `setup.py` — compilation boundary and exceptions. [VERIFIED: .specify/decisions/ADR-003-mypyc-compilation-boundary.md:26-42,158-177; setup.py:16-39]
- `.github/copilot-instructions.md`, `pyproject.toml`, `.planning/config.json` — workflow, performance, signature, version, and validation constraints. [VERIFIED: .github/copilot-instructions.md:32-71,95-109,206-221; pyproject.toml:1-73; .planning/config.json:15-23]
- `evidence/release-baseline.json` — Phase 15 correctness/performance reference. [VERIFIED: evidence/release-baseline.json:39-73]

### Secondary (MEDIUM confidence)

- Python 3.10 `collections` documentation — deque complexity and bounded behavior. [CITED: https://docs.python.org/3.10/library/collections.html#collections.deque]
- Python 3.10 `dataclasses` documentation — frozen and slots semantics. [CITED: https://docs.python.org/3.10/library/dataclasses.html]
- mypyc native class documentation — interpreted subclass and dataclass constraints. [CITED: https://mypyc.readthedocs.io/en/stable/native_classes.html]
- OWASP ASVS project and 5.0 taxonomy — current standard/versioning and category framing. [CITED: https://owasp.org/www-project-application-security-verification-standard/] [CITED: https://cornucopia.owasp.org/taxonomy/asvs-5.0]

### Tertiary (LOW confidence)

- None. Planner recommendations not directly established by source are individually tagged `[ASSUMED]` and listed above.

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — no new dependency; versions and boundaries come from project source and official standard-library docs.
- Architecture: HIGH — grounded in locked decisions and line-level inspection of every affected runtime path; exact private record/seam names remain discretionary.
- Pitfalls: HIGH — most failure modes are directly reproduced by current control flow; cycle error and deep-immutability interpretation are explicitly assumed.
- Validation: HIGH — existing framework/config/files and Phase 15 gates were inspected; new test names/filters are recommendations.

**Research date:** 2026-08-29
**Valid until:** 2026-09-28 for the stable in-repo design; re-check mypyc/ASVS documentation only if toolchain or policy changes.
