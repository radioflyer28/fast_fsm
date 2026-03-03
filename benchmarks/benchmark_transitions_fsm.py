"""
Aircraft Collision Avoidance System using the 'transitions' library
This is a port of my_fsm.py to use the transitions state machine library
"""

from transitions import Machine
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
# AIRCRAFT FLIGHT STATE MACHINE (using transitions library)
# =============================================================================


class Aircraft:
    """
    Aircraft class with FSM using transitions library for managing flight states
    """

    # Note: Can't use __slots__ with transitions library as it needs to dynamically add attributes

    # Define states
    states = ["normal", "maneuvering", "emergency", "recovering"]

    def __init__(self, call_sign: str, altitude: float = 10000) -> None:
        self.call_sign = call_sign
        self.own_data = OwnAircraftData(
            altitude=altitude, vertical_speed=0, airspeed=250, heading=0
        )
        self.active_maneuver = ManeuverType.NONE

        # Initialize the state machine
        self.machine = Machine(
            model=self,
            states=Aircraft.states,
            initial="normal",
            auto_transitions=False,
            send_event=True,
            finalize_event="finalize_transition",
        )

        # Define transitions with conditions and callbacks
        self.machine.add_transition(
            trigger="do_climb",
            source="normal",
            dest="maneuvering",
            conditions=["is_valid_rate"],
            before="execute_climb",
        )

        self.machine.add_transition(
            trigger="do_descend",
            source="normal",
            dest="maneuvering",
            conditions=["is_valid_rate"],
            before="execute_descend",
        )

        self.machine.add_transition(
            trigger="do_emergency_climb",
            source=["normal", "maneuvering"],
            dest="emergency",
            conditions=["is_valid_rate"],
            before="execute_emergency_climb",
        )

        self.machine.add_transition(
            trigger="do_emergency_descend",
            source=["normal", "maneuvering"],
            dest="emergency",
            conditions=["is_valid_rate"],
            before="execute_emergency_descend",
        )

        self.machine.add_transition(
            trigger="do_level_off",
            source=["maneuvering", "emergency"],
            dest="recovering",
            before="execute_level_off",
        )

        self.machine.add_transition(
            trigger="complete_maneuver",
            source=["maneuvering", "emergency"],
            dest="recovering",
            before="execute_level_off",
        )

        self.machine.add_transition(
            trigger="finish_recovery",
            source="recovering",
            dest="normal",
            before="reset_maneuver",
        )

        # Adjust maneuvers within same state
        self.machine.add_transition(
            trigger="adjust_climb",
            source="maneuvering",
            dest="maneuvering",
            conditions=["is_valid_rate"],
            before="execute_climb",
        )

        self.machine.add_transition(
            trigger="adjust_descend",
            source="maneuvering",
            dest="maneuvering",
            conditions=["is_valid_rate"],
            before="execute_descend",
        )

        self.machine.add_transition(
            trigger="adjust_emergency_climb",
            source="emergency",
            dest="emergency",
            conditions=["is_valid_rate", "can_adjust_emergency_climb"],
            before="execute_emergency_climb",
        )

        self.machine.add_transition(
            trigger="adjust_emergency_descend",
            source="emergency",
            dest="emergency",
            conditions=["is_valid_rate", "can_adjust_emergency_descend"],
            before="execute_emergency_descend",
        )

        # Abort transitions
        self.machine.add_transition(
            trigger="abort_maneuver",
            source=["maneuvering", "emergency"],
            dest="recovering",
            before="execute_level_off",
        )

        # Recovery transitions to new maneuvers
        self.machine.add_transition(
            trigger="do_climb",
            source="recovering",
            dest="maneuvering",
            conditions=["is_valid_rate"],
            before="execute_climb",
        )

        self.machine.add_transition(
            trigger="do_descend",
            source="recovering",
            dest="maneuvering",
            conditions=["is_valid_rate"],
            before="execute_descend",
        )

    def finalize_transition(self, event):
        """Called after each state transition"""
        print(f"{self.call_sign} Aircraft: Transitioning to {self.state}")

    # Condition methods
    def is_valid_rate(self, event):
        """Check if maneuver rate is valid"""
        rate = event.kwargs.get("rate", 0)
        return rate > 0

    def can_adjust_emergency_climb(self, event):
        """Check if can adjust emergency climb"""
        rate = event.kwargs.get("rate", 0)
        return self.own_data.vertical_speed > 0 and rate > abs(
            self.own_data.vertical_speed
        )

    def can_adjust_emergency_descend(self, event):
        """Check if can adjust emergency descend"""
        rate = event.kwargs.get("rate", 0)
        return self.own_data.vertical_speed < 0 and rate > abs(
            self.own_data.vertical_speed
        )

    # Action methods (before callbacks)
    def execute_climb(self, event):
        """Execute climb maneuver"""
        rate = event.kwargs.get("rate", 1000)
        self.own_data.vertical_speed = rate
        self.active_maneuver = ManeuverType.CLIMB
        print(f"{self.call_sign}: Executing climb at {rate} fpm")

    def execute_descend(self, event):
        """Execute descend maneuver"""
        rate = event.kwargs.get("rate", 1000)
        self.own_data.vertical_speed = -rate
        self.active_maneuver = ManeuverType.DESCEND
        print(f"{self.call_sign}: Executing descent at {rate} fpm")

    def execute_emergency_climb(self, event):
        """Execute emergency climb"""
        rate = event.kwargs.get("rate", 2500)
        self.own_data.vertical_speed = rate
        self.active_maneuver = ManeuverType.EMERGENCY_CLIMB
        print(f"{self.call_sign}: Executing EMERGENCY CLIMB at {rate} fpm")

    def execute_emergency_descend(self, event):
        """Execute emergency descend"""
        rate = event.kwargs.get("rate", 2500)
        self.own_data.vertical_speed = -rate
        self.active_maneuver = ManeuverType.EMERGENCY_DESCEND
        print(f"{self.call_sign}: Executing EMERGENCY DESCENT at {rate} fpm")

    def execute_level_off(self, event):
        """Execute level off"""
        self.own_data.vertical_speed = 0
        self.active_maneuver = ManeuverType.LEVEL_OFF
        print(f"{self.call_sign}: Leveling off at {self.own_data.altitude} ft")

    def reset_maneuver(self, event):
        """Reset maneuver to none"""
        self.active_maneuver = ManeuverType.NONE
        print(f"{self.call_sign}: Returning to normal flight")

    # Public interface methods
    def get_flight_phase(self) -> FlightPhase:
        """Get current flight phase"""
        if self.state == "normal":
            return FlightPhase.NORMAL
        elif self.state == "maneuvering":
            return FlightPhase.MANEUVERING
        elif self.state == "emergency":
            return FlightPhase.EMERGENCY
        elif self.state == "recovering":
            return FlightPhase.RECOVERING
        else:
            return FlightPhase.NORMAL

    def request_climb(self, rate: float = 1000) -> bool:
        """Request climb maneuver"""
        try:
            if self.state == "maneuvering":
                return self.adjust_climb(rate=rate)
            else:
                return self.do_climb(rate=rate)
        except:
            return False

    def request_descend(self, rate: float = 1000) -> bool:
        """Request descent maneuver"""
        try:
            if self.state == "maneuvering":
                return self.adjust_descend(rate=rate)
            else:
                return self.do_descend(rate=rate)
        except:
            return False

    def request_emergency_climb(self, rate: float = 2500) -> bool:
        """Request emergency climb"""
        try:
            if self.state == "emergency":
                return self.adjust_emergency_climb(rate=rate)
            else:
                return self.do_emergency_climb(rate=rate)
        except:
            return False

    def request_emergency_descend(self, rate: float = 2500) -> bool:
        """Request emergency descent"""
        try:
            if self.state == "emergency":
                return self.adjust_emergency_descend(rate=rate)
            else:
                return self.do_emergency_descend(rate=rate)
        except:
            return False

    def request_level_off(self) -> bool:
        """Request level off"""
        try:
            if self.state in ["normal", "recovering"]:
                print(f"{self.call_sign}: Already in level flight")
                return True
            return self.do_level_off()
        except:
            return False

    def complete_maneuver_request(self) -> None:
        """Signal that current maneuver is complete"""
        try:
            if self.state in ["maneuvering", "emergency"]:
                self.complete_maneuver()
            elif self.state == "recovering":
                self.finish_recovery()
        except:
            pass

    def abort_maneuver_request(self) -> bool:
        """Abort current maneuver"""
        try:
            if self.state in ["maneuvering", "emergency"]:
                return self.abort_maneuver()
            elif self.state == "recovering":
                return self.finish_recovery()
            return True
        except:
            return False

    # Status queries
    def is_maneuvering(self) -> bool:
        """Check if aircraft is currently maneuvering"""
        return self.state in ["maneuvering", "emergency"]

    def can_accept_maneuver(self) -> bool:
        """Check if aircraft can accept new maneuver commands"""
        return self.state != "emergency"  # Emergency state is more restrictive

    def get_current_altitude(self) -> float:
        """Get current altitude"""
        return self.own_data.altitude

    def get_vertical_speed(self) -> float:
        """Get current vertical speed"""
        return self.own_data.vertical_speed


