# Test Suite Audit

**Audited:** 2026-04-04
**Baseline:** 637 tests across 16 files
**Methodology:** Read all 16 test files; classify each test class by signal quality

---

## Summary

| Category | Count |
|----------|-------|
| Keep — unique behaviour signal | 629 |
| Redundant — duplicate coverage 1:1 | 3 |
| Low-value — trivial/weak assertions | 1 + 2 performance |

**Recommended removals: 4 tests** → target: 633 tests

---

## File-by-File Classification

### test_basic_functionality.py (23 declared functions → 28 parametrized + helpers)

| Test | Classification | Reason |
|------|----------------|--------|
| `TestBasicFunctionality::test_state_creation` | **Low-value** | Asserts `State("x").name == "x"`. Covered implicitly by every test in the corpus. |
| `TestBasicFunctionality::test_state_machine_creation` | Keep | Tests initial state and current_state identity |
| `TestBasicFunctionality::test_add_state` | Keep | Tests `states` property population |
| `TestBasicFunctionality::test_simple_transition` | Keep | Core behaviourally-valid test |
| `TestBasicFunctionality::test_transition_with_args` | Keep | Verifies kwargs pass through harmlessly |
| `TestConditionalTransitions::test_condition_success` | Keep | Integration: condition returning True unblocks FSM |
| `TestConditionalTransitions::test_condition_failure` | Keep | Integration: condition returning False blocks FSM |
| `TestConditionalTransitions::test_condition_with_context` | Keep | Unique: condition reads kwargs to decide |
| `TestErrorHandling::test_invalid_trigger` | Keep | Core error path |
| `TestErrorHandling::test_invalid_source_state` | Keep | Different failure mode than invalid trigger |
| `TestErrorHandling::test_can_trigger_method` | Keep | `can_trigger()` contract |
| `TestComplexScenarios::test_traffic_light_example` | Keep | Integration scenario with cycling transitions |
| `TestComplexScenarios::test_order_processing_example` | Keep | Integration: multi-state, list-source transitions |
| `TestComplexScenarios::test_multiple_target_states` | Keep | Tests two transitions from same source |
| `TestPerformance::test_many_states_performance` | **Low-value** | Asserts `elapsed < 1.0s` for 100 transitions. Not a real threshold. `test_performance_benchmarks.py` uses correct math (200k ops/sec). Brittle on slow CI. |
| `TestPerformance::test_repeated_transitions_performance` | **Low-value** | Same: `elapsed < 1.0s` for 1000 ops. Redundant with benchmarks. |
| `TestQuickBuildGaps` | Keep | Covers states= param and FSMBuilder edge cases |

---

### test_advanced_functionality.py (105 declared functions)

| Test Class | Classification | Reason |
|------------|----------------|--------|
| `TestAdvancedTransitions` | Keep | Bidirectional, emergency, multi-from transitions |
| `TestStateTriggerMethods::test_safe_trigger_vs_trigger` | Keep | Unique: condition exception handling in both methods |
| `TestStateTriggerMethods::test_safe_trigger_with_invalid_trigger` | **Redundant** | Calls `trigger("nonexistent")` and `safe_trigger("nonexistent")`. Both paths covered by: `test_basic::TestErrorHandling::test_invalid_trigger` and `test_boundary_negative::TestSafeTriggerEdgeCases::test_safe_trigger_invalid_trigger_returns_error`. Zero unique signal. |
| `TestStateCallbacks` | Keep | Thorough callback ordering and exception handling |
| `TestBatchOperations` | Keep | add_transitions, add_wildcard_trigger |
| `TestForceStateAndReset` | Keep | force_state(), reset(), initial_state_name |
| `TestSnapshot` | Keep | snapshot/restore/clone |
| `TestClone` | Keep | clone() semantics |
| `TestMachineCallbacks` | Keep | on_enter/on_exit per-state registration |
| `TestFromDict` | Keep | from_dict factory |
| `TestTransitionResultRaiseIfFailed` | Keep | raise_if_failed() semantics |

---

### test_async.py — Keep all
All async tests are targeted at async-specific behavior. No redundancy with sync tests.

### test_basic_functionality.py — 3 tests removed (see above)

### test_boundary_negative.py — Keep all
Focused boundary/negative tests, clearly scoped. No redundancy found.

### test_builder.py — Keep all
66 tests for FSMBuilder. Covers many builder-specific code paths.

### test_condition_templates.py — Keep all
74 tests for 9 condition types (~8 tests each). Well-structured, no redundancy.

### test_hypothesis.py — Keep all
8 property-based tests. High signal, no redundancy.

### test_listeners.py — Keep all  
27 tests for listener/observer pattern.

### test_logging_config.py — Keep all
11 tests for logging config helpers.

### test_mypyc_guard.py — Keep all
3 tests verifying mypyc compilation safety invariants (ADR-003).

### test_performance_benchmarks.py — Keep all
11 tests with real throughput thresholds.

### test_readme_examples.py — Keep all
10 tests validating README documentation examples.

### test_safety_kwargs.py — Keep all
37 tests for kwargs sanitization safety.

### test_state_machine_utils.py — Keep all
39 tests for utility methods (debug_info, is_in, get_available_triggers, etc.)

### test_validation.py — Keep all
86 tests for EnhancedFSMValidator, scoring, batch validation.

### test_visualization.py — Keep all
41 tests for Mermaid diagram generation.

---

## Recommended Removals

| File | Test | Reason |
|------|------|--------|
| `test_basic_functionality.py` | `TestBasicFunctionality::test_state_creation` | Trivial assert, covered implicitly everywhere |
| `test_basic_functionality.py` | `TestPerformance::test_many_states_performance` | Weak timing (< 1.0s), real coverage in benchmarks |
| `test_basic_functionality.py` | `TestPerformance::test_repeated_transitions_performance` | Same |
| `test_advanced_functionality.py` | `TestStateTriggerMethods::test_safe_trigger_with_invalid_trigger` | Duplicate of boundary negative tests |

**Result: 637 → 633 tests** (-4)

---

## Coverage Gaps (TESTS-03)

### Core.py coverage unmeasurable (compile artifact)
- `src/fast_fsm/core.py` shows **0% coverage** in pytest-cov because mypyc compiles it to a .so extension, which `coverage.py` cannot instrument.
- Coverage tooling only reports what it can trace — the .so is a black box.
- **Actual coverage is high** — 637 tests exercise the module extensively, but we cannot get a precise line count.
- **Workaround:** Run with `FAST_FSM_PURE_PYTHON=1` env var to get accurate coverage of the interpreted version.
- **Recommendation for v0.2.2:** Add `FAST_FSM_PURE_PYTHON=1 uv run pytest tests/ --cov=src/fast_fsm` to CI as a separate instrumented run.

### __init__.py uncovered lines (49-50)
- Lines 49-50 are the `except PackageNotFoundError` branch in the version lookup.
- This branch fires only when the package is not installed (editable or source installs with no dist-info).
- Low risk, but a test could exercise it by importing from source without install.
- **Recommendation:** Accept as tolerated uncovered branch (PackageNotFoundError → "unknown" is trivially correct).

### validation.py line 933
- Specific line in EnhancedFSMValidator not reached.
- Needs investigation in a future cycle.
