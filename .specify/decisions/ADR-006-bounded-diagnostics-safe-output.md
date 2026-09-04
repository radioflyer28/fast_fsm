# ADR-006: Bounded diagnostics and safe output

**Status**: Accepted
**Date**: 2026-09-04
**Deciders**: project maintainer + AI pair

---

## Context

Phase 19 corrects diagnostic, rendering, and logging surfaces that previously
could derive incompatible views of mutable topology, conflate the declared
initial state with runtime state, overwrite duplicate-name results, allocate
dense structures unconditionally, emit unsafe grammar text, or disrupt an
application logger. The library must keep `core.py` as its only mypyc unit,
preserve O(1) core operations and the compiled throughput floor, add no runtime
dependency, and remain backward compatible with established return shapes.

The durable public choices span D-01 through D-17. They include result schema,
exhaustion behavior, graph semantics, output encoding, trace redaction, and
reversible library logging ownership. Changing any of them after release would
force consumers to migrate diagnostic parsers, output snapshots, or logger
configuration assumptions.

## Decision

1. **D-01 — one snapshot per top-level call.** Validation, comparison, batch
   validation, JSON analysis, and every diagram/document call capture exactly
   one immutable internal graph snapshot and route it through private
   from-snapshot helpers. Neither nested helper nor renderer rereads live
   topology, current state, or graph version.
2. **D-02 — declared initial is structural.** Reachability starts at the
   captured declared initial state. Captured current state is separate metadata
   and never substitutes for the structural root.
3. **D-03 — position owns batch identity.** Comparison and batch schemas retain
   one ordered entry per input with zero-based `position`; names are labels,
   including duplicates and empty values. Comparison rankings break equal
   scores by ascending position.
4. **D-04 — zero inputs have an explicit schema.** Empty comparison returns
   empty entries/rankings, `best_fsm=None`, zero count/issue aggregates, and
   `None` for undefined numeric aggregates. It does not divide by zero or
   invent a numeric score.
5. **D-05/D-06 — finite counted budgets and truthful completion.**
   `DiagnosticLimits` has fixed defaults of `max_work=50_000`,
   `max_results=10_000`, `max_dense_cells=200_000`, and
   `max_path_expansions=20_000`. The shared ledger reserves before each work,
   result, dense allocation, or path expansion. `DiagnosticStatus` exposes
   completion, exhausted dimension/stage, and all four counters. Structured
   results carry status; a legacy shape that cannot carry truthful partial
   metadata raises fixed-message `DiagnosticBudgetExceeded` before a partial
   value escapes. Limits are deterministic counters, never elapsed-time
   enforcement.
6. **D-07/D-08 — iterative SCC and condensation semantics.** Iterative
   Kosaraju determines canonical cyclic SCC membership, including self-loops.
   Structural depth is iterative dynamic programming over an acyclic graph or
   its SCC condensation DAG. A cyclic result says
   `condensation_dag_depth`; it never promises an NP-hard exact longest simple
   path inside a component.
7. **D-09/D-10 — sparse first, dense/path preflight.** Ordered sparse rows are
   the normal `O(V + E)` representation. Dense transition (`V × events`) and
   adjacency (`V²`) compatibility structures reserve their whole cell count
   before allocation. Iterative generated paths retain request caps and shared
   expansion/work/result bounds.
8. **D-11/D-12/D-13 — snapshot-order identity and grammar-specific encoding.**
   Mermaid and PlantUML IDs are opaque `s{snapshot_position}` values; labels
   never participate in identity. Separate final-sink Mermaid, PlantUML, and
   Markdown encoders make titles, labels, triggers, and scalar condition names
   inert one-line data. JSON and diagrams follow snapshot order; repeated use
   of one snapshot is byte-stable. Caller-supplied dense adjacency must fully
   match that capture or raises one fixed mismatch error.
