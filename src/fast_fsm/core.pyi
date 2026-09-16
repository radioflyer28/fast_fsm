import logging
from dataclasses import dataclass, field
from typing import (
    Any,
    Callable,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Union,
    overload,
)

from .conditions import (
    AndCondition as AndCondition,
    AsyncCondition as AsyncCondition,
    CompiledFuncCondition as CompiledFuncCondition,
    Condition as Condition,
    FuncCondition as FuncCondition,
    GuardCallable as GuardCallable,
    GuardResult as GuardResult,
    NegatedCondition as NegatedCondition,
    NotCondition as NotCondition,
    OrCondition as OrCondition,
)

_TransitionRow = Union[
    Tuple[
        str,
        Union[str, "State", List[Union[str, "State"]]],
        Union[str, "State"],
    ],
    Tuple[
        str,
        Union[str, "State", List[Union[str, "State"]]],
        Union[str, "State"],
        Optional[Union[Condition, GuardCallable]],
    ],
    Tuple[
        str,
        Union[str, "State", List[Union[str, "State"]]],
        Union[str, "State"],
        Optional[Union[Condition, GuardCallable]],
        object,
    ],
    Tuple[
        str,
        Union[str, "State", List[Union[str, "State"]]],
        Union[str, "State"],
        Optional[Union[Condition, GuardCallable]],
        object,
        object,
    ],
    Tuple[
        str,
        Union[str, "State", List[Union[str, "State"]]],
        Union[str, "State"],
        Optional[Union[Condition, GuardCallable]],
        object,
        object,
        object,
    ],
]

@dataclass(frozen=True, slots=True)
class _GraphSnapshot:
    name: str
    initial_state: State
    graph_version: int
    states: tuple[State, ...]
    transitions: tuple[Any, ...]
    initial_state_name: str
    current_state_name: str
    state_names: tuple[str, ...]

@dataclass(frozen=True, slots=True)
class FSMTraceEvent:
    operation: str
    stage: str
    result: str
    trigger: str | None
    source_state: str | None
    destination_state: str | None
    positional_args: tuple[Any, ...]
    keyword_args: Mapping[str, Any]
    error: BaseException | None
    priority: int | None = ...

FSMTraceRedactor = Callable[[FSMTraceEvent], Mapping[str, object] | None]

class TransitionError(RuntimeError):
    result: TransitionResult

    def __init__(self, result: TransitionResult) -> None: ...

@dataclass(slots=True)
class TransitionResult:
    success: bool
    from_state: str | None = ...
    to_state: str | None = ...
    trigger: str | None = ...
    error: str = ...
    committed: bool = field(default=False, compare=False)
    stage: str | None = field(default=None, compare=False)
    cause: BaseException | None = field(default=None, repr=False, compare=False)
    priority: int | None = field(default=None, compare=False)

    def raise_if_failed(self) -> TransitionResult: ...

class TransitionRecord:
    from_state: str
    trigger: str
    to_state: str
    timestamp: float
    priority: int | None

    def __init__(
        self,
        from_state: str,
        trigger: str,
        to_state: str,
        timestamp: float,
        priority: int | None = None,
    ) -> None: ...

class TransitionEntry:
    to_state: State
    condition: Condition | None
    priority: int
    condition_ref: str | None
    after: float | None
    within: float | None

    def __init__(
        self,
        to_state: State,
        condition: Condition | None = None,
        priority: int = 0,
        condition_ref: str | None = None,
        after: float | None = None,
        within: float | None = None,
    ) -> None: ...

class State:
    name: str

    def __init__(self, name: str, *, final: bool = False) -> None: ...
    @property
    def final(self) -> bool: ...
    @classmethod
    def create(
        cls,
        name: str,
        on_enter: Callable[..., Any] | None = None,
        on_exit: Callable[..., Any] | None = None,
        *,
        final: bool = False,
    ) -> CallbackState: ...
    def on_enter(
        self, from_state: State | None, trigger: str, *args: Any, **kwargs: Any
    ) -> None: ...
    def on_exit(
        self, to_state: State | None, trigger: str, *args: Any, **kwargs: Any
    ) -> None: ...
    def can_transition(
        self, trigger: str, to_state: State, *args: Any, **kwargs: Any
    ) -> bool: ...
    def handle_event(
        self, event: str, *args: Any, **kwargs: Any
    ) -> TransitionResult: ...

