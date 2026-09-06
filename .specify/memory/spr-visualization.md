# SPR: Visualization module

**Category**: visualization  
**Created**: 2026-03-06  
**Updated**: 2026-09-03

- `visualization.py` has no module-import dependency on `validation.py`; the legacy quality adapter imports it lazily while adjacency data remains a plain `dict`, never a validator object.
- `to_mermaid(fsm, *, title=None, show_conditions=True, limits=None)` — returns raw Mermaid `stateDiagram-v2` string, no fences.
- `to_mermaid_fenced(fsm, *, title=None, show_conditions=True, limits=None)` — wraps one private Mermaid render in ` ```mermaid ` fences; suitable for embedding in Markdown.
- `to_mermaid_document(fsm, *, title=None, show_conditions=True, adjacency_matrix=None, include_adjacency=False, limits=None)` — full `.md` document with H1 title, fenced diagram, and opt-in/validated adjacency tables.
- `to_json(fsm, *, limits=None, include_adjacency=False)` — returns sparse JSON-ready topology plus bounded structured analysis; dense adjacency requires the explicit flag.
- When `adjacency_matrix` dict is supplied to `to_mermaid_document`, it appends an N×N adjacency table and a numbered transitions index table.
- `adjacency_matrix` dict format matches `FSMValidator.get_adjacency_matrix()` output: `{states, events, transitions, matrix}`.
- All three functions exported from `fast_fsm.__init__`; importable as `from fast_fsm import to_mermaid_document`.
- Typical pipeline: `matrix = FSMValidator(fsm).get_adjacency_matrix(); doc = to_mermaid_document(fsm, adjacency_matrix=matrix)`.
- Mermaid and PlantUML allocate every node ID as `s{snapshot_position}` from the immutable captured graph; a state label is display data only, even when it is empty or already identifier-safe.
- `_escape_mermaid_text()` and `_escape_plantuml_text()` are independent final-sink allowlist encoders. They keep titles, state labels, triggers, and scalar condition names on one physical line and encode caller punctuation, controls, and Unicode before grammar emission.
- `to_mermaid()` and `to_plantuml()` capture exactly one graph snapshot, create one diagnostic budget, and delegate to private `*_from_snapshot` renderers. Their bytes follow snapshot state/edge order and are stable when that snapshot is reused.
- Diagram rendering consumes only snapshot scalar condition names; it never evaluates, stringifies, or reprs a condition object.
- `to_json()` captures once and returns snapshot-ordered topology with declared `initial`, separate runtime `current`, sparse adjacency, SCC membership, structural depth plus interpretation, and scalar `diagnostic_status`; exhaustion is explicit rather than a `quality=None` fallback.
- `to_mermaid_fenced()` and `to_mermaid_document()` compose private from-snapshot helpers, so fences and documents do not call public renderers or recapture. Markdown headings and table cells use their own inert one-line encoders; fenced content is the already-rendered Mermaid string.
- Dense adjacency is absent from JSON and documents by default. `include_adjacency=True` reserves dense cells before allocation; a caller-supplied `adjacency_matrix` must fully match states, edges, events, and every matrix cell of the captured graph or raises `ValueError("adjacency matrix does not match captured snapshot")`.
