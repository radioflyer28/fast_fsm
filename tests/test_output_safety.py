"""Strict-RED hostile-output contracts for the Phase 19 renderer hardening.

These tests intentionally describe the post-19-06 rendering boundary.  They use
real state machines and inspect generated physical lines; optional Mermaid and
PlantUML CLIs are deliberately not part of the oracle.
"""

from __future__ import annotations

import json
import re
import threading
from dataclasses import dataclass

import pytest

import fast_fsm.visualization as visualization
from fast_fsm import (
    DiagnosticBudgetExceeded,
    DiagnosticLimits,
    FuncCondition,
    State,
    StateMachine,
    to_json,
    to_mermaid,
    to_mermaid_document,
    to_mermaid_fenced,
    to_plantuml,
)
from fast_fsm.validation import FSMValidator


@dataclass(frozen=True)
class HostileTextCase:
    """One caller-controlled value and the grammar category it exercises."""

    name: str
    value: str


ALL_OTHER_CONTROLS = "".join(chr(code) for code in range(1, 32) if code not in {10, 13})

HOSTILE_TEXT_CASES = (
    HostileTextCase("empty", ""),
    HostileTextCase("quotes-and-apostrophe", "quote\" and apostrophe'"),
    HostileTextCase("brackets-braces-and-angles", "[bracket]{brace}<angle>"),
    HostileTextCase("colons-and-semicolons", "left:right;next"),
    HostileTextCase("backslash", r"path\\segment"),
    HostileTextCase("crlf", "line-one\r\nline-two"),
    HostileTextCase("nul", "nul\x00payload"),
    HostileTextCase("remaining-controls", f"controls{ALL_OTHER_CONTROLS}done"),
    HostileTextCase("mermaid-comment", "%% injected comment"),
    HostileTextCase("plantuml-include", "!include injected.puml"),
    HostileTextCase("plantuml-import", "!import injected.puml"),
    HostileTextCase("plantuml-start", "@startuml"),
    HostileTextCase("plantuml-end", "@enduml"),
    HostileTextCase("markdown-fence", "```mermaid"),
    HostileTextCase("url", "https://example.invalid/a?b=c"),
    HostileTextCase("emoji", "diagram-🙂"),
    HostileTextCase("combining-mark", "e\u0301"),
    HostileTextCase("rtl-marker", "prefix\u202ertl"),
)

RENDERER_NAMES = ("mermaid", "plantuml", "fenced", "document", "json")
DIAGRAM_RENDERER_NAMES = ("mermaid", "plantuml")


def _machine_with_hostile_text(value: str) -> StateMachine:
    """Build a real two-state machine with caller text in every renderer sink."""

    source = State(value)
    target = State(f"target-{value}")
    condition = FuncCondition(lambda *_args, **_kwargs: True, f"condition-{value}")
    machine = StateMachine(source, name=f"machine-{value}")
    machine.add_state(target)
    machine.add_transition(f"trigger-{value}", source, target, condition)
    return machine


def _snapshot_machine() -> StateMachine:
    machine = StateMachine(State("initial"), name="snapshot-machine")
    machine.add_state(State("next"))
    machine.add_transition("advance", "initial", "next")
    return machine


def _render(renderer: str, machine: StateMachine, title: str) -> str:
    if renderer == "mermaid":
        return to_mermaid(machine, title=title)
    if renderer == "plantuml":
        return to_plantuml(machine, title=title)
    if renderer == "fenced":
        return to_mermaid_fenced(machine, title=title)
    if renderer == "document":
        return to_mermaid_document(machine, title=title)
    if renderer == "json":
        return json.dumps(to_json(machine), sort_keys=True, ensure_ascii=True)
    raise AssertionError(f"unknown renderer: {renderer}")


def _assert_mermaid_containment(output: str) -> None:
    lines = output.splitlines()
    assert lines.count("stateDiagram-v2") == 1
    assert all(not line.lstrip().startswith(("!include", "!import")) for line in lines)
    assert all("\x00" not in line and "\r" not in line for line in lines)


