from abc import ABC, abstractmethod
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


# =============================================================================
# AIRCRAFT FLIGHT STATE MACHINE
# =============================================================================


class Aircraft:
    """
    Aircraft class with its own FSM for managing flight states and maneuvers
    """

    __slots__ = ("call_sign", "own_data", "_flight_state", "active_maneuver")

    def __init__(self, call_sign: str, altitude: float = 10000) -> None:
        self.call_sign = call_sign
        self.own_data = OwnAircraftData(
            altitude=altitude, vertical_speed=0, airspeed=250, heading=0
        )
        self._flight_state: Optional["FlightState"] = None
        self.transition_to(NormalFlightState())
        self.active_maneuver = ManeuverType.NONE

    def transition_to(self, state: "FlightState") -> None:
        """Transition to a new flight state"""
        print(f"{self.call_sign} Aircraft: Transitioning to {type(state).__name__}")
        self._flight_state = state
        self._flight_state.context = self

    def get_flight_phase(self) -> FlightPhase:
        """Get current flight phase"""
        return self._flight_state.get_flight_phase()

    # Flight control commands (called by TCAS or pilot)
    def request_climb(self, rate: float = 1000) -> bool:
        """Request climb maneuver"""
        return self._flight_state.request_climb(rate)

    def request_descend(self, rate: float = 1000) -> bool:
        """Request descent maneuver"""
        return self._flight_state.request_descend(rate)

    def request_emergency_climb(self, rate: float = 2500) -> bool:
        """Request emergency climb"""
        return self._flight_state.request_emergency_climb(rate)

    def request_emergency_descend(self, rate: float = 2500) -> bool:
        """Request emergency descent"""
        return self._flight_state.request_emergency_descend(rate)

    def request_level_off(self) -> bool:
        """Request level off"""
        return self._flight_state.request_level_off()

    def complete_maneuver(self) -> None:
        """Signal that current maneuver is complete"""
        self._flight_state.complete_maneuver()

    def abort_maneuver(self) -> bool:
        """Abort current maneuver"""
        return self._flight_state.abort_maneuver()

    # Status queries
    def is_maneuvering(self) -> bool:
        """Check if aircraft is currently maneuvering"""
        return self.get_flight_phase() in [
            FlightPhase.MANEUVERING,
            FlightPhase.EMERGENCY,
        ]

    def can_accept_maneuver(self) -> bool:
        """Check if aircraft can accept new maneuver commands"""
        return self._flight_state.can_accept_maneuver()

    def get_current_altitude(self) -> float:
        """Get current altitude"""
        return self.own_data.altitude

    def get_vertical_speed(self) -> float:
        """Get current vertical speed"""
        return self.own_data.vertical_speed

    # Internal flight control methods
    def _execute_climb(self, rate: float) -> None:
        """Internal method to execute climb"""
        self.own_data.vertical_speed = rate
        self.active_maneuver = (
            ManeuverType.EMERGENCY_CLIMB if rate > 2000 else ManeuverType.CLIMB
        )
        print(f"{self.call_sign}: Executing climb at {rate} fpm")

    def _execute_descend(self, rate: float) -> None:
        """Internal method to execute descent"""
        self.own_data.vertical_speed = -rate
        self.active_maneuver = (
            ManeuverType.EMERGENCY_DESCEND if rate > 2000 else ManeuverType.DESCEND
        )
        print(f"{self.call_sign}: Executing descent at {rate} fpm")

    def _execute_level_off(self) -> None:
        """Internal method to level off"""
        self.own_data.vertical_speed = 0
        self.active_maneuver = ManeuverType.LEVEL_OFF
        print(f"{self.call_sign}: Leveling off at {self.own_data.altitude} ft")


