---
phase: 19
slug: bounded-diagnostics-safe-output
status: validated
nyquist_compliant: true
wave_0_complete: true
created: 2026-09-02
---

# Phase 19 — Validation Strategy

> Independently audited validation contract and execution evidence for correct,
> bounded, snapshot-consistent diagnostics, grammar-safe output, and
> ownership-safe redacted logging.

---

## Validation Posture

This document began as the plan-time strategy and now records independently
audited execution evidence. Every mapped requirement has an executable green
test, Wave 0 prerequisites landed, and the authoritative pure/fresh-compiled
gate passed on the finished candidate.

Phase 19 requires local asserted-pure and freshly compiled semantic parity because
`core.py` changes affect the mypyc boundary. It does not require a hosted
supported-version or installed wheel/sdist matrix: Phase 20 owns installed-artifact
parity and final release evidence. Hosted evidence becomes necessary here only if
implementation changes packaging, the CI matrix, or platform-specific behavior;
none is planned.

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.1; pytest-asyncio 1.3.0; Hypothesis; repository release-evidence and isolated pure/compiled harnesses |
| **Config files** | `pyproject.toml`, `Taskfile.yml`, `uv.lock` |
| **Fast diagnostic loop** | `uv run pytest tests/test_diagnostic_contracts.py -x -q` |
| **Fast output loop** | `uv run pytest tests/test_output_safety.py -x -q` |
| **Fast logging loop** | `uv run pytest tests/test_logging_config.py -x -q` |
| **Cross-surface loop** | `uv run pytest tests/test_diagnostic_contracts.py tests/test_output_safety.py tests/test_logging_config.py -x -q` |
| **Legacy regression loop** | `uv run pytest tests/test_validation.py tests/test_visualization.py tests/test_graph_invariants.py -x -q` |
| **Authoritative pure/compiled command** | `uv run python tools/phase16_isolated_verify.py --suite phase19` after Wave 0 adds that suite |
| **Full sequential suite** | `uv run pytest tests/ -x -q` |
| **Feedback target** | Focused task loop under 30 seconds; no correctness assertion uses elapsed time |

## Sampling Rate and Continuity

- **Before production edits:** land the owning strict-RED test or structural
  assertion and prove it fails for the intended reason. Later-wave RED cases may
  use `xfail(strict=True, reason="RED until 19-NN")`; an XPASS is a failure.
- **After every task commit:** run the row's focused command plus the exact legacy
  test module for each modified public surface.
- **After every `core.py` shape/signature edit:** run
  `uv run pytest tests/test_mypyc_guard.py tests/test_graph_invariants.py -x -q`
  and `task typecheck-mypy`.
- **After every wave:** run the cross-surface loop, the legacy regression loop,
  and all tests introduced or changed in that wave. Do not run the full suite
  after every task.
- **Before `$gsd-verify-work`:** run the Phase 19 asserted-pure/fresh-compiled
  suite, slots audit, compiled performance selection, Ruff, blocking mypy,
  advisory ty, docs, doctests, full sequential suite, and read-only baseline
  freshness check.
- **Continuity rule:** every provisional task below has an automated command.
  The planner may split or merge rows, but may never produce three consecutive
  implementation tasks without an automated verification point. If a split would
  do so, attach the nearest focused test command to the intermediate task.
- **No watch modes, sleeps, timing races, or machine-speed correctness checks.**
  Concurrency snapshot tests use barriers/events; budget tests use exact counts.

## Provisional Per-Task Verification Map

Task identifiers are provisional until the planner writes executable plans. The
planner must preserve equivalent coverage, Wave 0 dependencies, and sampling
continuity.

