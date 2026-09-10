#!/usr/bin/env python3
"""Exhaustive logic audit for the private collision-avoidance prototype.

This is intentionally a standalone prototype tool, not part of the Fast FSM
package test suite.  It checks the application's finite decision model and a
small command-integration scenario without changing the runtime FSM interface.
"""

from contextlib import redirect_stdout
from io import StringIO
from itertools import product

from arducopter_collision_avoidance import (
    COLLISION_TRANSITION_RULES,
    AircraftCommands,
    AlertLevel,
    AvoidanceCommand,
    CollisionDecisionFacts,
    DroneController,
    DroneTelemetry,
    FakeClock,
    FlightMode,
    TelemetryPolicy,
    TransitionEffect,
    active_inhibited,
    avoid_inhibited,
    avoidance_requested,
    base_eligible,
    guided_update_ready,
    select_collision_rule,
    traffic_confirmed_clear,
)


BOOLEAN_FACT_FIELDS = (
    "drone_heartbeat_fresh",
    "collision_heartbeat_fresh",
    "collision_data_fresh",
    "collision_ready_stable",
    "collision_switch_enabled",
    "altitude_within_limits",
    "any_failsafe",
    "landing",
    "on_ground",
    "alert_at_or_above_threshold",
    "command_available",
    "command_is_new",
    "guided_retry_ready",
    "awaiting_guided_confirmation",
    "guided_confirmation_failed",
)


