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

from typing import TYPE_CHECKING, Any

from ._diagnostics import (
    DiagnosticLimits,
    _DiagnosticBudget,
    _DiagnosticGraph,
    _graph_from_snapshot,
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


def _capture_diagnostic_graph(
    fsm: "StateMachine", limits: DiagnosticLimits | None
) -> tuple[Any, _DiagnosticGraph, _DiagnosticBudget]:
    """Capture one immutable graph and initialize its one shared renderer ledger."""
    snapshot = fsm._graph_snapshot()
    return snapshot, _graph_from_snapshot(snapshot), _DiagnosticBudget(limits)


def _transition_label(
    trigger: str,
    condition_name: str | None,
    *,
    show_conditions: bool,
    escape: Any,
) -> str:
    """Build a label from scalar snapshot fields without evaluating conditions."""
    label = escape(trigger)
    if show_conditions and condition_name is not None:
        label = f"{label} [{escape(condition_name)}]"
    return label


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
    budget.reserve_result(stage="mermaid.state_ids", amount=len(state_ids))
    lines: list[str] = []
    if title is not None:
        lines.append(f"%% {_escape_mermaid_text(title)}")
    lines.append("stateDiagram-v2")

    for state_index, state_name in enumerate(graph.state_names):
        budget.reserve_work(stage="mermaid.state")
        lines.append(
            f'    state "{_escape_mermaid_text(state_name)}" as {state_ids[state_index]}'
        )

    if graph.initial_index is not None:
        lines.append(f"    [*] --> {state_ids[graph.initial_index]}")

    for edge in graph.edges:
        budget.reserve_work(stage="mermaid.edge")
        label = _transition_label(
            edge.trigger,
            edge.condition_name,
            show_conditions=show_conditions,
            escape=_escape_mermaid_text,
        )
        lines.append(
            f"    {state_ids[edge.from_index]} --> {state_ids[edge.to_index]} : {label}"
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
    budget.reserve_result(stage="plantuml.state_ids", amount=len(state_ids))
    lines: list[str] = ["@startuml"]
    if title is not None:
        lines.append(f"title {_escape_plantuml_text(title)}")

    for state_index, state_name in enumerate(graph.state_names):
        budget.reserve_work(stage="plantuml.state")
        lines.append(
            f'state "{_escape_plantuml_text(state_name)}" as {state_ids[state_index]}'
        )

    if graph.initial_index is not None:
        lines.append(f"[*] --> {state_ids[graph.initial_index]}")

    has_outgoing = [False] * len(graph.state_names)
    for edge in graph.edges:
        budget.reserve_work(stage="plantuml.edge")
        has_outgoing[edge.from_index] = True
        label = _transition_label(
            edge.trigger,
            edge.condition_name,
            show_conditions=show_conditions,
            escape=_escape_plantuml_text,
        )
        lines.append(
            f"{state_ids[edge.from_index]} --> {state_ids[edge.to_index]} : {label}"
        )

    for state_index, has_edge in enumerate(has_outgoing):
        if not has_edge:
            budget.reserve_work(stage="plantuml.terminal")
            lines.append(f"{state_ids[state_index]} --> [*]")

    lines.append("@enduml")
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
            transition labels in ``[brackets]``.  Defaults to ``True``.
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
            [*] --> idle
            idle --> running : start
            running --> idle : stop
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
            transition labels in ``[brackets]``.  Defaults to ``True``.
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
        [*] --> idle
        idle --> running : start
        running --> idle : stop
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


def to_json(fsm: "StateMachine") -> dict:
    """
    Return a JSON-serialisable dict describing FSM topology plus analysis.

    The output is designed for consumption by coding agents and programmatic
    tooling.  Sections:

    - ``topology`` — states, initial state, transitions (with ``has_guard``)
    - ``analysis.reachability`` — reachable / unreachable / terminal state lists
    - ``analysis.cycles`` — whether cycles exist and which states participate
    - ``analysis.quality`` — ``EnhancedFSMValidator`` scores (``None`` if the
      validation module is unavailable)

    ``validation.py`` is imported lazily so this function adds zero import-time
    cost when the module is not installed or not needed.

    Args:
        fsm: The state machine to inspect.

    Returns:
        A plain dict safe for ``json.dumps()``.

    Example::

        >>> from fast_fsm import StateMachine, to_json
        >>> fsm = StateMachine.quick_build(
        ...     "idle",
        ...     [("start", "idle", "running"), ("stop", "running", "idle")],
        ... )
        >>> data = to_json(fsm)
        >>> data["topology"]["initial"]
        'idle'
    """
    # --- Topology -----------------------------------------------------------
    initial_name = next(iter(fsm._states))
    states_list = sorted(fsm._states.keys())
    transitions_list: list[dict] = []

    for from_name, triggers in fsm._transitions.items():
        for trigger_name, entry in triggers.items():
            transitions_list.append(
                {
                    "trigger": trigger_name,
                    "from": from_name,
                    "to": entry.to_state.name,
                    "has_guard": entry.condition is not None,
                }
            )

    topology = {
        "states": states_list,
        "initial": initial_name,
        "transitions": transitions_list,
    }

    # --- Reachability (BFS) -------------------------------------------------
    reachable: set[str] = set()
    queue = [initial_name]
    while queue:
        current = queue.pop()
        if current in reachable:
            continue
        reachable.add(current)
        for _trigger, entry in fsm._transitions.get(current, {}).items():
            to_name = entry.to_state.name
            if to_name not in reachable:
                queue.append(to_name)

    unreachable = sorted(set(fsm._states.keys()) - reachable)
    terminal = sorted(s for s in fsm._states if not fsm._transitions.get(s))

    reachability = {
        "reachable": sorted(reachable),
        "unreachable": unreachable,
        "terminal": terminal,
    }

    # --- Cycle detection (DFS with colour) ----------------------------------
    WHITE, GREY, BLACK = 0, 1, 2
    colour: dict[str, int] = {s: WHITE for s in fsm._states}
    states_in_cycles: set[str] = set()

    def _dfs(node: str) -> None:
        colour[node] = GREY
        for _trigger, entry in fsm._transitions.get(node, {}).items():
            successor = entry.to_state.name
            if colour.get(successor) == GREY:
                # Back-edge → cycle involving both nodes
                states_in_cycles.add(node)
                states_in_cycles.add(successor)
            elif colour.get(successor) == WHITE:
                _dfs(successor)
        colour[node] = BLACK

    for state_name in fsm._states:
        if colour[state_name] == WHITE:
            _dfs(state_name)

    cycles = {
        "has_cycles": bool(states_in_cycles),
        "states_in_cycles": sorted(states_in_cycles),
    }

    # --- Quality (lazy import) ----------------------------------------------
    quality = None
    try:
        from fast_fsm.validation import EnhancedFSMValidator

        v = EnhancedFSMValidator(fsm)
        score_data = v.get_validation_score()
        quality = {
            "completeness_score": score_data.get("completeness_score"),
            "structural_score": score_data.get("structural_score"),
            "overall_score": score_data.get("overall_score"),
            "grade": score_data.get("grade"),
            "issues": [
                {
                    "severity": issue.severity,
                    "category": issue.category,
                    "message": issue.description,
                }
                for issue in v.issues
            ],
        }
    except Exception:
        quality = None

    analysis = {
        "reachability": reachability,
        "cycles": cycles,
        "quality": quality,
    }

    return {"topology": topology, "analysis": analysis}


def to_mermaid_fenced(
    fsm: "StateMachine",
    *,
    title: str | None = None,
    show_conditions: bool = True,
) -> str:
    """
    Like :func:`to_mermaid` but wraps the output in ````mermaid`` fences for
    direct embedding in Markdown documents.

    Args:
        fsm: The state machine to visualize.
        title: Optional diagram title (rendered as a Mermaid ``%%`` comment).
        show_conditions: When ``True``, condition names are appended to
            transition labels.  Defaults to ``True``.

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
            [*] --> idle
            idle --> running : start
            running --> idle : stop
        ```
    """
    diagram = to_mermaid(fsm, title=title, show_conditions=show_conditions)
    return f"```mermaid\n{diagram}\n```"


def to_mermaid_document(
    fsm: "StateMachine",
    *,
    title: str | None = None,
    show_conditions: bool = True,
    adjacency_matrix: "dict | None" = None,
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
    heading = title or getattr(fsm, "name", "FSM")
    lines: list[str] = [f"# {heading}", ""]

    lines.extend(["## State Diagram", ""])
    lines.append(to_mermaid_fenced(fsm, show_conditions=show_conditions))

    if adjacency_matrix is not None:
        sorted_states: list[str] = adjacency_matrix.get("states", [])
        transitions_list: list[dict] = adjacency_matrix.get("transitions", [])
        matrix: list[list[list[int]]] = adjacency_matrix.get("matrix", [])

        if sorted_states:
            lines.extend(["", "## State Adjacency Matrix", ""])
            header = "| → | " + " | ".join(sorted_states) + " |"
            separator = "|---|" + "|".join(["---"] * len(sorted_states)) + "|"
            lines.append(header)
            lines.append(separator)
            for i, from_state in enumerate(sorted_states):
                row_cells: list[str] = []
                for j in range(len(sorted_states)):
                    t_indices = matrix[i][j]
                    if t_indices:
                        events_in_cell = [
                            transitions_list[idx]["event"] for idx in t_indices
                        ]
                        row_cells.append(", ".join(f"`{e}`" for e in events_in_cell))
                    else:
                        row_cells.append("—")
                lines.append(f"| **{from_state}** | " + " | ".join(row_cells) + " |")

        if transitions_list:
            lines.extend(["", "## Transitions", ""])
            lines.append("| # | From | Event | To |")
            lines.append("|---|------|-------|----|")
            for t in transitions_list:
                lines.append(
                    f"| {t['idx']} | {t['from_state']} | `{t['event']}` | {t['to_state']} |"
                )

    return "\n".join(lines)
