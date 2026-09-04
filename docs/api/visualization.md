# Visualization API

Utilities for generating diagram output from a `StateMachine`.  Import
only when you need diagrams — this module adds **zero overhead** to the
core runtime.

## Functions

```{eval-rst}
.. autofunction:: fast_fsm.to_mermaid
```

```{eval-rst}
.. autofunction:: fast_fsm.to_mermaid_fenced
```

```{eval-rst}
.. autofunction:: fast_fsm.to_mermaid_document
```

```{eval-rst}
.. autofunction:: fast_fsm.to_plantuml
```

```{eval-rst}
.. autofunction:: fast_fsm.to_json
```

## Usage Notes

## Snapshot, Budget, and Encoding Contract

Every public renderer captures one immutable graph snapshot and threads one
`DiagnosticLimits` budget through its private composition. `to_mermaid()`,
`to_plantuml()`, and `to_mermaid_fenced()` have the signature `(fsm, *,
title=None, show_conditions=True, limits=None)`. `to_mermaid_document(fsm,
*, title=None, show_conditions=True, adjacency_matrix=None,
include_adjacency=False, limits=None)` adds explicit dense-document controls.
`to_json(fsm, *, limits=None, include_adjacency=False)` returns the same
one-snapshot topology plus analysis. Fenced and Markdown document helpers
compose from private snapshot renderers; they do not call a public renderer
and recapture. The shared finite limits are `max_work=50_000`,
`max_results=10_000`, `max_dense_cells=200_000`, and
`max_path_expansions=20_000`. Exhaustion raises the fixed-message
`DiagnosticBudgetExceeded` rather than returning a partial diagram, document,
or JSON payload.

Node identity is always the opaque snapshot-position ID `s0`, `s1`, … . A
label is display data, never an identifier, so empty labels and labels that
sanitize to the same characters remain collision-free. Ordering follows the
captured snapshot and is byte-stable when that snapshot is reused. There is no
parser-validation promise and no condition object is evaluated, stringified,
or `repr`-formatted while rendering.

Each output grammar has an independent final-sink boundary. Mermaid encoding
handles diagram titles, state labels, triggers, and scalar condition names for
Mermaid syntax; PlantUML encoding does the same for PlantUML syntax; Markdown
heading and table-cell encoding is separate again. All make caller text a
single inert physical line, so controls, quotes, brackets, comment markers,
directives, fences, Unicode, and punctuation cannot become grammar syntax.

`to_json()` returns snapshot-ordered `topology` with `states`, declared
`initial`, runtime `current`, `transitions`, and sparse `sparse_adjacency`.
Its `analysis` contains `reachability`, `cycles`, `cyclic_components`,
`structural_depth`, `depth_interpretation`, scalar `diagnostic_status`, and
`quality`. Sparse adjacency is the default `O(V + E)` representation. Set
`include_adjacency=True` only when a dense `V²` matrix is required; it is
preflighted against `max_dense_cells` before allocation. A cyclic depth uses
`condensation_dag_depth`, not an exact simple longest path.

`to_mermaid_document(..., adjacency_matrix=None, include_adjacency=False,
limits=None)` omits dense data by default. When supplied, `adjacency_matrix`
must exactly match the captured snapshot's ordered states, events,
transitions, and every matrix cell. Missing, stale, reordered, or partial data
raises `ValueError("adjacency matrix does not match captured snapshot")`; the
renderer does not merge or hide incompatible output. A direct dense request
uses `include_adjacency=True` and the same preflighted budget.

### Diagram only

```python
from fast_fsm import StateMachine, to_mermaid

fsm = StateMachine.quick_build(
    "idle",
    [("start", "idle", "running"), ("stop", "running", "idle")],
    name="Demo",
)
print(to_mermaid(fsm))
```

### Markdown-fenced block (for embedding in `.md` files)

```python
from fast_fsm import to_mermaid_fenced

print(to_mermaid_fenced(fsm))
# ```mermaid
# stateDiagram-v2
#     [*] --> idle
#     ...
# ```
```

### Full document with adjacency matrix

Pass the result of {meth}`~fast_fsm.FSMValidator.get_adjacency_matrix`
to include a full state-adjacency table and numbered transitions list.
The ``visualization`` module has **no import dependency** on
``validation`` — the adjacency data is passed as a plain ``dict``.

```python
from fast_fsm import to_mermaid_document
from fast_fsm.validation import FSMValidator

adj = FSMValidator(fsm).get_adjacency_matrix()
doc = to_mermaid_document(fsm, adjacency_matrix=adj)
print(doc)
```
