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
        "s1",
        "s2",
        "s3",
        "s4",
        "s5",
        "s6",
        "s7",
        "s8",
        "s9",
        "s10",
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

    def test_name_override_uses_custom_name(self, well_designed_fsm):
        v = FSMValidator(well_designed_fsm, name="MyMachine")
        assert v._report_name == "MyMachine"
        result = v.validate_completeness()
        assert result["fsm_name"] == "MyMachine"

    def test_name_default_uses_fsm_name(self, well_designed_fsm):
        v = FSMValidator(well_designed_fsm)
        assert v._report_name == well_designed_fsm.name
        result = v.validate_completeness()
        assert result["fsm_name"] == well_designed_fsm.name

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

    def test_name_override_propagates(self, well_designed_fsm):
        v = EnhancedFSMValidator(well_designed_fsm, name="CustomName")
        assert v._report_name == "CustomName"

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
        # New split-score fields
        assert "structural_score" in score
        assert "completeness_score" in score
        assert "design_style" in score
        assert score["design_style"] in ("sparse", "dense")
        assert 0 <= score["structural_score"] <= 100
        assert 0 <= score["completeness_score"] <= 100
        # overall_score mirrors structural_score
        assert score["overall_score"] == score["structural_score"]

    def test_sparse_fsm_structural_score_not_penalised(self):
        """A sparse but structurally sound FSM should score A on structural."""
        fsm = StateMachine.quick_build(
            "idle",
            [
                ("start", "idle", "running"),
                ("pause", "running", "paused"),
                ("resume", "paused", "running"),
                ("stop", "running", "idle"),
                ("error", "running", "error"),
                ("reset", "error", "idle"),
            ],
            name="SparseButSound",
        )
        v = EnhancedFSMValidator(fsm)
        score = v.get_validation_score()
        assert score["design_style"] == "sparse"
        # Structural score should be A/B; completeness score will be lower
        assert score["structural_score"] >= 70, (
            f"Expected structural_score >= 70, got {score['structural_score']}"
        )
        assert score["completeness_score"] < score["structural_score"], (
            "Completeness score should be lower than structural for sparse FSM"
        )

    def test_dense_fsm_both_scores_present(self):
        """A small fully-connected FSM should be classified dense."""
        pairs = [
            ("t1", "A", "B"),
            ("t2", "A", "A"),
            ("t1", "B", "A"),
            ("t2", "B", "B"),
        ]
        fsm = StateMachine.quick_build("A", pairs, name="DenseFSM2")
        v = EnhancedFSMValidator(fsm)
        score = v.get_validation_score()
        assert score["design_style"] == "dense"

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


# ---------------------------------------------------------------------------
# Coverage gap tests for validation reports and exports
# ---------------------------------------------------------------------------


