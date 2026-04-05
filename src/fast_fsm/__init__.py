"""
Fast FSM - High-Performance Finite State Machine Library

A blazing fast, memory-efficient finite state machine library for Python.
"""

from .core import (
    State,
    CallbackState,
    StateMachine,
    AsyncStateMachine,
    FSMBuilder,
    TransitionResult,
    TransitionError,
    TransitionEntry,
    TransitionRecord,
    Condition,
    FuncCondition,
    CompiledFuncCondition,
    AsyncCondition,
    NegatedCondition,
    DeclarativeState,
    AsyncDeclarativeState,
    transition,
    configure_fsm_logging,
    set_fsm_logging_level,
    simple_fsm,
    quick_fsm,
    condition_builder,
)
from .visualization import to_mermaid, to_mermaid_fenced, to_mermaid_document, to_plantuml, to_json
from .validation import (
    FSMValidator,
    EnhancedFSMValidator,
    ValidationIssue,
    validate_fsm,
    quick_validation_report,
    enhanced_validate_fsm,
    quick_health_check,
    validate_and_score,
    compare_fsms,
    batch_validate,
    fsm_lint,
)

from importlib.metadata import version as _get_version, PackageNotFoundError as _PNF

try:
    __version__ = _get_version("fast_fsm")
except _PNF:
    __version__ = "unknown"
__all__ = [
    # Core FSM components
    "State",
    "CallbackState",
    "StateMachine",
    "AsyncStateMachine",
    "FSMBuilder",
    "TransitionResult",
    "TransitionError",
    "TransitionEntry",
    "TransitionRecord",
    # Condition system
    "Condition",
    "FuncCondition",
    "CompiledFuncCondition",
    "AsyncCondition",
    "NegatedCondition",
    # Advanced state handling
    "DeclarativeState",
    "AsyncDeclarativeState",
    "transition",
    # Logging configuration
    "configure_fsm_logging",
    "set_fsm_logging_level",
    # Convenience functions
    "simple_fsm",
    "quick_fsm",
    "condition_builder",
    # Visualization
    "to_mermaid",
    "to_mermaid_fenced",
    "to_mermaid_document",
    "to_plantuml",
    "to_json",
    # Validation components (enhanced)
    "FSMValidator",
    "EnhancedFSMValidator",
    "ValidationIssue",
    "validate_fsm",
    "quick_validation_report",
    "enhanced_validate_fsm",
    "quick_health_check",
    "validate_and_score",
    "compare_fsms",
    "batch_validate",
    "fsm_lint",
]
