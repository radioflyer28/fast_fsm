"""
Abstract base classes for fast_fsm.

These classes are kept separate and uncompiled to allow for easy inheritance
from interpreted Python code while still allowing the core FSM logic to be compiled.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Callable, Optional

__slots__ = ()


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
    def check(self, **kwargs: Any) -> bool:
        """
        Check if the condition is met.

        Args:
            **kwargs: Context data for evaluating the condition

        Returns:
            True if condition is satisfied, False otherwise
        """
        pass

    def __str__(self) -> str:
        """String representation showing condition name"""
        return self.name

    def __repr__(self) -> str:
        """Developer representation with class and name"""
        return f"{self.__class__.__name__}('{self.name}')"


class FuncCondition(Condition):
    """
    Condition wrapper for functions.

    Provides backward compatibility by wrapping callable objects
    in the standardized Condition interface.
    """

    __slots__ = ("func",)

    def __init__(
        self,
        func: Callable[..., bool],
        name: Optional[str] = None,
        description: str = "",
    ):
        """
        Initialize with a callable.

        Args:
            func: Callable that takes ``**kwargs`` and returns bool.
            name: Name for this condition (defaults to function name).
            description: Description of what this condition does.
        """
        if name is None:
            name = getattr(func, "__name__", "custom_function")

        # Ensure name is not None for type checker
        assert name is not None
        super().__init__(name, description)
        self.func = func

    def check(self, **kwargs: Any) -> bool:
        """Check condition by calling the wrapped function"""
        return self.func(**kwargs)


class NegatedCondition(Condition):
    """Wraps another condition and inverts its result.

    Used internally by the ``unless=`` shorthand on
    :meth:`~fast_fsm.StateMachine.add_transition`.  Can also be used
    directly when you want to store a negated condition explicitly.

    Args:
        inner: The condition whose result will be inverted.

    Example:
        locked = FuncCondition(lambda **kw: kw.get('locked', False))
        fsm.add_transition('open', 'closed', 'open', unless=locked)
        # equivalent to:
        fsm.add_transition('open', 'closed', 'open', condition=NegatedCondition(locked))
    """

    __slots__ = ("_inner",)

    def __init__(self, inner: Condition) -> None:
        super().__init__(f"not({inner})", f"Negation of: {inner.description}")
        self._inner = inner

    def check(self, **kwargs: Any) -> bool:
        """Return the inverse of the wrapped condition's result."""
        return not self._inner.check(**kwargs)


class AsyncCondition(Condition):
    """
    Abstract base class for asynchronous transition conditions.

    Allows checking real-time sensor data or other async operations.
    These conditions can be used in both sync and async state machines.
    """

    __slots__ = ()

    @abstractmethod
    async def check_async(self, **kwargs: Any) -> bool:
        """
        Asynchronously check if the condition is satisfied.

        Args:
            **kwargs: Context data for evaluating the condition

        Returns:
            True if condition is satisfied, False otherwise
        """
        pass

    def check(self, **kwargs: Any) -> bool:
        """
        Synchronous wrapper that runs the async check.

        Creates a new event loop via :func:`asyncio.run`.  For better
        performance in async contexts, call :meth:`check_async` directly.

        Raises:
            RuntimeError: If called from within a running event loop
                (use ``await condition.check_async()`` instead).
        """
        return asyncio.run(self.check_async(**kwargs))
