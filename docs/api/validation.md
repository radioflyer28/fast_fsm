# Validation API

Design-time analysis tools for FSM quality. These add **zero runtime
overhead** to FSMs that don't use them.

## Sparse vs. Dense Scoring

`EnhancedFSMValidator` automatically classifies your FSM as **sparse** or
**dense** based on transition density (defined transitions ÷ possible
state×event pairs).

- **Dense** — grade and `overall_score` reflect all issues including missing
  transitions.
- **Sparse** — `overall_score` and `grade` are based on **structural** health
  only (reachability, determinism, dead states). Missing-transition issues are
  downgraded to `info` and reported separately in `completeness_score`.

This means an intentionally sparse FSM — one where not every state handles
every event by design — receives a fair structural grade instead of a
misleading *D* for transition coverage.

```python
from fast_fsm import EnhancedFSMValidator, StateMachine

fsm = StateMachine.quick_build(
    "idle",
    [
        ("start", "idle", "running"),
        ("pause", "running", "paused"),
        ("resume", "paused", "running"),
        ("stop", "running", "idle"),
        ("error", "running", "error"),
        ("reset", "error", "idle"),
    ],
    name="MyFSM",
)

v = EnhancedFSMValidator(fsm)
score = v.get_validation_score()
print(score["design_style"])        # "sparse"
print(score["structural_score"])    # reflects only reachability, determinism etc.
print(score["completeness_score"])  # reflects transition coverage
print(score["grade"])               # based on structural_score only
```

## Tuning the Validator

`EnhancedFSMValidator` exposes three keyword-only constructor parameters that
let you adapt the sparse/dense classification and scoring to your FSM's design.

### Sparse/dense classification thresholds

| Parameter | Default | Effect |
|---|---|---|
| `design_style_threshold` | `0.4` | Density ratio below which an FSM is classified as *sparse*. Set to `0.0` to force *sparse*; `1.1` to force *dense*. |
| `min_transitions_for_style` | `6` | Minimum possible transitions (`states × events`) before the heuristic applies. Small FSMs below this are always treated as *dense*. |

```python
# Force dense classification regardless of density
v = EnhancedFSMValidator(fsm, design_style_threshold=1.1)
score = v.get_validation_score()
print(score["design_style"])  # "dense"
```

### Blending completeness into the overall score

By default `overall_score` and `grade` use only the **structural score** for
all FSMs. For dense FSMs where transition coverage matters, you can blend in
`completeness_score` with `completeness_weight`:

```python
# overall_score = 0.8 * structural + 0.2 * completeness
v = EnhancedFSMValidator(fsm, completeness_weight=0.2)
score = v.get_validation_score()
print(score["overall_score"])       # blended
print(score["structural_score"])    # always raw
print(score["completeness_score"])  # always raw
print(score["grade"])               # derived from blended overall_score
```

Sparse FSMs ignore `completeness_weight` — missing transitions are expected in
sparse designs and are never penalised in the final grade.

`completeness_weight` must be in `[0.0, 1.0]`; a `ValueError` is raised
otherwise.

## Adjacency Matrix

Use `FSMValidator.get_adjacency_matrix()` to get a stable, snapshot-ordered
representation of the FSM graph suitable for tooling or passing to
{func}`~fast_fsm.to_mermaid_document`:

```python
from fast_fsm.validation import FSMValidator

adj = FSMValidator(fsm).get_adjacency_matrix()
# adj["states"]      — snapshot-ordered list of state names
# adj["events"]      — deterministically ordered list of event names
# adj["transitions"] — flat list of {idx, from_state, to_state, event, ...}
# adj["matrix"]      — N×N list-of-lists; matrix[i][j] = [transition_idx, ...]
```

## Bounded Snapshot Diagnostics

`FSMValidator(fsm, *, name=None, limits=None)` and
`EnhancedFSMValidator(fsm, *, name=None, design_style_threshold=0.4,
min_transitions_for_style=6, completeness_weight=0.0, limits=None)` capture
one private immutable graph snapshot at construction. Every nested helper uses
that capture and its one shared budget; it never rereads live topology. The
declared initial state is the reachability root and is reported separately
from the captured current state.

