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

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .core import StateMachine


def _mermaid_id(name: str) -> str:
    """Replace characters that are invalid in a Mermaid node identifier."""
    return re.sub(r"[^A-Za-z0-9_]", "_", name)


def to_mermaid(
    fsm: "StateMachine",
    *,
    title: str | None = None,
    show_conditions: bool = True,
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
    lines: list[str] = []

    if title:
        lines.append(f"%% {title}")

    lines.append("stateDiagram-v2")

    # Pre-compute safe Mermaid IDs and emit alias declarations where needed.
    # dict preserves insertion order, so the first entry is always the initial
    # state (StateMachine.__init__ inserts it first).
    state_ids: dict[str, str] = {}
    for state_name in fsm._states:
        sid = _mermaid_id(state_name)
        state_ids[state_name] = sid
        if sid != state_name:
            lines.append(f'    state "{state_name}" as {sid}')

    # Mark the initial state (first entry in _states).
    initial_name = next(iter(fsm._states))
    lines.append(f"    [*] --> {state_ids[initial_name]}")

    # Emit one line per transition.
    for from_name, triggers in fsm._transitions.items():
        from_id = state_ids.get(from_name, _mermaid_id(from_name))
        for trigger_name, entry in triggers.items():
            to_name = entry.to_state.name
            to_id = state_ids.get(to_name, _mermaid_id(to_name))
            label = trigger_name
            if show_conditions and entry.condition is not None:
                cond_label = getattr(entry.condition, "name", None) or str(
                    entry.condition
                )
                label = f"{trigger_name} [{cond_label}]"
            lines.append(f"    {from_id} --> {to_id} : {label}")

    return "\n".join(lines)


def to_plantuml(
    fsm: "StateMachine",
    *,
    title: str | None = None,
    show_conditions: bool = True,
) -> str:
    """
    Generate a PlantUML state diagram string from a StateMachine.

    Args:
        fsm: The state machine to visualize.
        title: Optional diagram title (rendered with the ``title`` keyword).
        show_conditions: When ``True``, condition names are appended to
            transition labels in ``[brackets]``.  Defaults to ``True``.

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
    lines: list[str] = ["@startuml"]

    if title:
        lines.append(f"title {title}")

    # Mark the initial state (first entry in _states).
    initial_name = next(iter(fsm._states))
    lines.append(f"[*] --> {initial_name}")

    # Collect states that have outgoing transitions.
    states_with_outgoing: set[str] = set()

    # Emit one line per transition.
    for from_name, triggers in fsm._transitions.items():
        for trigger_name, entry in triggers.items():
            states_with_outgoing.add(from_name)
            to_name = entry.to_state.name
            label = trigger_name
            if show_conditions and entry.condition is not None:
                cond_label = getattr(entry.condition, "name", None) or str(
                    entry.condition
                )
                label = f"{trigger_name} [{cond_label}]"
            lines.append(f"{from_name} --> {to_name} : {label}")

    # Detect terminal states (no outgoing transitions) and mark them.
    for state_name in fsm._states:
        if state_name not in states_with_outgoing:
            lines.append(f"{state_name} --> [*]")

    lines.append("@enduml")
    return "\n".join(lines)


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