9. **D-14/D-15 — metadata-only trace and fail-closed redaction.** Default trace
   records include only fixed operation/stage/result categories, positional
   count, and bounded safe keyword names. The minimum frozen
   `FSMTraceEvent` reaches an explicit redactor only; only bounded scalar
   `operation`, `stage`, `result`, and `detail` output is accepted. Invalid,
   excessive, non-scalar, non-mapping, or an ordinary `Exception` from a
   redactor becomes fixed `redaction_failure` metadata without raw fallback.
   `BaseException` subclasses emit no trace record and are re-raised.
10. **D-16/D-17 — library handler ownership is reversible.**
    `configure_fsm_logging()` marks and replaces only its own stream handler,
    leaving application handler identity, filters, formatters, order, and open
    state untouched. `propagate=None` preserves application propagation; a
    Boolean is explicit. `FSMLoggingHandle` uses generation plus current-value
    comparison to restore only still-current library changes, safely and
    idempotently. `set_fsm_logging_level()` delegates to this same seam.

Diagnostics remain interpreted in `_diagnostics.py`; `core.py` provides only
the owned snapshot capture plus trace/logging guards. No diagnostic traversal,
dense allocation, or redactor execution belongs in `trigger()`,
`can_trigger()`, `add_state()`, or `add_transition()`.

## Considered Alternatives

### Recursive traversal and enumerating cyclic simple paths — Rejected

Recursive paths risk stack growth and simple-path enumeration is exponential
or NP-hard in cyclic graphs. Iterative SCC plus condensation depth has bounded,
truthful semantics.

### Dense-by-default diagnostics — Rejected

Unconditional `V²` allocation makes sparse/generated graphs unsafe. Sparse
rows give the normal case `O(V + E)` behavior; dense consumers opt in and are
preflighted.

### Name-keyed comparison or a zero-valued empty aggregate — Rejected

Names can duplicate or be empty, and zero is not a meaningful average/range
for no FSMs. Positional records preserve input cardinality and `None` preserves
undefined numeric aggregates.

### Generic sanitizer or label-derived identifiers — Rejected

One sanitizer cannot safely define Mermaid, PlantUML, and Markdown grammar
contexts, and sanitized labels collide. Each grammar receives a final-sink
encoder while opaque IDs remain independent of display text.

### Silent truncation, `None` fallback, or wall-clock budgets — Rejected

Partial legacy output would look authoritative, and timeouts vary by host.
Reserve-before-work counters and status/exception boundaries are deterministic
and auditable.

### Raw trace formatting or best-effort redactor fallback — Rejected

Formatting is not redaction. Raw payloads, errors, and hostile `repr` output
must never reach a record. A bounded allowlist and fixed fail-closed category
are safer than emitting a partially filtered value.

### Clearing handlers or unconditional restore — Rejected

Application logger configuration is not library-owned. Marked handlers and
generation-aware compare-and-restore avoid deleting application handlers or
overwriting subsequent configuration.

## Consequences

**Positive:**

- Consumers receive position-safe schemas, explicit zero-input semantics, and
  deterministic completion or failure instead of ambiguous output.
- Rendered diagrams remain collision-free and caller text cannot become
  Mermaid, PlantUML, or Markdown syntax.
- Logging starts payload-free, lets an application explicitly produce bounded
  safe detail, and preserves application ownership across configuration and
  restore.
- Analysis remains optional and outside all O(1) runtime operations, without a
  new dependency or a second compiled module.

**Negative / watch-outs:**

- Existing list/scalar/diagram callers receive a budget exception instead of a
  partial result when a finite limit is exhausted.
- Dense callers must request dense output deliberately and keep any supplied
  matrix exactly aligned with the captured graph.
- Custom redactors have a narrow contract and invalid output intentionally
  loses detail rather than attempting recovery.

## Deferred Follow-up

- FUTR-05 remains the future public, versioned topology snapshot/serialization
  contract; Phase 19's internal graph snapshot is not an external format.
- Phase 20 owns installed wheel/sdist pure/native parity, publication, and the
  final release evidence matrix. Phase 19 asserted pure/fresh-native source
  checks are not installed-artifact proof.
- Logging backends, automatic callback offload, schedulers, interactive
  diagrams, and new graph-query product features remain out of scope.
