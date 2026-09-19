#!/usr/bin/env python3
"""Drone pre-arm and in-flight failsafe example.

This is a deterministic training/simulation example, not flight-control software.
It models the decision layer that would receive already-validated telemetry from a
flight controller; it does not communicate with, command, or certify real hardware.
"""

from dataclasses import dataclass
from time import monotonic
from typing import Callable, Protocol

from fast_fsm import (
    FSMBuilder,
    FuncCondition,
    State,
    TransitionRejected,
    TransitionResult,
)


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


def report_state_entry(state_name: str) -> Callable[..., None]:
    """Create a built-in lifecycle callback that reports one committed entry."""

    def report(from_state: State | None, trigger: str, **_) -> None:
        source = from_state.name if from_state else "start"
        print(f"  -> {state_name} ({source} --{trigger}--> {state_name})")

    return report


def issue_aircraft_command(command: Callable[[], None]) -> Callable[..., None]:
    """Adapt a no-argument aircraft command to an FSM entry callback."""

    def issue(_from_state: State | None, _trigger: str, **_) -> None:
        command()

    return issue


@dataclass(frozen=True)
class TelemetrySample:
    """One normalized telemetry reading used only as a source of facts."""

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
    reenter_mission: bool = False
    navigation_conflict: bool = False


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


def mission_reentry_requested(telemetry_policy: TelemetryPolicy, **_) -> bool:
    """Request an external Mission self-transition with full re-entry effects."""
    return telemetry_policy.sample.reenter_mission


def mission_update_requested(telemetry_policy: TelemetryPolicy, **_) -> bool:
    """Commit a routine in-Mission update without restarting state residency."""
    return not telemetry_policy.sample.reenter_mission


def reject_navigation_conflict(telemetry_policy: TelemetryPolicy, **_) -> bool:
    """Signal a bounded terminal outcome for incompatible navigation facts."""
    if telemetry_policy.sample.navigation_conflict:
        raise TransitionRejected("navigation-conflict")
    return False


def create_drone_fsm(
    aircraft: AircraftCommands, *, clock: Callable[[], float] = monotonic
):
    """Build the controller's ground, mission, return, and emergency FSM."""
    pre_arm = State("PreArm")
    armed = State("Armed")
    takeoff = State("Takeoff")
    mission = State("Mission")
    return_home = State("ReturnHome")
    landing = State("Landing")
    emergency_landing = State("EmergencyLanding")
    landed = State("Landed", final=True)
    emergency_landed = State("EmergencyLanded", final=True)

    builder = (
        FSMBuilder(pre_arm, name="DroneSafety", clock=clock)
        .add_state(armed)
        .add_state(takeoff)
        .add_state(mission)
        .add_state(return_home)
        .add_state(landing)
        .add_state(emergency_landing)
        .add_state(landed)
        .add_state(emergency_landed)
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
        # One telemetry trigger leaves all selection in the FSM. Lower integer
        # priorities win, so critical fault, link loss, and low battery keep
        # their fixed failsafe precedence without controller-side routing.
        .add_transition(
            "telemetry_tick",
            ["Takeoff", "Mission", "ReturnHome", "Landing"],
            "EmergencyLanding",
            condition=FuncCondition(
                critical_fault_present, name="critical_fault_present"
            ),
            priority=0,
        )
        .add_transition(
            "telemetry_tick",
            ["Takeoff", "Mission"],
            "ReturnHome",
            condition=FuncCondition(link_lost, name="link_lost"),
            priority=10,
        )
        .add_transition(
            "telemetry_tick",
            ["Takeoff", "Mission"],
            "ReturnHome",
            condition=FuncCondition(battery_critical, name="battery_critical"),
            priority=20,
        )
        .add_transition(
            "telemetry_tick",
            "ReturnHome",
            "Landing",
            condition=FuncCondition(home_reached, name="home_reached"),
            priority=30,
        )
        .add_transition(
            "telemetry_tick",
            "Landing",
            "Landed",
            condition=FuncCondition(touchdown_detected, name="touchdown_detected"),
            priority=30,
        )
        # This guard is deliberately false for ordinary Mission telemetry so
        # selection falls through to its routine candidates. A conflict is a
        # distinct terminal domain outcome: it never selects a command path.
        .add_transition(
            "telemetry_tick",
            "Mission",
            "Mission",
            condition=FuncCondition(
                reject_navigation_conflict, name="reject_navigation_conflict"
            ),
            priority=40,
        )
        # Mission semantics are ordinary candidate transitions on the same
        # telemetry event. A requested re-entry comes before the routine
        # internal update, but both remain below every safety candidate.
        .add_transition(
            "telemetry_tick",
            "Mission",
            "Mission",
            condition=FuncCondition(
                mission_reentry_requested, name="mission_reentry_requested"
            ),
            priority=50,
        )
        .add_transition(
            "telemetry_tick",
            "Mission",
            "Mission",
            condition=FuncCondition(
                mission_update_requested, name="mission_update_requested"
            ),
            priority=60,
            internal=True,
        )
        .add_transition(
            "telemetry_tick",
            "EmergencyLanding",
            "EmergencyLanded",
            condition=FuncCondition(touchdown_detected, name="touchdown_detected"),
            priority=30,
        )
    )

    entry_commands = {
        "Armed": aircraft.command_arm_motors,
        "Takeoff": aircraft.command_takeoff,
        "Mission": aircraft.command_start_mission,
        "ReturnHome": aircraft.command_return_to_home,
        "Landing": aircraft.command_begin_landing,
        "EmergencyLanding": aircraft.command_emergency_land,
        "Landed": aircraft.command_disarm_motors,
        "EmergencyLanded": aircraft.command_disarm_motors,
    }
    for state_name in (
        "PreArm",
        "Armed",
        "Takeoff",
        "Mission",
        "ReturnHome",
        "Landing",
        "EmergencyLanding",
        "Landed",
        "EmergencyLanded",
    ):
        builder.on_enter(state_name, report_state_entry(state_name))
        command = entry_commands.get(state_name)
        if command is not None:
            builder.on_enter(state_name, issue_aircraft_command(command))

    machine = builder.build()
    machine.enable_history()
    return machine


