# Phase 23: Construction, Declarative & Serialization Parity - Research

**Researched:** 2026-09-07  
**Domain:** Python/mypyc construction adapters, declarative candidate identity, and callable-safe topology serialization  
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

### One topology across construction paths
- **D-01:** Existing construction APIs remain the public surface. Builders,
  `quick_build`, factory helpers, batch/bidirectional/emergency helpers, and
  declarative setup must replay priority-bearing candidate declarations through
  the same atomic registrar rather than maintain an adapter-specific transition
  model. Their row/declaration forms may gain an optional priority value without
  changing the ordinary default (`0`). — **Reversibility:** costly — divergent
  adapter topology would give callers different winner semantics for the same
  declared machine.
- **D-02:** A failed builder or factory construction remains unpublished and
  retryable: priority conflicts, malformed candidate data, and async preflight
  failures cannot overwrite staged handlers, freeze the builder, or expose a
  partial candidate group.

### Declarative candidate identity
- **D-03:** Declarative metadata must retain more than one handler declaration
  for a trigger. Handler resolution is candidate-specific: after Phase 22 has
  identified an entry, resolve only the matching target/priority declaration;
  never use a trigger-wide handler or guard that could be attached to a lower
  or different candidate. — **Reversibility:** costly — handler identity is an
  observable safety contract for priority groups.
- **D-04:** Sync and async declarative paths follow the same candidate identity
  rule and preserve their existing one-handler lifecycle behavior. Decorator
  and registration order must not decide precedence; stored numeric priority
  does.

### Callable-safe serialized identity
- **D-05:** `to_dict()` emits one explicit transition record per candidate in
  deterministic source/trigger/priority order. Each record preserves source,
  trigger, target, numeric priority, and an optional opaque condition reference;
  it never serializes a callable or condition implementation.
- **D-06:** `from_dict()` attaches supplied guards by the record's explicit
  opaque condition reference. Legacy bare-trigger condition mappings remain
  usable only when exactly one candidate matches; any ambiguous mapping raises
  clearly rather than reusing a guard across candidates. The condition-reference
  spelling and validation details may follow existing configuration conventions.
  — **Reversibility:** one-way — a wrong attachment can silently change a
  fail-safe winner, while explicit references make JSON/YAML topology portable
  and auditable.

### Coherent read and clone seams
- **D-07:** Clones preserve immutable candidate entries/groups and their
  priority/guard identities while retaining independent table ownership. Query
  helpers keep their documented high-level semantics (for example, trigger
  availability remains deduplicated), but target checks, topology snapshots,
  and serialization must inspect all candidates rather than require a singleton
  or silently collapse a group.
- **D-08:** Keep callback signatures and caller payloads unchanged. Priority
  remains candidate-derived metadata in results, history, and tracing; public
  construction/parity work must not smuggle it through callback kwargs.

### the agent's Discretion
- Choose private projection/helper names, exact typed row aliases, and focused
  test-file placement consistent with `core.py`'s mypyc and slots constraints.
- Preserve legacy serialized shapes whenever they are unambiguous; use explicit
  errors instead of heuristic attachment when a legacy shape is ambiguous.

### Deferred Ideas (OUT OF SCOPE)

None — candidate-aware validation/rendering belongs to Phase 24, and the
drone example, documentation, benchmarks, and installed-artifact proof belong
to Phase 25. Dynamic priorities, equal-priority policies, runtime candidate
mutation, and callable serialization remain future scope.
</user_constraints>

The constraints above are copied verbatim from the phase context. [VERIFIED: .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:21-76,157-163]

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PAR-01 | “Declarative handlers, factories, quick builders, and deserialization preserve candidate identity and priority without singular trigger-key overwrites.” | Replace scalar declarative handler storage with a candidate-qualified immutable collection; make quick/factory rows replay one registrar batch. [VERIFIED: .planning/REQUIREMENTS.md:46-48; src/fast_fsm/core.py:963-1078,4361-4419,4610-4654] |
| PAR-02 | “`can_trigger*()`, `TransitionResult`, transition history, tracing, cloning, topology snapshots, and query helpers expose coherent priority-aware behavior without changing callback signatures.” | Preserve the verified Phase 22 selector/result path; flatten local slots for topology/target queries while keeping trigger lists deduplicated and clone tables independent. [VERIFIED: .planning/REQUIREMENTS.md:50-52; .planning/phases/22-ordered-runtime-selection-lifecycle-integration/22-VERIFICATION.md:23-34; src/fast_fsm/core.py:2022-2117,2858-2920] |
| PAR-03 | “`to_dict()`/`from_dict()` round-trip candidate topology and candidate-specific guard attachment without serializing callables.” | Carry a scalar optional condition reference on candidate/projection records, validate the whole input, resolve explicit references before publication, and reject ambiguous legacy trigger mappings. [VERIFIED: .planning/REQUIREMENTS.md:54-55; .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:47-59] |
</phase_requirements>

## Summary

Phase 23 should not redesign priority selection. Phase 22 already proves that sync and async queries select from a direct singleton or an ascending frozen group before one lifecycle, and that selected priority reaches result/history/trace metadata. [VERIFIED: .planning/phases/22-ordered-runtime-selection-lifecycle-integration/22-VERIFICATION.md:23-34] The remaining defects are adapter and projection defects: `quick_build()` destructures only three-field rows and registers them one at a time; declarative `_handlers` stores one dictionary per trigger and overwrites earlier discoveries; `to_dict()`, `_graph_snapshot()`, `get_reachable_states()`, and target-specific `transition_exists()` call `_require_singleton_entry()`; and `from_dict()` attaches a guard by bare trigger to every matching record. [VERIFIED: src/fast_fsm/core.py:963-1078,1080-1227,1324-1373,2047-2095,4398-4419,4610-4654]