class FlightState(ABC):
    """Abstract base class for aircraft flight states"""

    @property
    def context(self) -> Aircraft:
        return self._context

    @context.setter
    def context(self, context: Aircraft) -> None:
        self._context = context

    @abstractmethod
    def get_flight_phase(self) -> FlightPhase:
        pass

    @abstractmethod
    def request_climb(self, rate: float) -> bool:
        pass

    @abstractmethod
    def request_descend(self, rate: float) -> bool:
        pass

    @abstractmethod
    def request_emergency_climb(self, rate: float) -> bool:
        pass

    @abstractmethod
    def request_emergency_descend(self, rate: float) -> bool:
        pass

    @abstractmethod
    def request_level_off(self) -> bool:
        pass

    @abstractmethod
    def complete_maneuver(self) -> None:
        pass

    @abstractmethod
    def abort_maneuver(self) -> bool:
        pass

    @abstractmethod
    def can_accept_maneuver(self) -> bool:
        pass


class NormalFlightState(FlightState):
    """Normal cruise flight state"""

    def get_flight_phase(self) -> FlightPhase:
        return FlightPhase.NORMAL

    def request_climb(self, rate: float) -> bool:
        if rate <= 0:
            print(f"{self.context.call_sign}: Invalid climb rate: {rate}")
            return False

        self.context._execute_climb(rate)
        self.context.transition_to(ManeuveringState())
        return True

    def request_descend(self, rate: float) -> bool:
        if rate <= 0:
            print(f"{self.context.call_sign}: Invalid descent rate: {rate}")
            return False

        self.context._execute_descend(rate)
        self.context.transition_to(ManeuveringState())
        return True

    def request_emergency_climb(self, rate: float) -> bool:
        if rate <= 0:
            print(f"{self.context.call_sign}: Invalid emergency climb rate: {rate}")
            return False

        print(f"{self.context.call_sign}: EMERGENCY CLIMB AUTHORIZED")
        self.context._execute_climb(rate)
        self.context.transition_to(EmergencyManeuverState())
        return True

    def request_emergency_descend(self, rate: float) -> bool:
        if rate <= 0:
            print(f"{self.context.call_sign}: Invalid emergency descent rate: {rate}")
            return False

        print(f"{self.context.call_sign}: EMERGENCY DESCENT AUTHORIZED")
        self.context._execute_descend(rate)
        self.context.transition_to(EmergencyManeuverState())
        return True

    def request_level_off(self) -> bool:
        # Already level in normal flight
        print(f"{self.context.call_sign}: Already in level flight")
        return True

    def complete_maneuver(self) -> None:
        print(f"{self.context.call_sign}: No active maneuver to complete")

    def abort_maneuver(self) -> bool:
        print(f"{self.context.call_sign}: No active maneuver to abort")
        return True

    def can_accept_maneuver(self) -> bool:
        return True


class ManeuveringState(FlightState):
    """Aircraft is performing a standard maneuver"""

    def get_flight_phase(self) -> FlightPhase:
        return FlightPhase.MANEUVERING

    def request_climb(self, rate: float) -> bool:
        if rate <= 0:
            return False

        print(f"{self.context.call_sign}: Adjusting to climb at {rate} fpm")
        self.context._execute_climb(rate)
        return True

    def request_descend(self, rate: float) -> bool:
        if rate <= 0:
            return False

        print(f"{self.context.call_sign}: Adjusting to descend at {rate} fpm")
        self.context._execute_descend(rate)
        return True

    def request_emergency_climb(self, rate: float) -> bool:
        if rate <= 0:
            return False

        print(f"{self.context.call_sign}: ESCALATING TO EMERGENCY CLIMB")
        self.context._execute_climb(rate)
        self.context.transition_to(EmergencyManeuverState())
        return True

    def request_emergency_descend(self, rate: float) -> bool:
        if rate <= 0:
            return False

        print(f"{self.context.call_sign}: ESCALATING TO EMERGENCY DESCENT")
        self.context._execute_descend(rate)
        self.context.transition_to(EmergencyManeuverState())
        return True

    def request_level_off(self) -> bool:
        self.context._execute_level_off()
        self.context.transition_to(RecoveringState())
        return True

    def complete_maneuver(self) -> None:
        print(f"{self.context.call_sign}: Standard maneuver complete")
        self.context._execute_level_off()
        self.context.transition_to(RecoveringState())

    def abort_maneuver(self) -> bool:
        print(f"{self.context.call_sign}: Aborting maneuver - leveling off")
        self.context._execute_level_off()
        self.context.transition_to(RecoveringState())
        return True

    def can_accept_maneuver(self) -> bool:
        return True  # Can adjust ongoing maneuver


