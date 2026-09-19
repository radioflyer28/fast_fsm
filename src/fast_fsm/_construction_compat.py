"""Interpreted warning boundaries for retained construction compatibility APIs.

The core runtime is optionally compiled by mypyc. Its native frames cannot
provide precise user warning locations, so these deliberately cold wrappers
retain ordinary Python-frame semantics while delegating all topology work to
the canonical private workers on ``StateMachine``.
"""

from __future__ import annotations

import time
import warnings
from functools import update_wrapper
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    List,
    MutableMapping,
    Optional,
    Sequence,
    Union,
    cast,
)

if TYPE_CHECKING:
    from .core import State, StateMachine, _TransitionRow


def _warn_deprecated_construction(message: str) -> None:
    """Emit a warning at the user call site through the Python wrappers."""
    warnings.warn(message, DeprecationWarning, stacklevel=3)


def _callable_metadata_source(public_callable: Any) -> Any:
    """Return the unbound metadata source when a runtime exposes one.

    Pure Python exposes a classmethod's underlying function as ``__func__``;
    mypyc may expose only the callable boundary itself.  Either form carries
    public metadata, while using the unbound form when available prevents the
    replacement classmethod from losing its first public argument to a second
    method-binding pass during ``inspect.signature()``.
    """
    return getattr(public_callable, "__func__", public_callable)


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
    # Capture every public boundary before replacement.  The native core can
    # expose classmethod callables without the pure-Python descriptor details,
    # so metadata is copied uniformly from the public callable rather than
    # conditionally reaching through ``__func__``.
    original_from_states = state_machine.from_states
    original_quick_build = state_machine.quick_build
    original_simple_fsm = cast(Callable[..., Any], module_globals["simple_fsm"])
    original_quick_fsm = cast(Callable[..., Any], module_globals["quick_fsm"])

    # ``update_wrapper`` copies forward annotations from core.py, but
    # get_type_hints() evaluates them in this interpreted wrapper module's
    # globals.  Publish the three core-only names here so runtime annotation
    # resolution remains the same in pure and mypyc-native imports.
    wrapper_globals = globals()
    wrapper_globals["State"] = module_globals["State"]
    wrapper_globals["StateMachine"] = state_machine
    wrapper_globals["_TransitionRow"] = module_globals["_TransitionRow"]

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

    # Preserve the complete public callable surface in both runtime modes.
    # Besides inspection and autodoc, the module-level identity makes pickle
    # resolve simple_fsm/quick_fsm through fast_fsm.core rather than this local
    # installer frame.
    from_states = update_wrapper(
        from_states, _callable_metadata_source(original_from_states)
    )
    quick_build = update_wrapper(
        quick_build, _callable_metadata_source(original_quick_build)
    )
    simple_fsm = update_wrapper(simple_fsm, original_simple_fsm)
    quick_fsm = update_wrapper(quick_fsm, original_quick_fsm)

    setattr(state_machine, "from_states", classmethod(from_states))
    setattr(state_machine, "quick_build", classmethod(quick_build))
    module_globals["simple_fsm"] = simple_fsm
    module_globals["quick_fsm"] = quick_fsm
