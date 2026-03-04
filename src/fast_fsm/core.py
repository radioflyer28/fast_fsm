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
from abc import ABC
from typing import Optional, Dict, Any, Callable, List, Union, Tuple, overload
from dataclasses import dataclass
import asyncio
from mypy_extensions import mypyc_attr
from .conditions import Condition, FuncCondition, AsyncCondition, NegatedCondition


@dataclass(slots=True)
class TransitionResult:
    """Result of a state transition."""

    success: bool
    from_state: Optional[str] = None
    to_state: Optional[str] = None
    trigger: Optional[str] = None
    error: str = ""


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


@mypyc_attr(allow_interpreted_subclasses=True)
class State(ABC):
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
            on_enter: Optional callback for entering the state
            on_exit: Optional callback for exiting the state

        Returns:
            CallbackState instance with configured callbacks

        Example:
            state = State.create('processing',
                               on_enter=lambda *args, **kwargs: print('Processing started'),
                               on_exit=lambda *args, **kwargs: print('Processing finished'))
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
        "_current_state",
        "_states",
        "_transitions",
        "_logger",
        "_on_exit_listeners",
        "_on_enter_listeners",
        "_after_listeners",
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
        self._name = name
        self._current_state = initial_state
        self._states: Dict[str, State] = {initial_state.name: initial_state}
        self._transitions: Dict[str, Dict[str, TransitionEntry]] = {}

        # Use name-based logger if not specified
        if logger_name is None:
            logger_name = f"fast_fsm.{name}"
        self._logger = logging.getLogger(logger_name)

        # Listener lists — pre-extracted bound method references for zero-overhead
        # empty checks.  Populated by add_listener().
        self._on_exit_listeners: List[Any] = []
        self._on_enter_listeners: List[Any] = []
        self._after_listeners: List[Any] = []

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

        Example:
            fsm = StateMachine.quick_build('idle', [
                ('start', 'idle', 'running'),
                ('stop', 'running', 'idle'),
                ('error', 'running', 'error')
            ])
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

    def _register_state(self, state: State) -> None:
        """Register a state and initialize its transition table"""
        self._states[state.name] = state
        if state.name not in self._transitions:
            self._transitions[state.name] = {}

    def add_state(self, state: State) -> None:
        """
        Add a state to the machine.

        Performance: O(1) - Constant time state registration
        Memory: +~32 bytes per state (slots optimization)
        """
        self._register_state(state)

    def add_transition(
        self,
        trigger: str,
        from_state: Union[str, State, List[Union[str, State]]],
        to_state: Union[str, State],
        condition: Optional[Union[Condition, Callable[..., bool]]] = None,
        *,
        unless: Optional[Union[Condition, Callable[..., bool]]] = None,
    ) -> None:
        """
        Add a transition to the state machine.

        Performance: O(1) - Direct dictionary insertion, no loops
        Memory: +~64 bytes per transition (dict entry overhead)

        Args:
            trigger: Event that triggers the transition
            from_state: Source state(s) - can be string, state object, or list
            to_state: Target state - can be string or state object
            condition: Optional condition - can be Condition or callable function.
                      Callable functions receive (*args, **kwargs) from trigger calls.
            unless: Negation shorthand — the transition is allowed when this
                    condition is **False**.  Mutually exclusive with ``condition``.
        """
        # Normalize inputs
        if not isinstance(from_state, list):
            from_state = [from_state]

        # Convert to state names
        from_names = []
        for state in from_state:
            if isinstance(state, State):
                from_names.append(state.name)
            else:
                from_names.append(state)

        to_name = to_state.name if isinstance(to_state, State) else to_state
        if isinstance(to_state, str):
            to_state_obj = self._states.get(to_name)
            if to_state_obj is None:
                raise ValueError(
                    f"Target state '{to_name}' not found. "
                    "Add it with add_state() before adding transitions."
                )
        else:
            to_state_obj = to_state

        # unless= and condition= are mutually exclusive
        if condition is not None and unless is not None:
            raise ValueError(
                "'condition' and 'unless' are mutually exclusive — use one or the other."
            )

        # Resolve unless= into a NegatedCondition
        if unless is not None:
            if isinstance(unless, Condition):
                condition = NegatedCondition(unless)
            elif callable(unless):
                condition = NegatedCondition(FuncCondition(unless))
            else:
                raise TypeError(
                    f"'unless' must be a Condition or callable, got {type(unless)}"
                )

        # Normalize condition - wrap functions in FuncCondition for consistency
        normalized_condition = None
        if condition is not None:
            if isinstance(condition, Condition):
                normalized_condition = condition
            elif callable(condition):
                # Wrap function in FuncCondition for consistent interface
                normalized_condition = FuncCondition(condition)
            else:
                raise TypeError(
                    f"Condition must be Condition or callable, got {type(condition)}"
                )

        # Add transitions for each source state
        for from_state_name in from_names:
            if from_state_name not in self._transitions:
                self._transitions[from_state_name] = {}

            self._transitions[from_state_name][trigger] = TransitionEntry(
                to_state_obj, normalized_condition
            )

    def add_transitions(
        self,
        transitions: List[
            Tuple[str, Union[str, State, List[Union[str, State]]], Union[str, State]]
        ],
    ) -> None:
        """
        Add multiple transitions at once.

        Args:
            transitions: List of (trigger, from_state(s), to_state) tuples

        Example:
            fsm.add_transitions([
                ('start', 'idle', 'running'),
                ('stop', 'running', 'idle'),
                ('error', ['running', 'idle'], 'error')
            ])
        """
        for trigger, from_state, to_state in transitions:
            self.add_transition(trigger, from_state, to_state)

    def add_bidirectional_transition(
        self,
        trigger1: str,
        trigger2: str,
        state1: Union[str, State],
        state2: Union[str, State],
        condition1: Optional[Union[Condition, Callable]] = None,
        condition2: Optional[Union[Condition, Callable]] = None,
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

        Example:
            fsm.add_bidirectional_transition('pause', 'resume', 'running', 'paused')
        """
        self.add_transition(trigger1, state1, state2, condition1)
        self.add_transition(trigger2, state2, state1, condition2)

    def add_emergency_transition(
        self,
        trigger: str,
        to_state: Union[str, State],
        condition: Optional[Union[Condition, Callable]] = None,
    ) -> None:
        """
        Add an emergency transition from all states to a specific state.

        Args:
            trigger: Emergency trigger name
            to_state: Target state for emergency
            condition: Optional condition for the emergency

        Example:
            fsm.add_emergency_transition('emergency_stop', 'error')
        """
        all_states: List[Union[str, State]] = list(self._states.keys())
        self.add_transition(trigger, all_states, to_state, condition)

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

        **Argument semantics:**

        - *source* / *target* — :class:`State` objects (access ``.name`` for the string)
        - *trigger* — the trigger name string
        - ``**kwargs`` — forwarded from the original :meth:`trigger` call

        Bound method references are extracted at registration time so the
        hot path pays zero per-call overhead when listeners are attached and
        *no* overhead at all when the list is empty (guarded by
        ``if self._on_exit_listeners``).

        Methods that are absent on a listener are silently skipped.

        Args:
            *listeners: One or more observer objects.

        Example:
            class TransitionLogger:
                def after_transition(self, source, target, trigger, **kwargs):
                    print(f"{source.name} --[{trigger}]--> {target.name}")

            fsm.add_listener(TransitionLogger())
        """
        for listener in listeners:
            fn = getattr(listener, "on_exit_state", None)
            if callable(fn):
                self._on_exit_listeners.append(fn)
            fn = getattr(listener, "on_enter_state", None)
            if callable(fn):
                self._on_enter_listeners.append(fn)
            fn = getattr(listener, "after_transition", None)
            if callable(fn):
                self._after_listeners.append(fn)

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
        current_name = self._current_state.name

        if current_name not in self._transitions:
            return False

        if trigger not in self._transitions[current_name]:
            return False

        entry = self._transitions[current_name][trigger]

        if entry.condition:
            safe_kwargs = self._sanitize_condition_kwargs(kwargs)
            if not entry.condition.check(*args, **safe_kwargs):
                return False

        return self._current_state.can_transition(
            trigger, entry.to_state, *args, **kwargs
        )

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
        # Default implementation: basic safety checks
        safe_kwargs = {}

        # Limit to reasonable number of arguments to prevent memory issues
        if len(kwargs) > 50:
            self._logger.warning(
                "%s: Too many kwargs (%d) passed to condition, truncating",
                self._name,
                len(kwargs),
            )
            # Keep only first 50 items
            kwargs = dict(list(kwargs.items())[:50])

        # Copy kwargs, filtering out potentially dangerous items
        for key, value in kwargs.items():
            # Skip private/protected attributes
            if key.startswith("_"):
                self._logger.debug(
                    "%s: Skipping private kwarg '%s' for condition", self._name, key
                )
                continue

            # Validate key is reasonable string
            if not isinstance(key, str) or len(key) > 100:
                self._logger.warning(
                    "%s: Skipping invalid kwarg key: %s", self._name, repr(key)
                )
                continue

            # Add value (conditions should validate their own expected types)
            safe_kwargs[key] = value

        return safe_kwargs

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
        current_name = self._current_state.name

        # Log trigger attempt (most verbose level)
        if self._logger.isEnabledFor(
            logging.DEBUG - 5
        ):  # Custom level for ultra-verbose
            args_str = f"args={args}, kwargs={kwargs}" if args or kwargs else "no args"
            self._logger.log(
                logging.DEBUG - 5,
                "%s: Attempting trigger '%s' from state '%s' with %s",
                self._name,
                trigger,
                current_name,
                args_str,
            )

        # Check if transition exists
        if (
            current_name not in self._transitions
            or trigger not in self._transitions[current_name]
        ):
            error_msg = (
                f"No transition for trigger '{trigger}' from state '{current_name}'"
            )
            self._logger.info("%s: FAILED - %s", self._name, error_msg)
            return TransitionResult(
                False, from_state=current_name, trigger=trigger, error=error_msg
            )

        return self._transitions[current_name][trigger], current_name

    def _execute_transition(
        self, to_state: State, trigger: str, *args: Any, **kwargs: Any
    ) -> TransitionResult:
        """Perform exit/enter callbacks and state change.

        Assumes all pre-checks (condition, permission) have already passed.
        """
        old_state = self._current_state

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
        except Exception as e:
            self._logger.warning(
                "%s: Exception in on_exit for state '%s': %s",
                self._name,
                old_state.name,
                e,
            )

        # Notify on_exit_state listeners (after state's own on_exit)
        if self._on_exit_listeners:
            for fn in self._on_exit_listeners:
                try:
                    fn(old_state, to_state, trigger, **kwargs)
                except Exception as e:
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
        except Exception as e:
            self._logger.warning(
                "%s: Exception in on_enter for state '%s': %s",
                self._name,
                to_state.name,
                e,
            )

        # Notify on_enter_state listeners (after state's own on_enter)
        if self._on_enter_listeners:
            for fn in self._on_enter_listeners:
                try:
                    fn(to_state, old_state, trigger, **kwargs)
                except Exception as e:
                    self._logger.warning(
                        "%s: Exception in on_enter_state listener: %s",
                        self._name,
                        e,
                    )

        # Log successful transition (main transition log)
        self._logger.info(
            "%s: %s --[%s]--> %s", self._name, old_state.name, trigger, to_state.name
        )

        # Notify after_transition listeners
        if self._after_listeners:
            for fn in self._after_listeners:
                try:
                    fn(old_state, to_state, trigger, **kwargs)
                except Exception as e:
                    self._logger.warning(
                        "%s: Exception in after_transition listener: %s",
                        self._name,
                        e,
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
        resolved = self._resolve_trigger(trigger, *args, **kwargs)
        if isinstance(resolved, TransitionResult):
            return resolved
        entry, current_name = resolved
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
                # Validate kwargs before passing to condition (safety improvement)
                safe_kwargs = self._sanitize_condition_kwargs(kwargs)
                condition_result = condition.check(*args, **safe_kwargs)
                self._logger.debug(
                    "%s: Condition '%s' result: %s",
                    self._name,
                    condition_name,
                    condition_result,
                )
                if not condition_result:
                    error_msg = f"Transition condition '{condition_name}' failed for '{trigger}' from '{current_name}'"
                    self._logger.info("%s: FAILED - %s", self._name, error_msg)
                    return TransitionResult(
                        False, from_state=current_name, trigger=trigger, error=error_msg
                    )
            except Exception as e:
                error_msg = f"Condition '{condition_name}' raised exception: {e}"
                self._logger.warning("%s: FAILED - %s", self._name, error_msg)
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
        if not self._current_state.can_transition(trigger, to_state, *args, **kwargs):
            error_msg = f"State '{current_name}' rejected transition '{trigger}'"
            self._logger.info("%s: FAILED - %s", self._name, error_msg)
            return TransitionResult(
                False, from_state=current_name, trigger=trigger, error=error_msg
            )

        return self._execute_transition(to_state, trigger, *args, **kwargs)

    def safe_trigger(self, trigger: str, *args, **kwargs) -> TransitionResult:
        """
        Safe version of trigger that never raises exceptions.

        Args:
            trigger: The trigger/event name
            *args: Positional arguments for the transition
            **kwargs: Keyword arguments for the transition

        Returns:
            TransitionResult with detailed error information
        """
        try:
            return self.trigger(trigger, *args, **kwargs)
        except Exception as e:
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
    """

    async def can_trigger_async(self, trigger: str, *args, **kwargs) -> bool:
        """Async version of can_trigger"""
        current_name = self._current_state.name

        if current_name not in self._transitions:
            return False

        if trigger not in self._transitions[current_name]:
            return False

        entry = self._transitions[current_name][trigger]
        condition = entry.condition

        if condition:
            if isinstance(condition, AsyncCondition):
                if not await condition.check_async(*args, **kwargs):
                    return False
            else:
                if not condition.check(*args, **kwargs):
                    return False

        # Use async can_transition when the state supports it (e.g. AsyncDeclarativeState)
        if hasattr(self._current_state, "can_transition_async"):
            return await self._current_state.can_transition_async(
                trigger, entry.to_state, *args, **kwargs
            )
        return self._current_state.can_transition(
            trigger, entry.to_state, *args, **kwargs
        )

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
        resolved = self._resolve_trigger(trigger, *args, **kwargs)
        if isinstance(resolved, TransitionResult):
            return resolved
        entry, current_name = resolved
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
                if isinstance(condition, AsyncCondition):
                    condition_result = await condition.check_async(*args, **kwargs)
                else:
                    condition_result = condition.check(*args, **kwargs)

                self._logger.debug(
                    "%s: Condition '%s' result: %s",
                    self._name,
                    condition_name,
                    condition_result,
                )
                if not condition_result:
                    error_msg = f"Transition condition '{condition_name}' failed for '{trigger}' from '{current_name}'"
                    self._logger.info("%s: FAILED - %s", self._name, error_msg)
                    return TransitionResult(
                        False, from_state=current_name, trigger=trigger, error=error_msg
                    )
            except Exception as e:
                error_msg = f"Condition '{condition_name}' raised exception: {e}"
                self._logger.warning("%s: FAILED - %s", self._name, error_msg)
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
        # Use async can_transition when the state supports it (e.g. AsyncDeclarativeState)
        if hasattr(self._current_state, "can_transition_async"):
            can_proceed = await self._current_state.can_transition_async(
                trigger, to_state, *args, **kwargs
            )
        else:
            can_proceed = self._current_state.can_transition(
                trigger, to_state, *args, **kwargs
            )
        if not can_proceed:
            error_msg = f"State '{current_name}' rejected transition '{trigger}'"
            self._logger.info("%s: FAILED - %s", self._name, error_msg)
            return TransitionResult(
                False, from_state=current_name, trigger=trigger, error=error_msg
            )

        return self._execute_transition(to_state, trigger, *args, **kwargs)


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
        # Check if we have a handler for this trigger
        if trigger in self._handlers:
            handler_info = self._handlers[trigger]
            condition = handler_info.get("condition")

            # Evaluate decorator condition if present
            if condition:
                try:
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
                        condition_result = condition(*args, **kwargs)
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

                except Exception as e:
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
        if event in self._handlers:
            handler_info = self._handlers[event]
            method = handler_info["method"]
            method_name = method.__name__

            self._logger.debug(
                "State '%s': Executing handler '%s' for event '%s'",
                self.name,
                method_name,
                event,
            )

            try:
                # Handle async methods
                if handler_info["is_async"]:
                    self._logger.warning(
                        "State '%s': Async handler '%s' cannot be executed in sync context. "
                        "Use AsyncDeclarativeState for async methods.",
                        self.name,
                        method_name,
                    )
                    return TransitionResult(
                        False, error=f"Async handler '{method_name}' in sync context"
                    )

                # Execute synchronous handler
                result = method(*args, **kwargs)

                # Normalize result
                if result is None:
                    result = TransitionResult(True)
                elif isinstance(result, bool):
                    result = TransitionResult(result)
                elif not isinstance(result, TransitionResult):
                    result = TransitionResult(
                        True, error=f"Invalid return type from handler: {type(result)}"
                    )

                # Log result
                if result.success:
                    self._logger.debug(
                        "State '%s': Handler '%s' succeeded", self.name, method_name
                    )
                else:
                    self._logger.info(
                        "State '%s': Handler '%s' failed: %s",
                        self.name,
                        method_name,
                        result.error or "Unknown error",
                    )

                return result

            except Exception as e:
                error_msg = f"Handler '{method_name}' raised exception: {e}"
                self._logger.warning("State '%s': %s", self.name, error_msg)
                return TransitionResult(False, error=error_msg)

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
        # Check if we have a handler for this trigger
        if trigger in self._handlers:
            handler_info = self._handlers[trigger]
            condition = handler_info.get("condition")

            # Evaluate decorator condition if present
            if condition:
                try:
                    # Handle async conditions
                    if isinstance(condition, AsyncCondition):
                        condition_result = await condition.check_async(*args, **kwargs)
                    elif isinstance(condition, Condition):
                        condition_result = condition.check(*args, **kwargs)
                    elif callable(condition):
                        condition_result = condition(*args, **kwargs)
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

                except Exception as e:
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
        if event in self._handlers:
            handler_info = self._handlers[event]
            method = handler_info["method"]
            method_name = method.__name__

            self._logger.debug(
                "State '%s': Executing async handler '%s' for event '%s'",
                self.name,
                method_name,
                event,
            )

            try:
                # Handle both async and sync methods
                if handler_info["is_async"]:
                    result = await method(*args, **kwargs)
                else:
                    result = method(*args, **kwargs)

                # Normalize result
                if result is None:
                    result = TransitionResult(True)
                elif isinstance(result, bool):
                    result = TransitionResult(result)
                elif not isinstance(result, TransitionResult):
                    result = TransitionResult(
                        True, error=f"Invalid return type from handler: {type(result)}"
                    )

                # Log result
                if result.success:
                    self._logger.debug(
                        "State '%s': Async handler '%s' succeeded",
                        self.name,
                        method_name,
                    )
                else:
                    self._logger.info(
                        "State '%s': Async handler '%s' failed: %s",
                        self.name,
                        method_name,
                        result.error or "Unknown error",
                    )

                return result

            except Exception as e:
                error_msg = f"Async handler '{method_name}' raised exception: {e}"
                self._logger.warning("State '%s': %s", self.name, error_msg)
                return TransitionResult(False, error=error_msg)

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
        self._initial_state = initial_state
        self._machine_kwargs = machine_kwargs
        self._states: Dict[str, State] = {initial_state.name: initial_state}
        self._transitions: List[tuple] = []

        # Set up logging
        logger_name = machine_kwargs.get("name", "FSM")
        self._logger = logging.getLogger(f"fast_fsm.builder.{logger_name}")

        # Determine machine type
        if async_mode is None:
            # Auto-detect based on initial state
            self._auto_detect = True
            self._machine_type = self._detect_async_requirements(initial_state)
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

        # We'll create the machine in build() to allow for re-evaluation
        self._machine = None

    def _detect_async_requirements(self, *states_or_conditions) -> type:
        """
        Detect if async FSM is required based on states and conditions.

        Args:
            *states_or_conditions: States, conditions, or other components to check

        Returns:
            AsyncStateMachine if async support needed, StateMachine otherwise
        """
        for item in states_or_conditions:
            # Check for AsyncDeclarativeState
            if isinstance(item, AsyncDeclarativeState):
                return AsyncStateMachine

            # Check for AsyncCondition
            if isinstance(item, AsyncCondition):
                return AsyncStateMachine

            # Check DeclarativeState for async handlers
            if isinstance(item, DeclarativeState):
                for handler_info in item._handlers.values():
                    if handler_info.get("is_async", False):
                        return AsyncStateMachine
                    condition = handler_info.get("condition")
                    if isinstance(condition, AsyncCondition):
                        return AsyncStateMachine

        return StateMachine

    def add_state(self, state: State) -> "FSMBuilder":
        """Add a state to the builder with async detection"""
        self._states[state.name] = state

        # Only upgrade if in auto-detect mode
        if self._machine is None and self._auto_detect:
            required_type = self._detect_async_requirements(state)
            if (
                required_type == AsyncStateMachine
                and self._machine_type == StateMachine
            ):
                self._machine_type = AsyncStateMachine
                self._logger.debug(
                    "Builder: Upgraded to async mode due to state '%s'", state.name
                )
        elif not self._auto_detect and self._machine_type == StateMachine:
            # In explicit sync mode, warn about async components
            if isinstance(state, AsyncDeclarativeState):
                self._logger.warning(
                    "Builder: AsyncDeclarativeState '%s' in explicit sync mode may have limited functionality",
                    state.name,
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
        self._transitions.append((trigger, from_state, to_state, condition))

        # Only upgrade if in auto-detect mode
        if condition and self._machine is None and self._auto_detect:
            required_type = self._detect_async_requirements(condition)
            if (
                required_type == AsyncStateMachine
                and self._machine_type == StateMachine
            ):
                self._machine_type = AsyncStateMachine
                self._logger.debug(
                    "Builder: Upgraded to async mode due to async condition '%s'",
                    getattr(condition, "name", str(condition)),
                )
        elif condition and not self._auto_detect and self._machine_type == StateMachine:
            # In explicit sync mode, warn about async conditions
            if isinstance(condition, AsyncCondition):
                self._logger.warning(
                    "Builder: AsyncCondition '%s' in explicit sync mode will be rejected",
                    getattr(condition, "name", str(condition)),
                )

        return self

    def force_async(self) -> "FSMBuilder":
        """Force the builder to create an AsyncStateMachine"""
        if self._machine is not None:
            raise RuntimeError(
                "Cannot change machine type after build() has been called"
            )

        self._machine_type = AsyncStateMachine
        self._logger.debug("Builder: Forced to async mode")
        return self

    def force_sync(self) -> "FSMBuilder":
        """Force the builder to create a regular StateMachine"""
        if self._machine is not None:
            raise RuntimeError(
                "Cannot change machine type after build() has been called"
            )

        # Validate that sync mode is compatible
        for state in self._states.values():
            if isinstance(state, AsyncDeclarativeState):
                self._logger.warning(
                    "Builder: AsyncDeclarativeState '%s' in sync mode may have limited functionality",
                    state.name,
                )

        for _, _, _, condition in self._transitions:
            if isinstance(condition, AsyncCondition):
                self._logger.warning(
                    "Builder: AsyncCondition '%s' in sync mode will be rejected",
                    getattr(condition, "name", str(condition)),
                )

        self._machine_type = StateMachine
        self._logger.debug("Builder: Forced to sync mode")
        return self

    def build(self) -> Union[StateMachine, AsyncStateMachine]:
        """Build and return the final state machine"""
        if self._machine is not None:
            return self._machine

        # Create the appropriate machine type
        self._machine = self._machine_type(self._initial_state, **self._machine_kwargs)
        assert self._machine is not None  # Help mypy understand this is not None

        # Add all states
        for state in self._states.values():
            if state != self._initial_state:  # Initial state already added
                self._machine.add_state(state)

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
                self._machine.add_transition(
                    trigger, from_state_list, to_state_obj, condition
                )
            else:
                from_state_single = (
                    self._states[from_state]
                    if from_state in self._states
                    else from_state
                )
                self._machine.add_transition(
                    trigger, from_state_single, to_state_obj, condition
                )

        # Log final machine type and stats
        machine_type_name = (
            "AsyncStateMachine"
            if isinstance(self._machine, AsyncStateMachine)
            else "StateMachine"
        )
        self._logger.info(
            "Builder: Created %s '%s' with %d states and %d transitions",
            machine_type_name,
            self._machine.name,
            len(self._states),
            len(self._transitions),
        )

        return self._machine

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
    verbosity: str = "off", logger_name: str = "fast_fsm"
) -> None:
    """
    Set FSM logging level using friendly names.

    Args:
        verbosity: Logging verbosity level
                  - 'off': No logging (default)
                  - 'basic': Show successful transitions and failures
                  - 'detailed': Show condition evaluation and validation
                  - 'ultra': Show all trigger attempts with arguments
        logger_name: Logger name to configure

    Examples:
        # Basic transition logging
        set_fsm_logging_level('basic')

        # Detailed debugging
        set_fsm_logging_level('detailed', 'fast_fsm.MyFSM')

        # Ultra-verbose logging
        set_fsm_logging_level('ultra')
    """
    level_map = {
        "off": logging.WARNING,
        "basic": logging.INFO,
        "detailed": logging.DEBUG,
        "ultra": logging.DEBUG - 5,  # Custom ultra-verbose level
    }

    if verbosity not in level_map:
        raise ValueError(
            f"Invalid verbosity level: {verbosity}. "
            f"Valid options: {list(level_map.keys())}"
        )

    configure_fsm_logging(level_map[verbosity], logger_name)


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

    Example:
        fsm = quick_fsm('idle', [
            ('start', 'idle', 'running'),
            ('stop', 'running', 'idle')
        ])
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

    Example:
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
