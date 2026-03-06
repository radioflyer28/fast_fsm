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

Use `FSMValidator.get_adjacency_matrix()` to get a stable, index-ordered
representation of the FSM graph suitable for tooling or passing to
{func}`~fast_fsm.to_mermaid_document`:

```python
from fast_fsm.validation import FSMValidator

adj = FSMValidator(fsm).get_adjacency_matrix()
# adj["states"]      — alphabetically sorted list of state names
# adj["events"]      — alphabetically sorted list of event names
# adj["transitions"] — flat list of {idx, from_state, to_state, event, ...}
# adj["matrix"]      — N×N list-of-lists; matrix[i][j] = [transition_idx, ...]
```

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
