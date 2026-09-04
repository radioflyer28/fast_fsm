"""
Tests for configure_fsm_logging and set_fsm_logging_level.

All tests use real logging infrastructure — no mocking.
"""

import logging
import uuid
from typing import Any

import pytest

from fast_fsm.core import (
    AsyncStateMachine,
    DeclarativeState,
    FSMTraceEvent,
    State,
    StateMachine,
    configure_fsm_logging,
    set_fsm_logging_level,
    transition,
)
from fast_fsm.conditions import FuncCondition


TRACE_LEVEL = logging.DEBUG - 5
TRIGGER_SENTINEL = "trigger-secret-19"
SOURCE_SENTINEL = "source-secret-19"
DESTINATION_SENTINEL = "destination-secret-19"
POSITIONAL_SENTINEL = "positional-secret-19"
KEYWORD_SENTINEL = "keyword-secret-19"
EXCEPTION_SENTINEL = "exception-secret-19"
REPR_SENTINEL = "repr-secret-19"
MACHINE_SENTINEL = "machine-secret-19"
PRIVATE_KEY_SENTINEL = "_private-key-secret-19"
INVALID_KEY_SENTINEL = "invalid-key-secret-19-" + "x" * 101
RAW_SENTINELS = (
    TRIGGER_SENTINEL,
    SOURCE_SENTINEL,
    DESTINATION_SENTINEL,
    POSITIONAL_SENTINEL,
    KEYWORD_SENTINEL,
    EXCEPTION_SENTINEL,
    REPR_SENTINEL,
    MACHINE_SENTINEL,
    PRIVATE_KEY_SENTINEL,
    INVALID_KEY_SENTINEL,
)


class HostileRepr:
    """Payload whose representation is both observable and sensitive."""

    def __init__(self) -> None:
        self.repr_calls = 0

    def __repr__(self) -> str:
        self.repr_calls += 1
        return REPR_SENTINEL


class CaptureHandler(logging.Handler):
    """Capture every observable record and formatter surface without mocks."""

    def __init__(self) -> None:
        super().__init__(TRACE_LEVEL)
        self.records: list[tuple[Any, Any, dict[str, Any], str]] = []
        self.setFormatter(logging.Formatter("%(levelname)s:%(message)s"))

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(
            (record.msg, record.args, record.__dict__.copy(), self.format(record))
        )


class ApplicationFilter(logging.Filter):
    """Identity-bearing filter used to prove library configuration does not mutate it."""


class CloseTrackingHandler(CaptureHandler):
    """Application handler that records whether library configuration closes it."""

    def __init__(self) -> None:
        super().__init__()
        self.close_calls = 0

    def close(self) -> None:
        self.close_calls += 1
        super().close()


def _logger_name(label: str) -> str:
    return f"fast_fsm.phase19.{label}.{uuid.uuid4().hex}"


def _contains_raw_secret(value: object, secret: str) -> bool:
    """Inspect record data without coercing arbitrary caller objects to text."""

    if isinstance(value, str):
        return secret in value
    if isinstance(value, dict):
        return any(
            _contains_raw_secret(item, secret)
            for pair in value.items()
            for item in pair
        )
    if isinstance(value, (list, tuple)):
        return any(_contains_raw_secret(item, secret) for item in value)
    return False


def _assert_no_raw_payload(
    handler: CaptureHandler, hostile_payload: HostileRepr, stderr: str
) -> None:
    """Scan the complete record and formatter surface for every raw secret."""

    assert handler.records, "trace configuration must emit at least one fixed event"
    assert hostile_payload.repr_calls == 0
    assert all(secret not in stderr for secret in RAW_SENTINELS)

    for message, args, record_dict, formatted in handler.records:
        assert hostile_payload not in args
        assert hostile_payload not in record_dict.values()
        for secret in RAW_SENTINELS:
            assert secret not in formatted
            assert not _contains_raw_secret(message, secret)
            assert not _contains_raw_secret(args, secret)
            assert not _contains_raw_secret(record_dict, secret)


