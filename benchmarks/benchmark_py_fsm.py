from statemachine import StateMachine, State
from statemachine.exceptions import TransitionNotAllowed
from enum import Enum
from typing import Optional
from dataclasses import dataclass


class ThreatLevel(Enum):
    NONE = "none"
    TRAFFIC_ADVISORY = "traffic_advisory"
    RESOLUTION_ADVISORY = "resolution_advisory"
    CRITICAL = "critical"


class ManeuverType(Enum):
    NONE = "none"
    CLIMB = "climb"
    DESCEND = "descend"
    LEVEL_OFF = "level_off"
    EMERGENCY_CLIMB = "emergency_climb"
    EMERGENCY_DESCEND = "emergency_descend"


class FlightPhase(Enum):
    NORMAL = "normal"
    MANEUVERING = "maneuvering"
    EMERGENCY = "emergency"
    RECOVERING = "recovering"


@dataclass(slots=True)
class TrafficData:
    distance: float
    altitude_difference: float
    closing_rate: float
    bearing: float
    time_to_closest_approach: float


@dataclass(slots=True)
class OwnAircraftData:
    altitude: float
    vertical_speed: float
    airspeed: float
    heading: float


# =============================================================================
# AIRCRAFT STATE MACHINE (using python-statemachine)
# =============================================================================


class AircraftStateMachine(StateMachine):
    """Aircraft Flight State Machine using python-statemachine library"""

    # Define states
    normal_flight = State(initial=True)
    maneuvering = State()
    emergency_maneuver = State()
    recovering = State()

    # Define transitions
    # From normal_flight
    start_climb = normal_flight.to(maneuvering)
    start_descend = normal_flight.to(maneuvering)
    start_emergency_climb = normal_flight.to(emergency_maneuver)
    start_emergency_descend = normal_flight.to(emergency_maneuver)
    normal_level_off = normal_flight.to(normal_flight)

    # From maneuvering
    continue_climb = maneuvering.to(maneuvering)
    continue_descend = maneuvering.to(maneuvering)
    escalate_to_emergency_climb = maneuvering.to(emergency_maneuver)
    escalate_to_emergency_descend = maneuvering.to(emergency_maneuver)
    complete_normal_maneuver = maneuvering.to(recovering)
    abort_normal_maneuver = maneuvering.to(recovering)
    level_off_from_maneuvering = maneuvering.to(recovering)

    # From emergency_maneuver
    continue_emergency_climb = emergency_maneuver.to(emergency_maneuver)
    continue_emergency_descend = emergency_maneuver.to(emergency_maneuver)
    complete_emergency_maneuver = emergency_maneuver.to(recovering)
    abort_emergency_maneuver = emergency_maneuver.to(recovering)
    level_off_from_emergency = emergency_maneuver.to(recovering)

    # From recovering
    start_climb_from_recovery = recovering.to(maneuvering)
    start_descend_from_recovery = recovering.to(maneuvering)
    emergency_climb_from_recovery = recovering.to(emergency_maneuver)
    emergency_descend_from_recovery = recovering.to(emergency_maneuver)
    level_off_from_recovery = recovering.to(recovering)
    finish_recovery = recovering.to(normal_flight)

    def __init__(self, aircraft):
        self.aircraft = aircraft
        super().__init__()

    # State entry/exit actions
    def on_enter_normal_flight(self):
        self.aircraft.active_maneuver = ManeuverType.NONE
        if hasattr(self.aircraft, "call_sign"):
            print(f"{self.aircraft.call_sign} Flight: Entered normal flight")

    def on_enter_maneuvering(self):
        if hasattr(self.aircraft, "call_sign"):
            print(f"{self.aircraft.call_sign} Flight: Started maneuvering")

    def on_enter_emergency_maneuver(self):
        if hasattr(self.aircraft, "call_sign"):
            print(f"{self.aircraft.call_sign} Flight: EMERGENCY MANEUVER INITIATED")

    def on_enter_recovering(self):
        if hasattr(self.aircraft, "call_sign"):
            print(f"{self.aircraft.call_sign} Flight: Stabilizing and recovering")

    # Transition guards (conditions)
    def before_start_emergency_climb(self):
        """Guard for emergency climb - always allowed from normal"""
        return True

    def before_escalate_to_emergency_climb(self):
        """Guard for escalating to emergency from maneuvering"""
        return True  # Emergency always takes precedence


