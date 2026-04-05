"""
Tests for the visualization module (to_mermaid, to_mermaid_fenced,
to_mermaid_document).

All tests verify the generated Mermaid/Markdown string structure without
rendering it.
"""

import pytest

from fast_fsm import StateMachine, State, FuncCondition, to_mermaid
from fast_fsm import to_mermaid_fenced, to_mermaid_document, to_plantuml, to_json
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


# ---------------------------------------------------------------------------
# to_mermaid_fenced
# ---------------------------------------------------------------------------


class TestToMermaidFenced:
    def test_wrapped_in_mermaid_fences(self, simple_fsm):
        out = to_mermaid_fenced(simple_fsm)
        assert out.startswith("```mermaid\n")
        assert out.endswith("\n```")

    def test_diagram_content_preserved(self, simple_fsm):
        out = to_mermaid_fenced(simple_fsm)
        assert "stateDiagram-v2" in out
        assert "[*] --> idle" in out
        assert "idle --> running : start" in out

    def test_title_forwarded(self, simple_fsm):
        out = to_mermaid_fenced(simple_fsm, title="My Title")
        assert "%% My Title" in out

    def test_conditions_forwarded(self, conditional_fsm):
        with_cond = to_mermaid_fenced(conditional_fsm, show_conditions=True)
        without_cond = to_mermaid_fenced(conditional_fsm, show_conditions=False)
        assert "[positive]" in with_cond
        assert "[positive]" not in without_cond

    def test_returns_string(self, simple_fsm):
        assert isinstance(to_mermaid_fenced(simple_fsm), str)


# ---------------------------------------------------------------------------
# to_mermaid_document — without adjacency matrix
# ---------------------------------------------------------------------------


class TestToMermaidDocumentBasic:
    def test_starts_with_heading(self, simple_fsm):
        doc = to_mermaid_document(simple_fsm)
        assert doc.startswith("# Simple")

    def test_diagram_section_present(self, simple_fsm):
        doc = to_mermaid_document(simple_fsm)
        assert "## State Diagram" in doc
        assert "```mermaid" in doc
        assert "stateDiagram-v2" in doc

    def test_custom_title(self, simple_fsm):
        doc = to_mermaid_document(simple_fsm, title="Custom Heading")
        assert doc.startswith("# Custom Heading")

    def test_no_adjacency_sections_without_matrix(self, simple_fsm):
        doc = to_mermaid_document(simple_fsm)
        assert "## State Adjacency Matrix" not in doc
        assert "## Transitions" not in doc

    def test_returns_string(self, simple_fsm):
        assert isinstance(to_mermaid_document(simple_fsm), str)


# ---------------------------------------------------------------------------
# to_mermaid_document — with adjacency matrix
# ---------------------------------------------------------------------------


class TestToMermaidDocumentWithMatrix:
    @pytest.fixture
    def fsm_and_matrix(self, simple_fsm):
        from fast_fsm.validation import FSMValidator

        adj = FSMValidator(simple_fsm).get_adjacency_matrix()
        return simple_fsm, adj

    def test_adjacency_section_present(self, fsm_and_matrix):
        fsm, adj = fsm_and_matrix
        doc = to_mermaid_document(fsm, adjacency_matrix=adj)
        assert "## State Adjacency Matrix" in doc

    def test_transitions_section_present(self, fsm_and_matrix):
        fsm, adj = fsm_and_matrix
        doc = to_mermaid_document(fsm, adjacency_matrix=adj)
        assert "## Transitions" in doc

    def test_state_names_in_adjacency_table(self, fsm_and_matrix):
        fsm, adj = fsm_and_matrix
        doc = to_mermaid_document(fsm, adjacency_matrix=adj)
        for state in adj["states"]:
            assert state in doc

    def test_event_names_in_transitions_table(self, fsm_and_matrix):
        fsm, adj = fsm_and_matrix
        doc = to_mermaid_document(fsm, adjacency_matrix=adj)
        for t in adj["transitions"]:
            assert t["event"] in doc

    def test_em_dash_for_missing_transitions(self, fsm_and_matrix):
        fsm, adj = fsm_and_matrix
        doc = to_mermaid_document(fsm, adjacency_matrix=adj)
        # linear FSM has no self-transitions, so some cells must show —
        assert "—" in doc

    def test_diagram_still_present_with_matrix(self, fsm_and_matrix):
        fsm, adj = fsm_and_matrix
        doc = to_mermaid_document(fsm, adjacency_matrix=adj)
        assert "stateDiagram-v2" in doc

    def test_empty_adjacency_dict_does_not_crash(self, simple_fsm):
        """Passing an empty dict should not raise."""
        doc = to_mermaid_document(simple_fsm, adjacency_matrix={})
        assert isinstance(doc, str)
        assert "## State Diagram" in doc


# ---------------------------------------------------------------------------
# to_plantuml
# ---------------------------------------------------------------------------