class TestValidationReportGaps:
    """Cover print_validation_report, export_report, and enhanced report."""

    @pytest.fixture
    def gap_problematic_fsm(self):
        idle = State("idle")
        processing = State("processing")
        error_state = State("error")
        orphan = State("orphan")

        fsm = StateMachine(idle, name="problematic")
        fsm.add_state(processing)
        fsm.add_state(error_state)
        fsm.add_state(orphan)
        fsm.add_transition("start", "idle", "processing")
        fsm.add_transition("fail", "processing", "error")
        return fsm

    @pytest.fixture
    def gap_well_designed_fsm(self):
        idle = State("idle")
        running = State("running")
        fsm = StateMachine(idle, name="good_fsm")
        fsm.add_state(running)
        fsm.add_transition("start", "idle", "running")
        fsm.add_transition("stop", "running", "idle")
        return fsm

    def test_print_validation_report(self, gap_problematic_fsm, capsys):
        """FSMValidator.print_validation_report() prints output."""
        validator = FSMValidator(gap_problematic_fsm)
        validator.print_validation_report()
        captured = capsys.readouterr()
        assert "Validation Report" in captured.out
        assert "States:" in captured.out

    def test_export_json(self, gap_problematic_fsm):
        """EnhancedFSMValidator export_report as JSON."""
        validator = enhanced_validate_fsm(gap_problematic_fsm)
        json_str = validator.export_report(format="json")
        data = json.loads(json_str)
        assert "fsm_name" in data
        assert "validation_score" in data

    def test_export_markdown(self, gap_problematic_fsm):
        """EnhancedFSMValidator export_report as Markdown."""
        validator = enhanced_validate_fsm(gap_problematic_fsm)
        md = validator.export_report(format="markdown")
        assert "# FSM Validation Report" in md
        assert "## Metrics" in md

    def test_export_text(self, gap_problematic_fsm):
        """EnhancedFSMValidator export_report as text."""
        validator = enhanced_validate_fsm(gap_problematic_fsm)
        text = validator.export_report(format="text")
        assert "Enhanced FSM Validation Report" in text

    def test_print_enhanced_report_returns_string(self, gap_problematic_fsm):
        """print_enhanced_report with return_string=True."""
        validator = enhanced_validate_fsm(gap_problematic_fsm)
        result = validator.print_enhanced_report(return_string=True)
        assert result is not None
        assert isinstance(result, str)

    def test_print_enhanced_report_prints(self, gap_problematic_fsm, capsys):
        """print_enhanced_report with return_string=False prints to stdout."""
        validator = enhanced_validate_fsm(gap_problematic_fsm)
        result = validator.print_enhanced_report(return_string=False)
        assert result is None
        captured = capsys.readouterr()
        assert "Enhanced FSM Validation Report" in captured.out

    def test_batch_validate(self, gap_well_designed_fsm, gap_problematic_fsm):
        """batch_validate runs on multiple FSMs."""
        results = batch_validate(
            gap_well_designed_fsm, gap_problematic_fsm, show_summary=False
        )
        assert len(results) == 2
        assert "good_fsm" in results
        assert "problematic" in results

    def test_validation_score(self, gap_well_designed_fsm):
        """get_validation_score returns expected structure."""
        validator = enhanced_validate_fsm(gap_well_designed_fsm)
        score = validator.get_validation_score()
        assert "overall_score" in score
        assert "grade" in score
        assert score["grade"] in ("A", "B", "C", "D")


# ---------------------------------------------------------------------------
# Additional coverage-gap tests (coverage target ≥ 95 %)
# ---------------------------------------------------------------------------


