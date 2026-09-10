#!/usr/bin/env python3
"""Private ArduCopter collision-avoidance FSM prototype.

This intentionally lives outside ``examples/``: it is an application sketch, not
part of Fast FSM's documented or tested example suite.  It simulates commands and
telemetry only; it is not flight-control software.
"""

from dataclasses import dataclass
from enum import Enum, IntEnum
from math import hypot
from time import monotonic
from typing import Callable, Protocol

from fast_fsm import FSMBuilder, FuncCondition, State, TransitionResult


class FlightMode(str, Enum):
    """Normalized ArduCopter flight modes used by this controller."""

    AUTO = "AUTO"
    GUIDED = "GUIDED"
    LAND = "LAND"
    RTL = "RTL"
    OTHER = "OTHER"


class AlertLevel(IntEnum):
    """Ordered collision-system alert levels."""

    CLEAR = 0
    ADVISORY = 1
    AVOID = 2
    CRITICAL = 3


class CommandAck(str, Enum):
    """Observed acknowledgment for the initial Guided reposition command."""

    NONE = "none"
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


@dataclass(frozen=True)
class DroneTelemetry:
    """One immutable, normalized aircraft telemetry snapshot."""

    flight_mode: FlightMode
    altitude_m: float
    collision_switch_enabled: bool
    critical_battery: bool = False
    low_battery: bool = False
    lost_link: bool = False
    landing: bool = False
    on_ground: bool = False


@dataclass(frozen=True)
class AvoidanceCommand:
    """One collision-system command in controller-friendly units.

    Positive climb rate means up.  The Guided adapter translates it to MAVLink's
    NED convention, where positive Z velocity means down.
    """

    sequence: int
    target_latitude_deg: float
    target_longitude_deg: float
    target_relative_altitude_m: float
    north_velocity_m_s: float = 0.0
    east_velocity_m_s: float = 0.0
    climb_rate_m_s: float = 0.0
    heading_deg: float | None = None


@dataclass(frozen=True)
class CollisionDecisionFacts:
    """Immutable facts consumed by every transition guard for one control tick.

    ``TelemetryPolicy`` owns measurements and temporal state.  This snapshot is
    deliberately free of transition decisions so the same pure guard functions
    can be exercised exhaustively without constructing telemetry histories.
    """

    flight_mode: FlightMode
    drone_heartbeat_fresh: bool
    collision_heartbeat_fresh: bool
    collision_data_fresh: bool
    collision_ready_stable: bool
    collision_switch_enabled: bool
    altitude_within_limits: bool
    any_failsafe: bool
    landing: bool
    on_ground: bool
    alert_at_or_above_threshold: bool
    command_available: bool
    command_is_new: bool
    guided_retry_ready: bool
    awaiting_guided_confirmation: bool
    guided_confirmation_failed: bool


class AircraftCommands(Protocol):
    """Seam implemented by a simulated aircraft or real MAVLink adapter."""

    def send_do_reposition(
        self,
        command: AvoidanceCommand,
        *,
        change_to_guided: bool,
    ) -> None: ...

    def send_position_target_global_int(
        self,
        command: AvoidanceCommand,
        *,
        down_velocity_m_s: float,
    ) -> None: ...


class SimulatedAircraft:
    """Record the ArduCopter-facing calls made by the command handler."""

    __slots__ = ("commands",)

    def __init__(self) -> None:
        self.commands: list[str] = []

    def send_do_reposition(
        self,
        command: AvoidanceCommand,
        *,
        change_to_guided: bool,
    ) -> None:
        flags = "CHANGE_MODE" if change_to_guided else "NONE"
        record = (
            "MAV_CMD_DO_REPOSITION("
            f"seq={command.sequence}, flags={flags}, "
            f"lat={command.target_latitude_deg:.6f}, "
            f"lon={command.target_longitude_deg:.6f}, "
            f"alt={command.target_relative_altitude_m:.1f}m)"
        )
        self.commands.append(record)
        print(f"  aircraft.{record}")

    def send_position_target_global_int(
        self,
        command: AvoidanceCommand,
        *,
        down_velocity_m_s: float,
    ) -> None:
        horizontal_speed = hypot(
            command.north_velocity_m_s,
            command.east_velocity_m_s,
        )
        heading = "current" if command.heading_deg is None else command.heading_deg
        record = (
            "SET_POSITION_TARGET_GLOBAL_INT("
            f"seq={command.sequence}, horizontal={horizontal_speed:.1f}m/s, "
            f"down={down_velocity_m_s:.1f}m/s, "
            f"alt={command.target_relative_altitude_m:.1f}m, "
            f"heading={heading})"
        )
        self.commands.append(record)
        print(f"  aircraft.{record}")