class EmergencyManeuverState(FlightState):
    """Aircraft is performing an emergency maneuver (higher priority)"""

    def get_flight_phase(self) -> FlightPhase:
        return FlightPhase.EMERGENCY

    def request_climb(self, rate: float) -> bool:
        # Can only adjust emergency maneuver in same direction or increase intensity
        if self.context.own_data.vertical_speed > 0:  # Already climbing
            if rate > abs(self.context.own_data.vertical_speed):
                print(
                    f"{self.context.call_sign}: Increasing emergency climb to {rate} fpm"
                )
                self.context._execute_climb(rate)
                return True
        print(f"{self.context.call_sign}: Cannot change emergency maneuver direction")
        return False

    def request_descend(self, rate: float) -> bool:
        # Can only adjust emergency maneuver in same direction or increase intensity
        if self.context.own_data.vertical_speed < 0:  # Already descending
            if rate > abs(self.context.own_data.vertical_speed):
                print(
                    f"{self.context.call_sign}: Increasing emergency descent to {rate} fpm"
                )
                self.context._execute_descend(rate)
                return True
        print(f"{self.context.call_sign}: Cannot change emergency maneuver direction")
        return False

    def request_emergency_climb(self, rate: float) -> bool:
        if rate <= 0:
            return False

        print(f"{self.context.call_sign}: Adjusting emergency climb to {rate} fpm")
        self.context._execute_climb(rate)
        return True

    def request_emergency_descend(self, rate: float) -> bool:
        if rate <= 0:
            return False

        print(f"{self.context.call_sign}: Adjusting emergency descent to {rate} fpm")
        self.context._execute_descend(rate)
        return True

    def request_level_off(self) -> bool:
        print(f"{self.context.call_sign}: Emergency maneuver complete - leveling off")
        self.context._execute_level_off()
        self.context.transition_to(RecoveringState())
        return True

    def complete_maneuver(self) -> None:
        print(f"{self.context.call_sign}: Emergency maneuver complete")
        self.context._execute_level_off()
        self.context.transition_to(RecoveringState())

    def abort_maneuver(self) -> bool:
        # Emergency maneuvers should not be aborted easily
        print(
            f"{self.context.call_sign}: WARNING: Attempting to abort emergency maneuver"
        )
        print(f"{self.context.call_sign}: Emergency abort authorized - leveling off")
        self.context._execute_level_off()
        self.context.transition_to(RecoveringState())
        return True

    def can_accept_maneuver(self) -> bool:
        return False  # Emergency maneuvers have restricted acceptance


class RecoveringState(FlightState):
    """Aircraft is recovering from a maneuver and stabilizing"""

    def get_flight_phase(self) -> FlightPhase:
        return FlightPhase.RECOVERING

    def request_climb(self, rate: float) -> bool:
        print(f"{self.context.call_sign}: Recovery complete - initiating new climb")
        if rate <= 0:
            return False

        self.context._execute_climb(rate)
        self.context.transition_to(ManeuveringState())
        return True

    def request_descend(self, rate: float) -> bool:
        print(f"{self.context.call_sign}: Recovery complete - initiating new descent")
        if rate <= 0:
            return False

        self.context._execute_descend(rate)
        self.context.transition_to(ManeuveringState())
        return True

    def request_emergency_climb(self, rate: float) -> bool:
        print(f"{self.context.call_sign}: Interrupting recovery for emergency climb")
        if rate <= 0:
            return False

        self.context._execute_climb(rate)
        self.context.transition_to(EmergencyManeuverState())
        return True

    def request_emergency_descend(self, rate: float) -> bool:
        print(f"{self.context.call_sign}: Interrupting recovery for emergency descent")
        if rate <= 0:
            return False

        self.context._execute_descend(rate)
        self.context.transition_to(EmergencyManeuverState())
        return True

    def request_level_off(self) -> bool:
        print(f"{self.context.call_sign}: Continuing level flight")
        return True

    def complete_maneuver(self) -> None:
        print(
            f"{self.context.call_sign}: Recovery complete - returning to normal flight"
        )
        self.context.active_maneuver = ManeuverType.NONE
        self.context.transition_to(NormalFlightState())

    def abort_maneuver(self) -> bool:
        print(
            f"{self.context.call_sign}: Recovery complete - returning to normal flight"
        )
        self.context.active_maneuver = ManeuverType.NONE
        self.context.transition_to(NormalFlightState())
        return True

    def can_accept_maneuver(self) -> bool:
        return True  # Can accept new maneuvers after brief stabilization