class CallbackState(State):
    def __init__(
        self,
        name: str,
        on_enter: Callable[..., Any] | None = None,
        on_exit: Callable[..., Any] | None = None,
        *,
        final: bool = False,
    ) -> None: ...
    def on_enter(
        self, from_state: State | None, trigger: str, *args: Any, **kwargs: Any
    ) -> None: ...
    def on_exit(
        self, to_state: State | None, trigger: str, *args: Any, **kwargs: Any
    ) -> None: ...

class StateMachine:
    def __init__(
        self,
        initial_state: State,
        *,
        name: str = "FSM",
        logger_name: str | None = None,
        clock: Callable[[], float] = ...,
    ) -> None: ...
    @classmethod
    def from_states(
        cls,
        *state_names: str,
        initial: str | None = None,
        name: str = "FSM",
        clock: Callable[[], float] = ...,
    ) -> StateMachine: ...
    @classmethod
    def quick_build(
        cls,
        initial_state: str | State,
        transitions: Sequence[_TransitionRow],
        states: list[str | State] | None = None,
        name: str = "FSM",
        clock: Callable[[], float] = ...,
    ) -> StateMachine: ...
    @classmethod
    def from_dict(
        cls,
        config: dict[str, Any],
        *,
        name: str | None = None,
        conditions: dict[str, Condition | GuardCallable] | None = None,
        clock: Callable[[], float] = ...,
    ) -> StateMachine: ...
    def to_dict(self) -> dict[str, Any]: ...
    def _graph_snapshot(self) -> _GraphSnapshot: ...
    def enable_history(self, max_entries: Any = 1000) -> None: ...
    def disable_history(self) -> None: ...
    @property
    def history(self) -> list[TransitionRecord]: ...
    def add_state(self, state: State) -> None: ...
    def add_transition(
        self,
        trigger: str,
        from_state: str | State | list[str | State],
        to_state: str | State,
        condition: Condition | GuardCallable | None = None,
        *,
        unless: Condition | GuardCallable | None = None,
        priority: object = 0,
        after: object = None,
        within: object = None,
    ) -> None: ...
    def add_transitions(self, transitions: list[_TransitionRow]) -> None: ...
    def add_bidirectional_transition(
        self,
        trigger1: str,
        trigger2: str,
        state1: str | State,
        state2: str | State,
        condition1: Condition | GuardCallable | None = None,
        condition2: Condition | GuardCallable | None = None,
        *,
        unless1: Condition | GuardCallable | None = None,
        unless2: Condition | GuardCallable | None = None,
        priority1: object = 0,
        priority2: object = 0,
        after1: object = None,
        within1: object = None,
        after2: object = None,
        within2: object = None,
    ) -> None: ...
    def add_emergency_transition(
        self,
        trigger: str,
        to_state: str | State,
        condition: Condition | GuardCallable | None = None,
        *,
        unless: Condition | GuardCallable | None = None,
        priority: object = 0,
        after: object = None,
        within: object = None,
    ) -> None: ...
    @property
    def name(self) -> str: ...
    @property
    def current_state(self) -> State: ...
    @property
    def is_terminated(self) -> bool: ...
    @property
    def current_state_name(self) -> str: ...
    @property
    def initial_state_name(self) -> str: ...
    def is_in(self, state: str | State) -> bool: ...
    def add_listener(self, *listeners: Any) -> None: ...
    def on_enter(self, state_name: str, callback: Any) -> None: ...
    def on_exit(self, state_name: str, callback: Any) -> None: ...
    def after_transition(self, callback: Any) -> None: ...
    def on_failed(self, callback: Any) -> None: ...
    def on_trigger(self, trigger_name: str, callback: Any) -> None: ...
    @property
    def states(self) -> list[str]: ...
    @property
    def triggers(self) -> list[str]: ...
    def get_available_triggers(self, state: str | None = None) -> list[str]: ...
    def get_reachable_states(self, from_state: str | None = None) -> list[str]: ...
    def transition_exists(
        self,
        trigger: str,
        from_state: str | None = None,
        to_state: str | None = None,
    ) -> bool: ...
    def can_trigger(self, trigger: str, *args: Any, **kwargs: Any) -> bool: ...
    def force_state(self, state_name: str) -> None: ...
    def reset(self) -> None: ...
    def snapshot(self) -> dict[str, Any]: ...
    def restore(self, snapshot: dict[str, Any]) -> None: ...
    def clone(self) -> StateMachine: ...
    def trigger(self, trigger: str, *args: Any, **kwargs: Any) -> TransitionResult: ...
    def safe_trigger(
        self, trigger: str, *args: Any, **kwargs: Any
    ) -> TransitionResult: ...
    def debug_info(self) -> dict[str, Any]: ...
    def print_debug_info(self) -> None: ...
    def validate_transition_completeness(self) -> dict[str, list[str]]: ...