def _sync_trace_machine(
    logger_name: str, hostile_payload: HostileRepr
) -> tuple[StateMachine, StateMachine]:
    source = State(SOURCE_SENTINEL)
    destination = State(DESTINATION_SENTINEL)
    success_machine = StateMachine(source, name="sync-trace", logger_name=logger_name)
    success_machine.add_state(destination)
    success_machine.add_transition(TRIGGER_SENTINEL, source, destination)

    def raise_guard(*_args: object, **_kwargs: object) -> bool:
        raise ValueError(EXCEPTION_SENTINEL)

    failure_machine = StateMachine(
        State(f"failure-{SOURCE_SENTINEL}"),
        name="sync-trace-failure",
        logger_name=logger_name,
    )
    failure_target = State(f"failure-{DESTINATION_SENTINEL}")
    failure_machine.add_state(failure_target)
    failure_machine.add_transition(
        f"failure-{TRIGGER_SENTINEL}",
        failure_machine.current_state,
        failure_target,
        FuncCondition(raise_guard, "raising-guard"),
    )

    assert success_machine.trigger(
        TRIGGER_SENTINEL,
        POSITIONAL_SENTINEL,
        hostile_payload,
        sensitive=KEYWORD_SENTINEL,
    ).success
    assert not failure_machine.trigger(
        f"failure-{TRIGGER_SENTINEL}",
        POSITIONAL_SENTINEL,
        hostile_payload,
        sensitive=KEYWORD_SENTINEL,
    ).success
    return success_machine, failure_machine


# ---------------------------------------------------------------------------
# configure_fsm_logging
# ---------------------------------------------------------------------------