| Task ID | Likely plan/wave | Requirements | Secure/correct behavior | Test type | Automated command | File exists | Status |
|---------|------------------|--------------|-------------------------|-----------|-------------------|-------------|--------|
| 19-00-01 | Wave 0 harness | DIAG-01–08, TEST-07 | Strict-RED graph fixtures, exact budget ledger assertions, snapshot-call spy, duplicate/empty schemas | unit/property scaffold | `uv run pytest tests/test_diagnostic_contracts.py -x -q` | Yes | covered |
| 19-00-02 | Wave 0 harness | OUT-01–05 | Hostile renderer corpus, capture-handler leak oracle, redactor failure oracle, handler ownership fixtures | security/integration scaffold | `uv run pytest tests/test_output_safety.py tests/test_logging_config.py -x -q` | Yes | covered |
| 19-00-03 | Wave 0 harness | DIAG-08, OUT-03–05, TEST-07 | Phase 19 inventory and asserted pure/fresh-compiled runner without native-shadow reuse | structural/conformance | `uv run python tools/phase16_isolated_verify.py --suite phase19` | Yes | covered |
| 19-01-01 | Plan 01 / tracer | DIAG-01, DIAG-07, DIAG-08 | One synchronized deeply stable snapshot, one shared deterministic budget, declared-initial reachability, explicit exhaustion | unit + integration | `uv run pytest tests/test_diagnostic_contracts.py tests/test_graph_invariants.py -x -q -k 'snapshot or initial or budget'` | Yes | covered |
| 19-02-01 | Plan 02 / graph | DIAG-04, DIAG-05 | Complete self-loop/long-cycle SCC membership and memoized condensation-DAG depth | unit/property | `uv run pytest tests/test_diagnostic_contracts.py -x -q -k 'cycle or scc or depth or longest'` | Yes | covered |
| 19-02-02 | Plan 02 / graph | DIAG-06, DIAG-07, TEST-07 | Sparse-first results, dense preflight before allocation, path count/length/expansion bounds | unit/adversarial | `uv run pytest tests/test_diagnostic_contracts.py -x -q -k 'sparse or dense or path or budget'` | Yes | covered |
| 19-03-01 | Plan 03 / API | DIAG-02, DIAG-03, DIAG-07, DIAG-08 | Duplicate names preserve position/cardinality/order; zero comparison has exact `None` aggregates; each input captured once | schema/integration | `uv run pytest tests/test_diagnostic_contracts.py tests/test_validation.py -x -q -k 'compare or batch or duplicate or empty or snapshot'` | Yes | covered |
| 19-03-02 | Plan 03 / API | DIAG-01, DIAG-04–08 | Validators, reports, and JSON share sparse analysis/status without silent partial fallback | integration/regression | `uv run pytest tests/test_diagnostic_contracts.py tests/test_validation.py tests/test_visualization.py -x -q -k 'json or report or status or exhaust or snapshot'` | Yes | covered |
| 19-04-01 | Plan 04 / output | OUT-01, OUT-02, DIAG-08 | Opaque snapshot-order IDs and separate Mermaid/PlantUML/Markdown encoders keep hostile text inert and byte-stable | security/property/golden | `uv run pytest tests/test_output_safety.py tests/test_visualization.py -x -q -k 'opaque or mermaid or plantuml or markdown or snapshot or stable'` | Yes | covered |
| 19-05-01 | Plan 05 / logging | OUT-03, OUT-04, TEST-07 | Disabled trace stays constant-time/allocation-free; default metadata has no payload; explicit redactor receives minimum input and fails closed | security/performance | `uv run pytest tests/test_logging_config.py tests/test_performance_benchmarks.py -x -q -k 'trace or redact or payload or trigger_min_throughput'` | Yes | covered |
| 19-05-02 | Plan 05 / logging | OUT-05 | Application handlers/filters/formatters survive; only marked library handler changes; propagation is explicit; handles restore idempotently/out of order | logging integration | `uv run pytest tests/test_logging_config.py -x -q -k 'handler or restore or propagation or delegate'` | Yes | covered |
| 19-06-01 | Plan 06 / contracts | DIAG-01–08, OUT-01–05, TEST-07 | Public docs, ADR, SPRs, exports, signatures, complexity and budget semantics agree | docs/structural/type | `task typecheck-mypy && task typecheck-ty && uv run sphinx-build -b html docs docs/_build/html -W --keep-going && uv run sphinx-build -b doctest docs docs/_build/doctest` | Yes | covered |
| 19-06-02 | Plan 06 / phase gate | DIAG-01–08, OUT-01–05, TEST-07 | Asserted pure and fresh native parity, slots, O(1) runtime boundary, compiled throughput floor, full regression suite | conformance/performance/release | `uv run python tools/phase16_isolated_verify.py --suite phase19` | Yes | covered |

