# Phase 12: Timing Condition Implementation - Context

**Gathered:** 2026-04-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement three timing condition classes (`TimeoutCondition`, `CooldownCondition`, `ElapsedCondition`) in `condition_templates.py` and export them from `fast_fsm.__init__`. These are `Condition` subclasses that use `time.monotonic()` for platform-safe time checks and follow the library's `__slots__` convention.

</domain>

<decisions>
## Implementation Decisions

### Timeout Semantics & Edge Cases
- `TimeoutCondition.check()` returns `True` before timeout expires (transition allowed), `False` after (blocks) — per TIME-01
- `CooldownCondition` tracks "last successful check" internally — `check()` records `time.monotonic()` each time it returns `True`
- Conditions are reusable across multiple transitions — a single instance can guard multiple transitions
- Construction time is the default reference — `_ref = time.monotonic()` set in `__init__` (no need for explicit `reset()` before first use)

### Constructor & API Design
- Parameter name: `seconds: float` — matches `time.sleep()` convention
- Auto-generate `name` and `description` from class name + threshold value (e.g., `timeout_5.0`, `"Blocks after 5.0s"`)
- `reset()` returns `None` — consistent with stdlib conventions, no fluent chaining

### Agent's Discretion
- Internal storage for cooldown tracking (simple float attribute vs deque) — at agent's discretion
- Docstring wording — follow Google-style per project convention

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `Condition` ABC in `conditions.py` — base class with `__slots__ = ("name", "description")`, requires `check(**kwargs) -> bool`
- `condition_templates.py` — existing conditions (`AlwaysCondition`, `NeverCondition`, `ComparisonCondition`, etc.) all follow same pattern: `__slots__`, call `super().__init__(name, description)`, implement `check(**kwargs)`

### Established Patterns
- All condition classes use `__slots__` with explicit slot declarations
- All `check()` methods accept `**kwargs` for forward compatibility
- Conditions import from `.conditions` using relative imports
- `__init__.py` imports conditions from `core.py` (re-exported), not directly from `conditions.py`

### Integration Points
- New classes go in `condition_templates.py` (INT-01)
- Exports added to `fast_fsm.__init__` — import from `condition_templates` and add to `__all__` (INT-02)
- No changes needed to `core.py` — timing conditions are standard `Condition` subclasses

</code_context>

<specifics>
## Specific Ideas

- Use `time.monotonic()` exclusively — immune to NTP jumps (TIME-04)
- Each condition gets a `reset()` method to restart internal clock (TIME-05)
- Single `time.monotonic()` call per `check()` invocation — keeps hot path fast (PERF-01)

</specifics>

<deferred>
## Deferred Ideas

- `ThrottleCondition(max_count, window_seconds)` — rate limiter (future requirement)
- `TimeWindowCondition(start_offset, end_offset)` — time window guard (future requirement)

</deferred>