class Aircraft:
    """Aircraft using python-statemachine for flight state management"""

    __slots__ = ("call_sign", "own_data", "active_maneuver", "state_machine")

    def __init__(self, call_sign: str, altitude: float = 10000):
        self.call_sign = call_sign
        self.own_data = OwnAircraftData(
            altitude=altitude, vertical_speed=0, airspeed=250, heading=0
        )
        self.active_maneuver = ManeuverType.NONE
        self.state_machine = AircraftStateMachine(self)

    def get_flight_phase(self) -> FlightPhase:
        """Get current flight phase based on state"""
        state_to_phase = {
            "normal_flight": FlightPhase.NORMAL,
            "maneuvering": FlightPhase.MANEUVERING,
            "emergency_maneuver": FlightPhase.EMERGENCY,
            "recovering": FlightPhase.RECOVERING,
        }
        return state_to_phase.get(
            self.state_machine.current_state.id, FlightPhase.NORMAL
        )

    def request_climb(self, target_altitude: float) -> bool:
        """Request climb maneuver"""
        try:
            current_state = self.state_machine.current_state.id

            if current_state == "normal_flight":
                self.state_machine.start_climb()
                self.active_maneuver = ManeuverType.CLIMB
            elif current_state == "maneuvering":
                self.state_machine.continue_climb()
                self.active_maneuver = ManeuverType.CLIMB
            elif current_state == "recovering":
                self.state_machine.start_climb_from_recovery()
                self.active_maneuver = ManeuverType.CLIMB
            else:  # emergency_maneuver
                print(
                    f"{self.call_sign} Flight: Cannot accept normal climb during emergency"
                )
                return False

            self._execute_climb(target_altitude)
            return True

        except TransitionNotAllowed:
            print(
                f"{self.call_sign} Flight: Climb request rejected - invalid state transition"
            )
            return False

    def request_descend(self, target_altitude: float) -> bool:
        """Request descend maneuver"""
        try:
            current_state = self.state_machine.current_state.id

            if current_state == "normal_flight":
                self.state_machine.start_descend()
                self.active_maneuver = ManeuverType.DESCEND
            elif current_state == "maneuvering":
                self.state_machine.continue_descend()
                self.active_maneuver = ManeuverType.DESCEND
            elif current_state == "recovering":
                self.state_machine.start_descend_from_recovery()
                self.active_maneuver = ManeuverType.DESCEND
            else:  # emergency_maneuver
                print(
                    f"{self.call_sign} Flight: Cannot accept normal descend during emergency"
                )
                return False

            self._execute_descend(target_altitude)
            return True

        except TransitionNotAllowed:
            print(
                f"{self.call_sign} Flight: Descend request rejected - invalid state transition"
            )
            return False

    def request_emergency_climb(self, target_altitude: float) -> bool:
        """Request emergency climb"""
        try:
            current_state = self.state_machine.current_state.id

            if current_state == "normal_flight":
                self.state_machine.start_emergency_climb()
            elif current_state == "maneuvering":
                self.state_machine.escalate_to_emergency_climb()
            elif current_state == "emergency_maneuver":
                self.state_machine.continue_emergency_climb()
            elif current_state == "recovering":
                self.state_machine.emergency_climb_from_recovery()

            self.active_maneuver = ManeuverType.EMERGENCY_CLIMB
            self._execute_emergency_climb(target_altitude)
            return True

        except TransitionNotAllowed:
            print(
                f"{self.call_sign} Flight: Emergency climb rejected - invalid transition"
            )
            return False

    def request_emergency_descend(self, target_altitude: float) -> bool:
        """Request emergency descend"""
        try:
            current_state = self.state_machine.current_state.id

            if current_state == "normal_flight":
                self.state_machine.start_emergency_descend()
            elif current_state == "maneuvering":
                self.state_machine.escalate_to_emergency_descend()
            elif current_state == "emergency_maneuver":
                self.state_machine.continue_emergency_descend()
            elif current_state == "recovering":
                self.state_machine.emergency_descend_from_recovery()

            self.active_maneuver = ManeuverType.EMERGENCY_DESCEND
            self._execute_emergency_descend(target_altitude)
            return True

        except TransitionNotAllowed:
            print(
                f"{self.call_sign} Flight: Emergency descend rejected - invalid transition"
            )
            return False

    def request_level_off(self) -> bool:
        """Request level off"""
        try:
            current_state = self.state_machine.current_state.id

            if current_state == "normal_flight":
                self.state_machine.normal_level_off()
            elif current_state == "maneuvering":
                self.state_machine.level_off_from_maneuvering()
            elif current_state == "emergency_maneuver":
                self.state_machine.level_off_from_emergency()
            elif current_state == "recovering":
                self.state_machine.level_off_from_recovery()

            self.active_maneuver = ManeuverType.LEVEL_OFF
            self._execute_level_off()
            return True

        except TransitionNotAllowed:
            print(f"{self.call_sign} Flight: Level off rejected - invalid transition")
            return False

    def complete_maneuver(self) -> bool:
        """Complete current maneuver"""
        try:
            current_state = self.state_machine.current_state.id

            if current_state == "maneuvering":
                self.state_machine.complete_normal_maneuver()
            elif current_state == "emergency_maneuver":
                self.state_machine.complete_emergency_maneuver()
            elif current_state == "recovering":
                self.state_machine.finish_recovery()

            return True

        except TransitionNotAllowed:
            print(
                f"{self.call_sign} Flight: Cannot complete maneuver from current state"
            )
            return False

    # Private execution methods (simulation)
    def _execute_climb(self, target_altitude: float):
        self.own_data.vertical_speed = 1500
        print(f"{self.call_sign} Flight: Climbing to {target_altitude} ft")

    def _execute_descend(self, target_altitude: float):
        self.own_data.vertical_speed = -1500
        print(f"{self.call_sign} Flight: Descending to {target_altitude} ft")

    def _execute_emergency_climb(self, target_altitude: float):
        self.own_data.vertical_speed = 2500
        print(f"{self.call_sign} Flight: EMERGENCY CLIMB to {target_altitude} ft")

    def _execute_emergency_descend(self, target_altitude: float):
        self.own_data.vertical_speed = -2500
        print(f"{self.call_sign} Flight: EMERGENCY DESCENT to {target_altitude} ft")

    def _execute_level_off(self):
        self.own_data.vertical_speed = 0
        print(f"{self.call_sign} Flight: Leveling off at {self.own_data.altitude} ft")