## Requirement-to-Evidence Map

| Requirement | Required observable evidence | Primary focused command | Final evidence |
|-------------|------------------------------|-------------------------|----------------|
| DIAG-01 | Move machine away from initial; every validator/JSON report still reaches from declared initial and may report current separately | `uv run pytest tests/test_diagnostic_contracts.py -x -q -k initial` | Phase 19 pure/compiled suite |
| DIAG-02 | Three same-name inputs remain three ordered position identities in compare and batch, including tied scores | `uv run pytest tests/test_diagnostic_contracts.py -x -q -k duplicate` | Phase 19 pure/compiled suite |
| DIAG-03 | `compare_fsms()` with no inputs returns empty entries/rankings, no best, zero counts, and `None` undefined aggregates | `uv run pytest tests/test_diagnostic_contracts.py -x -q -k empty` | Phase 19 pure/compiled suite |
| DIAG-04 | Self-loop, 3-cycle, overlapping cyclic SCCs, multiple SCCs, and acyclic tails return exactly all cyclic members once in snapshot order | `uv run pytest tests/test_diagnostic_contracts.py -x -q -k 'cycle or scc'` | Phase 19 pure/compiled suite |
| DIAG-05 | DAG edge depth is exact; cyclic graph reports condensation depth/interpretation; long chain does not recurse; counted work is linear-bound | `uv run pytest tests/test_diagnostic_contracts.py -x -q -k 'depth or longest'` | Phase 19 pure/compiled suite |
| DIAG-06 | Zero-edge many-state graph remains sparse by default; dense output preflights `V²`/`V*events`; paths honor three independent limits | `uv run pytest tests/test_diagnostic_contracts.py -x -q -k 'sparse or dense or path'` | Phase 19 pure/compiled suite |
| DIAG-07 | Exact budget succeeds and one-less exhausts before work/allocation for every dimension; structured status or redacted exception is explicit | `uv run pytest tests/test_diagnostic_contracts.py -x -q -k budget` | Phase 19 pure/compiled suite |
| DIAG-08 | Snapshot-call spy observes one call per machine/top-level API; barrier mutation cannot mix graph versions; same snapshot renders byte-identically | `uv run pytest tests/test_diagnostic_contracts.py tests/test_output_safety.py -x -q -k snapshot` | Phase 19 pure/compiled suite |
| OUT-01 | Old-colliding labels such as punctuation variants get distinct opaque IDs; labels never serve as IDs | `uv run pytest tests/test_output_safety.py -x -q -k opaque` | Phase 19 pure/compiled suite |
| OUT-02 | Hostile state/trigger/condition/title text cannot create physical lines, comments, directives, fences, aliases, links, or terminators in either grammar | `uv run pytest tests/test_output_safety.py -x -q -k 'escape or hostile'` | Phase 19 pure/compiled suite |
| OUT-03 | Unique sentinels placed in trigger/state/args/kw-values/errors/reprs are absent from message, args, record dictionary, formatter output, and all handlers | `uv run pytest tests/test_logging_config.py -x -q -k 'trace and redaction'` | Phase 19 pure/compiled suite + performance selection |
| OUT-04 | Redactor sees only the documented minimum event, safe output is accepted, invalid/raising redactor emits fixed failure/suppression without raw fallback | `uv run pytest tests/test_logging_config.py -x -q -k redactor` | Phase 19 pure/compiled suite |
| OUT-05 | Preinstalled app handlers retain identity/order/config; repeated calls replace one library handler; restore affects only owned current generation; setter delegates | `uv run pytest tests/test_logging_config.py -x -q -k 'handler or restore or propagation or delegate'` | Phase 19 pure/compiled suite |
| TEST-07 | Complexity docs match implementation counters; disabled tracing leaves O(1) trigger; compiled throughput remains at least 200,000 operations/second | `uv run pytest tests/test_performance_benchmarks.py -x -q -k 'trigger_min_throughput or trace'` | slots audit, benchmark, Phase 19 suite, full suite |

## Wave 0 Requirements

Wave 0 is incomplete until all items below exist and their strict-RED behavior is
observed. These bullets describe prerequisites, not issue tracking.