class TestCoverageGaps:
    """Cover remaining uncovered branches in validation.py."""

    # ------------------------------------------------------------------
    # Helpers / fixtures
    # ------------------------------------------------------------------

    @staticmethod
    def _cyclic_fsm():
        """Simple 2-state cycle: a → b → a."""
        fsm = StateMachine.quick_build("a", [("go", "a", "b"), ("back", "b", "a")])
        return fsm

    @staticmethod
    def _clean_fsm():
        """Fully-covered 2-state FSM with zero issues.

        A --go→ B, A --back→ A, B --go→ B, B --back→ A.
        Defines all 4 (state, event) pairs so completeness, reachability,
        determinism, and complexity checks all pass cleanly.
        """
        fsm = StateMachine.quick_build(
            "A",
            [
                ("go", "A", "B"),
                ("back", "A", "A"),
                ("go", "B", "B"),
                ("back", "B", "A"),
            ],
            name="CleanFSM",
        )
        return fsm

    @staticmethod
    def _critical_fsm():
        """Single-state, zero-event FSM → triggers error-level issue."""
        return StateMachine.from_states("only", name="CriticalFSM")

    # ------------------------------------------------------------------
    # find_cycles – explicit cycle coverage (line 235)
    # ------------------------------------------------------------------

    def test_find_cycles_detects_cycle(self):
        """find_cycles appends cycles for a simple a→b→a ring."""
        v = FSMValidator(self._cyclic_fsm())
        cycles = v.find_cycles()
        assert len(cycles) > 0
        # Every cycle must start and end at the same state
        for cycle in cycles:
            assert cycle[0] == cycle[-1]

    # ------------------------------------------------------------------
    # print_validation_report – ">10 more" branch (line 292)
    # and cycles branch (lines 301-303)
    # ------------------------------------------------------------------

    def test_print_validation_report_many_missing(self, capsys):
        """'>10 more' banner appears when missing transitions exceed 10."""
        # 4 states × 4 events = 16 possible; define only 4 → 12 missing > 10
        s0 = State("s0")
        fsm = StateMachine(s0, name="ManyMissing")
        for label in ("s1", "s2", "s3"):
            fsm.add_state(State(label))
        # Use 4 distinct events so event-set size = 4
        fsm.add_transition("e0", "s0", "s1")
        fsm.add_transition("e1", "s0", "s2")
        fsm.add_transition("e2", "s0", "s3")
        fsm.add_transition("e3", "s0", "s1")
        # states s1/s2/s3 have no transitions for any event → 12 missing entries
        v = FSMValidator(fsm)
        v.print_validation_report()
        captured = capsys.readouterr()
        assert "more" in captured.out

    def test_print_validation_report_shows_cycles(self, capsys):
        """Cycles section appears in print_validation_report output."""
        v = FSMValidator(self._cyclic_fsm())
        v.print_validation_report()
        captured = capsys.readouterr()
        assert "Cycles Found" in captured.out

    # ------------------------------------------------------------------
    # EnhancedFSMValidator._analyze_complexity
    # ------------------------------------------------------------------

    def test_high_branching_factor_flagged(self):
        """FSM with >10 outgoing triggers from one state gets complexity issue."""
        # hub → s1 … s11 via 11 distinct triggers
        transitions = [(f"t{i}", "hub", f"s{i}") for i in range(1, 12)]
        fsm = StateMachine.quick_build("hub", transitions, name="HighBranch")
        v = EnhancedFSMValidator(fsm)
        categories = [i.category for i in v.issues]
        assert "complexity" in categories

    def test_deep_path_flagged(self):
        """Linear chain of 22 states (longest path 21 > 20) is flagged."""
        transitions = [("step", f"s{i}", f"s{i + 1}") for i in range(22)]
        fsm = StateMachine.quick_build("s0", transitions, name="DeepFSM")
        v = EnhancedFSMValidator(fsm)
        complexity_issues = [i for i in v.issues if i.category == "complexity"]
        descriptions = " ".join(i.description for i in complexity_issues)
        assert "deep" in descriptions.lower() or "path" in descriptions.lower()

    def test_sparse_fsm_flagged(self):
        """Sparse FSM (density<0.4, >6 possible transitions) is classified as
        sparse in metrics and design_style, and missing-transition completeness
        issues are downgraded to info rather than warning."""
        # 11 states, only 1 event + 1 transition → density ≈ 9 % → sparse
        fsm = StateMachine.from_states(
            "hub",
            *[f"leaf{i}" for i in range(10)],
            initial="hub",
            name="SparseFSM",
        )
        fsm.add_transition("go", "hub", "leaf0")
        v = EnhancedFSMValidator(fsm)
        assert v.metrics["design_style"] == "sparse"
        score = v.get_validation_score()
        assert score["design_style"] == "sparse"
        assert "structural_score" in score
        assert "completeness_score" in score
        # Missing-transition issues should be info, not warning, for sparse FSMs
        completeness_warnings = [
            i
            for i in v.issues
            if i.category == "completeness"
            and "missing transitions" in i.description
            and i.severity == "warning"
        ]
        assert completeness_warnings == [], (
            "Missing-transition issues should be info-level for sparse FSMs"
        )

    def test_dense_fsm_recommendation(self):
        """Fully-connected FSM (density>0.8) triggers the dense recommendation."""
        # 3 states × 3 events, all 9 pairs defined (100 % density)
        pairs = [
            ("t1", "A", "B"),
            ("t2", "A", "C"),
            ("t3", "A", "A"),
            ("t1", "B", "A"),
            ("t2", "B", "C"),
            ("t3", "B", "B"),
            ("t1", "C", "A"),
            ("t2", "C", "B"),
            ("t3", "C", "C"),
        ]
        fsm = StateMachine.quick_build("A", pairs, name="DenseFSM")
        v = EnhancedFSMValidator(fsm)
        dense_rec = any("dense" in r.lower() for r in v.recommendations)
        assert dense_rec, f"Expected dense recommendation, got: {v.recommendations}"

    # ------------------------------------------------------------------
    # quick_health_check – "critical" return path (line 842)
    # ------------------------------------------------------------------

    def test_quick_health_check_critical(self):
        """quick_health_check returns 'critical' for an error-level FSM."""
        result = quick_health_check(self._critical_fsm())
        assert result == "critical"

    def test_quick_health_check_healthy(self):
        """quick_health_check returns 'healthy' for a zero-issue FSM."""
        result = quick_health_check(self._clean_fsm())
        assert result == "healthy"

    # ------------------------------------------------------------------
    # fsm_lint – critical branch, no-issues branch, fix_mode branch
    # ------------------------------------------------------------------

    def test_fsm_lint_critical(self, capsys):
        """fsm_lint prints critical-issues banner for an error-level FSM."""
        fsm_lint(self._critical_fsm())
        captured = capsys.readouterr()
        assert "Critical issues found" in captured.out

    def test_fsm_lint_no_issues(self, capsys):
        """fsm_lint prints '✅ No issues found!' for a clean FSM."""
        fsm_lint(self._clean_fsm())
        captured = capsys.readouterr()
        assert "No issues found" in captured.out

    def test_fsm_lint_warnings_only(self, capsys):
        """fsm_lint prints warnings-count banner when FSM has warnings but no errors."""
        # C is unreachable (warning) but has all outgoing transitions (no error)
        fsm = StateMachine.quick_build(
            "A",
            [
                ("e1", "A", "B"),
                ("e2", "A", "A"),
                ("e1", "B", "A"),
                ("e2", "B", "B"),
                ("e1", "C", "A"),
                ("e2", "C", "A"),
            ],
            name="WarningsFSM",
        )
        fsm_lint(fsm)
        captured = capsys.readouterr()
        assert "issues found" in captured.out

    def test_fsm_lint_fix_mode(self, capsys):
        """fsm_lint with fix_mode=True invokes the wizard (which exits cleanly for clean FSM)."""
        # Using clean FSM so interactive_fix_wizard() returns immediately (no issues)
        fsm_lint(self._clean_fsm(), fix_mode=True)
        captured = capsys.readouterr()
        # Wizard prints "No issues found" and returns without blocking on input()
        assert "No issues" in captured.out