# =============================================================================
# TCAS STATE MACHINE (using python-statemachine)
# =============================================================================


class TcasStateMachine(StateMachine):
    """TCAS State Machine using python-statemachine library"""

    # Define states
    normal_flight = State(initial=True)
    traffic_advisory = State()
    resolution_advisory = State()
    critical_avoidance = State()

    # Define transitions
    # From normal_flight
    detect_traffic = normal_flight.to(traffic_advisory)
    issue_resolution = normal_flight.to(resolution_advisory)
    critical_threat_detected = normal_flight.to(critical_avoidance)

    # From traffic_advisory
    escalate_to_resolution = traffic_advisory.to(resolution_advisory)
    escalate_to_critical = traffic_advisory.to(critical_avoidance)
    clear_from_advisory = traffic_advisory.to(normal_flight)

    # From resolution_advisory
    escalate_resolution_to_critical = resolution_advisory.to(critical_avoidance)
    downgrade_to_advisory = resolution_advisory.to(traffic_advisory)
    clear_from_resolution = resolution_advisory.to(normal_flight)

    # From critical_avoidance
    downgrade_critical_to_resolution = critical_avoidance.to(resolution_advisory)
    clear_from_critical = critical_avoidance.to(normal_flight)

    def __init__(self, collision_avoidance_system):
        self.cas = collision_avoidance_system
        super().__init__()

    # State entry actions
    def on_enter_normal_flight(self):
        if hasattr(self.cas, "aircraft"):
            print(f"{self.cas.aircraft.call_sign} TCAS: Clear of traffic")

    def on_enter_traffic_advisory(self):
        if hasattr(self.cas, "aircraft"):
            print(f"{self.cas.aircraft.call_sign} TCAS: TRAFFIC ADVISORY")

    def on_enter_resolution_advisory(self):
        if hasattr(self.cas, "aircraft"):
            print(f"{self.cas.aircraft.call_sign} TCAS: RESOLUTION ADVISORY")

    def on_enter_critical_avoidance(self):
        if hasattr(self.cas, "aircraft"):
            print(f"{self.cas.aircraft.call_sign} TCAS: CRITICAL AVOIDANCE MANEUVER")