def _assert_plantuml_containment(output: str) -> None:
    lines = output.splitlines()
    assert lines[0] == "@startuml"
    assert lines[-1] == "@enduml"
    assert lines.count("@startuml") == 1
    assert lines.count("@enduml") == 1
    assert all(not line.lstrip().startswith(("!include", "!import")) for line in lines)
    assert all("\x00" not in line and "\r" not in line for line in lines)


def _assert_markdown_containment(output: str) -> None:
    lines = output.splitlines()
    assert lines.count("```mermaid") == 1
    assert sum(line == "```" for line in lines) == 1
    assert all(not line.lstrip().startswith(("!include", "!import")) for line in lines)
    assert all("\x00" not in line and "\r" not in line for line in lines)


def _assert_json_containment(output: str) -> None:
    assert "\n" not in output
    assert "\r" not in output
    assert "\x00" not in output
    assert json.loads(output)


def _assert_physical_line_containment(renderer: str, output: str) -> None:
    if renderer == "mermaid":
        _assert_mermaid_containment(output)
    elif renderer == "plantuml":
        _assert_plantuml_containment(output)
    elif renderer == "fenced":
        _assert_markdown_containment(output)
        _assert_mermaid_containment(output)
    elif renderer == "document":
        _assert_markdown_containment(output)
        _assert_mermaid_containment(output)
    elif renderer == "json":
        _assert_json_containment(output)
    else:  # pragma: no cover - fixed parameter domain above
        raise AssertionError(f"unknown renderer: {renderer}")


def test_hostile_corpus_covers_every_planned_sink_and_category() -> None:
    """Keep the required hostile corpus complete before production work starts."""

    values = {case.value for case in HOSTILE_TEXT_CASES}
    assert "" in values
    assert ALL_OTHER_CONTROLS in "".join(values)
    for token in (
        "%%",
        "!include",
        "!import",
        "@startuml",
        "@enduml",
        "```",
        "https://",
        "🙂",
        "\u0301",
        "\u202e",
        "\r\n",
        "\x00",
    ):
        assert any(token in value for value in values)


@pytest.mark.parametrize("renderer", DIAGRAM_RENDERER_NAMES)
def test_empty_state_label_uses_snapshot_position_identity(
    monkeypatch: pytest.MonkeyPatch, renderer: str
) -> None:
    """Even an empty label gets an opaque ID and one captured graph snapshot."""

    machine = _machine_with_hostile_text("")
    original_snapshot = StateMachine._graph_snapshot
    calls = 0

    def capture_once(instance: StateMachine):
        nonlocal calls
        calls += 1
        return original_snapshot(instance)

    monkeypatch.setattr(StateMachine, "_graph_snapshot", capture_once)
    output = _render(renderer, machine, "")

    assert calls == 1
    assert "s0" in output and "s1" in output
    _assert_physical_line_containment(renderer, output)


@pytest.mark.parametrize("renderer", DIAGRAM_RENDERER_NAMES)
def test_repeated_rendering_of_one_snapshot_is_byte_stable(
    monkeypatch: pytest.MonkeyPatch, renderer: str
) -> None:
    """Freeze a single captured snapshot to prove order and bytes are stable."""

    machine = _snapshot_machine()
    captured = machine._graph_snapshot()
    calls = 0

    def return_captured_snapshot(_instance: StateMachine):
        nonlocal calls
        calls += 1
        return captured

    monkeypatch.setattr(StateMachine, "_graph_snapshot", return_captured_snapshot)
    first = _render(renderer, machine, "stable")
    machine.add_state(State("late-stable-state"))
    second = _render(renderer, machine, "stable")

    assert calls == 2
    assert first.encode("utf-8") == second.encode("utf-8")