class DroneController:
    """Own the FSM for one aircraft command adapter."""

    __slots__ = ("_aircraft", "_fsm", "_telemetry_policy")

    def __init__(
        self,
        aircraft: AircraftCommands,
        telemetry_policy: TelemetryPolicy | None = None,
        *,
        fsm_clock: Callable[[], float] = monotonic,
    ) -> None:
        self._aircraft = aircraft
        self._telemetry_policy = (
            TelemetryPolicy() if telemetry_policy is None else telemetry_policy
        )
        self._fsm = create_drone_fsm(aircraft, clock=fsm_clock)

    @property
    def current_state_name(self) -> str:
        """Return the controller's current flight state."""
        return self._fsm.current_state_name

    def update_from_telemetry(self, sample: TelemetrySample) -> TransitionResult:
        """Observe one normalized sample and send one telemetry tick to the FSM.

        In a real integration, construct ``TelemetrySample`` from a normalized,
        independently validated telemetry packet, then call this method once per
        packet. The policy retains only facts; fixed-priority FSM guards select
        the transition, and a committed destination entry may command aircraft.
        """
        self._telemetry_policy.observe(sample)
        print(
            f"\nTelemetry: battery={sample.battery_pct}% "
            f"link={'ok' if sample.link_ok else 'lost'} "
            f"state={self.current_state_name}"
        )

        return self._report(
            self._fsm.trigger("telemetry_tick", telemetry_policy=self._telemetry_policy)
        )

    def perform_operator_action(self, action: str) -> TransitionResult:
        """Submit one explicit non-telemetry operator action to the FSM."""
        print(f"\nOperator action: {action} state={self.current_state_name}")
        return self._report(
            self._fsm.trigger(action, telemetry_policy=self._telemetry_policy)
        )

    def _report(self, result: TransitionResult) -> TransitionResult:
        """Print one FSM result without attempting a fallback trigger."""
        if result.success:
            if result.internal:
                mode = "internal update"
            elif result.from_state == result.to_state:
                mode = "external self re-entry"
            else:
                mode = "state change"
            print(
                f"✓ {result.trigger}: {result.from_state} -> {result.to_state} [{mode}]"
            )
        elif result.rejected:
            print(f"! expected rejection: {result.rejection_code}")
        elif result.cause is not None:
            print("✗ unexpected transition failure")
        else:
            print("• no eligible transition")
        return result


def simulated_telemetry() -> list[TelemetrySample]:
    """Return the first deterministic training flight's telemetry sequence."""
    ready = {
        "battery_pct": 82,
        "gps_fix": True,
        "home_position_set": True,
        "propellers_clear": True,
        "geofence_loaded": True,
        "launch_area_clear": True,
    }
    return [
        TelemetrySample(**{**ready, "battery_pct": 74}),
        TelemetrySample(**ready),
        TelemetrySample(**{**ready, "reenter_mission": True}),
        TelemetrySample(**{**ready, "navigation_conflict": True}),
        TelemetrySample(**{**ready, "battery_pct": 22}),
        TelemetrySample(**{**ready, "home_reached": True}),
        TelemetrySample(**{**ready, "on_ground": True}),
    ]


def main() -> None:
    """Run two deterministic flights through independently owned controllers."""
    print("Drone safety state-machine telemetry-loop simulation")
    print(
        "This example is deterministic training software, not flight-control software.\n"
    )

    normal_aircraft = SimulatedAircraft()
    normal_flight = DroneController(normal_aircraft)

    for index, sample in enumerate(simulated_telemetry(), start=1):
        print(f"--- Normal-flight telemetry tick {index} ---")
        normal_flight.update_from_telemetry(sample)
        if index == 1:
            for action in ("arm", "takeoff", "begin_mission"):
                normal_flight.perform_operator_action(action)

    print(f"Normal flight final state: {normal_flight.current_state_name}")
    print(f"Normal-flight commands: {', '.join(normal_aircraft.commands)}\n")

    print("--- Second flight: a fresh controller owns a new adapter ---")
    emergency_aircraft = SimulatedAircraft()
    emergency_flight = DroneController(emergency_aircraft)
    ready = {
        "battery_pct": 82,
        "gps_fix": True,
        "home_position_set": True,
        "propellers_clear": True,
        "geofence_loaded": True,
        "launch_area_clear": True,
    }
    emergency_flight.update_from_telemetry(TelemetrySample(**ready))
    for action in ("arm", "takeoff", "begin_mission"):
        emergency_flight.perform_operator_action(action)
    emergency_flight.update_from_telemetry(
        TelemetrySample(**{**ready, "critical_fault": True})
    )
    emergency_flight.update_from_telemetry(
        TelemetrySample(**{**ready, "on_ground": True})
    )

    print(f"Emergency flight final state: {emergency_flight.current_state_name}")
    print(f"Emergency-flight commands: {', '.join(emergency_aircraft.commands)}")


if __name__ == "__main__":
    main()
