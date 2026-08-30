"""
Fast FSM Library - High-performance finite state machine implementation
Simplified version that avoids complex type constraints while maintaining performance.

Key design principles:
1. Maintain slots optimization for memory efficiency
2. Direct state management without reflection/introspection overhead
3. Minimal abstraction layers
4. Type hints for performance and clarity
5. Uses Python logging for better performance than print statements
6. Named state machines for better debugging and monitoring
7. Optional features to avoid overhead when not needed
"""

import logging
import time
from collections import deque
from typing import Optional, Dict, Any, Callable, List, Union, Tuple, cast, overload
from dataclasses import dataclass
import asyncio
from mypy_extensions import mypyc_attr
from .conditions import Condition, FuncCondition, AsyncCondition, NegatedCondition


# The machine-owned dispatch seam evaluates a declarative decorator guard before
# invoking state policy. The per-task marker suppresses only the base
# declarative class's duplicate evaluation for one exact source/trigger/target
# tuple. A marker is restored after each dispatch so nested policy calls retain
# the outer state safely in both pure Python and mypyc builds.
_prepared_declarative_guards: Dict[Optional[int], Tuple[int, str, int]] = {}


def _prepared_guard_scope_key() -> Optional[int]:
    """Return a task-local key, or the synchronous dispatch scope key."""
    try:
        task = asyncio.current_task()
    except RuntimeError:
        return None
    return id(task) if task is not None else None


def _set_prepared_declarative_guard(
    source_state: "State", trigger: str, to_state: "State"
) -> Tuple[Optional[int], Optional[Tuple[int, str, int]]]:
    """Mark one dispatch guard as prepared and return its restoration token."""
    scope_key = _prepared_guard_scope_key()
    previous = _prepared_declarative_guards.get(scope_key)
    _prepared_declarative_guards[scope_key] = (
        id(source_state),
        trigger,
        id(to_state),
    )
    return scope_key, previous


def _reset_prepared_declarative_guard(
    scope_key: Optional[int], previous: Optional[Tuple[int, str, int]]
) -> None:
    """Restore the task-local marker after one policy callback returns."""
    if previous is None:
        del _prepared_declarative_guards[scope_key]
    else:
        _prepared_declarative_guards[scope_key] = previous


def _has_prepared_declarative_guard(
    source_state: "State", trigger: str, to_state: "State"
) -> bool:
    """Return whether this base declarative check already ran in machine dispatch."""
    return _prepared_declarative_guards.get(_prepared_guard_scope_key()) == (
        id(source_state),
        trigger,
        id(to_state),
    )


def _reject_sync_awaitable(awaitable: Any) -> None:
    """Close a newly created coroutine before rejecting it in sync dispatch."""
    close = getattr(awaitable, "close", None)
    if callable(close):
        close()
    raise TypeError("Async condition requires AsyncStateMachine and trigger_async()")


def _is_awaitable(value: Any) -> bool:
    """Recognize coroutine, Future, and custom ``__await__`` protocol values."""
    return (
        asyncio.iscoroutine(value)
        or asyncio.isfuture(value)
        or hasattr(value, "__await__")
    )


@mypyc_attr(native_class=False)
class TransitionError(RuntimeError):
    """Raised by :meth:`TransitionResult.raise_if_failed` when a transition did not succeed.

    The originating :class:`TransitionResult` is available as the ``result`` attribute
    for callers that need to inspect trigger, from_state, or error details after catching.
    """

    def __init__(self, result: "TransitionResult") -> None:
        self.result: "TransitionResult" = result
        trigger_part = f" (trigger={result.trigger!r})" if result.trigger else ""
        from_part = f" from {result.from_state!r}" if result.from_state else ""
        error_part = f": {result.error}" if result.error else ""
        super().__init__(f"Transition failed{from_part}{trigger_part}{error_part}")


@dataclass(slots=True)
class TransitionResult:
    """Result of a state transition."""

    success: bool
    from_state: Optional[str] = None
    to_state: Optional[str] = None
    trigger: Optional[str] = None
    error: str = ""

    def raise_if_failed(self) -> "TransitionResult":
        """Raise :class:`TransitionError` if the transition did not succeed.

        Returns ``self`` unchanged on success, enabling one-liner chaining::

            to = fsm.trigger('start').raise_if_failed().to_state

        Raises:
            TransitionError: when ``self.success`` is ``False``.
        """
        if not self.success:
            raise TransitionError(self)
        return self


class TransitionRecord:
    """A single recorded transition event.

    Instances are created automatically when history recording is enabled
    via :meth:`StateMachine.enable_history`.
    """

    __slots__ = ("from_state", "trigger", "to_state", "timestamp")

    def __init__(
        self, from_state: str, trigger: str, to_state: str, timestamp: float
    ) -> None:
        self.from_state: str = from_state
        self.trigger: str = trigger
        self.to_state: str = to_state
        self.timestamp: float = timestamp

    def __repr__(self) -> str:
        return (
            f"TransitionRecord(from_state={self.from_state!r}, "
            f"trigger={self.trigger!r}, to_state={self.to_state!r})"
        )


class TransitionEntry:
    """Internal typed container for a single transition's target and guard.

    Uses ``__slots__`` for the same memory/speed profile as the raw ``dict``
    it replaces, while giving attribute access and type safety.
    """

    __slots__ = ("to_state", "condition")

    def __init__(
        self, to_state: "State", condition: Optional[Condition] = None
    ) -> None:
        self.to_state: "State" = to_state
        self.condition: Optional[Condition] = condition


@dataclass(frozen=True, slots=True)
class _GraphTransition:
    """Immutable private projection of one canonical transition edge."""

    from_state: "State"
    trigger: str
    to_state: "State"
    condition: Optional[Condition]


@dataclass(frozen=True, slots=True)
class _GraphSnapshot:
    """Immutable private projection of a machine's canonical topology.

    This is intentionally not a public serialization format.  Its tuples prevent
    callers from replacing structural rows while retaining identity-bearing State
    and Condition references for internal analysis tools.
    """

    name: str
    initial_state: "State"
    graph_version: int
    states: Tuple["State", ...]
    transitions: Tuple[_GraphTransition, ...]


@dataclass(frozen=True, slots=True)
class _PreparedTransition:
    """Fully validated private transition request awaiting one graph commit."""

    trigger: str
    sources: Tuple["State", ...]
    target: "State"
    condition: Optional[Condition]


@dataclass(frozen=True, slots=True)
class _PreparedDispatch:
    """One fresh canonical lookup and optional guard context for dispatch."""

    entry: TransitionEntry
    current_name: str
    trigger: str
    args: Tuple[Any, ...]
    condition_kwargs: Optional[Dict[str, Any]]
    declarative_handler: Optional[Dict[str, Any]]


@mypyc_attr(native_class=False)
class CompiledFuncCondition(Condition):
    """A mypyc-compiled wrapper around a callable for use as a transition guard.

    This is the **opt-in fast path** alternative to :class:`~fast_fsm.FuncCondition`.
    Because this class lives in ``core.py`` (the compiled module), its ``check()``
    method body is compiled to native machine code by mypyc.  This eliminates the
    per-call CPython bytecode interpretation overhead that the uncompiled
    :class:`~fast_fsm.FuncCondition` incurs when the guard fires on a hot
    transition path.

    **When to use this over** :class:`~fast_fsm.FuncCondition`:

    * You have measured that condition evaluation is a bottleneck (≥ 5 % of
      ``trigger()`` wall time in a profile).
    * Your guard is a simple, self-contained callable with no need for
      mixing-in additional behaviour.

    **Implementation notes** — the class uses
    ``@mypyc_attr(native_class=False)`` so that it can inherit from the
    uncompiled ``Condition`` ABC without `__slots__` conflicts.  Attribute
    storage falls back to a ``__dict__``.  The ``check()`` dispatch is
    compiled; attribute access is not.  Unlike a fully-native mypyc class,
    this class *can* be subclassed from interpreted Python — use
    :class:`~fast_fsm.FuncCondition` as a base when subclassing is needed.

    Args:
        func: Any callable ``(*args, **kwargs) -> bool``. Receives the same
            positional and sanitised keyword arguments as every other condition
            (private ``_``-prefixed keys stripped, capped at 50 items).
        name: Human-readable label.  Defaults to ``func.__name__`` when
            available, otherwise ``"compiled_func"``.
        description: Optional longer description.

    Example::

        from fast_fsm import StateMachine, CompiledFuncCondition

        is_ready = CompiledFuncCondition(lambda **kw: kw.get("ready", False))
        fsm = StateMachine.quick_build("idle", [("start", "idle", "running")])
        fsm.add_transition("go", "idle", "running", condition=is_ready)
    """

    def __init__(
        self,
        func: Callable[..., bool],
        name: Optional[str] = None,
        description: str = "",
    ) -> None:
        resolved_name: str = (
            name if name is not None else getattr(func, "__name__", "compiled_func")
        )
        super().__init__(resolved_name, description)
        self.func: Callable[..., bool] = func

    def check(self, *args: Any, **kwargs: Any) -> bool:
        """Call the wrapped function and return its result."""
        return self.func(*args, **kwargs)


@mypyc_attr(allow_interpreted_subclasses=True)
class State:
    """
    Base state class for FSM states.
    Uses slots for memory efficiency.
    """

    __slots__ = ("name",)

    def __init__(self, name: str):
        self.name = name

    @classmethod
    def create(
        cls,
        name: str,
        on_enter: Optional[Callable] = None,
        on_exit: Optional[Callable] = None,
    ) -> "CallbackState":
        """
        Factory method to create a state with inline callbacks.

        Args:
            name: State name
            on_enter: Optional callback for entering the state. It receives
                ``*args`` and ``**kwargs``.
            on_exit: Optional callback for exiting the state. It receives
                ``*args`` and ``**kwargs``.

        Returns:
            CallbackState instance with configured callbacks

        Example::

            state = State.create(
                "processing",
                on_enter=lambda *args, **kwargs: print("Processing started"),
                on_exit=lambda *args, **kwargs: print("Processing finished"),
            )
        """
        return CallbackState(name, on_enter, on_exit)

    def on_enter(
        self, from_state: Optional["State"], trigger: str, *args, **kwargs
    ) -> None:
        """Called when entering this state"""
        pass

    def on_exit(
        self, to_state: Optional["State"], trigger: str, *args, **kwargs
    ) -> None:
        """Called when exiting this state"""
        pass

    def can_transition(self, trigger: str, to_state: "State", *args, **kwargs) -> bool:
        """Override to add custom transition logic"""
        return True

    def handle_event(self, event: str, *args, **kwargs) -> TransitionResult:
        """Override to handle events in this state"""
        return TransitionResult(
            False, error=f"Unhandled event '{event}' in state '{self.name}'"
        )

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}('{self.name}')"


@mypyc_attr(allow_interpreted_subclasses=True)
class CallbackState(State):
    """
    State class that allows custom callbacks to be set.
    """

    __slots__ = ("_on_enter", "_on_exit")

    def __init__(
        self,
        name: str,
        on_enter: Optional[Callable] = None,
        on_exit: Optional[Callable] = None,
    ):
        super().__init__(name)
        self._on_enter = on_enter
        self._on_exit = on_exit

    def on_enter(
        self, from_state: Optional["State"], trigger: str, *args, **kwargs
    ) -> None:
        if self._on_enter:
            self._on_enter(from_state, trigger, *args, **kwargs)

    def on_exit(
        self, to_state: Optional["State"], trigger: str, *args, **kwargs
    ) -> None:
        if self._on_exit:
            self._on_exit(to_state, trigger, *args, **kwargs)