@pytest.mark.parametrize("renderer", DIAGRAM_RENDERER_NAMES)
def test_capture_barrier_prevents_a_late_mutation_from_mixing_output(
    monkeypatch: pytest.MonkeyPatch, renderer: str
) -> None:
    """A top-level renderer must retain one snapshot across a barrier mutation."""

    machine = _snapshot_machine()
    original_snapshot = StateMachine._graph_snapshot
    initial_calls = 0
    snapshot_active = False

    class SnapshotOnlyDict(dict):
        """Reject a renderer that rereads live topology after capture returns."""

        def _check(self) -> None:
            assert snapshot_active, (
                "renderer reread live topology outside snapshot capture"
            )

        def __contains__(self, key: object) -> bool:
            self._check()
            return super().__contains__(key)

        def __getitem__(self, key: str):
            self._check()
            return super().__getitem__(key)

        def get(self, key: str, default: object = None):
            self._check()
            return super().get(key, default)

        def items(self):
            self._check()
            return super().items()

        def keys(self):
            self._check()
            return super().keys()

        def __iter__(self):
            self._check()
            return super().__iter__()

    original_states = machine._states
    original_transitions = machine._transitions
    machine._states = SnapshotOnlyDict(original_states)
    machine._transitions = SnapshotOnlyDict(original_transitions)

    def count_first_capture(instance: StateMachine):
        nonlocal initial_calls, snapshot_active
        initial_calls += 1
        snapshot_active = True
        try:
            return original_snapshot(instance)
        finally:
            snapshot_active = False

    monkeypatch.setattr(StateMachine, "_graph_snapshot", count_first_capture)
    _render(renderer, machine, "before-barrier")
    assert initial_calls == 1
    machine._states = original_states
    machine._transitions = original_transitions

    entered = threading.Barrier(2, timeout=5)
    continue_render = threading.Barrier(2, timeout=5)
    barrier_calls = 0
    rendered: list[str] = []

    def capture_then_pause(instance: StateMachine):
        nonlocal barrier_calls
        barrier_calls += 1
        snapshot = original_snapshot(instance)
        entered.wait()
        continue_render.wait()
        return snapshot

    def render_in_thread() -> None:
        rendered.append(_render(renderer, machine, "after-barrier"))

    monkeypatch.setattr(StateMachine, "_graph_snapshot", capture_then_pause)
    worker = threading.Thread(target=render_in_thread)
    worker.start()
    entered.wait()
    machine.add_state(State("late-after-snapshot"))
    continue_render.wait()
    worker.join(timeout=5)

    assert not worker.is_alive()
    assert barrier_calls == 1
    assert "late-after-snapshot" not in rendered[0]


@pytest.mark.parametrize("renderer", DIAGRAM_RENDERER_NAMES)
@pytest.mark.parametrize("case", HOSTILE_TEXT_CASES[1:], ids=lambda case: case.name)
def test_hostile_caller_text_stays_inert_on_one_physical_line(
    monkeypatch: pytest.MonkeyPatch, renderer: str, case: HostileTextCase
) -> None:
    """Every label, trigger, condition, title, and document field is inert data."""

    machine = _machine_with_hostile_text(case.value)
    if renderer == "json":
        original_snapshot = StateMachine._graph_snapshot
        snapshot_active = False

        class SnapshotOnlyDict(dict):
            def _check(self) -> None:
                assert snapshot_active, (
                    "JSON reread live topology outside snapshot capture"
                )

            def __iter__(self):
                self._check()
                return super().__iter__()

            def items(self):
                self._check()
                return super().items()

            def get(self, key: str, default: object = None):
                self._check()
                return super().get(key, default)

        machine._states = SnapshotOnlyDict(machine._states)
        machine._transitions = SnapshotOnlyDict(machine._transitions)

        def capture_only(instance: StateMachine):
            nonlocal snapshot_active
            snapshot_active = True
            try:
                return original_snapshot(instance)
            finally:
                snapshot_active = False

        monkeypatch.setattr(StateMachine, "_graph_snapshot", capture_only)

    output = _render(renderer, machine, case.value)

    if renderer == "plantuml" and case.value in {"@startuml", "@enduml"}:
        # These are the fixed outer grammar delimiters, not caller text.
        assert output.count(case.value) == 1
    else:
        assert case.value not in output
    _assert_physical_line_containment(renderer, output)


