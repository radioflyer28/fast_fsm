"""
Aircraft implementation using the fast_fsm library for benchmarking.
This demonstrates the performance of our improved FSM with logging and condition system.
"""

from fast_fsm.core import StateMachine, State, Condition
from enum import Enum
from typing import Optional
from dataclasses import dataclass


class ThreatLevel(Enum):
    NONE = "none"
    TRAFFIC_ADVISORY = "traffic_advisory"  # TA
    RESOLUTION_ADVISORY = "resolution_advisory"  # RA
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
    """Represents another aircraft's position and movement data"""

    distance: float  # nautical miles
    altitude_difference: float  # feet (positive = other aircraft is higher)
    closing_rate: float  # knots (positive = approaching)
    bearing: float  # degrees
    time_to_closest_approach: float  # seconds


@dataclass(slots=True)
class OwnAircraftData:
    """Represents our aircraft's current state"""

    altitude: float  # feet
    vertical_speed: float  # feet per minute
    airspeed: float  # knots
    heading: float  # degrees


# Condition classes for flight control
class CanManeuverCondition(Condition):
    """Check if aircraft can perform maneuvers"""

    __slots__ = ()

    def __init__(self):
        super().__init__("can_maneuver", "Aircraft is not currently maneuvering")

    def check(self, **kwargs) -> bool:
        aircraft = kwargs.get("aircraft")
        if aircraft is None:
            return False
        return aircraft.active_maneuver == ManeuverType.NONE


class IsEmergencyCondition(Condition):
    """Check if aircraft is in emergency state"""

    __slots__ = ()

    def __init__(self):
        super().__init__("is_emergency", "Aircraft is in emergency state")

    def check(self, **kwargs) -> bool:
        aircraft = kwargs.get("aircraft")
        if aircraft is None:
            return False
        return aircraft.get_flight_phase() == FlightPhase.EMERGENCY


# =============================================================================
# AIRCRAFT FLIGHT STATE MACHINE
# =============================================================================


class Aircraft:
    """
    Aircraft class using fast_fsm for managing flight states and maneuvers
    """

    __slots__ = ("call_sign", "own_data", "active_maneuver", "_fsm")

    def __init__(self, call_sign: str, altitude: float = 10000) -> None:
        self.call_sign = call_sign
        self.own_data = OwnAircraftData(
            altitude=altitude, vertical_speed=0, airspeed=250, heading=0
        )
        self.active_maneuver = ManeuverType.NONE

        # Create states
        normal_state = State("normal")
        maneuvering_state = State("maneuvering")
        emergency_state = State("emergency")
        recovering_state = State("recovering")

        # Create state machine
        self._fsm = StateMachine(normal_state, name=f"Aircraft-{call_sign}")
        self._fsm.add_state(maneuvering_state)
        self._fsm.add_state(emergency_state)
        self._fsm.add_state(recovering_state)

        # Add transitions with conditions
        can_maneuver = CanManeuverCondition()

        # Normal flight transitions
        self._fsm.add_transition("request_climb", "normal", "maneuvering", can_maneuver)
        self._fsm.add_transition(
            "request_descend", "normal", "maneuvering", can_maneuver
        )
        self._fsm.add_transition("request_emergency_climb", "normal", "emergency")
        self._fsm.add_transition("request_emergency_descend", "normal", "emergency")

        # Maneuvering transitions
        self._fsm.add_transition("complete_maneuver", "maneuvering", "normal")
        self._fsm.add_transition("request_emergency_climb", "maneuvering", "emergency")
        self._fsm.add_transition(
            "request_emergency_descend", "maneuvering", "emergency"
        )

        # Emergency transitions
        self._fsm.add_transition("complete_maneuver", "emergency", "recovering")

        # Recovery transitions
        self._fsm.add_transition("complete_maneuver", "recovering", "normal")

    def get_flight_phase(self) -> FlightPhase:
        """Get current flight phase"""
        state_to_phase = {
            "normal": FlightPhase.NORMAL,
            "maneuvering": FlightPhase.MANEUVERING,
            "emergency": FlightPhase.EMERGENCY,
            "recovering": FlightPhase.RECOVERING,
        }
        return state_to_phase.get(self._fsm.current_state.name, FlightPhase.NORMAL)

    # Flight control commands
    def request_climb(self, rate: float = 1000) -> bool:
        """Request climb maneuver"""
        result = self._fsm.trigger("request_climb", aircraft=self, rate=rate)
        if result.success:
            self.active_maneuver = ManeuverType.CLIMB
            self.own_data.vertical_speed = rate
        return result.success

    def request_descend(self, rate: float = 1000) -> bool:
        """Request descent maneuver"""
        result = self._fsm.trigger("request_descend", aircraft=self, rate=rate)
        if result.success:
            self.active_maneuver = ManeuverType.DESCEND
            self.own_data.vertical_speed = -rate
        return result.success

    def request_emergency_climb(self, rate: float = 2500) -> bool:
        """Request emergency climb"""
        result = self._fsm.trigger("request_emergency_climb", aircraft=self, rate=rate)
        if result.success:
            self.active_maneuver = ManeuverType.EMERGENCY_CLIMB
            self.own_data.vertical_speed = rate
        return result.success

    def request_emergency_descend(self, rate: float = 2500) -> bool:
        """Request emergency descent"""
        result = self._fsm.trigger(
            "request_emergency_descend", aircraft=self, rate=rate
        )
        if result.success:
            self.active_maneuver = ManeuverType.EMERGENCY_DESCEND
            self.own_data.vertical_speed = -rate
        return result.success

    def request_level_off(self) -> bool:
        """Request level off"""
        self.active_maneuver = ManeuverType.LEVEL_OFF
        self.own_data.vertical_speed = 0
        return True

    def complete_maneuver(self) -> None:
        """Signal that current maneuver is complete"""
        result = self._fsm.trigger("complete_maneuver", aircraft=self)
        if result.success:
            self.active_maneuver = ManeuverType.NONE
            self.own_data.vertical_speed = 0


