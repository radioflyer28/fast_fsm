"""
Visualization utilities for Fast FSM state machines.

Intentionally separate from the core ``StateMachine`` so the runtime stays
lightweight. Import this module only when you need to produce diagram output.

Example::

    from fast_fsm import StateMachine, to_mermaid

    fsm = StateMachine.quick_build(
        "idle",
        [("start", "idle", "running"), ("stop", "running", "idle")],
        name="Demo",
    )
    print(to_mermaid(fsm))
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict
from typing import TYPE_CHECKING, Any, cast

from ._diagnostics import (
    DiagnosticLimits,
    _DiagnosticBudget,
    _DiagnosticGraph,
    _dense_adjacency,
    _escape_markdown_text,
    _graph_from_snapshot,
    _reachable_indices,
    _sparse_adjacency,
    _strongly_connected_components,
    _structural_depth,
)

if TYPE_CHECKING:
    from .core import StateMachine


_SAFE_DIAGRAM_TEXT = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _.-"
)


def _opaque_state_ids(graph: _DiagnosticGraph) -> tuple[str, ...]:
    """Allocate the only diagram identities from immutable snapshot position."""
    return tuple(f"s{position}" for position in range(len(graph.state_names)))


def _escape_mermaid_text(value: str) -> str:
    """Encode caller text as inert Mermaid label/comment content on one line."""
    return "".join(
        character if character in _SAFE_DIAGRAM_TEXT else f"&#x{ord(character):04X};"
        for character in value
    )


def _escape_plantuml_text(value: str) -> str:
    """Encode caller text as inert PlantUML label/title content on one line."""
    return "".join(
        character
        if character in _SAFE_DIAGRAM_TEXT
        else (
            f"\\u{ord(character):04X}"
            if ord(character) <= 0xFFFF
            else f"\\U{ord(character):08X}"
        )
        for character in value
    )


def _escape_markdown_heading(value: str) -> str:
    """Encode one caller heading as inert Markdown text on one physical line."""
    return _escape_markdown_text(value)


def _escape_markdown_cell(value: str) -> str:
    """Encode one caller table cell as inert Markdown text on one physical line."""
    return _escape_markdown_text(value)


def _capture_diagnostic_graph(
    fsm: "StateMachine", limits: DiagnosticLimits | None
) -> tuple[Any, _DiagnosticGraph, _DiagnosticBudget]:
    """Capture one immutable graph and initialize its one shared renderer ledger."""
    snapshot = fsm._graph_snapshot()
    return snapshot, _graph_from_snapshot(snapshot), _DiagnosticBudget(limits)


def _transition_label(
    trigger: str,
    condition_name: str | None,
    priority: int,
    *,
    show_conditions: bool,
    escape: Any,
) -> str:
    """Build a label from scalar snapshot fields without evaluating conditions."""
    label = escape(trigger)
    if show_conditions and condition_name is not None:
        label = f"{label} [{escape(condition_name)}]"
    return f"{label} [priority {priority}]"


def _append_rendered_line(
    lines: list[str], budget: _DiagnosticBudget, *, stage: str, line: str
) -> None:
    """Reserve one rendered physical line before exposing it in diagram output."""
    budget.reserve_result(stage=stage)
    lines.append(line)


def _to_mermaid_from_snapshot(
    _snapshot: Any,
    graph: _DiagnosticGraph,
    budget: _DiagnosticBudget,
    *,
    title: str | None,
    show_conditions: bool,
) -> str:
    """Render one already-captured graph as a collision-free Mermaid diagram."""
    state_ids = _opaque_state_ids(graph)
    lines: list[str] = []
    if title is not None:
        _append_rendered_line(
            lines,
            budget,
            stage="mermaid.title",
            line=f"%% {_escape_mermaid_text(title)}",
        )
    _append_rendered_line(lines, budget, stage="mermaid.header", line="stateDiagram-v2")

    for state_index, state_name in enumerate(graph.state_names):
        budget.reserve_work(stage="mermaid.state")
        _append_rendered_line(
            lines,
            budget,
            stage="mermaid.state",
            line=f'    state "{_escape_mermaid_text(state_name)}" as {state_ids[state_index]}',
        )

    if graph.initial_index is not None:
        _append_rendered_line(
            lines,
            budget,
            stage="mermaid.initial",
            line=f"    [*] --> {state_ids[graph.initial_index]}",
        )

    for edge in graph.edges:
        budget.reserve_work(stage="mermaid.edge")
        label = _transition_label(
            edge.trigger,
            edge.condition_name,
            edge.priority,
            show_conditions=show_conditions,
            escape=_escape_mermaid_text,
        )
        _append_rendered_line(
            lines,
            budget,
            stage="mermaid.edge",
            line=f"    {state_ids[edge.from_index]} --> {state_ids[edge.to_index]} : {label}",
        )

    return "\n".join(lines)


def _to_plantuml_from_snapshot(
    _snapshot: Any,
    graph: _DiagnosticGraph,
    budget: _DiagnosticBudget,
    *,
    title: str | None,
    show_conditions: bool,
) -> str:
    """Render one already-captured graph as a collision-free PlantUML diagram."""
    state_ids = _opaque_state_ids(graph)
    lines: list[str] = []
    _append_rendered_line(lines, budget, stage="plantuml.open", line="@startuml")
    if title is not None:
        _append_rendered_line(
            lines,
            budget,
            stage="plantuml.title",
            line=f"title {_escape_plantuml_text(title)}",
        )

    for state_index, state_name in enumerate(graph.state_names):
        budget.reserve_work(stage="plantuml.state")
        _append_rendered_line(
            lines,
            budget,
            stage="plantuml.state",
            line=f'state "{_escape_plantuml_text(state_name)}" as {state_ids[state_index]}',
        )

    if graph.initial_index is not None:
        _append_rendered_line(
            lines,
            budget,
            stage="plantuml.initial",
            line=f"[*] --> {state_ids[graph.initial_index]}",
        )

    has_outgoing = [False] * len(graph.state_names)
    for edge in graph.edges:
        budget.reserve_work(stage="plantuml.edge")
        has_outgoing[edge.from_index] = True
        label = _transition_label(
            edge.trigger,
            edge.condition_name,
            edge.priority,
            show_conditions=show_conditions,
            escape=_escape_plantuml_text,
        )
        _append_rendered_line(
            lines,
            budget,
            stage="plantuml.edge",
            line=f"{state_ids[edge.from_index]} --> {state_ids[edge.to_index]} : {label}",
        )

    for state_index, has_edge in enumerate(has_outgoing):
        if not has_edge:
            budget.reserve_work(stage="plantuml.terminal")
            _append_rendered_line(
                lines,
                budget,
                stage="plantuml.terminal",
                line=f"{state_ids[state_index]} --> [*]",
            )

    _append_rendered_line(lines, budget, stage="plantuml.close", line="@enduml")
    return "\n".join(lines)


def to_mermaid(
    fsm: "StateMachine",
    *,
    title: str | None = None,
    show_conditions: bool = True,
    limits: DiagnosticLimits | None = None,
) -> str:
    """
    Generate a Mermaid ``stateDiagram-v2`` diagram from a StateMachine.

    This function is intentionally *not* a method on ``StateMachine`` so the
    core runtime carries zero visualization overhead.  Works equally with
    ``StateMachine`` and ``AsyncStateMachine``.

    Args:
        fsm: The state machine to visualize.
        title: Optional diagram title (rendered as a Mermaid ``%%`` comment).
        show_conditions: When ``True``, condition names are appended to
            transition labels in ``[brackets]``. Candidate priorities are
            always shown. Defaults to ``True``.
        limits: Optional finite diagnostic budget for this one captured graph.

    Returns:
        A Mermaid ``stateDiagram-v2`` string ready to paste into any Mermaid
        renderer (GitHub README, VS Code Markdown Preview, mermaid.live, etc.)

    Example::

        >>> from fast_fsm import StateMachine, to_mermaid
        >>> fsm = StateMachine.quick_build(
        ...     "idle",
        ...     [("start", "idle", "running"), ("stop", "running", "idle")],
        ... )
        >>> print(to_mermaid(fsm))
        stateDiagram-v2
            state "idle" as s0
            state "running" as s1
            [*] --> s0
            s0 --> s1 : start [priority 0]
            s1 --> s0 : stop [priority 0]
    """
    snapshot, graph, budget = _capture_diagnostic_graph(fsm, limits)
    return _to_mermaid_from_snapshot(
        snapshot,
        graph,
        budget,
        title=title,
        show_conditions=show_conditions,
    )


def to_plantuml(
    fsm: "StateMachine",
    *,
    title: str | None = None,
    show_conditions: bool = True,
    limits: DiagnosticLimits | None = None,
) -> str:
    """
    Generate a PlantUML state diagram string from a StateMachine.

    Args:
        fsm: The state machine to visualize.
        title: Optional diagram title (rendered with the ``title`` keyword).
        show_conditions: When ``True``, condition names are appended to
            transition labels in ``[brackets]``. Candidate priorities are
            always shown. Defaults to ``True``.
        limits: Optional finite diagnostic budget for this one captured graph.

    Returns:
        A PlantUML ``@startuml`` / ``@enduml`` string.

    Example::

        >>> from fast_fsm import StateMachine, to_plantuml
        >>> fsm = StateMachine.quick_build(
        ...     "idle",
        ...     [("start", "idle", "running"), ("stop", "running", "idle")],
        ... )
        >>> print(to_plantuml(fsm))
        @startuml
        state "idle" as s0
        state "running" as s1
        [*] --> s0
        s0 --> s1 : start [priority 0]
        s1 --> s0 : stop [priority 0]
        @enduml
    """
    snapshot, graph, budget = _capture_diagnostic_graph(fsm, limits)
    return _to_plantuml_from_snapshot(
        snapshot,
        graph,
        budget,
        title=title,
        show_conditions=show_conditions,
    )


def _quality_from_snapshot(
    fsm: "StateMachine",
    snapshot: Any,
    graph: _DiagnosticGraph,
    budget: _DiagnosticBudget,
) -> dict[str, object]:
    """Build legacy quality fields without a second snapshot or budget ledger."""
    from .validation import EnhancedFSMValidator

    validator = EnhancedFSMValidator.__new__(EnhancedFSMValidator)
    validator._design_style_threshold = (
        EnhancedFSMValidator.DEFAULT_DESIGN_STYLE_THRESHOLD
    )
    validator._min_transitions_for_style = (
        EnhancedFSMValidator.DEFAULT_MIN_TRANSITIONS_FOR_STYLE
    )
    validator._completeness_weight = EnhancedFSMValidator.DEFAULT_COMPLETENESS_WEIGHT
    validator._snapshot = snapshot
    validator.fsm = fsm
    validator._report_name = snapshot.name
    validator.states = set(graph.state_names)
    validator.transitions = defaultdict(lambda: defaultdict(set))
    validator.events = set()
    validator.initial_state = graph.initial_state_name
    validator.current_state = graph.current_state_name
    validator._diagnostic_graph = graph
    validator._budget = budget
    for edge in graph.edges:
        from_state = graph.state_names[edge.from_index]
        to_state = graph.state_names[edge.to_index]
        validator.transitions[from_state][edge.trigger].add(to_state)
        validator.events.add(edge.trigger)
    validator.issues = []
    validator.recommendations = []
    validator.metrics = {}
    validator._analyze_comprehensive()
    score = validator.get_validation_score()
    issues = sorted(
        (
            {
                "severity": issue.severity,
                "category": issue.category,
                "message": issue.description,
            }
            for issue in validator.issues
        ),
        key=lambda issue: (
            str(issue["severity"]),
            str(issue["category"]),
            str(issue["message"]),
        ),
    )
    return {
        "completeness_score": score["completeness_score"],
        "structural_score": score["structural_score"],
        "overall_score": score["overall_score"],
        "grade": score["grade"],
        "issues": issues,
    }


def _to_json_from_snapshot(
    fsm: "StateMachine",
    snapshot: Any,
    graph: _DiagnosticGraph,
    budget: _DiagnosticBudget,
    *,
    include_adjacency: bool,
) -> dict[str, object]:
    """Return stable structured JSON data from one snapshot, graph, and ledger."""
    reachable_indices = _reachable_indices(graph, budget)
    reachable_set = set(reachable_indices)
    unreachable: list[str] = []
    terminal: list[str] = []
    for state_index, state_name in enumerate(graph.state_names):
        budget.reserve_work(stage="json.state")
        if state_index not in reachable_set:
            budget.reserve_result(stage="json.unreachable")
            unreachable.append(state_name)
        if not graph.forward[state_index]:
            budget.reserve_result(stage="json.terminal")
            terminal.append(state_name)

    components = _strongly_connected_components(graph, budget)
    depth = _structural_depth(graph, budget)
    sparse = _sparse_adjacency(graph, budget)
    sparse_states = cast(tuple[str, ...], sparse["states"])
    sparse_events = cast(tuple[str, ...], sparse["events"])
    sparse_edges = cast(tuple[dict[str, object], ...], sparse["edges"])
    sparse_topology = {
        "states": list(sparse_states),
        "events": list(sparse_events),
        "edges": [dict(edge) for edge in sparse_edges],
    }
    transitions: list[dict[str, object]] = []
    for edge in graph.edges:
        budget.reserve_work(stage="json.transition")
        budget.reserve_result(stage="json.transition")
        transitions.append(
            {
                "trigger": edge.trigger,
                "from": graph.state_names[edge.from_index],
                "to": graph.state_names[edge.to_index],
                "has_guard": edge.has_guard,
                "priority": edge.priority,
            }
        )

    topology: dict[str, object] = {
        "states": list(graph.state_names),
        "initial": graph.initial_state_name,
        "current": graph.current_state_name,
        "transitions": transitions,
        "sparse_adjacency": sparse_topology,
    }
    if include_adjacency:
        topology["adjacency_matrix"] = _dense_adjacency(graph, budget)

    cyclic_members = [
        state_name for component in components for state_name in component
    ]
    quality = _quality_from_snapshot(fsm, snapshot, graph, budget)
    status = asdict(budget.status)
    return {
        "topology": topology,
        "analysis": {
            "reachability": {
                "reachable": [graph.state_names[index] for index in reachable_indices],
                "unreachable": unreachable,
                "terminal": terminal,
            },
            "cycles": {
                "has_cycles": bool(components),
                "states_in_cycles": cyclic_members,
            },
            "cyclic_components": [list(component) for component in components],
            "structural_depth": depth["depth"],
            "depth_interpretation": depth["interpretation"],
            "diagnostic_status": status,
            "quality": quality,
        },
    }


def to_json(
    fsm: "StateMachine",
    *,
    limits: DiagnosticLimits | None = None,
    include_adjacency: bool = False,
) -> dict[str, object]:
    """Return a stable, bounded JSON-ready topology and structural analysis.

    The returned ``topology`` declares ``initial`` separately from the runtime
    ``current`` state, preserves snapshot order, and uses sparse adjacency by
    default.  Set ``include_adjacency=True`` for the preflighted dense
    compatibility matrix.  Budget exhaustion raises ``DiagnosticBudgetExceeded``
    rather than returning a partial payload.
    """
    snapshot, graph, budget = _capture_diagnostic_graph(fsm, limits)
    return _to_json_from_snapshot(
        fsm,
        snapshot,
        graph,
        budget,
        include_adjacency=include_adjacency,
    )


def to_mermaid_fenced(
    fsm: "StateMachine",
    *,
    title: str | None = None,
    show_conditions: bool = True,
    limits: DiagnosticLimits | None = None,
) -> str:
    """
    Like :func:`to_mermaid` but wraps the output in ````mermaid`` fences for
    direct embedding in Markdown documents.

    Args:
        fsm: The state machine to visualize.
        title: Optional diagram title (rendered as a Mermaid ``%%`` comment).
        show_conditions: When ``True``, condition names are appended to
            transition labels. Candidate priorities are always shown.
            Defaults to ``True``.
        limits: Optional finite diagnostic budget for this one captured graph.

    Returns:
        A Markdown fenced code block string::

            ```mermaid
            stateDiagram-v2
                ...
            ```

    Example::

        >>> from fast_fsm import StateMachine, to_mermaid_fenced
        >>> fsm = StateMachine.quick_build(
        ...     "idle",
        ...     [("start", "idle", "running"), ("stop", "running", "idle")],
        ... )
        >>> print(to_mermaid_fenced(fsm))
        ```mermaid
        stateDiagram-v2
            state "idle" as s0
            state "running" as s1
            [*] --> s0
            s0 --> s1 : start [priority 0]
            s1 --> s0 : stop [priority 0]
        ```
    """
    snapshot, graph, budget = _capture_diagnostic_graph(fsm, limits)
    return _to_mermaid_fenced_from_snapshot(
        snapshot,
        graph,
        budget,
        title=title,
        show_conditions=show_conditions,
    )


def _to_mermaid_fenced_from_snapshot(
    snapshot: Any,
    graph: _DiagnosticGraph,
    budget: _DiagnosticBudget,
    *,
    title: str | None,
    show_conditions: bool,
) -> str:
    """Fence one already-rendered snapshot diagram without another capture."""
    budget.reserve_result(stage="mermaid.fence.open")
    diagram = _to_mermaid_from_snapshot(
        snapshot,
        graph,
        budget,
        title=title,
        show_conditions=show_conditions,
    )
    budget.reserve_result(stage="mermaid.fence.close")
    return f"```mermaid\n{diagram}\n```"


def _adjacency_mismatch() -> ValueError:
    """Return the fixed, non-leaking compatibility failure for stale matrices."""
    return ValueError("adjacency matrix does not match captured snapshot")


def _validate_adjacency_matrix(
    adjacency_matrix: object,
    graph: _DiagnosticGraph,
    budget: _DiagnosticBudget,
) -> dict[str, object]:
    """Verify a caller's dense matrix against this exact captured graph."""
    if not isinstance(adjacency_matrix, dict):
        raise _adjacency_mismatch()

    states = adjacency_matrix.get("states")
    transitions = adjacency_matrix.get("transitions")
    matrix = adjacency_matrix.get("matrix")
    expected_states = list(graph.state_names)
    expected_events = sorted({edge.trigger for edge in graph.edges})
    if (
        not isinstance(states, list)
        or states != expected_states
        or not isinstance(transitions, list)
        or not isinstance(matrix, list)
        or (
            "events" in adjacency_matrix
            and adjacency_matrix["events"] != expected_events
        )
    ):
        raise _adjacency_mismatch()

    state_count = len(expected_states)
    budget.reserve_dense_cells(
        stage="document.adjacency.preflight", amount=state_count * state_count
    )
    if len(matrix) != state_count or any(
        not isinstance(row, list) or len(row) != state_count for row in matrix
    ):
        raise _adjacency_mismatch()

    expected_cells: dict[tuple[int, int], list[int]] = {}
    for edge_index, edge in enumerate(graph.edges):
        budget.reserve_work(stage="document.adjacency.transition")
        expected_transition = {
            "idx": edge_index,
            "from_state_idx": edge.from_index,
            "from_state": graph.state_names[edge.from_index],
            "to_state_idx": edge.to_index,
            "to_state": graph.state_names[edge.to_index],
            "event_idx": expected_events.index(edge.trigger),
            "event": edge.trigger,
            "priority": edge.priority,
        }
        if (
            edge_index >= len(transitions)
            or not isinstance(transitions[edge_index], dict)
            or transitions[edge_index] != expected_transition
            or type(transitions[edge_index].get("priority")) is not int
        ):
            raise _adjacency_mismatch()
        expected_cells.setdefault((edge.from_index, edge.to_index), []).append(
            edge_index
        )
    if len(transitions) != len(graph.edges):
        raise _adjacency_mismatch()

    for source_index, row in enumerate(matrix):
        for target_index, cell in enumerate(row):
            budget.reserve_work(stage="document.adjacency.cell")
            if cell != expected_cells.get((source_index, target_index), []):
                raise _adjacency_mismatch()
    return adjacency_matrix


