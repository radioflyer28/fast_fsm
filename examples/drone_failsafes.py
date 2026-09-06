#!/usr/bin/env python3
"""Drone pre-arm and in-flight failsafe example.

This is a deterministic training/simulation example, not flight-control software.
It models the decision layer that would receive already-validated telemetry from a
flight controller; it does not communicate with, command, or certify real hardware.
"""

from fast_fsm import FSMBuilder, FuncCondition, State


class DroneState(State):
    """Print each modeled state change with its originating event."""

    def on_enter(self, from_state, trigger, **kwargs):
        source = from_state.name if from_state else "start"
        print(f"  -> {self.name} ({source} --{trigger}--> {self.name})")


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
    armed = DroneState("Armed")
    takeoff = DroneState("Takeoff")
    mission = DroneState("Mission")
    return_home = DroneState("ReturnHome")
    landing = DroneState("Landing")
    emergency_landing = DroneState("EmergencyLanding")
    landed = DroneState("Landed")

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


def dispatch(drone, event: str, **telemetry) -> None:
    """Send one modeled event and make accepted or blocked results visible."""
    result = drone.trigger(event, **telemetry)
    if result.success:
        print(f"✓ {event}: {result.from_state} -> {result.to_state}")
    else:
        print(f"✗ {event}: blocked ({result.error})")


def main() -> None:
    """Run one normal return-to-home and one critical-fault scenario."""
    print("Drone safety state-machine simulation")
    print("This example is not flight-control software.\n")

    drone = create_drone_fsm()
    ready_telemetry = {
        "battery_pct": 82,
        "gps_fix": True,
        "home_position_set": True,
        "propellers_clear": True,
        "geofence_loaded": True,
        "launch_area_clear": True,
    }

    print("--- Pre-arm checks ---")
    dispatch(drone, "arm", **{**ready_telemetry, "battery_pct": 20})
    dispatch(drone, "arm", **ready_telemetry)
    dispatch(drone, "takeoff", **ready_telemetry)
    dispatch(drone, "begin_mission")

    print("\n--- Low-battery return-to-home ---")
    dispatch(drone, "failsafe_low_battery", battery_pct=19)
    dispatch(drone, "home_reached")
    dispatch(drone, "touchdown")

    print("\n--- Critical-fault emergency landing ---")
    dispatch(drone, "prepare_next_flight")
    dispatch(drone, "arm", **ready_telemetry)
    dispatch(drone, "takeoff", **ready_telemetry)
    dispatch(drone, "failsafe_critical_fault", critical_fault=True)
    dispatch(drone, "touchdown")

    print(f"\nFinal state: {drone.current_state_name}")


if __name__ == "__main__":
    main()
