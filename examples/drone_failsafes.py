#!/usr/bin/env python3
"""Drone pre-arm and in-flight failsafe example.

This is a deterministic training/simulation example, not flight-control software.
It models the decision layer that would receive already-validated telemetry from a
flight controller; it does not communicate with, command, or certify real hardware.
"""

from dataclasses import asdict, dataclass
from typing import Callable

from fast_fsm import FSMBuilder, FuncCondition, State


class SimulatedAircraft:
    """Expose the command methods a real aircraft adapter would implement."""

    __slots__ = ("commands",)

    def __init__(self) -> None:
        self.commands: list[str] = []

    def _record(self, command: str) -> None:
        """Record one command without contacting real hardware."""
        self.commands.append(command)
        print(f"  aircraft.{command}()")

    def command_arm_motors(self) -> None:
        self._record("command_arm_motors")

    def command_takeoff(self) -> None:
        self._record("command_takeoff")

    def command_start_mission(self) -> None:
        self._record("command_start_mission")

    def command_return_to_home(self) -> None:
        self._record("command_return_to_home")

    def command_begin_landing(self) -> None:
        self._record("command_begin_landing")

    def command_emergency_land(self) -> None:
        self._record("command_emergency_land")

    def command_disarm_motors(self) -> None:
        self._record("command_disarm_motors")


class DroneState(State):
    """Print each modeled state change and issue its post-commit command."""

    __slots__ = ("entry_action",)

    def __init__(
        self,
        name: str,
        entry_action: Callable[[SimulatedAircraft], None] | None = None,
    ) -> None:
        super().__init__(name)
        self.entry_action = entry_action

    def on_enter(self, from_state, trigger, **kwargs):
        source = from_state.name if from_state else "start"
        print(f"  -> {self.name} ({source} --{trigger}--> {self.name})")
        aircraft = kwargs.get("aircraft")
        if self.entry_action is not None and aircraft is not None:
            self.entry_action(aircraft)


@dataclass(frozen=True)
class TelemetrySample:
    """One normalized telemetry reading plus an optional operator request."""

    battery_pct: int
    gps_fix: bool = False
    home_position_set: bool = False
    propellers_clear: bool = False
    geofence_loaded: bool = False
    launch_area_clear: bool = False
    link_ok: bool = True
    home_reached: bool = False
    on_ground: bool = False
    critical_fault: bool = False
    operator_command: str | None = None


def pre_arm_ready(**telemetry) -> bool:
    """Require every ground-safety interlock before arming."""
    return (
        telemetry.get("battery_pct", 0) >= 30
        and telemetry.get("gps_fix", False)
        and telemetry.get("home_position_set", False)
        and telemetry.get("propellers_clear", False)
        and telemetry.get("geofence_loaded", False)
    )


def launch_clear(**telemetry) -> bool:
    """Require a clear launch area and an acceptable battery reserve."""
    return (
        telemetry.get("launch_area_clear", False)
        and telemetry.get("battery_pct", 0) >= 35
    )


def battery_critical(**telemetry) -> bool:
    """Allow the low-battery failsafe only below its conservative threshold."""
    return telemetry.get("battery_pct", 100) < 25


def link_lost(**telemetry) -> bool:
    """Report that the independently monitored command link is unavailable."""
    return not telemetry.get("link_ok", True)


def critical_fault_present(**telemetry) -> bool:
    """Model a flight controller reporting an unrecoverable vehicle fault."""
    return telemetry.get("critical_fault", False)


def home_reached(**telemetry) -> bool:
    """Report that the aircraft has reached its stored home position."""
    return telemetry.get("home_reached", False)


def touchdown_detected(**telemetry) -> bool:
    """Report that the aircraft is on the ground."""
    return telemetry.get("on_ground", False)


@dataclass(frozen=True, slots=True)
class TelemetryRule:
    """One ordered raw-telemetry rule that emits a discrete FSM event."""

    event: str
    predicate: Callable[..., bool]


class TelemetryPolicy:
    """Rank telemetry into FSM event candidates with an explicit priority table.

    This policy deliberately has no knowledge of flight states.  It determines
    which observed condition wins when a packet contains several signals; the
    drone FSM determines whether that selected event is legal in its current
    state.
    """

    __slots__ = ("_rules", "_operator_events")

    def __init__(
        self,
        rules: tuple[TelemetryRule, ...],
        operator_events: dict[str, str],
    ) -> None:
        self._rules = rules
        self._operator_events = operator_events

    def events_for(self, **telemetry) -> tuple[str, ...]:
        """Return observed events in descending priority order.

        A rule may match while its event is illegal from the FSM's current
        state. The caller submits candidates in order and lets the FSM accept
        the first legal one, without this policy learning about flight states.
        """
        events = [rule.event for rule in self._rules if rule.predicate(**telemetry)]
        operator_event = self._operator_events.get(telemetry.get("operator_command"))
        if operator_event is not None:
            events.append(operator_event)
        return tuple(events)


# Rules rank all observations. The flight FSM—not this policy—decides which
# source states accept each event; the loop uses the first one it accepts.
TELEMETRY_POLICY = TelemetryPolicy(
    rules=(
        TelemetryRule("failsafe_critical_fault", critical_fault_present),
        TelemetryRule("failsafe_link_lost", link_lost),
        TelemetryRule("failsafe_low_battery", battery_critical),
        TelemetryRule("home_reached", home_reached),
        TelemetryRule("touchdown", touchdown_detected),
    ),
    operator_events={
        "arm": "arm",
        "takeoff": "takeoff",
        "begin_mission": "begin_mission",
        "prepare_next_flight": "prepare_next_flight",
    },
)