# =============================================================================
# COLLISION AVOIDANCE STATE MACHINE (Updated to work with Aircraft FSM)
# =============================================================================


class CollisionAvoidanceSystem:
    """
    TCAS system that commands the aircraft through its flight state machine
    """

    __slots__ = ("aircraft", "current_threat", "_state")

    def __init__(self, aircraft: Aircraft) -> None:
        self.aircraft = aircraft
        self.current_threat: Optional[TrafficData] = None
        self._state: Optional["AvoidanceState"] = None
        self.transition_to(NormalFlightState_TCAS())

    def transition_to(self, state: "AvoidanceState") -> None:
        """Transition to a new avoidance state"""
        print(f"\n{self.aircraft.call_sign} TCAS: Entering {type(state).__name__}")
        self._state = state
        self._state.context = self
        self._state.aircraft = self.aircraft

    def get_threat_level(self) -> ThreatLevel:
        """Get current threat level"""
        return self._state.get_threat_level()

    def update_traffic(self, traffic_data: TrafficData) -> None:
        """Update with new traffic information"""
        self.current_threat = traffic_data
        self._state.update_traffic(traffic_data)

    def clear_traffic(self) -> None:
        """Clear traffic threat"""
        self.current_threat = None
        self._state.clear_traffic()

    def pilot_compliance_confirmed(self) -> None:
        """Pilot confirms maneuver compliance"""
        self._state.pilot_compliance_confirmed()

    def maneuver_complete(self) -> None:
        """Signal that maneuver is complete"""
        self._state.maneuver_complete()


class AvoidanceState(ABC):
    """Abstract base class for collision avoidance states"""

    @property
    def context(self) -> CollisionAvoidanceSystem:
        return self._context

    @context.setter
    def context(self, context: CollisionAvoidanceSystem) -> None:
        self._context = context

    @property
    def aircraft(self) -> Aircraft:
        return self._aircraft

    @aircraft.setter
    def aircraft(self, aircraft: Aircraft) -> None:
        self._aircraft = aircraft

    @abstractmethod
    def get_threat_level(self) -> ThreatLevel:
        pass

    @abstractmethod
    def update_traffic(self, traffic_data: TrafficData) -> None:
        pass

    @abstractmethod
    def clear_traffic(self) -> None:
        pass

    @abstractmethod
    def pilot_compliance_confirmed(self) -> None:
        pass

    @abstractmethod
    def maneuver_complete(self) -> None:
        pass

    def _assess_threat_level(self, traffic_data: TrafficData) -> ThreatLevel:
        """Assess threat level based on traffic data"""
        if traffic_data.distance > 6.0:  # > 6 nm
            return ThreatLevel.NONE
        elif traffic_data.distance > 2.5:  # 2.5-6 nm
            if traffic_data.time_to_closest_approach < 40:
                return ThreatLevel.TRAFFIC_ADVISORY
        elif traffic_data.distance > 0.5:  # 0.5-2.5 nm
            if traffic_data.time_to_closest_approach < 25:
                return ThreatLevel.RESOLUTION_ADVISORY
        else:  # < 0.5 nm
            return ThreatLevel.CRITICAL

        return ThreatLevel.NONE


