# Phase 24: Candidate-Aware Diagnostics & Output - Research

**Researched:** 2026-09-06
**Domain:** Python snapshot-backed graph diagnostics, conservative priority analysis, bounded structured output, and mypyc parity
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

### One immutable diagnostic projection
- **D-01:** Every validator, analysis helper, renderer, and export captures one
  immutable graph snapshot then derives its diagnostic graph solely from that
  snapshot. Consumers must not inspect private singleton-or-group runtime
  storage or recapture topology while producing one result. —
  **Reversibility:** costly — mixed projections would make reports internally
  inconsistent under mutation and violate the established snapshot/budget
  contract.

### Conservative candidate analysis
- **D-02:** A strictly increasing candidate group is deterministic. Equal or
  malformed priorities are validation errors. Shadow analysis must be
  conservative: report a lower candidate as provably shadowed only when the
  snapshot establishes that fact without evaluating user guards or permissions;
  otherwise distinguish a possible shadowing observation from a correctness
  error. — **Reversibility:** costly — false-positive safety diagnostics would
  cause users to distrust validation and may encourage removal of a live
  fallback.

### Candidate-complete output contract
- **D-03:** JSON, Mermaid, PlantUML, Markdown, generated paths, and adjacency
  data emit one edge/record per candidate in deterministic source, trigger,
  priority order. Numeric priority is explicit wherever a transition is shown;
  existing state, trigger, condition, title, Markdown, Mermaid, and PlantUML
  escaping remains the only text-encoding policy. — **Reversibility:** costly
  — output consumers need one stable, auditable representation of priority
  multiplicity rather than collapsed trigger pairs.

### Candidate-sized safety budgets
- **D-04:** Diagnostic edge counts, traversal work, result limits, and generated
  paths charge each candidate edge independently. On exhaustion, retain the
  current explicit incomplete-result/status behavior; never silently collapse
  candidates or emit an apparently complete partial projection. —
  **Reversibility:** costly — budgeting by collapsed slots would allow a large
  candidate group to evade the safety limits that protect diagnostics.

### the agent's Discretion
- Choose report field names and label punctuation that fit the established JSON,
  Mermaid, PlantUML, and Markdown contracts, provided priority is unambiguous,
  numeric, deterministic, and escaped only through the existing format-specific
  routines.
- Choose the narrowest static evidence for a provably shadowed candidate and
  place diagnostics-specific tests beside their existing validators/renderers.

### Deferred Ideas (OUT OF SCOPE)

None — performance claims, installed-artifact parity, public documentation,
and the complete drone example remain Phase 25 scope.
</user_constraints>

The constraints above are copied verbatim from the phase context. [VERIFIED: .planning/phases/24-candidate-aware-diagnostics-output/24-CONTEXT.md:21-63,147-151]

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DIAG-01 | “Validation treats strictly ordered candidate groups as deterministic, rejects malformed ties, and reports provably shadowed lower candidates conservatively.” | Group the already ordered diagnostic edges by source/trigger, validate exact increasing integer priorities, and classify shadowing from snapshot-captured static facts without invoking a condition or state policy. [VERIFIED: .planning/REQUIREMENTS.md:59-61; src/fast_fsm/core.py:1513-1566] |
| DIAG-02 | “JSON, Mermaid, PlantUML, Markdown, adjacency data, and generated paths preserve candidate multiplicity and priority under existing escaping and budget contracts.” | Carry numeric priority on `_DiagnosticEdge`, keep one row per snapshot transition, add priority to every emitted transition/path record, and reserve work/result/path counts once per candidate occurrence. [VERIFIED: .planning/REQUIREMENTS.md:63-65; src/fast_fsm/_diagnostics.py:194-221,432-574; src/fast_fsm/visualization.py:92-234,394-472,578-842] |
</phase_requirements>

## Summary

Phase 23 has already supplied the correct immutable input: `_graph_snapshot_owned()` flattens each source/trigger slot through `_transition_entries()` and appends one `_GraphTransition` for every candidate in sorted source, sorted trigger, and stored ascending-priority order. `_GraphTransition` already carries exact `priority`, optional `condition_ref`, scalar names, and identity-bearing state/condition references. [VERIFIED: src/fast_fsm/core.py:677-703,1513-1566; tests/test_graph_invariants.py:95-142] Phase 24 should therefore leave runtime storage and selectors untouched and repair only the downstream projection and consumers. [VERIFIED: .planning/phases/24-candidate-aware-diagnostics-output/24-CONTEXT.md:21-28,130-134]

The first loss occurs in `_graph_from_snapshot()`: `_DiagnosticEdge` currently retains only `from_index`, `trigger`, `to_index`, and `condition_name`, so priority disappears at the scalar boundary. The next loss occurs in `FSMValidator.transitions`, whose target `set` collapses same-target candidates; `check_determinism()` then defines multiple distinct targets as non-determinism even though a strict priority group has one deterministic first-match order. [VERIFIED: src/fast_fsm/_diagnostics.py:80-102,194-221; src/fast_fsm/validation.py:141-173,396-424] Renderers and exports already iterate `graph.edges`, so once priority survives that one boundary, they can remain one-snapshot consumers and emit one candidate each without learning the private singleton/group representation. [VERIFIED: src/fast_fsm/visualization.py:84-89,151-164,207-220,394-472]