class TestToPlantUMLBasic:
    def test_starts_and_ends_correctly(self, simple_fsm):
        out = to_plantuml(simple_fsm)
        lines = out.splitlines()
        assert lines[0] == "@startuml"
        assert lines[-1] == "@enduml"

    def test_initial_state_marker(self, simple_fsm):
        out = to_plantuml(simple_fsm)
        assert "[*] --> idle" in out

    def test_all_transitions_present(self, simple_fsm):
        out = to_plantuml(simple_fsm)
        assert "idle --> running : start" in out
        assert "running --> done : finish" in out

    def test_terminal_state_marked(self, simple_fsm):
        out = to_plantuml(simple_fsm)
        assert "done --> [*]" in out

    def test_cyclic_no_terminal_states(self, cyclic_fsm):
        out = to_plantuml(cyclic_fsm)
        # All states have outgoing transitions — no terminal markers
        assert "--> [*]" not in out.replace("[*] -->", "")

    def test_returns_string(self, simple_fsm):
        assert isinstance(to_plantuml(simple_fsm), str)


class TestToPlantUMLTitle:
    def test_title_present(self, simple_fsm):
        out = to_plantuml(simple_fsm, title="My FSM")
        assert "title My FSM" in out

    def test_no_title_by_default(self, simple_fsm):
        out = to_plantuml(simple_fsm)
        assert "title " not in out


class TestToPlantUMLConditions:
    def test_condition_shown_by_default(self, conditional_fsm):
        out = to_plantuml(conditional_fsm)
        assert "[positive]" in out

    def test_condition_hidden_when_disabled(self, conditional_fsm):
        out = to_plantuml(conditional_fsm, show_conditions=False)
        assert "[positive]" not in out
        assert "waiting --> active : go" in out


class TestToPlantUMLEdgeCases:
    def test_single_state_no_transitions(self):
        fsm = StateMachine(State("lonely"), name="Solo")
        out = to_plantuml(fsm)
        assert "[*] --> lonely" in out
        assert "lonely --> [*]" in out

    def test_works_with_async_state_machine(self):
        from fast_fsm import AsyncStateMachine

        fsm = AsyncStateMachine(State("wait"), name="Async")
        fsm.add_state(State("done"))
        fsm.add_transition("go", "wait", "done")
        out = to_plantuml(fsm)
        assert "[*] --> wait" in out
        assert "wait --> done : go" in out
        assert "done --> [*]" in out


# ---------------------------------------------------------------------------
# to_json
# ---------------------------------------------------------------------------


class TestToJsonTopology:
    def test_top_level_keys(self, simple_fsm):
        data = to_json(simple_fsm)
        assert "topology" in data
        assert "analysis" in data

    def test_states_sorted(self, simple_fsm):
        data = to_json(simple_fsm)
        assert data["topology"]["states"] == sorted(["idle", "running", "done"])

    def test_initial_state(self, simple_fsm):
        data = to_json(simple_fsm)
        assert data["topology"]["initial"] == "idle"

    def test_transitions_present(self, simple_fsm):
        data = to_json(simple_fsm)
        triggers = {t["trigger"] for t in data["topology"]["transitions"]}
        assert "start" in triggers
        assert "finish" in triggers

    def test_has_guard_false_when_no_condition(self, simple_fsm):
        data = to_json(simple_fsm)
        for t in data["topology"]["transitions"]:
            assert t["has_guard"] is False

    def test_has_guard_true_with_condition(self, conditional_fsm):
        data = to_json(conditional_fsm)
        guarded = [t for t in data["topology"]["transitions"] if t["has_guard"]]
        assert len(guarded) >= 1


class TestToJsonReachability:
    def test_all_reachable_in_simple_fsm(self, simple_fsm):
        r = to_json(simple_fsm)["analysis"]["reachability"]
        assert set(r["reachable"]) == {"idle", "running", "done"}
        assert r["unreachable"] == []

    def test_unreachable_state_detected(self):
        fsm = StateMachine(State("a"), name="Unreach")
        fsm.add_state(State("b"))
        fsm.add_state(State("orphan"))
        fsm.add_transition("go", "a", "b")
        r = to_json(fsm)["analysis"]["reachability"]
        assert "orphan" in r["unreachable"]

    def test_terminal_states(self, simple_fsm):
        r = to_json(simple_fsm)["analysis"]["reachability"]
        assert "done" in r["terminal"]


class TestToJsonCycles:
    def test_cyclic_machine(self, cyclic_fsm):
        c = to_json(cyclic_fsm)["analysis"]["cycles"]
        assert c["has_cycles"] is True
        assert len(c["states_in_cycles"]) > 0

    def test_dag_no_cycles(self, simple_fsm):
        c = to_json(simple_fsm)["analysis"]["cycles"]
        assert c["has_cycles"] is False
        assert c["states_in_cycles"] == []


class TestToJsonQuality:
    def test_quality_section_populated(self, simple_fsm):
        q = to_json(simple_fsm)["analysis"]["quality"]
        assert q is not None
        assert "overall_score" in q
        assert "grade" in q
        assert "issues" in q

    def test_json_serialisable(self, simple_fsm):
        import json

        data = to_json(simple_fsm)
        # Must not raise TypeError
        serialised = json.dumps(data)
        assert isinstance(serialised, str)
