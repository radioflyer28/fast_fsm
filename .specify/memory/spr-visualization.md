# SPR: Visualization module

**Category**: visualization  
**Created**: 2026-03-06  
**Updated**: 2026-03-06

- `visualization.py` has zero import dependency on `validation.py`; adjacency data passed as a plain `dict`, never as validator objects.
- `to_mermaid(fsm, *, title=None, show_conditions=True)` — returns raw Mermaid `stateDiagram-v2` string, no fences.
- `to_mermaid_fenced(fsm, *, title=None, show_conditions=True)` — wraps `to_mermaid()` output in ` ```mermaid ` fences; suitable for embedding in Markdown.
- `to_mermaid_document(fsm, *, title=None, show_conditions=True, adjacency_matrix=None)` — full `.md` document with H1 title, fenced diagram, and optional adjacency tables.
- When `adjacency_matrix` dict is supplied to `to_mermaid_document`, it appends an N×N adjacency table and a numbered transitions index table.
- `adjacency_matrix` dict format matches `FSMValidator.get_adjacency_matrix()` output: `{states, events, transitions, matrix}`.
- All three functions exported from `fast_fsm.__init__`; importable as `from fast_fsm import to_mermaid_document`.
- Typical pipeline: `matrix = FSMValidator(fsm).get_adjacency_matrix(); doc = to_mermaid_document(fsm, adjacency_matrix=matrix)`.