The safe implementation is one candidate-complete projection seam plus two adapters. First, extend the identity-bearing entry/prepared/snapshot records with an optional scalar condition reference and add one private slot-flattening helper used outside dispatch. Second, make serialization validate and resolve all records before one atomic publication. Third, make declarative metadata immutable and plural per trigger, and resolve exactly one handler by canonical source, trigger, target, and priority after the runtime selector chooses an entry. [VERIFIED: .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:35-76,120-140]

The highest-risk compatibility edge is direct `DeclarativeState.handle_event*()`: it has no target or priority parameter, so it cannot truthfully choose among several same-trigger declarations. Preserve its current behavior when exactly one declaration matches; when several match, return one explicit failed `TransitionResult` and invoke none. This retains every existing unambiguous use while ensuring attribute discovery order never becomes a hidden priority policy. This is the recommended resolution of the research flag, derived from the locked candidate-specific and order-independent rules. [VERIFIED: .planning/research/SUMMARY.md:357-365; .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:35-45]

**Primary recommendation:** plan three ordered units: (1) candidate-complete entry/snapshot/query projection and callable-safe round-trip schema, (2) candidate-qualified sync/async declarative storage/resolution and builder preflight, and (3) quick/factory parity plus pure/native, slots, atomicity, and compatibility proof. [VERIFIED: .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:120-142]

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|--------------|----------------|-----------|
| Candidate identity and condition-reference storage | Library core model | mypyc compilation boundary | The candidate record already owns target, guard, and priority; a separate metadata table would create a second identity source that clone and serialization could drift from. [VERIFIED: src/fast_fsm/core.py:611-638,692-714] |
| Quick/factory/builder construction | Library construction adapters | Core registrar | Adapters collect declarations, but `_commit_transition_plan()` remains the sole topology publication seam. [VERIFIED: src/fast_fsm/core.py:1481-1504,5213-5311] |
| Declarative handler selection | Declarative state metadata | Sync/async runtime selector | Metadata owns declarations; the selector supplies the already-selected canonical target and priority. [VERIFIED: src/fast_fsm/core.py:2181-2277,4055-4141,4361-4419] |
| Topology serialization | Library projection layer | Core snapshot | `to_dict()` emits scalar records; `from_dict()` reconstructs live guard identity from an external registry without encoding callables. [VERIFIED: src/fast_fsm/core.py:1080-1227; .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:47-59] |
| Candidate-aware validation/rendering | Phase 24, not Phase 23 | Snapshot consumer | Phase 23 supplies the complete snapshot; Phase 24 owns diagnostic meanings and public output. [VERIFIED: .planning/ROADMAP.md:103-116; .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:138-142,157-163] |
| Installed artifact/performance guidance and drone example | Phase 25, not Phase 23 | Release evidence/docs | This phase runs an early native regression check but does not publish artifact or benchmark claims. [VERIFIED: .planning/ROADMAP.md:118-132; .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:157-163] |

## Project Constraints (from AGENTS.md)

- Use `bd` for project issue tracking, JSON output for programmatic operations, and `discovered-from` links; do not create a second markdown or external task tracker. [VERIFIED: AGENTS.md:9-78]
- Use `uv` for Python, testing, and tool execution; run targeted tests during implementation, sequentially, and the full suite once before push. [VERIFIED: .github/copilot-instructions.md:34-38,65-70,228-246]
- Hot-path production classes must use `__slots__`; the exact registered exceptions are “CompiledFuncCondition, TransitionError, and DiagnosticBudgetExceeded”. Run the recursive slots-policy audit after changing core records. [VERIFIED: .github/copilot-instructions.md:40-50]
- Keep callback and condition `*args, **kwargs` channels unchanged; public symbol removal requires deprecation, and public API changes require documentation/SPR updates in the same change. [VERIFIED: .github/copilot-instructions.md:54-58,255-314]
- Keep `core.py` as the sole mypyc compilation unit and add no runtime dependency. [VERIFIED: .planning/PROJECT.md:96-122; setup.py:16-39]
- Ruff uses fix-then-validate; mypy is blocking and ty remains independently visible advisory feedback. [VERIFIED: .github/copilot-instructions.md:184-202]
- Preserve user work in a dirty tree and stage only explicit task paths. Project session completion normally includes a successful push, but this delegated research task is explicitly local-only and must not run remote operations. [VERIFIED: .github/copilot-instructions.md:102-105; delegated task scope]

## Standard Stack

### Core

| Library/tool | Version | Purpose | Why standard here |
|--------------|---------|---------|-------------------|
| Python | `>=3.10` | Public schema parsing and typed runtime | Existing supported runtime; no new parser or serializer dependency is needed. [VERIFIED: pyproject.toml:1-9] |
| mypyc | `1.17.1` build pin | Compile `src/fast_fsm/core.py` | The phase changes native records and declarative helpers inside the sole compiled module. [VERIFIED: pyproject.toml:22-26,43-45; setup.py:16-39] |
| pytest | `8.4.1` detected | Behavioral, compatibility, and atomicity tests | Existing configured sequential test framework. [VERIFIED: pyproject.toml:12-20,56-74; local `uv run pytest --version`] |
| mypy | `1.17.1` detected | Blocking compiled-core type compatibility | Existing project authority for mypyc-compatible typing. [VERIFIED: pyproject.toml:12-20; local `uv run mypy --version`] |

### Supporting

