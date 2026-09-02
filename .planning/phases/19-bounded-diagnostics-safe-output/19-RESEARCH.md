# Phase 19: Bounded Diagnostics & Safe Output - Research

**Researched:** 2026-09-02
**Domain:** Deterministic graph diagnostics, grammar-safe serialization, and ownership-safe Python logging
**Confidence:** HIGH for repository behavior and graph algorithms; MEDIUM for renderer grammar details verified from official documentation

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

## Implementation Decisions

### Snapshot Identity and Batch Results

- **D-01:** Every top-level validation, comparison, JSON-analysis, and diagram call captures exactly one immutable internal graph snapshot and passes that snapshot through all nested analysis/rendering. No nested helper may reread `_states`, `_transitions`, current runtime state, or graph version independently.
- **D-02:** Reachability always starts from the snapshot's declared initial state. The current runtime state may be reported separately, but it never substitutes for the initial state in structural analysis.
- **D-03:** Batch and comparison results preserve input cardinality and order with stable positional identities even when machine display names are duplicated. Names remain labels, not dictionary keys. — **Reversibility:** costly — changing identity after publishing the Phase 19 comparison schema would require downstream result consumers to migrate.
- **D-04:** Comparing zero machines succeeds with a documented empty structured result: empty entries/rankings, no best machine, and aggregate counts of zero. Undefined numeric aggregates are represented explicitly as `None`, never invented as zero and never computed by division.

### Deterministic Budgets and Graph Semantics

- **D-05:** Potentially expanding diagnostic work has a finite deterministic default budget based on counted graph operations/results, not wall-clock time. Public top-level diagnostic APIs accept additive keyword-only limit overrides; exact public helper/type names remain the planner's discretion.
- **D-06:** Structured diagnostic results expose whether analysis is complete, which budget was exhausted, and deterministic work/result counts. APIs whose established return type cannot safely carry partial metadata fail with one documented redacted diagnostic-budget exception; no API silently returns partial output. — **Reversibility:** costly — callers will rely on the complete/incomplete contract and stable failure boundary.
- **D-07:** Cycle membership is defined by strongly connected components: every state in every cyclic SCC is reported, including self-loops and cycles longer than two states. Output is deterministic and deduplicated; representative cycle paths may be additional evidence but are not the membership oracle.
- **D-08:** Longest-path diagnostics use memoized dynamic programming on a DAG. Cyclic graphs are condensed to an SCC DAG and report structural depth plus the interpretation used; the library does not promise the NP-hard exact longest simple path through a cyclic graph.
- **D-09:** Sparse adjacency/edge data is the default analysis representation. Dense N×N matrices remain an explicit compatibility/opt-in output and must be budget-checked before allocation. Generated test paths are separately bounded by both path count and expansion work.
- **D-10:** Budget defaults must complete ordinary existing test/doc examples while remaining small enough to make adversarial generated graphs deterministic in CI. Tests use exact counted-work boundaries, never timing sleeps or machine-speed assumptions.

### Collision-Free, Grammar-Safe Output

- **D-11:** Mermaid and PlantUML assign deterministic opaque node identifiers (for example, snapshot-order IDs) independently of labels. Distinct state names can never collide merely because punctuation sanitizes to the same text.
- **D-12:** Labels, triggers, conditions, titles, Unicode, newlines/control characters, quotes, brackets, comment markers, and directive-like text pass through separate Mermaid- and PlantUML-specific escaping functions. User text is always inert data and never emitted into identifier, directive, comment, or fence syntax unescaped. — **Reversibility:** costly — rendered text is a user-visible output contract and downstream snapshots may depend on deterministic encoding.
- **D-13:** Diagram and JSON ordering follows the immutable snapshot's deterministic ordering. Repeated calls on the same snapshot are byte-stable; live graph changes can affect only a subsequently captured snapshot.

### Redacted and Reversible Logging

- **D-14:** Default trace logging is metadata-only: fixed operation/stage/result categories, positional argument count, and sanitized keyword names may be emitted; trigger names, state names, positional values, keyword values, exception payloads, and object representations are redacted by default.
- **D-15:** Applications may provide an explicit redactor that receives the minimum structured event needed to produce safe logging fields. Redactor failure is fail-closed: emit a fixed redaction-failure category or suppress the event, and never fall back to raw values.
- **D-16:** `configure_fsm_logging()` never clears or mutates application-owned handlers. Library-created handlers are explicitly identifiable, repeated configuration replaces only library-owned configuration, propagation is deliberate and caller-selectable, and the call returns or exposes a reversible library-owned configuration handle that restores only library changes. — **Reversibility:** costly — application logging ownership and restoration become part of the public safety contract.
- **D-17:** `set_fsm_logging_level()` delegates to the same ownership-preserving configuration seam; no alternate helper may reintroduce handler clearing or raw trace formatting.

### Agent's Discretion

- Exact names and slot-backed shapes for private snapshot consumers, budget counters, structured analysis records, and reversible logging handles.
- Exact deterministic default limit values after adversarial tests calibrate them, provided limits are documented and do not depend on elapsed time.
- Whether legacy list/scalar helpers gain additive sibling APIs or keyword-only options, provided compatibility is preserved and exhaustion is never silent.
- Internal SCC implementation and grammar-escape tables, provided they are dependency-free, deterministic, and covered by hostile-input tests.

### Deferred Ideas (OUT OF SCOPE)

- A public versioned topology snapshot serialization contract remains FUTR-05.
- Installed wheel/sdist pure/native parity and final release publication evidence remain Phase 20.
- New graph query/product features, interactive diagram tooling, logging backends, and scheduler/offload behavior remain outside this milestone.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DIAG-01 | Validation always performs reachability from the machine's declared initial state, regardless of its current runtime state. | Snapshot projection carries an immutable `initial_state_name`; every reachability entry point consumes it. |
| DIAG-02 | Batch validation and FSM comparison preserve every input when machine names are duplicated. | Position-indexed entry records replace name-keyed maps. |
| DIAG-03 | Comparing zero FSMs returns a documented empty result or explicit validation error instead of dividing by zero. | Exact empty comparison schema is specified below. |
| DIAG-04 | Cycle analysis reports every state in each cycle, including all members of cycles longer than two states. | Iterative SCC analysis is the membership oracle. |
| DIAG-05 | Longest-path analysis uses a bounded or memoized graph algorithm rather than enumerating exponentially many acyclic paths. | DAG memoization and condensation-DAG semantics are specified below. |
| DIAG-06 | Diagnostic APIs can avoid unconditional dense N×N allocation and unbounded path expansion for sparse or generated graphs. | Sparse-first projection, dense preflight, and bounded iterative path generation are specified below. |
| DIAG-07 | When a deterministic analysis budget is exceeded, the caller receives explicit incomplete-result metadata or a documented error rather than silent partial output. | A shared counted-work ledger and fail-closed exception boundary are specified below. |
| DIAG-08 | Validation, comparison, JSON analysis, and visualization consume the stable graph snapshot instead of coupling independently to mutable private dictionaries. | Top-level capture/private `*_from_snapshot` layering is specified below. |
| OUT-01 | Mermaid output assigns collision-free opaque identifiers when distinct state names sanitize to the same text. | Snapshot-order IDs (`s0`, `s1`, …) are independent of labels. |
| OUT-02 | Mermaid and PlantUML state names, triggers, titles, Unicode, control text, and punctuation are escaped according to each target grammar. | Two allowlist encoders and hostile grammar fixtures are specified below. |
| OUT-03 | Trace logging redacts trigger values by default and cannot expose raw positional or keyword payloads merely because trace mode is enabled. | Trace records carry only fixed categories, argument count, and sanitized key names. |
| OUT-04 | An application can supply an explicit trace redactor when key-only default logging is insufficient. | A minimum-event redactor protocol with fail-closed failure handling is specified below. |
| OUT-05 | `configure_fsm_logging()` preserves application-owned handlers and offers reversible library-owned configuration with deliberate propagation behavior. | Token-marked library handlers and a generation-aware reversible handle are specified below. |
| TEST-07 | Core runtime operations remain O(1), while diagnostic APIs document and enforce their separate complexity and budget contracts. | Complexity table, exact budget-boundary tests, isolated pure/compiled checks, slots audit, and throughput gate are specified below. |
</phase_requirements>