For conservative shadow analysis, capture one additional scalar fact on `_GraphTransition`: whether the candidate is statically unconditional. The narrow proof should be `entry.condition is None` and `type(source_state) is State`. Exact base `State.can_transition()` returns `True`; using the exact type excludes interpreted subclasses, `DeclarativeState`, and custom permission logic. [VERIFIED: src/fast_fsm/core.py:773-829,2428-2591] An earlier statically unconditional candidate proves every later candidate in that source/trigger group is shadowed. An earlier unguarded candidate on any other state type is only a possible shadow, because a custom or declarative permission may still reject it. Do not recognize arbitrary guard names or call `AlwaysCondition.check()`; that would execute user-adjacent behavior or confuse a label/type hint with proof. This is the prescriptive narrow-static-evidence choice authorized by D-02. [VERIFIED: .planning/phases/24-candidate-aware-diagnostics-output/24-CONTEXT.md:30-38,57-63; src/fast_fsm/core.py:2510-2591]

**Primary recommendation:** plan three ordered units: (1) extend the immutable core/diagnostic projection and implement strict-priority plus conservative shadow validation, (2) propagate priority and candidate-sized accounting through adjacency, paths, JSON, Mermaid, PlantUML, and both Markdown report paths, and (3) lock one-snapshot, escaping, budget, slots/type, pure-source, and fresh-native behavior with focused and full regression gates. [VERIFIED: .planning/ROADMAP.md:123-133; .planning/phases/24-candidate-aware-diagnostics-output/24-CONTEXT.md:95-134]

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|--------------|----------------|-----------|
| Candidate snapshot facts | Library core projection | mypyc boundary | `core.py` owns the atomic snapshot capture and is the only place that can freeze state/condition facts at the topology read boundary. [VERIFIED: src/fast_fsm/core.py:691-722,1513-1566; setup.py:16-39] |
| Scalar candidate graph | Interpreted diagnostics | Core snapshot | `_diagnostics.py` converts one immutable snapshot to positional scalar edges and must retain priority/multiplicity without importing runtime storage. [VERIFIED: src/fast_fsm/_diagnostics.py:1-6,80-102,194-221] |
| Determinism and shadow classification | Validation layer | Diagnostic graph | Validation assigns meanings to ordered groups; it must not evaluate runtime guards or permissions. [VERIFIED: src/fast_fsm/validation.py:99-178,396-424; .planning/phases/24-candidate-aware-diagnostics-output/24-CONTEXT.md:30-38] |
| Adjacency and generated paths | Diagnostic algorithms | Validation adapters | The algorithms own candidate indices, traversal order, and budget charging; public validator methods only adapt their immutable results. [VERIFIED: src/fast_fsm/_diagnostics.py:432-574; src/fast_fsm/validation.py:262-305,369-394] |
| Mermaid, PlantUML, JSON, Markdown | Visualization/report sinks | Diagnostic graph and ledger | Final sinks append priority to each edge while preserving their existing grammar-specific escaping and one shared ledger. [VERIFIED: src/fast_fsm/visualization.py:42-111,114-234,394-472,694-842] |
| Dispatch, selection, callbacks, history | Phase 22/23 core; out of Phase 24 | — | Selectors already use one slot and stored group order; Phase 24 cannot call diagnostic helpers from a hot path or alter lifecycle behavior. [VERIFIED: src/fast_fsm/core.py:2351-2413; .specify/decisions/ADR-007-priority-topology.md:24-39] |

## Project Constraints (from AGENTS.md)

- Use `bd` for project issue tracking, JSON output for programmatic operations, and `discovered-from` links; do not create a parallel issue tracker. [VERIFIED: AGENTS.md:9-78]
- Use `uv` for Python and test/tool execution. Run targeted tests during implementation, run tests sequentially, and run the full suite once before integration. [VERIFIED: .github/copilot-instructions.md:32-38,60-66,229-256]
- Keep hot-path production classes slotted. The exact registered slots exceptions are “CompiledFuncCondition, TransitionError, and DiagnosticBudgetExceeded”; run the recursive slots-policy audit when a core record changes. [VERIFIED: .github/copilot-instructions.md:40-50,310-324]
- Preserve condition and callback `*args, **kwargs`; do not remove public symbols without deprecation. [VERIFIED: .github/copilot-instructions.md:55-58,325-326]
- Keep validation optional and outside runtime dispatch; keep `core.py` as the sole compiled module and add no runtime dependency. [VERIFIED: .github/copilot-instructions.md:332-338; setup.py:16-39; pyproject.toml:1-9]
- Ruff is format/fix then validate; mypy is blocking and ty is independently visible advisory feedback. [VERIFIED: .github/copilot-instructions.md:211-226]
- Preserve unrelated dirty-tree work and stage only explicit paths. This delegated task is local-only and must not push or perform remote operations. [VERIFIED: .github/copilot-instructions.md:109-125; delegated task scope]

## Standard Stack

### Core