- `tests/test_diagnostic_contracts.py`: real-machine fixtures for empty, single
  state, moved-current-state, self-loop, long chain, high-fan-out DAG, multiple
  SCCs, zero-edge sparse graph, duplicate names, snapshot-call counting, and
  barrier-controlled mutation.
- A reusable exact-budget assertion helper that first obtains the deterministic
  required count under a high limit, proves the exact limit succeeds, then proves
  `required - 1` exhausts the named dimension before the forbidden operation.
- `tests/test_output_safety.py`: table-driven hostile text across state labels,
  triggers, conditions, titles, Markdown headings/cells, Unicode, combining and
  directionality characters, all controls, quotes, comment markers, directives,
  fence text, URLs, and old identifier collisions.
- Extend `tests/test_logging_config.py` with a real capture handler/formatter,
  hostile `__repr__`, unique secret sentinels in every raw field, redactor output
  filtering/failure, propagation choices, handler identity/order, repeated
  configuration, and in-order/out-of-order/idempotent restore.
- Extend `tests/test_performance_benchmarks.py` with disabled-trace evidence that
  does not weaken the existing compiled throughput floor and does not use a timing
  assertion to establish functional correctness.
- Add `PHASE19_INVENTORY` and `--suite phase19` to
  `tools/phase16_isolated_verify.py`. The suite must overlay every changed source,
  test, documentation contract input needed by its commands; assert `.py` origin
  before pure tests and freshly built native origin before compiled tests. Move
  `baseline-write` to the Phase 19 inventory so the refreshed manifest measures
  the actual candidate rather than the prior phase's overlay set.
- Update current legacy expectations only when the new contract intentionally
  changes schema/escaping/handler behavior. Keep callable names and additive
  keyword-only signature compatibility guarded by `tests/test_mypyc_guard.py`.

### Strict-RED Removal Protocol

1. Assign every strict-RED row to exactly one later plan task and encode that owner
   in the `xfail(strict=True, reason="RED until 19-NN")` reason.
2. At the start of the owning task, remove only its markers and run its focused
   selection. It must fail on the intended behavioral assertion before production
   code changes.
3. Implement until that selection passes; later owners' strict-RED rows remain.
4. Before the phase gate, assert no Phase 19 strict-RED markers remain and run the
   complete diagnostic/output/logging selection.

## Deterministic Budget Boundary Matrix

| Dimension | Required case | Pass boundary | Exhaust boundary | Fail-closed assertion |
|-----------|---------------|---------------|------------------|-----------------------|
| Graph work | reachability, SCC passes, condensation, depth | `max_work == observed_required` | `max_work == observed_required - 1` | No next vertex/edge operation; exact count/category only |
| Result count | issues, cycle members, comparison entries, generated paths | `max_results == observed_required` | one less | No append after exhaustion; legacy shapes return nothing partial |
| Dense cells | transition and adjacency matrix | exact `V*events` or `V²` | one less | Exception occurs before outer matrix/list allocation |
| Path expansions | branching cyclic and acyclic graphs | exact expansion count | one less | No hidden truncation; exhaustion distinguished from `max_paths`/`max_length` |
| Aggregate top-level budget | JSON/report invoking multiple analyses | exact combined count | one less | Nested helper cannot reset budget; status names exhausted stage/dimension |

Run each boundary case repeatedly and under at least two `PYTHONHASHSEED` values;
counts and result order must be identical. Hash-seed runs are deterministic process
invocations, not statistical performance sampling.

## Hostile Output and Logging Matrix

### Diagram and Markdown Sources

- Assert opaque node IDs derive only from snapshot position and are unique for all
  labels, including empty and punctuation-colliding names.
- Assert every caller-controlled sink is covered: state label, source/target label,
  trigger, condition, title, Mermaid comment/title line, PlantUML title/alias/edge,
  Markdown heading, table header/cell, and fenced body.
- Include `%%`, `!include`, `!import`, `@startuml`, `@enduml`, backticks/fences,
  quotes, apostrophes, colons, semicolons, brackets/braces/angles, backslashes,
  CR/LF/NUL and remaining controls, URLs, emoji, combining marks, and RTL markers.
- Verify structural containment and deterministic bytes locally. Optional Mermaid or
  PlantUML CLI parser smoke tests may be added when tools are available, but they
  cannot be the only evidence and cannot become runtime dependencies.

