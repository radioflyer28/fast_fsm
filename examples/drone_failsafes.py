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


def critical_fault_present(**telemetry) -> bool:
    """Model a flight controller reporting an unrecoverable vehicle fault."""
    return telemetry.get("critical_fault", False)


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
        # In-flight failsafes: the monitoring layer emits these events from
        # current telemetry.  Link loss returns home immediately; battery and
        # hardware-fault events retain an explicit threshold/fault guard.
        .add_transition("failsafe_link_lost", ["Takeoff", "Mission"], "ReturnHome")
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
        .add_transition("home_reached", "ReturnHome", "Landing")
        .add_transition("touchdown", ["Landing", "EmergencyLanding"], "Landed")
        .add_transition("prepare_next_flight", "Landed", "PreArm")
        .build()
    )


def dispatch(drone, aircraft: SimulatedAircraft, event: str, **telemetry) -> None:
    """Send one modeled event and expose accepted or blocked results."""
    telemetry["aircraft"] = aircraft
    result = drone.trigger(event, **telemetry)
    if result.success:
        print(f"✓ {event}: {result.from_state} -> {result.to_state}")
    else:
        print(f"✗ {event}: blocked ({result.error})")


def update_from_telemetry(
    drone, aircraft: SimulatedAircraft, sample: TelemetrySample
) -> None:
    """Apply one telemetry reading, prioritizing failsafes over operator commands.

    In a real integration, construct ``TelemetrySample`` from a normalized,
    independently validated telemetry packet, then call this function once per
    packet. Safety events are intentionally evaluated before commands such as
    arming or takeoff.
    """
    telemetry = asdict(sample)
    state = drone.current_state_name
    print(
        f"\nTelemetry: battery={sample.battery_pct}% link={'ok' if sample.link_ok else 'lost'} "
        f"state={state} command={sample.operator_command or '-'}"
    )

    # Failsafes always outrank normal progress. A flight controller would
    # normally emit these values from independently monitored subsystems.
    if state in {"Takeoff", "Mission", "ReturnHome"} and sample.critical_fault:
        dispatch(drone, aircraft, "failsafe_critical_fault", **telemetry)
        return
    if state in {"Takeoff", "Mission"} and not sample.link_ok:
        dispatch(drone, aircraft, "failsafe_link_lost", **telemetry)
        return
    if state in {"Takeoff", "Mission"} and sample.battery_pct < 25:
        dispatch(drone, aircraft, "failsafe_low_battery", **telemetry)
        return
    if state == "ReturnHome" and sample.home_reached:
        dispatch(drone, aircraft, "home_reached", **telemetry)
        return
    if state in {"Landing", "EmergencyLanding"} and sample.on_ground:
        dispatch(drone, aircraft, "touchdown", **telemetry)
        return

    command_events = {
        ("PreArm", "arm"): "arm",
        ("Armed", "takeoff"): "takeoff",
        ("Takeoff", "begin_mission"): "begin_mission",
        ("Landed", "prepare_next_flight"): "prepare_next_flight",
    }
    event = command_events.get((state, sample.operator_command))
    if event is not None:
        dispatch(drone, aircraft, event, **telemetry)
    else:
        print("• no state transition")


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
