"""
Abstract base classes for fast_fsm.

These classes are kept separate and uncompiled to allow for easy inheritance
from interpreted Python code while still allowing the core FSM logic to be compiled.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Awaitable, Callable, Optional, TypeAlias

__slots__ = ()


# Guard wrappers can retain an awaitable until the owning machine chooses the
# synchronous rejection or asynchronous awaiting boundary.  These aliases are
# public because ``fast_fsm`` is a typed distribution and callers may provide
# async callable objects (including instances with an async ``__call__``).
GuardResult: TypeAlias = bool | Awaitable[bool]
GuardCallable: TypeAlias = Callable[..., GuardResult]


class Condition(ABC):
    """
    Abstract base class for transition conditions.

    This class provides a standardized interface for creating custom transition
    conditions with logging support and performance optimization.
    """

    __slots__ = ("name", "description")

    def __init__(self, name: str, description: str = ""):
        """
        Initialize a condition.

        Args:
            name: Human-readable name for this condition
            description: Optional description of what this condition checks
        """
        self.name = name
        self.description = description or name

    @abstractmethod
    def check(self, *args: Any, **kwargs: Any) -> GuardResult:
        """
        Check if the condition is met.

        Args:
            **kwargs: Context data for evaluating the condition

        Returns:
            ``True`` or ``False`` for synchronous conditions. Callable-backed
            wrappers may return an awaitable; a ``StateMachine`` closes and
            rejects that result, while ``AsyncStateMachine`` awaits it.
        """
        pass  # pragma: no cover

    def __str__(self) -> str:
        """String representation showing condition name"""
        return self.name

    def __repr__(self) -> str:
        """Developer representation with class and name"""
        return f"{self.__class__.__name__}('{self.name}')"


_compiled_func_condition_check: Optional[Callable[..., GuardResult]] = None


def _bind_compiled_func_condition_check(
    checker: Callable[..., GuardResult],
) -> None:
    """Install the compiled core evaluator after the import cycle has completed."""
    global _compiled_func_condition_check
    _compiled_func_condition_check = checker


class FuncCondition(Condition):
    """
    Condition wrapper for functions.

    Provides backward compatibility by wrapping callable objects
    in the standardized Condition interface.
    """

    __slots__ = ("func",)

    def __init__(
        self,
        func: GuardCallable,
        name: Optional[str] = None,
        description: str = "",
    ):
        """
        Initialize with a callable.

        Args:
            func: Callable that takes ``**kwargs`` and returns ``GuardResult``.
            name: Name for this condition (defaults to function name).
            description: Description of what this condition does.
        """
        if name is None:
            name = getattr(func, "__name__", "custom_function")

        # Ensure name is not None for type checker
        assert name is not None
        super().__init__(name, description)
        self.func = func

    def check(self, *args: Any, **kwargs: Any) -> GuardResult:
        """Check condition by calling the wrapped function"""
        return self.func(*args, **kwargs)


class CompiledFuncCondition(Condition):
    """An interpreted-subclassable guard whose evaluation delegates to compiled core code.

    The public wrapper intentionally stays in ``conditions.py`` so users can
    inherit from it in ordinary Python. Once :mod:`fast_fsm.core` is imported,
    its ``check`` method dispatches to a mypyc-compiled helper. This keeps the
    accelerated evaluation path without asking mypyc to accept interpreted
    subclasses of a compiled class.

    Args:
        func: Any callable ``(*args, **kwargs) -> GuardResult``.
        name: Human-readable label. Defaults to ``func.__name__`` when present.
        description: Optional longer description.
    """

    __slots__ = ("func", "__dict__")

    def __init__(
        self,
        func: GuardCallable,
        name: Optional[str] = None,
        description: str = "",
    ) -> None:
        resolved_name = (
            name if name is not None else getattr(func, "__name__", "compiled_func")
        )
        super().__init__(resolved_name, description)
        self.func = func

    def check(self, *args: Any, **kwargs: Any) -> GuardResult:
        """Evaluate the wrapped function through the compiled core helper."""
        checker = _compiled_func_condition_check
        if checker is None:
            # Importing ``fast_fsm.conditions`` alone remains usable before the
            # package's core module binds the optional acceleration helper.
            return self.func(*args, **kwargs)
        return checker(self, *args, **kwargs)


class NegatedCondition(Condition):
    """Wraps another condition and inverts its result.

    Used internally by the ``unless=`` shorthand on
    :meth:`~fast_fsm.StateMachine.add_transition`.  Can also be used
    directly when you want to store a negated condition explicitly.

    Args:
        inner: The condition whose result will be inverted.

    Example::

        locked = FuncCondition(lambda **kw: kw.get('locked', False))
        fsm.add_transition('open', 'closed', 'open', unless=locked)
        # equivalent to:
        fsm.add_transition('open', 'closed', 'open', condition=NegatedCondition(locked))
    """

    __slots__ = ("_inner",)

    def __init__(self, inner: Condition) -> None:
        super().__init__(f"not({inner})", f"Negation of: {inner.description}")
        self._inner = inner

    def check(self, *args: Any, **kwargs: Any) -> bool:
        """Return the inverse of the wrapped condition's result."""
        return not self._inner.check(*args, **kwargs)


class AsyncCondition(Condition):
    """
    Abstract base class for asynchronous transition conditions.

    Allows checking real-time sensor data or other async operations.
    These conditions can be used in both sync and async state machines.
    """

    __slots__ = ()

    @abstractmethod
    async def check_async(self, *args: Any, **kwargs: Any) -> bool:
        """
        Asynchronously check if the condition is satisfied.

        Args:
            **kwargs: Context data for evaluating the condition

        Returns:
            True if condition is satisfied, False otherwise
        """
        pass  # pragma: no cover

    def check(self, *args: Any, **kwargs: Any) -> bool:
        """
        Synchronous wrapper that runs the async check.

        Creates a new event loop via :func:`asyncio.run`.  For better
        performance in async contexts, call :meth:`check_async` directly.

        Raises:
            RuntimeError: If called from within a running event loop
                (use ``await condition.check_async()`` instead).
        """
        return asyncio.run(self.check_async(*args, **kwargs))