class CollisionAvoidanceSystem:
    """TCAS using python-statemachine for threat assessment"""

    __slots__ = ("aircraft", "current_traffic", "state_machine")

    def __init__(self, aircraft: Aircraft):
        self.aircraft = aircraft
        self.current_traffic: Optional[TrafficData] = None
        self.state_machine = TcasStateMachine(self)

    def get_threat_level(self) -> ThreatLevel:
        """Get current threat level based on state"""
        state_to_threat = {
            "normal_flight": ThreatLevel.NONE,
            "traffic_advisory": ThreatLevel.TRAFFIC_ADVISORY,
            "resolution_advisory": ThreatLevel.RESOLUTION_ADVISORY,
            "critical_avoidance": ThreatLevel.CRITICAL,
        }
        return state_to_threat.get(
            self.state_machine.current_state.id, ThreatLevel.NONE
        )

    def update_traffic(self, traffic: TrafficData):
        """Update traffic information and assess threat"""
        self.current_traffic = traffic
        threat_level = self._assess_threat(traffic)

        try:
            current_state = self.state_machine.current_state.id

            if threat_level == ThreatLevel.CRITICAL:
                if current_state != "critical_avoidance":
                    if current_state == "normal_flight":
                        self.state_machine.critical_threat_detected()
                    elif current_state == "traffic_advisory":
                        self.state_machine.escalate_to_critical()
                    elif current_state == "resolution_advisory":
                        self.state_machine.escalate_resolution_to_critical()
                    self._issue_critical_avoidance()

            elif threat_level == ThreatLevel.RESOLUTION_ADVISORY:
                if current_state == "normal_flight":
                    self.state_machine.issue_resolution()
                    self._issue_resolution_advisory()
                elif current_state == "traffic_advisory":
                    self.state_machine.escalate_to_resolution()
                    self._issue_resolution_advisory()
                elif current_state == "critical_avoidance":
                    self.state_machine.downgrade_critical_to_resolution()

            elif threat_level == ThreatLevel.TRAFFIC_ADVISORY:
                if current_state == "normal_flight":
                    self.state_machine.detect_traffic()
                elif current_state in ["resolution_advisory", "critical_avoidance"]:
                    if current_state == "resolution_advisory":
                        self.state_machine.downgrade_to_advisory()
                    else:  # critical_avoidance
                        # Need to go through resolution first for this transition
                        pass

        except TransitionNotAllowed as e:
            print(f"TCAS transition not allowed: {e}")

    def clear_traffic(self):
        """Clear all traffic threats"""
        self.current_traffic = None

        try:
            current_state = self.state_machine.current_state.id

            if current_state == "traffic_advisory":
                self.state_machine.clear_from_advisory()
            elif current_state == "resolution_advisory":
                self.state_machine.clear_from_resolution()
            elif current_state == "critical_avoidance":
                self.state_machine.clear_from_critical()

        except TransitionNotAllowed as e:
            print(f"TCAS clear transition not allowed: {e}")

    def maneuver_complete(self):
        """Signal that avoidance maneuver is complete"""
        self.aircraft.complete_maneuver()

    def _assess_threat(self, traffic: TrafficData) -> ThreatLevel:
        """Assess threat level based on traffic data"""
        if traffic.time_to_closest_approach < 5 and traffic.distance < 0.25:
            return ThreatLevel.CRITICAL
        elif traffic.time_to_closest_approach < 15 and traffic.distance < 1.0:
            return ThreatLevel.RESOLUTION_ADVISORY
        elif traffic.distance < 5.0:
            return ThreatLevel.TRAFFIC_ADVISORY
        else:
            return ThreatLevel.NONE

    def _issue_resolution_advisory(self):
        """Issue resolution advisory maneuver"""
        if not self.current_traffic:
            return

        if self.current_traffic.altitude_difference > 0:
            # Other aircraft is higher, we should descend
            target_altitude = self.aircraft.own_data.altitude - 1000
            self.aircraft.request_descend(target_altitude)
        else:
            # Other aircraft is lower, we should climb
            target_altitude = self.aircraft.own_data.altitude + 1000
            self.aircraft.request_climb(target_altitude)

    def _issue_critical_avoidance(self):
        """Issue critical avoidance maneuver"""
        if not self.current_traffic:
            return

        if self.current_traffic.altitude_difference > 0:
            target_altitude = self.aircraft.own_data.altitude - 2000
            self.aircraft.request_emergency_descend(target_altitude)
        else:
            target_altitude = self.aircraft.own_data.altitude + 2000
            self.aircraft.request_emergency_climb(target_altitude)