# =============================================================================
# COLLISION AVOIDANCE STATE MACHINE (using transitions library)
# =============================================================================


class CollisionAvoidanceSystem:
    """
    TCAS system using transitions library
    """

    # Note: Can't use __slots__ with transitions library as it needs to dynamically add attributes

    # Define states
    states = ["normal", "traffic_advisory", "resolution_advisory", "critical_avoidance"]

    def __init__(self, aircraft: Aircraft) -> None:
        self.aircraft = aircraft
        self.current_threat: Optional[TrafficData] = None
        self.advisory_issued = False
        self.emergency_issued = False

        # Initialize the state machine
        self.machine = Machine(
            model=self,
            states=CollisionAvoidanceSystem.states,
            initial="normal",
            auto_transitions=False,
            send_event=True,
            finalize_event="finalize_transition",
        )

        # Define transitions
        self.machine.add_transition(
            trigger="detect_traffic_advisory",
            source="normal",
            dest="traffic_advisory",
            before="enter_traffic_advisory",
        )

        self.machine.add_transition(
            trigger="escalate_to_resolution",
            source=["normal", "traffic_advisory"],
            dest="resolution_advisory",
            before="enter_resolution_advisory",
        )

        self.machine.add_transition(
            trigger="escalate_to_critical",
            source=["normal", "traffic_advisory", "resolution_advisory"],
            dest="critical_avoidance",
            before="enter_critical_avoidance",
        )

        self.machine.add_transition(
            trigger="downgrade_to_resolution",
            source="critical_avoidance",
            dest="resolution_advisory",
            before="reset_emergency_flag",
        )

        self.machine.add_transition(
            trigger="downgrade_to_traffic",
            source="resolution_advisory",
            dest="traffic_advisory",
            before="reset_advisory_flag",
        )

        self.machine.add_transition(
            trigger="clear_all_traffic",
            source=["traffic_advisory", "resolution_advisory", "critical_avoidance"],
            dest="normal",
            before="reset_all_flags",
        )

    def finalize_transition(self, event):
        """Called after each state transition"""
        print(f"\n{self.aircraft.call_sign} TCAS: Entering {self.state}")

    # Action methods (before callbacks)
    def enter_traffic_advisory(self, event):
        """Enter traffic advisory state"""
        print("TCAS: TRAFFIC DETECTED")

    def enter_resolution_advisory(self, event):
        """Enter resolution advisory state"""
        print("TCAS: RESOLUTION ADVISORY")
        if not self.advisory_issued:
            self._issue_resolution_advisory()
            self.advisory_issued = True

    def enter_critical_avoidance(self, event):
        """Enter critical avoidance state"""
        print("TCAS: CRITICAL THREAT")
        if not self.emergency_issued:
            self._issue_emergency_advisory()
            self.emergency_issued = True

    def reset_advisory_flag(self, event):
        """Reset advisory issued flag"""
        self.advisory_issued = False

    def reset_emergency_flag(self, event):
        """Reset emergency issued flag"""
        self.emergency_issued = False

    def reset_all_flags(self, event):
        """Reset all flags"""
        self.advisory_issued = False
        self.emergency_issued = False

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

    def _issue_resolution_advisory(self) -> None:
        """Issue RA and command aircraft"""
        if self.current_threat:
            if self.current_threat.altitude_difference > 0:
                print("TCAS RA: DESCEND")
                success = self.aircraft.request_descend(1500)
                if not success:
                    print("TCAS: Aircraft unable to accept descent command")
            else:
                print("TCAS RA: CLIMB")
                success = self.aircraft.request_climb(1500)
                if not success:
                    print("TCAS: Aircraft unable to accept climb command")

    def _issue_emergency_advisory(self) -> None:
        """Issue emergency RA and command aircraft"""
        if self.current_threat:
            if self.current_threat.altitude_difference > 0:
                print("TCAS CRITICAL: EMERGENCY DESCENT")
                success = self.aircraft.request_emergency_descend(2500)
            else:
                print("TCAS CRITICAL: EMERGENCY CLIMB")
                success = self.aircraft.request_emergency_climb(2500)

            if not success:
                print("TCAS: ALERT - Aircraft unable to execute emergency maneuver!")

    # Public interface methods
    def get_threat_level(self) -> ThreatLevel:
        """Get current threat level"""
        if self.state == "normal":
            return ThreatLevel.NONE
        elif self.state == "traffic_advisory":
            return ThreatLevel.TRAFFIC_ADVISORY
        elif self.state == "resolution_advisory":
            return ThreatLevel.RESOLUTION_ADVISORY
        elif self.state == "critical_avoidance":
            return ThreatLevel.CRITICAL
        else:
            return ThreatLevel.NONE

    def update_traffic(self, traffic_data: TrafficData) -> None:
        """Update with new traffic information"""
        self.current_threat = traffic_data
        threat_level = self._assess_threat_level(traffic_data)

        try:
            if threat_level == ThreatLevel.CRITICAL:
                self.escalate_to_critical()
            elif threat_level == ThreatLevel.RESOLUTION_ADVISORY:
                if self.state == "critical_avoidance":
                    self.downgrade_to_resolution()
                elif self.state in ["normal", "traffic_advisory"]:
                    self.escalate_to_resolution()
            elif threat_level == ThreatLevel.TRAFFIC_ADVISORY:
                if self.state == "resolution_advisory":
                    self.downgrade_to_traffic()
                elif self.state == "normal":
                    self.detect_traffic_advisory()
            elif threat_level == ThreatLevel.NONE:
                if self.state != "normal":
                    self.clear_all_traffic()
        except:
            pass  # Transition not allowed from current state

    def clear_traffic(self) -> None:
        """Clear traffic threat"""
        self.current_threat = None
        try:
            if self.state != "normal":
                self.clear_all_traffic()
        except:
            pass

    def pilot_compliance_confirmed(self) -> None:
        """Pilot confirms maneuver compliance"""
        if self.state == "resolution_advisory":
            print("TCAS RA: Compliance confirmed")
        elif self.state == "critical_avoidance":
            print("TCAS CRITICAL: Emergency compliance confirmed")

    def maneuver_complete(self) -> None:
        """Signal that maneuver is complete"""
        if self.state == "resolution_advisory":
            print("TCAS RA: Maneuver complete")
            self.aircraft.complete_maneuver_request()
            if self.current_threat is None:
                try:
                    self.clear_all_traffic()
                except:
                    pass
        elif self.state == "critical_avoidance":
            print("TCAS: Emergency maneuver complete")
            self.aircraft.complete_maneuver_request()
            if self.current_threat is None:
                try:
                    self.clear_all_traffic()
                except:
                    pass


# =============================================================================
# SIMULATION
# =============================================================================


def simulate_transitions_state_machines():
    """Simulate collision avoidance with transitions library FSMs"""

    print("=== TRANSITIONS LIBRARY STATE MACHINE SIMULATION ===")

    # Create aircraft with its own FSM
    aircraft = Aircraft("United 123", altitude=10000)
    print(f"Aircraft Flight State: {aircraft.get_flight_phase().value}")

    # Create TCAS system
    tcas = CollisionAvoidanceSystem(aircraft)

    # Test normal maneuver first
    print("\n--- Testing Normal Aircraft Maneuver ---")
    aircraft.request_climb(1000)
    print(f"Aircraft Flight State: {aircraft.get_flight_phase().value}")
    aircraft.complete_maneuver_request()
    print(f"Aircraft Flight State: {aircraft.get_flight_phase().value}")
    aircraft.complete_maneuver_request()  # Complete recovery
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
    simulate_transitions_state_machines()
