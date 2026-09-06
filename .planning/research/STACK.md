# Technology Stack: Priority-Aware Guarded Transitions

**Project:** Fast FSM v0.4.0
**Researched:** 2026-09-06
**Overall confidence:** MEDIUM — repository/runtime findings are direct and HIGH-confidence; external documentation was verified against primary sources, but the GSD research seam classifies web-retrieved evidence as MEDIUM

## Recommendation in One Sentence

Keep Fast FSM's production stack unchanged—Python 3.10+ with only
`mypy-extensions` at runtime—and implement priority inside the existing compiled
`core.py` as a direct `(state, trigger)` dictionary lookup followed by a
preordered, finite candidate scan; carry the same scalar priority through the
builder, declarative metadata, immutable graph snapshot, serialization,
diagnostics, and existing pure/compiled proof harness.

## Recommended Stack

### Core Runtime

| Technology | Project Version | Purpose | Recommendation |
|------------|-----------------|---------|----------------|
| CPython | `>=3.10`; CI covers 3.10–3.14 | Runtime language and standard containers | Keep. The feature needs only dictionaries, tuples/lists, integers, and existing locks. Do not raise the Python floor. |
| `mypy-extensions` | Runtime requirement `>=1.0`; lock resolves 1.1.0 | Existing `@mypyc_attr` boundary | Keep as the sole runtime dependency. Priority resolution does not justify another package. |
| mypy + mypyc | Build pin `1.17.1` | Compile `src/fast_fsm/core.py` and enforce its static types | Keep the reviewed pin for this milestone. Do not combine the semantic change with a compiler upgrade. |
| setuptools | Build pin `80.9.0` | Existing selective-mypyc build hook | Keep. No backend change is needed. |
| wheel | Build pin `0.45.1` | Pure and native wheel production | Keep. Validate both artifact modes after the core representation changes. |

**Confidence: HIGH.** These versions and boundaries come directly from
`pyproject.toml`, `setup.py`, `uv.lock`, CI, and the v0.3 release-evidence
contract.

### Runtime Representation

Retain the outer lookup shape:

```text
dict[source_state_name][trigger] -> TransitionEntry | TransitionGroup
```

Use two private, native, slotted core containers:

```python
class TransitionEntry:
    __slots__ = ("to_state", "condition", "priority")

class TransitionGroup:
    __slots__ = ("candidates",)
    # candidates: tuple[TransitionEntry, ...], ascending priority
```

Recommended behavior:

- Preserve a lone transition as a direct `TransitionEntry`. This keeps the
  overwhelmingly common one-transition path close to its current allocation,
  memory, and dispatch cost.
- Promote to `TransitionGroup` only when a second transition is registered for
  the same `(source, trigger)` pair.
- Store group candidates as an immutable tuple sorted once during topology
  mutation. Dispatch must never sort.
- Replace a group atomically with a newly prepared group rather than mutating a
  shared list in place. This fits the current normalize/preflight/commit model,
  makes graph snapshots stable, and prevents `clone()` from sharing a mutable
  candidate list accidentally.
- Keep candidate ordering ascending by an explicit integer priority. Use
  `priority: int = 0` as the keyword-only public default; reject booleans and
  non-integers (`type(priority) is int`), and reject a conflicting equal
  priority within one source/trigger group. An exactly identical registration
  may remain an idempotent no-op.
- Do not use registration order as a hidden tie-break. Python preserves dict
  insertion order and sort stability, but safety-significant precedence should
  survive setup-code reordering and topology round trips.

This representation adds one predictable type branch after the existing direct
lookup while avoiding a new wrapper allocation and tuple iteration for every
ordinary single transition.

**Confidence: HIGH** for fit with the current code; **MEDIUM** for the exact
performance/memory result until measured in both pure and compiled modes.

### Ordering Primitive

Use a standard-library insertion routine during registration. A small explicit
linear insertion into a copied list followed by `tuple(...)` is preferable to a
new sorted-collection dependency. `bisect` is also available on every supported
Python and gained `key=` in Python 3.10, but its search advantage does not
change the required O(k) list insertion cost.

The cold-path cost is therefore:

```text
lookup candidate group: O(1) relative to total topology
insert/rebuild group:    O(k) for k candidates in that group
```

The hot-path cost is:

```text
lookup candidate group:  O(1) relative to total topology
resolve candidate:       O(k) worst case, because up to k guards must run
ordinary singleton:      O(1), as today
```