class GuidedCommandHandler:
    """Translate normalized collision commands into ArduCopter Guided calls."""

    __slots__ = ("_aircraft",)

    def __init__(self, aircraft: AircraftCommands) -> None:
        self._aircraft = aircraft

    def begin_avoidance(self, command: AvoidanceCommand) -> None:
        """Atomically request Guided and install the first position target."""
        self._aircraft.send_do_reposition(command, change_to_guided=True)

    def update_avoidance(self, command: AvoidanceCommand) -> None:
        """Translate later velocity, altitude, and heading updates in Guided."""
        self._aircraft.send_position_target_global_int(
            command,
            down_velocity_m_s=-command.climb_rate_m_s,
        )


class FakeClock:
    """Deterministic monotonic clock for the simulation."""

    __slots__ = ("now",)

    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class TelemetryPolicy:
    """Retain input facts and derive freshness and timing measurements.

    This module never selects events, transitions, states, or commands.  Fast FSM
    guards own those rules.
    """

    __slots__ = (
        "_alert_level",
        "_clock",
        "_collision_data_timeout_s",
        "_collision_heartbeat_timeout_s",
        "_collision_ready",
        "_collision_ready_since",
        "_command",
        "_drone",
        "_drone_heartbeat_timeout_s",
        "_guided_confirmed",
        "_guided_request_ack",
        "_guided_request_started_at",
        "_guided_request_timeout_s",
        "_last_collision_data_at",
        "_last_collision_heartbeat_at",
        "_last_dispatched_sequence",
        "_last_drone_heartbeat_at",
        "_last_guided_failure_at",
        "_max_altitude_m",
        "_min_altitude_m",
        "_ready_dwell_s",
        "_retry_cooldown_s",
        "_threshold",
    )

    def __init__(
        self,
        *,
        clock: Callable[[], float] = monotonic,
        drone_heartbeat_timeout_s: float = 2.0,
        collision_heartbeat_timeout_s: float = 2.0,
        collision_data_timeout_s: float = 1.0,
        ready_dwell_s: float = 1.0,
        guided_request_timeout_s: float = 2.0,
        retry_cooldown_s: float = 3.0,
        min_altitude_m: float = 5.0,
        max_altitude_m: float = 120.0,
        threshold: AlertLevel = AlertLevel.AVOID,
    ) -> None:
        self._clock = clock
        self._drone_heartbeat_timeout_s = drone_heartbeat_timeout_s
        self._collision_heartbeat_timeout_s = collision_heartbeat_timeout_s
        self._collision_data_timeout_s = collision_data_timeout_s
        self._ready_dwell_s = ready_dwell_s
        self._guided_request_timeout_s = guided_request_timeout_s
        self._retry_cooldown_s = retry_cooldown_s
        self._min_altitude_m = min_altitude_m
        self._max_altitude_m = max_altitude_m
        self._threshold = threshold
        self._drone: DroneTelemetry | None = None
        self._last_drone_heartbeat_at: float | None = None
        self._last_collision_heartbeat_at: float | None = None
        self._collision_ready = False
        self._collision_ready_since: float | None = None
        self._last_collision_data_at: float | None = None
        self._alert_level = AlertLevel.CLEAR
        self._command: AvoidanceCommand | None = None
        self._last_dispatched_sequence: int | None = None
        self._guided_request_started_at: float | None = None
        self._guided_request_ack = CommandAck.NONE
        self._guided_confirmed = False
        self._last_guided_failure_at: float | None = None

    def observe_drone(self, telemetry: DroneTelemetry) -> None:
        """Record one aircraft heartbeat and its normalized telemetry facts."""
        self._drone = telemetry
        self._last_drone_heartbeat_at = self._clock()
        if (
            self._guided_request_started_at is not None
            and telemetry.flight_mode is FlightMode.GUIDED
        ):
            self._guided_confirmed = True

    def observe_collision_heartbeat(self, *, ready: bool) -> None:
        """Record collision-system liveness separately from collision data."""
        now = self._clock()
        heartbeat_was_fresh = self.collision_heartbeat_fresh()
        self._last_collision_heartbeat_at = now
        if ready and (not self._collision_ready or not heartbeat_was_fresh):
            self._collision_ready_since = now
        elif not ready:
            self._collision_ready_since = None
        self._collision_ready = ready

    def observe_collision_status(
        self,
        alert_level: AlertLevel,
        command: AvoidanceCommand | None,
    ) -> None:
        """Record a fresh alert status; absence of a command is not a heartbeat."""
        self._last_collision_data_at = self._clock()
        self._alert_level = alert_level
        self._command = command

    def observe_guided_ack(self, *, accepted: bool) -> None:
        """Record the COMMAND_ACK for the initial DO_REPOSITION request."""
        self._guided_request_ack = (
            CommandAck.ACCEPTED if accepted else CommandAck.REJECTED
        )

    @property
    def drone(self) -> DroneTelemetry:
        if self._drone is None:
            raise RuntimeError("no drone telemetry has been observed")
        return self._drone

    @property
    def command(self) -> AvoidanceCommand:
        if self._command is None:
            raise RuntimeError("no collision command is available")
        return self._command

    def drone_heartbeat_fresh(self) -> bool:
        return self._age_within(
            self._last_drone_heartbeat_at,
            self._drone_heartbeat_timeout_s,
        )

    def collision_heartbeat_fresh(self) -> bool:
        return self._age_within(
            self._last_collision_heartbeat_at,
            self._collision_heartbeat_timeout_s,
        )

    def collision_data_fresh(self) -> bool:
        return self._age_within(
            self._last_collision_data_at,
            self._collision_data_timeout_s,
        )

    def collision_ready_stable(self) -> bool:
        return (
            self._collision_ready
            and self._collision_ready_since is not None
            and self._clock() - self._collision_ready_since >= self._ready_dwell_s
        )

    def altitude_within_limits(self) -> bool:
        return self._min_altitude_m <= self.drone.altitude_m <= self._max_altitude_m

    def any_failsafe(self) -> bool:
        telemetry = self.drone
        return (
            telemetry.critical_battery or telemetry.low_battery or telemetry.lost_link
        )

    def command_is_new(self) -> bool:
        return (
            self._command is not None
            and self._command.sequence != self._last_dispatched_sequence
        )

    def guided_retry_ready(self) -> bool:
        return (
            self._last_guided_failure_at is None
            or self._clock() - self._last_guided_failure_at >= self._retry_cooldown_s
        )

    def awaiting_guided_confirmation(self) -> bool:
        return (
            self._guided_request_started_at is not None
            and not self._guided_confirmed
            and self._guided_request_ack is not CommandAck.REJECTED
            and self._clock() - self._guided_request_started_at
            <= self._guided_request_timeout_s
        )

    def guided_confirmation_failed(self) -> bool:
        if self._guided_request_ack is CommandAck.REJECTED:
            return True
        return (
            self._guided_request_started_at is not None
            and not self._guided_confirmed
            and self._clock() - self._guided_request_started_at
            > self._guided_request_timeout_s
        )

    def decision_facts(self) -> CollisionDecisionFacts:
        """Freeze all guard inputs once for a consistent control-tick decision."""
        telemetry = self._drone
        flight_mode = FlightMode.OTHER if telemetry is None else telemetry.flight_mode
        return CollisionDecisionFacts(
            flight_mode=flight_mode,
            drone_heartbeat_fresh=self.drone_heartbeat_fresh(),
            collision_heartbeat_fresh=self.collision_heartbeat_fresh(),
            collision_data_fresh=self.collision_data_fresh(),
            collision_ready_stable=self.collision_ready_stable(),
            collision_switch_enabled=(
                False if telemetry is None else telemetry.collision_switch_enabled
            ),
            altitude_within_limits=(
                False if telemetry is None else self.altitude_within_limits()
            ),
            any_failsafe=False if telemetry is None else self.any_failsafe(),
            landing=False if telemetry is None else telemetry.landing,
            on_ground=False if telemetry is None else telemetry.on_ground,
            alert_at_or_above_threshold=self._alert_level >= self._threshold,
            command_available=self._command is not None,
            command_is_new=self.command_is_new(),
            guided_retry_ready=self.guided_retry_ready(),
            awaiting_guided_confirmation=self.awaiting_guided_confirmation(),
            guided_confirmation_failed=self.guided_confirmation_failed(),
        )

    def note_initial_command_dispatched(self) -> None:
        self._guided_request_started_at = self._clock()
        self._guided_request_ack = CommandAck.PENDING
        self._guided_confirmed = False
        self._last_dispatched_sequence = self.command.sequence

    def note_update_dispatched(self) -> None:
        self._last_dispatched_sequence = self.command.sequence

    def note_avoidance_exit(self) -> None:
        if self.guided_confirmation_failed():
            self._last_guided_failure_at = self._clock()
        self._guided_request_started_at = None
        self._guided_request_ack = CommandAck.NONE
        self._guided_confirmed = False
        # A pilot AUTO selection during an active alert intentionally permits the
        # still-current command to re-engage after the FSM returns through Active.
        self._last_dispatched_sequence = None

    def _age_within(self, timestamp: float | None, limit_s: float) -> bool:
        return timestamp is not None and self._clock() - timestamp <= limit_s