@pytest.mark.parametrize("renderer", DIAGRAM_RENDERER_NAMES)
def test_old_sanitizer_collisions_receive_unique_opaque_ids(renderer: str) -> None:
    """`a-b` and `a_b` must not share an identifier after rendering."""

    machine = StateMachine(State("a-b"), name="collision")
    machine.add_state(State("a_b"))
    machine.add_transition("go", "a-b", "a_b")
    output = _render(renderer, machine, "collision")
    aliases = tuple(re.findall(r"\bas (s\d+)$", output, flags=re.MULTILINE))

    assert aliases == ("s0", "s1")
    assert len(set(aliases)) == 2
    _assert_physical_line_containment(renderer, output)


def test_fenced_renderer_composes_the_private_snapshot_renderer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fenced output must not call a public renderer that could recapture."""

    machine = _snapshot_machine()

    def public_renderer_must_not_be_called(*_args: object, **_kwargs: object) -> str:
        raise AssertionError("fenced output recaptured through to_mermaid")

    monkeypatch.setattr(visualization, "to_mermaid", public_renderer_must_not_be_called)
    assert "stateDiagram-v2" in to_mermaid_fenced(machine)


def test_document_composes_private_fenced_output_and_captures_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Document output keeps one snapshot instead of chaining public helpers."""

    machine = _snapshot_machine()
    original_snapshot = StateMachine._graph_snapshot
    calls = 0

    def capture_once(instance: StateMachine):
        nonlocal calls
        calls += 1
        return original_snapshot(instance)

    def public_fence_must_not_be_called(*_args: object, **_kwargs: object) -> str:
        raise AssertionError("document output recaptured through to_mermaid_fenced")

    monkeypatch.setattr(StateMachine, "_graph_snapshot", capture_once)
    monkeypatch.setattr(
        visualization, "to_mermaid_fenced", public_fence_must_not_be_called
    )
    assert "stateDiagram-v2" in to_mermaid_document(machine)
    assert calls == 1


def test_json_uses_one_snapshot_and_publishes_sparse_structured_analysis(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """JSON must not derive live traversal facts after its single capture."""

    machine = _snapshot_machine()
    assert machine.trigger("advance").success is True
    original_snapshot = StateMachine._graph_snapshot
    calls = 0

    def capture_once(instance: StateMachine):
        nonlocal calls
        calls += 1
        return original_snapshot(instance)

    monkeypatch.setattr(StateMachine, "_graph_snapshot", capture_once)
    payload = to_json(machine)

    assert calls == 1
    assert payload["topology"]["initial"] == "initial"
    assert payload["topology"]["current"] == "next"
    assert payload["topology"]["sparse_adjacency"]["states"] == ["initial", "next"]
    assert payload["analysis"]["cyclic_components"] == []
    assert payload["analysis"]["structural_depth"] == 1
    assert payload["analysis"]["depth_interpretation"] == "dag_longest_path"
    assert payload["analysis"]["diagnostic_status"]["complete"] is True
    assert "adjacency_matrix" not in payload["topology"]


def test_dense_output_is_opt_in_preflighted_and_stale_matrices_are_rejected() -> None:
    """Dense compatibility data needs an explicit budgeted request or exact match."""

    machine = _snapshot_machine()
    exact = DiagnosticLimits(max_dense_cells=4)
    payload = to_json(machine, include_adjacency=True, limits=exact)
    assert payload["topology"]["adjacency_matrix"]["matrix"] == [[[], [0]], [[], []]]

    with pytest.raises(DiagnosticBudgetExceeded):
        to_json(
            machine,
            include_adjacency=True,
            limits=DiagnosticLimits(max_dense_cells=3),
        )

    adjacency = FSMValidator(machine).get_adjacency_matrix()
    machine.add_state(State("late"))
    with pytest.raises(
        ValueError, match="adjacency matrix does not match captured snapshot"
    ):
        to_mermaid_document(machine, adjacency_matrix=adjacency)