This is the honest complexity contract. No container can choose the first
passing arbitrary predicate in sublinear time without evaluating the preceding
predicates. The roadmap must update blanket claims that every `trigger()` and
`add_transition()` call is O(1): prioritized groups are bounded by their local
candidate count, not by the size of the full FSM graph.

**Confidence: HIGH.** Python's official `bisect` documentation explicitly notes
that O(log n) search is dominated by O(n) insertion, and the need to evaluate
arbitrary guards establishes the dispatch lower bound.

### Sync and Async Evaluation

Keep the current split evaluators and one shared candidate representation:

| Path | Required behavior |
|------|-------------------|
| `can_trigger()` / `trigger()` | Evaluate candidates sequentially in priority order through `_evaluate_condition_sync()`. Reject awaitable requirements as today. |
| `can_trigger_async()` / `trigger_async()` | Await candidates sequentially in the same priority order through `_evaluate_condition_async()`. |
| Guard context | Sanitize keyword arguments once per public trigger attempt when any candidate needs them, then reuse that same fresh mapping for every candidate evaluation. |
| Ownership | Hold the existing per-machine sync/async ownership envelope across candidate selection and the chosen lifecycle. |
| Cancellation | Preserve existing async cancellation behavior. Never convert cancellation into a lower-priority fallback. |

Do not use `asyncio.gather()` or tasks to evaluate competing guards in parallel.
Parallel evaluation would execute guards that should have been short-circuited,
make side effects race, and let completion timing replace explicit priority as
the decision rule.

Once a candidate passes all pre-transition eligibility checks and lifecycle
execution begins, callback failure must return that candidate's existing staged
failure; it must not fall through to a lower-priority transition. Likewise, a
guard exception should preserve the current fail-closed result rather than be
silently treated as false unless the milestone explicitly changes the global
guard-error contract.

**Confidence: HIGH.** This preserves the Phase 17 lifecycle and Phase 18
ownership/cancellation contracts already implemented in `core.py`.

### Builder and Declarative APIs

Do not add parallel public APIs. Thread the same keyword through existing ones:

```python
fsm.add_transition(..., priority=10)
builder.add_transition(..., priority=10)
@transition(..., priority=10)
```

Implementation constraints:

- Extend `FSMBuilder._transitions` staging rows to carry priority, and include
  every staged candidate when recursively detecting async guard requirements.
- Keep builder publication atomic: conflicting priorities or invalid later
  candidates must not publish a partially built machine or freeze a failed
  builder.
- `DeclarativeState._handlers` currently stores one metadata dictionary per
  trigger. Priority-aware declarative alternatives require a finite collection
  per trigger and resolution by canonical target plus priority. Merely adding
  priority to machine edges while leaving `_handlers[trigger]` singular would
  execute or guard the wrong handler.
- Continue using the existing target-aware declarative resolver and
  context-local prepared-guard marker. Extend their identity to include the
  selected candidate/priority so one candidate cannot consume another's guard
  marker.

**Confidence: HIGH** that these seams must change; exact decorator semantics
remain a requirements decision.

### Graph, Serialization, and Diagnostics

Priority is topology, not runtime payload. Carry it through every existing
projection:

| Surface | Required stack change |
|---------|-----------------------|
| `_GraphTransition` / `_GraphSnapshot` | Add scalar `priority`; emit one immutable edge row per candidate in deterministic `(source, trigger, priority, target)` order. |
| `_DiagnosticEdge` | Add scalar priority and retain candidate multiplicity instead of collapsing edges by target. |
| `to_dict()` / `from_dict()` | Include a JSON integer `priority` on every transition row and restore candidate groups through the existing `add_transition()`. No serialization package is needed. |
| `clone()` | Copy outer/inner dictionaries while safely sharing immutable transition entries/groups and conditions, matching the existing shallow-topology contract. |
| Mermaid / PlantUML / JSON | Render/export the priority so diagrams and machine-readable output explain why an edge wins. |
| Validation | Treat distinct priorities as deterministic ordering, not the current "multiple targets means non-deterministic" result; flag duplicate priority and an unconditional candidate that shadows every lower candidate. |

The current `from_dict(..., conditions={trigger: guard})` lookup cannot uniquely
address multiple guarded candidates sharing a trigger. Requirements must define
an exact candidate key—prefer a tuple such as `(from_state, trigger, priority)`
with the existing string key retained only as a fallback—rather than introduce a
second deserializer. This is an evolution of the existing `conditions`
parameter, not a new API surface.