class NormalFlightState_TCAS(AvoidanceState):
    """Normal flight with no traffic threats"""

    def get_threat_level(self) -> ThreatLevel:
        return ThreatLevel.NONE

    def update_traffic(self, traffic_data: TrafficData) -> None:
        threat_level = self._assess_threat_level(traffic_data)

        if threat_level == ThreatLevel.TRAFFIC_ADVISORY:
            print("TCAS: TRAFFIC DETECTED")
            self.context.transition_to(TrafficAdvisoryState_TCAS())
        elif threat_level == ThreatLevel.RESOLUTION_ADVISORY:
            print("TCAS: RESOLUTION ADVISORY")
            self.context.transition_to(ResolutionAdvisoryState_TCAS())
        elif threat_level == ThreatLevel.CRITICAL:
            print("TCAS: CRITICAL THREAT")
            self.context.transition_to(CriticalAvoidanceState_TCAS())

    def clear_traffic(self) -> None:
        print("TCAS: No traffic to clear")

    def pilot_compliance_confirmed(self) -> None:
        pass

    def maneuver_complete(self) -> None:
        pass


class TrafficAdvisoryState_TCAS(AvoidanceState):
    """Traffic Advisory - monitoring only"""

    def get_threat_level(self) -> ThreatLevel:
        return ThreatLevel.TRAFFIC_ADVISORY

    def update_traffic(self, traffic_data: TrafficData) -> None:
        threat_level = self._assess_threat_level(traffic_data)

        print(f"TCAS TA: Traffic at {traffic_data.distance:.1f} nm")

        if threat_level == ThreatLevel.RESOLUTION_ADVISORY:
            self.context.transition_to(ResolutionAdvisoryState_TCAS())
        elif threat_level == ThreatLevel.CRITICAL:
            self.context.transition_to(CriticalAvoidanceState_TCAS())
        elif threat_level == ThreatLevel.NONE:
            self.context.transition_to(NormalFlightState_TCAS())

    def clear_traffic(self) -> None:
        print("TCAS: Traffic cleared")
        self.context.transition_to(NormalFlightState_TCAS())

    def pilot_compliance_confirmed(self) -> None:
        pass

    def maneuver_complete(self) -> None:
        pass


class ResolutionAdvisoryState_TCAS(AvoidanceState):
    """Resolution Advisory - active avoidance required"""

    def __init__(self):
        self.advisory_issued = False

    def get_threat_level(self) -> ThreatLevel:
        return ThreatLevel.RESOLUTION_ADVISORY

    def update_traffic(self, traffic_data: TrafficData) -> None:
        threat_level = self._assess_threat_level(traffic_data)

        if not self.advisory_issued:
            self._issue_resolution_advisory(traffic_data)
            self.advisory_issued = True

        if threat_level == ThreatLevel.CRITICAL:
            self.context.transition_to(CriticalAvoidanceState_TCAS())
        elif threat_level == ThreatLevel.NONE:
            if self.aircraft.is_maneuvering():
                print("TCAS: Threat reduced but continuing maneuver")
            else:
                self.context.transition_to(NormalFlightState_TCAS())

    def _issue_resolution_advisory(self, traffic_data: TrafficData) -> None:
        """Issue RA and command aircraft through its FSM"""
        if traffic_data.altitude_difference > 0:
            print("TCAS RA: DESCEND")
            success = self.aircraft.request_descend(1500)
            if not success:
                print("TCAS: Aircraft unable to accept descent command")
        else:
            print("TCAS RA: CLIMB")
            success = self.aircraft.request_climb(1500)
            if not success:
                print("TCAS: Aircraft unable to accept climb command")

    def clear_traffic(self) -> None:
        if self.aircraft.is_maneuvering():
            print("TCAS: Letting aircraft complete current maneuver")
        else:
            self.context.transition_to(NormalFlightState_TCAS())

    def pilot_compliance_confirmed(self) -> None:
        print("TCAS RA: Compliance confirmed")

    def maneuver_complete(self) -> None:
        print("TCAS RA: Maneuver complete")
        self.aircraft.complete_maneuver()
        if self.context.current_threat is None:
            self.context.transition_to(NormalFlightState_TCAS())


