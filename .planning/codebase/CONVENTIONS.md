<!-- refreshed: 2026-08-29 -->
# Coding Conventions

**Analysis Date:** 2026-08-29

**Assessment Basis:** Independent comparison of written project rules with the
actual signatures, control flow, tests, and locally executed quality gates.

## Naming Patterns

**Files:**
- Use lowercase `snake_case.py` for implementation and test modules, for example `src/fast_fsm/condition_templates.py` and `tests/test_condition_templates.py`.
- Use uppercase names only for repository-level documentation and metadata files; package modules do not use them.

**Functions:**
- Use lowercase `snake_case` for public functions, methods, and private helpers: `StateMachine.add_transition()` and `StateMachine._resolve_trigger()` in `src/fast_fsm/core.py`.
- Prefix implementation-only helpers and attributes with one underscore, such as `_sanitize_condition_kwargs()` and `_current_state` in `src/fast_fsm/core.py`.
- Use factory names that describe the construction shortcut, such as `simple_fsm()`, `quick_fsm()`, `StateMachine.from_states()`, and `StateMachine.quick_build()`.

**Variables:**
- Use descriptive lowercase `snake_case` locals (`initial_state`, `from_state`, `condition_result`).
- Use short names only for tightly scoped iteration (`i`, `t`, `e`) or conventional values (`fsm`, `cb`).
- Keep callback and guard call signatures permissive with `*args, **kwargs` as
  required by `.github/copilot-instructions.md`. The current guard hierarchy in
  `src/fast_fsm/conditions.py` implements only `**kwargs`; passing positional
  context through a guarded transition is a confirmed defect, not a convention
  to copy.

**Types:**
- Use PascalCase for classes and exceptions: `StateMachine`, `AsyncStateMachine`, `FSMBuilder`, `TransitionResult`, and `TransitionError`.
- Use singular descriptive nouns for domain types (`Condition`, `State`, `TransitionRecord`) and suffix validation result types with `Issue` where appropriate (`ValidationIssue` in `src/fast_fsm/validation.py`).
- Use `Optional`, `Union`, `Dict`, `List`, and `Tuple` in the older/public API portions of `src/fast_fsm/core.py`; newer code also uses built-in generics such as `list[str]` and `set[str]`. Match the surrounding module when extending it.

## Code Style

**Formatting:**
- Use 4-space indentation, standard Python block layout, and an 88-character line target. Formatting is run with `uv run ruff format src/ tests/` through `Taskfile.yml`.
- Keep module, class, and public method docstrings close to the implementation. Public API docstrings generally use Google-style `Args`, `Returns`, `Raises`, and `Example` sections, as in `StateMachine.from_dict()` in `src/fast_fsm/core.py`.
- Use `@dataclass(slots=True)` for small record-like values (`TransitionResult` in `src/fast_fsm/core.py`) and `__slots__` for hot-path/domain objects (`State`, `StateMachine`, and condition classes).
- Preserve selective mypyc annotations on user-subclassable core classes (`@mypyc_attr(allow_interpreted_subclasses=True)` in `src/fast_fsm/core.py`). New classes on the compiled boundary must follow the corresponding safety test in `tests/test_mypyc_guard.py`.

**Linting:**
- Ruff is the project formatter/linter and type validation uses `ty`; the operational commands are `uv run ruff check src/ tests/` and `uv run ty check src/` in `Taskfile.yml` and `.github/copilot-instructions.md`.
- No `[tool.ruff]` section is present in `pyproject.toml`; use the repository commands and existing style rather than introducing a new lint configuration casually.
- The project runs on Python `>=3.10` according to `pyproject.toml`; keep public annotations compatible with that minimum unless the package requirement is deliberately changed.
- Current gate state is not an example of the desired convention: on
  2026-08-29, `ty` passed, but `ruff format --check` reported
  `src/fast_fsm/visualization.py` and `ruff check` reported the unused `fsm`
  assignment at `tests/test_advanced_functionality.py:1488`.

## Import Organization

**Order:**
1. Standard-library imports (`logging`, `time`, `asyncio`, `typing`, `dataclasses`, `collections`).
2. Third-party imports (`pytest`, `hypothesis`, `mypy_extensions`).
3. Local package imports (`from .conditions ...`, `from fast_fsm.core ...`).

The dominant order appears in `src/fast_fsm/conditions.py`, `tests/test_async.py`, and `tests/test_validation.py`. A few existing modules, notably `src/fast_fsm/condition_templates.py` and `tests/test_safety_kwargs.py`, have imports out of that order; preserve the local file carefully and let Ruff format/check determine whether a touched block needs cleanup.

**Path Aliases:**
- No path aliases are configured or used. Package-relative imports are used inside `src/fast_fsm/`, while tests import public symbols from `fast_fsm` or focused modules such as `fast_fsm.core` and `fast_fsm.conditions`.

## Error Handling

