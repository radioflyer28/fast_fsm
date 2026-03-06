# SPR: Validation module

**Category**: validation
**Updated**: 2026-03-06 (added design_style_threshold / min_transitions_for_style)
**Created**: 2026-03-06

- `FSMValidator(fsm, *, name=None)` — base class; `name=` overrides display name stored in `_report_name` slot; all report/display methods use `_report_name`, not `fsm.__class__.__name__`.
- `FSMValidator` provides: `get_adjacency_matrix()`, `validate_completeness()`, `check_determinism()`, `find_unreachable_states()`, `find_dead_states()`, `find_missing_transitions()`, `find_cycles()`, `generate_test_paths()`.
- `get_adjacency_matrix()` returns `{states: [...], events: [...], transitions: [{idx, from_state_idx, from_state, to_state_idx, to_state, event_idx, event}], matrix: N×N}`.
- `EnhancedFSMValidator(fsm, *, name=None, design_style_threshold=0.4, min_transitions_for_style=6)` — analysis + reporting layer; forwards `name=` to super. `design_style_threshold` controls the density cutoff; `min_transitions_for_style` is the minimum *possible* transitions before the heuristic applies (small FSMs always classified as *dense*). Class constants `DEFAULT_DESIGN_STYLE_THRESHOLD` and `DEFAULT_MIN_TRANSITIONS_FOR_STYLE` expose the defaults.
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
