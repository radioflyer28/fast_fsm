# SPR Memory Index

Auto-aggregated from 3 SPR file(s). Last updated: 2026-03-06

---

# SPR: StateMachine core API

**Category**: core-api  
**Created**: 2026-03-06  
**Updated**: 2026-03-06

- `StateMachine` and all hot-path classes use `__slots__`; dynamic attribute assignment on core objects is prohibited.
- Core operations (`trigger`, `can_trigger`, `add_state`, `add_transition`) are O(1) via direct dict lookup; throughput target â‰¥ 250,000 ops/sec.
- `TransitionEntry(to_state, condition)` is the internal container replacing raw dicts; slots-optimised.
- `trigger()` returns `TransitionResult(success, from_state, to_state, trigger, error)`; never raises by default.
- `safe_trigger()` wraps `trigger()` in try/except; never raises under any circumstance.
- `add_transition(trigger, from_state, to_state, condition=None, *, unless=None)` â€” `unless=` is a negation shorthand, mutually exclusive with `condition=`.
- `from_state` accepts a string, `State` object, or list of either; fan-out to multiple sources in one call.
- `add_bidirectional_transition(t1, t2, s1, s2, c1, c2)` registers two directed transitions; thin convenience wrapper, no special internal representation.
- `add_emergency_transition(trigger, to_state)` fans from all current states to one target.
- `add_transitions(list_of_tuples)` batch-registers `(trigger, from, to)` tuples.
- `StateMachine.from_transitions(transitions, initial_state)` classmethod builds a machine from a flat list.
- `is_in(state)` â€” O(1) identity/name check against `_current_state`.
- `can_trigger(trigger)` â€” evaluates guard condition synchronously before committing; use for pre-flight checks.
- Listener protocol: objects with `on_exit_state`, `on_enter_state`, `after_transition` methods; registered via `add_listener(*listeners)`.
- `AsyncStateMachine` subclasses `StateMachine`; adds `trigger_async` and `can_trigger_async`; auto-detects `AsyncCondition`.
- `FSMBuilder` fluent builder; auto-detects async requirement from states/conditions; `force_async()` / `force_sync()` override; `build()` is idempotent.
- `CallbackState` extends `State` with `_on_enter` / `_on_exit` slots; use when state-level callbacks needed without losing slots optimisation.
- `DeclarativeState` enables `@transition`-decorated methods on state classes; auto-discovers via `_discover_handlers()`.
- mypyc compiles `core.py` only; `conditions.py` and `condition_templates.py` must stay interpreted (users subclass `Condition` from Python).
- `_sanitize_condition_kwargs` strips private kwargs (leading `_`) and caps at 50 items before passing to conditions.

---

# SPR: Validation module

**Category**: validation  
**Created**: 2026-03-06  
**Updated**: 2026-03-06

- `FSMValidator(fsm, *, name=None)` â€” base class; `name=` overrides display name stored in `_report_name` slot; all report/display methods use `_report_name`, not `fsm.__class__.__name__`.
- `FSMValidator` provides: `get_adjacency_matrix()`, `validate_completeness()`, `check_determinism()`, `find_unreachable_states()`, `find_dead_states()`, `find_missing_transitions()`, `find_cycles()`, `generate_test_paths()`.
- `get_adjacency_matrix()` returns `{states: [...], events: [...], transitions: [{idx, from_state_idx, from_state, to_state_idx, to_state, event_idx, event}], matrix: NÃ—N}`.
- `EnhancedFSMValidator(fsm, *, name=None)` â€” analysis + reporting layer; forwards `name=` to super.
- `design_style` auto-classified in `_analyze_structure`: `"sparse"` when `density < 0.4 AND possible_transitions > 6`, else `"dense"`.
- Split scoring: `structural_score` covers reachability/dead-ends/determinism; `completeness_score` covers transition coverage; `overall_score` mirrors `structural_score`; `grade` based on structural only.
- Missing-transition issues emitted as `"info"` severity for sparse FSMs, `"warning"` for dense; never affect `structural_score`.
- `get_validation_score()` returns `{structural_score, completeness_score, design_style, overall_score, grade}`; grade âˆˆ {A, B, C, D}.
- `_export_json()` includes `design_style`, `states`, `events`, `transitions`, `adjacency_matrix` fields.
- `_export_markdown()` renders two score rows with sparse/dense contextual note.
- `print_enhanced_report()` shows design style icon + two score lines.
- Validation module is design-time only; zero runtime overhead on FSMs that don't use it.
- `ValidationIssue(severity, category, message)` â€” severity âˆˆ {error, warning, info, debug}.
- Upper-triangular matrix was rejected: directed graphs have cycles and asymmetric edges; full NÃ—N adjacency matrix used instead (ADR-001).
- User-annotation for sparsity (`sparse=True` flag) was rejected: users don't self-identify; auto-detection preferred (ADR-001).

---

# SPR: Visualization module

**Category**: visualization  
**Created**: 2026-03-06  
**Updated**: 2026-03-06

- `visualization.py` has zero import dependency on `validation.py`; adjacency data passed as a plain `dict`, never as validator objects.
- `to_mermaid(fsm, *, title=None, show_conditions=True)` â€” returns raw Mermaid `stateDiagram-v2` string, no fences.
- `to_mermaid_fenced(fsm, *, title=None, show_conditions=True)` â€” wraps `to_mermaid()` output in ` ```mermaid ` fences; suitable for embedding in Markdown.
- `to_mermaid_document(fsm, *, title=None, show_conditions=True, adjacency_matrix=None)` â€” full `.md` document with H1 title, fenced diagram, and optional adjacency tables.
- When `adjacency_matrix` dict is supplied to `to_mermaid_document`, it appends an NÃ—N adjacency table and a numbered transitions index table.
- `adjacency_matrix` dict format matches `FSMValidator.get_adjacency_matrix()` output: `{states, events, transitions, matrix}`.
- All three functions exported from `fast_fsm.__init__`; importable as `from fast_fsm import to_mermaid_document`.
- Typical pipeline: `matrix = FSMValidator(fsm).get_adjacency_matrix(); doc = to_mermaid_document(fsm, adjacency_matrix=matrix)`.

