"""
Tests for the FSM validation module.

Covers FSMValidator, EnhancedFSMValidator, ValidationIssue, and all
convenience functions (enhanced_validate_fsm, quick_health_check,
validate_and_score, compare_fsms, batch_validate, fsm_lint, validate_fsm,
quick_validation_report).
"""

import json

import pytest

from fast_fsm import (
    StateMachine,
    State,
    simple_fsm,
    FSMValidator,
    EnhancedFSMValidator,
    ValidationIssue,
    enhanced_validate_fsm,
    quick_health_check,
    validate_and_score,
    compare_fsms,
    batch_validate,
    fsm_lint,
    validate_fsm,
    quick_validation_report,
)


# ---------------------------------------------------------------------------
# Fixtures — reusable FSMs with different quality characteristics
# ---------------------------------------------------------------------------


@pytest.fixture
def well_designed_fsm():
    """A well-designed FSM with good state coverage and recovery paths."""
    return StateMachine.quick_build(
        "idle",
        [
            ("start", "idle", "running"),
            ("pause", "running", "paused"),
            ("resume", "paused", "running"),
            ("stop", "running", "idle"),
            ("stop", "paused", "idle"),
            ("error", "running", "error"),
            ("reset", "error", "idle"),
        ],
        name="GoodFSM",
    )


@pytest.fixture
def problematic_fsm():
    """An FSM with orphaned state and missing recovery transitions."""
    fsm = simple_fsm(
        "idle", "running", "error", "orphaned", initial="idle", name="ProblematicFSM"
    )
    fsm.add_transitions(
        [
            ("start", "idle", "running"),
            ("error", "running", "error"),
            # Missing: error recovery, 'orphaned' never reachable
        ]
    )
    return fsm


@pytest.fixture
def minimal_fsm():
    """A single-state FSM with no transitions."""
    return StateMachine.from_states("only_state", name="MinimalFSM")


@pytest.fixture
def complex_fsm():
    """An FSM with many states and many transitions."""
    fsm = StateMachine.from_states(
        "s1", "s2", "s3", "s4", "s5", "s6", "s7", "s8", "s9", "s10",
        initial="s1",
        name="ComplexFSM",
    )
    for i in range(1, 10):
        for j in range(i + 1, 11):
            fsm.add_transition(f"e_{i}_{j}", f"s{i}", f"s{j}")
    return fsm


# ---------------------------------------------------------------------------
# FSMValidator (base class)
# ---------------------------------------------------------------------------


class TestFSMValidator:
    """Tests for the base FSMValidator."""

    def test_extract_states_and_events(self, well_designed_fsm):
        v = FSMValidator(well_designed_fsm)
        assert "idle" in v.states
        assert "running" in v.states
        assert "start" in v.events
        assert v.initial_state == "idle"

    def test_reachable_states_good_fsm(self, well_designed_fsm):
        v = FSMValidator(well_designed_fsm)
        reachable = v.get_reachable_states()
        assert reachable == v.states  # all states should be reachable

    def test_unreachable_states_detected(self, problematic_fsm):
        v = FSMValidator(problematic_fsm)
        unreachable = v.find_unreachable_states()
        assert "orphaned" in unreachable

    def test_dead_states_detected(self, problematic_fsm):
        v = FSMValidator(problematic_fsm)
        dead = v.find_dead_states()
        # 'error' and 'orphaned' have no outgoing transitions
        assert "error" in dead
        assert "orphaned" in dead

    def test_missing_transitions(self, problematic_fsm):
        v = FSMValidator(problematic_fsm)
        missing = v.find_missing_transitions()
        assert len(missing) > 0
        # Every state-event pair without a transition should be listed
        missing_set = {(s, e) for s, e in missing}
        assert ("idle", "error") in missing_set

    def test_transition_matrix(self, well_designed_fsm):
        v = FSMValidator(well_designed_fsm)
        matrix = v.get_transition_matrix()
        assert isinstance(matrix, dict)
        assert "idle" in matrix
        assert "start" in matrix["idle"]
        assert "running" in matrix["idle"]["start"]

    def test_validate_completeness(self, well_designed_fsm):
        v = FSMValidator(well_designed_fsm)
        result = v.validate_completeness()
        assert result["total_states"] == len(v.states)
        assert result["total_events"] == len(v.events)
        assert result["initial_state"] == "idle"
        assert result["is_reachable"] is True

    def test_determinism_check(self, well_designed_fsm):
        v = FSMValidator(well_designed_fsm)
        d = v.check_determinism()
        assert d["is_deterministic"] is True
        assert d["non_deterministic_transitions"] == []

    def test_cycle_detection(self, well_designed_fsm):
        v = FSMValidator(well_designed_fsm)
        cycles = v.find_cycles()
        # idle -> running -> paused -> running (cycle), idle -> running -> error -> idle (cycle)
        assert len(cycles) > 0

    def test_test_path_generation(self, well_designed_fsm):
        v = FSMValidator(well_designed_fsm)
        paths = v.generate_test_paths(max_length=3, max_paths=5)
        assert len(paths) > 0
        # Each path is a list of (from_state, event, to_state) tuples
        for path in paths:
            for from_state, event, to_state in path:
                assert from_state in v.states
                assert to_state in v.states
                assert event in v.events