def create_drone_fsm():
    """Build the drone's ground, mission, return, and emergency state model."""
    pre_arm = DroneState("PreArm")
    armed = DroneState("Armed", SimulatedAircraft.command_arm_motors)
    takeoff = DroneState("Takeoff", SimulatedAircraft.command_takeoff)
    mission = DroneState("Mission", SimulatedAircraft.command_start_mission)
    return_home = DroneState("ReturnHome", SimulatedAircraft.command_return_to_home)
    landing = DroneState("Landing", SimulatedAircraft.command_begin_landing)
    emergency_landing = DroneState(
        "EmergencyLanding", SimulatedAircraft.command_emergency_land
    )
    landed = DroneState("Landed", SimulatedAircraft.command_disarm_motors)

    return (
        FSMBuilder(pre_arm, name="DroneSafety")
        .add_state(armed)
        .add_state(takeoff)
        .add_state(mission)
        .add_state(return_home)
        .add_state(landing)
        .add_state(emergency_landing)
        .add_state(landed)
        # Ground checks: only complete, acceptable telemetry may arm the drone.
        .add_transition(
            "arm",
            "PreArm",
            "Armed",
            condition=FuncCondition(pre_arm_ready, name="pre_arm_ready"),
        )
        .add_transition(
            "takeoff",
            "Armed",
            "Takeoff",
            condition=FuncCondition(launch_clear, name="launch_clear"),
        )
        .add_transition("begin_mission", "Takeoff", "Mission")
        # The telemetry policy selects one event from its ordered rule table.
        # These transitions alone determine which flight states accept it.
        .add_transition(
            "failsafe_link_lost",
            ["Takeoff", "Mission"],
            "ReturnHome",
            condition=FuncCondition(link_lost, name="link_lost"),
        )
        .add_transition(
            "failsafe_low_battery",
            ["Takeoff", "Mission"],
            "ReturnHome",
            condition=FuncCondition(battery_critical, name="battery_critical"),
        )
        .add_transition(
            "failsafe_critical_fault",
            ["Takeoff", "Mission", "ReturnHome"],
            "EmergencyLanding",
            condition=FuncCondition(
                critical_fault_present, name="critical_fault_present"
            ),
        )
        .add_transition(
            "home_reached",
            "ReturnHome",
            "Landing",
            condition=FuncCondition(home_reached, name="home_reached"),
        )
        .add_transition(
            "touchdown",
            ["Landing", "EmergencyLanding"],
            "Landed",
            condition=FuncCondition(touchdown_detected, name="touchdown_detected"),
        )
        .add_transition("prepare_next_flight", "Landed", "PreArm")
        .build()
    )


def dispatch(drone, aircraft: SimulatedAircraft, event: str, **telemetry):
    """Send one modeled event and expose accepted or blocked results."""
    telemetry["aircraft"] = aircraft
    result = drone.trigger(event, **telemetry)
    if result.success:
        print(f"✓ {event}: {result.from_state} -> {result.to_state}")
    else:
        print(f"✗ {event}: blocked ({result.error})")
    return result


def update_from_telemetry(
    drone, aircraft: SimulatedAircraft, sample: TelemetrySample
) -> None:
    """Apply one telemetry reading through the state-independent policy.

    In a real integration, construct ``TelemetrySample`` from a normalized,
    independently validated telemetry packet, then call this function once per
    packet. The policy ranks all observed event candidates; the flight FSM
    accepts the first legal one based on its current state and its guards.
    """
    telemetry = asdict(sample)
    print(
        f"\nTelemetry: battery={sample.battery_pct}% link={'ok' if sample.link_ok else 'lost'} "
        f"state={drone.current_state_name} command={sample.operator_command or '-'}"
    )

    events = TELEMETRY_POLICY.events_for(**telemetry)
    if not events:
        print("• no state transition")
        return

    for event in events:
        if dispatch(drone, aircraft, event, **telemetry).success:
            return


def simulated_telemetry() -> list[TelemetrySample]:
    """Return a deterministic sequence that resembles a live telemetry stream."""
    ready = {
        "battery_pct": 82,
        "gps_fix": True,
        "home_position_set": True,
        "propellers_clear": True,
        "geofence_loaded": True,
        "launch_area_clear": True,
    }
    return [
        TelemetrySample(**{**ready, "battery_pct": 20, "operator_command": "arm"}),
        TelemetrySample(**{**ready, "operator_command": "arm"}),
        TelemetrySample(**{**ready, "operator_command": "takeoff"}),
        TelemetrySample(**{**ready, "operator_command": "begin_mission"}),
        TelemetrySample(**{**ready, "battery_pct": 74}),
        TelemetrySample(**{**ready, "battery_pct": 22}),
        TelemetrySample(**{**ready, "battery_pct": 20, "home_reached": True}),
        TelemetrySample(**{**ready, "battery_pct": 20, "on_ground": True}),
        TelemetrySample(**{**ready, "operator_command": "prepare_next_flight"}),
        TelemetrySample(**{**ready, "operator_command": "arm"}),
        TelemetrySample(**{**ready, "operator_command": "takeoff"}),
        TelemetrySample(**{**ready, "critical_fault": True}),
        TelemetrySample(**{**ready, "on_ground": True}),
    ]


def main() -> None:
    """Run a simulated stream through the state machine one packet at a time."""
    print("Drone safety state-machine telemetry-loop simulation")
    print("This example is not flight-control software.\n")

    drone = create_drone_fsm()
    aircraft = SimulatedAircraft()

    for index, sample in enumerate(simulated_telemetry(), start=1):
        print(f"--- Telemetry tick {index} ---")
        update_from_telemetry(drone, aircraft, sample)

    print(f"\nFinal state: {drone.current_state_name}")
    print(f"Commands issued: {', '.join(aircraft.commands)}")


if __name__ == "__main__":
    main()