Keep `_diagnostics.py`, `validation.py`, and `visualization.py` interpreted and
opt-in. Candidate-aware validation must consume the immutable snapshot; it must
not be called from `trigger()`.

**Confidence: HIGH.** These are direct consumers of the current single-entry
shape and will otherwise lose or misclassify candidate edges.

## Verification Stack

Reuse the repository's established tools and pins:

| Tool | Resolved / Required Version | Priority-specific use |
|------|-----------------------------|-----------------------|
| pytest | 8.4.1 | API validation, tie rejection, selection/fallthrough, lifecycle failure, serialization, clone, and introspection tests |
| pytest-asyncio | 1.3.0 | Sequential async guard order, short-circuiting, exceptions, cancellation, and sync/async parity |
| Hypothesis | 6.138.8 resolved | Generate finite candidate groups with unique priorities and assert the minimum passing priority wins independent of registration order |
| mypy/mypyc | 1.17.1 build pin | Blocking type/compile check for the new union/group representation in `core.py` |
| Ruff | 0.12.11 resolved | Existing format/lint gate |
| uv | 0.12.6 evidence pin | Reproduce pure, compiled, test, docs, and artifact verification environments |
| Sphinx + doctest | Existing docs group | Verify the public priority API and telemetry example |

Required benchmark cases:

1. Existing unguarded singleton toggle, unchanged, remains the principal
   compiled `trigger()` floor of at least 200,000 operations/second.
2. Guarded singleton transition, to expose any cost added by the group-capable
   preparation path.
3. Candidate groups of 2, 4, and 8 where the first guard passes.
4. Candidate groups of 2, 4, and 8 where only the last guard passes.
5. Candidate groups where every guard rejects.
6. Matching sequential async scenarios as semantic/relative measurements rather
   than the synchronous throughput floor.
7. Registration scaling that varies unrelated topology separately from local
   candidate count, proving `O(1) + O(k)` rather than accidentally scanning the
   whole graph.
8. Per-singleton and per-candidate memory measurements, including pure/native
   layout and the slots-policy audit.

Run the same priority oracle against source, installed pure wheel, and installed
compiled wheel. Reuse the Phase 20 artifact-conformance/evidence machinery rather
than creating a new benchmark or packaging framework.

**Confidence: HIGH.** Every named tool and artifact mode already exists in the
repository.

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Public API | Extend `add_transition`, builder, and `@transition` with `priority=` | Add `add_transition_candidate()` | Duplicates the concept; the user has explicitly chosen one transition API. |
| Storage | Direct singleton entry; promote competing keys to a slotted immutable group | Store a list for every trigger | Adds allocation, pointer indirection, and iteration to every ordinary transition before evidence shows it is necessary. |
| Ordering | Explicit integer priority, lower value first, equal value rejected | Registration order | Implicit precedence changes when setup code or serialized rows are reordered. |
| Mutation | Preorder/copy candidates during topology commit | Sort candidates inside every trigger | Moves avoidable work into the compiled hot path. |
| Candidate lookup | Existing nested dictionaries | Scan all outgoing edges | Violates the graph-size-independent lookup contract. |
| Async selection | Sequential awaits with short-circuiting | `gather()` competing guards | Runs irrelevant guards and makes timing/side effects part of resolution. |
| Ordered collection | Standard tuple/list operations | `sortedcontainers` or another runtime package | Local groups are small, mutation is cold, and a dependency weakens the minimal-runtime contract. |
| Priority type | Non-boolean `int` | floats, enums, arbitrary comparable keys | Complicates JSON, type checking, NaN/tie semantics, and mypyc without adding useful expressiveness. |
| Dispatch policy | First eligible candidate wins | External telemetry/event arbitration | Recreates transition logic outside the FSM, the problem this milestone exists to remove. |
| Compilation | Keep only `core.py` native | Compile `conditions.py` or diagnostics | Breaks the interpreted user-subclass boundary and adds no justified hot-path benefit. |
| Tooling | Existing pytest/Hypothesis/evidence harness | New benchmarking or FSM framework | Adds maintenance while the current harness already proves pure/native semantics and throughput. |

## What Must Not Be Added