class CriticalAvoidanceState_TCAS(AvoidanceState):
    """Critical avoidance - emergency maneuvers"""

    def __init__(self):
        self.emergency_issued = False

    def get_threat_level(self) -> ThreatLevel:
        return ThreatLevel.CRITICAL

    def update_traffic(self, traffic_data: TrafficData) -> None:
        if not self.emergency_issued:
            self._issue_emergency_advisory(traffic_data)
            self.emergency_issued = True

        if traffic_data.distance > 3.0:
            self.context.transition_to(ResolutionAdvisoryState_TCAS())

    def _issue_emergency_advisory(self, traffic_data: TrafficData) -> None:
        """Issue emergency RA and command aircraft"""
        if traffic_data.altitude_difference > 0:
            print("TCAS CRITICAL: EMERGENCY DESCENT")
            success = self.aircraft.request_emergency_descend(2500)
        else:
            print("TCAS CRITICAL: EMERGENCY CLIMB")
            success = self.aircraft.request_emergency_climb(2500)

        if not success:
            print("TCAS: ALERT - Aircraft unable to execute emergency maneuver!")

    def clear_traffic(self) -> None:
        if self.aircraft.is_maneuvering():
            self.aircraft.complete_maneuver()
        self.context.transition_to(NormalFlightState_TCAS())

    def pilot_compliance_confirmed(self) -> None:
        print("TCAS CRITICAL: Emergency compliance confirmed")

    def maneuver_complete(self) -> None:
        print("TCAS: Emergency maneuver complete")
        self.aircraft.complete_maneuver()
        if self.context.current_threat is None:
            self.context.transition_to(NormalFlightState_TCAS())


# =============================================================================
# SIMULATION
# =============================================================================


def simulate_dual_state_machines():
    """Simulate collision avoidance with both Aircraft FSM and TCAS FSM"""

    print("=== DUAL STATE MACHINE SIMULATION ===")

    # Create aircraft with its own FSM
    aircraft = Aircraft("United 123", altitude=10000)
    print(f"Aircraft Flight State: {aircraft.get_flight_phase().value}")

    # Create TCAS system
    tcas = CollisionAvoidanceSystem(aircraft)

    # Test normal maneuver first
    print("\n--- Testing Normal Aircraft Maneuver ---")
    aircraft.request_climb(1000)
    print(f"Aircraft Flight State: {aircraft.get_flight_phase().value}")
    aircraft.complete_maneuver()
    print(f"Aircraft Flight State: {aircraft.get_flight_phase().value}")
    aircraft.complete_maneuver()  # Complete recovery
    print(f"Aircraft Flight State: {aircraft.get_flight_phase().value}")

    # Now test TCAS command during normal operations
    print("\n--- TCAS Commands During Normal Flight ---")

    # Traffic detected - RA triggered
    traffic = TrafficData(
        distance=2.0,
        altitude_difference=-300,  # traffic below
        closing_rate=180,
        bearing=45,
        time_to_closest_approach=20,
    )
    tcas.update_traffic(traffic)
    print(f"Aircraft Flight State: {aircraft.get_flight_phase().value}")
    print(f"TCAS Threat Level: {tcas.get_threat_level().value}")

    # Traffic becomes critical
    critical_traffic = TrafficData(
        distance=0.3,
        altitude_difference=-100,
        closing_rate=200,
        bearing=45,
        time_to_closest_approach=8,
    )
    tcas.update_traffic(critical_traffic)
    print(f"Aircraft Flight State: {aircraft.get_flight_phase().value}")
    print(f"TCAS Threat Level: {tcas.get_threat_level().value}")

    # Try to issue conflicting command during emergency
    print("\n--- Attempting Conflicting Command During Emergency ---")
    success = aircraft.request_descend(1000)  # Try to descend while emergency climbing
    print(f"Command accepted: {success}")

    # Complete emergency maneuver
    print("\n--- Completing Emergency Maneuver ---")
    tcas.maneuver_complete()
    print(f"Aircraft Flight State: {aircraft.get_flight_phase().value}")

    # Clear traffic
    tcas.clear_traffic()
    print(f"Aircraft Flight State: {aircraft.get_flight_phase().value}")
    print(f"TCAS Threat Level: {tcas.get_threat_level().value}")


if __name__ == "__main__":
    simulate_dual_state_machines()