**Patterns:**
- Return a `TransitionResult(success=False, error=...)` for expected runtime transition failures: unknown triggers, wrong source states, rejected guards, and rejected state transitions in `src/fast_fsm/core.py`.
- Raise `ValueError`, `TypeError`, or `KeyError` for invalid construction/configuration inputs, such as malformed `from_dict()` data and invalid transition conditions. Tests assert both exception type and message fragments with `pytest.raises(..., match=...)` in `tests/test_boundary_negative.py` and `tests/test_advanced_functionality.py`.
- Use `TransitionResult.raise_if_failed()` when callers explicitly want exception-style control flow; it raises the domain-specific `TransitionError` while retaining the original result.
- Isolate guard failures by returning a failed result; isolate lifecycle callback
  failures by logging and continuing. Do not describe those policies as
  equivalent: callback failure may still yield a successful transition after
  state mutation. `State.can_transition()` exceptions are not caught by
  `trigger()` and reach `safe_trigger()` or the caller.
- Use `safe_trigger()` in `src/fast_fsm/core.py` as the last-resort API boundary that converts unexpected exceptions into failed results. Do not add validation work to the hot `trigger()` path without a measured reason.

## Logging

**Framework:** Python standard-library `logging`, with per-machine/per-state loggers created in `src/fast_fsm/core.py`.

**Patterns:**
- Obtain named loggers with `logging.getLogger(...)`; use parameterized logger messages (`logger.debug("...%s", value)`) rather than eagerly interpolated strings in hot paths.
- Use `debug` for dispatch/condition details, `info` for successful builder/setup events, `warning` for user callback/guard failures, and `error` for failures at callback or `safe_trigger()` barriers.
- Configure logging through `configure_fsm_logging()` or `set_fsm_logging_level()` in `src/fast_fsm/core.py`; tests observe records with pytest’s `caplog` fixture in `tests/test_logging_config.py` and `tests/test_safety_kwargs.py`.
- Keep normal library behavior quiet: direct `print()` calls are confined to demos/reporting paths such as `src/fast_fsm/condition_templates.py` and `src/fast_fsm/validation.py`.

## Comments

**When to Comment:**
- Comment performance-sensitive choices, compilation boundaries, callback ordering, and deliberate exception barriers. Representative comments are adjacent to slots/listener setup in `src/fast_fsm/core.py` and the mypyc guard rationale in `tests/test_mypyc_guard.py`.
- Use section divider comments in long modules and test modules to group helpers, fixtures, and feature families; examples include `tests/test_builder.py` and `tests/test_validation.py`.
- Prefer comments that explain why behavior is constrained. Keep comments synchronized with implementation; stale behavior comments are treated as defects by the project constitution in `.specify/memory/constitution.md`.

**JSDoc/TSDoc:**
- Not applicable; this is a Python package. Use Python docstrings instead.
- Public functions/classes should have a concise summary and, where useful, Google-style argument/return/raise documentation. Internal underscore helpers generally have at least a one-line docstring when their behavior is non-obvious.

## Function Design

**Size:**
- Keep hot-path operations shallow and O(1), especially `trigger()`, `can_trigger()`, `add_state()`, and `add_transition()` in `src/fast_fsm/core.py`. Move design-time analysis into `src/fast_fsm/validation.py` rather than adding it to dispatch.
- `src/fast_fsm/core.py` is intentionally a large cohesive module; use nearby helpers and existing layer boundaries before creating another abstraction.

**Parameters:**
- Use keyword-only options for configuration that should not be confused with positional state/transition data, as in `StateMachine.__init__()` and `StateMachine.from_dict()`.
- Preserve flexible callback/condition parameters (`*args, **kwargs`) as the
  intended compatibility contract, and add parity tests whenever modifying
  sync/async dispatch. Accept both domain objects and names only where endpoint
  registration remains valid; the current ability to attach an unregistered
  `State` target is an invariant bug, not an extension pattern.
- For builder APIs, return `self` to support fluent chaining; follow `FSMBuilder.add_state()`, `add_transition()`, and callback registration methods.

**Return Values:**
- Return explicit domain values (`TransitionResult`, `bool`, `List[str]`, or typed dictionaries) and document unusual normalization behavior. Declarative handlers normalize `None`, `bool`, and `TransitionResult` in `DeclarativeState.handle_event()` in `src/fast_fsm/core.py`.
- Return copies for exposed mutable state/history snapshots where the surrounding API promises isolation (`StateMachine.history()` and `snapshot()` in `src/fast_fsm/core.py`).

## Module Design

**Exports:**
- Add public symbols to the package-level re-export list and `__all__` in `src/fast_fsm/__init__.py`; validation also maintains an explicit `__all__` in `src/fast_fsm/validation.py`.
- Keep the implementation dependency direction simple: `core.py` imports
  conditions, validation imports the core, and visualization avoids a top-level
  validation import. Do not introduce a reverse import from conditions or core
  into design-time modules.

**Barrel Files:**
- `src/fast_fsm/__init__.py` is the sole package-level barrel/re-export module. There are no per-subdirectory barrel files.
- Tests import through `fast_fsm` for public API examples and through focused modules when testing internals or specialized classes. Follow the same distinction in new tests.

---

*Convention analysis: 2026-08-29*