- No new runtime dependency.
- No second candidate-registration API.
- No scheduler, polling loop, heartbeat timer, or telemetry policy that chooses
  transitions; derived facts may remain outside the FSM, but guards and
  precedence belong to the machine.
- No runtime sorting, topology-wide scan, validation call, graph snapshot, or
  diagnostic allocation in `trigger()`.
- No automatic parallel guard evaluation.
- No registration-order or object-identity tie-break.
- No mutable candidate list shared between clones or escaped through snapshots.
- No compilation of `conditions.py`, `condition_templates.py`, diagnostics,
  validation, or visualization.
- No mypyc/build-tool upgrade bundled into the semantic milestone unless native
  compatibility proves the current reviewed pin cannot implement the design.

## Installation

No production installation change is recommended:

```bash
uv sync --all-groups

# Targeted development gates
uv run ruff format --check src/ tests/
uv run ruff check src/ tests/
uv run mypy src/fast_fsm/core.py
uv run pytest tests/ -x -q

# Native compatibility and performance
FAST_FSM_BUILD_MODE=compiled uv run python setup.py build_ext --inplace
uv run python tools/release_evidence.py slots-policy --json
uv run pytest tests/test_performance_benchmarks.py -m slow -x -q
```

The milestone should modify source and tests, not package dependencies or the
lockfile.

## Roadmap Implications

1. **Freeze semantics first:** priority type/default/order, equal-priority
   handling, guard rejection versus exception behavior, and candidate-specific
   declarative/serialization identity.
2. **Change the compiled topology representation:** slotted entry/group,
   atomic registration, lookup/preparation, sync selection, clone, and graph
   snapshot.
3. **Reach parity before adding adapters:** async sequential resolution,
   builder staging/preflight, and declarative handler collections.
4. **Make every projection truthful:** `to_dict`/`from_dict`, diagnostics,
   determinism checks, Mermaid, PlantUML, JSON, docs, and examples.
5. **Close on measured artifacts:** complexity counters, candidate-count
   benchmarks, slots/memory evidence, full suite, docs, and installed pure/native
   conformance.

## Sources

### Repository sources (HIGH confidence)

- `pyproject.toml` — runtime/build dependencies, Python floor, pytest settings
- `setup.py` — selective `core.py` mypyc compilation
- `src/fast_fsm/core.py` — transition storage, sync/async resolution, builder,
  declarative handlers, graph snapshot, clone, and serialization
- `src/fast_fsm/_diagnostics.py`, `validation.py`, and `visualization.py` —
  interpreted snapshot consumers that must preserve candidate multiplicity
- `tests/test_performance_benchmarks.py` and `tools/release_evidence.py` —
  complexity, compiled throughput, slots, and installed-artifact proof
- `.specify/memory/spr-core-api.md` and `docs/dev/architecture.md` — current
  lifecycle, ownership, complexity, and compilation contracts

### External primary sources (MEDIUM confidence via research seam)

- [Python 3.10 `bisect` documentation](https://docs.python.org/3.10/library/bisect.html) — ordered insertion and O(n) `insort` cost
- [Python 3.10 built-in container documentation](https://docs.python.org/3.10/library/stdtypes.html#list.sort) — stable sort and insertion-ordered dictionaries
- [mypyc native classes](https://mypyc.readthedocs.io/en/stable/native_classes.html) — native layouts, generic erasure, interpreted subclasses, and dataclass efficiency caveat
- [mypyc differences from Python](https://mypyc.readthedocs.io/en/stable/differences_from_python.html) — compile-time typing, native runtime checks, early binding, and concurrency cautions
- [python-statemachine transitions](https://python-statemachine.readthedocs.io/en/stable/transitions.html) — ecosystem precedent for one event evaluating ordered guarded alternatives until the first match

## Open Questions for Requirements

- Does an exact duplicate `(source, trigger, priority, target, guard identity)`
  remain an idempotent no-op, or are all repeated priorities errors?
- When `State.can_transition()` or a candidate-specific declarative guard returns
  false, does selection continue to the next candidate? The recommended answer
  is yes: a candidate wins only after all pre-lifecycle eligibility checks pass.
- What exact key addresses candidate guards in `from_dict(..., conditions=...)`?
  A trigger string alone is insufficient once candidates share that trigger.
- Must every competing candidate have an explicit priority, or is the default
  integer accepted? The recommended simple contract is default `0` with equal
  priorities rejected, making unannotated duplicates fail visibly.
