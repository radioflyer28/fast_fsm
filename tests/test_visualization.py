"""
Tests for the visualization module (to_mermaid).

All tests verify the generated Mermaid string structure without rendering it.
"""

import pytest

from fast_fsm import StateMachine, State, FuncCondition, to_mermaid
from fast_fsm.visualization import _mermaid_id


# ---------------------------------------------------------------------------
# _mermaid_id helper
# ---------------------------------------------------------------------------


class TestMermaidId:
    def test_plain_name_unchanged(self):
        assert _mermaid_id("idle") == "idle"

    def test_snake_case_unchanged(self):
        assert _mermaid_id("my_state") == "my_state"

    def test_spaces_replaced(self):
        assert _mermaid_id("my state") == "my_state"

    def test_hyphens_replaced(self):
        assert _mermaid_id("my-state") == "my_state"

    def test_dots_replaced(self):
        assert _mermaid_id("state.1") == "state_1"

    def test_mixed_special_chars(self):
        result = _mermaid_id("a b-c.d")
        assert result == "a_b_c_d"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def simple_fsm():
    """idle --> running --> done (linear)."""
    return StateMachine.quick_build(
        "idle",
        [("start", "idle", "running"), ("finish", "running", "done")],
        name="Simple",
    )


@pytest.fixture
def cyclic_fsm():
    """Traffic-light style cyclic FSM with three states."""
    return StateMachine.quick_build(
        "red",
        [
            ("timer", "red", "green"),
            ("timer", "green", "yellow"),
            ("timer", "yellow", "red"),
        ],
        name="TrafficLight",
    )


@pytest.fixture
def conditional_fsm():
    """FSM with a named condition on one transition."""
    cond = FuncCondition(lambda value=0, **kw: value > 0, "positive", "value > 0")
    fsm = StateMachine(State("waiting"), name="Conditional")
    fsm.add_state(State("active"))
    fsm.add_transition("go", "waiting", "active", cond)
    fsm.add_transition("reset", "active", "waiting")
    return fsm


# ---------------------------------------------------------------------------
# Basic structure
# ---------------------------------------------------------------------------


class TestToMermaidBasic:
    def test_starts_with_diagram_type(self, simple_fsm):
        out = to_mermaid(simple_fsm)
        assert out.startswith("stateDiagram-v2")

    def test_initial_state_arrow_present(self, simple_fsm):
        out = to_mermaid(simple_fsm)
        assert "[*] --> idle" in out

    def test_all_transitions_present(self, simple_fsm):
        out = to_mermaid(simple_fsm)
        assert "idle --> running : start" in out
        assert "running --> done : finish" in out

    def test_cyclic_transitions(self, cyclic_fsm):
        out = to_mermaid(cyclic_fsm)
        assert "[*] --> red" in out
        assert "red --> green : timer" in out
        assert "green --> yellow : timer" in out
        assert "yellow --> red : timer" in out

    def test_returns_string(self, simple_fsm):
        assert isinstance(to_mermaid(simple_fsm), str)

    def test_no_empty_lines_in_output(self, simple_fsm):
        """No blank lines should appear in the output."""
        for line in to_mermaid(simple_fsm).splitlines():
            assert line.strip() != "" or line == ""


# ---------------------------------------------------------------------------
# Title
# ---------------------------------------------------------------------------


class TestToMermaidTitle:
    def test_title_appears_as_comment(self, simple_fsm):
        out = to_mermaid(simple_fsm, title="My Diagram")
        assert "%% My Diagram" in out

    def test_title_before_diagram_type(self, simple_fsm):
        out = to_mermaid(simple_fsm, title="T")
        lines = out.splitlines()
        assert lines[0] == "%% T"
        assert lines[1] == "stateDiagram-v2"

    def test_no_title_by_default(self, simple_fsm):
        out = to_mermaid(simple_fsm)
        assert "%%" not in out


# ---------------------------------------------------------------------------
# Conditions
# ---------------------------------------------------------------------------


class TestToMermaidConditions:
    def test_condition_name_included_by_default(self, conditional_fsm):
        out = to_mermaid(conditional_fsm)
        assert "[positive]" in out

    def test_condition_omitted_when_disabled(self, conditional_fsm):
        out = to_mermaid(conditional_fsm, show_conditions=False)
        assert "[positive]" not in out
        assert "waiting --> active : go" in out

    def test_unconditional_transition_unaffected(self, conditional_fsm):
        out = to_mermaid(conditional_fsm)
        assert "active --> waiting : reset" in out

    def test_no_brackets_on_transitions_without_conditions(self, simple_fsm):
        out = to_mermaid(simple_fsm)
        # Condition brackets appear after the colon in "from --> to : label [cond]"
        for line in out.splitlines():
            if "-->" in line and ":" in line:
                assert "[" not in line.split(":", 1)[1]


# ---------------------------------------------------------------------------
# State names requiring sanitization
# ---------------------------------------------------------------------------


class TestToMermaidSanitization:
    def test_hyphenated_state_name_aliased(self):
        fsm = StateMachine(State("on-hold"), name="Dash")
        fsm.add_state(State("active"))
        fsm.add_transition("resume", "on-hold", "active")
        out = to_mermaid(fsm)
        # Alias declaration should appear
        assert 'state "on-hold" as on_hold' in out
        # Transitions should use the safe ID
        assert "on_hold --> active : resume" in out

    def test_spaced_state_name_aliased(self):
        fsm = StateMachine(State("on hold"), name="Space")
        fsm.add_state(State("active"))
        fsm.add_transition("resume", "on hold", "active")
        out = to_mermaid(fsm)
        assert 'state "on hold" as on_hold' in out
        assert "on_hold --> active : resume" in out

    def test_plain_names_no_alias(self, simple_fsm):
        out = to_mermaid(simple_fsm)
        assert "state " not in out  # no alias declarations needed


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestToMermaidEdgeCases:
    def test_single_state_no_transitions(self):
        fsm = StateMachine(State("lonely"), name="Solo")
        out = to_mermaid(fsm)
        assert "[*] --> lonely" in out
        assert "stateDiagram-v2" in out

    def test_works_with_async_state_machine(self):
        from fast_fsm import AsyncStateMachine

        fsm = AsyncStateMachine(State("wait"), name="Async")
        fsm.add_state(State("done"))
        fsm.add_transition("go", "wait", "done")
        out = to_mermaid(fsm)
        assert "[*] --> wait" in out
        assert "wait --> done : go" in out