## Summary

Phase 19 should introduce one dependency-free internal diagnostics seam rather than patching each public helper independently. The current private snapshot is frozen and deterministically ordered, but it retains mutable `State`/`Condition` references; diagnostics therefore need stable scalar names captured into the snapshot projection, and snapshot capture itself must serialize with topology writers. The validator currently starts from the current state, comparisons overwrite duplicate names and divide by zero on empty input, cycle logic misses members, longest-path traversal copies visited sets recursively, dense matrices allocate unconditionally in reports, and JSON/renderers reread private dictionaries. These failures are both visible in source and reproduced by an executed repository probe. [VERIFIED: src/fast_fsm/core.py:371-394] [VERIFIED: src/fast_fsm/validation.py:36-69] [VERIFIED: src/fast_fsm/validation.py:1112-1154] [VERIFIED: src/fast_fsm/visualization.py:206-306]

Use an immutable scalar `_DiagnosticGraph` constructed once from `_GraphSnapshot`: snapshot-order state labels and indices, initial index, sorted edge rows, sparse forward/reverse adjacency, and stable condition labels. One mutable slot-backed `_DiagnosticBudget` is passed through all analyses. Iterative reachability plus iterative Kosaraju SCC is linear in vertices plus edges; SCC condensation turns cyclic depth into a linear-time DAG longest-path calculation. Dense outputs preflight every cell before allocation, and path generation counts expansions as well as results. [VERIFIED: src/fast_fsm/validation.py:141-196] [VERIFIED: src/fast_fsm/validation.py:232-262] [VERIFIED: src/fast_fsm/validation.py:688-706]

Output safety needs target-specific encoders, not a generic sanitizer. Mermaid documents support aliases and use `%%` line comments, while PlantUML supports quoted labels/aliases and a preprocessing language with include/import directives. Opaque IDs eliminate collision risk, and strict allowlist encoding keeps all caller text out of directive, comment, identifier, fence, and line structure. Logging must similarly keep raw payloads out of the `LogRecord` entirely and must replace only explicitly marked library handlers. Python's logging documentation assigns handler configuration to applications and provides `addHandler`/`removeHandler` plus deliberate propagation; the current `handlers.clear()` violates that ownership boundary. [CITED: https://mermaid.js.org/syntax/stateDiagram.html] [CITED: https://plantuml.com/state-diagram] [CITED: https://plantuml.com/preprocessing] [CITED: https://docs.python.org/3/howto/logging.html]