# ---------------------------------------------------------------------------
# TestDesignStyleThreshold
# ---------------------------------------------------------------------------


class TestDesignStyleThreshold:
    """Tests for the design_style_threshold and min_transitions_for_style kwargs."""

    # ------------------------------------------------------------------ helpers

    def _sparse_candidate(self):
        """A low-density FSM that is sparse under defaults (10 states, 3 transitions)."""
        fsm = StateMachine.quick_build(
            "a",
            [("go", "a", "b"), ("go", "b", "c"), ("go", "c", "d")],
            states=["e", "f", "g", "h", "i", "j"],
            name="SparseFSM",
        )
        return fsm

    def _dense_candidate(self):
        """A high-density FSM with most transitions filled."""
        return StateMachine.quick_build(
            "x",
            [
                ("t1", "x", "y"),
                ("t2", "x", "z"),
                ("t1", "y", "x"),
                ("t2", "y", "z"),
                ("t1", "z", "x"),
                ("t2", "z", "y"),
            ],
            name="DenseFSM",
        )

    # ------------------------------------------------------------------ default behaviour

    def test_defaults_preserved(self):
        """Default kwargs yield same design_style as the original hardcoded values."""
        v1 = EnhancedFSMValidator(self._sparse_candidate())
        v2 = EnhancedFSMValidator(
            self._sparse_candidate(),
            design_style_threshold=0.4,
            min_transitions_for_style=6,
        )
        assert v1.metrics["design_style"] == v2.metrics["design_style"]

    def test_sparse_candidate_is_sparse_by_default(self):
        """The sparse candidate FSM classifies as sparse with default thresholds."""
        v = EnhancedFSMValidator(self._sparse_candidate())
        assert v.metrics["design_style"] == "sparse"

    def test_dense_candidate_is_dense_by_default(self):
        """The dense candidate FSM classifies as dense with default thresholds."""
        v = EnhancedFSMValidator(self._dense_candidate())
        assert v.metrics["design_style"] == "dense"

    # ------------------------------------------------------------------ design_style_threshold tuning

    def test_threshold_0_forces_dense(self):
        """threshold=0.0: density is always >= 0, so design_style is always dense."""
        v = EnhancedFSMValidator(self._sparse_candidate(), design_style_threshold=0.0)
        assert v.metrics["design_style"] == "dense"

    def test_threshold_1_1_forces_sparse_if_above_min(self):
        """threshold=1.1: density always < 1.1 (max density is 1.0), so always sparse."""
        v = EnhancedFSMValidator(self._sparse_candidate(), design_style_threshold=1.1)
        assert v.metrics["design_style"] == "sparse"

    def test_threshold_reclassifies_borderline_fsm(self):
        """Adjusting threshold flips classification of a borderline FSM."""
        # 4 states (a, b, c, d), 2 events (e1, e2) → possible=8, actual=2, density=0.25
        # sparse under default 0.4, dense if threshold is lowered to 0.2 (0.25 >= 0.2)
        fsm = StateMachine.quick_build(
            "a",
            [("e1", "a", "b"), ("e2", "a", "c")],
            states=["d"],
            name="BorderlineFSM",
        )
        v_default = EnhancedFSMValidator(fsm)
        v_low = EnhancedFSMValidator(fsm, design_style_threshold=0.2)
        assert v_default.metrics["density"] == pytest.approx(0.25)
        assert v_default.metrics["design_style"] == "sparse"
        assert v_low.metrics["design_style"] == "dense"

    # ------------------------------------------------------------------ min_transitions_for_style tuning

    def test_min_transitions_0_allows_tiny_sparse_fsm(self):
        """min_transitions_for_style=0: even a tiny FSM can be sparse."""
        # tiny FSM: 2 states, 1 event → possible=2, actual=1, density=0.5
        # With default min=6, possible (2) <= 6 → always dense.
        # With min=0, density < 0.4 check applies: 0.5 >= 0.4 → still dense.
        # Use an even sparser tiny FSM to verify the guard is off:
        fsm = StateMachine.from_states("a", "b", "c", "d", initial="a", name="T")
        fsm.add_transition("go", "a", "b")  # 1/12 transitions → very sparse
        v = EnhancedFSMValidator(fsm, min_transitions_for_style=0)
        # density ~= 1/12 < 0.4, possible=12 > 0 → sparse
        assert v.metrics["design_style"] == "sparse"

    def test_min_transitions_large_forces_dense_for_small_fsm(self):
        """min_transitions_for_style=9999: small FSMs always classify as dense."""
        v = EnhancedFSMValidator(
            self._sparse_candidate(), min_transitions_for_style=9999
        )
        assert v.metrics["design_style"] == "dense"

    # ------------------------------------------------------------------ metrics propagation

    def test_threshold_stored_does_not_affect_other_metrics(self):
        """Changing threshold/min_transitions does not affect density or counts."""
        fsm = self._sparse_candidate()
        v1 = EnhancedFSMValidator(fsm)
        v2 = EnhancedFSMValidator(
            fsm, design_style_threshold=0.9, min_transitions_for_style=2
        )
        for key in (
            "density",
            "actual_transitions",
            "possible_transitions",
            "total_states",
        ):
            assert v1.metrics[key] == v2.metrics[key]

    def test_class_constants_match_defaults(self):
        """DEFAULT_* class constants equal the default kwarg values."""
        assert EnhancedFSMValidator.DEFAULT_DESIGN_STYLE_THRESHOLD == 0.4
        assert EnhancedFSMValidator.DEFAULT_MIN_TRANSITIONS_FOR_STYLE == 6