# =============================================================================
# COLLISION AVOIDANCE STATE MACHINE
# =============================================================================


class ThreatAssessmentCondition(Condition):
    """Assess threat level based on traffic data"""

    __slots__ = ()

    def __init__(self):
        super().__init__("threat_assessment", "Assess threat level from traffic data")

    def check(self, **kwargs) -> bool:
        traffic = kwargs.get("traffic")
        if not traffic:
            return False

        # Calculate threat level based on distance and time to closest approach
        if traffic.distance < 1.0 and traffic.time_to_closest_approach < 15:
            return True  # Resolution Advisory needed
        elif traffic.distance < 2.0 and traffic.time_to_closest_approach < 30:
            return True  # Traffic Advisory
        return False


class CollisionAvoidanceSystem:
    """
    TCAS-like collision avoidance system using fast_fsm
    """

    __slots__ = ("aircraft", "threat_level", "traffic_data", "_fsm")

    def __init__(self, aircraft: Aircraft) -> None:
        self.aircraft = aircraft
        self.threat_level = ThreatLevel.NONE
        self.traffic_data: Optional[TrafficData] = None

        # Create states
        clear_state = State("clear")
        advisory_state = State("advisory")
        resolution_state = State("resolution")

        # Create state machine
        self._fsm = StateMachine(clear_state, name=f"TCAS-{aircraft.call_sign}")
        self._fsm.add_state(advisory_state)
        self._fsm.add_state(resolution_state)

        # Add transitions
        threat_condition = ThreatAssessmentCondition()

        self._fsm.add_transition(
            "update_traffic", "clear", "advisory", threat_condition
        )
        self._fsm.add_transition(
            "update_traffic", "advisory", "resolution", threat_condition
        )
        self._fsm.add_transition("clear_traffic", ["advisory", "resolution"], "clear")
        self._fsm.add_transition("maneuver_complete", "resolution", "advisory")

    def update_traffic(self, traffic: TrafficData) -> None:
        """Update traffic information and assess threat"""
        self.traffic_data = traffic
        result = self._fsm.trigger("update_traffic", traffic=traffic, tcas=self)

        if result.success:
            current_state = self._fsm.current_state.name
            if current_state == "advisory":
                self.threat_level = ThreatLevel.TRAFFIC_ADVISORY
            elif current_state == "resolution":
                self.threat_level = ThreatLevel.RESOLUTION_ADVISORY
                self._issue_resolution_advisory()

    def _issue_resolution_advisory(self) -> None:
        """Issue resolution advisory to aircraft"""
        if not self.traffic_data:
            return

        # Simple logic: if other aircraft is higher, we descend; if lower, we climb
        if self.traffic_data.altitude_difference > 0:
            self.aircraft.request_emergency_descend(2500)
        else:
            self.aircraft.request_emergency_climb(2500)

    def maneuver_complete(self) -> None:
        """Signal that avoidance maneuver is complete"""
        result = self._fsm.trigger("maneuver_complete", tcas=self)
        if result.success:
            self.threat_level = ThreatLevel.TRAFFIC_ADVISORY

    def clear_traffic(self) -> None:
        """Clear traffic threat"""
        result = self._fsm.trigger("clear_traffic", tcas=self)
        if result.success:
            self.threat_level = ThreatLevel.NONE
            self.traffic_data = None
