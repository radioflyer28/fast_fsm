# SPR: Validation module

**Category**: validation
**Updated**: 2026-03-06 (added design_style_threshold / min_transitions_for_style / completeness_weight)
**Created**: 2026-03-06

- `FSMValidator(fsm, *, name=None, limits=None)` — base class; `name=` overrides display name stored in `_report_name` slot; all report/display methods use `_report_name`, not `fsm.__class__.__name__`. A supplied `DiagnosticLimits` becomes its shared ledger for nested graph work.
- `FSMValidator` provides sparse-first `get_sparse_adjacency()`, plus compatibility `get_transition_matrix(*, limits=None)` and `get_adjacency_matrix(*, limits=None)`, `validate_completeness(*, limits=None, include_dense=False)`, `check_determinism()`, `find_unreachable_states()`, `find_dead_states()`, `find_missing_transitions()`, `find_cycles()`, and `generate_test_paths(max_length=10, max_paths=50, *, max_expansions=None, limits=None)`.
- Sparse adjacency is the default report representation: `{states: snapshot-order tuple, events: ordered tuple, edges: ordered edge rows}`. It is O(V+E) and never allocates a V² matrix; `validate_completeness(include_dense=True)` is the explicit compatibility opt-in.
- `get_transition_matrix()` preflights and reserves exactly V×events `max_dense_cells` before building its outer nested mapping; `get_adjacency_matrix()` preflights and reserves exactly V² cells before constructing its outer list. Both return the existing stable matrix schemas and raise `DiagnosticBudgetExceeded` before allocation when one-less.
- `generate_test_paths()` uses iterative DFS frames. `max_length` and positional `max_paths` are explicit request caps; every followed edge reserves `max_path_expansions` and `max_work`, and every copied/appended path reserves `max_results`. Budget exhaustion raises rather than returning a partial legacy list.
- `EnhancedFSMValidator(fsm, *, name=None, design_style_threshold=0.4, min_transitions_for_style=6, completeness_weight=0.0)` — analysis + reporting layer; forwards `name=` to super. `design_style_threshold` controls the density cutoff; `min_transitions_for_style` is the minimum *possible* transitions before the heuristic applies (small FSMs always classified as *dense*). Class constants `DEFAULT_DESIGN_STYLE_THRESHOLD`, `DEFAULT_MIN_TRANSITIONS_FOR_STYLE`, and `DEFAULT_COMPLETENESS_WEIGHT` expose the defaults.
- `completeness_weight` (0.0–1.0): weight blended into `overall_score` and `grade` for **dense** FSMs only — `overall_score = (1-w)*structural + w*completeness`. Sparse FSMs always use pure structural score regardless of weight. Default `0.0` preserves backward compatibility. Raises `ValueError` outside `[0.0, 1.0]`.
- `design_style` auto-classified in `_analyze_structure`: `"sparse"` when `density < threshold AND possible_transitions > min_guard`, else `"dense"`.
- Split scoring: `structural_score` covers reachability/dead-ends/determinism; `completeness_score` covers transition coverage; `overall_score` mirrors `structural_score`; `grade` based on structural only.
- Missing-transition issues emitted as `"info"` severity for sparse FSMs, `"warning"` for dense; never affect `structural_score`.
- `get_validation_score()` returns `{structural_score, completeness_score, design_style, overall_score, grade}`; grade ∈ {A, B, C, D}.
- `_export_json()` includes `design_style`, `states`, `events`, `transitions`, `adjacency_matrix` fields.
- `_export_markdown()` renders two score rows with sparse/dense contextual note.
- `print_enhanced_report()` shows design style icon + two score lines.
- Validation module is design-time only; zero runtime overhead on FSMs that don't use it.
- `ValidationIssue(severity, category, message)` — severity ∈ {error, warning, info, debug}.
- Upper-triangular matrix was rejected: directed graphs have cycles and asymmetric edges; full N×N adjacency matrix used instead (ADR-001).
- User-annotation for sparsity (`sparse=True` flag) was rejected: users don't self-identify; auto-detection preferred (ADR-001).
- Phase 19 validators capture one scalar graph snapshot and thread one shared `DiagnosticLimits` ledger through graph helpers. Legacy list/scalar helpers raise the fixed-message `DiagnosticBudgetExceeded` rather than return a partial result.
- `_strongly_connected_components()` is iterative Kosaraju over snapshot-ordered forward/reverse adjacency. It returns every cyclic SCC exactly once: components and members are ordered by lowest snapshot index; size-one SCCs appear only for self-loops.
- SCC traversal reserves `max_work` before forward/reverse vertex visits and edge examinations, and reserves `max_results` before publishing canonical cyclic membership. Exact limits succeed; one-less limits fail before the next action with scalar status metadata.
- `_structural_depth()` uses an iterative topological dynamic program over deduplicated SCC-condensation edges. It reports `dag_longest_path` for acyclic graphs and `condensation_dag_depth` for cyclic graphs; the latter never promises a longest simple path inside an SCC.
- `FSMValidator.find_cycles()` remains a path-shaped compatibility adapter, but it derives its deterministic closed representatives from the canonical iterative SCC membership; `EnhancedFSMValidator._find_longest_path()` consumes the structural-depth adapter.
- Calibrated finite defaults are `max_work=50_000`, `max_results=10_000`, `max_dense_cells=200_000`, and `max_path_expansions=20_000`: enough for the longest ordinary diagnostics fixture with documented headroom, while generated adversarial graphs deterministically exhaust by exact counters rather than elapsed time.