def to_mermaid_document(
    fsm: "StateMachine",
    *,
    title: str | None = None,
    show_conditions: bool = True,
    adjacency_matrix: "dict | None" = None,
    include_adjacency: bool = False,
    limits: DiagnosticLimits | None = None,
) -> str:
    """
    Generate a self-contained Markdown document for a StateMachine.

    The document always contains the Mermaid state diagram wrapped in a fenced
    code block.  When *adjacency_matrix* is supplied, a full N×N adjacency table
    and a numbered transitions table are appended below the diagram.

    The adjacency data is accepted as a plain ``dict`` so that
    ``visualization.py`` has no import dependency on ``validation.py``.  Obtain
    it with::

        from fast_fsm.validation import FSMValidator

        adj = FSMValidator(fsm).get_adjacency_matrix()
        doc = to_mermaid_document(fsm, adjacency_matrix=adj)

    Args:
        fsm: The state machine to document.
        title: Document heading; defaults to ``fsm.name``.
        show_conditions: Passed through to :func:`to_mermaid`.
        adjacency_matrix: Optional dict returned by
            ``FSMValidator.get_adjacency_matrix()``.  When provided, the
            document includes a full adjacency table and a numbered transition
            list below the diagram.

    Returns:
        A Markdown string suitable for saving as ``.md`` or rendering in any
        Markdown viewer.
    """
    snapshot, graph, budget = _capture_diagnostic_graph(fsm, limits)
    return _to_mermaid_document_from_snapshot(
        snapshot,
        graph,
        budget,
        title=title,
        show_conditions=show_conditions,
        adjacency_matrix=adjacency_matrix,
        include_adjacency=include_adjacency,
    )


