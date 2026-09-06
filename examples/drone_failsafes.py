#!/usr/bin/env python3
"""Drone pre-arm and in-flight failsafe example.

This is a deterministic training/simulation example, not flight-control software.
It models the decision layer that would receive already-validated telemetry from a
flight controller; it does not communicate with, command, or certify real hardware.
"""

from dataclasses import dataclass
from time import monotonic
from typing import Callable, Protocol

from fast_fsm import FSMBuilder, FuncCondition, State


class AircraftCommands(Protocol):
    """The command port that a real or simulated aircraft adapter implements."""

    def command_arm_motors(self) -> None: ...

    def command_takeoff(self) -> None: ...

    def command_start_mission(self) -> None: ...

    def command_return_to_home(self) -> None: ...

    def command_begin_landing(self) -> None: ...

    def command_emergency_land(self) -> None: ...

    def command_disarm_motors(self) -> None: ...


class SimulatedAircraft:
    """A simulated implementation of the aircraft command port."""

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
        entry_action: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(name)
        self.entry_action = entry_action

    def on_enter(self, from_state, trigger, **kwargs):
        source = from_state.name if from_state else "start"
        print(f"  -> {self.name} ({source} --{trigger}--> {self.name})")
        if self.entry_action is not None:
            self.entry_action()


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


class TelemetryPolicy:
    """Retain telemetry facts and derive time-based measurements.

    This service does not select events or inspect flight states. Transition
    guards query it for the facts they need, keeping transition logic inside
    the FSM.
    """

    __slots__ = ("_clock", "_last_heartbeat_at", "_sample")

    def __init__(self, clock: Callable[[], float] = monotonic) -> None:
        self._clock = clock
        self._last_heartbeat_at: float | None = None
        self._sample: TelemetrySample | None = None

    def observe(self, sample: TelemetrySample) -> None:
        """Record the latest normalized telemetry reading."""
        self._sample = sample
        if sample.link_ok:
            self._last_heartbeat_at = self._clock()

    def heartbeat_older_than(self, seconds: float) -> bool:
        """Return whether no healthy heartbeat has arrived within ``seconds``."""
        if self._last_heartbeat_at is None:
            return True
        return self._clock() - self._last_heartbeat_at > seconds

    @property
    def sample(self) -> TelemetrySample:
        """Return the latest observation after one has been recorded."""
        if self._sample is None:
            raise RuntimeError("TelemetryPolicy has not observed a sample")
        return self._sample


def pre_arm_ready(telemetry_policy: TelemetryPolicy, **_) -> bool:
    """Require every ground-safety interlock before arming."""
    sample = telemetry_policy.sample
    return (
        sample.battery_pct >= 30
        and sample.gps_fix
        and sample.home_position_set
        and sample.propellers_clear
        and sample.geofence_loaded
    )


def launch_clear(telemetry_policy: TelemetryPolicy, **_) -> bool:
    """Require a clear launch area and an acceptable battery reserve."""
    sample = telemetry_policy.sample
    return sample.launch_area_clear and sample.battery_pct >= 35


def battery_critical(telemetry_policy: TelemetryPolicy, **_) -> bool:
    """Allow the low-battery failsafe only below its conservative threshold."""
    return telemetry_policy.sample.battery_pct < 25


def link_lost(telemetry_policy: TelemetryPolicy, **_) -> bool:
    """Report an unavailable link or a heartbeat absent for five seconds."""
    return not telemetry_policy.sample.link_ok or telemetry_policy.heartbeat_older_than(
        5
    )


def critical_fault_present(telemetry_policy: TelemetryPolicy, **_) -> bool:
    """Model a flight controller reporting an unrecoverable vehicle fault."""
    return telemetry_policy.sample.critical_fault


def home_reached(telemetry_policy: TelemetryPolicy, **_) -> bool:
    """Report that the aircraft has reached its stored home position."""
    return telemetry_policy.sample.home_reached


def touchdown_detected(telemetry_policy: TelemetryPolicy, **_) -> bool:
    """Report that the aircraft is on the ground."""
    return telemetry_policy.sample.on_ground


# This is an ordering declaration, not telemetry classification. Every rule
# that makes a candidate event valid lives in its transition's FuncCondition.
TELEMETRY_EVENT_PRIORITY = (
    "failsafe_critical_fault",
    "failsafe_link_lost",
    "failsafe_low_battery",
    "home_reached",
    "touchdown",
)


def create_drone_fsm(aircraft: AircraftCommands):
    """Build the controller's ground, mission, return, and emergency FSM."""
    pre_arm = DroneState("PreArm")
    armed = DroneState("Armed", aircraft.command_arm_motors)
    takeoff = DroneState("Takeoff", aircraft.command_takeoff)
    mission = DroneState("Mission", aircraft.command_start_mission)
    return_home = DroneState("ReturnHome", aircraft.command_return_to_home)
    landing = DroneState("Landing", aircraft.command_begin_landing)
    emergency_landing = DroneState("EmergencyLanding", aircraft.command_emergency_land)
    landed = DroneState("Landed", aircraft.command_disarm_motors)

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


class DroneController:
    """Own the FSM for one aircraft command adapter."""

    __slots__ = ("_aircraft", "_fsm", "_telemetry_policy")

    def __init__(
        self,
        aircraft: AircraftCommands,
        telemetry_policy: TelemetryPolicy | None = None,
    ) -> None:
        self._aircraft = aircraft
        self._telemetry_policy = (
            TelemetryPolicy() if telemetry_policy is None else telemetry_policy
        )
        self._fsm = create_drone_fsm(aircraft)

    @property
    def current_state_name(self) -> str:
        """Return the controller's current flight state."""
        return self._fsm.current_state_name

    def update_from_telemetry(self, sample: TelemetrySample) -> None:
        """Apply one reading by offering ordered triggers to the FSM.

        In a real integration, construct ``TelemetrySample`` from a normalized,
        independently validated telemetry packet, then call this method once per
        packet. The policy retains telemetry facts; transition guards are their
        sole consumer for deciding whether an event is valid. This controller
        only submits named triggers in priority order.
        """
        self._telemetry_policy.observe(sample)
        print(
            f"\nTelemetry: battery={sample.battery_pct}% "
            f"link={'ok' if sample.link_ok else 'lost'} "
            f"state={self.current_state_name} "
            f"command={sample.operator_command or '-'}"
        )

        for event in (*TELEMETRY_EVENT_PRIORITY, sample.operator_command):
            if event is not None and self._dispatch(event).success:
                return
        print("• no state transition")

    def _dispatch(self, event: str):
        """Send one candidate event and report an accepted transition."""
        result = self._fsm.trigger(event, telemetry_policy=self._telemetry_policy)
        if result.success:
            print(f"✓ {event}: {result.from_state} -> {result.to_state}")
        return result


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

    aircraft = SimulatedAircraft()
    drone = DroneController(aircraft)

    for index, sample in enumerate(simulated_telemetry(), start=1):
        print(f"--- Telemetry tick {index} ---")
        drone.update_from_telemetry(sample)

    print(f"\nFinal state: {drone.current_state_name}")
    print(f"Commands issued: {', '.join(aircraft.commands)}")


if __name__ == "__main__":
    main()