**Primary recommendation:** Build and test the shared snapshot/budget/graph seam first, migrate all validators and serializers to private from-snapshot entry points second, then harden grammar encoders and reversible trace logging before running the pure/compiled and performance gates.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Atomic topology capture | Core runtime boundary | Diagnostics | Only `StateMachine` can serialize a view with graph mutations; consumers receive data and never inspect live dictionaries. [VERIFIED: src/fast_fsm/core.py:1015-1047] |
| Sparse projection, budgets, SCC, depth, paths | Interpreted diagnostics module | Validation/JSON adapters | Keeps traversal off the compiled trigger path while giving all consumers identical semantics. [VERIFIED: setup.py:16-39] |
| Comparison and report schemas | Validation API | Diagnostics | Positional identity and completion metadata are API concerns built from the shared graph result. |
| Mermaid/PlantUML/Markdown encoding | Visualization adapter | Diagnostics | Renderer grammar owns contextual encoding; graph identity/order comes from the shared projection. |
| Trace event capture | Compiled core boundary | Logging configuration | The trigger boundary knows argument shape, while the logging seam must discard raw values before creating a record. [VERIFIED: setup.py:16-39] |
| Handler lifecycle | Standard-library logging adapter | Application | Library code may manage only its marked handler and reversible changes; application handlers remain untouched. [CITED: https://docs.python.org/3/library/logging.html] |

## Project Constraints (from AGENTS.md)

- Use `bd` with `--json` for all issue tracking and do not create Markdown TODO trackers. This research task creates no issue. [VERIFIED: AGENTS.md:13-66]
- Use `uv` for Python commands. The authoritative full suite is sequential: `uv run pytest tests/ -x -q`. [VERIFIED: .github/copilot-instructions.md:36-60]
- Compiled `trigger()` must remain at least 200,000 operations/second, and `trigger()`, `can_trigger()`, `add_state()`, and `add_transition()` remain O(1). [VERIFIED: .github/copilot-instructions.md:40-48] The verbatim threshold is `200000` in the evidence manifest. [VERIFIED: evidence/release-baseline.json:39-55]
- Hot-path production classes use `__slots__`; run the recursive slots-policy audit. [VERIFIED: .github/copilot-instructions.md:40-45]
- Preserve public symbols; constructor changes are forbidden and additive options should be keyword-only or sibling APIs. [VERIFIED: .github/copilot-instructions.md:50-53]
- Mypy is blocking, ty is independently visible advisory feedback, and Ruff runs format/fix then validation. [VERIFIED: .github/copilot-instructions.md:206-221]
- `validation.py` is optional design-time analysis and must add no runtime work when unused. Only `src/fast_fsm/core.py` is mypyc-compiled; condition modules remain interpreted/subclassable. [VERIFIED: .github/copilot-instructions.md:305-330] [VERIFIED: setup.py:16-39]
- Public API or significant behavior changes require docs, SPR updates, and an ADR for lasting cross-module/public design. [VERIFIED: .github/copilot-instructions.md:254-302] [VERIFIED: .github/copilot-instructions.md:333-382]
- The parent task explicitly limits this research run to this file and forbids committing; implementation must later follow the repository landing workflow.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python standard library | `>=3.10` | `dataclasses`, `collections`, `logging`, iterative graph structures | The package already targets Python `>=3.10`; no new runtime dependency is needed. [VERIFIED: pyproject.toml:1-9] |
| Existing `_GraphSnapshot` | private Phase 16 contract | Canonical graph capture | It already carries declared initial identity, graph version, sorted states, and sorted transitions. The exact existing fields are `"name"`, `"initial_state"`, `"graph_version"`, `"states"`, and `"transitions"`. [VERIFIED: src/fast_fsm/core.py:381-394] |
| `logging` | standard library | Level checks, propagation, handlers, formatters | Existing public helpers already use it; official guidance defines logger/handler ownership and propagation. [VERIFIED: src/fast_fsm/core.py:4573-4655] [CITED: https://docs.python.org/3/library/logging.html] |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | `>=8.4.1` | Exact budget boundaries, hostile text, schemas, concurrency probes | All Phase 19 behavior tests. [VERIFIED: pyproject.toml:11-20] |
| Hypothesis | `>=6.136.6` | Generated sparse graphs and hostile strings | Cross-check deterministic invariants and encoding, with fixed settings/examples for budget boundary assertions. [VERIFIED: pyproject.toml:11-20] |
| Ruff / mypy / ty | repository-pinned ranges | Formatting and type compatibility | Every changed Python file; mypy is the mypyc compatibility authority. [VERIFIED: pyproject.toml:11-20] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Iterative Kosaraju SCC | Iterative Tarjan SCC | Both are O(V+E); Kosaraju is easier to audit with already-required reverse adjacency, while Tarjan saves one graph pass. The recommendation is a design choice, not a new dependency. [ASSUMED] |
| Internal `_diagnostics.py` | Duplicate private helpers in validation and visualization | Duplication would risk semantic drift and violate the one shared analysis seam from CONTEXT.md. |
| Strict allowlist encoders | Regex replacement sanitizer | Replacement cannot prove grammar safety and already collides (`"a-b"` and `"a_b"` both become `"a_b"`). [VERIFIED: src/fast_fsm/visualization.py:28-30] |

**Installation:** no packages. Phase 19 must not add a runtime dependency. [VERIFIED: pyproject.toml:1-9]

## Architecture Patterns

### System Architecture Diagram

```text
top-level API call
      |
      v
StateMachine._graph_snapshot() -- exactly once --> immutable scalar projection
                                                   |
                                                   v
                                   _DiagnosticGraph + _DiagnosticBudget
                                      /          |           \
                                     v           v            v
                            validation       JSON schema    diagram renderer
                         SCC/reach/depth      + status       opaque IDs +
                         sparse/dense/path                   grammar encoder
                                     \           |            /
                                      +----------+-----------+
                                                 |
                              complete result OR redacted budget exception

trigger/trigger_async -- trace-level guard --> minimum trace event --> redactor
                                                              |
                                                              v
                                      sanitized LogRecord --> app + library handlers
```

### Recommended Project Structure

```text
src/fast_fsm/
├── core.py                 # synchronized stable snapshot fields; trace seam; logging handle
├── _diagnostics.py         # NEW interpreted sparse graph, budget, SCC, depth, path primitives
├── validation.py           # public validators/reports/comparison adapters
├── visualization.py        # public JSON/Mermaid/PlantUML/Markdown adapters and encoders
└── __init__.py             # re-export only intentionally public types/exceptions
tests/
├── test_diagnostic_contracts.py   # NEW snapshot, duplicate/empty, budgets, SCC, depth, sparse
├── test_output_safety.py          # NEW hostile Mermaid/PlantUML/JSON/Markdown cases
├── test_logging_config.py         # ownership, reversal, redactor, payload non-disclosure
├── test_validation.py             # compatibility/schema updates
├── test_visualization.py          # deterministic ordinary output updates
└── test_performance_benchmarks.py # disabled-trace and compiled throughput regression
```

The new module is internal and interpreted. `core.py` must not import `_diagnostics.py`; validation and visualization import it after capture, preserving the one-way compiled-boundary dependency. [VERIFIED: setup.py:16-39]

### Pattern 1: Deeply Stable, Serialized Snapshot

`_GraphSnapshot` is frozen, but its exact existing transition values are object references: `"from_state"`, `"trigger"`, `"to_state"`, and `"condition"`; `State` itself has the writable slot `"name"`. A frozen tuple of mutable referenced objects is not byte-stable for rendering. [VERIFIED: src/fast_fsm/core.py:371-394] [VERIFIED: src/fast_fsm/core.py:420-487]

Prescribe additive private scalar fields such as `initial_state_name`, `state_names`, and per-edge `from_name`, `to_name`, `condition_name`, plus `has_guard`. Derive state labels from the authoritative `_states` registration keys, including an identity-to-key map for initial/target objects, rather than rereading mutable `State.name`; capture condition display text once while the topology ownership primitive is held. Keep existing identity fields so Phase 16 invariants remain valid. Split capture into `_graph_snapshot_owned()` and a wrapper that captures directly if the current thread already owns the machine, otherwise acquires/releases `_sync_ownership_lock`; do not call the public ownership policy seam because a diagnostic invoked from a callback must not self-deadlock or acquire AsyncStateMachine policy. The current ownership fields are exactly `"_sync_ownership_lock"` and `"_sync_owner_thread_id"`. [VERIFIED: src/fast_fsm/core.py:600-626]

Every top-level API follows `snapshot = fsm._graph_snapshot()` once, then calls a private `*_from_snapshot(snapshot, budget, ...)`. `to_mermaid_fenced()` and `to_mermaid_document()` must call a renderer taking the captured snapshot rather than recursively calling public `to_mermaid()`. `to_json()` must build quality/reachability/cycles from that same projection rather than instantiate a validator that recaptures. The current nested public call and multiple direct dictionary reads are visible at lines 206-306 and 348-349. [VERIFIED: src/fast_fsm/visualization.py:206-306] [VERIFIED: src/fast_fsm/visualization.py:309-349]

### Pattern 2: Deterministic Counted-Work Ledger

Use one slot-backed internal counter shared by all nested operations. Recommended dimensions are `work`, `results`, and `dense_cells`; each has a finite non-negative limit, count, and exhausted marker. [ASSUMED] Count before performing the operation or appending/allocating the result: one unit per vertex visit, edge examination, path emission, issue/result emission, and dense cell. Preflight known products (`V*V`, `V*E`) with overflow-safe arithmetic before allocation. This makes `limit == required_count` succeed and `limit == required_count - 1` fail before the forbidden operation. [ASSUMED]

Public structured results should include a common status record: `complete: bool`, `exhausted: str | None`, `work_count: int`, `result_count: int`, and `dense_cell_count: int`. [ASSUMED] A new public `DiagnosticBudgetExceeded(RuntimeError)` should carry only fixed budget category plus numeric limit/count fields; its message must not include state, trigger, condition, machine, exception, or payload text. Legacy list/scalar/string APIs cannot safely attach partial metadata, so they raise it. JSON/dict APIs may return an explicitly incomplete status only if every section is marked incomplete and no field masquerades as complete; default to raising for diagrams and dense matrices because partial syntax/matrices are misleading. [ASSUMED]

Do not freeze numeric defaults in the first task. Build adversarial fixtures, measure exact counted work for ordinary docs/tests, then choose defaults above that maximum with documented headroom and below the generated exhaustion fixture. The locked contract requires calibration, so untested round numbers would be premature. Preserve the existing path defaults `max_length=10` and `max_paths=50` unless tests/documentation justify a compatibility change; the verbatim current values are `10` and `50`. [VERIFIED: src/fast_fsm/validation.py:232-240]

### Pattern 3: Sparse Graph + SCC Condensation

Build state indices from snapshot order, edges in snapshot order, and tuple/list adjacency for both directions. Iterative Kosaraju avoids recursion depth: first compute finish order over forward adjacency; second traverse reverse adjacency in reverse finish order. Sort each component by snapshot index and sort components by their minimum index. A component is cyclic exactly when it has more than one member or its sole member has a self-loop. This yields complete, deterministic, deduplicated cycle membership in O(V+E) time and O(V+E) space. [ASSUMED]

Reachability is one iterative traversal from `initial_index`. Because every considered state is reachable from the initial SCC, “can return to initial” is equivalent to membership in the initial SCC; this replaces the current traversal from every reachable state. [VERIFIED: src/fast_fsm/validation.py:549-584] [ASSUMED]

For depth, deduplicate cross-component edges to form the condensation DAG. Starting at the initial component, process topological order and memoize `depth[c] = max(1 + depth[next])`, with terminal depth zero. Report both `depth` and exact interpretation: `"dag_longest_path"` for an acyclic graph or `"condensation_dag_depth"` when any cyclic SCC exists. Those exact proposed values are not current API values and require an ADR/schema test before publication. [ASSUMED] This is O(V+E); never claim exact longest simple path inside a cyclic SCC.

### Pattern 4: Sparse-First Materialization

The default result contains ordered states, events, and edge records only. Compute total missing transition count from `sum(|events| - outgoing_event_count[state])` without creating every pair. If issue examples are needed, scan the state/event product but emit only up to the result budget. `validate_completeness()` must stop unconditionally embedding `get_transition_matrix()`; it currently does so. [VERIFIED: src/fast_fsm/validation.py:198-230]

Keep `get_transition_matrix()` and `get_adjacency_matrix()` as compatibility outputs, but add keyword-only budget limits and preflight `V*E` or `V*V` before allocating. `to_mermaid_document(..., adjacency_matrix=...)` currently accepts caller-supplied plain data that can be stale and unsafely combines it with a fresh diagram. Preserve the argument but validate its states/edges/version fingerprint against the one captured snapshot or reject it with a fixed `ValueError`; add an internally generated `include_adjacency=True` opt-in that derives the matrix from the same snapshot. [VERIFIED: src/fast_fsm/visualization.py:352-425]

Rewrite path generation as iterative DFS frames over ordered outgoing edges. Enforce all three independent bounds: `max_length`, `max_paths`, and expansion-work budget. Count an expansion before constructing/copying the next path; count a result before append. The current recursion copies a path for every branch and returns a truncation without explaining whether `max_paths` or traversal stopped it. [VERIFIED: src/fast_fsm/validation.py:232-262]

### Pattern 5: Positional Comparison Identity

Publish comparison entries in input order, each with `position`, `name`, `score`, `metrics`, and `issue_count`; rankings contain `position`, `name`, and `score`, sorted by descending score then ascending position. `best_fsm` is the same `{position, name}` identity or `None`. Aggregate shape should include `count`, `avg_score`, `score_range`, and `total_issues`. [ASSUMED]

For zero inputs the exact semantics are: entries/rankings empty, best `None`, `count=0`, `total_issues=0`, and `avg_score=None`, `score_range=None`. These are locked, while the recommended field spellings are planner discretion. For batch validation, return ordered entry records rather than a name-keyed dictionary; optionally provide a `by_name` grouping where each value is a list of positions, never a single overwritten entry. [ASSUMED] Current code keys both validators/results by `fsm.name`, and current tests assert name-indexed dictionaries, so update tests/docs as an intentional pre-production schema migration without removing callable symbols. [VERIFIED: src/fast_fsm/validation.py:1112-1154] [VERIFIED: src/fast_fsm/validation.py:1187-1222] [VERIFIED: tests/test_validation.py:384-410]

### Pattern 6: Opaque IDs and Contextual Encoding

Allocate IDs `s0`, `s1`, … from snapshot state order for both renderers; always emit an alias/label declaration even for “safe” names. IDs never contain caller text. Mermaid state syntax supports alias declarations and `%%` comments, and its official docs describe numeric entity codes for troublesome characters. [CITED: https://mermaid.js.org/syntax/stateDiagram.html] [CITED: https://mermaid.js.org/syntax/flowchart.html]

Use separate encoders:

- Mermaid: allow only ASCII letters, digits, ordinary spaces, and underscore in caller-facing label bodies; encode every other code point to Mermaid decimal entity form, including `%`, `#`, `;`, quotes, backticks, backslash, brackets/braces/angles, colon, newline, carriage return, and all controls. Encode controls as visible escaped data, never a physical source line break. Title text follows the same single-line encoder before it enters a fixed library-owned comment/title line. [ASSUMED]
- PlantUML: allow the same minimal characters and encode every other code point using the documented Unicode escape form. In particular encode `!`, `%`, `'`, `@`, quotes, backslash, colon, brackets, angle brackets, newlines, and controls so `!include`, `!import`, comments, `@enduml`, Creole/URL/image syntax, and preprocessing expressions cannot be emitted raw. [CITED: https://plantuml.com/preprocessing] [CITED: https://plantuml.com/creole]
- Markdown document: separately escape heading and table-cell data (`|`, backtick, backslash, CR/LF, HTML-like text) or reuse a plain-text encoder. Never rely only on the diagram encoder, because the current document writes names/events directly into Markdown. [VERIFIED: src/fast_fsm/visualization.py:388-425]

Test encoders as syntax containment, not merely expected pretty text: no caller-supplied physical newline, fence, directive prefix, comment opener, diagram terminator, or opaque-ID token may appear raw. Also assert ordinary Unicode remains recoverable after target decoding even if its encoded representation changes. [ASSUMED]

### Pattern 7: Payload-Free Trace Records and Reversible Handler Ownership

At the trigger/async-trigger entry point, first call `logger.isEnabledFor(TRACE_LEVEL)`. When false, allocate no trace event, do not enumerate values, and add only the constant-time level check. When true with the default policy, build safe fields directly from fixed operation/stage/result categories, `len(args)`, and sanitized string keyword names; never place raw `args`, `kwargs`, trigger/state strings, exception objects/messages, or reprs in the `LogRecord`. [ASSUMED]

When and only when an application explicitly configures a redactor, construct a separate ephemeral minimum redaction input containing the raw fields needed for that event (for example trigger, source/destination, `args`, and `kwargs`, but only fields applicable to that stage). The redactor returns a mapping of approved scalar logging fields; the raw input itself is never attached to a `LogRecord`. Filter returned keys to safe names and values to bounded scalar types/lengths. On ordinary redactor exception, emit only a fixed `redaction_failure` category (or suppress); on `BaseException`, emit nothing and re-raise so cancellation/interrupt semantics survive. Never attach raw fallback data to `extra`, because application formatters/handlers can expose it. [ASSUMED]

Change `configure_fsm_logging()` additively to return a slot-backed `FSMLoggingHandle`, with keyword-only `propagate` and `redactor` options. Mark every library-created handler with an unforgeable/private ownership token, store the logger plus exact handler and a generation number, and use `logger.addHandler()`/`removeHandler()`. Reconfiguration removes/closes only handlers carrying this library token. It never calls `handlers.clear()`, never edits another handler/formatter/filter, and leaves propagation unchanged unless explicitly supplied. The current helper clears all handlers at line 4612. [VERIFIED: src/fast_fsm/core.py:4573-4619] [CITED: https://docs.python.org/3/library/logging.html]

The handle's idempotent `restore()` removes only its exact still-current library handler and restores level/propagation only when they still equal values set by that generation; this preserves later application changes and makes superseded handles harmless. `set_fsm_logging_level()` returns/delegates to the same handle seam; its current level vocabulary is exactly `"debug"`, `"info"`, `"warning"`, `"error"`, `"critical"`, `"off"`, and `"trace"`. [VERIFIED: src/fast_fsm/core.py:4622-4655]

### Anti-Patterns to Avoid

- **Deeply mutable “immutable” snapshots:** frozen containers that dereference live `State.name` or `Condition.name` can change rendered bytes.
- **Locking through public ownership policy:** this can reject callback-local diagnostics or apply async busy/loop policy to a read; use a reentry-aware internal capture seam.
- **One budget per helper:** nested resets allow aggregate work to exceed the top-level limit; pass one counter.
- **Count after allocation:** an exhausted call has already consumed the resource; reserve first.
- **Wall-clock timeouts:** nondeterministic across CI machines and cannot provide exact boundary tests.
- **DFS back-edge endpoints as cycle membership:** it misses interior states, as current JSON does. [VERIFIED: src/fast_fsm/visualization.py:250-274]
- **Exact simple longest path on cyclic graphs:** it invites exponential/NP-hard behavior; report condensation depth.
- **Default dense reports:** `N*N` empty lists dominate sparse graphs. [VERIFIED: src/fast_fsm/validation.py:185-196]
- **Generic “escape” helper:** Mermaid, PlantUML, and Markdown have different grammars.
- **Catch-all JSON fallback:** current `except Exception: quality = None` hides exhaustion and correctness failures. [VERIFIED: src/fast_fsm/visualization.py:276-304]
- **Raw data in `LogRecord.extra`:** downstream application handlers can print it even if the library formatter does not.
- **Handler inference by class/formatter:** an application may legitimately use the same objects; use explicit identity/ownership.

## Public and Internal Contract Recommendation

The following names are concrete planning recommendations, not existing API facts. [ASSUMED]

| Surface | Recommended contract |
|---------|----------------------|
| `DiagnosticLimits` | Frozen/slot-backed public value with finite `max_work`, `max_results`, `max_dense_cells`; constructor rejects bool, negative, and non-int values. |
| `DiagnosticStatus` | Frozen/slot-backed public value with `complete`, `exhausted`, and exact counters. |
| `DiagnosticBudgetExceeded` | Public redacted exception with fixed category and numeric limit/count only. |
| `_DiagnosticBudget` | One mutable internal ledger created at top level and threaded through nested operations. |
| `_DiagnosticGraph` | Immutable scalar projection with names/indices, initial index, edges, forward/reverse adjacency. |
| `FSMValidator._from_snapshot` | Private factory; public constructor captures once then delegates. |
| `compare_fsms(..., *, limits=None)` | Ordered positional entries; each input captured exactly once; empty succeeds. |
| `batch_validate(..., show_summary=True, *, limits=None)` | Ordered entry result, never name-keyed identity. |
| `to_json(..., *, limits=None)` | Topology plus analysis and status from one snapshot; no silent `None` fallback. |
| diagram helpers | Add keyword-only limits; raise on exhaustion; render from one captured snapshot. |
| `configure_fsm_logging(..., *, propagate=None, redactor=None)` | Returns reversible `FSMLoggingHandle`; preserves app-owned state. |
| `set_fsm_logging_level(...)` | Same return type and ownership seam. |

Compatibility rule: retain every existing import in `fast_fsm.__init__`; add only intentionally public types. Current root exports validators, comparison/batch helpers, renderers, and logging helpers, so schema/signature documentation must be updated together. [VERIFIED: src/fast_fsm/__init__.py:7-110]

## Complexity and Budget Contract

| Operation | Time | Space/output | Exhaustion behavior |
|-----------|------|--------------|---------------------|
| Snapshot scalar projection | O(V+E) | O(V+E) | Captures fully or raises; never partial. [ASSUMED] |
| Reachability/dead states | O(V+E) | O(V) | Structured status or redacted exception. [ASSUMED] |
| SCC membership/condensation | O(V+E) | O(V+E) | Structured status or redacted exception. [ASSUMED] |
| Condensation depth | O(V+E) | O(V+E) | Structured status or redacted exception. [ASSUMED] |
| Sparse report/JSON | O(V+E+R) | O(V+E+R) | Status identifies work/result exhaustion. [ASSUMED] |
| Missing transition enumeration | O(V*E_events) | O(min(R, V*E_events)) | Count is cheap after per-state outgoing counts; enumeration is result-bounded. [ASSUMED] |
| Transition matrix | O(V*E_events+E) | O(V*E_events+E) | Preflight and raise before allocation. [ASSUMED] |
| Adjacency matrix | O(V²+E) | O(V²+E) | Explicit opt-in; preflight `V²`; raise before allocation. [ASSUMED] |
| Test paths | O(min(expansions, max_work)) | bounded by path/result/length limits | Legacy list raises on work exhaustion; structured sibling may report explicit incomplete status. [ASSUMED] |
| Disabled trace | O(1) | O(1), no event allocation | Covered by trigger benchmark. [ASSUMED] |

`TEST-07` requires documenting these separately from runtime operations. Diagnostics are allowed to be O(V+E) or explicitly dense/output-sensitive; no diagnostic traversal may be inserted into `trigger()`, `can_trigger()`, `add_state()`, or `add_transition()`. [VERIFIED: .github/copilot-instructions.md:40-48]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Cycle membership | Back-edge endpoint collector | Iterative SCC decomposition | SCC membership is the exact equivalence relation needed for all cycle members. |
| Cyclic longest simple path | Exhaustive visited-set DFS | Condensation DAG + memoized/topological DP | Stable linear structural depth avoids exponential work. |
| Timeout budget | elapsed-time watchdog | counted operations/results | Exact, portable, deterministic CI boundaries. |
| Node identifiers | label-derived regex replacement | snapshot-order opaque IDs | Identity and presentation remain separate; collisions are impossible within a render. |
| Cross-grammar escaping | one regex/sanitizer | grammar-specific allowlist encoders | Each parser has different comments/directives/delimiters. |
| Logging framework | custom sink/dispatcher | standard `logging` ownership primitives | Existing logger hierarchy, propagation, and handler lifecycle are sufficient. [CITED: https://docs.python.org/3/library/logging.html] |
| Graph dependency | install NetworkX at runtime | small internal sparse algorithms | The runtime dependency budget is already one package; benchmark-only NetworkX is not a runtime dependency. [VERIFIED: pyproject.toml:7-31] |

**Key insight:** the hard part is not traversing a graph; it is making every entry point share identity, ordering, budget, completeness, and redaction semantics.

## Common Pitfalls

### Pitfall 1: “One Snapshot” Still Recaptures in Nested APIs

**What goes wrong:** a public renderer calls another public renderer or validator constructor, producing mixed versions.
**Why it happens:** reuse is placed at the public boundary. Current fenced rendering calls public `to_mermaid()`. [VERIFIED: src/fast_fsm/visualization.py:309-349]
**How to avoid:** public capture once, private from-snapshot composition.
**Warning signs:** snapshot-call spies observe more than one call per machine/top-level invocation.

### Pitfall 2: Snapshot Captures Identity but Not Text

**What goes wrong:** a later mutation of a retained object name changes output from the same snapshot.
**Why it happens:** frozen dataclasses do not freeze referenced objects. [VERIFIED: src/fast_fsm/core.py:371-394]
**How to avoid:** capture scalar labels and guard presence during the synchronized copy.
**Warning signs:** rendering the same snapshot twice yields different bytes.

### Pitfall 3: Budget Accounting Depends on Set Order

**What goes wrong:** counts/exhaustion points vary with hash seed.
**Why it happens:** current validators store state/events in sets and iterate them directly. [VERIFIED: src/fast_fsm/validation.py:46-70]
**How to avoid:** index/order solely from the sorted snapshot; no traversal over unordered sets.
**Warning signs:** `PYTHONHASHSEED` changes result or exhausted count.

### Pitfall 4: Partial Results Look Complete

**What goes wrong:** a caller trusts omitted cycles/issues/paths.
**Why it happens:** max-path slicing and broad exception fallback have no completion marker. [VERIFIED: src/fast_fsm/validation.py:245-262] [VERIFIED: src/fast_fsm/visualization.py:276-304]
**How to avoid:** status on structured output; documented redacted exception for legacy shapes.
**Warning signs:** exhaustion changes data without changing status or raising.

### Pitfall 5: Dense Allocation Is Checked Too Late

**What goes wrong:** the budget exception arrives after `N²` lists exist.
**Why it happens:** count is applied while filling, not before construction. Current code creates all cells in one comprehension. [VERIFIED: src/fast_fsm/validation.py:185-189]
**How to avoid:** reserve/check the full product first.
**Warning signs:** memory spikes on a zero-edge many-state graph.

### Pitfall 6: Escaping Makes IDs Safe but Labels Remain Syntax

**What goes wrong:** comments, directives, fences, or new lines are injected through titles/triggers/conditions.
**Why it happens:** current Mermaid only sanitizes IDs and writes all label fields raw; PlantUML writes every field raw. [VERIFIED: src/fast_fsm/visualization.py:28-102] [VERIFIED: src/fast_fsm/visualization.py:107-169]
**How to avoid:** opaque IDs plus encoder at every caller-data sink, including Markdown wrappers.
**Warning signs:** hostile text appears byte-for-byte in rendered source.

### Pitfall 7: A Safe Formatter Still Leaks Through Application Handlers

**What goes wrong:** raw event data stored on a record is printed by another handler.
**Why it happens:** formatting is mistaken for redaction.
**How to avoid:** discard raw data before calling `logger.log`; record contains only approved fields.
**Warning signs:** a capture handler can inspect trigger/args/kwargs/exception values.

### Pitfall 8: Restore Overwrites Later Application Changes

**What goes wrong:** an old handle resets a level/propagation set by the application or a newer handle.
**Why it happens:** unconditional baseline restoration.
**How to avoid:** identity- and generation-aware compare-and-restore.
**Warning signs:** restoring handles out of order changes current application configuration.

## Code Examples

These are implementation skeletons and proposed names, not current public values. [ASSUMED]

### One-Capture Adapter

```python
def to_json(fsm, *, limits=None):
    snapshot = fsm._graph_snapshot()          # exactly once
    budget = _DiagnosticBudget.from_limits(limits)
    graph = _DiagnosticGraph.from_snapshot(snapshot, budget)
    return _json_from_graph(graph, budget)
```

### Reserve-Before-Work

```python
def spend_work(self, amount=1):
    next_count = self.work_count + amount
    if next_count > self.max_work:
        self.exhausted = "work"
        raise DiagnosticBudgetExceeded("diagnostic budget exhausted")
    self.work_count = next_count
```

### Cyclic Membership

```python
components = _kosaraju_iterative(graph, budget)
cyclic = [
    component
    for component in components
    if len(component) > 1 or graph.has_self_loop(component[0])
]
members = tuple(i for component in cyclic for i in component)
```

### Fail-Closed Trace Emission

```python
if logger.isEnabledFor(TRACE_LEVEL):
    safe_fields = _default_trace_metadata(operation, stage, result, args, kwargs)
    if redactor is not None:
        try:
            raw_input = _minimum_redaction_input(
                operation, stage, result, trigger, source, target, args, kwargs
            )
            safe_fields = _filter_safe_fields(redactor(raw_input))
        except Exception:
            safe_fields = {"category": "redaction_failure"}
    logger.log(TRACE_LEVEL, "fsm_trace", extra=_filter_safe_fields(safe_fields))
```

## State of the Art

| Old Approach | Current Phase 19 Approach | Impact |
|--------------|---------------------------|--------|
| Current-state reachability | declared-initial snapshot reachability | Structural diagnostics are runtime-position independent. |
| Name-keyed batch dict | position-keyed ordered entries | Duplicate names and cardinality are preserved. |
| Back-edge endpoint cycles | SCC membership | Self-loops and every long-cycle member are exact. |
| Recursive path-copy depth | condensation-DAG DP | Linear structural depth with explicit cyclic interpretation. |
| Dense report default | sparse default, dense opt-in/preflight | Generated sparse graphs remain bounded. |
| Label-derived IDs | opaque snapshot-order IDs | No punctuation collision. |
| Raw interpolated renderer text | target grammar encoders | Caller data cannot become syntax. |
| `handlers.clear()` | marked library handler + reversible handle | Application handler ownership is preserved. |
| Raw ultra-verbose arguments | minimum metadata + explicit redactor | Trace enablement does not reveal payloads. |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Iterative Kosaraju is preferred over iterative Tarjan. | Standard Stack / Pattern 3 | Low; either correct deterministic SCC implementation satisfies the locked contract. |
| A2 | Proposed public names are `DiagnosticLimits`, `DiagnosticStatus`, `DiagnosticBudgetExceeded`, and `FSMLoggingHandle`. | Public Contract | Medium; names become public documentation but semantics matter more. |
| A3 | Status counter dimensions are work/results/dense cells. | Pattern 2 | Medium; insufficient dimensions could make accounting ambiguous. |
| A4 | Legacy diagram/matrix/list helpers raise on work exhaustion, while structured dict results may report incomplete data. | Pattern 2 | Medium; planner must map each established return shape explicitly. |
| A5 | Strict allowlist encoders use decimal Mermaid entities and PlantUML Unicode escapes for all non-safe code points. | Pattern 6 | Medium; implementation must validate exact parser behavior with official grammar fixtures or optional external rendering, without adding a runtime dependency. |
| A6 | Redactor output accepts only bounded scalars after filtering. | Pattern 7 | Low; this is a recommended defense-in-depth constraint. |
| A7 | Exact default budget numbers are selected only after deterministic calibration tests. | Pattern 2 | High if skipped; arbitrary defaults could break ordinary use or fail to constrain adversarial graphs. |

## Open Questions

1. **What exact default limits should be public?**
   - What we know: limits must be finite, deterministic, complete ordinary examples, and exhaust adversarial generated graphs.
   - What's unclear: exact counts are not knowable until the shared accounting rules and fixtures exist.
   - Recommendation: make calibration an explicit implementation task: record the maximum ordinary fixture count, select documented headroom, then pin exact-pass and one-less-fails tests. Do not ask the user; this is delegated discretion.

2. **Should incomplete structured results be returned anywhere by default?**
   - What we know: structured results may expose incomplete status; legacy shapes must raise and no result may silently truncate.
   - What's unclear: partial validation issue lists may be less useful than a uniform exception.
   - Recommendation: return incomplete metadata only from an explicitly named structured analysis sibling; keep existing public helpers fail-closed on budget exhaustion for the first release.

3. **How should caller-supplied `adjacency_matrix` compatibility work?**
   - What we know: combining it blindly with a fresh graph violates snapshot consistency.
   - What's unclear: current consumers may pass matrices without version/fingerprint metadata.
   - Recommendation: validate full state/edge equivalence under budget or raise a fixed incompatibility error; document `include_adjacency=True` as the safe replacement.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Python via uv | implementation/tests | ✓ | Python 3.12 environment; project requires `>=3.10` [VERIFIED: pyproject.toml:6] | — |
| uv | all Python commands | ✓ | `0.12.6` [VERIFIED: executed `uv --version`] | none; repository mandates uv |
| pytest | tests | ✓ | `8.4.1` [VERIFIED: executed `uv run pytest --version`] | — |
| mypy | blocking typecheck | ✓ | `1.17.1 (compiled: yes)` [VERIFIED: executed `uv run mypy --version`] | — |
| Ruff | lint/format | ✓ | `0.12.11` [VERIFIED: executed `uv run ruff --version`] | — |
| ty | advisory typecheck | ✓ | `0.0.1-alpha.19` [VERIFIED: executed `uv run ty --version`] | — |
| Sphinx | docs | ✓ | `9.1.0` [VERIFIED: executed `uv run sphinx-build --version`] | — |
| Mermaid CLI | optional parser/render smoke | ✗ | — [VERIFIED: executed `command -v mmdc`] | deterministic source containment tests; CI renderer optional |
| PlantUML CLI | optional parser/render smoke | ✗ | — [VERIFIED: executed `command -v plantuml`] | deterministic source containment tests; CI renderer optional |

**Missing dependencies with no fallback:** none for required implementation or verification.

**Missing dependencies with fallback:** Mermaid and PlantUML CLIs are optional; do not add them as runtime dependencies.

## Validation Architecture

Nyquist validation is enabled: the exact config value is `"nyquist_validation": true`. [VERIFIED: .planning/config.json:15-28]

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest `>=8.4.1`, Hypothesis `>=6.136.6` [VERIFIED: pyproject.toml:11-20] |
| Config file | `pyproject.toml`; test path `"tests"`, files `"test_*.py"`, and default `"-x"`, `"-q"`, `"--tb=short"`, `"--strict-markers"`. [VERIFIED: pyproject.toml:56-75] |
| Quick run command | `uv run pytest tests/test_diagnostic_contracts.py tests/test_output_safety.py tests/test_logging_config.py -x -q` |
| Full suite command | `uv run pytest tests/ -x -q` [VERIFIED: .github/copilot-instructions.md:55-61] |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DIAG-01 | moved runtime state does not change initial reachability | unit/regression | `uv run pytest tests/test_diagnostic_contracts.py -x -q -k initial` | ❌ Wave 0 |
| DIAG-02 | duplicate names preserve order/cardinality in compare and batch | unit/schema | `uv run pytest tests/test_diagnostic_contracts.py -x -q -k duplicate` | ❌ Wave 0 |
| DIAG-03 | empty comparison exact schema/`None` aggregates | unit/schema | `uv run pytest tests/test_diagnostic_contracts.py -x -q -k empty` | ❌ Wave 0 |
| DIAG-04 | self-loop, 3-cycle, overlapping SCCs, acyclic tails | unit/property | `uv run pytest tests/test_diagnostic_contracts.py -x -q -k cycle` | ❌ Wave 0 |
| DIAG-05 | DAG depth and SCC-condensed depth, linear counted work | unit/property | `uv run pytest tests/test_diagnostic_contracts.py -x -q -k depth` | ❌ Wave 0 |
| DIAG-06 | sparse default, dense preflight, bounded paths | unit/adversarial | `uv run pytest tests/test_diagnostic_contracts.py -x -q -k 'sparse or dense or path'` | ❌ Wave 0 |
| DIAG-07 | exact limit succeeds, one-less fails with redacted metadata | unit/property | `uv run pytest tests/test_diagnostic_contracts.py -x -q -k budget` | ❌ Wave 0 |
| DIAG-08 | exactly one snapshot call; mutation after capture cannot mix output | integration/concurrency | `uv run pytest tests/test_diagnostic_contracts.py tests/test_output_safety.py -x -q -k snapshot` | ❌ Wave 0 |
| OUT-01 | colliding labels map to distinct opaque IDs | unit/golden | `uv run pytest tests/test_output_safety.py -x -q -k opaque` | ❌ Wave 0 |
| OUT-02 | hostile Mermaid/PlantUML/Markdown text remains inert | unit/property | `uv run pytest tests/test_output_safety.py -x -q -k escape` | ❌ Wave 0 |
| OUT-03 | no trigger/state/arg/kwarg/error/repr reaches capture handler | integration | `uv run pytest tests/test_logging_config.py -x -q -k redaction` | ⚠️ extend existing |
| OUT-04 | custom redactor gets minimum event; exception fails closed | integration | `uv run pytest tests/test_logging_config.py -x -q -k redactor` | ⚠️ extend existing |
| OUT-05 | app handler preserved; propagation explicit; restore idempotent/out-of-order safe | integration | `uv run pytest tests/test_logging_config.py -x -q -k 'handler or restore or propagation'` | ⚠️ replace unsafe expectations |
| TEST-07 | counts/complexity docs, no hot-path regression, slots/mypyc gates | performance/integration | commands below | ⚠️ extend existing |

### Sampling Rate

- **Per task commit:** run the targeted file(s) above plus `uv run ruff check <changed.py files>` and `task typecheck-mypy`.
- **Per wave merge:** `uv run pytest tests/test_validation.py tests/test_visualization.py tests/test_logging_config.py tests/test_graph_invariants.py tests/test_diagnostic_contracts.py tests/test_output_safety.py -x -q`.
- **Phase gate:** full suite and all commands below green before `$gsd-verify-work`.

### Deterministic Adversarial Matrix

- Empty, single-state/no-edge, self-loop, 3-cycle, multiple SCCs with bridges, long chain beyond recursion depth, high fan-out DAG, and many-state zero-edge sparse graph.
- Duplicate machine names at positions 0/1/2, tied scores, empty input, and mutation after per-input capture.
- For every budget dimension: run once with a high limit to obtain exact required count, assert that exact count succeeds, then assert one less produces the documented exhausted dimension with no partial legacy return.
- Render corpus includes quotes, apostrophes, brackets/braces/angles, colons/semicolons, backslashes, backticks/fences, CR/LF/NUL/control characters, `%`/`%%`, `!include`, `!import`, `@startuml`, `@enduml`, URLs, emoji, combining marks, RTL markers, and names whose old sanitizer collides.
- Logging sentinels appear separately in trigger, state, positional arg, keyword value, exception message, and hostile `__repr__`; scan message, args, record dictionary, formatter output, and every application handler capture for absence.

### Wave 0 Gaps

- Needed: `tests/test_diagnostic_contracts.py` — DIAG-01 through DIAG-08 and deterministic budget fixtures.
- Needed: `tests/test_output_safety.py` — OUT-01/02 and one-snapshot renderer/JSON assertions.
- Needed: extend `tests/test_logging_config.py` — replace the current handler-clearing expectation at lines 35-48 with ownership/reversal tests. [VERIFIED: tests/test_logging_config.py:35-48]
- Needed: add a Phase 19 inventory/suite to `tools/phase16_isolated_verify.py`; current accepted suite values are exactly `"graph"`, `"baseline-write"`, `"baseline-check"`, `"phase16"`, `"phase17"`, and `"phase18"`. [VERIFIED: tools/phase16_isolated_verify.py:1043-1060]

### Exact Verification Commands

```bash
uv run pytest tests/test_diagnostic_contracts.py tests/test_output_safety.py tests/test_logging_config.py -x -q
uv run pytest tests/test_validation.py tests/test_visualization.py tests/test_graph_invariants.py -x -q
uv run ruff format --check src/fast_fsm/core.py src/fast_fsm/_diagnostics.py src/fast_fsm/validation.py src/fast_fsm/visualization.py src/fast_fsm/__init__.py tests/test_diagnostic_contracts.py tests/test_output_safety.py tests/test_logging_config.py
uv run ruff check src/fast_fsm/core.py src/fast_fsm/_diagnostics.py src/fast_fsm/validation.py src/fast_fsm/visualization.py src/fast_fsm/__init__.py tests/test_diagnostic_contracts.py tests/test_output_safety.py tests/test_logging_config.py
task typecheck-mypy
task typecheck-ty
uv run python tools/release_evidence.py slots-policy --json
uv run pytest tests/test_performance_benchmarks.py -x -q -k 'trigger_min_throughput or lifecycle_success'
uv run python benchmarks/benchmark_fast_fsm.py
uv run sphinx-build -b html docs docs/_build/html -W --keep-going
uv run sphinx-build -b doctest docs docs/_build/doctest
uv run pytest tests/ -x -q
uv run python tools/phase16_isolated_verify.py --suite phase19
task release-baseline-check
```

The final `--suite phase19` command requires implementation to add that suite and inventory first; the existing isolated runner already exercises both `"pure"` and `"compiled"` modes for graph and prior phase semantics. [VERIFIED: tools/phase16_isolated_verify.py:808-827] [VERIFIED: tools/phase16_isolated_verify.py:972-1039]

## Security Domain

Security enforcement is enabled because `.planning/config.json` does not set `security_enforcement` to `false`. [VERIFIED: .planning/config.json:1-37]

OWASP ASVS 5.0 renamed/reorganized the older template categories: contextual encoding is V1 “Encoding and Sanitization,” and logging/error safety is V16 “Security Logging and Error Handling.” The relevant controls require contextual final-step encoding, protection against format/template injection, log-data protection/encoding, generic failure without sensitive disclosure, and secure failure behavior. [CITED: https://github.com/OWASP/ASVS/blob/master/5.0/en/0x10-V1-Encoding-and-Sanitization.md] [CITED: https://github.com/OWASP/ASVS/blob/master/5.0/en/0x25-V16-Security-Logging-and-Error-Handling.md]

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | Library diagnostics do not authenticate users. |
| V3 Session Management | no | No session surface. |
| V4 Access Control | no | No authorization decision is introduced. |
| V1 Encoding and Sanitization (ASVS 5.0) | yes | Final-step Mermaid, PlantUML, and Markdown contextual encoders; opaque IDs. [CITED: https://github.com/OWASP/ASVS/blob/master/5.0/en/0x10-V1-Encoding-and-Sanitization.md] |
| V16 Security Logging and Error Handling (ASVS 5.0) | yes | Payload-free records, log-injection-safe fields, fixed redacted failure categories, fail-closed budgets/redactor. [CITED: https://github.com/OWASP/ASVS/blob/master/5.0/en/0x25-V16-Security-Logging-and-Error-Handling.md] |
| V6 Cryptography (legacy template label) | no | No cryptographic primitive is needed; opaque IDs are local indices, not security tokens. |

### Known Threat Patterns for This Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Mermaid/PlantUML directive or comment injection | Tampering | Grammar-specific final-step encoding and opaque IDs; hostile source-containment tests. |
| Markdown fence/table/heading injection | Tampering | Separate Markdown contextual escaping and no physical caller-controlled newlines. |
| Trace payload/exception/repr disclosure | Information Disclosure | Raw fields never enter LogRecord; default metadata-only event; custom redactor fail-closed. |
| Application logger disruption | Denial of Service / Tampering | Never clear app handlers; identity-marked library handler; generation-aware restore. |
| Dense matrix/path explosion | Denial of Service | finite work/result/cell limits, reserve before allocate, sparse default. |
| Silent partial analysis | Spoofing / Tampering | explicit incomplete status or fixed redacted exception; no broad fallback. |
| Nondeterministic hash order | Repudiation | snapshot-order indices and stable traversal/tie-breaking. |
| Malicious `__repr__` side effect/leak | Information Disclosure / DoS | never call repr/str on payloads; snapshot condition label is captured from the defined string field with bounded encoding. |

## Likely Implementation and Documentation Files

| File | Planned responsibility |
|------|------------------------|
| `src/fast_fsm/core.py` | Deeply stable synchronized private snapshot fields; constant-time trace guard/event; logging handle and ownership-safe helpers. |
| `src/fast_fsm/_diagnostics.py` | New internal projection, limits/budget ledger, reachability, iterative SCC, condensation depth, sparse/dense/path primitives. |
| `src/fast_fsm/validation.py` | Snapshot-backed constructors, bounded APIs, positional compare/batch schema, sparse reports. |
| `src/fast_fsm/visualization.py` | One-snapshot JSON/rendering, opaque IDs, three contextual encoders, no broad exception fallback. |
| `src/fast_fsm/__init__.py` | Intentional public re-exports. |
| tests listed in Validation Architecture | Requirement and regression coverage. |
| `tools/phase16_isolated_verify.py` | Phase 19 pure/compiled inventory and suite. |
| `docs/api/validation.md`, `docs/api/visualization.md`, core API docs | Limits, complexity, schemas, escaping, logging ownership/redactor. |
| `docs/dev/architecture.md`, `docs/dev/testing.md` | Snapshot seam, counted-work rules, exact gate commands. |
| `.specify/memory/spr-validation.md`, `.specify/memory/spr-visualization.md` | Updated durable behavior summary. |
| `.specify/decisions/ADR-006-bounded-diagnostics-safe-output.md` | Costly public schemas, cyclic depth meaning, budget exhaustion, renderer/logging contracts. [ASSUMED] |
| `evidence/release-baseline.json` | Refresh only after all tests pass and review the diff; current exact baseline is `1379` passed, `97.89` total coverage, `97.28` core coverage. [VERIFIED: evidence/release-baseline.json:58-73] |

## Sources

### Primary (HIGH confidence)

- Repository source and tests cited inline: `core.py`, `validation.py`, `visualization.py`, `setup.py`, `pyproject.toml`, test suites, isolated verifier, and release evidence.
- `.planning/phases/19-bounded-diagnostics-safe-output/19-CONTEXT.md` — locked Phase 19 decisions and scope.
- `.planning/REQUIREMENTS.md` and `.planning/ROADMAP.md` — DIAG-01..08, OUT-01..05, TEST-07, phase goal, and success criteria.
- Upstream Phase 16–18 contexts and Phase 18 verification — immutable graph/initial-state, redacted lifecycle, ownership, and no-offload boundaries.

### Secondary (MEDIUM confidence)

- [Mermaid state diagram documentation](https://mermaid.js.org/syntax/stateDiagram.html) — aliases, starts, comments, state syntax.
- [Mermaid flowchart documentation](https://mermaid.js.org/syntax/flowchart.html) — quoting and numeric entity encoding guidance.
- [PlantUML state diagram documentation](https://plantuml.com/state-diagram) — aliases, labels, state diagram syntax.
- [PlantUML preprocessing documentation](https://plantuml.com/preprocessing) — directives and preprocessing threat surface.
- [PlantUML Creole/Unicode documentation](https://plantuml.com/creole) — Unicode escape form.
- [Python logging HOWTO](https://docs.python.org/3/howto/logging.html) and [logging library reference](https://docs.python.org/3/library/logging.html) — library/application ownership, propagation, handler lifecycle.
- [OWASP ASVS 5.0 V1](https://github.com/OWASP/ASVS/blob/master/5.0/en/0x10-V1-Encoding-and-Sanitization.md) and [V16](https://github.com/OWASP/ASVS/blob/master/5.0/en/0x25-V16-Security-Logging-and-Error-Handling.md) — contextual encoding and safe logging/error controls.

### Tertiary (LOW confidence)

- None used as authority. Proposed API names and policy details are explicitly marked `[ASSUMED]` and logged above.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new package; versions and build boundary read from repository source.
- Architecture: HIGH — current defects were read and reproduced; recommended graph algorithms have deterministic, testable complexity. Exact new API names remain assumptions.
- Renderer grammar: MEDIUM — checked official Mermaid/PlantUML documentation, but CLIs are unavailable locally; source-containment tests are mandatory and parser smoke tests optional.
- Logging: HIGH for Python ownership semantics; MEDIUM for the exact proposed reversible-handle shape.
- Pitfalls: HIGH — each current-code failure is cited or reproduced.

**Research seam note:** official-source queries were routed through the GSD research-plan seam. Context7 was not available in this environment, so official web documentation was used. The classify-confidence seam returned `MEDIUM`. Cache persistence was attempted but the sandbox denied writes to `/Users/akriz/.gsd/research-cache`; this does not affect the repository artifact.

**Research date:** 2026-09-02
**Valid until:** 2026-10-02 (graph/logging architecture is stable; recheck renderer grammar if upstream syntax changes)