def _to_mermaid_document_from_snapshot(
    snapshot: Any,
    graph: _DiagnosticGraph,
    budget: _DiagnosticBudget,
    *,
    title: str | None,
    show_conditions: bool,
    adjacency_matrix: object,
    include_adjacency: bool,
) -> str:
    """Compose the full Markdown document from one graph and one ledger."""
    heading = snapshot.name if title is None else title
    lines: list[str] = []
    _append_rendered_line(
        lines,
        budget,
        stage="document.heading",
        line=f"# {_escape_markdown_heading(heading)}",
    )
    _append_rendered_line(lines, budget, stage="document.separator", line="")
    _append_rendered_line(
        lines, budget, stage="document.diagram.heading", line="## State Diagram"
    )
    _append_rendered_line(lines, budget, stage="document.separator", line="")
    lines.append(
        _to_mermaid_fenced_from_snapshot(
            snapshot,
            graph,
            budget,
            title=None,
            show_conditions=show_conditions,
        )
    )

    dense_data: dict[str, object] | None = None
    if adjacency_matrix is not None:
        dense_data = _validate_adjacency_matrix(adjacency_matrix, graph, budget)
    elif include_adjacency:
        dense_data = _dense_adjacency(graph, budget)  # type: ignore[assignment]

    if dense_data is None:
        return "\n".join(lines)

    states = dense_data["states"]
    transitions = dense_data["transitions"]
    matrix = dense_data["matrix"]
    if (
        not isinstance(states, list)
        or not isinstance(transitions, list)
        or not isinstance(matrix, list)
    ):
        raise _adjacency_mismatch()

    if states:
        _append_rendered_line(lines, budget, stage="document.separator", line="")
        _append_rendered_line(
            lines,
            budget,
            stage="document.adjacency.heading",
            line="## State Adjacency Matrix",
        )
        _append_rendered_line(lines, budget, stage="document.separator", line="")
        header_cells = [_escape_markdown_cell(str(state)) for state in states]
        _append_rendered_line(
            lines,
            budget,
            stage="document.adjacency.header",
            line="| → | " + " | ".join(header_cells) + " |",
        )
        _append_rendered_line(
            lines,
            budget,
            stage="document.adjacency.separator",
            line="|---|" + "|".join(["---"] * len(states)) + "|",
        )
        for source_index, state_name in enumerate(states):
            row_cells: list[str] = []
            row = matrix[source_index]
            if not isinstance(row, list):
                raise _adjacency_mismatch()
            for transition_indices in row:
                if not isinstance(transition_indices, list):
                    raise _adjacency_mismatch()
                if transition_indices:
                    events: list[str] = []
                    for transition_index in transition_indices:
                        if (
                            not isinstance(transition_index, int)
                            or transition_index < 0
                            or transition_index >= len(transitions)
                            or not isinstance(transitions[transition_index], dict)
                        ):
                            raise _adjacency_mismatch()
                        event = transitions[transition_index].get("event")
                        priority = transitions[transition_index].get("priority")
                        if not isinstance(event, str) or type(priority) is not int:
                            raise _adjacency_mismatch()
                        budget.reserve_result(stage="document.adjacency.candidate")
                        events.append(
                            f"`{_escape_markdown_cell(event)}` [priority {priority}]"
                        )
                    row_cells.append(", ".join(events))
                else:
                    row_cells.append("—")
            _append_rendered_line(
                lines,
                budget,
                stage="document.adjacency.row",
                line=f"| **{_escape_markdown_cell(str(state_name))}** | "
                + " | ".join(row_cells)
                + " |",
            )

    if transitions:
        _append_rendered_line(lines, budget, stage="document.separator", line="")
        _append_rendered_line(
            lines, budget, stage="document.transitions.heading", line="## Transitions"
        )
        _append_rendered_line(lines, budget, stage="document.separator", line="")
        _append_rendered_line(
            lines,
            budget,
            stage="document.transitions.header",
            line="| # | From | Event | To | Priority |",
        )
        _append_rendered_line(
            lines,
            budget,
            stage="document.transitions.separator",
            line="|---|------|-------|----|----------|",
        )
        for transition in transitions:
            if not isinstance(transition, dict):
                raise _adjacency_mismatch()
            index = transition.get("idx")
            from_state = transition.get("from_state")
            event = transition.get("event")
            to_state = transition.get("to_state")
            priority = transition.get("priority")
            if (
                not isinstance(index, int)
                or not isinstance(from_state, str)
                or not isinstance(event, str)
                or not isinstance(to_state, str)
                or type(priority) is not int
            ):
                raise _adjacency_mismatch()
            _append_rendered_line(
                lines,
                budget,
                stage="document.transitions.row",
                line=f"| {index} | {_escape_markdown_cell(from_state)} | "
                f"`{_escape_markdown_cell(event)}` | "
                f"{_escape_markdown_cell(to_state)} | {priority} |",
            )

    return "\n".join(lines)