# ---------------------------------------------------------------------------
# ValidationIssue
# ---------------------------------------------------------------------------


class TestValidationIssue:
    """Tests for the ValidationIssue dataclass."""

    def test_str_representation(self):
        issue = ValidationIssue("error", "reachability", "State X is unreachable")
        text = str(issue)
        assert "ERROR" in text
        assert "unreachable" in text

    def test_repr(self):
        issue = ValidationIssue("warning", "completeness", "Dead end")
        assert "warning" in repr(issue)

    def test_location_in_str(self):
        issue = ValidationIssue(
            "info", "determinism", "Non-deterministic", location="stateA.event1"
        )
        assert "stateA.event1" in str(issue)


# ---------------------------------------------------------------------------
# EnhancedFSMValidator
# ---------------------------------------------------------------------------


class TestEnhancedFSMValidator:
    """Tests for the EnhancedFSMValidator."""

    def test_issues_populated_for_problematic_fsm(self, problematic_fsm):
        v = EnhancedFSMValidator(problematic_fsm)
        assert len(v.issues) > 0

    def test_no_critical_issues_for_good_fsm(self, well_designed_fsm):
        v = EnhancedFSMValidator(well_designed_fsm)
        assert not v.has_critical_issues()

    def test_has_critical_issues_for_minimal_fsm(self, minimal_fsm):
        v = EnhancedFSMValidator(minimal_fsm)
        # Single state with no events → error-level structural issue
        assert v.has_critical_issues() or len(v.issues) > 0

    def test_metrics_calculated(self, well_designed_fsm):
        v = EnhancedFSMValidator(well_designed_fsm)
        assert "total_states" in v.metrics
        assert "density" in v.metrics
        assert v.metrics["total_states"] > 0
        assert 0.0 <= v.metrics["density"] <= 1.0

    def test_get_issues_by_severity(self, problematic_fsm):
        v = EnhancedFSMValidator(problematic_fsm)
        warnings = v.get_issues_by_severity("warning")
        assert all(i.severity == "warning" for i in warnings)

    def test_get_issues_by_category(self, problematic_fsm):
        v = EnhancedFSMValidator(problematic_fsm)
        categories = {i.category for i in v.issues}
        for cat in categories:
            filtered = v.get_issues_by_category(cat)
            assert len(filtered) > 0
            assert all(i.category == cat for i in filtered)

    def test_validation_score_structure(self, well_designed_fsm):
        v = EnhancedFSMValidator(well_designed_fsm)
        score = v.get_validation_score()
        assert "overall_score" in score
        assert "grade" in score
        assert 0 <= score["overall_score"] <= 100
        assert score["grade"] in ("A", "B", "C", "D")

    def test_good_fsm_scores_higher_than_problematic(
        self, well_designed_fsm, problematic_fsm
    ):
        good_score = EnhancedFSMValidator(well_designed_fsm).get_validation_score()
        bad_score = EnhancedFSMValidator(problematic_fsm).get_validation_score()
        assert good_score["overall_score"] > bad_score["overall_score"]

    def test_export_json(self, well_designed_fsm):
        v = EnhancedFSMValidator(well_designed_fsm)
        raw = v.export_report("json")
        parsed = json.loads(raw)
        assert "fsm_name" in parsed
        assert "validation_score" in parsed
        assert "issues" in parsed
        assert isinstance(parsed["issues"], list)

    def test_export_markdown(self, well_designed_fsm):
        v = EnhancedFSMValidator(well_designed_fsm)
        md = v.export_report("markdown")
        assert "# FSM Validation Report" in md
        assert "Score" in md

    def test_export_text(self, well_designed_fsm):
        v = EnhancedFSMValidator(well_designed_fsm)
        text = v.export_report("text")
        assert isinstance(text, str)
        assert len(text) > 0

    def test_recommendations_generated(self, problematic_fsm):
        v = EnhancedFSMValidator(problematic_fsm)
        assert isinstance(v.recommendations, list)
        # Problematic FSM should have at least one recommendation
        assert len(v.recommendations) > 0


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_enhanced_validate_fsm_returns_validator(self, well_designed_fsm):
        result = enhanced_validate_fsm(well_designed_fsm)
        assert isinstance(result, EnhancedFSMValidator)

    def test_validate_fsm_returns_enhanced_validator(self, well_designed_fsm):
        result = validate_fsm(well_designed_fsm)
        assert isinstance(result, EnhancedFSMValidator)

    def test_quick_health_check_good_fsm(self, well_designed_fsm):
        health = quick_health_check(well_designed_fsm)
        assert health in ("healthy", "issues", "critical")

    def test_quick_health_check_problematic_fsm(self, problematic_fsm):
        health = quick_health_check(problematic_fsm)
        assert health in ("issues", "critical")

    def test_validate_and_score(self, well_designed_fsm):
        result = validate_and_score(well_designed_fsm)
        assert "overall_score" in result
        assert "grade" in result
        assert "status" in result
        assert "top_recommendations" in result
        assert result["status"] in ("good", "needs_attention", "critical")

    def test_compare_fsms(self, well_designed_fsm, problematic_fsm, minimal_fsm):
        comparison = compare_fsms(well_designed_fsm, problematic_fsm, minimal_fsm)
        assert "rankings" in comparison
        assert "best_fsm" in comparison
        assert "comparison_metrics" in comparison
        assert len(comparison["rankings"]) == 3
        # Rankings should be sorted by score descending
        scores = [score for _, score in comparison["rankings"]]
        assert scores == sorted(scores, reverse=True)

    def test_batch_validate(self, well_designed_fsm, problematic_fsm, capsys):
        validators = batch_validate(
            well_designed_fsm, problematic_fsm, show_summary=True
        )
        assert isinstance(validators, dict)
        assert "GoodFSM" in validators
        assert "ProblematicFSM" in validators
        assert isinstance(validators["GoodFSM"], EnhancedFSMValidator)
        # show_summary=True should produce console output
        captured = capsys.readouterr()
        assert "Batch Validation" in captured.out

    def test_batch_validate_no_summary(self, well_designed_fsm, capsys):
        validators = batch_validate(well_designed_fsm, show_summary=False)
        captured = capsys.readouterr()
        assert captured.out == ""
        assert len(validators) == 1

    def test_fsm_lint(self, problematic_fsm, capsys):
        fsm_lint(problematic_fsm, fix_mode=False)
        captured = capsys.readouterr()
        assert "Linting FSM" in captured.out
        assert "ProblematicFSM" in captured.out

    def test_quick_validation_report(self, well_designed_fsm, capsys):
        quick_validation_report(well_designed_fsm)
        captured = capsys.readouterr()
        assert len(captured.out) > 0


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Edge case and regression tests."""

    def test_single_state_no_transitions(self):
        """Validation should not crash on a trivial FSM."""
        fsm = StateMachine.from_states("only", name="Trivial")
        v = EnhancedFSMValidator(fsm)
        assert v.metrics["total_states"] == 1
        assert v.metrics["total_events"] == 0
        score = v.get_validation_score()
        assert isinstance(score["overall_score"], (int, float))

    def test_complex_fsm_no_crash(self, complex_fsm):
        """Validation should handle large FSMs without error."""
        v = EnhancedFSMValidator(complex_fsm)
        assert v.metrics["total_states"] == 10
        score = v.get_validation_score()
        assert score["overall_score"] >= 0

    def test_compare_single_fsm(self, well_designed_fsm):
        """Comparing a single FSM should still work."""
        result = compare_fsms(well_designed_fsm)
        assert result["best_fsm"] == "GoodFSM"
        assert len(result["rankings"]) == 1

    def test_export_json_is_valid(self, problematic_fsm):
        """JSON export should be parseable and contain expected keys."""
        v = EnhancedFSMValidator(problematic_fsm)
        parsed = json.loads(v.export_report("json"))
        assert parsed["fsm_name"] == "ProblematicFSM"
        assert len(parsed["issues"]) == len(v.issues)
        for issue_dict in parsed["issues"]:
            assert "severity" in issue_dict
            assert "category" in issue_dict
            assert "description" in issue_dict