class RecordingAircraft(AircraftCommands):
    """Record structured command calls without producing simulation output."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, int, bool | float]] = []

    def send_do_reposition(
        self,
        command: AvoidanceCommand,
        *,
        change_to_guided: bool,
    ) -> None:
        self.calls.append(("do_reposition", command.sequence, change_to_guided))

    def send_position_target_global_int(
        self,
        command: AvoidanceCommand,
        *,
        down_velocity_m_s: float,
    ) -> None:
        self.calls.append(
            ("position_target_global_int", command.sequence, down_velocity_m_s)
        )


def decision_facts(
    flight_mode: FlightMode,
    values: tuple[bool, ...],
) -> CollisionDecisionFacts:
    return CollisionDecisionFacts(
        flight_mode=flight_mode,
        **dict(zip(BOOLEAN_FACT_FIELDS, values, strict=True)),
    )


def audit_transition_topology() -> None:
    """Check rule metadata used by both the runtime FSM and decision audit."""
    priorities: set[tuple[str, int]] = set()
    for rule in COLLISION_TRANSITION_RULES:
        priority_key = (rule.source, rule.priority)
        assert priority_key not in priorities, f"ambiguous priority: {priority_key}"
        priorities.add(priority_key)

        if rule.effect is TransitionEffect.BEGIN_AVOIDANCE:
            assert (rule.source, rule.destination) == ("Active", "Avoid")
        elif rule.effect is TransitionEffect.UPDATE_AVOIDANCE:
            assert (rule.source, rule.destination) == ("Avoid", "Avoid")
        elif rule.effect is TransitionEffect.FINISH_AVOIDANCE:
            assert (rule.source, rule.destination) == ("Avoid", "Inactive")


def audit_decision_table() -> tuple[int, int]:
    """Exhaustively check all abstract input combinations in every state."""
    fact_rows = 0
    state_decisions = 0
    for mode, values in product(
        FlightMode,
        product((False, True), repeat=len(BOOLEAN_FACT_FIELDS)),
    ):
        facts = decision_facts(mode, values)
        fact_rows += 1

        expected_base_eligible = (
            facts.drone_heartbeat_fresh
            and facts.collision_heartbeat_fresh
            and facts.collision_data_fresh
            and facts.collision_ready_stable
            and facts.collision_switch_enabled
            and facts.altitude_within_limits
            and not facts.any_failsafe
            and not facts.landing
            and not facts.on_ground
        )
        assert base_eligible(facts) is expected_base_eligible

        inactive_rule = select_collision_rule("Inactive", facts)
        active_rule = select_collision_rule("Active", facts)
        avoid_rule = select_collision_rule("Avoid", facts)
        state_decisions += 3

        assert (inactive_rule is not None) == (
            expected_base_eligible and mode is FlightMode.AUTO
        )

        if active_inhibited(facts):
            assert active_rule is not None
            assert active_rule.name == "active_inhibited"
        elif avoidance_requested(facts):
            assert active_rule is not None
            assert active_rule.name == "avoidance_requested"
        else:
            assert active_rule is None

        if avoid_inhibited(facts):
            assert avoid_rule is not None
            assert avoid_rule.name == "avoid_inhibited"
        elif guided_update_ready(facts):
            assert avoid_rule is not None
            assert avoid_rule.name == "guided_update_ready"
        elif traffic_confirmed_clear(facts):
            assert avoid_rule is not None
            assert avoid_rule.name == "traffic_confirmed_clear"
        else:
            assert avoid_rule is None

        if not expected_base_eligible:
            assert inactive_rule is None
            assert active_rule is not None
            assert active_rule.destination == "Inactive"
            assert avoid_rule is not None
            assert avoid_rule.destination == "Inactive"

        for state in ("Inactive", "Active", "Avoid"):
            eligible = [
                rule
                for rule in COLLISION_TRANSITION_RULES
                if rule.source == state and rule.guard(decision_facts=facts)
            ]
            if eligible:
                winning_priority = min(rule.priority for rule in eligible)
                assert sum(rule.priority == winning_priority for rule in eligible) == 1

        for rule in (inactive_rule, active_rule, avoid_rule):
            if rule is None:
                continue
            if rule.effect is TransitionEffect.BEGIN_AVOIDANCE:
                assert facts.flight_mode is FlightMode.AUTO
                assert facts.guided_retry_ready
                assert facts.alert_at_or_above_threshold
                assert facts.command_available and facts.command_is_new
            elif rule.effect is TransitionEffect.UPDATE_AVOIDANCE:
                assert facts.flight_mode is FlightMode.GUIDED
                assert facts.alert_at_or_above_threshold
                assert facts.command_available and facts.command_is_new

    return fact_rows, state_decisions


def healthy_policy(
    clock: FakeClock,
    *,
    guided_request_timeout_s: float = 2.0,
) -> TelemetryPolicy:
    return TelemetryPolicy(
        clock=clock,
        ready_dwell_s=0.0,
        guided_request_timeout_s=guided_request_timeout_s,
    )


def observe_healthy_inputs(
    policy: TelemetryPolicy,
    *,
    mode: FlightMode,
    alert: AlertLevel = AlertLevel.CLEAR,
    command: AvoidanceCommand | None = None,
    low_battery: bool = False,
) -> None:
    policy.observe_drone(
        DroneTelemetry(
            flight_mode=mode,
            altitude_m=30.0,
            collision_switch_enabled=True,
            low_battery=low_battery,
        )
    )
    policy.observe_collision_heartbeat(ready=True)
    policy.observe_collision_status(alert, command)


def command(sequence: int) -> AvoidanceCommand:
    return AvoidanceCommand(
        sequence=sequence,
        target_latitude_deg=38.8895,
        target_longitude_deg=-77.0353,
        target_relative_altitude_m=35.0,
        climb_rate_m_s=0.5,
    )


def audit_command_integration() -> None:
    """Check the command effects selected by representative real FSM ticks."""
    clock = FakeClock()
    policy = healthy_policy(clock)
    aircraft = RecordingAircraft()
    controller = DroneController(aircraft, policy)

    with redirect_stdout(StringIO()):
        observe_healthy_inputs(policy, mode=FlightMode.AUTO)
        assert controller.tick().success
        assert controller.state == "Active"
        assert aircraft.calls == []

        observe_healthy_inputs(
            policy,
            mode=FlightMode.AUTO,
            alert=AlertLevel.AVOID,
            command=command(1),
        )
        assert controller.tick().success
        assert controller.state == "Avoid"
        assert aircraft.calls == [("do_reposition", 1, True)]

        policy.observe_guided_ack(accepted=True)
        observe_healthy_inputs(
            policy,
            mode=FlightMode.GUIDED,
            alert=AlertLevel.CRITICAL,
            command=command(2),
        )
        assert controller.tick().success
        assert controller.state == "Avoid"
        assert aircraft.calls[-1] == ("position_target_global_int", 2, -0.5)

        calls_before_safety_exit = list(aircraft.calls)
        observe_healthy_inputs(
            policy,
            mode=FlightMode.GUIDED,
            alert=AlertLevel.CRITICAL,
            command=command(3),
            low_battery=True,
        )
        assert controller.tick().success
        assert controller.state == "Inactive"
        assert aircraft.calls == calls_before_safety_exit

    assert all(call[0] != "auto" for call in aircraft.calls)


def audit_time_boundaries() -> None:
    """Check inclusive/exclusive timing and altitude edges behind decision facts."""
    clock = FakeClock()
    policy = TelemetryPolicy(clock=clock)
    observe_healthy_inputs(policy, mode=FlightMode.AUTO)
    assert not policy.decision_facts().collision_ready_stable

    clock.advance(1.0)
    assert policy.decision_facts().collision_ready_stable
    assert policy.decision_facts().collision_data_fresh
    assert policy.decision_facts().drone_heartbeat_fresh

    clock.advance(0.000_001)
    assert not policy.decision_facts().collision_data_fresh
    clock.advance(0.999_999)
    assert policy.decision_facts().drone_heartbeat_fresh
    clock.advance(0.000_001)
    assert not policy.decision_facts().drone_heartbeat_fresh

    for altitude, expected in (
        (5.0, True),
        (120.0, True),
        (4.999, False),
        (120.001, False),
    ):
        edge_policy = healthy_policy(FakeClock())
        edge_policy.observe_drone(
            DroneTelemetry(FlightMode.AUTO, altitude, collision_switch_enabled=True)
        )
        edge_policy.observe_collision_heartbeat(ready=True)
        edge_policy.observe_collision_status(AlertLevel.CLEAR, None)
        assert edge_policy.decision_facts().altitude_within_limits is expected

    guided_clock = FakeClock()
    guided_policy = healthy_policy(guided_clock, guided_request_timeout_s=2.0)
    observe_healthy_inputs(
        guided_policy,
        mode=FlightMode.AUTO,
        alert=AlertLevel.AVOID,
        command=command(10),
    )
    guided_policy.note_initial_command_dispatched()
    guided_clock.advance(2.0)
    assert guided_policy.decision_facts().awaiting_guided_confirmation
    assert not guided_policy.decision_facts().guided_confirmation_failed
    guided_clock.advance(0.000_001)
    assert not guided_policy.decision_facts().awaiting_guided_confirmation
    assert guided_policy.decision_facts().guided_confirmation_failed


def main() -> None:
    audit_transition_topology()
    fact_rows, state_decisions = audit_decision_table()
    audit_command_integration()
    audit_time_boundaries()
    print("Collision-avoidance logic audit: PASS")
    print(f"Abstract fact rows: {fact_rows:,}")
    print(f"State decisions checked: {state_decisions:,}")
    print("Command integration and time-boundary invariants: PASS")


if __name__ == "__main__":
    main()