### Trace and Handler Safety

- Put different secret sentinels in trigger name, source/destination name,
  positional value, keyword value, exception payload, and `__repr__`. Trigger all
  fixed result/stage categories in sync and async machines.
- Capture the full `LogRecord`: `msg`, `args`, formatted message, `__dict__`, and
  output observed by both library-owned and application-owned handlers. No default
  trace path may contain a sentinel or invoke hostile repr.
- With an explicit redactor, assert the input has only fields documented for that
  event, the raw input never reaches the record, output fields are allowlisted and
  bounded, and exception/invalid output emits only a fixed category or suppression.
- Install application handlers, filters, and formatters before configuration;
  assert identity, order, level, formatter, filters, and closed state are unchanged.
  Exercise repeated configuration, explicit propagation values, default-preserved
  propagation, setter delegation, restore twice, and restore handles out of order.

## Fresh Pure/Compiled Parity

During development, the runner's task mode can isolate the focused suite before
the final `phase19` suite exists:

```bash
uv run python tools/phase16_isolated_verify.py --mode task --build-mode pure \
  --include src/fast_fsm/core.py \
  --include src/fast_fsm/_diagnostics.py \
  --include src/fast_fsm/validation.py \
  --include src/fast_fsm/visualization.py \
  --include src/fast_fsm/__init__.py \
  --include tests/test_diagnostic_contracts.py \
  --include tests/test_output_safety.py \
  --include tests/test_logging_config.py \
  -- uv run pytest tests/test_diagnostic_contracts.py tests/test_output_safety.py tests/test_logging_config.py -x -q

uv run python tools/phase16_isolated_verify.py --mode task --build-mode compiled \
  --include src/fast_fsm/core.py \
  --include src/fast_fsm/_diagnostics.py \
  --include src/fast_fsm/validation.py \
  --include src/fast_fsm/visualization.py \
  --include src/fast_fsm/__init__.py \
  --include tests/test_diagnostic_contracts.py \
  --include tests/test_output_safety.py \
  --include tests/test_logging_config.py \
  -- uv run pytest tests/test_diagnostic_contracts.py tests/test_output_safety.py tests/test_logging_config.py -x -q
```

The final `--suite phase19` must run the same semantic matrix in an asserted pure
temporary source tree and a separate freshly compiled temporary tree, then run the
compiled performance selection and pure release gate. It must fail closed on wrong
origin or missing overlay files. Do not reuse an in-checkout `.so`/`.pyd`.

## Performance and Complexity Gates

| Contract | Evidence | Gate |
|----------|----------|------|
| `trigger()`, `can_trigger()`, `add_state()`, `add_transition()` remain O(1) | Structural review plus existing benchmark suite | No graph traversal, snapshot capture, renderer, redactor call, or handler search on default runtime path |
| Disabled trace adds only level check | Targeted benchmark and structural assertion | No event/map creation, args copy, kwargs value traversal, repr/str, or redactor invocation when disabled |
| Compiled trigger floor | Existing performance test and benchmark | At least 200,000 operations/second |
| Reachability/SCC/depth | Exact counters over graph families | O(V+E) operations within documented constant accounting |
| Sparse default | Zero-edge/high-state generated graph | O(V+E) stored graph data; no `V²` allocation |
| Dense compatibility | Preallocation budget test | O(V²+E) or O(V*events+E), opt-in and rejected before allocation when over limit |
| Path generation | Exact expansion/result counters | Bounded by length, path count, and expansion limit; no silent partial list |

Required final commands:

```bash
uv run python tools/phase16_isolated_verify.py --suite phase19
uv run python tools/release_evidence.py slots-policy --json
uv run pytest tests/test_performance_benchmarks.py -x -q -k 'trigger_min_throughput or trace'
uv run python benchmarks/benchmark_fast_fsm.py
```

Performance measurements may vary by host; only the repository's existing compiled
throughput floor is a timing gate. Diagnostic complexity and exhaustion are proven
by exact counted operations, not elapsed time.

## Documentation and Static Gates

