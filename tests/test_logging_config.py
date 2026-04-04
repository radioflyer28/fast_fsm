"""
Tests for configure_fsm_logging and set_fsm_logging_level.

All tests use real logging infrastructure — no mocking.
"""

import logging

import pytest

from fast_fsm.core import (
    State,
    StateMachine,
    configure_fsm_logging,
    set_fsm_logging_level,
)


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

    def test_warning_level_removes_handler(self):
        # First add a handler
        configure_fsm_logging(logging.INFO, "fast_fsm.test_cfg_3")
        # Now switch to WARNING — should clear handlers
        configure_fsm_logging(logging.WARNING, "fast_fsm.test_cfg_3")
        logger = logging.getLogger("fast_fsm.test_cfg_3")
        assert logger.handlers == []

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