| Library/tool | Version | Purpose | Why standard here |
|--------------|---------|---------|-------------------|
| Python | `>=3.10` | Frozen/slotted records, tuples, deterministic dictionary-based output | Existing supported runtime; no graph, serializer, or rendering dependency is needed. [VERIFIED: pyproject.toml:1-9] |
| mypyc | `1.17.1` build pin | Compile the extended `_GraphTransition` inside `core.py` | `core.py` is the sole selective compilation unit and the snapshot record is defined there. [VERIFIED: pyproject.toml:22-26,43-45; setup.py:16-39] |
| pytest | `8.4.1` detected | Validation, output golden, budget boundary, and snapshot-mutation tests | Existing configured sequential framework. [VERIFIED: pyproject.toml:12-20,56-74; local `uv run --offline pytest --version`, 2026-09-07] |
| stdlib `json` | Python 3.10 | Encode JSON-ready priority-bearing mappings/lists | The standard encoder preserves order for ordered containers, handles integer scalars, and raises for unsupported arbitrary objects unless explicitly adapted. [CITED: https://docs.python.org/3.10/library/json.html] |

### Supporting

| Tool | Version | Purpose | When to use |
|------|---------|---------|-------------|
| Ruff | `0.12.11` detected | Format/lint changed Python | Every implementation task touching source or tests. [VERIFIED: local `uv run --offline ruff --version`, 2026-09-07] |
| mypy | `1.17.1` detected | Blocking core/native type compatibility | After each task that changes `_GraphTransition` or typed output records. [VERIFIED: local `uv run --offline mypy --version`, 2026-09-07] |
| ty | `0.0.1-alpha.19` detected | Independent advisory type feedback | After mypy, without replacing the blocking authority. [VERIFIED: local `uv run --offline ty --version`, 2026-09-07] |
| Existing `_DiagnosticBudget` | Four fixed counted dimensions | Reserve before traversal, result emission, dense allocation, and path expansion | Reuse for every candidate-aware consumer; do not add a second limiter. [VERIFIED: src/fast_fsm/_diagnostics.py:31-77,104-191] |

### Alternatives Considered

| Instead of | Could use | Tradeoff |
|------------|-----------|----------|
| Extend `_DiagnosticEdge` once | Teach each renderer about `_GraphTransition` or runtime groups | That duplicates projection logic, risks mixed snapshots, and couples interpreted tools to private core storage. [VERIFIED: .planning/phases/24-candidate-aware-diagnostics-output/24-CONTEXT.md:21-28,113-124] |
| Static unconditional scalar captured by core | Evaluate guards or call `can_transition()` during validation | Evaluation may mutate user state, raise, depend on telemetry, or disagree with later dispatch; D-02 forbids it. [VERIFIED: src/fast_fsm/core.py:2449-2591; .planning/phases/24-candidate-aware-diagnostics-output/24-CONTEXT.md:30-38] |
| Exact base-`State` proof | Infer from condition name, `AlwaysCondition`, or arbitrary subclass shape | Names are display text, guard implementations are user-extensible, and subclasses may override permission. [VERIFIED: src/fast_fsm/core.py:773-829; src/fast_fsm/conditions.py:205-247] |
| Existing format-specific encoders | One generic sanitizer | Mermaid, PlantUML, and Markdown have different syntax; existing sinks already isolate their encoders. [VERIFIED: src/fast_fsm/visualization.py:42-81; .specify/decisions/ADR-006-bounded-diagnostics-safe-output.md:47-52] |
| Candidate records/indices in adjacency and paths | Collapse by source/trigger or target | Collapsing loses same-target multiplicity and lets candidate groups evade edge/result budgets. [VERIFIED: .planning/phases/24-candidate-aware-diagnostics-output/24-CONTEXT.md:40-55; src/fast_fsm/_diagnostics.py:432-574] |

**Installation:** none. Phase 24 uses the existing standard-library runtime and development toolchain. [VERIFIED: pyproject.toml:1-45; .planning/REQUIREMENTS.md:57-65]

## Package Legitimacy Audit

Not applicable: this phase installs no external package. [VERIFIED: pyproject.toml:1-45; .planning/phases/24-candidate-aware-diagnostics-output/24-CONTEXT.md:6-14]

## Architecture Patterns

### System Architecture Diagram

```text
public diagnostic/report call
          |
          v
StateMachine._graph_snapshot()  -- exactly once under ownership boundary
          |
          | immutable candidate rows:
          | source, trigger, target, condition label, priority, static fact
          v
_graph_from_snapshot()
          |
          v
tuple-backed _DiagnosticGraph
  one _DiagnosticEdge per candidate, in snapshot order
          |
          +----------------------+-----------------------+
          |                      |                       |
          v                      v                       v
 strict group validation    bounded graph work      final output sinks
 priorities + shadowing     reach/SCC/adj/path       JSON/diagrams/Markdown
          |                      |                       |
          +----------------------+-----------------------+
                                 |
                    reserve-before-work/result/path
                                 |
                    complete value OR fixed explicit
                    DiagnosticBudgetExceeded/status
```

This preserves the Phase 19 one-capture architecture while making the one scalar edge record the only candidate-aware diagnostic seam. [VERIFIED: .specify/decisions/ADR-006-bounded-diagnostics-safe-output.md:21-52,65-72; src/fast_fsm/visualization.py:84-89]

### Recommended Project Structure

```text
src/fast_fsm/core.py                    # append static snapshot fact only; no diagnostic traversal
src/fast_fsm/_diagnostics.py            # priority-bearing scalar edge, grouping, adjacency, paths, budgets
src/fast_fsm/validation.py              # determinism/shadow semantics, metrics, JSON/Markdown/text reports
src/fast_fsm/visualization.py           # Mermaid/PlantUML/JSON/Markdown priority rendering
tests/test_graph_invariants.py           # immutable candidate snapshot order/static-fact capture
tests/test_diagnostic_contracts.py       # one-capture and exact candidate-sized budget/path contracts
tests/test_validation.py                 # strict priority, malformed group, definite/possible shadow reports
tests/test_visualization.py              # candidate-complete escaped output goldens
tests/test_mypyc_guard.py                # exact frozen/slotted core record and fresh-native probe
.specify/memory/spr-core-api.md          # living diagnostic/output candidate contract
```

The context names `tests/test_diagnostic_budgets.py`, but no such file exists; the active budget/snapshot suite is `tests/test_diagnostic_contracts.py`. Plan against the real file and do not create a duplicate budget suite. [VERIFIED: .planning/phases/24-candidate-aware-diagnostics-output/24-CONTEXT.md:104-106; repository file inventory and tests/test_diagnostic_contracts.py:1-41]

### Pattern 1: Extend the existing scalar edge, not the runtime storage

The current discrete snapshot fields are verbatim: `“from_state”, “trigger”, “to_state”, “condition”, “from_state_name”, “to_state_name”, “condition_name”, “priority”, “condition_ref”`. [VERIFIED: src/fast_fsm/core.py:691-703] The current diagnostic edge fields are verbatim: `“from_index”, “trigger”, “to_index”, “condition_name”`. [VERIFIED: src/fast_fsm/_diagnostics.py:80-88]

Append `priority` plus a static unconditional boolean to the frozen/slotted core snapshot row, then copy priority, guard presence, and the static fact into `_DiagnosticEdge`. Preserve transition order exactly; do not sort in `_graph_from_snapshot()` because the producer already emits source/trigger/stored-priority order. This is an agent-discretion private-field recommendation, not a claim about an existing name. [VERIFIED: src/fast_fsm/core.py:1534-1566; tests/test_graph_invariants.py:95-142]

Compute the static boolean during owned snapshot capture with the narrow rule `entry.condition is None and type(source_state) is State`. The rule does not call user code and remains false for subclasses and declarative states even when they appear unconditional. [VERIFIED: src/fast_fsm/core.py:773-829,1513-1566; .planning/phases/24-candidate-aware-diagnostics-output/24-CONTEXT.md:30-38,57-63]

### Pattern 2: Validate groups by identity and order, never by target cardinality

Scan `graph.edges` once and group consecutive edges by `(from_index, trigger)`. For each candidate, reserve one deterministic work unit before inspecting its priority. Exact built-in integers in strictly increasing order are deterministic regardless of target multiplicity. A non-integer, Boolean, duplicate, or descending priority is a malformed correctness error. [VERIFIED: src/fast_fsm/core.py:684-688,1534-1555; .planning/phases/24-candidate-aware-diagnostics-output/24-CONTEXT.md:30-38]

Keep the existing `check_determinism()` keys `“is_deterministic”` and `“non_deterministic_transitions”` for compatibility, and add candidate-level records for `priority_errors`, `provably_shadowed_candidates`, and `possibly_shadowed_candidates`. These exact additive field names are recommended under the report-field discretion. `is_deterministic` must be false only for malformed priority topology, not for a valid multi-target group. [VERIFIED: src/fast_fsm/validation.py:396-424; .planning/ROADMAP.md:128-133]

For each group, the first earlier edge marked statically unconditional proves all later edges shadowed. If an earlier edge has no transition guard but lacks the exact-base-state proof, classify lower edges as possible shadows only. Emit candidate identity as source, trigger/event, target, priority, and the shadowing priority so same-target candidates remain distinguishable. Do not call a guard or permission and do not use condition display names as semantics. [VERIFIED: src/fast_fsm/core.py:2449-2591; .planning/phases/24-candidate-aware-diagnostics-output/24-CONTEXT.md:30-38]

`EnhancedFSMValidator._analyze_determinism()` should create error issues for malformed groups, warning issues for proven shadows, and informational issues for possible shadows. Its current advice to “use conditions to make transitions deterministic” is wrong for valid ordered groups and must be replaced with priority-specific guidance. [VERIFIED: src/fast_fsm/validation.py:772-788]

### Pattern 3: Candidate-complete output with one numeric spelling

Use the existing scalar key `“priority”` in JSON and adjacency records; Python's default JSON encoder represents ordinary integers as JSON numbers and preserves ordered container iteration. [VERIFIED: src/fast_fsm/core.py:1401-1410; CITED: https://docs.python.org/3.10/library/json.html] Add the field to:

- `_sparse_adjacency(...)[“edges”]` records;
- `_dense_adjacency(...)[“transitions”]` records and adjacency compatibility validation;
- `to_json(...)[“topology”][“transitions”]` records;
- validation JSON exports and both Markdown transition tables;
- generated path steps as the trailing fourth scalar after source, event, and target.

These current output keys are verbatim from the implementations: `“edges”`, `“transitions”`, `“topology”`, `“trigger”`, `“from”`, `“to”`, `“has_guard”`, `“event”`, `“idx”`, `“from_state”`, and `“to_state”`. [VERIFIED: src/fast_fsm/_diagnostics.py:432-460,468-524; src/fast_fsm/visualization.py:394-472]

For Mermaid and PlantUML, append generated text ` [priority N]` to every transition label after the optional escaped condition label. Priority is a validated integer, so it is not caller-controlled text; trigger and condition labels must still pass through the existing format-specific escape callback. `show_conditions=False` hides only the condition, never priority. [VERIFIED: src/fast_fsm/visualization.py:92-103,151-164,207-220; .planning/phases/24-candidate-aware-diagnostics-output/24-CONTEXT.md:40-47,57-61]

For Markdown adjacency cells, render each transition index as escaped event text plus its numeric priority, and add a `Priority` column to both visualization and validation transition tables. Keep opaque state IDs and all existing Markdown, Mermaid, PlantUML, condition, trigger, and title encoders unchanged. [VERIFIED: src/fast_fsm/visualization.py:47-81,756-842; src/fast_fsm/validation.py:992-1086]

The legacy dense transition matrix currently stores only target-name strings and cannot distinguish two candidates with the same target or expose priority. Because D-03 requires every shown transition to be one priority-bearing record, evolve each populated cell to ordered candidate records containing target and numeric priority, update its public annotation/docstring, and cover the deliberate output-shape evolution. This recommendation follows the locked output contract; it is not a new topology API. [VERIFIED: src/fast_fsm/_diagnostics.py:479-494; src/fast_fsm/validation.py:268-281,307-366; .planning/phases/24-candidate-aware-diagnostics-output/24-CONTEXT.md:40-47]

### Pattern 4: Reserve once for every candidate occurrence

Graph traversal already follows edge indices in `forward`/`reverse`, so preserving one `_DiagnosticEdge` per snapshot candidate naturally charges reachability, SCC, depth, adjacency, and path expansion once per candidate edge. [VERIFIED: src/fast_fsm/_diagnostics.py:207-220,224-424,432-574] Add missing explicit reservations where candidate rows are newly emitted: determinism/group inspection, JSON transition records, validation/report transition rows, and any new shadow/error records. Reserve before appending or formatting, matching the existing ledger discipline. [VERIFIED: src/fast_fsm/_diagnostics.py:104-191; .specify/decisions/ADR-006-bounded-diagnostics-safe-output.md:32-37]

Do not deduplicate edges by target in diagnostic algorithms. Deduplication remains correct only for event-name catalogs and SCC condensation arcs, because those are derived structural sets rather than candidate outputs; both loops must still reserve work for each input edge before deduplication. [VERIFIED: src/fast_fsm/_diagnostics.py:364-385,427-429]

Retain the existing exhaustion boundary: reserve-before-work updates `DiagnosticStatus`; fixed-shape legacy output raises the fixed message `“diagnostic budget exhausted”` rather than returning partial data that looks complete. The exact status fields are verbatim: `“complete”, “exhausted_dimension”, “exhausted_stage”, “work_count”, “result_count”, “dense_cell_count”, “path_expansion_count”`. [VERIFIED: src/fast_fsm/_diagnostics.py:57-77,104-191; tests/test_diagnostic_contracts.py:246-284]

### Anti-Patterns to Avoid

- **Reading `fsm._transitions` from validation or renderers:** this violates the one-snapshot contract and teaches every tool the private storage union. [VERIFIED: tests/test_diagnostic_contracts.py:305-312; .planning/phases/24-candidate-aware-diagnostics-output/24-CONTEXT.md:21-28]
- **Using `FSMValidator.transitions` sets for candidate counts or determinism:** same-target candidates collapse and target count is no longer the definition of determinism. [VERIFIED: src/fast_fsm/validation.py:153-173,319-324,396-424]
- **Sorting diagnostic candidates during output:** order is already canonical; another sort can hide malformed snapshot order and adds unnecessary work. [VERIFIED: src/fast_fsm/core.py:1534-1555; tests/test_graph_invariants.py:95-139]
- **Evaluating `Condition.check()` or `State.can_transition()` during diagnostics:** analysis would gain side effects, telemetry dependence, exceptions, and sync/async divergence. [VERIFIED: src/fast_fsm/core.py:2449-2591,4291-4396]
- **Hiding priority when `show_conditions=False`:** condition visibility is optional; candidate precedence is mandatory output identity. [VERIFIED: .planning/phases/24-candidate-aware-diagnostics-output/24-CONTEXT.md:40-47]
- **Charging one budget unit per source/trigger group:** a finite group of size `k` must consume `k` edge/result/path operations where applicable. [VERIFIED: .planning/phases/24-candidate-aware-diagnostics-output/24-CONTEXT.md:49-55]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Candidate topology projection | A renderer-specific group flattener | `_graph_snapshot()` → `_graph_from_snapshot()` | The existing capture is immutable, owner-aware, deterministic, and already candidate-complete. [VERIFIED: src/fast_fsm/core.py:1513-1566; src/fast_fsm/_diagnostics.py:194-221] |
| Safety limits | Per-renderer counters or timeouts | `_DiagnosticBudget` and `DiagnosticStatus` | The shared reserve-before-work ledger already defines deterministic exhaustion semantics. [VERIFIED: src/fast_fsm/_diagnostics.py:31-77,104-191] |
| Graph algorithms | New recursive DFS or `networkx` runtime dependency | Existing iterative reachability, SCC, depth, adjacency, and path helpers | The helpers are already bounded and keep diagnostics out of the core runtime dependency set. [VERIFIED: src/fast_fsm/_diagnostics.py:224-574; pyproject.toml:7-9,27-32] |
| Output sanitization | One generic sanitizer | Existing `_escape_mermaid_text`, `_escape_plantuml_text`, and Markdown encoders | Context-specific output encoding prevents caller text from changing the target grammar. [VERIFIED: src/fast_fsm/visualization.py:42-81; CITED: https://cornucopia.owasp.org/taxonomy/asvs-5.0/01-encoding-and-sanitization/02-injection-prevention] |
| Shadow certainty | Guard execution, name heuristics, or callable inspection | Snapshot-captured static unconditional fact | Only a frozen fact can support deterministic, side-effect-free diagnostics. [VERIFIED: .planning/phases/24-candidate-aware-diagnostics-output/24-CONTEXT.md:30-38] |

**Key insight:** this phase is a metadata propagation and diagnostic-semantics change. The existing snapshot, graph traversal, encoders, and budget ledger are the hard parts; preserve them and remove only singular/collapsing assumptions. [VERIFIED: .planning/phases/24-candidate-aware-diagnostics-output/24-CONTEXT.md:110-134]

## Common Pitfalls

### Pitfall 1: Valid ordered candidates are reported as non-deterministic
**What goes wrong:** two targets under one state/event make `check_determinism()` fail even though unique priorities fully order evaluation. [VERIFIED: src/fast_fsm/validation.py:396-424]
**Why it happens:** the current implementation measures target-set cardinality, a pre-priority model. [VERIFIED: src/fast_fsm/validation.py:411-419]
**How to avoid:** validate exact increasing priority per source/trigger group and treat target multiplicity as ordinary candidate topology. [VERIFIED: .planning/phases/24-candidate-aware-diagnostics-output/24-CONTEXT.md:30-38]
**Warning signs:** a valid two-priority group yields `is_deterministic=False` or an Enhanced validator recommendation to add conditions.

### Pitfall 2: Same-target candidates disappear
**What goes wrong:** sets or source/trigger maps collapse two candidate edges that differ only by priority/guard. [VERIFIED: src/fast_fsm/validation.py:153-173]
**Why it happens:** destination names were formerly sufficient edge identity.
**How to avoid:** use `graph.edges` and transition indices for counts, metrics, paths, tables, and output; keep legacy sets only for old membership adapters. [VERIFIED: src/fast_fsm/_diagnostics.py:90-102,207-220]
**Warning signs:** `actual_transitions < len(graph.edges)`, repeated targets produce one row, or a path loses priority.

### Pitfall 3: An “unconditional” label becomes false proof
**What goes wrong:** validation claims a lower candidate is unreachable because an earlier edge lacks a transition condition, ignoring custom state permission or a declarative guard. [VERIFIED: src/fast_fsm/core.py:2510-2591]
**Why it happens:** candidate eligibility has three ordered stages, not one. [VERIFIED: src/fast_fsm/core.py:2428-2591]
**How to avoid:** prove only the exact base-`State`, no-transition-guard case; classify other unguarded higher candidates as possible shadowing.
**Warning signs:** diagnostics invoke user code, inspect condition names, or call every unguarded candidate definitely shadowing.

### Pitfall 4: Output exposes priority in one surface but not another
**What goes wrong:** JSON is correct while diagrams, adjacency rows, Markdown cells, validation exports, or paths remain ambiguous. [VERIFIED: src/fast_fsm/_diagnostics.py:432-574; src/fast_fsm/visualization.py:394-472,578-842; src/fast_fsm/validation.py:949-1086]
**How to avoid:** test one same-source/same-trigger/same-target fixture across every named output and assert the exact ordered priority sequence.
**Warning signs:** any transition representation has no numeric priority or output cardinality differs from `snapshot.transitions`.

### Pitfall 5: Candidate output bypasses result budgets
**What goes wrong:** a large group produces thousands of lines/records while counting one group or only traversal work.
**Why it happens:** renderer loops append rows without reserving a result, or validation counts state/event cells rather than candidates. [VERIFIED: src/fast_fsm/validation.py:396-419; src/fast_fsm/visualization.py:427-437]
**How to avoid:** reserve before every candidate inspection and emitted candidate row; exact-limit and one-less tests must name the exhausted stage. [VERIFIED: tests/test_diagnostic_contracts.py:163-186,383-449]
**Warning signs:** doubling group size leaves counters unchanged or a one-less limit returns partial output.

### Pitfall 6: Native parity is assumed because diagnostics are interpreted
**What goes wrong:** the interpreted consumer works in pure mode but the extended `_GraphTransition` layout or constructor fails under compiled `core.py`. [VERIFIED: setup.py:16-39; tests/test_mypyc_guard.py:384-482]
**How to avoid:** update the exact AST field guard, build a fresh native core, run the same snapshot→validation→output probe in pure and native modes, then restore a clean source origin. [VERIFIED: .github/copilot-instructions.md:68-76,310-338]
**Warning signs:** fields differ by mode, stale `.so` shadows source, or slots-policy gains a new exception.

## Code Examples

### Candidate-complete scalar projection

```python
# Existing source pattern: src/fast_fsm/_diagnostics.py:194-221.
# Recommended private fields are added under Phase 24's discretion.
edges = tuple(
    _DiagnosticEdge(
        from_index=state_indices[row.from_state_name],
        trigger=row.trigger,
        to_index=state_indices[row.to_state_name],
        condition_name=row.condition_name,
        priority=row.priority,
        statically_unconditional=row.statically_unconditional,
    )
    for row in snapshot.transitions
)
```

The existing source values `“from_state_name”, “trigger”, “to_state_name”, “condition_name”, “priority”` are quoted verbatim from `_GraphTransition`; `statically_unconditional` is the recommended new private spelling, not an asserted current value. [VERIFIED: src/fast_fsm/core.py:691-703]

### Strict-priority group validation

```python
# Pseudocode: one pass over already ordered graph edges.
for group in candidate_groups:
    previous_priority = None
    for edge in group:
        budget.reserve_work(stage="determinism.candidate")
        if type(edge.priority) is not int or (
            previous_priority is not None and edge.priority <= previous_priority
        ):
            record_priority_error(edge)
        previous_priority = edge.priority
```

The exact-int boundary and ascending storage rule already exist in core; diagnostics defensively verifies the snapshot instead of sorting or normalizing it. [VERIFIED: src/fast_fsm/core.py:684-688,1715-1736]

### Diagram label contract

```python
label = escape(trigger)
if show_conditions and condition_name is not None:
    label = f"{label} [{escape(condition_name)}]"
label = f"{label} [priority {priority}]"
```

The first two operations are the existing final-sink pattern. The trailing generated numeric label is the recommended punctuation under D-03 discretion and must appear even when conditions are hidden. [VERIFIED: src/fast_fsm/visualization.py:92-103; .planning/phases/24-candidate-aware-diagnostics-output/24-CONTEXT.md:40-47,57-61]

## State of the Art

| Current singular assumption | Phase 24 contract | Impact |
|-----------------------------|-------------------|--------|
| `_DiagnosticEdge` drops priority | Carry priority and static eligibility evidence on every scalar edge | All consumers share one truthful candidate identity. [VERIFIED: src/fast_fsm/_diagnostics.py:80-102,194-221] |
| Determinism means at most one distinct target per state/event | Determinism means exact strictly increasing priority order | Valid priority overlap is accepted; malformed ties/order are correctness errors. [VERIFIED: src/fast_fsm/validation.py:396-424; .planning/REQUIREMENTS.md:59-61] |
| Legacy target sets drive counts/metrics | `len(graph.edges)` and indexed edge iteration drive candidate counts | Same-target candidates remain visible and budgeted. [VERIFIED: src/fast_fsm/validation.py:153-173,319-324,653-681] |
| Diagrams and JSON show trigger/guard only | Every edge also shows numeric priority | Readers can reconstruct precedence without knowing registration order. [VERIFIED: src/fast_fsm/visualization.py:92-103,394-472] |
| Paths are `(from, event, to)` triples | Paths append numeric priority per step | Repeated same-target candidate paths remain auditable. [VERIFIED: src/fast_fsm/_diagnostics.py:527-574; .planning/REQUIREMENTS.md:63-65] |
| Adjacency transition rows omit priority | Sparse/dense rows and Markdown cells/tables include priority | Matrix indices continue to identify one candidate each. [VERIFIED: src/fast_fsm/_diagnostics.py:432-524; src/fast_fsm/visualization.py:578-842] |

**Deprecated/outdated:** the `check_determinism()` docstring phrase `“at most one transition per state-event pair”`, the target-only transition-matrix schema, and path triple documentation are inconsistent with DIAG-01/02 and must be updated with their tests and living SPR. [VERIFIED: src/fast_fsm/validation.py:396-404,268-305,369-386; .planning/REQUIREMENTS.md:59-65]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| — | None. Proposed private/report field names, label punctuation, exact-base-state proof, and candidate-record cell shape are prescriptive choices made under the explicit agent-discretion grant, not claims about current behavior. | — | — |

## Open Questions

None blocking. D-01 through D-04 settle the projection, ordering, visibility, and budget policies. The recommended exact-base-`State` shadow proof deliberately leaves additional true-but-unprovable cases classified as possible; expanding proof later would require a new trusted static condition/permission contract. [VERIFIED: .planning/phases/24-candidate-aware-diagnostics-output/24-CONTEXT.md:21-63]

## Environment Availability

Step 2.6 skipped: Phase 24 is a code/config-only change with no external service or new dependency. The existing `uv`, pytest, Ruff, mypy, ty, and Task toolchain is available through the repository environment; the current pure-source preflight and focused diagnostic baseline passed. [VERIFIED: local tool and focused test runs, 2026-09-07]

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest `8.4.1`, sequential, pytest-asyncio auto mode [VERIFIED: pyproject.toml:56-74; local version check] |
| Config file | `pyproject.toml` [VERIFIED: pyproject.toml:56-74] |
| Quick run command | `FAST_FSM_BUILD_MODE=pure UV_CACHE_DIR=/private/tmp/fast-fsm-phase23-uv-cache uv run --offline pytest tests/test_validation.py tests/test_visualization.py tests/test_diagnostic_contracts.py tests/test_graph_invariants.py -x -q` [VERIFIED: focused baseline passed, 2026-09-07] |
| Full suite command | `uv run pytest tests/ -x -q` [VERIFIED: .github/copilot-instructions.md:60-66,229-238] |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DIAG-01 | Strict groups accepted; duplicate, descending, Boolean, and non-integer priorities rejected; same-target groups retained | unit/integration | `uv run pytest tests/test_validation.py tests/test_graph_invariants.py -k 'priority or candidate or determinism or shadow' -x -q` | ✅ existing files; add cases |
| DIAG-01 | Exact-base unguarded winner proves lower shadows; custom/declarative permission produces possible observation; no guard/permission called | unit | `uv run pytest tests/test_validation.py -k 'shadow or unconditional' -x -q` | ✅ existing file; add cases |
| DIAG-02 | Sparse/dense adjacency and generated paths emit every candidate with ordered priority | unit | `uv run pytest tests/test_diagnostic_contracts.py tests/test_validation.py -k 'priority or candidate or adjacency or path or budget' -x -q` | ✅ existing files; add cases |
| DIAG-02 | JSON/Mermaid/PlantUML/Markdown expose numeric priority, multiplicity, escaping, and one snapshot | integration/golden | `uv run pytest tests/test_visualization.py tests/test_diagnostic_contracts.py -k 'priority or candidate or escape or snapshot or budget' -x -q` | ✅ existing files; add cases |
| DIAG-01/02 | Frozen/slotted snapshot layout and pure/native result equivalence | static/build/integration | `uv run pytest tests/test_mypyc_guard.py tests/test_graph_invariants.py tests/test_validation.py tests/test_visualization.py -k 'graph or diagnostic or priority or candidate' -x -q` after fresh compiled build | ✅ existing files; add probes |

### Sampling Rate

- **Per task commit:** run the directly modified focused file(s) with pure-source mode. [VERIFIED: .github/copilot-instructions.md:60-66,229-238]
- **Per wave merge:** run the four-file focused diagnostic suite after `task pure-source-check`. [VERIFIED: tests/test_diagnostic_contracts.py:305-312,743-827]
- **Phase gate:** Ruff, mypy, ty, slots-policy, full pure suite, fresh compiled build/import, focused native diagnostic probe, then restore and recheck pure-source origin. [VERIFIED: .github/copilot-instructions.md:68-76,211-226,310-338]

### Wave 0 Gaps

No framework/config/fixture file is missing. Add requirement cases to the existing files rather than creating `tests/test_diagnostic_budgets.py`: candidate fixture and malformed-snapshot validation in `test_validation.py`; exact edge/result/path budget boundaries in `test_diagnostic_contracts.py`; cross-format escaped goldens in `test_visualization.py`; snapshot order/static fact in `test_graph_invariants.py`; and compiled-layout/native parity in `test_mypyc_guard.py`. [VERIFIED: repository test inventory; .github/copilot-instructions.md:240-256]

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | No authentication boundary in an in-process FSM diagnostic library. [VERIFIED: phase scope in .planning/phases/24-candidate-aware-diagnostics-output/24-CONTEXT.md:6-14] |
| V3 Session Management | no | No session state or credential lifecycle in scope. [VERIFIED: phase scope in .planning/phases/24-candidate-aware-diagnostics-output/24-CONTEXT.md:6-14] |
| V4 Access Control | no | Diagnostics read a caller-supplied machine snapshot; no authorization surface is introduced. [VERIFIED: src/fast_fsm/validation.py:118-164; src/fast_fsm/visualization.py:84-89] |
| V5 Input Validation / encoding | yes | Keep exact integer priority validation, immutable snapshots, fixed adjacency mismatch errors, and format-specific final-sink encoding. [VERIFIED: src/fast_fsm/core.py:684-688; src/fast_fsm/visualization.py:42-81,573-641; CITED: https://cornucopia.owasp.org/taxonomy/asvs-5.0/01-encoding-and-sanitization/02-injection-prevention] |
| V6 Cryptography | no | No cryptographic operation or secret storage in scope. [VERIFIED: phase scope in .planning/phases/24-candidate-aware-diagnostics-output/24-CONTEXT.md:6-14] |

### Known Threat Patterns for Snapshot Diagnostics

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Caller-controlled state/trigger/condition/title changes Mermaid, PlantUML, Markdown, or JSON structure | Tampering / Information disclosure | Existing grammar-specific final-sink encoders and JSON-native scalar mappings; never interpolate raw labels into syntax. [VERIFIED: src/fast_fsm/visualization.py:42-81,92-103; CITED: https://cornucopia.owasp.org/taxonomy/asvs-5.0/01-encoding-and-sanitization/02-injection-prevention] |
| Large candidate group evades limits through source/trigger collapse | Denial of service | Preserve one edge per candidate and reserve work/results/path expansions before each candidate operation. [VERIFIED: src/fast_fsm/_diagnostics.py:104-191; .planning/phases/24-candidate-aware-diagnostics-output/24-CONTEXT.md:49-55] |
| Concurrent mutation yields internally inconsistent report | Tampering | Exactly one owner-aware immutable graph snapshot per top-level operation. [VERIFIED: src/fast_fsm/core.py:1513-1532; tests/test_diagnostic_contracts.py:219-243,812-827] |
| Guard/state policy executes during static analysis | Tampering / Denial of service | Snapshot-captured scalar facts only; never call conditions or permissions from diagnostics. [VERIFIED: .planning/phases/24-candidate-aware-diagnostics-output/24-CONTEXT.md:30-38] |
| Stale caller adjacency is rendered against another snapshot | Tampering | Full positional/field/cell equality check and one fixed non-leaking mismatch error, extended to include priority. [VERIFIED: src/fast_fsm/visualization.py:573-641] |

## Sources

### Primary (HIGH confidence)

- `src/fast_fsm/core.py` — candidate records, exact priority boundary, snapshot capture, sync/async eligibility stages. [VERIFIED: src/fast_fsm/core.py:611-765,1513-1566,2351-2591]
- `src/fast_fsm/_diagnostics.py` — scalar graph, budget ledger, traversal, adjacency, and paths. [VERIFIED: src/fast_fsm/_diagnostics.py:31-221,224-574]
- `src/fast_fsm/validation.py` — legacy adapters, determinism, metrics, reports, and exports. [VERIFIED: src/fast_fsm/validation.py:99-424,541-1086]
- `src/fast_fsm/visualization.py` — one-capture renderers, escaping, JSON, adjacency validation, and Markdown. [VERIFIED: src/fast_fsm/visualization.py:42-103,114-330,394-496,573-842]
- Phase 24 context, roadmap, requirements, ADR-006, ADR-007, and verified Phase 23 boundary. [VERIFIED: .planning/phases/24-candidate-aware-diagnostics-output/24-CONTEXT.md:6-151; .planning/ROADMAP.md:123-133; .planning/REQUIREMENTS.md:57-65; .specify/decisions/ADR-006-bounded-diagnostics-safe-output.md:21-72; .specify/decisions/ADR-007-priority-topology.md:20-39; .planning/phases/23-construction-declarative-serialization-parity/23-VERIFICATION.md:19-44]

### Secondary (MEDIUM confidence)

- Python 3.10 `json` documentation — default scalar/container encoding and order preservation. [CITED: https://docs.python.org/3.10/library/json.html]
- OWASP ASVS 5.0.0 encoding/injection prevention — context-specific output encoding. [CITED: https://cornucopia.owasp.org/taxonomy/asvs-5.0/01-encoding-and-sanitization/02-injection-prevention]

### Tertiary (LOW confidence)

- None.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — versions and compilation boundaries are read from repository configuration and local tools. [VERIFIED: pyproject.toml:1-74; setup.py:16-39]
- Architecture: HIGH — every recommended change follows a directly traced snapshot→diagnostic graph→consumer seam and locked phase decisions. [VERIFIED: src/fast_fsm/core.py:1513-1566; src/fast_fsm/_diagnostics.py:194-221; .planning/phases/24-candidate-aware-diagnostics-output/24-CONTEXT.md:21-63]
- Pitfalls: HIGH — collapse, missing priority, determinism, and budget gaps are visible in active code and tests. [VERIFIED: src/fast_fsm/validation.py:153-173,319-324,396-424; src/fast_fsm/visualization.py:92-103,427-437]

**Research date:** 2026-09-06
**Valid until:** 2026-10-06 (stable in-repository phase contract)