# =============================================================================
# DEMO
# =============================================================================


def demo_python_statemachine():
    """Demo the python-statemachine implementation"""
    print("=== Python-StateMachine Implementation Demo ===\n")

    # Create aircraft with TCAS
    aircraft = Aircraft("UAL123", 10000)
    tcas = CollisionAvoidanceSystem(aircraft)

    print(
        f"Initial state - Aircraft: {aircraft.get_flight_phase().value}, TCAS: {tcas.get_threat_level().value}"
    )

    # Normal flight operations
    print("\n--- Normal Flight Operations ---")
    aircraft.request_climb(11000)
    print(f"Aircraft state: {aircraft.get_flight_phase().value}")
    aircraft.complete_maneuver()  # -> recovering
    aircraft.complete_maneuver()  # -> normal
    print(f"Aircraft state: {aircraft.get_flight_phase().value}")

    # TCAS operations
    print("\n--- TCAS Operations ---")
    traffic = TrafficData(3.0, -200, 100, 90, 12)
    tcas.update_traffic(traffic)
    print(f"TCAS state: {tcas.get_threat_level().value}")
    print(f"Aircraft state: {aircraft.get_flight_phase().value}")

    # Critical threat
    print("\n--- Critical Threat ---")
    critical_traffic = TrafficData(0.2, 100, 200, 0, 4)
    tcas.update_traffic(critical_traffic)
    print(f"TCAS state: {tcas.get_threat_level().value}")
    print(f"Aircraft state: {aircraft.get_flight_phase().value}")

    # Recovery
    print("\n--- Recovery ---")
    tcas.maneuver_complete()  # emergency -> recovery
    tcas.maneuver_complete()  # recovery -> normal
    tcas.clear_traffic()
    print(
        f"Final - Aircraft: {aircraft.get_flight_phase().value}, TCAS: {tcas.get_threat_level().value}"
    )


if __name__ == "__main__":
    demo_python_statemachine()
