"""Interpreted warning boundaries for retained construction compatibility APIs.

The core runtime is optionally compiled by mypyc. Its native frames cannot
provide precise user warning locations, so these deliberately cold wrappers
retain ordinary Python-frame semantics while delegating all topology work to
the canonical private workers on ``StateMachine``.
"""

from __future__ import annotations

import time
import warnings
from functools import wraps
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    List,
    MutableMapping,
    Optional,
    Sequence,
    Union,
)

if TYPE_CHECKING:
    from .core import State, StateMachine, _TransitionRow


def _warn_deprecated_construction(message: str) -> None:
    """Emit a warning at the user call site through the Python wrappers."""
    warnings.warn(message, DeprecationWarning, stacklevel=3)


def install_construction_compat(
    *,
    state_machine: Any,
    module_globals: MutableMapping[str, object],
    from_states_message: str,
    quick_build_message: str,
    simple_fsm_message: str,
    quick_fsm_message: str,
) -> None:
    """Install caller-attributed, interpreted compatibility entry points."""
    original_from_states = state_machine.from_states
    original_quick_build = state_machine.quick_build

    def from_states(
        cls: type[StateMachine],
        *state_names: str,
        initial: Optional[str] = None,
        name: str = "FSM",
        clock: Callable[[], float] = time.monotonic,
    ) -> StateMachine:
        _warn_deprecated_construction(from_states_message)
        return getattr(cls, "_from_states_compat")(
            *state_names, initial=initial, name=name, clock=clock
        )

    def quick_build(
        cls: type[StateMachine],
        initial_state: Union[str, State],
        transitions: Sequence[_TransitionRow],
        states: Optional[List[Union[str, State]]] = None,
        name: str = "FSM",
        clock: Callable[[], float] = time.monotonic,
    ) -> StateMachine:
        _warn_deprecated_construction(quick_build_message)
        return getattr(cls, "_quick_build_compat")(
            initial_state,
            transitions,
            states=states,
            name=name,
            clock=clock,
        )

    def simple_fsm(
        *state_names: str,
        initial: Optional[str] = None,
        name: str = "FSM",
        clock: Callable[[], float] = time.monotonic,
    ) -> StateMachine:
        _warn_deprecated_construction(simple_fsm_message)
        return state_machine._from_states_compat(
            *state_names, initial=initial, name=name, clock=clock
        )

    def quick_fsm(
        initial_state: str,
        transitions: List[_TransitionRow],
        name: str = "FSM",
        *,
        clock: Callable[[], float] = time.monotonic,
    ) -> StateMachine:
        _warn_deprecated_construction(quick_fsm_message)
        return state_machine._quick_build_compat(
            initial_state, transitions, name=name, clock=clock
        )

    if hasattr(original_from_states, "__func__"):
        from_states = wraps(original_from_states.__func__)(from_states)
    if hasattr(original_quick_build, "__func__"):
        quick_build = wraps(original_quick_build.__func__)(quick_build)

    setattr(state_machine, "from_states", classmethod(from_states))
    setattr(state_machine, "quick_build", classmethod(quick_build))
    module_globals["simple_fsm"] = simple_fsm
    module_globals["quick_fsm"] = quick_fsm