class AsyncStateMachine(StateMachine):
    def __init__(
        self,
        initial_state: State,
        *,
        name: str = "FSM",
        logger_name: str | None = None,
        clock: Callable[[], float] = ...,
    ) -> None: ...
    def on_enter_async(self, state_name: str, callback: Any) -> None: ...
    def on_exit_async(self, state_name: str, callback: Any) -> None: ...
    def clone(self) -> AsyncStateMachine: ...
    async def can_trigger_async(
        self, trigger: str, *args: Any, **kwargs: Any
    ) -> bool: ...
    async def trigger_async(
        self, trigger: str, *args: Any, **kwargs: Any
    ) -> TransitionResult: ...

def transition(
    trigger: str,
    from_state: str | list[str] | None = None,
    to_state: str | None = None,
    condition: Any | None = None,
    *,
    priority: object = 0,
    after: object = None,
    within: object = None,
) -> Any: ...

class DeclarativeState(State):
    def __init__(
        self,
        name: str,
        logger_name: str | None = None,
        *,
        final: bool = False,
    ) -> None: ...
    def can_transition(
        self, trigger: str, to_state: State, *args: Any, **kwargs: Any
    ) -> bool: ...
    def handle_event(
        self, event: str, *args: Any, **kwargs: Any
    ) -> TransitionResult: ...

class AsyncDeclarativeState(DeclarativeState):
    async def can_transition_async(
        self, trigger: str, to_state: State, *args: Any, **kwargs: Any
    ) -> bool: ...
    async def handle_event_async(
        self, event: str, *args: Any, **kwargs: Any
    ) -> TransitionResult: ...

class FSMBuilder:
    def __init__(
        self,
        initial_state: State,
        *,
        async_mode: bool | None = None,
        **machine_kwargs: Any,
    ) -> None: ...
    def add_state(self, state: State) -> FSMBuilder: ...
    def add_transition(
        self,
        trigger: str,
        from_state: str | list[str],
        to_state: str,
        condition: Condition | GuardCallable | None = None,
        *,
        unless: Condition | GuardCallable | None = None,
        priority: object = 0,
        after: object = None,
        within: object = None,
    ) -> FSMBuilder: ...
    def on_enter(self, state_name: str, callback: Any) -> FSMBuilder: ...
    def on_exit(self, state_name: str, callback: Any) -> FSMBuilder: ...
    def on_enter_async(self, state_name: str, callback: Any) -> FSMBuilder: ...
    def on_exit_async(self, state_name: str, callback: Any) -> FSMBuilder: ...
    def force_async(self) -> FSMBuilder: ...
    def force_sync(self) -> FSMBuilder: ...
    def build(self) -> StateMachine | AsyncStateMachine: ...
    @property
    def machine_type(self) -> type: ...
    @property
    def is_async(self) -> bool: ...

class FSMLoggingHandle:
    def __init__(
        self,
        logger: logging.Logger,
        handler: logging.StreamHandler[Any] | None,
        prior_level: int,
        prior_propagate: bool,
        configured_level: int,
        configured_propagate: bool | None,
        generation: int,
    ) -> None: ...
    def restore(self) -> None: ...

def configure_fsm_logging(
    level: int = ...,
    logger_name: str = "fast_fsm",
    format_string: str = "%(message)s",
    *,
    propagate: bool | None = None,
    redactor: FSMTraceRedactor | None = None,
) -> FSMLoggingHandle: ...
def set_fsm_logging_level(
    verbosity: str = "warning",
    logger_name: str = "fast_fsm",
    *,
    propagate: bool | None = None,
    redactor: FSMTraceRedactor | None = None,
) -> FSMLoggingHandle: ...
def simple_fsm(
    *state_names: str,
    initial: str | None = None,
    name: str = "FSM",
    clock: Callable[[], float] = ...,
) -> StateMachine: ...
def quick_fsm(
    initial_state: str,
    transitions: list[_TransitionRow],
    name: str = "FSM",
    *,
    clock: Callable[[], float] = ...,
) -> StateMachine: ...
@overload
def condition_builder(func: GuardCallable) -> FuncCondition: ...
@overload
def condition_builder(
    func: None = None,
    *,
    name: str = "",
    description: str = "",
) -> Callable[[GuardCallable], FuncCondition]: ...
