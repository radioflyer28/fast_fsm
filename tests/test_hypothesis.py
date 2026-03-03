"""
Hypothesis property-based tests for core FSM invariants.

These tests verify structural invariants that must hold for ANY valid FSM
regardless of shape (states, transitions, triggers). Using Hypothesis to
generate random FSM topologies and random trigger sequences.

All tests use real FSM components — no mocking.
"""

import string

from hypothesis import given, settings, assume, HealthCheck
from hypothesis import strategies as st

from fast_fsm.core import State, StateMachine, TransitionResult


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# State names: 1-20 chars, printable, no empty
state_name = st.text(
    alphabet=string.ascii_lowercase + string.digits + "_",
    min_size=1,
    max_size=12,
)

# A unique list of state names (at least 2, at most 8)
state_names = st.lists(state_name, min_size=2, max_size=8, unique=True)


def build_fsm(names: list[str], transitions: list[tuple[str, str, str]]):
    """Helper: build a StateMachine from names + transitions."""
    fsm = StateMachine(State(names[0]), name="hypo")
    for n in names[1:]:
        fsm.add_state(State(n))
    for trigger, src, dst in transitions:
        fsm.add_transition(trigger, src, dst)
    return fsm


@st.composite
def fsm_with_transitions(draw):
    """Strategy that produces (fsm, list_of_transitions)."""
    names = draw(state_names)
    # Generate some random transitions between existing states
    n_trans = draw(st.integers(min_value=1, max_value=len(names) * 2))
    trigger_name = st.text(alphabet=string.ascii_lowercase, min_size=1, max_size=6)
    transitions = []
    for _ in range(n_trans):
        t = draw(trigger_name)
        src = draw(st.sampled_from(names))
        dst = draw(st.sampled_from(names))
        transitions.append((t, src, dst))
    fsm = build_fsm(names, transitions)
    return fsm, transitions


# ---------------------------------------------------------------------------
# Invariant tests
# ---------------------------------------------------------------------------


class TestCurrentStateInvariant:
    """current_state is always one of the defined states."""

    @given(data=fsm_with_transitions())
    @settings(max_examples=80, suppress_health_check=[HealthCheck.too_slow])
    def test_current_state_always_valid(self, data):
        fsm, transitions = data
        valid_states = set(fsm.states)
        assert fsm.current_state.name in valid_states

        all_triggers = [t for t, _, _ in transitions]
        for trigger in all_triggers:
            fsm.trigger(trigger)
            assert fsm.current_state.name in valid_states


class TestTriggerReturnType:
    """trigger() always returns a TransitionResult."""

    @given(data=fsm_with_transitions())
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_trigger_always_returns_result(self, data):
        fsm, transitions = data
        all_triggers = list({t for t, _, _ in transitions})
        # Also try a completely bogus trigger
        for trig in all_triggers + ["__nonexistent__"]:
            result = fsm.trigger(trig)
            assert isinstance(result, TransitionResult)
            assert isinstance(result.success, bool)


class TestIdempotentFailedTransition:
    """A failed trigger must NOT change current_state."""

    @given(data=fsm_with_transitions())
    @settings(max_examples=80, suppress_health_check=[HealthCheck.too_slow])
    def test_failed_trigger_preserves_state(self, data):
        fsm, _ = data
        before = fsm.current_state.name
        result = fsm.trigger("__definitely_nonexistent__")
        assert not result.success
        assert fsm.current_state.name == before


class TestCanTriggerConsistency:
    """can_trigger() agrees with trigger() on success/failure."""

    @given(data=fsm_with_transitions())
    @settings(max_examples=80, suppress_health_check=[HealthCheck.too_slow])
    def test_can_trigger_predicts_trigger(self, data):
        fsm, transitions = data
        for trig, _, _ in transitions:
            can = fsm.can_trigger(trig)
            before = fsm.current_state.name
            result = fsm.trigger(trig)
            if can:
                # If can_trigger said yes, trigger should succeed
                # (assuming no conditions change state mid-check).
                assert result.success, (
                    f"can_trigger('{trig}') was True but trigger() failed "
                    f"from state '{before}': {result.error}"
                )
            # Reset state for next iteration to keep test predictable
            fsm._current_state = fsm._states[before]


class TestDeterministicTransition:
    """Same state + same trigger = same outcome (deterministic)."""

    @given(data=fsm_with_transitions())
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_trigger_is_deterministic(self, data):
        fsm, transitions = data
        for trig, _, _ in transitions:
            state_before = fsm.current_state.name
            r1 = fsm.trigger(trig)
            after1 = fsm.current_state.name
            # Reset
            fsm._current_state = fsm._states[state_before]
            r2 = fsm.trigger(trig)
            after2 = fsm.current_state.name
            assert r1.success == r2.success
            assert after1 == after2


class TestFromStatesRoundTrip:
    """from_states creates an FSM with exactly those states."""

    @given(names=state_names)
    @settings(max_examples=50)
    def test_from_states_has_all_states(self, names):
        fsm = StateMachine.from_states(*names)
        assert set(fsm.states) == set(names)
        assert fsm.current_state.name == names[0]


class TestQuickBuildRoundTrip:
    """quick_build includes initial + all states from transitions."""

    @given(names=state_names)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_quick_build_covers_states(self, names):
        assume(len(names) >= 2)
        initial = names[0]
        transitions = [
            (f"t{i}", names[i], names[(i + 1) % len(names)]) for i in range(len(names))
        ]
        fsm = StateMachine.quick_build(initial, transitions)
        assert fsm.current_state.name == initial
        # Every state mentioned in transitions should exist
        for _, src, dst in transitions:
            assert src in fsm.states
            assert dst in fsm.states


class TestStatesPropertyNeverEmpty:
    """An FSM always has at least one state."""

    @given(data=fsm_with_transitions())
    @settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow])
    def test_states_nonempty(self, data):
        fsm, _ = data
        assert len(fsm.states) >= 1
