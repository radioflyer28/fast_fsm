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