`DiagnosticLimits` is a frozen, slotted keyword-only budget object with these
finite integer defaults:

| Field | Default | Counted boundary |
|---|---:|---|
| `max_work` | 50,000 | visits, edge examinations, and other diagnostic work |
| `max_results` | 10,000 | emitted analysis results |
| `max_dense_cells` | 200,000 | complete dense cells before allocation |
| `max_path_expansions` | 20,000 | followed generated-path edges |

All fields must be non-negative integers (not `bool`). These limits are not
timeouts. A status is the frozen scalar `DiagnosticStatus(complete,
exhausted_dimension, exhausted_stage, work_count, result_count,
dense_cell_count, path_expansion_count)`. A structured report carries its
`diagnostic_status`; a legacy set/list/scalar/printing/dense-matrix method
raises `DiagnosticBudgetExceeded(status)` with the fixed message
`diagnostic budget exhausted` before it can return a partial value.

`validate_completeness(*, limits=None, include_dense=False)` returns
`fsm_name`, `total_states`, `total_events`, `total_transitions`,
`initial_state`, `current_state`, `unreachable_states`, `dead_states`,
`missing_transitions`, `is_complete`, `is_reachable`, `has_dead_states`,
`cyclic_components`, flattened `states_in_cycles`, `structural_depth`,
`depth_interpretation`, `sparse_adjacency`, and `diagnostic_status`. It adds
`transition_matrix` only when `include_dense=True`. `get_sparse_adjacency(*,
limits=None)` is the normal `O(V + E)` result with snapshot-ordered `states`,
ordered `events`, and ordered `edges`. `get_transition_matrix(*, limits=None)`
preflights `V × events`, and `get_adjacency_matrix(*, limits=None)` preflights
`V²`, before allocating either compatibility shape.

`find_cycles(*, limits=None)` is a path-shaped compatibility view derived from
iterative SCC membership. SCCs include every member of a self-loop or larger
cycle exactly once in deterministic snapshot order. `structural_depth` is
computed with iterative dynamic programming: `depth_interpretation` is
`dag_longest_path` for an acyclic graph and `condensation_dag_depth` for a
cyclic graph. The latter is deliberately not an exact simple-path claim
inside an SCC. `generate_test_paths(max_length=10, max_paths=50, *,
max_expansions=None, limits=None)` uses iterative DFS; its requested length
and path caps are separate from shared work/result and expansion budgets.

## Position-Safe Comparison and Batch Schemas

`compare_fsms(*fsms, limits=None)` validates each input once and returns:

```text
{
  "entries": [{"position", "name", "score", "metrics", "issue_count",
               "diagnostic_status"}, ...],
  "rankings": [{"position", "name", "score"}, ...],
  "best_fsm": {"position", "name"} | None,
  "comparison_metrics": {"count", "avg_score", "score_range",
                         "total_issues", "diagnostic_status"},
}
```

`position` is the zero-based identity. Duplicate and empty names are labels,
not keys; stable ties sort by descending score and then ascending `position`.
For no inputs, `entries` and `rankings` are empty, `best_fsm` is `None`,
`count` and `total_issues` are `0`, and `avg_score` and `score_range` are
`None`.

`batch_validate(*fsms, show_summary=True, limits=None)` returns
`{count, entries, diagnostic_status}` where each ordered entry is
`{position, name, validator, diagnostic_status}`. It preserves every input,
including duplicate labels. Each supplied `limits` value is independently
applied to each one-capture input; aggregate status preserves the first
exhaustion boundary and sums deterministic counters.

## Validators

```{eval-rst}
.. autoclass:: fast_fsm.FSMValidator
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: fast_fsm.EnhancedFSMValidator
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: fast_fsm.ValidationIssue
   :members:
   :undoc-members:
```

## Convenience Functions

```{eval-rst}
.. autofunction:: fast_fsm.validate_fsm

.. autofunction:: fast_fsm.quick_validation_report

.. autofunction:: fast_fsm.enhanced_validate_fsm

.. autofunction:: fast_fsm.quick_health_check

.. autofunction:: fast_fsm.validate_and_score

.. autofunction:: fast_fsm.compare_fsms

.. autofunction:: fast_fsm.batch_validate

.. autofunction:: fast_fsm.fsm_lint
```