class TestConfigureFsmLogging:
    def test_sets_logger_level(self):
        configure_fsm_logging(logging.DEBUG, "fast_fsm.test_cfg_1")
        logger = logging.getLogger("fast_fsm.test_cfg_1")
        assert logger.level == logging.DEBUG

    def test_adds_handler_at_info(self):
        configure_fsm_logging(logging.INFO, "fast_fsm.test_cfg_2")
        logger = logging.getLogger("fast_fsm.test_cfg_2")
        assert len(logger.handlers) >= 1

    def test_warning_level_removes_only_library_owned_handlers(self):
        """Warning configuration must not clear application-owned handlers."""

        logger_name = _logger_name("warning")
        logger = logging.getLogger(logger_name)
        application_handler = CaptureHandler()
        logger.addHandler(application_handler)
        try:
            configure_fsm_logging(logging.INFO, logger_name)
            configure_fsm_logging(logging.WARNING, logger_name)
            assert logger.handlers == [application_handler]
        finally:
            logger.removeHandler(application_handler)
            application_handler.close()

    def test_duplicate_calls_dont_stack_handlers(self):
        for _ in range(5):
            configure_fsm_logging(logging.INFO, "fast_fsm.test_cfg_4")
        logger = logging.getLogger("fast_fsm.test_cfg_4")
        # Handlers should be cleared each time, so only 1 remains
        assert len(logger.handlers) == 1

    def test_fsm_respects_configured_logging(self, caplog):
        """Real FSM produces log messages when logging is enabled."""
        fsm = StateMachine(State("a"), name="log_test_1")
        fsm.add_state(State("b"))
        fsm.add_transition("go", "a", "b")

        with caplog.at_level(logging.DEBUG, logger="fast_fsm.log_test_1"):
            fsm.trigger("go")

        assert any("go" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# Phase 19 strict-RED trace redaction and ownership contracts
# ---------------------------------------------------------------------------


def test_default_trace_records_are_metadata_only_for_sync_results(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Default trace output never stores raw data in any handler-visible record."""

    logger_name = _logger_name("sync-default")
    logger = logging.getLogger(logger_name)
    application_handler = CaptureHandler()
    logger.addHandler(application_handler)
    try:
        handle = configure_fsm_logging(
            TRACE_LEVEL,
            logger_name,
            propagate=False,
            redactor=None,
        )
        hostile_payload = HostileRepr()
        _sync_trace_machine(logger_name, hostile_payload)
        _assert_no_raw_payload(
            application_handler, hostile_payload, capsys.readouterr().err
        )
        handle.restore()
    finally:
        logger.removeHandler(application_handler)
        application_handler.close()


@pytest.mark.asyncio
async def test_default_trace_records_are_metadata_only_for_async_results(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Async trace stages have the same no-payload record contract as sync ones."""

    logger_name = _logger_name("async-default")
    logger = logging.getLogger(logger_name)
    application_handler = CaptureHandler()
    logger.addHandler(application_handler)
    try:
        handle = configure_fsm_logging(
            TRACE_LEVEL,
            logger_name,
            propagate=False,
            redactor=None,
        )
        hostile_payload = HostileRepr()
        source = State(f"async-{SOURCE_SENTINEL}")
        destination = State(f"async-{DESTINATION_SENTINEL}")
        machine = AsyncStateMachine(source, name="async-trace", logger_name=logger_name)
        machine.add_state(destination)
        machine.add_transition(f"async-{TRIGGER_SENTINEL}", source, destination)

        result = await machine.trigger_async(
            f"async-{TRIGGER_SENTINEL}",
            POSITIONAL_SENTINEL,
            hostile_payload,
            sensitive=KEYWORD_SENTINEL,
        )
        assert result.success
        _assert_no_raw_payload(
            application_handler, hostile_payload, capsys.readouterr().err
        )
        handle.restore()
    finally:
        logger.removeHandler(application_handler)
        application_handler.close()


@pytest.mark.asyncio
async def test_async_trace_suppresses_legacy_failure_warnings(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A failed async guard cannot leak caller data through any warning record."""

    logger_name = _logger_name("async-failure")
    logger = logging.getLogger(logger_name)
    application_handler = CaptureHandler()
    logger.addHandler(application_handler)

    def raise_guard(*_args: object, **_kwargs: object) -> bool:
        raise ValueError(EXCEPTION_SENTINEL)

    def raise_failure_observer(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError(EXCEPTION_SENTINEL)

    try:
        handle = configure_fsm_logging(
            TRACE_LEVEL,
            logger_name,
            propagate=False,
            redactor=None,
        )
        hostile_payload = HostileRepr()
        source = State(SOURCE_SENTINEL)
        destination = State(DESTINATION_SENTINEL)
        machine = AsyncStateMachine(
            source,
            name=MACHINE_SENTINEL,
            logger_name=logger_name,
        )
        machine.add_state(destination)
        machine.add_transition(
            TRIGGER_SENTINEL,
            source,
            destination,
            FuncCondition(raise_guard, "raising-guard"),
        )
        machine.on_failed(raise_failure_observer)

        result = await machine.trigger_async(
            TRIGGER_SENTINEL,
            hostile_payload,
            sensitive=KEYWORD_SENTINEL,
        )

        assert not result.success
        _assert_no_raw_payload(
            application_handler, hostile_payload, capsys.readouterr().err
        )
        handle.restore()
    finally:
        logger.removeHandler(application_handler)
        application_handler.close()


def test_exact_trace_suppresses_trigger_and_declarative_legacy_diagnostics(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Every trigger-adjacent legacy diagnostic remains outside TRACE records."""

    logger_name = _logger_name("trigger-diagnostics")
    logger = logging.getLogger(logger_name)
    application_handler = CaptureHandler()
    logger.addHandler(application_handler)

    class GuardedState(DeclarativeState):
        @transition(
            TRIGGER_SENTINEL,
            from_state=SOURCE_SENTINEL,
            to_state=DESTINATION_SENTINEL,
            condition=lambda *_args, **_kwargs: True,
        )
        def guarded(self, *_args: object, **_kwargs: object) -> bool:
            return True

    class AsyncHandlerState(DeclarativeState):
        @transition(TRIGGER_SENTINEL)
        async def guarded(self, *_args: object, **_kwargs: object) -> bool:
            return True

    try:
        handle = configure_fsm_logging(
            TRACE_LEVEL, logger_name, propagate=False, redactor=None
        )
        hostile_payload = HostileRepr()
        source = GuardedState(SOURCE_SENTINEL, logger_name=logger_name)
        destination = State(DESTINATION_SENTINEL)
        machine = StateMachine(
            source, name=MACHINE_SENTINEL, logger_name=logger_name
        )
        machine.add_state(destination)
        machine.add_transition(TRIGGER_SENTINEL, source, destination)
        kwargs = {
            **{f"field_{index}": KEYWORD_SENTINEL for index in range(51)},
            INVALID_KEY_SENTINEL: KEYWORD_SENTINEL,
            PRIVATE_KEY_SENTINEL: KEYWORD_SENTINEL,
        }

        assert machine.trigger(
            TRIGGER_SENTINEL, POSITIONAL_SENTINEL, hostile_payload, **kwargs
        ).success

        async_source = AsyncHandlerState(SOURCE_SENTINEL, logger_name=logger_name)
        async_destination = State(DESTINATION_SENTINEL)
        sync_machine = StateMachine(
            async_source, name=MACHINE_SENTINEL, logger_name=logger_name
        )
        sync_machine.add_state(async_destination)
        sync_machine.add_transition(
            TRIGGER_SENTINEL, async_source, async_destination
        )
        assert not sync_machine.trigger(TRIGGER_SENTINEL).success

        _assert_no_raw_payload(
            application_handler, hostile_payload, capsys.readouterr().err
        )
        handle.restore()
    finally:
        logger.removeHandler(application_handler)
        application_handler.close()


def test_custom_redactor_receives_only_minimum_event_and_safe_output(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The explicit redactor is the only payload boundary and output is allowlisted."""

    logger_name = _logger_name("redactor")
    logger = logging.getLogger(logger_name)
    application_handler = CaptureHandler()
    logger.addHandler(application_handler)
    redactor_events: list[FSMTraceEvent] = []

    def redactor(event: FSMTraceEvent) -> dict[str, str]:
        redactor_events.append(event)
        assert tuple(event.__dataclass_fields__) == (
            "operation",
            "stage",
            "result",
            "trigger",
            "source_state",
            "destination_state",
            "positional_args",
            "keyword_args",
            "error",
        )
        return {"operation": "trusted-redaction", "detail": "allowed"}

    try:
        handle = configure_fsm_logging(
            TRACE_LEVEL,
            logger_name,
            propagate=False,
            redactor=redactor,
        )
        hostile_payload = HostileRepr()
        _sync_trace_machine(logger_name, hostile_payload)
        assert redactor_events
        _assert_no_raw_payload(
            application_handler, hostile_payload, capsys.readouterr().err
        )
        assert any(
            record_dict.get("trace_operation") == "trusted-redaction"
            for _message, _args, record_dict, _formatted in application_handler.records
        )
        handle.restore()
    finally:
        logger.removeHandler(application_handler)
        application_handler.close()


def test_trace_redactor_follows_reachable_parent_handler() -> None:
    """A child logger inherits its parent redactor but respects propagation stops."""

    parent_name = _logger_name("redactor-parent")
    child_name = f"{parent_name}.machine"
    blocked_name = f"{parent_name}.blocked"
    parent = logging.getLogger(parent_name)
    application_handler = CaptureHandler()
    parent.addHandler(application_handler)
    redactor_calls = 0

    def redactor(_event: FSMTraceEvent) -> dict[str, str]:
        nonlocal redactor_calls
        redactor_calls += 1
        return {"detail": "parent-redactor"}

    try:
        handle = configure_fsm_logging(
            TRACE_LEVEL,
            parent_name,
            propagate=False,
            redactor=redactor,
        )
        machine = StateMachine(State("source"), logger_name=child_name)
        machine.add_state(State("destination"))
        machine.add_transition("advance", "source", "destination")

        assert machine.trigger("advance").success
        assert redactor_calls == 1
        assert any(
            record[2].get("trace_detail") == "parent-redactor"
            for record in application_handler.records
        )

        blocked = logging.getLogger(blocked_name)
        blocked.setLevel(TRACE_LEVEL)
        blocked.propagate = False
        blocked_machine = StateMachine(
            State("blocked-source"), logger_name=f"{blocked_name}.machine"
        )
        blocked_machine.add_state(State("blocked-destination"))
        blocked_machine.add_transition(
            "advance", "blocked-source", "blocked-destination"
        )

        assert blocked_machine.trigger("advance").success
        assert redactor_calls == 1
    finally:
        logging.getLogger(blocked_name).setLevel(logging.NOTSET)
        logging.getLogger(blocked_name).propagate = True
        handle.restore()
        parent.removeHandler(application_handler)
        application_handler.close()


@pytest.mark.parametrize(
    "redactor",
    (
        lambda _event: (_ for _ in ()).throw(ValueError(EXCEPTION_SENTINEL)),
        lambda _event: {"unsafe": POSITIONAL_SENTINEL, "nested": object()},
        lambda _event: [],
        lambda _event: {"detail": object()},
        lambda _event: {"detail": "x" * 201},
    ),
    ids=("raising", "unknown-key", "non-mapping", "nested-value", "long-string"),
)
def test_redactor_failure_is_fixed_category_or_suppression_without_raw_fallback(
    capsys: pytest.CaptureFixture[str], redactor: object
) -> None:
    """A broken redactor never causes raw values to re-enter records or handlers."""

    logger_name = _logger_name("redactor-failure")
    logger = logging.getLogger(logger_name)
    application_handler = CaptureHandler()
    logger.addHandler(application_handler)
    try:
        handle = configure_fsm_logging(
            TRACE_LEVEL,
            logger_name,
            propagate=False,
            redactor=redactor,
        )
        hostile_payload = HostileRepr()
        _sync_trace_machine(logger_name, hostile_payload)
        assert hostile_payload.repr_calls == 0
        stderr = capsys.readouterr().err
        assert all(secret not in stderr for secret in RAW_SENTINELS)
        for message, args, record_dict, formatted in application_handler.records:
            assert hostile_payload not in args
            assert hostile_payload not in record_dict.values()
            assert (
                record_dict.get("trace_operation") == "redaction_failure"
                or not application_handler.records
            )
        handle.restore()
    finally:
        logger.removeHandler(application_handler)
        application_handler.close()


def test_trace_keyword_names_are_bounded_before_records_are_emitted() -> None:
    """Trace records retain at most fifty safe keyword labels, never their values."""
    logger_name = _logger_name("keyword-bound")
    logger = logging.getLogger(logger_name)
    application_handler = CaptureHandler()
    logger.addHandler(application_handler)
    try:
        handle = configure_fsm_logging(
            TRACE_LEVEL, logger_name, propagate=False, redactor=None
        )
        machine = StateMachine(State("source"), logger_name=logger_name)
        machine.add_state(State("destination"))
        machine.add_transition("go", "source", "destination")
        keyword_args = {f"field_{index}": index for index in range(51)}
        keyword_args["_private"] = "ignored"
        keyword_args["x" * 101] = "ignored"

        assert machine.trigger("go", **keyword_args).success
        names = [
            record[2]["trace_keyword_names"]
            for record in application_handler.records
            if "trace_keyword_names" in record[2]
        ]
        assert any(len(entry) == 50 for entry in names)
        assert all("_private" not in entry for entry in names)
        assert all("x" * 101 not in entry for entry in names)
        handle.restore()
    finally:
        logger.removeHandler(application_handler)
        application_handler.close()


def test_application_handlers_survive_configuration_and_generation_safe_restore() -> (
    None
):
    """Only a marked library handler may change; old restores cannot win races."""

    logger_name = _logger_name("ownership")
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.ERROR)
    logger.propagate = True
    first_handler = CloseTrackingHandler()
    second_handler = CloseTrackingHandler()
    first_filter = ApplicationFilter()
    first_handler.setLevel(logging.CRITICAL)
    first_handler.addFilter(first_filter)
    first_handler.setFormatter(logging.Formatter("application:%(message)s"))
    logger.addHandler(first_handler)
    logger.addHandler(second_handler)
    original_handlers = (first_handler, second_handler)
    original_level = logger.level
    original_propagation = logger.propagate
    try:
        first = configure_fsm_logging(logging.INFO, logger_name)
        assert tuple(logger.handlers[:2]) == original_handlers
        assert first_handler.level == logging.CRITICAL
        assert first_handler.filters == [first_filter]
        assert first_handler.formatter._fmt == "application:%(message)s"
        assert first_handler.close_calls == 0
        assert logger.propagate is original_propagation

        second = configure_fsm_logging(logging.DEBUG, logger_name, propagate=False)
        assert tuple(logger.handlers[:2]) == original_handlers
        assert len(logger.handlers) == len(original_handlers) + 1
        assert first_handler.close_calls == 0
        assert second_handler.close_calls == 0
        assert logger.propagate is False

        first.restore()
        assert logger.level == logging.DEBUG
        assert logger.propagate is False

        second.restore()
        assert tuple(logger.handlers) == original_handlers
        assert logger.level == original_level
        assert logger.propagate is original_propagation
        second.restore()
        assert tuple(logger.handlers) == original_handlers
        assert first_handler.close_calls == 0
        assert second_handler.close_calls == 0
    finally:
        logger.removeHandler(first_handler)
        logger.removeHandler(second_handler)
        first_handler.close()
        second_handler.close()


def test_level_setter_delegates_to_the_reversible_ownership_seam() -> None:
    """The shorthand setter must return the same restore-capable configuration handle."""

    logger_name = _logger_name("setter")
    logger = logging.getLogger(logger_name)
    application_handler = CaptureHandler()
    logger.addHandler(application_handler)
    try:
        handle = set_fsm_logging_level("trace", logger_name)
        assert logger.level == TRACE_LEVEL
        assert logger.handlers[0] is application_handler
        handle.restore()
        assert logger.handlers == [application_handler]
    finally:
        logger.removeHandler(application_handler)
        application_handler.close()


def test_restore_does_not_overwrite_application_changes_after_configuration() -> None:
    """Compare-before-restore leaves application changes authoritative."""

    logger_name = _logger_name("application-change")
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.ERROR)
    logger.propagate = True
    handle = configure_fsm_logging(logging.INFO, logger_name, propagate=False)
    try:
        logger.setLevel(logging.CRITICAL)
        logger.propagate = True
        handle.restore()
        assert logger.level == logging.CRITICAL
        assert logger.propagate is True
        assert not logger.handlers
    finally:
        handle.restore()


# ---------------------------------------------------------------------------
# set_fsm_logging_level
# ---------------------------------------------------------------------------


class TestSetFsmLoggingLevel:
    def test_off(self):
        set_fsm_logging_level("off", "fast_fsm.test_lvl_1")
        logger = logging.getLogger("fast_fsm.test_lvl_1")
        assert logger.level == logging.WARNING

    def test_warning(self):
        set_fsm_logging_level("warning", "fast_fsm.test_lvl_2")
        logger = logging.getLogger("fast_fsm.test_lvl_2")
        assert logger.level == logging.WARNING

    def test_debug(self):
        set_fsm_logging_level("debug", "fast_fsm.test_lvl_3")
        logger = logging.getLogger("fast_fsm.test_lvl_3")
        assert logger.level == logging.DEBUG

    def test_info(self):
        set_fsm_logging_level("info", "fast_fsm.test_lvl_5")
        logger = logging.getLogger("fast_fsm.test_lvl_5")
        assert logger.level == logging.INFO

    def test_trace(self):
        set_fsm_logging_level("trace", "fast_fsm.test_lvl_4")
        logger = logging.getLogger("fast_fsm.test_lvl_4")
        assert logger.level == logging.DEBUG - 5

    def test_case_insensitive(self):
        set_fsm_logging_level("DEBUG", "fast_fsm.test_lvl_6")
        logger = logging.getLogger("fast_fsm.test_lvl_6")
        assert logger.level == logging.DEBUG

    def test_invalid_verbosity_raises(self):
        with pytest.raises(ValueError, match="Invalid verbosity"):
            set_fsm_logging_level("extreme")

    def test_debug_emits_transition_logs(self, caplog):
        """'debug' level shows transitions in a real FSM."""
        set_fsm_logging_level("debug", "fast_fsm.log_test_2")
        fsm = StateMachine(
            State("idle"), name="log_test_2", logger_name="fast_fsm.log_test_2"
        )
        fsm.add_state(State("running"))
        fsm.add_transition("start", "idle", "running")

        with caplog.at_level(logging.DEBUG, logger="fast_fsm.log_test_2"):
            fsm.trigger("start")

        assert any("start" in r.message for r in caplog.records)