| Tool | Version | Purpose | When to use |
|------|---------|---------|-------------|
| Ruff | `0.12.11` detected | Format/lint changed Python | Every implementation task that changes source/tests. [VERIFIED: local `uv run ruff --version`; .github/copilot-instructions.md:184-202] |
| ty | `0.0.1-alpha.19` detected | Independent advisory type feedback | After mypy passes, without replacing it as the blocking authority. [VERIFIED: local `uv run ty --version`; .github/copilot-instructions.md:184-202] |
| stdlib `json` | Python 3.10 contract | Verify the emitted dictionary contains only JSON-native values | Default encoding supports mappings, sequences, strings, numbers, booleans, and null; arbitrary condition/callable objects need custom conversion or raise. [CITED: https://docs.python.org/3.10/library/json.html#json.JSONEncoder] |

### Alternatives Considered

| Instead of | Could use | Tradeoff |
|------------|-----------|----------|
| Optional reference stored with the candidate | Separate machine-level reference map | A second table complicates atomic registration, clone isolation, snapshot capture, and duplicate identity; keep identity co-located. [VERIFIED: .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:47-67] |
| One private slot-flattening helper | Teach each consumer about `_TransitionGroup` | Repeated branching invites future collapse and couples Phase 24 consumers to private storage. [VERIFIED: .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:61-67,138-140] |
| Scalar condition reference plus external registry | Callable serialization/custom JSON encoder | Callable persistence is explicitly out of scope and unsafe for portable topology data. [VERIFIED: .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:47-59,157-163; CITED: https://docs.python.org/3.10/library/json.html#json.JSONEncoder] |
| Exact candidate-qualified declarative match | Lowest-discovered or last-discovered handler | Attribute/decorator order would become an undeclared precedence rule and could attach a lower candidate's guard or callback. [VERIFIED: src/fast_fsm/core.py:4637-4654; .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:35-45] |

**Installation:** none. Phase 23 uses only the existing runtime/development stack. [VERIFIED: pyproject.toml:1-45; .planning/REQUIREMENTS.md:78-80]

## Package Legitimacy Audit

Not applicable: no package is added or installed by this phase. [VERIFIED: .planning/REQUIREMENTS.md:78-80]

## Architecture Patterns

### System Architecture Diagram

```text
declaration input
  |-- direct/builder/quick/factory rows
  |-- declarative handler metadata
  `-- serialized scalar records + external guard registry
                    |
                    v
       validate/normalize entire construction
                    |
          ambiguity/conflict/error? ----> fail before publication; retryable
                    |
                    v
          one atomic registrar publication
                    |
          direct entry OR frozen priority group
                    |
          +---------+------------------+
          |                            |
          v                            v
  sync/async selector          candidate-complete snapshot
  selects one entry            (one row per candidate)
          |                            |
          v                            +--> target/query flattening
  exact target+priority handler        `--> scalar to_dict records
          |
          v
  one existing lifecycle/result/history/trace path
```

The flow preserves the existing atomic registrar and Phase 22 lifecycle while making construction and projection candidate-complete. [VERIFIED: src/fast_fsm/core.py:1481-1504,2181-2421,4055-4226; .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:21-70]

### Recommended Project Structure

```text
src/fast_fsm/core.py                 # candidate metadata, adapters, declarative resolver, snapshot/query/serialization
tests/test_builder.py                # quick/builder/declarative sync+async parity and retryability
tests/test_advanced_functionality.py # from_dict/to_dict schema, legacy ambiguity, clone behavior
tests/test_graph_invariants.py       # flattened snapshot identity/order and atomic registrar invariants
tests/test_state_machine_utils.py    # deduplicated trigger/target query behavior
tests/test_transition_lifecycle.py   # exactly one selected declarative handler and unchanged callbacks
tests/test_async.py                  # async declarative/query parity
tests/test_mypyc_guard.py            # exact record fields, slots, closed union, native probe
.specify/memory/spr-core-api.md       # living constructor/declarative/serialization contract
```

These are the current source-to-test seams mandated by project guidance and Phase 23 context. [VERIFIED: .github/copilot-instructions.md:228-255; .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:105-113]

### Pattern 1: One candidate-complete projection seam

Add a private helper that returns the existing frozen group tuple or a one-element tuple for a direct entry. Use it only in cold construction, snapshot, serialization, and query paths; dispatch must keep its direct singleton branch and its existing no-copy group iteration. [VERIFIED: src/fast_fsm/core.py:631-650,2181-2243,4055-4097; .planning/phases/22-ordered-runtime-selection-lifecycle-integration/22-VERIFICATION.md:31-34]

Extend `_GraphTransition` with candidate priority and the optional scalar condition reference, then make `_graph_snapshot_owned()` append one row for each flattened entry inside its existing ownership boundary. The deterministic order is sorted source, sorted trigger, then the already ascending group tuple; no dispatch-time sorting is introduced. [VERIFIED: src/fast_fsm/core.py:660-690,1324-1373,1528-1530; .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:48-50,61-67]

Keep public `snapshot()` unchanged at the exact shape `{"state": <current_state_name>, "version": 1}`. It stores runtime position, not topology; `to_dict()` and the private graph snapshot own candidate topology. [VERIFIED: src/fast_fsm/core.py:2807-2822; .planning/PROJECT.md:96-104]

### Pattern 2: Validate-resolve-publish serialized construction

Use `condition_ref` as the recommended record spelling because it is explicit, does not overload the existing callable-free `condition` omission, and reads naturally in JSON/YAML/TOML. This exact spelling is an agent-discretion schema choice; the locked contract is that the value is an optional opaque scalar reference. [VERIFIED: .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:47-59,72-76]

`to_dict()` must emit one record per candidate with `trigger`, `from`, `to`, and numeric `priority`; include `condition_ref` only when the candidate has one. Never infer the reference from `Condition.name`: names are descriptive and need not be unique, while the reference is an application-owned registry key. The emitted values remain within the stdlib encoder's default scalar/container set. [VERIFIED: src/fast_fsm/conditions.py:205-220; .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:47-59; CITED: https://docs.python.org/3.10/library/json.html#json.JSONEncoder]

`from_dict()` should perform these steps before publishing topology: validate container and required fields; exact-validate every priority with `_normalize_priority()`; expand source lists for ambiguity accounting; validate each explicit reference as a non-empty string; resolve every explicit reference against `conditions`; resolve a bare-trigger key only when it names exactly one candidate and is not already used as an explicit reference; then normalize every row and commit once. Extra registry keys may retain the existing ignored behavior. Missing explicit references and ambiguous legacy trigger mappings must raise index-oriented errors without echoing callable representations. [VERIFIED: src/fast_fsm/core.py:653-657,1080-1192,1399-1504; .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:47-59,72-76]

Repeated explicit references are valid: several records may deliberately point to one external guard object. Explicit record references take precedence over legacy trigger interpretation, so a key cannot accidentally serve both namespaces. This is the prescriptive ambiguity rule that best satisfies D-06 without heuristic attachment. [VERIFIED: .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:52-59]

Store the optional reference as a trailing field on `TransitionEntry`, `_PreparedTransition`, and `_GraphTransition`. Include it in exact duplicate identity for internally referenced candidates: the same target/condition/priority with a different reference must not silently discard one serialized identity. Existing public calls supply `None`, preserving their current duplicate behavior and callback/runtime path. [VERIFIED: src/fast_fsm/core.py:611-700,1399-1529; .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:47-67]

### Pattern 3: Immutable plural declarative metadata

Replace `_handlers: Dict[str, Dict[str, Any]]` with a trigger-to-tuple collection of typed, frozen/slotted handler records containing method, source metadata, target metadata, condition, async classification, and exact priority. Build the complete local collection in `_discover_handlers()` and publish it once; do not overwrite while walking `dir(self)`. Mypyc native classes restrict attributes to statically visible definitions and only partially optimize dataclasses, so keep every field declared and retain slots/native tests. [VERIFIED: src/fast_fsm/core.py:4610-4654; CITED: https://mypyc.readthedocs.io/en/stable/native_classes.html]

Extend `@transition(...)` with keyword-only `priority=0`, validate through the same exact-int normalizer, and preserve existing scalar metadata attributes for unstacked compatibility tests. Prefer also accumulating immutable declaration metadata on the decorated method so stacked uses preserve every declaration instead of the outer decorator overwriting the inner one. [VERIFIED: src/fast_fsm/core.py:4361-4386,653-657; .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:21-45]

Change `_resolve_declarative_handler()` to accept the selected candidate priority and filter by canonical source name, trigger, target name, and exact priority. It returns no handler when none matches and one handler when exactly one matches; multiple matches are malformed declarative topology and must fail before transition publication where construction has enough context. Both sync and async candidate selectors then store only that resolved handler in `_PreparedDispatch`, preserving the one-handler lifecycle. [VERIFIED: src/fast_fsm/core.py:703-714,2181-2277,4055-4141,4398-4419; .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:35-45]

For direct `handle_event()` / `handle_event_async()`, invoke only when the trigger has one unambiguous declaration after source filtering. If several declarations remain, return one failed compatibility `TransitionResult` and invoke none; do not choose the lowest declaration because direct calls have not evaluated the FSM candidate guards or target permission. Apply the same unique-match rule to direct `can_transition*()` when target metadata still leaves multiple priorities. [VERIFIED: src/fast_fsm/core.py:4666-4812; .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:35-45]

Flatten handler tuples in both `FSMBuilder._detect_async_requirements()` and `_preflight_async_requirements()`. Every declaration must participate in async classification even when it is not the first discovered handler for its trigger; otherwise explicit sync can silently construct a machine containing a hidden async guard/handler. [VERIFIED: src/fast_fsm/core.py:4927-4965,5165-5201; .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:30-45]

### Pattern 4: Construction adapters replay the registrar

`FSMBuilder` already stages five values `(trigger, from_state, to_state, condition, priority)`, validates before append, builds into a local candidate, and publishes `_machine` only after one `add_transitions()` call and callback wiring. Preserve this architecture; only update its declarative metadata iteration and add candidate-group retryability tests. [VERIFIED: src/fast_fsm/core.py:5003-5061,5213-5311]

Teach `StateMachine.quick_build()` and `quick_fsm()` the existing three-, four-, and five-field transition row forms accepted by `add_transitions()`. Parse endpoint identity from those forms, create a local machine, and materialize all rows through one batch call rather than per-row `add_transition()`. Ordinary three-field behavior remains unchanged; exact priority validation and group tie rules stay centralized. [VERIFIED: src/fast_fsm/core.py:963-1078,1572-1668,5626-5650; .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:21-33]

Do not alter `from_states()` or `simple_fsm()`: neither declares transitions, so they cannot lose candidate multiplicity. [VERIFIED: src/fast_fsm/core.py:925-960,5606-5623]

### Pattern 5: Query and clone semantics stay high-level

Keep `triggers` and `get_available_triggers()` deduplicated because they answer event availability, not candidate count. Make `get_reachable_states()` flatten every local slot and deduplicate target names, and make `transition_exists(..., to_state=...)` return true when any candidate in the slot reaches that target. `can_trigger()` and `can_trigger_async()` already use the Phase 22 selectors and require only declarative candidate-resolution regression coverage. [VERIFIED: src/fast_fsm/core.py:2022-2117,4036-4044; .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:61-70]

The current clone implementation already copies outer/per-state dictionaries and shares entry/group values while constructing fresh ownership state; retain it and test the new condition reference and candidate-complete snapshot on both sync and async clones. Do not rebuild groups through registration during clone. [VERIFIED: src/fast_fsm/core.py:2858-2920,3784-3796; .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:61-67]

Leave `debug_info()` transition counts, validation meanings, Mermaid/PlantUML/JSON presentation, adjacency, and generated paths to Phase 24. Phase 23 may make `debug_info()` stop failing indirectly by fixing reachable-state queries, but it must not define candidate-aware diagnostic counts or renderer schema. [VERIFIED: src/fast_fsm/core.py:3499-3557; .planning/ROADMAP.md:103-116; .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:138-142,157-163]

### Component Responsibilities

| Component | Phase 23 responsibility | Boundary |
|-----------|--------------------------|----------|
| `TransitionEntry` / `_PreparedTransition` | Carry optional condition reference beside target/guard/priority | Trailing additive field; no caller kwargs. [VERIFIED: src/fast_fsm/core.py:611-700; .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:68-70] |
| Private slot-entry helper | Flatten one slot for cold consumers | Never replace direct dispatch branches. [VERIFIED: src/fast_fsm/core.py:2181-2243,4055-4097] |
| `_GraphTransition` / `_GraphSnapshot` | One immutable row per candidate with priority/reference | Internal topology seam only; public snapshot v2 remains out of scope. [VERIFIED: src/fast_fsm/core.py:660-690; .planning/PROJECT.md:96-104] |
| `from_dict()` / `to_dict()` | Validate, resolve, atomically replay, and emit scalar candidate records | Never serialize or infer callables. [VERIFIED: src/fast_fsm/core.py:1080-1227; .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:47-59] |
| `transition()` / `DeclarativeState` | Preserve all declarations and exact candidate handler identity | Direct helper ambiguity invokes none. [VERIFIED: src/fast_fsm/core.py:4361-4812; .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:35-45] |
| `FSMBuilder` | Flatten declarative metadata during preflight; retain local-until-success publication | Do not add adapter-specific group logic. [VERIFIED: src/fast_fsm/core.py:4927-5311] |
| quick/factory helpers | Accept priority-bearing row forms and call one batch registrar | `from_states`/`simple_fsm` unchanged. [VERIFIED: src/fast_fsm/core.py:925-1078,5606-5650] |
| query helpers / clone | Flatten target checks; preserve deduplicated triggers and shared immutable values | Diagnostic counts remain Phase 24. [VERIFIED: src/fast_fsm/core.py:2022-2095,2858-2920] |

### Anti-Patterns to Avoid

- **Trigger-wide declarative lookup:** `_handlers[trigger]` cannot identify target or priority and is the exact overwrite bug this phase removes. [VERIFIED: src/fast_fsm/core.py:4410-4419,4627-4654]
- **Condition name as serialized key:** descriptive names are not a unique application registry and may collide; preserve an explicit opaque reference instead. [VERIFIED: src/fast_fsm/conditions.py:205-220; .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:47-59]
- **Legacy guard fan-out:** do not apply `conditions[trigger]` to two or more expanded candidates; raise before construction. [VERIFIED: src/fast_fsm/core.py:1184-1190; .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:52-59]
- **Per-adapter group assembly:** quick builders and deserializers must not sort/merge candidates themselves; the atomic registrar owns priority validation, ties, duplicates, and graph-version updates. [VERIFIED: src/fast_fsm/core.py:1399-1530; .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:21-33]
- **Snapshot collapse:** never reduce a group to its first candidate or one target set before storing priority/reference identity. [VERIFIED: src/fast_fsm/core.py:1324-1373; .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:47-67]
- **Dispatch regression:** do not route selectors through the cold tuple helper or add sorting/copying to trigger paths. [VERIFIED: .planning/phases/22-ordered-runtime-selection-lifecycle-integration/22-VERIFICATION.md:31-34]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Priority merge/tie semantics in each factory | Adapter-local sorting and overwrite rules | Existing `_normalize_transition_request()` + `_commit_transition_plan()` | The registrar already provides exact-int validation, immutable ordering, duplicate identity, conflict rollback, and one version change. [VERIFIED: src/fast_fsm/core.py:1399-1530] |
| Callable persistence | Pickle/import-path/custom JSON callable format | Opaque scalar reference + caller-supplied `conditions` registry | Portable topology must not execute or encode application code. [VERIFIED: .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:47-59; CITED: https://docs.python.org/3.10/library/json.html#json.JSONEncoder] |
| New public topology snapshot version | Expanded runtime `snapshot()` | Candidate-complete private graph snapshot + `to_dict()` | The project explicitly excludes `snapshot()` v2 and assigns topology to `to_dict()`. [VERIFIED: .planning/PROJECT.md:96-104] |
| Declarative priority dispatcher | Handler-side sorting/selection | Phase 22 selector + exact selected-entry resolver | Selection must include transition guard, declarative guard, and target permission before lifecycle. [VERIFIED: .planning/phases/22-ordered-runtime-selection-lifecycle-integration/22-VERIFICATION.md:23-34] |

**Key insight:** adapters should transport declarations and projections should flatten candidates; neither should become a second state-machine policy engine. [VERIFIED: .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:21-41,61-67]

## Runtime State Inventory

| Category | Items Found | Action Required |
|----------|-------------|-----------------|
| Stored data | No repository-owned JSON/YAML/TOML machine configuration was found. External legacy `from_dict()` documents may exist, but the project is a library and they are not repo-managed runtime state. [VERIFIED: local repository config search, 2026-09-07] | Code compatibility: accept old records without priority as priority `0`; fail only ambiguous legacy guard mappings. No data migration task. |
| Live service config | None — this phase adds no service, database, dashboard, or remotely stored configuration. [VERIFIED: .planning/REQUIREMENTS.md:44-55,78-80] | None. |
| OS-registered state | None — no launchd/systemd/task registration participates in FSM topology. [VERIFIED: repository workflow/config search, 2026-09-07] | None. |
| Secrets/env vars | Existing build-mode variables choose pure/compiled packaging and do not encode transition schema or guard keys. [VERIFIED: setup.py:23-29] | None. Never treat opaque condition references as secrets or log callable values. |
| Build artifacts | Ignored in-place native extension shadows and egg metadata are present in the worktree. [VERIFIED: local build-artifact inventory, 2026-09-07] | Run the established non-destructive pure-source preflight and rebuild native evidence after core changes; no persistent-data migration. |

## Common Pitfalls

### Pitfall 1: A correct runtime selector with a lossy constructor
**What goes wrong:** direct registration works, but quick/declarative/from-dict construction overwrites a candidate or loses priority. [VERIFIED: src/fast_fsm/core.py:963-1078,1184-1190,4637-4654]  
**Why it happens:** each adapter currently has a singular row/trigger assumption. [VERIFIED: same source ranges]  
**How to avoid:** replay one complete declaration batch through the registrar and compare fingerprints across every constructor. [VERIFIED: .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:21-33]  
**Warning signs:** any adapter writes `_transitions` directly, calls `add_transition()` in a publication loop, or stores one handler dictionary per trigger.

### Pitfall 2: Ambiguous legacy guards silently become shared guards
**What goes wrong:** one bare trigger key attaches the same guard to safety candidates that require different facts. [VERIFIED: src/fast_fsm/core.py:1124-1136,1184-1190]  
**Why it happens:** trigger names were previously treated as global guard identity.  
**How to avoid:** count expanded candidates first; permit a legacy key only at cardinality one, otherwise raise before any registrar call. [VERIFIED: .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:52-59]  
**Warning signs:** a conditions lookup remains inside the per-record registration loop.

### Pitfall 3: Handler selection uses target but not priority
**What goes wrong:** two candidates with the same source/trigger/target but different priorities resolve the same handler/guard. [VERIFIED: src/fast_fsm/core.py:4398-4419]  
**Why it happens:** Phase 22 extended topology identity, but the resolver signature still ends at target. [VERIFIED: src/fast_fsm/core.py:4398-4406]  
**How to avoid:** pass `entry.priority` into the resolver before `_PreparedDispatch` is built and test same-target candidates explicitly. [VERIFIED: .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:35-45]  
**Warning signs:** `_resolve_declarative_handler(source, trigger, target)` still has only three identity inputs.

### Pitfall 4: Plural handlers break async preflight
**What goes wrong:** builder auto-detection sees a tuple as one handler or checks only the first declaration, publishing an invalid sync machine. [VERIFIED: src/fast_fsm/core.py:4927-4965,5165-5201]  
**Why it happens:** both preflight loops assume each dictionary value is one metadata mapping.  
**How to avoid:** flatten every declaration through one helper shared by detection and preflight. [VERIFIED: .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:30-45]  
**Warning signs:** `.get("is_async")` is called directly on `_handlers.values()`.

### Pitfall 5: Native layout drift
**What goes wrong:** pure tests pass while compiled field assignment, subclassing, or record layout fails. Mypyc native classes allow assignment only to statically declared attributes, and dataclass support is partial. [CITED: https://mypyc.readthedocs.io/en/stable/native_classes.html]  
**Why it happens:** candidate/declarative/projection records live in the sole compiled module. [VERIFIED: setup.py:16-39]  
**How to avoid:** update exact AST slot/field assertions, run mypy, slots policy, an in-place compiled build, and focused native behavior. [VERIFIED: tests/test_mypyc_guard.py:384-463,1445-1503]  
**Warning signs:** new instance attributes appear only in `__init__`, handler data widens to untyped mutable lists, or compiled import is skipped.

### Pitfall 6: Phase boundary creep
**What goes wrong:** Phase 23 starts defining candidate-aware diagnostic counts or renderer schemas, creating two projections before the snapshot contract is stable. [VERIFIED: .planning/ROADMAP.md:103-116]  
**How to avoid:** make the snapshot complete, but leave validation meanings, debug counts, structured/human output, adjacency, and generated paths to Phase 24; leave docs/benchmarks/installed artifacts/drone work to Phase 25. [VERIFIED: .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:138-142,157-163]

## Code Examples

### Candidate-complete cold-path flattening

```python
# Source pattern: current storage union in src/fast_fsm/core.py:631-650.
# Dispatch continues to branch directly; cold consumers may use this helper.
def _transition_entries(slot: _TransitionSlot) -> Tuple[TransitionEntry, ...]:
    if isinstance(slot, _TransitionGroup):
        return slot.entries
    return (slot,)
```

This helper is implementation guidance, not a new public API. [VERIFIED: src/fast_fsm/core.py:631-650; .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:61-67]

### Recommended scalar serialized record

```python
# Agent-discretion schema recommendation grounded in 23-CONTEXT.md:47-59.
record = {
    "trigger": trigger_name,
    "from": source_name,
    "to": target_name,
    "priority": priority_value,
    "condition_ref": guard_ref,
}
conditions = {guard_ref: guard_condition}
```

The contract is one record per candidate, exact numeric priority, and an optional opaque scalar reference resolved from a separate live registry. [VERIFIED: .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:47-59; CITED: https://docs.python.org/3.10/library/json.html#json.JSONEncoder]

### Candidate-qualified declarative declaration

```python
# Existing decorator shape: src/fast_fsm/core.py:4361-4386.
# Phase 23 adds the exact-int priority qualifier without changing callback args.
@transition(
    trigger_name,
    from_state=source_name,
    to_state=target_name,
    condition=guard_condition,
    priority=priority_value,
)
def command_return_home(self, *args, **kwargs):
    ...
```

Selection remains in the FSM; the chosen declaration supplies only its guard and one post-commit handler. [VERIFIED: .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:35-45,68-70]

## State of the Art

| Old/current singular approach | Phase 23 approach | Impact |
|-------------------------------|-------------------|--------|
| `quick_build()` accepts/destructures only 3-tuples and loops `add_transition()` | Accept established 3/4/5 row forms and commit one registrar batch | Factories can construct groups with the same atomic semantics as direct registration. [VERIFIED: src/fast_fsm/core.py:963-1078,1572-1668] |
| `_handlers[trigger] = handler_info` | Immutable plural per-trigger declarations resolved by source/target/priority | No attribute-order overwrite or wrong candidate callback. [VERIFIED: src/fast_fsm/core.py:4637-4654; .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:35-45] |
| Bare `conditions[trigger]` is reused for every record | Explicit per-record reference; legacy key only at cardinality one | Ambiguity becomes an error instead of a silent safety-policy change. [VERIFIED: src/fast_fsm/core.py:1124-1136,1184-1190; .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:52-59] |
| Snapshot/serialization/target queries call `_require_singleton_entry()` | Cold-path flattening with one row/check per candidate | Complete identity reaches Phase 24 without changing dispatch. [VERIFIED: src/fast_fsm/core.py:1211-1221,1345-1363,2047-2093; .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:61-67] |
| Clone shares direct/group values and copies tables | Same structure plus reference/snapshot parity tests | No clone reconstruction or new ownership state. [VERIFIED: src/fast_fsm/core.py:2858-2920,3784-3796] |

**Deprecated/outdated:** the `from_dict()` documentation that says one trigger condition is applied to all matching transitions becomes valid only for an unambiguous single candidate; update the living SPR and docstring in the same implementation change. [VERIFIED: src/fast_fsm/core.py:1124-1136; .specify/memory/spr-core-api.md:59; .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:52-59]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| — | None. Exact private names and the `condition_ref` spelling are prescriptive recommendations made under the explicit agent-discretion grant, not claims about existing behavior. | — | — |

## Open Questions

None blocking. The locked decisions resolve topology, precedence, ambiguity, and phase boundaries. The planner may adopt the recommended `condition_ref` spelling and the fail-without-invocation direct-handler ambiguity rule under the granted private/schema discretion. [VERIFIED: .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:35-76]

## Environment Availability

Step 2.6 skipped: this is a code/config-only phase with no external service or new dependency. The existing Python/uv/mypyc/pytest toolchain is present; the focused Phase 23 baseline completed successfully. [VERIFIED: local tool/version checks and focused pytest run, 2026-09-07]

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest `8.4.1` with pytest-asyncio auto mode [VERIFIED: pyproject.toml:56-74; local version check] |
| Config file | `pyproject.toml` [VERIFIED: pyproject.toml:56-74] |
| Quick run command | `uv run pytest tests/test_builder.py tests/test_graph_invariants.py tests/test_state_machine_utils.py tests/test_advanced_functionality.py::TestFromDict tests/test_advanced_functionality.py::TestToDict tests/test_advanced_functionality.py::TestFromDictConditions tests/test_priority_selection.py -x -q` [VERIFIED: focused run passed, 2026-09-07] |
| Full suite command | `uv run pytest tests/ -x -q` [VERIFIED: .github/copilot-instructions.md:65-70] |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PAR-01 | quick/factory/builder/declarative paths preserve groups, priority, exact handler identity, async preflight, and retryability | Unit/integration | `uv run pytest tests/test_builder.py tests/test_async.py -k 'priority or declarative or quick or retry' -x -q` | Existing files; Wave 0 cases needed |
| PAR-02 | sync/async query selection stays non-mutating; snapshot/target queries/clone preserve all candidates and priority metadata | Unit/integration | `uv run pytest tests/test_graph_invariants.py tests/test_state_machine_utils.py tests/test_transition_lifecycle.py tests/test_priority_selection.py -k 'priority or candidate or clone or snapshot or reachable or transition_exists' -x -q` | Existing files; Wave 0 cases needed |
| PAR-03 | scalar JSON round-trip, same-target multiplicity, explicit guard refs, ambiguous legacy failures, no callables | Unit/integration | `uv run pytest tests/test_advanced_functionality.py -k 'FromDict or ToDict or condition_ref or priority' -x -q` | Existing file; Wave 0 cases needed |

### Required Test Matrix

- Direct, builder, quick-build, and quick-factory topology fingerprints match for priorities registered out of order, including same-target candidates and multi-source rows.
- A late conflict/malformed priority/async preflight failure publishes no factory result and leaves builder staging/machine cache/mode retryable.
- Multiple same-trigger declarative methods survive discovery; exact source/target/priority selects one guard and invokes one handler in sync and async lifecycles; later/lower handlers remain untouched.
- Direct `handle_event*()` keeps every one-handler legacy result shape; ambiguous declarations return failure and invoke zero handlers.
- Explicit condition references attach only their record's guard; repeated explicit refs deliberately share one object; missing refs and bare-trigger mappings with two expanded candidates raise before publication.
- `to_dict()` order is source/trigger/priority, always includes numeric priority, conditionally includes only scalar reference, and survives `json.dumps`/`loads`; no callable, `Condition`, or repr appears.
- `get_available_triggers()` remains deduplicated; reachable targets and target-specific existence flatten all candidates; public runtime snapshot remains version 1 and unchanged.
- Sync/async clones share immutable entry/group/reference values but own independent outer/inner tables and fresh ownership primitives; later registration cannot mutate the peer.
- AST/slots tests include the new candidate/projection/declarative fields, selector AST stays unchanged, mypy and ty run, slots-policy passes, compiled import succeeds, and focused native construction/serialization/declarative behavior matches pure Python.

### Sampling Rate

- **Per task commit:** run the directly modified test file/class in under 30 seconds.
- **After declarative changes:** run builder + async + lifecycle + priority selection focused cases.
- **After record/projection changes:** run graph invariants + serialization + mypyc guard, then mypy and advisory ty.
- **Phase gate:** full pure suite, Ruff, mypy, ty, slots-policy, compiled build/import, and focused native Phase 23 suite.

### Wave 0 Gaps

| Test area | Required additions |
|-----------|--------------------|
| `tests/test_builder.py` | plural/stacked declarative metadata, priority-qualified resolver, direct ambiguity, quick/factory group parity, builder retryability |
| `tests/test_advanced_functionality.py` | priority/reference round-trip, deterministic order, same-target candidates, explicit/missing/repeated refs, ambiguous legacy guard failure |
| `tests/test_graph_invariants.py` | flattened `_GraphSnapshot` rows and condition-reference/priority identity |
| `tests/test_state_machine_utils.py` | grouped reachable-state deduplication and any-target `transition_exists` |
| `tests/test_async.py` / `tests/test_transition_lifecycle.py` | async exact handler identity, one lifecycle, unchanged callback kwargs, clone/query parity |
| `tests/test_mypyc_guard.py` | exact new frozen/slotted record fields, plural-handler native typing, unchanged selector no-copy/no-sort checks, compiled behavior |

The focused existing baseline passed before implementation, so Wave 0 is additive rather than test-infrastructure repair. [VERIFIED: focused pytest run, 2026-09-07]

## Security Domain

Security enforcement is enabled because `.planning/config.json` does not set `security_enforcement` to false. [VERIFIED: .planning/config.json:1-37]

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | No | Library phase has no authentication boundary. |
| V3 Session Management | No | FSM ownership is concurrency control, not an application session. |
| V4 Access Control | No | State permission is domain policy, not user authorization. |
| V5 Input Validation | Yes | Validate serialized container/field types, exact non-bool priority, non-empty scalar references, complete guard resolution, and ambiguity before one publication. [VERIFIED: src/fast_fsm/core.py:653-657,1080-1192,1399-1504; .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:30-33,52-59] |
| V6 Cryptography | No | No cryptographic or secret-storage feature is introduced. |

### Known Threat Patterns for the Python FSM Runtime

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Wrong guard attached by ambiguous legacy key | Tampering | Count expanded candidates and fail before construction when a bare trigger key is not unique. [VERIFIED: .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:52-59] |
| Callable or exception repr leaks through topology output/errors | Information Disclosure | Emit only scalar references; use transition index/field names in validation errors and never stringify live callables. [VERIFIED: .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:47-59] |
| Malformed late record leaves usable prefix topology | Tampering | Validate/normalize all rows then publish once through the atomic registrar. [VERIFIED: .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:21-33; src/fast_fsm/core.py:1481-1504] |
| Huge unrelated topology enters dispatch through projection reuse | Denial of Service | Keep flattening on cold projection/query paths and preserve Phase 22's direct singleton/local group selectors. [VERIFIED: .planning/phases/22-ordered-runtime-selection-lifecycle-integration/22-VERIFICATION.md:31-34] |
| Attribute discovery order chooses a handler | Tampering | Store every declaration and require one exact source/target/priority match; ambiguous direct helpers invoke none. [VERIFIED: .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:35-45] |

## Phase Exclusions

- Candidate-aware validator severity, shadow analysis, diagnostic budgets/counts, adjacency, Mermaid, PlantUML, Markdown, structured JSON presentation, and generated paths belong to Phase 24. [VERIFIED: .planning/ROADMAP.md:103-116]
- Public docs, migration guide, performance claims/benchmarks, installed pure/compiled conformance, release evidence, and the drone controller example belong to Phase 25. [VERIFIED: .planning/ROADMAP.md:118-132]
- Public `snapshot()` v2, callable serialization, dynamic priorities, equal-priority policies, runtime mutation/removal/reordering, and parallel async evaluation remain out of scope. [VERIFIED: .planning/PROJECT.md:96-104; .planning/REQUIREMENTS.md:66-80; .planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md:157-163]

## Sources

### Primary (HIGH confidence)

- `.planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md` — locked decisions, discretion, and exclusions.
- `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, and `.planning/PROJECT.md` — PAR-01 through PAR-03, phase success criteria, project constraints.
- `.planning/phases/21-priority-contract-atomic-registration/21-RESEARCH.md` and `.planning/phases/22-ordered-runtime-selection-lifecycle-integration/22-RESEARCH.md` — established topology/selection research.
- `.planning/phases/22-ordered-runtime-selection-lifecycle-integration/22-VERIFICATION.md` and `22-03-SUMMARY.md` — verified runtime selector, metadata, complexity, and native boundaries.
- `src/fast_fsm/core.py` and `src/fast_fsm/conditions.py` — current implementation source of truth.
- Relevant builder, async, graph, lifecycle, advanced, utility, priority, and mypyc tests — current executable compatibility contracts.
- `.github/copilot-instructions.md`, `AGENTS.md`, `pyproject.toml`, and `setup.py` — workflow, toolchain, slots, and compiled-unit constraints.

### Secondary (MEDIUM confidence)

- [Python 3.10 `json.JSONEncoder`](https://docs.python.org/3.10/library/json.html#json.JSONEncoder) — default JSON-native value boundary and custom-object failure behavior.
- [mypyc native classes](https://mypyc.readthedocs.io/en/stable/native_classes.html) — static attribute/native class and partial dataclass constraints. The fetched current docs were cross-checked against the repository's pinned mypyc tests.

### Tertiary (LOW confidence)

- None.

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — repository pins and installed tool versions were verified; no package is added.
- Architecture: HIGH — derived from current core source, locked Phase 23 context, and verified Phase 21/22 contracts.
- Serialization/ambiguity: HIGH — the dangerous current trigger-wide lookup is visible in source and the replacement behavior is locked by D-05/D-06.
- Declarative direct-call policy: HIGH — no target/priority exists on the direct method signature, and the no-order/candidate-specific constraints rule out silently choosing one declaration.
- Mypyc risks: HIGH — record layout is already AST-guarded and the native-class restrictions were checked against official docs.

**Research date:** 2026-09-07  
**Valid until:** 2026-10-07 (stable in-repository architecture; re-check after any Phase 23 implementation or core-schema change)