def base_eligible(facts: CollisionDecisionFacts) -> bool:
    """Return whether common liveness and safety prerequisites hold."""
    return (
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


def activation_ready(decision_facts: CollisionDecisionFacts, **_) -> bool:
    return base_eligible(decision_facts) and (
        decision_facts.flight_mode is FlightMode.AUTO
    )


def active_inhibited(decision_facts: CollisionDecisionFacts, **_) -> bool:
    return not activation_ready(decision_facts)


def avoidance_requested(decision_facts: CollisionDecisionFacts, **_) -> bool:
    return (
        activation_ready(decision_facts)
        and decision_facts.guided_retry_ready
        and decision_facts.alert_at_or_above_threshold
        and decision_facts.command_available
        and decision_facts.command_is_new
    )


def avoid_inhibited(decision_facts: CollisionDecisionFacts, **_) -> bool:
    if not base_eligible(decision_facts):
        return True
    if decision_facts.guided_confirmation_failed:
        return True
    mode = decision_facts.flight_mode
    return mode is not FlightMode.GUIDED and not (
        mode is FlightMode.AUTO and decision_facts.awaiting_guided_confirmation
    )


def guided_update_ready(decision_facts: CollisionDecisionFacts, **_) -> bool:
    return (
        base_eligible(decision_facts)
        and decision_facts.flight_mode is FlightMode.GUIDED
        and decision_facts.alert_at_or_above_threshold
        and decision_facts.command_available
        and decision_facts.command_is_new
    )


def traffic_confirmed_clear(decision_facts: CollisionDecisionFacts, **_) -> bool:
    return (
        decision_facts.collision_heartbeat_fresh
        and decision_facts.collision_data_fresh
        and decision_facts.collision_ready_stable
        and not decision_facts.alert_at_or_above_threshold
    )


class TransitionEffect(str, Enum):
    """Externally relevant effect associated with a selected transition."""

    NONE = "none"
    BEGIN_AVOIDANCE = "begin_avoidance"
    UPDATE_AVOIDANCE = "update_avoidance"
    FINISH_AVOIDANCE = "finish_avoidance"


@dataclass(frozen=True)
class CollisionTransitionRule:
    """One auditable transition candidate and its externally relevant effect."""

    source: str
    destination: str
    priority: int
    name: str
    guard: Callable[..., bool]
    effect: TransitionEffect = TransitionEffect.NONE


COLLISION_TRANSITION_RULES = (
    CollisionTransitionRule(
        "Inactive", "Active", 10, "activation_ready", activation_ready
    ),
    CollisionTransitionRule(
        "Active", "Inactive", 0, "active_inhibited", active_inhibited
    ),
    CollisionTransitionRule(
        "Active",
        "Avoid",
        10,
        "avoidance_requested",
        avoidance_requested,
        TransitionEffect.BEGIN_AVOIDANCE,
    ),
    CollisionTransitionRule(
        "Avoid",
        "Inactive",
        0,
        "avoid_inhibited",
        avoid_inhibited,
        TransitionEffect.FINISH_AVOIDANCE,
    ),
    CollisionTransitionRule(
        "Avoid",
        "Avoid",
        10,
        "guided_update_ready",
        guided_update_ready,
        TransitionEffect.UPDATE_AVOIDANCE,
    ),
    CollisionTransitionRule(
        "Avoid",
        "Inactive",
        20,
        "traffic_confirmed_clear",
        traffic_confirmed_clear,
        TransitionEffect.FINISH_AVOIDANCE,
    ),
)


def select_collision_rule(
    state: str,
    decision_facts: CollisionDecisionFacts,
) -> CollisionTransitionRule | None:
    """Resolve the same ordered candidate set without executing callbacks."""
    eligible = (
        rule
        for rule in COLLISION_TRANSITION_RULES
        if rule.source == state and rule.guard(decision_facts=decision_facts)
    )
    return min(eligible, key=lambda rule: rule.priority, default=None)


def report_state_entry(state_name: str) -> Callable[..., None]:
    def report(from_state: State | None, trigger: str, **_) -> None:
        source = from_state.name if from_state is not None else "start"
        print(f"  state: {source} --{trigger}--> {state_name}")

    return report


def create_collision_fsm(handler: GuidedCommandHandler):
    """Build the complete collision-avoidance transition topology."""
    inactive = State("Inactive")
    active = State("Active")
    avoid = State("Avoid")

    builder = FSMBuilder(inactive, name="ArduCopterCollisionAvoidance")
    builder.add_state(active).add_state(avoid)
    for rule in COLLISION_TRANSITION_RULES:
        builder.add_transition(
            "control_tick",
            rule.source,
            rule.destination,
            condition=FuncCondition(rule.guard, name=rule.name),
            priority=rule.priority,
        )

    for state_name in ("Inactive", "Active", "Avoid"):
        builder.on_enter(state_name, report_state_entry(state_name))

    def issue_avoidance_command(
        from_state: State | None,
        _trigger: str,
        *,
        telemetry_policy: TelemetryPolicy,
        **_,
    ) -> None:
        if from_state is None:
            return
        effect = next(
            rule.effect
            for rule in COLLISION_TRANSITION_RULES
            if rule.source == from_state.name and rule.destination == "Avoid"
        )
        if effect is TransitionEffect.BEGIN_AVOIDANCE:
            telemetry_policy.note_initial_command_dispatched()
            try:
                handler.begin_avoidance(telemetry_policy.command)
            except BaseException:
                telemetry_policy.observe_guided_ack(accepted=False)
                raise
        elif effect is TransitionEffect.UPDATE_AVOIDANCE:
            handler.update_avoidance(telemetry_policy.command)
            telemetry_policy.note_update_dispatched()

    def finish_avoidance(
        from_state: State | None,
        _trigger: str,
        *,
        telemetry_policy: TelemetryPolicy,
        **_,
    ) -> None:
        if from_state is not None and from_state.name == "Avoid":
            # Deliberately issue no neutral target and no AUTO command.  The last
            # accepted Guided target remains under ArduCopter's normal semantics.
            telemetry_policy.note_avoidance_exit()

    builder.on_enter("Avoid", issue_avoidance_command)
    builder.on_enter("Inactive", finish_avoidance)
    return builder.build()


class DroneController:
    """Own input facts, the FSM, and the Guided command adapter."""

    __slots__ = ("_fsm", "_policy")

    def __init__(
        self,
        aircraft: AircraftCommands,
        policy: TelemetryPolicy | None = None,
    ) -> None:
        self._policy = TelemetryPolicy() if policy is None else policy
        self._fsm = create_collision_fsm(GuidedCommandHandler(aircraft))

    @property
    def state(self) -> str:
        return self._fsm.current_state_name

    def observe_drone(self, telemetry: DroneTelemetry) -> None:
        self._policy.observe_drone(telemetry)

    def observe_collision_heartbeat(self, *, ready: bool) -> None:
        self._policy.observe_collision_heartbeat(ready=ready)

    def observe_collision_status(
        self,
        alert_level: AlertLevel,
        command: AvoidanceCommand | None = None,
    ) -> None:
        self._policy.observe_collision_status(alert_level, command)

    def observe_guided_ack(self, *, accepted: bool) -> None:
        self._policy.observe_guided_ack(accepted=accepted)

    def tick(self) -> TransitionResult:
        """Evaluate one periodic control tick, even if no input just arrived."""
        result = self._fsm.trigger(
            "control_tick",
            telemetry_policy=self._policy,
            decision_facts=self._policy.decision_facts(),
        )
        if not result.success:
            print(f"  state: {self.state} (no transition)")
        return result


def sample_command(sequence: int) -> AvoidanceCommand:
    return AvoidanceCommand(
        sequence=sequence,
        target_latitude_deg=38.8895,
        target_longitude_deg=-77.0353,
        target_relative_altitude_m=35.0,
        north_velocity_m_s=2.0,
        east_velocity_m_s=-1.0,
        climb_rate_m_s=0.5,
        heading_deg=270.0,
    )


def main() -> None:
    """Run a deterministic telemetry and collision-system simulation."""
    print("Private ArduCopter collision-avoidance FSM prototype")
    print("No real aircraft is contacted.\n")

    clock = FakeClock()
    aircraft = SimulatedAircraft()
    policy = TelemetryPolicy(clock=clock)
    controller = DroneController(aircraft, policy)

    auto = DroneTelemetry(
        flight_mode=FlightMode.AUTO,
        altitude_m=30.0,
        collision_switch_enabled=True,
    )
    guided = DroneTelemetry(
        flight_mode=FlightMode.GUIDED,
        altitude_m=30.0,
        collision_switch_enabled=True,
    )

    print("Tick 1: no heartbeats")
    controller.tick()

    print("\nTick 2: both systems alive, collision readiness still dwelling")
    controller.observe_drone(auto)
    controller.observe_collision_heartbeat(ready=True)
    controller.observe_collision_status(AlertLevel.CLEAR)
    controller.tick()

    print("\nTick 3: readiness stable; monitoring becomes active")
    clock.advance(1.1)
    controller.observe_drone(auto)
    controller.observe_collision_heartbeat(ready=True)
    controller.observe_collision_status(AlertLevel.CLEAR)
    controller.tick()

    print("\nTick 4: actionable alert atomically requests Guided and a target")
    controller.observe_collision_status(AlertLevel.AVOID, sample_command(1))
    controller.tick()

    print("\nTick 5: Guided is confirmed; a newer command is accepted")
    clock.advance(0.1)
    controller.observe_guided_ack(accepted=True)
    controller.observe_drone(guided)
    controller.observe_collision_heartbeat(ready=True)
    controller.observe_collision_status(AlertLevel.CRITICAL, sample_command(2))
    controller.tick()

    print("\nTick 6: fresh all-clear leaves the last Guided command untouched")
    clock.advance(0.1)
    controller.observe_drone(guided)
    controller.observe_collision_heartbeat(ready=True)
    controller.observe_collision_status(AlertLevel.CLEAR)
    controller.tick()

    print("\nTick 7: only the pilot's AUTO selection re-enables monitoring")
    clock.advance(0.1)
    controller.observe_drone(auto)
    controller.observe_collision_heartbeat(ready=True)
    controller.observe_collision_status(AlertLevel.CLEAR)
    controller.tick()

    print("\nTick 8: collision heartbeat expires despite fresh drone telemetry")
    clock.advance(2.1)
    controller.observe_drone(auto)
    controller.observe_collision_status(AlertLevel.CLEAR)
    controller.tick()

    print(f"\nFinal state: {controller.state}")
    print("Commands issued:")
    for command in aircraft.commands:
        print(f"  - {command}")


if __name__ == "__main__":
    main()