```bash
uv run ruff format --check src/fast_fsm/core.py src/fast_fsm/_diagnostics.py src/fast_fsm/validation.py src/fast_fsm/visualization.py src/fast_fsm/__init__.py tests/test_diagnostic_contracts.py tests/test_output_safety.py tests/test_logging_config.py
uv run ruff check src/fast_fsm/core.py src/fast_fsm/_diagnostics.py src/fast_fsm/validation.py src/fast_fsm/visualization.py src/fast_fsm/__init__.py tests/test_diagnostic_contracts.py tests/test_output_safety.py tests/test_logging_config.py
task typecheck-mypy
task typecheck-ty
uv run sphinx-build -b html docs docs/_build/html -W --keep-going
uv run sphinx-build -b doctest docs docs/_build/doctest
```

Documentation must state snapshot-per-call semantics, positional comparison
identity and empty schema, every default/override budget and counted unit,
structured completion versus exception behavior, SCC and cyclic-depth meaning,
sparse/dense/path complexities, renderer encoding guarantees, default trace
redaction, custom-redactor trust/failure boundary, handler ownership, propagation,
and reversible handle behavior.

## Final Local Phase Gate

Run once after implementation and focused/wave checks are green:

```bash
uv run pytest tests/ -x -q
uv run python tools/phase16_isolated_verify.py --suite baseline-write --manifest-output evidence/release-baseline.json
git diff -- evidence/release-baseline.json
uv run python tools/phase16_isolated_verify.py --suite phase19
task release-baseline-check
```

Phase 19 adds tests, so the prior exact-count release baseline is expected to become
stale. Refresh it only through the isolated reviewed baseline-write flow above,
inspect the exact diff, and rerun the read-only check. A fresh baseline is evidence,
not a substitute for the requirement-focused suite.

## Manual-Only Verifications

All Phase 19 behavior is automatable locally. Human review is limited to judging
the published comparison/budget/escaping/logging API wording and reviewing any
intentional baseline diff; those reviews do not replace automated behavior tests.

No hosted evidence is required for Phase 19 under the current scope. If a plan
unexpectedly changes packaging, CI, or platform-sensitive native behavior, stop and
add an exact-candidate-SHA hosted gate rather than treating a queued/running/stale
workflow as success. Otherwise leave installed wheel/sdist and Python-version
matrix parity to Phase 20 as locked.

## Pre-Execution Readiness Checks

| Check | Current state |
|-------|---------------|
| Every requirement maps to focused and final evidence | verified |
| Every provisional task has automated verification | verified |
| No three consecutive unverified tasks | verified; zero unverified rows |
| Wave 0 test files/harness extensions exist | complete |
| Strict-RED failures observed before production edits | complete; recorded in plan summaries |
| Pure and compiled semantic origins asserted | passed |
| Performance/complexity gates pass | passed |
| Full suite and baseline freshness pass | 1,503/1,503; baseline current |
| Independent Nyquist audit performed | complete; 14/14 mappings covered |

## Validation Sign-Off

| Criterion | Status |
|-----------|--------|
| All tasks have automated verification or Wave 0 dependencies | passed |
| Sampling continuity has no three consecutive unverified tasks | passed |
| Wave 0 covers every missing reference | passed |
| No watch-mode flags or timing sleeps | passed |
| Focused feedback target is under 30 seconds | passed for focused loops |
| Asserted pure/fresh-compiled parity passes | passed |
| Deterministic budget boundaries pass | passed |
| Hostile grammar/logging matrix passes | passed |
| Compiled trigger remains at least 200,000 operations/second | passed under strict uninstrumented gate |
| `nyquist_compliant: true` | set after independent audit |

**Approval:** validated independently on 2026-09-04.

## Validation Audit 2026-09-04

| Metric | Count |
|--------|-------|
| Requirement mappings audited | 14 |
| Gaps found | 0 |
| Resolved | 14 |
| Escalated | 0 |

The auditor traced DIAG-01 through DIAG-08, OUT-01 through OUT-05, and the
Phase 19 TEST-07 prerequisite to executable behavior. The authoritative
`uv run python tools/phase16_isolated_verify.py --suite phase19` gate passed
from asserted pure and freshly compiled origins with 1,503/1,503 tests,
98.11% total coverage, 97.52% `core.py` coverage, and the strict compiled
200,000 operations/second floor exercised under an uninstrumented process.
