# Phase 13: Testing & Integration Verification - Context

**Gathered:** 2026-04-05
**Status:** Ready for planning
**Mode:** Auto-generated (infrastructure phase — discuss skipped)

<domain>
## Phase Boundary

Verify timing conditions work as guards on both sync and async state machines, with performance within contract and no regressions. Write comprehensive tests for `TimeoutCondition`, `CooldownCondition`, `ElapsedCondition` covering unit behavior, FSM integration (StateMachine + AsyncStateMachine), FSMBuilder support, and throughput benchmarks.

</domain>

<decisions>
## Implementation Decisions

### Agent's Discretion
All implementation choices are at the agent's discretion — pure infrastructure/testing phase. Use ROADMAP phase goal, success criteria, and codebase conventions to guide decisions.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `tests/test_condition_templates.py` — existing tests for condition_templates (AlwaysCondition, NeverCondition, etc.)
- `tests/test_safety_kwargs.py` — tests for **kwargs forwarding on all conditions
- `tests/test_async.py` — async FSM tests with AsyncCondition
- `tests/test_performance_benchmarks.py` — throughput benchmarks (200k ops/sec gate)

### Established Patterns
- Tests use pytest with no fixtures — simple function-based tests
- Performance tests use `time.perf_counter()` timing loops with explicit logging suppression
- Async tests use `pytest.mark.asyncio`

### Integration Points
- New tests go in `tests/test_condition_templates.py` (unit tests) and possibly new file for integration
- Performance test goes in `tests/test_performance_benchmarks.py`

</code_context>

<specifics>
## Specific Ideas

No specific requirements — infrastructure phase. Refer to ROADMAP phase description and success criteria.

</specifics>

<deferred>
## Deferred Ideas

None — testing phase.

</deferred>
