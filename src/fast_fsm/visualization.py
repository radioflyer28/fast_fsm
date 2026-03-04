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