class StateMachine:
    """
    High-performance finite state machine.
    Optimized for speed and memory efficiency using slots.
    """

    __slots__ = (
        "_name",
        "_initial_state",
        "_current_state",
        "_states",
        "_transitions",
        "_graph_version",
        "_logger",
        "_before_listeners",
        "_on_exit_listeners",
        "_on_enter_listeners",
        "_after_listeners",
        "_on_failed_callbacks",
        "_trigger_callbacks",
        "_state_exit_callbacks",
        "_state_enter_callbacks",
        "_history",
        "_history_max",
    )

    def __init__(
        self,
        initial_state: State,
        *,
        name: str = "FSM",
        logger_name: Optional[str] = None,
    ):
        """
        Initialize the state machine.

        Performance: O(1) - Constant time initialization
        Memory: ~0.2KB base overhead with slots optimization

        Args:
            initial_state: The starting state
            name: Human-readable name for this state machine
            logger_name: Name of the logger to use (defaults to 'fast_fsm.{name}')
        """
        if not isinstance(initial_state, State):
            raise TypeError(
                "initial_state must be a State instance, "
                f"got {type(initial_state).__name__}"
            )
        self._name = name
        self._initial_state = initial_state
        self._current_state = initial_state
        self._states: Dict[str, State] = {}
        self._transitions: Dict[str, Dict[str, TransitionEntry]] = {}
        self._graph_version = 0

        # Use name-based logger if not specified
        if logger_name is None:
            logger_name = f"fast_fsm.{name}"
        self._logger = logging.getLogger(logger_name)

        # Listener lists — pre-extracted bound method references for zero-overhead
        # empty checks.  Populated by add_listener().
        self._before_listeners: list = []
        self._on_exit_listeners: List[Any] = []
        self._on_enter_listeners: List[Any] = []
        self._after_listeners: List[Any] = []
        self._on_failed_callbacks: list = []
        self._trigger_callbacks: dict = {}

        # Per-state callbacks registered via on_enter() / on_exit().
        # Keyed by state name; values are lists of callables (appended in
        # registration order, all called on transition).
        self._state_exit_callbacks: Dict[str, List[Any]] = {}
        self._state_enter_callbacks: Dict[str, List[Any]] = {}

        # History — opt-in transition recording (None = disabled)
        self._history: Optional[deque[TransitionRecord]] = None
        self._history_max: int = 1000

        # Register the initial state
        self._register_state(initial_state)

    @classmethod
    def from_states(
        cls, *state_names: str, initial: Optional[str] = None, name: str = "FSM"
    ) -> "StateMachine":
        """
        Factory method to quickly create a StateMachine from state names.

        Args:
            *state_names: Names of the states to create
            initial: Name of the initial state (defaults to first state)
            name: Name for the state machine

        Returns:
            StateMachine with simple states created

        Example:
            fsm = StateMachine.from_states('idle', 'processing', 'done', initial='idle')
        """
        if not state_names:
            raise ValueError("At least one state name is required")

        # Create simple states
        states = [State(name) for name in state_names]
        initial_state = (
            states[0]
            if initial is None
            else next(s for s in states if s.name == initial)
        )

        # Create FSM
        fsm = cls(initial_state, name=name)
        for state in states:
            if state != initial_state:
                fsm.add_state(state)

        return fsm

    @classmethod
    def quick_build(
        cls,
        initial_state: Union[str, State],
        transitions: List[Tuple[str, str, str]],
        states: Optional[List[Union[str, State]]] = None,
        name: str = "FSM",
    ) -> "StateMachine":
        """
        Factory method for rapid FSM construction from transition list.

        Args:
            initial_state: Initial state name or State object
            transitions: List of (trigger, from_state, to_state) tuples
            states: Optional additional states to add
            name: Name for the state machine

        Returns:
            Configured StateMachine

        Example::

            fsm = StateMachine.quick_build(
                "idle",
                [
                    ("start", "idle", "running"),
                    ("stop", "running", "idle"),
                    ("error", "running", "error"),
                ],
            )
        """
        # Collect all state names from transitions
        all_states = set()
        if isinstance(initial_state, str):
            all_states.add(initial_state)

        for trigger, from_state, to_state in transitions:
            if isinstance(from_state, list):
                all_states.update(from_state)
            else:
                all_states.add(from_state)
            all_states.add(to_state)

        # Add additional states
        if states:
            for state in states:
                if isinstance(state, str):
                    all_states.add(state)
                else:
                    all_states.add(state.name)

        # Create state objects
        state_objects = {}
        for state_name in all_states:
            state_objects[state_name] = State(state_name)

        # Handle initial state
        if isinstance(initial_state, str):
            initial_obj = state_objects[initial_state]
        else:
            initial_obj = initial_state
            state_objects[initial_state.name] = initial_state

        # Create FSM
        fsm = cls(initial_obj, name=name)
        for state_obj in state_objects.values():
            if state_obj != initial_obj:
                fsm.add_state(state_obj)

        # Add transitions
        for trigger, from_state, to_state in transitions:
            fsm.add_transition(trigger, from_state, to_state)

        return fsm

    @classmethod
    def from_dict(
        cls,
        config: Dict[str, Any],
        *,
        name: Optional[str] = None,
        conditions: Optional[Dict[str, Union[Condition, Callable[..., bool]]]] = None,
    ) -> "StateMachine":
        """Build a :class:`StateMachine` from a plain dictionary description.

        This is the inverse of the mental model behind :meth:`snapshot` /
        :meth:`restore`: it reconstructs *topology* (states + transitions)
        from a serialisable dict, making it easy to define machines in JSON,
        YAML, or TOML config files.

        Shape of *config*::

            {
                "name":    "MyFSM",          # optional — overridden by kwarg
                "initial": "idle",           # required
                "states":  ["idle", "running", "done"],  # optional — auto-
                                             # discovered from transitions
                "transitions": [
                    {"trigger": "start",  "from": "idle",    "to": "running"},
                    {"trigger": "finish", "from": "running", "to": "done"},
                    {"trigger": "fail",   "from": ["running", "done"], "to": "error"},
                ]
            }

        ``"from"`` may be a string or a list of strings (fan-out shorthand,
        same as :meth:`add_transition`).

        Guard conditions can be attached at construction time via the
        ``conditions`` keyword argument.  Because callables are not
        serialisable, they cannot live inside *config*; pass them separately::

            config = {"initial": "idle", "transitions": [
                {"trigger": "start", "from": "idle", "to": "running"},
            ]}
            fsm = StateMachine.from_dict(
                config,
                conditions={"start": FuncCondition("ready", lambda **kw: kw.get("ready"))},
            )

        If the same trigger name appears in multiple transition entries, the
        *same* condition object is applied to all of them — consistent with
        how a named guard normally applies to a trigger regardless of source
        state.  To apply different conditions per source state, call
        :meth:`add_transition` after construction.

        Args:
            config: Dictionary describing the machine topology.
            name: Override the machine name.  Takes precedence over
                ``config["name"]`` if both are provided.
            conditions: Optional mapping of ``trigger_name → Condition``
                (or any ``(**kwargs) -> bool`` callable).  Keys that do not
                match any trigger in *config* are silently ignored.

        Returns:
            Configured :class:`StateMachine` instance.

        Raises:
            ValueError: If ``"initial"`` is missing, or any transition entry
                is missing ``"trigger"`` / ``"from"`` / ``"to"``.

        Example::

            import json
            config = json.loads(open("traffic_light.json").read())
            fsm = StateMachine.from_dict(config)
        """
        # Resolve machine name
        fsm_name: str = name or config.get("name", "FSM")

        # Validate required field
        if "initial" not in config:
            raise ValueError("from_dict: config must contain an 'initial' key.")

        initial: str = config["initial"]

        # Parse and validate the transition list
        raw_transitions = config.get("transitions", [])
        for i, entry in enumerate(raw_transitions):
            for required in ("trigger", "from", "to"):
                if required not in entry:
                    raise ValueError(
                        f"from_dict: transition[{i}] is missing required key '{required}'."
                    )

        # Collect all state names (initial + explicit list + transition endpoints)
        all_state_names: set[str] = {initial}
        explicit: List[str] = config.get("states") or []
        all_state_names.update(explicit)
        for entry in raw_transitions:
            frm = entry["from"]
            if isinstance(frm, list):
                all_state_names.update(frm)
            else:
                all_state_names.add(frm)
            all_state_names.add(entry["to"])

        # Build the machine with all discovered states
        fsm = cls.from_states(*all_state_names, initial=initial, name=fsm_name)

        # Add transitions — add_transition natively supports str-or-list from_state
        _conditions: Dict[str, Union[Condition, Callable[..., bool]]] = conditions or {}
        for entry in raw_transitions:
            cond = _conditions.get(entry["trigger"])
            fsm.add_transition(
                entry["trigger"], entry["from"], entry["to"], condition=cond
            )

        return fsm

    def to_dict(self) -> Dict[str, Any]:
        """Export the machine topology as a plain dictionary.

        The returned dict is structurally compatible with :meth:`from_dict`,
        enabling full roundtrip serialisation::

            config = fsm.to_dict()
            fsm2 = StateMachine.from_dict(config)

        Guard conditions are **not** included — they are callable objects
        and therefore not serialisable.  Re-attach them via the
        ``conditions`` kwarg on :meth:`from_dict` after reconstruction.

        Returns:
            A JSON-serialisable dict with keys ``"name"``, ``"initial"``,
            ``"states"``, and ``"transitions"``.
        """
        transitions: List[Dict[str, str]] = []
        for from_name, triggers in self._transitions.items():
            for trigger_name, entry in triggers.items():
                transitions.append(
                    {
                        "trigger": trigger_name,
                        "from": from_name,
                        "to": entry.to_state.name,
                    }
                )
        return {
            "name": self._name,
            "initial": self._initial_state.name,
            "states": sorted(self._states.keys()),
            "transitions": transitions,
        }

    def enable_history(self, max_entries: Any = 1000) -> None:
        """Enable transition history recording.

        When enabled, every successful :meth:`trigger` call appends a
        :class:`TransitionRecord` to an internal bounded buffer.  The buffer
        holds at most *max_entries* records; when full the oldest entry is
        dropped.

        Calling this method again replaces the buffer (existing records are
        discarded).

        Args:
            max_entries: Maximum number of records to keep.

        Raises:
            TypeError: If ``max_entries`` is not a non-boolean integer.
            ValueError: If ``max_entries`` is zero or negative.
        """
        if type(max_entries) is bool or not isinstance(max_entries, int):
            raise TypeError("max_entries must be a positive integer")
        if max_entries <= 0:
            raise ValueError("max_entries must be a positive integer")
        self._history_max = max_entries
        self._history = deque(maxlen=max_entries)

    def disable_history(self) -> None:
        """Disable transition history recording and discard all records."""
        self._history = None

    @property
    def history(self) -> List["TransitionRecord"]:
        """Return a copy of the transition history.

        Returns an empty list when history is disabled.
        """
        if self._history is None:
            return []
        return list(self._history)

    def _register_state(self, state: State) -> bool:
        """Register an exact state identity and initialize its transition table.

        Returns ``True`` only when the registry gains a new canonical object.
        Re-registering the same object is a safe no-op; a distinct object with the
        same name is rejected before either topology dictionary changes.
        """
        if not isinstance(state, State):
            raise TypeError(
                f"state must be a State instance, got {type(state).__name__}"
            )
        existing = self._states.get(state.name)
        if existing is not None:
            if existing is state:
                return False
            raise ValueError(
                f"State name {state.name!r} is already registered with a different object"
            )
        self._states[state.name] = state
        self._transitions[state.name] = {}
        return True

    def add_state(self, state: State) -> None:
        """
        Add a state to the machine.

        Performance: O(1) - Constant time state registration
        Memory: +~32 bytes per state (slots optimization)
        """
        if self._register_state(state):
            self._graph_version += 1

    def _graph_snapshot(self) -> _GraphSnapshot:
        """Return a fresh, deterministically ordered, immutable topology view.

        The private snapshot intentionally leaves the public ``snapshot()`` and
        ``to_dict()`` schemas untouched.  It is assembled from the authoritative
        dictionaries on demand, so no stale cached structural view can escape.
        """
        states = tuple(state for _, state in sorted(self._states.items()))
        transitions = tuple(
            _GraphTransition(
                self._states[from_name], trigger, entry.to_state, entry.condition
            )
            for from_name, entries in sorted(self._transitions.items())
            for trigger, entry in sorted(entries.items())
        )
        return _GraphSnapshot(
            self._name,
            self._initial_state,
            self._graph_version,
            states,
            transitions,
        )

    def _resolve_canonical_state(self, state: Any, *, role: str) -> State:
        """Resolve a transition endpoint to its exact registered State object."""
        if isinstance(state, str):
            canonical = self._states.get(state)
            if canonical is None:
                raise ValueError(
                    f"{role} state {state!r} is not registered; "
                    "add it with add_state() before adding transitions."
                )
            return canonical
        if isinstance(state, State):
            canonical = self._states.get(state.name)
            if canonical is None:
                raise ValueError(f"{role} state {state.name!r} is not registered")
            if canonical is not state:
                raise ValueError(
                    f"{role} state {state.name!r} is not the canonical registered object"
                )
            return canonical
        raise ValueError(
            f"{role} state must be a registered state name or State object, "
            f"got {type(state).__name__}"
        )

    def _normalize_transition_request(
        self,
        trigger: str,
        from_state: Union[str, State, List[Union[str, State]]],
        to_state: Union[str, State],
        condition: Optional[Union[Condition, Callable[..., bool]]] = None,
        *,
        unless: Optional[Union[Condition, Callable[..., bool]]] = None,
    ) -> _PreparedTransition:
        """Materialize and validate a complete transition request without writing."""
        raw_sources: List[Any]
        if isinstance(from_state, list):
            raw_sources = list(from_state)
        else:
            raw_sources = [from_state]
        if not raw_sources:
            raise ValueError("transition source list cannot be empty")

        sources: List[State] = []
        source_names: set[str] = set()
        for raw_source in raw_sources:
            source = self._resolve_canonical_state(raw_source, role="source")
            if source.name in source_names:
                raise ValueError(
                    f"duplicate canonical source state {source.name!r} in one request"
                )
            source_names.add(source.name)
            sources.append(source)
        target = self._resolve_canonical_state(to_state, role="target")

        if condition is not None and unless is not None:
            raise ValueError(
                "'condition' and 'unless' are mutually exclusive — use one or the other."
            )
        if not isinstance(self, AsyncStateMachine):
            if isinstance(condition, AsyncCondition):
                raise TypeError(
                    f"AsyncCondition '{getattr(condition, 'name', condition)}' "
                    "cannot be used with a sync StateMachine. "
                    "Use AsyncStateMachine (or FSMBuilder with async auto-detection) instead."
                )
            if isinstance(unless, AsyncCondition):
                raise TypeError(
                    f"AsyncCondition '{getattr(unless, 'name', unless)}' "
                    "cannot be used with a sync StateMachine via 'unless='. "
                    "Use AsyncStateMachine (or FSMBuilder with async auto-detection) instead."
                )
        if unless is not None:
            if isinstance(unless, Condition):
                condition = NegatedCondition(unless)
            elif callable(unless):
                condition = NegatedCondition(FuncCondition(unless))
            else:
                raise TypeError(
                    f"'unless' must be a Condition or callable, got {type(unless)}"
                )
        if condition is None:
            normalized_condition: Optional[Condition] = None
        elif isinstance(condition, Condition):
            normalized_condition = condition
        elif callable(condition):
            normalized_condition = FuncCondition(condition)
        else:
            raise TypeError(
                f"Condition must be Condition or callable, got {type(condition)}"
            )
        if normalized_condition is not None:
            has_async_requirement = self._contains_async_requirement(
                normalized_condition
            )
            if not isinstance(self, AsyncStateMachine) and has_async_requirement:
                raise TypeError(
                    "AsyncCondition nested in a supported condition wrapper "
                    "cannot be used with a sync StateMachine. Use "
                    "AsyncStateMachine (or FSMBuilder with async auto-detection) instead."
                )
        return _PreparedTransition(
            trigger, tuple(sources), target, normalized_condition
        )

    def _commit_transition_plan(self, plans: Tuple[_PreparedTransition, ...]) -> None:
        """Commit a complete validated topology plan and advance once if changed."""
        final_entries: Dict[Tuple[str, str], Tuple[State, Optional[Condition]]] = {}
        for plan in plans:
            for source in plan.sources:
                final_entries[(source.name, plan.trigger)] = (
                    plan.target,
                    plan.condition,
                )
        changed = any(
            (existing := self._transitions[source_name].get(trigger)) is None
            or existing.to_state is not target
            or existing.condition is not guard
            for (source_name, trigger), (target, guard) in final_entries.items()
        )
        if not changed:
            return
        for (source_name, trigger), (target, guard) in final_entries.items():
            self._transitions[source_name][trigger] = TransitionEntry(target, guard)
        self._graph_version += 1

    def add_transition(
        self,
        trigger: str,
        from_state: Union[str, State, List[Union[str, State]]],
        to_state: Union[str, State],
        condition: Optional[Union[Condition, Callable[..., bool]]] = None,
        *,
        unless: Optional[Union[Condition, Callable[..., bool]]] = None,
    ) -> None:
        """Add a validated, canonical transition in one topology operation."""
        prepared = self._normalize_transition_request(
            trigger, from_state, to_state, condition, unless=unless
        )
        self._commit_transition_plan((prepared,))

    def add_transitions(
        self,
        transitions: List[
            Union[
                Tuple[
                    str, Union[str, State, List[Union[str, State]]], Union[str, State]
                ],
                Tuple[
                    str,
                    Union[str, State, List[Union[str, State]]],
                    Union[str, State],
                    Optional[Union[Condition, Callable[..., bool]]],
                ],
            ]
        ],
    ) -> None:
        """
        Add multiple transitions at once.

        Each entry is either a 3-tuple ``(trigger, from_state, to_state)`` or a
        4-tuple ``(trigger, from_state, to_state, condition)`` where *condition*
        follows the same rules as :meth:`add_transition` — a
        :class:`~fast_fsm.Condition` instance, a plain ``(**kwargs) -> bool``
        callable, or ``None`` / omitted for an unconditional transition.

        Args:
            transitions: List of 3- or 4-tuples describing each transition.

        Example::

            fsm.add_transitions([
                ('start', 'idle', 'running'),
                ('pause', 'running', 'paused',  lambda **kw: kw.get('pausable', True)),
                ('stop',  ['running', 'paused'], 'stopped'),
                ('reset', 'stopped', 'idle',    None),   # explicit None == no guard
            ])
        """
        prepared: List[_PreparedTransition] = []
        for entry in transitions:
            if len(entry) not in (3, 4):
                raise ValueError("each transition entry must contain 3 or 4 items")
            trigger, from_state, to_state, *rest = entry  # type: ignore[misc]
            condition: Optional[Union[Condition, Callable[..., bool]]] = (
                rest[0] if rest else None
            )
            prepared.append(
                self._normalize_transition_request(
                    trigger, from_state, to_state, condition
                )
            )
        self._commit_transition_plan(tuple(prepared))

    def add_bidirectional_transition(
        self,
        trigger1: str,
        trigger2: str,
        state1: Union[str, State],
        state2: Union[str, State],
        condition1: Optional[Union[Condition, Callable]] = None,
        condition2: Optional[Union[Condition, Callable]] = None,
        *,
        unless1: Optional[Union[Condition, Callable]] = None,
        unless2: Optional[Union[Condition, Callable]] = None,
    ) -> None:
        """
        Add transitions in both directions between two states.

        Args:
            trigger1: Trigger from state1 to state2
            trigger2: Trigger from state2 to state1
            state1: First state
            state2: Second state
            condition1: Optional condition for trigger1
            condition2: Optional condition for trigger2
            unless1: Negation shorthand for trigger1 — mutually exclusive with
                ``condition1``.  The transition fires when this condition is **False**.
            unless2: Negation shorthand for trigger2 — mutually exclusive with
                ``condition2``.

        Example::

            fsm.add_bidirectional_transition('pause', 'resume', 'running', 'paused')
            # With negation shorthand:
            is_locked = FuncCondition("locked", lambda **kw: kw.get("locked", False))
            fsm.add_bidirectional_transition('open', 'close', 'closed', 'open',
                                             unless1=is_locked)
        """
        first = self._normalize_transition_request(
            trigger1, state1, state2, condition1, unless=unless1
        )
        second = self._normalize_transition_request(
            trigger2, state2, state1, condition2, unless=unless2
        )
        self._commit_transition_plan((first, second))

    def add_emergency_transition(
        self,
        trigger: str,
        to_state: Union[str, State],
        condition: Optional[Union[Condition, Callable]] = None,
        *,
        unless: Optional[Union[Condition, Callable]] = None,
    ) -> None:
        """
        Add an emergency transition from all states to a specific state.

        Args:
            trigger: Emergency trigger name
            to_state: Target state for emergency
            condition: Optional condition for the emergency
            unless: Negation shorthand — mutually exclusive with ``condition``.
                The transition fires when this condition is **False**.

        Example::

            fsm.add_emergency_transition('emergency_stop', 'error')
            # Gated on a condition:
            fsm.add_emergency_transition('fallback', 'safe',
                                         condition=FuncCondition("critical", is_critical))
            # With negation shorthand:
            fsm.add_emergency_transition('fallback', 'safe', unless=is_safe)
        """
        prepared = self._normalize_transition_request(
            trigger,
            list(self._states.values()),
            to_state,
            condition,
            unless=unless,
        )
        self._commit_transition_plan((prepared,))

    @property
    def name(self) -> str:
        """Get the name of this state machine"""
        return self._name

    @property
    def current_state(self) -> State:
        """Get the current state"""
        return self._current_state

    @property
    def current_state_name(self) -> str:
        """Get the current state name"""
        return self._current_state.name

    @property
    def initial_state_name(self) -> str:
        """Get the name of the state the machine was initialised with."""
        return self._initial_state.name

    def is_in(self, state: Union[str, State]) -> bool:
        """Return ``True`` if the machine is currently in *state*.

        Accepts either a state name string or a :class:`State` object.
        Identity comparison (``is``) is used for objects; name comparison
        is used for strings.

        Performance: O(1) — single attribute access plus one comparison.

        Args:
            state: The state to check — either its name or the object itself.

        Returns:
            ``True`` if *state* is the current active state, ``False`` otherwise.

        Example:
            idle = State("idle")
            fsm = StateMachine(idle)
            assert fsm.is_in("idle")
            assert fsm.is_in(idle)
        """
        if isinstance(state, str):
            return self._current_state.name == state
        return self._current_state is state

    def add_listener(self, *listeners: Any) -> None:
        """Register one or more observer objects.

        Each listener is a plain Python object that may implement any subset
        of the following duck-typed protocol (all optional):

        .. code-block:: python

            class MyListener:
                def on_exit_state(self, source, target, trigger, **kwargs): ...
                def on_enter_state(self, target, source, trigger, **kwargs): ...
                def after_transition(self, source, target, trigger, **kwargs): ...

        .. rubric:: Argument semantics

        - ``source`` / ``target`` — :class:`State` objects (access ``.name`` for the string)
        - ``trigger`` — the trigger name string
        - ``**kwargs`` — forwarded from the original :meth:`trigger` call

        Bound method references are extracted at registration time so the
        hot path pays zero per-call overhead when listeners are attached and
        *no* overhead at all when the list is empty (guarded by
        ``if self._on_exit_listeners``).

        Methods that are absent on a listener are silently skipped.

        Args:
            *listeners: One or more observer objects.

        Example::

            class TransitionLogger:
                def after_transition(self, source, target, trigger, **kwargs):
                    print(f"{source.name} --[{trigger}]--> {target.name}")

            fsm.add_listener(TransitionLogger())
        """
        for listener in listeners:
            fn = getattr(listener, "before_transition", None)
            if callable(fn):
                self._before_listeners.append(fn)
            fn = getattr(listener, "on_exit_state", None)
            if callable(fn):
                self._on_exit_listeners.append(fn)
            fn = getattr(listener, "on_enter_state", None)
            if callable(fn):
                self._on_enter_listeners.append(fn)
            fn = getattr(listener, "after_transition", None)
            if callable(fn):
                self._after_listeners.append(fn)

    def on_enter(self, state_name: str, callback: Any) -> None:
        """Register a callback to fire whenever the machine enters *state_name*.

        The callback fires **after** the state's own ``on_enter`` method and
        before the machine-level ``on_enter_state`` listeners.

        Signature: ``callback(from_state: State, trigger: str, **kwargs)``

        Multiple callbacks for the same state are called in registration order.

        Args:
            state_name: Name of the state to watch.  Does not need to be
                registered yet — the callback is stored and fires once the
                state is visited.
            callback: Callable matching the signature above.

        Example::

            fsm.on_enter("running", lambda from_s, t, **kw: print("entered running"))
        """
        if state_name not in self._state_enter_callbacks:
            self._state_enter_callbacks[state_name] = []
        self._state_enter_callbacks[state_name].append(callback)

    def on_exit(self, state_name: str, callback: Any) -> None:
        """Register a callback to fire whenever the machine exits *state_name*.

        The callback fires **after** the state's own ``on_exit`` method and
        before the machine-level ``on_exit_state`` listeners.

        Signature: ``callback(to_state: State, trigger: str, **kwargs)``

        Multiple callbacks for the same state are called in registration order.

        Args:
            state_name: Name of the state to watch.  Does not need to be
                registered yet.
            callback: Callable matching the signature above.

        Example::

            fsm.on_exit("running", lambda to_s, t, **kw: print("left running"))
        """
        if state_name not in self._state_exit_callbacks:
            self._state_exit_callbacks[state_name] = []
        self._state_exit_callbacks[state_name].append(callback)

    def after_transition(self, callback: Any) -> None:
        """Register a callback fired after every successful transition.

        Args:
            callback: Callable ``fn(source, target, trigger, **kwargs)``.
        """
        self._after_listeners.append(callback)

    def on_failed(self, callback: Any) -> None:
        """Register a callback fired whenever trigger() returns a failed result.

        Args:
            callback: Callable ``fn(trigger, from_state, error, **kwargs)``.
        """
        self._on_failed_callbacks.append(callback)

    def on_trigger(self, trigger_name: str, callback: Any) -> None:
        """Register a callback fired after a successful transition for trigger_name.

        Args:
            trigger_name: The trigger name to watch.
            callback: Callable ``fn(from_state, to_state, trigger, **kwargs)``.
        """
        if trigger_name not in self._trigger_callbacks:
            self._trigger_callbacks[trigger_name] = []
        self._trigger_callbacks[trigger_name].append(callback)

    @property
    def states(self) -> List[str]:
        """Get all state names"""
        return list(self._states.keys())

    @property
    def triggers(self) -> List[str]:
        """Get all available triggers"""
        triggers: set[str] = set()
        for state_transitions in self._transitions.values():
            triggers.update(state_transitions.keys())
        return list(triggers)

    def get_available_triggers(self, state: Optional[str] = None) -> List[str]:
        """
        Get triggers available from a specific state.

        Args:
            state: State name (defaults to current state)

        Returns:
            List of available trigger names
        """
        state_name = state or self.current_state_name
        return list(self._transitions.get(state_name, {}).keys())

    def get_reachable_states(self, from_state: Optional[str] = None) -> List[str]:
        """
        Get states reachable from a specific state.

        Args:
            from_state: Starting state (defaults to current state)

        Returns:
            List of reachable state names
        """
        state_name = from_state or self.current_state_name
        reachable = set()

        for entry in self._transitions.get(state_name, {}).values():
            reachable.add(entry.to_state.name)

        return list(reachable)

    def transition_exists(
        self,
        trigger: str,
        from_state: Optional[str] = None,
        to_state: Optional[str] = None,
    ) -> bool:
        """
        Check if a transition exists.

        Args:
            trigger: Trigger name
            from_state: Source state (defaults to current state)
            to_state: Optional target state to check specifically

        Returns:
            True if transition exists
        """
        state_name = from_state or self.current_state_name

        if (
            state_name not in self._transitions
            or trigger not in self._transitions[state_name]
        ):
            return False

        if to_state is not None:
            entry = self._transitions[state_name][trigger]
            return entry.to_state.name == to_state

        return True

    def can_trigger(self, trigger: str, *args, **kwargs) -> bool:
        """
        Check if a trigger can be fired from the current state.

        Performance: O(1) - Direct dictionary lookup + condition check
        Use this for validation before expensive operations.
        """
        prepared = self._prepare_transition(trigger, args, kwargs)
        if isinstance(prepared, TransitionResult):
            return False

        entry = prepared.entry
        if entry.condition:
            assert prepared.condition_kwargs is not None
            if not self._evaluate_condition_sync(
                entry.condition, prepared.args, prepared.condition_kwargs
            ):
                return False

        if not self._evaluate_declarative_condition_sync(prepared):
            return False

        return self._can_transition_after_declarative_guard(
            trigger, entry.to_state, args, kwargs
        )

    def _prepare_transition(
        self, trigger: str, args: Tuple[Any, ...], kwargs: Dict[str, Any]
    ) -> Union[_PreparedDispatch, TransitionResult]:
        """Resolve one canonical transition and prepare its guard context.

        Every public can/do path calls this once.  The direct dictionary lookup
        keeps missing and unconditional transitions allocation-free with respect
        to guard context, while a guarded transition gets one fresh sanitized
        mapping for exactly that evaluation.
        """
        current_name = self._current_state.name
        entries = self._transitions.get(current_name)
        entry = entries.get(trigger) if entries is not None else None
        if entry is None:
            error_msg = (
                f"No transition for trigger '{trigger}' from state '{current_name}'"
            )
            self._logger.debug("%s: FAILED - %s", self._name, error_msg)
            return TransitionResult(
                False, from_state=current_name, trigger=trigger, error=error_msg
            )
        declarative_handler = _resolve_declarative_handler(
            self._current_state, trigger, entry.to_state
        )
        has_declarative_guard = bool(
            declarative_handler and declarative_handler.get("condition")
        )
        condition_kwargs = (
            self._sanitize_condition_kwargs(kwargs)
            if entry.condition or has_declarative_guard
            else None
        )
        return _PreparedDispatch(
            entry, current_name, trigger, args, condition_kwargs, declarative_handler
        )

    def _evaluate_declarative_condition_sync(self, prepared: _PreparedDispatch) -> bool:
        """Evaluate one resolved declarative guard through the sync guard seam."""
        handler_info = prepared.declarative_handler
        if handler_info is None:
            return True
        condition = handler_info.get("condition")
        if not condition:
            return True

        source_state = cast(DeclarativeState, self._current_state)
        try:
            assert prepared.condition_kwargs is not None
            condition_result: Any
            if isinstance(condition, Condition):
                condition_result = self._evaluate_condition_sync(
                    condition, prepared.args, prepared.condition_kwargs
                )
            elif callable(condition):
                if asyncio.iscoroutinefunction(condition):
                    raise TypeError(
                        "Async declarative condition requires AsyncStateMachine and "
                        "trigger_async()"
                    )
                condition_result = condition(
                    *prepared.args, **prepared.condition_kwargs
                )
                if _is_awaitable(condition_result):
                    _reject_sync_awaitable(condition_result)
            else:
                condition_result = bool(condition)
            source_state._logger.debug(
                "State '%s': Condition check for trigger '%s': %s",
                source_state.name,
                prepared.trigger,
                condition_result,
            )
            return bool(condition_result)
        except Exception as exc:  # broad catch isolates declarative guard failures
            source_state._logger.warning(
                "State '%s': Condition evaluation failed for trigger '%s': %s",
                source_state.name,
                prepared.trigger,
                exc,
            )
            return False

    async def _evaluate_declarative_condition_async(
        self, prepared: _PreparedDispatch
    ) -> bool:
        """Evaluate one resolved declarative guard through the async guard seam."""
        handler_info = prepared.declarative_handler
        if handler_info is None:
            return True
        condition = handler_info.get("condition")
        if not condition:
            return True

        source_state = cast(DeclarativeState, self._current_state)
        try:
            assert prepared.condition_kwargs is not None
            condition_result: Any
            if isinstance(condition, Condition):
                condition_result = await self._evaluate_condition_async(
                    condition, prepared.args, prepared.condition_kwargs
                )
            elif callable(condition):
                condition_result = condition(
                    *prepared.args, **prepared.condition_kwargs
                )
                if _is_awaitable(condition_result):
                    condition_result = await condition_result
            else:
                condition_result = bool(condition)
            source_state._logger.debug(
                "State '%s': Async condition check for trigger '%s': %s",
                source_state.name,
                prepared.trigger,
                condition_result,
            )
            return bool(condition_result)
        except Exception as exc:  # broad catch isolates declarative guard failures
            source_state._logger.warning(
                "State '%s': Async condition evaluation failed for trigger '%s': %s",
                source_state.name,
                prepared.trigger,
                exc,
            )
            return False

    def _can_transition_after_declarative_guard(
        self,
        trigger: str,
        to_state: State,
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
    ) -> bool:
        """Run effective sync state policy without re-evaluating its base guard."""
        source_state = self._current_state
        if not isinstance(source_state, DeclarativeState):
            return source_state.can_transition(trigger, to_state, *args, **kwargs)
        scope_key, previous = _set_prepared_declarative_guard(
            source_state, trigger, to_state
        )
        try:
            # Preserve the public subclass hook. DeclarativeState itself sees
            # the narrow context and skips only its duplicate decorator guard.
            return source_state.can_transition(trigger, to_state, *args, **kwargs)
        finally:
            _reset_prepared_declarative_guard(scope_key, previous)

    def _sanitize_condition_kwargs(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize kwargs passed to conditions for safety.

        This method provides a hook for validating and sanitizing context data
        passed to conditions. Override this method to implement custom validation.

        Args:
            kwargs: Raw kwargs from trigger call

        Returns:
            Sanitized kwargs safe for condition evaluation
        """
        safe_kwargs: Dict[str, Any] = {}

        # Retain the established diagnostic only; values are never logged.
        if len(kwargs) > 50:
            self._logger.warning(
                "%s: Too many kwargs (%d) passed to condition, truncating",
                self._name,
                len(kwargs),
            )

        # Filter first so invalid leading entries cannot consume the bounded
        # guard context budget.  Dict insertion order makes the retained safe
        # keys deterministic without retaining the caller's mapping.
        for key, value in kwargs.items():
            if not isinstance(key, str) or len(key) > 100:
                self._logger.warning(
                    "%s: Skipping invalid kwarg key for condition", self._name
                )
                continue
            if key.startswith("_"):
                self._logger.debug(
                    "%s: Skipping private kwarg '%s' for condition", self._name, key
                )
                continue
            if len(safe_kwargs) == 50:
                continue
            safe_kwargs[key] = value

        return safe_kwargs

    @staticmethod
    def _condition_children(condition: Condition) -> Tuple[Condition, ...]:
        """Return only the supported private built-in wrapper child edges."""
        from .condition_templates import AndCondition, NotCondition, OrCondition

        condition_type = type(condition)
        if condition_type is NegatedCondition:
            return (cast(NegatedCondition, condition)._inner,)
        if condition_type is AndCondition:
            return cast(AndCondition, condition).conditions
        if condition_type is OrCondition:
            return cast(OrCondition, condition).conditions
        if condition_type is NotCondition:
            return (cast(NotCondition, condition).condition,)
        return ()

    @staticmethod
    def _contains_async_requirement(condition: Condition) -> bool:
        """Detect nested async leaves while rejecting active wrapper cycles."""
        active: set[int] = set()
        completed: Dict[int, bool] = {}
        stack: List[Tuple[Condition, bool]] = [(condition, False)]

        while stack:
            current, leaving = stack.pop()
            current_id = id(current)
            if leaving:
                children = StateMachine._condition_children(current)
                completed[current_id] = (
                    any(completed[id(child)] for child in children)
                    if children
                    else (
                        isinstance(current, AsyncCondition)
                        or (
                            isinstance(current, FuncCondition)
                            and asyncio.iscoroutinefunction(current.func)
                        )
                    )
                )
                active.remove(current_id)
                continue

            if current_id in active:
                raise ValueError("supported condition wrapper cycle detected")
            if current_id in completed:
                continue

            active.add(current_id)
            stack.append((current, True))
            for child in reversed(StateMachine._condition_children(current)):
                stack.append((child, False))

        return completed[id(condition)]

    def _evaluate_condition_sync(
        self,
        condition: Condition,
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
        active: Optional[set[int]] = None,
        completed: Optional[set[int]] = None,
    ) -> bool:
        """Evaluate supported wrappers synchronously without hiding async leaves."""
        from .condition_templates import AndCondition, NotCondition, OrCondition

        if active is None:
            active = set()
        if completed is None:
            completed = set()
        entered: set[int] = set()
        stack: List[Tuple[str, Condition, int]] = [("evaluate", condition, 0)]
        result: Any = False

        try:
            while stack:
                action, current, child_index = stack.pop()
                current_id = id(current)

                if action == "evaluate":
                    if current_id in active:
                        raise ValueError("supported condition wrapper cycle detected")
                    active.add(current_id)
                    entered.add(current_id)
                    condition_type = type(current)
                    children = self._condition_children(current)

                    if (
                        condition_type is NegatedCondition
                        or condition_type is NotCondition
                    ):
                        stack.append(("negate", current, 0))
                        stack.append(("evaluate", children[0], 0))
                    elif condition_type is AndCondition:
                        if children:
                            stack.append(("and", current, 1))
                            stack.append(("evaluate", children[0], 0))
                        else:
                            result = True
                            active.remove(current_id)
                    elif condition_type is OrCondition:
                        if children:
                            stack.append(("or", current, 1))
                            stack.append(("evaluate", children[0], 0))
                        else:
                            result = False
                            active.remove(current_id)
                    elif isinstance(current, AsyncCondition):
                        raise TypeError(
                            "AsyncCondition requires AsyncStateMachine and trigger_async()"
                        )
                    else:
                        result = current.check(*args, **kwargs)
                        if _is_awaitable(result):
                            _reject_sync_awaitable(result)
                        active.remove(current_id)
                elif action == "negate":
                    result = not result
                    active.remove(current_id)
                elif action == "and":
                    children = self._condition_children(current)
                    if not result or child_index == len(children):
                        active.remove(current_id)
                    else:
                        stack.append(("and", current, child_index + 1))
                        stack.append(("evaluate", children[child_index], 0))
                else:  # action == "or"
                    children = self._condition_children(current)
                    if result or child_index == len(children):
                        active.remove(current_id)
                    else:
                        stack.append(("or", current, child_index + 1))
                        stack.append(("evaluate", children[child_index], 0))

            return result
        finally:
            active.difference_update(entered)
            completed.update(entered)

    async def _evaluate_condition_async(
        self,
        condition: Condition,
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
        active: Optional[set[int]] = None,
        completed: Optional[set[int]] = None,
    ) -> bool:
        """Await async leaves through supported built-in wrappers iteratively."""
        from .condition_templates import AndCondition, NotCondition, OrCondition

        if active is None:
            active = set()
        if completed is None:
            completed = set()
        entered: set[int] = set()
        stack: List[Tuple[str, Condition, int]] = [("evaluate", condition, 0)]
        result: Any = False

        try:
            while stack:
                action, current, child_index = stack.pop()
                current_id = id(current)

                if action == "evaluate":
                    if current_id in active:
                        raise ValueError("supported condition wrapper cycle detected")
                    active.add(current_id)
                    entered.add(current_id)
                    condition_type = type(current)
                    children = self._condition_children(current)

                    if (
                        condition_type is NegatedCondition
                        or condition_type is NotCondition
                    ):
                        stack.append(("negate", current, 0))
                        stack.append(("evaluate", children[0], 0))
                    elif condition_type is AndCondition:
                        if children:
                            stack.append(("and", current, 1))
                            stack.append(("evaluate", children[0], 0))
                        else:
                            result = True
                            active.remove(current_id)
                    elif condition_type is OrCondition:
                        if children:
                            stack.append(("or", current, 1))
                            stack.append(("evaluate", children[0], 0))
                        else:
                            result = False
                            active.remove(current_id)
                    elif isinstance(current, AsyncCondition):
                        result = await current.check_async(*args, **kwargs)
                        active.remove(current_id)
                    else:
                        result = current.check(*args, **kwargs)
                        if _is_awaitable(result):
                            result = await cast(Any, result)
                        active.remove(current_id)
                elif action == "negate":
                    result = not result
                    active.remove(current_id)
                elif action == "and":
                    children = self._condition_children(current)
                    if not result or child_index == len(children):
                        active.remove(current_id)
                    else:
                        stack.append(("and", current, child_index + 1))
                        stack.append(("evaluate", children[child_index], 0))
                else:  # action == "or"
                    children = self._condition_children(current)
                    if result or child_index == len(children):
                        active.remove(current_id)
                    else:
                        stack.append(("or", current, child_index + 1))
                        stack.append(("evaluate", children[child_index], 0))

            return result
        finally:
            active.difference_update(entered)
            completed.update(entered)

    def force_state(self, state_name: str) -> None:
        """Force the machine into a named state, bypassing guard conditions.

        Fires the full on_exit / on_enter / after_transition callback chain so
        that listeners stay consistent.  The synthetic trigger name
        ``"__force__"`` is passed to every callback.

        Use this for testing, error recovery, or programmatic state injection.
        Prefer normal ``trigger()`` calls in production flow.

        Args:
            state_name: Name of the target state.  Must already be registered.

        Raises:
            KeyError: If ``state_name`` is not a registered state.
        """
        if state_name not in self._states:
            raise KeyError(
                f"State '{state_name}' is not registered in '{self._name}'. "
                f"Registered states: {list(self._states)}"
            )
        to_state = self._states[state_name]
        self._execute_transition(to_state, "__force__")

    def reset(self) -> None:
        """Return the machine to its initial state, bypassing guard conditions.

        Equivalent to ``force_state(initial_state_name)``.  Fires the full
        callback chain (on_exit, on_enter, after_transition) with the
        synthetic trigger ``"__force__"``.

        Safe to call when the machine is already in its initial state
        (callbacks still fire).
        """
        self.force_state(self._initial_state.name)

    def snapshot(self) -> Dict[str, Any]:
        """Capture a lightweight, serialisable snapshot of the current state.

        The returned dict is safe to pickle, JSON-serialise, or store in any
        external store.  Restore it later with :meth:`restore`.

        Returns:
            ``{"state": <current_state_name>, "version": 1}``

        Example::

            snap = fsm.snapshot()        # {"state": "running", "version": 1}
            # ... time passes / process restarts ...
            fsm.restore(snap)
        """
        return {"state": self._current_state.name, "version": 1}

    def restore(self, snapshot: Dict[str, Any]) -> None:
        """Restore the machine to a previously captured snapshot.

        Calls :meth:`force_state` under the hood, so the full callback chain
        fires and guards are bypassed.

        Args:
            snapshot: A dict previously returned by :meth:`snapshot`.

        Raises:
            ValueError: If the snapshot dict is malformed or has an
                unsupported version number.
            KeyError: If the state named in the snapshot is no longer
                registered (e.g. machine topology changed since capture).
        """
        version = snapshot.get("version", 1)
        if version != 1:
            raise ValueError(
                f"Unsupported snapshot version: {version!r}. "
                "Only version 1 is currently supported."
            )
        state_name = snapshot.get("state")
        if not isinstance(state_name, str):
            raise ValueError(
                f"Snapshot 'state' must be a string, got {type(state_name).__name__!r}."
            )
        self.force_state(state_name)

    def clone(self) -> "StateMachine":
        """Create a verbatim clone of this machine reset to its initial state.

        The clone is a shallow copy of the original: same topology (states,
        transitions, guard conditions), same callbacks and listeners, but with
        current state reset to the initial state.

        All callback and listener lists are shallow-copied so the clone starts
        with the same behaviour as the original. Adding new callbacks to the
        clone after cloning does *not* affect the original, and vice versa.

        This is useful for running independent simulations from the same
        configured template, or for per-request/per-session FSM instances.

        Returns:
            A new :class:`StateMachine` (or subclass) instance.

        Note:
            ``CallbackState`` on_enter / on_exit function references are shared
            (shallow copy), which is correct since they are typically pure
            functions or methods.
        """
        new_fsm: "StateMachine" = self.__class__(self._initial_state, name=self._name)
        # Replace the minimal state/transition tables __init__ created with
        # full shallow copies of our own tables (same State objects, independent
        # inner transition dicts so additions to one don't bleed into the other).
        new_fsm._states = dict(self._states)
        new_fsm._transitions = {
            state_name: dict(triggers)
            for state_name, triggers in self._transitions.items()
        }
        new_fsm._graph_version = self._graph_version
        # current_state is already _initial_state from __init__ — correct.
        # Per-state callbacks are copied (shallow copy of each list).
        new_fsm._state_exit_callbacks = {
            k: list(v) for k, v in self._state_exit_callbacks.items()
        }
        new_fsm._state_enter_callbacks = {
            k: list(v) for k, v in self._state_enter_callbacks.items()
        }
        # Copy all listener/callback lists (shallow copy — same callables, independent lists).
        new_fsm._before_listeners = list(self._before_listeners)
        new_fsm._on_exit_listeners = list(self._on_exit_listeners)
        new_fsm._on_enter_listeners = list(self._on_enter_listeners)
        new_fsm._after_listeners = list(self._after_listeners)
        new_fsm._on_failed_callbacks = list(self._on_failed_callbacks)
        for tname, cbs in self._trigger_callbacks.items():
            new_fsm._trigger_callbacks[tname] = list(cbs)
        # History is NOT copied — the clone starts with a fresh (disabled) history.
        # If the original had history enabled, the clone does not inherit it.
        new_fsm._history = None
        new_fsm._history_max = self._history_max
        return new_fsm

    def _resolve_trigger(
        self, trigger: str, *args: Any, **kwargs: Any
    ) -> Union[Tuple[TransitionEntry, str], TransitionResult]:
        """Look up a transition entry for the given trigger.

        Logs the trigger attempt (ultra-verbose) and validates that a
        transition exists from the current state.

        Returns:
            ``(entry, current_state_name)`` on success, or a failure
            :class:`TransitionResult` if no transition exists.
        """
        prepared = self._prepare_transition(trigger, args, kwargs)
        if isinstance(prepared, TransitionResult):
            return prepared
        return prepared.entry, prepared.current_name

    def _execute_transition(
        self, to_state: State, trigger: str, *args: Any, **kwargs: Any
    ) -> TransitionResult:
        """Perform exit/enter callbacks and state change.

        Assumes all pre-checks (condition, permission) have already passed.
        """
        old_state = self._current_state

        # Fire before_transition listeners (before on_exit)
        if self._before_listeners:
            for fn in self._before_listeners:
                try:
                    fn(old_state, to_state, trigger, **kwargs)
                except Exception as e:  # broad catch intentional — isolates user callback exceptions from FSM control flow
                    self._logger.error("before_transition listener error: %s", e)

        # Log transition start
        self._logger.debug(
            "%s: Executing transition %s --[%s]--> %s",
            self._name,
            old_state.name,
            trigger,
            to_state.name,
        )

        # Call exit handler
        try:
            old_state.on_exit(to_state, trigger, *args, **kwargs)
        except Exception as e:  # broad catch intentional — isolates user callback exceptions from FSM control flow
            self._logger.warning(
                "%s: Exception in on_exit for state '%s': %s",
                self._name,
                old_state.name,
                e,
            )

        # Fire per-state exit callbacks registered via on_exit(state, fn)
        _exit_cbs = self._state_exit_callbacks.get(old_state.name)
        if _exit_cbs:
            for fn in _exit_cbs:
                try:
                    fn(to_state, trigger, **kwargs)
                except Exception as e:  # broad catch intentional — isolates user callback exceptions from FSM control flow
                    self._logger.warning(
                        "%s: Exception in on_exit callback for state '%s': %s",
                        self._name,
                        old_state.name,
                        e,
                    )

        # Notify on_exit_state listeners (after state's own on_exit)
        if self._on_exit_listeners:
            for fn in self._on_exit_listeners:
                try:
                    fn(old_state, to_state, trigger, **kwargs)
                except Exception as e:  # broad catch intentional — isolates user callback exceptions from FSM control flow
                    self._logger.warning(
                        "%s: Exception in on_exit_state listener: %s",
                        self._name,
                        e,
                    )

        # Change state
        self._current_state = to_state

        # Call enter handler
        try:
            to_state.on_enter(old_state, trigger, *args, **kwargs)
        except Exception as e:  # broad catch intentional — isolates user callback exceptions from FSM control flow
            self._logger.warning(
                "%s: Exception in on_enter for state '%s': %s",
                self._name,
                to_state.name,
                e,
            )

        # Fire per-state enter callbacks registered via on_enter(state, fn)
        _enter_cbs = self._state_enter_callbacks.get(to_state.name)
        if _enter_cbs:
            for fn in _enter_cbs:
                try:
                    fn(old_state, trigger, **kwargs)
                except Exception as e:  # broad catch intentional — isolates user callback exceptions from FSM control flow
                    self._logger.warning(
                        "%s: Exception in on_enter callback for state '%s': %s",
                        self._name,
                        to_state.name,
                        e,
                    )

        # Notify on_enter_state listeners (after state's own on_enter)
        if self._on_enter_listeners:
            for fn in self._on_enter_listeners:
                try:
                    fn(to_state, old_state, trigger, **kwargs)
                except Exception as e:  # broad catch intentional — isolates user callback exceptions from FSM control flow
                    self._logger.warning(
                        "%s: Exception in on_enter_state listener: %s",
                        self._name,
                        e,
                    )

        # Log successful transition (main transition log)
        self._logger.debug(
            "%s: %s --[%s]--> %s", self._name, old_state.name, trigger, to_state.name
        )

        # Notify after_transition listeners
        if self._after_listeners:
            for fn in self._after_listeners:
                try:
                    fn(old_state, to_state, trigger, **kwargs)
                except Exception as e:  # broad catch intentional — isolates user callback exceptions from FSM control flow
                    self._logger.warning(
                        "%s: Exception in after_transition listener: %s",
                        self._name,
                        e,
                    )

        # Fire per-trigger callbacks registered via on_trigger(name, fn)
        if trigger in self._trigger_callbacks:
            for fn in self._trigger_callbacks[trigger]:
                try:
                    fn(old_state, to_state, trigger, **kwargs)
                except Exception as e:  # broad catch intentional — isolates user callback exceptions from FSM control flow
                    self._logger.error("on_trigger callback error: %s", e)

        # Record transition in history (zero-cost when disabled — single None check)
        if self._history is not None:
            self._history.append(
                TransitionRecord(
                    old_state.name, trigger, to_state.name, time.monotonic()
                )
            )

        return TransitionResult(
            True, from_state=old_state.name, to_state=to_state.name, trigger=trigger
        )

    def trigger(self, trigger: str, *args, **kwargs) -> TransitionResult:
        """
        Trigger a state transition.

        Performance: O(1) - Direct dictionary lookup + condition evaluation
        Throughput: ~250,000 transitions/sec on modern hardware

        Args:
            trigger: The trigger/event name
            *args: Positional arguments for the transition
            **kwargs: Keyword arguments for the transition

        Returns:
            TransitionResult indicating success or failure
        """
        prepared = self._prepare_transition(trigger, args, kwargs)
        if isinstance(prepared, TransitionResult):
            if self._on_failed_callbacks:
                for fn in self._on_failed_callbacks:
                    try:
                        fn(trigger, self._current_state.name, prepared.error, **kwargs)
                    except Exception as e:  # broad catch intentional — isolates user callback exceptions from FSM control flow
                        self._logger.error("on_failed callback error: %s", e)
            return prepared
        entry = prepared.entry
        current_name = prepared.current_name
        to_state = entry.to_state
        condition = entry.condition

        # Check condition with logging
        if condition:
            condition_name = str(condition)
            self._logger.debug(
                "%s: Evaluating condition '%s' for '%s' -> '%s'",
                self._name,
                condition_name,
                current_name,
                to_state.name,
            )
            try:
                assert prepared.condition_kwargs is not None
                condition_result = self._evaluate_condition_sync(
                    condition, prepared.args, prepared.condition_kwargs
                )
                self._logger.debug(
                    "%s: Condition '%s' result: %s",
                    self._name,
                    condition_name,
                    condition_result,
                )
                if not condition_result:
                    error_msg = f"Transition condition '{condition_name}' failed for '{trigger}' from '{current_name}'"
                    self._logger.debug("%s: FAILED - %s", self._name, error_msg)
                    if self._on_failed_callbacks:
                        for fn in self._on_failed_callbacks:
                            try:
                                fn(trigger, current_name, error_msg, **kwargs)
                            except Exception as e:  # broad catch intentional — isolates user callback exceptions from FSM control flow
                                self._logger.error("on_failed callback error: %s", e)
                    return TransitionResult(
                        False, from_state=current_name, trigger=trigger, error=error_msg
                    )
            except Exception as e:  # broad catch intentional — isolates user-defined condition exceptions; failed condition = failed transition
                error_msg = f"Condition '{condition_name}' raised exception: {e}"
                self._logger.warning("%s: FAILED - %s", self._name, error_msg)
                if self._on_failed_callbacks:
                    for fn in self._on_failed_callbacks:
                        try:
                            fn(trigger, current_name, error_msg, **kwargs)
                        except Exception as e:  # broad catch intentional — isolates user callback exceptions from FSM control flow
                            self._logger.error("on_failed callback error: %s", e)
                return TransitionResult(
                    False, from_state=current_name, trigger=trigger, error=error_msg
                )

        if not self._evaluate_declarative_condition_sync(prepared):
            error_msg = f"State '{current_name}' rejected transition '{trigger}'"
            self._logger.debug("%s: FAILED - %s", self._name, error_msg)
            if self._on_failed_callbacks:
                for fn in self._on_failed_callbacks:
                    try:
                        fn(trigger, current_name, error_msg, **kwargs)
                    except Exception as e:  # broad catch intentional — isolates user callback exceptions from FSM control flow
                        self._logger.error("on_failed callback error: %s", e)
            return TransitionResult(
                False, from_state=current_name, trigger=trigger, error=error_msg
            )

        # Check if source state allows transition
        self._logger.debug(
            "%s: Checking if state '%s' allows transition '%s'",
            self._name,
            current_name,
            trigger,
        )
        if not self._can_transition_after_declarative_guard(
            trigger, to_state, args, kwargs
        ):
            error_msg = f"State '{current_name}' rejected transition '{trigger}'"
            self._logger.debug("%s: FAILED - %s", self._name, error_msg)
            if self._on_failed_callbacks:
                for fn in self._on_failed_callbacks:
                    try:
                        fn(trigger, current_name, error_msg, **kwargs)
                    except Exception as e:  # broad catch intentional — isolates user callback exceptions from FSM control flow
                        self._logger.error("on_failed callback error: %s", e)
            return TransitionResult(
                False, from_state=current_name, trigger=trigger, error=error_msg
            )

        old_state = self._current_state
        result = self._execute_transition(to_state, trigger, *args, **kwargs)
        handler_info = prepared.declarative_handler
        if handler_info is not None:
            _invoke_declarative_handler(
                old_state, handler_info, trigger, prepared.args, kwargs
            )
        return result

    def safe_trigger(self, trigger: str, *args, **kwargs) -> TransitionResult:
        """
        Safe version of trigger that never raises exceptions.

        Unlike :meth:`trigger`, which propagates any exception that escapes
        callback/condition isolation (e.g. a ``BaseException`` subclass or an
        unexpected internal error), ``safe_trigger()`` wraps the entire call in a
        broad ``except Exception`` barrier.  Any exception that reaches this
        barrier is caught, logged at ERROR level, and returned as a failed
        :class:`TransitionResult`.

        **Exception semantics:**

        * Exceptions from user callbacks (on_enter, on_exit, listeners) and
          conditions are *already isolated* inside :meth:`trigger` —
          they are caught, logged at WARNING level, and result in a failed
          ``TransitionResult``.  They do **not** propagate to this barrier.
        * ``safe_trigger()`` is a last-resort safety net — it catches any
          exception that somehow escapes those inner guards (e.g. an unexpected
          internal FSM error).  Normal user code should never see exceptions
          land here.
        * ``BaseException`` subclasses (``KeyboardInterrupt``, ``SystemExit``)
          are **not** caught — they propagate normally.

        Args:
            trigger: The trigger/event name
            *args: Positional arguments for the transition
            **kwargs: Keyword arguments for the transition

        Returns:
            TransitionResult with detailed error information
        """
        try:
            return self.trigger(trigger, *args, **kwargs)
        except Exception as e:  # broad catch intentional — last-resort safe_trigger() barrier; see docstring
            error_msg = f"Exception during trigger '{trigger}': {e}"
            self._logger.error("%s: %s", self._name, error_msg)
            return TransitionResult(
                False,
                from_state=self.current_state_name,
                trigger=trigger,
                error=error_msg,
            )

    def debug_info(self) -> Dict[str, Any]:
        """
        Get detailed debugging information about the FSM.

        Returns:
            Dictionary with FSM state information
        """
        return {
            "name": self._name,
            "current_state": self.current_state_name,
            "states": self.states,
            "triggers": self.triggers,
            "available_triggers": self.get_available_triggers(),
            "reachable_states": self.get_reachable_states(),
            "transition_count": sum(
                len(transitions) for transitions in self._transitions.values()
            ),
        }

    def print_debug_info(self) -> None:
        """Print human-readable debugging information."""
        info = self.debug_info()
        print(f"🔧 FSM Debug Info: {info['name']}")
        print(f"   Current State: {info['current_state']}")
        print(f"   Available Triggers: {info['available_triggers']}")
        print(f"   Reachable States: {info['reachable_states']}")
        print(f"   Total States: {len(info['states'])}")
        print(f"   Total Transitions: {info['transition_count']}")

    def validate_transition_completeness(self) -> Dict[str, List[str]]:
        """
        Quick validation to find missing transitions.

        Returns:
            Dictionary with validation results
        """
        issues: Dict[str, List[str]] = {
            "dead_end_states": [],
            "unreachable_states": [],
            "states_with_no_transitions": [],
        }

        # Find states with no outgoing transitions
        for state_name in self.states:
            if state_name not in self._transitions or not self._transitions[state_name]:
                issues["dead_end_states"].append(state_name)

        # Find unreachable states (simple version)
        reachable = {self.current_state_name}
        for state_name in self.states:
            for entry in self._transitions.get(state_name, {}).values():
                reachable.add(entry.to_state.name)

        for state_name in self.states:
            if state_name not in reachable:
                issues["unreachable_states"].append(state_name)

        return issues


class AsyncStateMachine(StateMachine):
    """
    Async-aware state machine that can handle AsyncCondition instances properly.

    Extends :class:`StateMachine` with:

    - :meth:`trigger_async` / :meth:`can_trigger_async` — await-safe transition
      methods that evaluate :class:`AsyncCondition` guards.
    - :meth:`on_enter_async` / :meth:`on_exit_async` — register ``async``
      callbacks for specific states, fired after all synchronous callbacks.
    """

    __slots__ = ("_state_enter_async_callbacks", "_state_exit_async_callbacks")

    def __init__(
        self,
        initial_state: State,
        *,
        name: str = "FSM",
        logger_name: Optional[str] = None,
    ) -> None:
        super().__init__(initial_state, name=name, logger_name=logger_name)
        self._state_enter_async_callbacks: Dict[str, List[Any]] = {}
        self._state_exit_async_callbacks: Dict[str, List[Any]] = {}

    def on_enter_async(self, state_name: str, callback: Any) -> None:
        """Register an ``async`` callback fired when the machine enters *state_name*.

        Fires **after** the synchronous :meth:`~StateMachine.on_enter` callbacks,
        still within the same ``trigger_async`` call.

        Signature: ``async callback(from_state: State, trigger: str, **kwargs)``

        Multiple callbacks for the same state are called in registration order.

        Args:
            state_name: Name of the state to watch.  Does not need to be
                registered yet.
            callback: Async callable matching the signature above.

        Example::

            async def log_entry(from_s, t, **kw):
                await db.log(f"entered running from {from_s.name}")

            fsm.on_enter_async("running", log_entry)
        """
        if state_name not in self._state_enter_async_callbacks:
            self._state_enter_async_callbacks[state_name] = []
        self._state_enter_async_callbacks[state_name].append(callback)

    def on_exit_async(self, state_name: str, callback: Any) -> None:
        """Register an ``async`` callback fired when the machine exits *state_name*.

        Fires **after** the synchronous :meth:`~StateMachine.on_exit` callbacks,
        still within the same ``trigger_async`` call.

        Signature: ``async callback(to_state: State, trigger: str, **kwargs)``

        Multiple callbacks for the same state are called in registration order.

        Args:
            state_name: Name of the state to watch.  Does not need to be
                registered yet.
            callback: Async callable matching the signature above.

        Example::

            async def log_exit(to_s, t, **kw):
                await db.log(f"left running -> {to_s.name}")

            fsm.on_exit_async("running", log_exit)
        """
        if state_name not in self._state_exit_async_callbacks:
            self._state_exit_async_callbacks[state_name] = []
        self._state_exit_async_callbacks[state_name].append(callback)

    def clone(self) -> "AsyncStateMachine":
        """Create a structural clone; also copies async per-state callbacks."""
        base = super().clone()
        # super().clone() calls self.__class__(...) which creates an AsyncStateMachine
        # with empty async callback dicts.  Copy them over now.
        assert isinstance(base, AsyncStateMachine)
        base._state_enter_async_callbacks = {
            k: list(v) for k, v in self._state_enter_async_callbacks.items()
        }
        base._state_exit_async_callbacks = {
            k: list(v) for k, v in self._state_exit_async_callbacks.items()
        }
        return base

    async def can_trigger_async(self, trigger: str, *args, **kwargs) -> bool:
        """Async version of can_trigger"""
        prepared = self._prepare_transition(trigger, args, kwargs)
        if isinstance(prepared, TransitionResult):
            return False

        entry = prepared.entry
        condition = entry.condition

        if condition:
            assert prepared.condition_kwargs is not None
            if not await self._evaluate_condition_async(
                condition, prepared.args, prepared.condition_kwargs
            ):
                return False

        if not await self._evaluate_declarative_condition_async(prepared):
            return False

        return await self._can_transition_after_declarative_guard_async(
            trigger, entry.to_state, args, kwargs
        )

    async def _can_transition_after_declarative_guard_async(
        self,
        trigger: str,
        to_state: State,
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
    ) -> bool:
        """Run effective async policy while suppressing only a prepared base guard."""
        source_state = self._current_state
        if not isinstance(source_state, DeclarativeState):
            if hasattr(source_state, "can_transition_async"):
                return await source_state.can_transition_async(
                    trigger, to_state, *args, **kwargs
                )
            return source_state.can_transition(trigger, to_state, *args, **kwargs)
        scope_key, previous = _set_prepared_declarative_guard(
            source_state, trigger, to_state
        )
        try:
            if hasattr(source_state, "can_transition_async"):
                return await source_state.can_transition_async(
                    trigger, to_state, *args, **kwargs
                )
            return source_state.can_transition(trigger, to_state, *args, **kwargs)
        finally:
            _reset_prepared_declarative_guard(scope_key, previous)

    async def trigger_async(self, trigger: str, *args, **kwargs) -> TransitionResult:
        """
        Async version of trigger that properly handles AsyncCondition instances.

        Args:
            trigger: The trigger/event name
            *args: Positional arguments for the transition
            **kwargs: Keyword arguments for the transition

        Returns:
            TransitionResult indicating success or failure
        """
        prepared = self._prepare_transition(trigger, args, kwargs)
        if isinstance(prepared, TransitionResult):
            if self._on_failed_callbacks:
                for fn in self._on_failed_callbacks:
                    try:
                        fn(trigger, self._current_state.name, prepared.error, **kwargs)
                    except Exception as e:  # broad catch intentional — isolates user callback exceptions from FSM control flow
                        self._logger.error("on_failed callback error: %s", e)
            return prepared
        entry = prepared.entry
        current_name = prepared.current_name
        to_state = entry.to_state
        condition = entry.condition

        # Check condition with async support
        if condition:
            condition_name = str(condition)
            self._logger.debug(
                "%s: Evaluating condition '%s' for '%s' -> '%s'",
                self._name,
                condition_name,
                current_name,
                to_state.name,
            )
            try:
                assert prepared.condition_kwargs is not None
                condition_result = await self._evaluate_condition_async(
                    condition, prepared.args, prepared.condition_kwargs
                )

                self._logger.debug(
                    "%s: Condition '%s' result: %s",
                    self._name,
                    condition_name,
                    condition_result,
                )
                if not condition_result:
                    error_msg = f"Transition condition '{condition_name}' failed for '{trigger}' from '{current_name}'"
                    self._logger.debug("%s: FAILED - %s", self._name, error_msg)
                    if self._on_failed_callbacks:
                        for fn in self._on_failed_callbacks:
                            try:
                                fn(trigger, current_name, error_msg, **kwargs)
                            except Exception as e:  # broad catch intentional — isolates user callback exceptions from FSM control flow
                                self._logger.error("on_failed callback error: %s", e)
                    return TransitionResult(
                        False, from_state=current_name, trigger=trigger, error=error_msg
                    )
            except Exception as e:  # broad catch intentional — isolates user-defined condition exceptions; failed condition = failed transition
                error_msg = f"Condition '{condition_name}' raised exception: {e}"
                self._logger.warning("%s: FAILED - %s", self._name, error_msg)
                if self._on_failed_callbacks:
                    for fn in self._on_failed_callbacks:
                        try:
                            fn(trigger, current_name, error_msg, **kwargs)
                        except Exception as e:  # broad catch intentional — isolates user callback exceptions from FSM control flow
                            self._logger.error("on_failed callback error: %s", e)
                return TransitionResult(
                    False, from_state=current_name, trigger=trigger, error=error_msg
                )

        if not await self._evaluate_declarative_condition_async(prepared):
            error_msg = f"State '{current_name}' rejected transition '{trigger}'"
            self._logger.debug("%s: FAILED - %s", self._name, error_msg)
            if self._on_failed_callbacks:
                for fn in self._on_failed_callbacks:
                    try:
                        fn(trigger, current_name, error_msg, **kwargs)
                    except Exception as e:  # broad catch intentional — isolates user callback exceptions from FSM control flow
                        self._logger.error("on_failed callback error: %s", e)
            return TransitionResult(
                False, from_state=current_name, trigger=trigger, error=error_msg
            )

        # Check if source state allows transition
        self._logger.debug(
            "%s: Checking if state '%s' allows transition '%s'",
            self._name,
            current_name,
            trigger,
        )
        can_proceed = await self._can_transition_after_declarative_guard_async(
            trigger, to_state, args, kwargs
        )
        if not can_proceed:
            error_msg = f"State '{current_name}' rejected transition '{trigger}'"
            self._logger.debug("%s: FAILED - %s", self._name, error_msg)
            if self._on_failed_callbacks:
                for fn in self._on_failed_callbacks:
                    try:
                        fn(trigger, current_name, error_msg, **kwargs)
                    except Exception as e:  # broad catch intentional — isolates user callback exceptions from FSM control flow
                        self._logger.error("on_failed callback error: %s", e)
            return TransitionResult(
                False, from_state=current_name, trigger=trigger, error=error_msg
            )

        old_state = self._current_state
        result = self._execute_transition(to_state, trigger, *args, **kwargs)

        handler_info = prepared.declarative_handler
        if handler_info is not None:
            await _invoke_declarative_handler_async(
                old_state, handler_info, trigger, prepared.args, kwargs
            )

        # Fire async per-state exit callbacks (after all sync callbacks)
        _async_exit = self._state_exit_async_callbacks.get(old_state.name)
        if _async_exit:
            for fn in _async_exit:
                try:
                    await fn(to_state, trigger, **kwargs)
                except Exception as e:  # broad catch intentional — isolates user callback exceptions from FSM control flow
                    self._logger.warning(
                        "%s: Exception in on_exit_async callback for state '%s': %s",
                        self._name,
                        old_state.name,
                        e,
                    )

        # Fire async per-state enter callbacks
        _async_enter = self._state_enter_async_callbacks.get(to_state.name)
        if _async_enter:
            for fn in _async_enter:
                try:
                    await fn(old_state, trigger, **kwargs)
                except Exception as e:  # broad catch intentional — isolates user callback exceptions from FSM control flow
                    self._logger.warning(
                        "%s: Exception in on_enter_async callback for state '%s': %s",
                        self._name,
                        to_state.name,
                        e,
                    )

        return result


# Convenience functions and classes


def transition(
    trigger: str,
    from_state: Optional[Union[str, List[str]]] = None,
    to_state: Optional[str] = None,
    condition: Optional[Any] = None,
):
    """
    Decorator to mark methods as transition handlers.
    Can be used to build FSMs declaratively.

    Args:
        trigger: Event name that this handler responds to
        from_state: Optional source state(s) constraint
        to_state: Optional target state name
        condition: Optional guard — can be a :class:`Condition`, a callable,
            or any truthy object evaluated via ``bool()``
    """

    def decorator(func):
        func._fsm_trigger = trigger
        func._fsm_from_state = from_state
        func._fsm_to_state = to_state
        func._fsm_condition = condition
        return func

    return decorator


def _metadata_matches_state(metadata: Any, state_name: str) -> bool:
    """Return whether optional declarative metadata accepts one canonical name."""
    if metadata is None:
        return True
    if isinstance(metadata, list):
        return state_name in metadata
    return metadata == state_name


def _resolve_declarative_handler(
    source_state: State, trigger: str, target_state: Optional[State]
) -> Optional[Dict[str, Any]]:
    """Find a handler by canonical source, trigger, and optional target metadata.

    Ordinary machine dispatch always supplies both canonical endpoints.  The
    compatibility helpers pass ``None`` for ``target_state`` because their
    public signatures have never accepted a target; that keeps their legacy
    direct-call behavior while sharing this resolver and invocation boundary.
    """
    if not isinstance(source_state, DeclarativeState):
        return None
    handler_info = source_state._handlers.get(trigger)
    if handler_info is None:
        return None
    if not _metadata_matches_state(handler_info["from_state"], source_state.name):
        return None
    if target_state is not None and not _metadata_matches_state(
        handler_info["to_state"], target_state.name
    ):
        return None
    return handler_info


def _normalize_declarative_handler_result(result: Any) -> TransitionResult:
    """Preserve the compatibility helper's normalized handler result shape."""
    if result is None:
        return TransitionResult(True)
    if isinstance(result, bool):
        return TransitionResult(result)
    if isinstance(result, TransitionResult):
        return result
    return TransitionResult(
        True, error=f"Invalid return type from handler: {type(result)}"
    )


def _invoke_declarative_handler(
    source_state: State,
    handler_info: Dict[str, Any],
    event: str,
    args: Tuple[Any, ...],
    kwargs: Dict[str, Any],
) -> TransitionResult:
    """Invoke one resolved synchronous declarative handler exactly once."""
    method = handler_info["method"]
    method_name = method.__name__
    logger = cast(DeclarativeState, source_state)._logger
    logger.debug(
        "State '%s': Executing handler '%s' for event '%s'",
        source_state.name,
        method_name,
        event,
    )
    if handler_info["is_async"]:
        logger.warning(
            "State '%s': Async handler '%s' cannot be executed in sync context. "
            "Use AsyncDeclarativeState for async methods.",
            source_state.name,
            method_name,
        )
        return TransitionResult(
            False, error=f"Async handler '{method_name}' in sync context"
        )
    try:
        result = _normalize_declarative_handler_result(method(*args, **kwargs))
    except Exception as exc:  # broad catch isolates user handler failures
        error_msg = f"Handler '{method_name}' raised exception: {exc}"
        logger.warning("State '%s': %s", source_state.name, error_msg)
        return TransitionResult(False, error=error_msg)
    if result.success:
        logger.debug(
            "State '%s': Handler '%s' succeeded", source_state.name, method_name
        )
    else:
        logger.debug(
            "State '%s': Handler '%s' failed: %s",
            source_state.name,
            method_name,
            result.error or "Unknown error",
        )
    return result


async def _invoke_declarative_handler_async(
    source_state: State,
    handler_info: Dict[str, Any],
    event: str,
    args: Tuple[Any, ...],
    kwargs: Dict[str, Any],
) -> TransitionResult:
    """Invoke one resolved declarative handler through the async boundary once."""
    method = handler_info["method"]
    method_name = method.__name__
    logger = cast(DeclarativeState, source_state)._logger
    logger.debug(
        "State '%s': Executing async handler '%s' for event '%s'",
        source_state.name,
        method_name,
        event,
    )
    try:
        raw_result = (
            await method(*args, **kwargs)
            if handler_info["is_async"]
            else method(*args, **kwargs)
        )
        result = _normalize_declarative_handler_result(raw_result)
    except Exception as exc:  # broad catch isolates user handler failures
        error_msg = f"Async handler '{method_name}' raised exception: {exc}"
        logger.warning("State '%s': %s", source_state.name, error_msg)
        return TransitionResult(False, error=error_msg)
    if result.success:
        logger.debug(
            "State '%s': Async handler '%s' succeeded", source_state.name, method_name
        )
    else:
        logger.debug(
            "State '%s': Async handler '%s' failed: %s",
            source_state.name,
            method_name,
            result.error or "Unknown error",
        )
    return result


@mypyc_attr(allow_interpreted_subclasses=True)
class DeclarativeState(State):
    """
    State that can handle events through decorated methods.
    Useful for complex state logic with full library feature support.

    Features:
    - Auto-discovery of @transition decorated methods
    - Condition evaluation from decorator metadata
    - Integrated logging for handler execution
    - Async method support
    - Enhanced error handling and reporting
    """

    __slots__ = ("_handlers", "_logger")

    def __init__(self, name: str, logger_name: Optional[str] = None):
        super().__init__(name)
        self._handlers: Dict[str, Dict[str, Any]] = {}

        # Set up logging (aligned with StateMachine pattern)
        if logger_name is None:
            logger_name = f"fast_fsm.state.{name}"
        self._logger = logging.getLogger(logger_name)

        # Auto-discover transition handlers with full metadata
        self._discover_handlers()

    def _discover_handlers(self) -> None:
        """Discover and register decorated transition handlers"""
        for attr_name in dir(self):
            if not attr_name.startswith("_"):
                attr = getattr(self, attr_name)
                if callable(attr) and hasattr(attr, "_fsm_trigger"):
                    trigger = getattr(attr, "_fsm_trigger", attr_name)

                    # Extract full decorator metadata
                    handler_info = {
                        "method": attr,
                        "from_state": getattr(attr, "_fsm_from_state", None),
                        "to_state": getattr(attr, "_fsm_to_state", None),
                        "condition": getattr(attr, "_fsm_condition", None),
                        "is_async": asyncio.iscoroutinefunction(attr),
                    }

                    self._handlers[trigger] = handler_info

                    # Log handler registration
                    self._logger.debug(
                        "State '%s': Registered handler '%s' for trigger '%s'%s",
                        self.name,
                        attr_name,
                        trigger,
                        " (async)" if handler_info["is_async"] else "",
                    )

    def can_transition(self, trigger: str, to_state: "State", *args, **kwargs) -> bool:
        """
        Enhanced transition validation with condition support.
        Checks both decorator conditions and custom logic.
        """
        # Machine-owned dispatch has already evaluated the decorator guard when
        # its private context matches this exact request; direct state use keeps
        # the legacy guard evaluation.
        if trigger in self._handlers and not _has_prepared_declarative_guard(
            self, trigger, to_state
        ):
            handler_info = self._handlers[trigger]
            condition = handler_info.get("condition")

            # Evaluate decorator condition if present
            if condition:
                try:
                    condition_result: Any
                    # Handle different condition types
                    if isinstance(condition, AsyncCondition):
                        # For sync context, we can't handle async conditions properly
                        self._logger.warning(
                            "State '%s': Async condition '%s' in sync context. "
                            "Consider using AsyncDeclarativeState.",
                            self.name,
                            condition.name,
                        )
                        return False
                    elif isinstance(condition, Condition):
                        condition_result = condition.check(*args, **kwargs)
                    elif callable(condition):
                        if asyncio.iscoroutinefunction(condition):
                            raise TypeError(
                                "Async declarative condition requires "
                                "AsyncStateMachine and trigger_async()"
                            )
                        condition_result = condition(*args, **kwargs)
                        if _is_awaitable(condition_result):
                            _reject_sync_awaitable(condition_result)
                    else:
                        condition_result = bool(condition)

                    self._logger.debug(
                        "State '%s': Condition check for trigger '%s': %s",
                        self.name,
                        trigger,
                        condition_result,
                    )

                    if not condition_result:
                        return False

                except Exception as e:  # broad catch intentional — isolates user-defined condition exceptions from DeclarativeState control flow
                    self._logger.warning(
                        "State '%s': Condition evaluation failed for trigger '%s': %s",
                        self.name,
                        trigger,
                        e,
                    )
                    return False

        # Call parent implementation for additional custom logic
        return super().can_transition(trigger, to_state, *args, **kwargs)

    def handle_event(self, event: str, *args, **kwargs) -> TransitionResult:
        """
        Enhanced event handling with full logging and async support.
        """
        handler_info = _resolve_declarative_handler(self, event, None)
        if handler_info is not None:
            return _invoke_declarative_handler(self, handler_info, event, args, kwargs)

        # Fallback to parent implementation
        return super().handle_event(event, *args, **kwargs)


@mypyc_attr(allow_interpreted_subclasses=True)
class AsyncDeclarativeState(DeclarativeState):
    """
    Async-aware version of DeclarativeState that can handle async decorated methods.
    Integrates seamlessly with AsyncStateMachine for full async support.
    """

    __slots__ = ()

    async def can_transition_async(
        self, trigger: str, to_state: "State", *args, **kwargs
    ) -> bool:
        """
        Async version of can_transition with async condition support.
        """
        # The matching machine-owned dispatch path has already evaluated the
        # decorator guard. Keep direct calls backward-compatible.
        if trigger in self._handlers and not _has_prepared_declarative_guard(
            self, trigger, to_state
        ):
            handler_info = self._handlers[trigger]
            condition = handler_info.get("condition")

            # Evaluate decorator condition if present
            if condition:
                try:
                    condition_result: Any
                    # Handle async conditions
                    if isinstance(condition, AsyncCondition):
                        condition_result = await condition.check_async(*args, **kwargs)
                    elif isinstance(condition, Condition):
                        condition_result = condition.check(*args, **kwargs)
                    elif callable(condition):
                        condition_result = condition(*args, **kwargs)
                        if _is_awaitable(condition_result):
                            condition_result = await condition_result
                    else:
                        condition_result = bool(condition)

                    self._logger.debug(
                        "State '%s': Async condition check for trigger '%s': %s",
                        self.name,
                        trigger,
                        condition_result,
                    )

                    if not condition_result:
                        return False

                except Exception as e:  # broad catch intentional — isolates user-defined condition exceptions from AsyncDeclarativeState control flow
                    self._logger.warning(
                        "State '%s': Async condition evaluation failed for trigger '%s': %s",
                        self.name,
                        trigger,
                        e,
                    )
                    return False

        # Skip DeclarativeState.can_transition (which would re-evaluate the
        # same condition synchronously and reject AsyncCondition).  Go directly
        # to State.can_transition for any additional custom logic.
        return State.can_transition(self, trigger, to_state, *args, **kwargs)

    async def handle_event_async(self, event: str, *args, **kwargs) -> TransitionResult:
        """
        Async version of handle_event that can execute both sync and async handlers.
        """
        handler_info = _resolve_declarative_handler(self, event, None)
        if handler_info is not None:
            return await _invoke_declarative_handler_async(
                self, handler_info, event, args, kwargs
            )

        # Fallback to sync parent implementation
        return super().handle_event(event, *args, **kwargs)


class FSMBuilder:
    """
    Enhanced builder pattern for constructing FSMs with fluent interface.

    Performance: O(1) for all builder operations, O(n) only at build() time
    Memory: Minimal overhead during construction, full optimization after build()

    Features:
    - Auto-detection of async requirements (AsyncCondition, AsyncDeclarativeState)
    - Explicit async/sync mode selection
    - Support for both StateMachine and AsyncStateMachine
    - Enhanced logging and validation
    - Backwards compatibility with existing code
    - Fluent per-state callback registration (on_enter, on_exit, on_enter_async, on_exit_async)
    """

    __slots__ = (
        "_machine_type",
        "_initial_state",
        "_machine_kwargs",
        "_states",
        "_transitions",
        "_logger",
        "_machine",
        "_auto_detect",
        "_enter_callbacks",
        "_exit_callbacks",
        "_enter_async_callbacks",
        "_exit_async_callbacks",
    )

    # Explicit type annotation so mypyc doesn't narrow _machine to None
    # from the __init__ assignment.  (GH#4)
    _machine: Optional[StateMachine]

    def __init__(
        self,
        initial_state: State,
        *,
        async_mode: Optional[bool] = None,
        **machine_kwargs,
    ):
        """
        Initialize the FSM builder.

        Args:
            initial_state: The starting state
            async_mode: Force async (True) or sync (False) mode, or auto-detect (None)
            **machine_kwargs: Arguments passed to StateMachine/AsyncStateMachine constructor
        """
        if not isinstance(initial_state, State):
            raise TypeError("initial_state must be a State instance")
        self._initial_state = initial_state
        self._machine_kwargs = machine_kwargs
        self._states: Dict[str, State] = {initial_state.name: initial_state}
        self._transitions: List[tuple] = []

        # Set up logging
        logger_name = machine_kwargs.get("name", "FSM")
        self._logger = logging.getLogger(f"fast_fsm.builder.{logger_name}")

        # Validate every initial declarative guard regardless of selected mode.
        # Auto mode additionally uses the complete traversal for classification.
        detected_type = self._detect_async_requirements(initial_state)

        # Determine machine type
        if async_mode is None:
            self._auto_detect = True
            self._machine_type = detected_type
            self._logger.debug(
                "Builder: Auto-detected %s mode based on initial state",
                "async" if self._machine_type == AsyncStateMachine else "sync",
            )
        else:
            self._auto_detect = False
            self._machine_type = AsyncStateMachine if async_mode else StateMachine
            self._logger.debug(
                "Builder: Explicitly set to %s mode", "async" if async_mode else "sync"
            )

        # Per-state callback queues — applied in build()
        self._enter_callbacks: List[tuple] = []
        self._exit_callbacks: List[tuple] = []
        self._enter_async_callbacks: List[tuple] = []
        self._exit_async_callbacks: List[tuple] = []

        # We'll create the machine in build() to allow for re-evaluation
        self._machine = None

    def _ensure_mutable(self) -> None:
        """Raise when a successful build has published the immutable cache."""
        if self._machine is not None:
            raise RuntimeError(
                "Cannot mutate builder; Cannot change machine type after build() has been called"
            )

    def _detect_async_requirements(self, *states_or_conditions) -> type:
        """
        Detect if async FSM is required based on states and conditions.

        Args:
            *states_or_conditions: States, conditions, or other components to check

        Returns:
            AsyncStateMachine if async support needed, StateMachine otherwise
        """
        async_required = False
        for item in states_or_conditions:
            # Check for AsyncDeclarativeState
            if isinstance(item, AsyncDeclarativeState):
                async_required = True

            # Check direct and nested built-in condition wrappers through the
            # canonical graph classifier used by runtime dispatch.
            if isinstance(item, Condition) and StateMachine._contains_async_requirement(
                item
            ):
                async_required = True
            elif callable(item) and asyncio.iscoroutinefunction(item):
                async_required = True

            # Check DeclarativeState for async handlers
            if isinstance(item, DeclarativeState):
                for handler_info in item._handlers.values():
                    if handler_info.get("is_async", False):
                        async_required = True
                    condition = handler_info.get("condition")
                    if isinstance(
                        condition, Condition
                    ) and StateMachine._contains_async_requirement(condition):
                        async_required = True
                    elif callable(condition) and asyncio.iscoroutinefunction(condition):
                        async_required = True

        return AsyncStateMachine if async_required else StateMachine

    def add_state(self, state: State) -> "FSMBuilder":
        """Add a state to the builder with async detection"""
        self._ensure_mutable()
        if not isinstance(state, State):
            raise TypeError("state must be a State instance")
        registered = self._states.get(state.name)
        if registered is not None:
            if registered is state:
                return self
            raise ValueError(
                f"Builder already contains a different State object named '{state.name}'"
            )

        # Validate the complete candidate graph in every mode before publishing
        # staging. Explicit modes ignore the classification but not validation.
        detected_type = self._detect_async_requirements(state)
        required_type = self._machine_type
        if self._auto_detect:
            if (
                detected_type == AsyncStateMachine
                and self._machine_type == StateMachine
            ):
                required_type = AsyncStateMachine

        # Detection can reject malformed condition graphs. Do not publish the
        # candidate state or machine-mode upgrade until that validation passes.
        self._states[state.name] = state
        if required_type != self._machine_type:
            self._machine_type = required_type
            self._logger.debug(
                "Builder: Upgraded to async mode due to state '%s'", state.name
            )
        return self

    def add_transition(
        self,
        trigger: str,
        from_state: Union[str, List[str]],
        to_state: str,
        condition: Optional[Union[Condition, Callable]] = None,
        *,
        unless: Optional[Union[Condition, Callable]] = None,
    ) -> "FSMBuilder":
        """Add a transition to the builder with async detection.

        Args:
            trigger: Event that triggers the transition.
            from_state: Source state name or list of source state names.
            to_state: Target state name.
            condition: Optional guard condition.
            unless: Negation shorthand — allowed when this condition is False.
                    Mutually exclusive with ``condition``.
        """
        self._ensure_mutable()
        if condition is not None and unless is not None:
            raise ValueError(
                "'condition' and 'unless' are mutually exclusive — use one or the other."
            )
        if unless is not None:
            if isinstance(unless, Condition):
                condition = NegatedCondition(unless)
            elif callable(unless):
                condition = NegatedCondition(FuncCondition(unless))
            else:
                raise TypeError(
                    f"'unless' must be a Condition or callable, got {type(unless)}"
                )
        # Validate a supported guard graph before changing staging in auto and
        # explicit modes alike. Only auto mode consumes its async classification.
        detected_type = self._detect_async_requirements(condition)
        required_type = self._machine_type
        if self._auto_detect:
            if (
                detected_type == AsyncStateMachine
                and self._machine_type == StateMachine
            ):
                required_type = AsyncStateMachine

        # Keep the builder staging area atomic: graph validation must succeed
        # before either the transition or the auto-detected machine type lands.
        self._transitions.append((trigger, from_state, to_state, condition))
        if required_type != self._machine_type:
            self._machine_type = required_type
            self._logger.debug(
                "Builder: Upgraded to async mode due to async condition '%s'",
                getattr(condition, "name", str(condition)),
            )
        return self

    def on_enter(self, state_name: str, callback: Any) -> "FSMBuilder":
        """Register a synchronous on_enter callback for a state.

        The callback is wired to the machine in :meth:`build`. Multiple
        callbacks for the same state are registered in order.

        Args:
            state_name: Name of the state to watch.
            callback: Callable invoked when the FSM enters *state_name*.
                      Signature: ``callback(from_state, trigger, **kwargs)``.

        Returns:
            self, for method chaining.
        """
        self._ensure_mutable()
        self._enter_callbacks.append((state_name, callback))
        return self

    def on_exit(self, state_name: str, callback: Any) -> "FSMBuilder":
        """Register a synchronous on_exit callback for a state.

        Args:
            state_name: Name of the state to watch.
            callback: Callable invoked when the FSM exits *state_name*.
                      Signature: ``callback(to_state, trigger, **kwargs)``.

        Returns:
            self, for method chaining.
        """
        self._ensure_mutable()
        self._exit_callbacks.append((state_name, callback))
        return self

    def on_enter_async(self, state_name: str, callback: Any) -> "FSMBuilder":
        """Register an async on_enter callback for a state.

        Registering at least one async callback auto-upgrades the builder to
        :class:`AsyncStateMachine` when *async_mode* is ``None`` (auto-detect).
        Has no effect if the machine is forced to sync mode via *async_mode=False*
        or :meth:`force_sync` — a warning is logged instead.

        Args:
            state_name: Name of the state to watch.
            callback: Async callable invoked when the FSM enters *state_name*.
                      Signature: ``async callback(from_state, trigger, **kwargs)``.

        Returns:
            self, for method chaining.
        """
        self._ensure_mutable()
        self._enter_async_callbacks.append((state_name, callback))
        if self._auto_detect and self._machine_type == StateMachine:
            self._machine_type = AsyncStateMachine
            self._logger.debug(
                "Builder: Upgraded to async mode due to on_enter_async callback for '%s'",
                state_name,
            )
        return self

    def on_exit_async(self, state_name: str, callback: Any) -> "FSMBuilder":
        """Register an async on_exit callback for a state.

        Registering at least one async callback auto-upgrades the builder to
        :class:`AsyncStateMachine` when *async_mode* is ``None`` (auto-detect).

        Args:
            state_name: Name of the state to watch.
            callback: Async callable invoked when the FSM exits *state_name*.
                      Signature: ``async callback(to_state, trigger, **kwargs)``.

        Returns:
            self, for method chaining.
        """
        self._ensure_mutable()
        self._exit_async_callbacks.append((state_name, callback))
        if self._auto_detect and self._machine_type == StateMachine:
            self._machine_type = AsyncStateMachine
            self._logger.debug(
                "Builder: Upgraded to async mode due to on_exit_async callback for '%s'",
                state_name,
            )
        return self

    def force_async(self) -> "FSMBuilder":
        """Force the builder to create an AsyncStateMachine"""
        self._ensure_mutable()
        self._auto_detect = False
        self._machine_type = AsyncStateMachine
        self._logger.debug("Builder: Forced to async mode")
        return self

    def force_sync(self) -> "FSMBuilder":
        """Force the builder to create a regular StateMachine"""
        self._ensure_mutable()
        self._auto_detect = False
        self._machine_type = StateMachine
        self._logger.debug("Builder: Forced to sync mode")
        return self

    def _preflight_async_requirements(self) -> Optional[str]:
        """Validate all staged graphs and describe their first async requirement."""
        first_requirement: Optional[str] = None
        for state in self._states.values():
            if isinstance(state, AsyncDeclarativeState):
                if first_requirement is None:
                    first_requirement = f"AsyncDeclarativeState '{state.name}'"
            if isinstance(state, DeclarativeState):
                for trigger, handler_info in state._handlers.items():
                    if handler_info.get("is_async", False):
                        if first_requirement is None:
                            first_requirement = (
                                f"declarative handler for trigger '{trigger}'"
                            )
                    condition = handler_info.get("condition")
                    if isinstance(
                        condition, Condition
                    ) and StateMachine._contains_async_requirement(condition):
                        if first_requirement is None:
                            first_requirement = (
                                f"declarative condition for trigger '{trigger}'"
                            )
                    elif callable(condition) and asyncio.iscoroutinefunction(condition):
                        if first_requirement is None:
                            first_requirement = (
                                f"declarative condition for trigger '{trigger}'"
                            )

        for trigger, _, _, condition in self._transitions:
            if isinstance(
                condition, Condition
            ) and StateMachine._contains_async_requirement(condition):
                if first_requirement is None:
                    first_requirement = f"transition '{trigger}' condition"
            elif callable(condition) and asyncio.iscoroutinefunction(condition):
                if first_requirement is None:
                    first_requirement = f"transition '{trigger}' condition"

        if self._enter_async_callbacks:
            state_name, _ = self._enter_async_callbacks[0]
            if first_requirement is None:
                first_requirement = f"on_enter_async callback for '{state_name}'"
        if self._exit_async_callbacks:
            state_name, _ = self._exit_async_callbacks[0]
            if first_requirement is None:
                first_requirement = f"on_exit_async callback for '{state_name}'"
        return first_requirement

    def build(self) -> Union[StateMachine, AsyncStateMachine]:
        """Build and return the final state machine"""
        if self._machine is not None:
            return self._machine

        async_requirement = self._preflight_async_requirements()
        if async_requirement is not None:
            if self._auto_detect:
                self._machine_type = AsyncStateMachine
            elif self._machine_type == StateMachine:
                raise RuntimeError(
                    "Cannot build explicit sync FSM with async requirement in "
                    f"{async_requirement}"
                )

        # Keep all construction local until every registration succeeds. A failed
        # candidate must not freeze staging or become observable through _machine.
        candidate = self._machine_type(self._initial_state, **self._machine_kwargs)

        # Add all states
        for state in self._states.values():
            if state != self._initial_state:  # Initial state already added
                candidate.add_state(state)

        # Add all transitions
        for trigger, from_state, to_state, condition in self._transitions:
            to_state_obj = (
                self._states[to_state] if to_state in self._states else to_state
            )

            # Convert string names to state objects for the machine
            if isinstance(from_state, list):
                from_state_list = [
                    self._states[name] if name in self._states else name
                    for name in from_state
                ]
                candidate.add_transition(
                    trigger, from_state_list, to_state_obj, condition
                )
            else:
                from_state_single = (
                    self._states[from_state]
                    if from_state in self._states
                    else from_state
                )
                candidate.add_transition(
                    trigger, from_state_single, to_state_obj, condition
                )

        # Wire per-state sync callbacks
        for state_name, cb in self._enter_callbacks:
            candidate.on_enter(state_name, cb)
        for state_name, cb in self._exit_callbacks:
            candidate.on_exit(state_name, cb)

        # Wire per-state async callbacks (AsyncStateMachine only)
        if isinstance(candidate, AsyncStateMachine):
            for state_name, cb in self._enter_async_callbacks:
                candidate.on_enter_async(state_name, cb)
            for state_name, cb in self._exit_async_callbacks:
                candidate.on_exit_async(state_name, cb)
        elif self._enter_async_callbacks or self._exit_async_callbacks:
            self._logger.warning(
                "Builder: %d async callback(s) registered but building sync machine — they will be ignored",
                len(self._enter_async_callbacks) + len(self._exit_async_callbacks),
            )

        # Log final machine type and stats
        machine_type_name = (
            "AsyncStateMachine"
            if isinstance(candidate, AsyncStateMachine)
            else "StateMachine"
        )
        self._logger.info(
            "Builder: Created %s '%s' with %d states and %d transitions",
            machine_type_name,
            candidate.name,
            len(self._states),
            len(self._transitions),
        )

        self._machine = candidate
        return candidate

    @property
    def machine_type(self) -> type:
        """Get the type of machine that will be built"""
        return self._machine_type

    @property
    def is_async(self) -> bool:
        """Check if the builder will create an async machine"""
        return self._machine_type == AsyncStateMachine

    def __repr__(self) -> str:
        """String representation of the builder state"""
        machine_type_name = "AsyncStateMachine" if self.is_async else "StateMachine"
        return (
            f"FSMBuilder(states={len(self._states)}, transitions={len(self._transitions)}, "
            f"type={machine_type_name}, built={self._machine is not None})"
        )


def configure_fsm_logging(
    level: int = logging.WARNING,
    logger_name: str = "fast_fsm",
    format_string: str = "%(message)s",
) -> None:
    """
    Configure logging for FSM instances.

    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO, logging.WARNING)
        logger_name: Name of the logger to configure. Can use wildcards:
                    - 'fast_fsm' for all FSMs with default naming
                    - 'fast_fsm.MyFSM' for a specific named FSM
                    - 'traffic_light' for FSMs with custom logger names
        format_string: Format string for log messages

    Logging Levels for FSM:
        - WARNING: No FSM logging (default)
        - INFO: Successful transitions and failures
        - DEBUG: + condition evaluation, state validation
        - DEBUG-5 (5): + trigger attempts with arguments (ultra-verbose)

    Examples:
        # Enable transition logging
        configure_fsm_logging(logging.INFO, 'fast_fsm')

        # Enable detailed debugging
        configure_fsm_logging(logging.DEBUG, 'fast_fsm')

        # Enable ultra-verbose logging
        configure_fsm_logging(5, 'fast_fsm')  # DEBUG-5 level

        # Enable logging for a specific named FSM
        configure_fsm_logging(logging.INFO, 'fast_fsm.TrafficLight')
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Only add handler if we want to see output
    if level <= logging.INFO:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(format_string)
        handler.setFormatter(formatter)
        logger.addHandler(handler)


def set_fsm_logging_level(
    verbosity: str = "warning", logger_name: str = "fast_fsm"
) -> None:
    """
    Set FSM logging level using standard Python logging level names.

    Args:
        verbosity: Logging level name (case-insensitive).
                  Standard levels: 'debug', 'info', 'warning', 'error', 'critical'.
                  Convenience alias: 'off' (same as 'warning' — silences FSM logs).
                  Custom level: 'trace' (DEBUG-5, ultra-verbose trigger attempts).
        logger_name: Logger name to configure

    Examples:
        # Show transitions (DEBUG level)
        set_fsm_logging_level('debug')

        # Scope to a specific machine
        set_fsm_logging_level('debug', 'fast_fsm.MyFSM')

        # Silence FSM logs
        set_fsm_logging_level('warning')  # or 'off'

        # Ultra-verbose trigger tracing
        set_fsm_logging_level('trace')
    """
    level_map = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
        "off": logging.WARNING,  # convenience alias
        "trace": logging.DEBUG - 5,  # custom ultra-verbose level
    }

    key = verbosity.lower()
    if key not in level_map:
        raise ValueError(
            f"Invalid verbosity level: {verbosity!r}. "
            f"Valid options: {list(level_map.keys())}"
        )

    configure_fsm_logging(level_map[key], logger_name)


# Convenience factory functions


def simple_fsm(
    *state_names: str, initial: Optional[str] = None, name: str = "FSM"
) -> StateMachine:
    """
    Create a simple FSM with basic states.

    Args:
        *state_names: Names of states to create
        initial: Initial state name (defaults to first)
        name: FSM name

    Returns:
        StateMachine instance

    Example:
        fsm = simple_fsm('idle', 'running', 'error', initial='idle')
    """
    return StateMachine.from_states(*state_names, initial=initial, name=name)


def quick_fsm(
    initial_state: str, transitions: List[Tuple[str, str, str]], name: str = "FSM"
) -> StateMachine:
    """
    Quickly create an FSM from a transition list.

    Args:
        initial_state: Initial state name
        transitions: List of (trigger, from_state, to_state) tuples
        name: FSM name

    Returns:
        Configured StateMachine

    Example::

        fsm = quick_fsm(
            "idle",
            [
                ("start", "idle", "running"),
                ("stop", "running", "idle"),
            ],
        )
    """
    return StateMachine.quick_build(initial_state, transitions, name=name)


@overload
def condition_builder(func: Callable[..., bool]) -> FuncCondition: ...


@overload
def condition_builder(
    func: None = None, *, name: str = "", description: str = ""
) -> Callable[[Callable[..., bool]], FuncCondition]: ...


def condition_builder(
    func: Optional[Callable[..., bool]] = None,
    *,
    name: str = "",
    description: str = "",
) -> Union[FuncCondition, Callable[[Callable[..., bool]], FuncCondition]]:
    """
    Decorator to create condition functions with metadata.

    Can be used bare (``@condition_builder``) or with arguments
    (``@condition_builder(name="fuel_check")``).

    Args:
        func: Function to wrap (when used as bare decorator)
        name: Condition name (defaults to function ``__name__``)
        description: Condition description

    Returns:
        ``FuncCondition`` when used as bare decorator, or a decorator
        callable when used with arguments.

    Example::

        @condition_builder(name="fuel_check", description="Check fuel level")
        def has_fuel(level=0, **kwargs):
            return level > 0
    """

    def decorator(f: Callable[..., bool]) -> FuncCondition:
        func_name = getattr(f, "__name__", "anonymous_condition")
        return FuncCondition(f, name or func_name, description)

    if func is None:
        return decorator
    else:
        return decorator(func)
