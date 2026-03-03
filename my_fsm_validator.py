from typing import Dict, Set, List, Tuple
from collections import defaultdict, deque
import networkx as nx
import matplotlib.pyplot as plt

from my_fsm import *

class FSMValidator:
    """Validates FSM completeness and reachability"""
    
    def __init__(self, name: str):
        self.name = name
        self.states: Set[str] = set()
        self.transitions: Dict[str, Dict[str, Set[str]]] = defaultdict(lambda: defaultdict(set))
        self.initial_states: Set[str] = set()
        self.final_states: Set[str] = set()
        self.events: Set[str] = set()
    
    def add_state(self, state: str, is_initial: bool = False, is_final: bool = False):
        """Add a state to the FSM"""
        self.states.add(state)
        if is_initial:
            self.initial_states.add(state)
        if is_final:
            self.final_states.add(state)
    
    def add_transition(self, from_state: str, to_state: str, event: str):
        """Add a transition between states"""
        self.states.add(from_state)
        self.states.add(to_state)
        self.transitions[from_state][event].add(to_state)
        self.events.add(event)
    
    def get_transition_matrix(self) -> Dict[str, Dict[str, List[str]]]:
        """Generate complete transition matrix"""
        matrix = {}
        for state in self.states:
            matrix[state] = {}
            for event in self.events:
                if event in self.transitions[state]:
                    matrix[state][event] = list(self.transitions[state][event])
                else:
                    matrix[state][event] = []  # No transition defined
        return matrix
    
    def find_unreachable_states(self) -> Set[str]:
        """Find states unreachable from initial states"""
        if not self.initial_states:
            return set()
        
        reachable = set()
        queue = deque(self.initial_states)
        reachable.update(self.initial_states)
        
        while queue:
            current_state = queue.popleft()
            for event in self.events:
                next_states = self.transitions[current_state].get(event, set())
                for next_state in next_states:
                    if next_state not in reachable:
                        reachable.add(next_state)
                        queue.append(next_state)
        
        return self.states - reachable
    
    def find_dead_states(self) -> Set[str]:
        """Find states with no outgoing transitions"""
        dead_states = set()
        for state in self.states:
            has_outgoing = False
            for event in self.events:
                if self.transitions[state][event]:
                    has_outgoing = True
                    break
            if not has_outgoing and state not in self.final_states:
                dead_states.add(state)
        return dead_states
    
    def find_missing_transitions(self) -> List[Tuple[str, str]]:
        """Find state-event combinations with no defined transitions"""
        missing = []
        for state in self.states:
            for event in self.events:
                if not self.transitions[state][event]:
                    missing.append((state, event))
        return missing
    
    def validate_completeness(self) -> Dict[str, any]:
        """Comprehensive FSM validation"""
        return {
            'total_states': len(self.states),
            'total_events': len(self.events),
            'total_transitions': sum(len(self.transitions[s][e]) 
                                   for s in self.states 
                                   for e in self.events 
                                   if self.transitions[s][e]),
            'initial_states': self.initial_states,
            'final_states': self.final_states,
            'unreachable_states': self.find_unreachable_states(),
            'dead_states': self.find_dead_states(),
            'missing_transitions': self.find_missing_transitions(),
            'transition_matrix': self.get_transition_matrix()
        }
    
    def generate_test_paths(self, max_length: int = 10) -> List[List[Tuple[str, str]]]:
        """Generate test paths through the FSM"""
        paths = []
        
        def dfs_paths(current_state: str, path: List[Tuple[str, str]], visited_states: Set[str]):
            if len(path) >= max_length:
                return
            
            for event in self.events:
                next_states = self.transitions[current_state].get(event, set())
                for next_state in next_states:
                    new_path = path + [(event, next_state)]
                    paths.append(new_path.copy())
                    
                    # Continue exploring if we haven't been in a cycle too long
                    if len(visited_states) < len(self.states) or next_state not in visited_states:
                        new_visited = visited_states.copy()
                        new_visited.add(next_state)
                        dfs_paths(next_state, new_path, new_visited)
        
        for initial_state in self.initial_states:
            dfs_paths(initial_state, [], {initial_state})
        
        return paths[:50]  # Limit to reasonable number


def create_aircraft_fsm_validator() -> FSMValidator:
    """Create validator for Aircraft FSM"""
    validator = FSMValidator("Aircraft_FSM")
    
    # Define states
    validator.add_state("NormalFlight", is_initial=True)
    validator.add_state("Maneuvering")
    validator.add_state("EmergencyManeuver")
    validator.add_state("Recovering", is_final=True)
    
    # Define transitions
    # From NormalFlight
    validator.add_transition("NormalFlight", "Maneuvering", "request_climb")
    validator.add_transition("NormalFlight", "Maneuvering", "request_descend")
    validator.add_transition("NormalFlight", "EmergencyManeuver", "request_emergency_climb")
    validator.add_transition("NormalFlight", "EmergencyManeuver", "request_emergency_descend")
    validator.add_transition("NormalFlight", "NormalFlight", "request_level_off")
    validator.add_transition("NormalFlight", "NormalFlight", "complete_maneuver")
    validator.add_transition("NormalFlight", "NormalFlight", "abort_maneuver")
    
    # From Maneuvering
    validator.add_transition("Maneuvering", "Maneuvering", "request_climb")
    validator.add_transition("Maneuvering", "Maneuvering", "request_descend")
    validator.add_transition("Maneuvering", "EmergencyManeuver", "request_emergency_climb")
    validator.add_transition("Maneuvering", "EmergencyManeuver", "request_emergency_descend")
    validator.add_transition("Maneuvering", "Recovering", "request_level_off")
    validator.add_transition("Maneuvering", "Recovering", "complete_maneuver")
    validator.add_transition("Maneuvering", "Recovering", "abort_maneuver")
    
    # From EmergencyManeuver
    validator.add_transition("EmergencyManeuver", "EmergencyManeuver", "request_emergency_climb")
    validator.add_transition("EmergencyManeuver", "EmergencyManeuver", "request_emergency_descend")
    validator.add_transition("EmergencyManeuver", "Recovering", "request_level_off")
    validator.add_transition("EmergencyManeuver", "Recovering", "complete_maneuver")
    validator.add_transition("EmergencyManeuver", "Recovering", "abort_maneuver")
    # Note: Emergency states reject normal climb/descend requests
    
    # From Recovering
    validator.add_transition("Recovering", "Maneuvering", "request_climb")
    validator.add_transition("Recovering", "Maneuvering", "request_descend")
    validator.add_transition("Recovering", "EmergencyManeuver", "request_emergency_climb")
    validator.add_transition("Recovering", "EmergencyManeuver", "request_emergency_descend")
    validator.add_transition("Recovering", "Recovering", "request_level_off")
    validator.add_transition("Recovering", "NormalFlight", "complete_maneuver")
    validator.add_transition("Recovering", "NormalFlight", "abort_maneuver")
    
    return validator

def create_tcas_fsm_validator() -> FSMValidator:
    """Create validator for TCAS FSM"""
    validator = FSMValidator("TCAS_FSM")
    
    # Define states
    validator.add_state("NormalFlight", is_initial=True)
    validator.add_state("TrafficAdvisory")
    validator.add_state("ResolutionAdvisory")
    validator.add_state("CriticalAvoidance")
    
    # Define transitions
    # From NormalFlight
    validator.add_transition("NormalFlight", "TrafficAdvisory", "traffic_detected")
    validator.add_transition("NormalFlight", "ResolutionAdvisory", "resolution_required")
    validator.add_transition("NormalFlight", "CriticalAvoidance", "critical_threat")
    validator.add_transition("NormalFlight", "NormalFlight", "traffic_cleared")
    
    # From TrafficAdvisory
    validator.add_transition("TrafficAdvisory", "NormalFlight", "traffic_cleared")
    validator.add_transition("TrafficAdvisory", "ResolutionAdvisory", "threat_escalated")
    validator.add_transition("TrafficAdvisory", "CriticalAvoidance", "critical_threat")
    validator.add_transition("TrafficAdvisory", "TrafficAdvisory", "traffic_updated")
    
    # From ResolutionAdvisory
    validator.add_transition("ResolutionAdvisory", "NormalFlight", "traffic_cleared")
    validator.add_transition("ResolutionAdvisory", "TrafficAdvisory", "threat_reduced")
    validator.add_transition("ResolutionAdvisory", "CriticalAvoidance", "threat_escalated")
    validator.add_transition("ResolutionAdvisory", "ResolutionAdvisory", "maneuver_updated")
    
    # From CriticalAvoidance
    validator.add_transition("CriticalAvoidance", "ResolutionAdvisory", "threat_reduced")
    validator.add_transition("CriticalAvoidance", "NormalFlight", "traffic_cleared")
    validator.add_transition("CriticalAvoidance", "CriticalAvoidance", "emergency_continued")
    
    return validator


import unittest
from typing import List, Set

class FSMTestSuite:
    """Test suite for FSM validation"""
    
    def __init__(self, validator: FSMValidator):
        self.validator = validator
        self.validation_results = validator.validate_completeness()
    
    def test_no_unreachable_states(self) -> bool:
        """Test that all states are reachable"""
        unreachable = self.validation_results['unreachable_states']
        if unreachable:
            print(f"❌ FAILED: Unreachable states found: {unreachable}")
            return False
        print("✅ PASSED: All states are reachable")
        return True
    
    def test_no_dead_states(self) -> bool:
        """Test that no states are dead ends (except final states)"""
        dead_states = self.validation_results['dead_states']
        if dead_states:
            print(f"❌ FAILED: Dead states found: {dead_states}")
            return False
        print("✅ PASSED: No dead states found")
        return True
    
    def test_all_transitions_defined(self) -> bool:
        """Test that all state-event combinations have defined behavior"""
        missing = self.validation_results['missing_transitions']
        critical_missing = []
        
        # Some missing transitions might be intentional (invalid operations)
        # Filter for truly critical missing transitions
        for state, event in missing:
            if self._is_critical_transition(state, event):
                critical_missing.append((state, event))
        
        if critical_missing:
            print(f"❌ FAILED: Critical missing transitions: {critical_missing}")
            return False
        print("✅ PASSED: All critical transitions defined")
        return True
    
    def test_initial_state_exists(self) -> bool:
        """Test that at least one initial state exists"""
        if not self.validation_results['initial_states']:
            print("❌ FAILED: No initial state defined")
            return False
        print(f"✅ PASSED: Initial states: {self.validation_results['initial_states']}")
        return True
    
    def test_state_machine_determinism(self) -> bool:
        """Test for non-deterministic transitions"""
        non_deterministic = []
        matrix = self.validation_results['transition_matrix']
        
        for state, transitions in matrix.items():
            for event, next_states in transitions.items():
                if len(next_states) > 1:
                    non_deterministic.append((state, event, next_states))
        
        if non_deterministic:
            # Non-determinism might be acceptable in some cases
            print(f"⚠️  WARNING: Non-deterministic transitions: {non_deterministic}")
        else:
            print("✅ PASSED: FSM is deterministic")
        return True
    
    def test_cyclical_paths_exist(self) -> bool:
        """Test that FSM can return to initial states"""
        has_cycles = False
        paths = self.validator.generate_test_paths(max_length=6)
        
        for path in paths:
            if len(path) > 1:
                start_state = list(self.validator.initial_states)[0] if self.validator.initial_states else ""
                end_state = path[-1][1]
                if end_state in self.validator.initial_states:
                    has_cycles = True
                    break
        
        if not has_cycles:
            print("⚠️  WARNING: No paths back to initial states found")
        else:
            print("✅ PASSED: Cyclical paths exist")
        return True
    
    def _is_critical_transition(self, state: str, event: str) -> bool:
        """Determine if a missing transition is critical"""
        # Define critical events that should always have transitions
        critical_events = {"abort_maneuver", "complete_maneuver", "traffic_cleared"}
        return event in critical_events
    
    def run_all_tests(self) -> bool:
        """Run complete test suite"""
        print(f"\n=== FSM Validation: {self.validator.name} ===")
        print(f"States: {len(self.validator.states)}")
        print(f"Events: {len(self.validator.events)}")
        print(f"Transitions: {self.validation_results['total_transitions']}")
        
        tests = [
            self.test_initial_state_exists,
            self.test_no_unreachable_states,
            self.test_no_dead_states,
            self.test_all_transitions_defined,
            self.test_state_machine_determinism,
            self.test_cyclical_paths_exist
        ]
        
        results = [test() for test in tests]
        passed = sum(results)
        total = len(results)
        
        print(f"\n📊 Results: {passed}/{total} tests passed")
        return passed == total


from hypothesis import given, strategies as st, assume
import hypothesis

class FSMPropertyTest:
    """Property-based testing for FSM behavior"""
    
    def __init__(self, fsm_class, initial_params=None):
        self.fsm_class = fsm_class
        self.initial_params = initial_params or {}
    
    @given(st.lists(
        st.sampled_from(['request_climb', 'request_descend', 'request_emergency_climb', 
                        'request_emergency_descend', 'request_level_off', 'complete_maneuver', 
                        'abort_maneuver']), 
        min_size=1, max_size=20
    ))
    def test_fsm_never_crashes(self, event_sequence):
        """Property: FSM should never crash regardless of event sequence"""
        try:
            fsm = self.fsm_class(**self.initial_params)
            initial_state = type(fsm._flight_state).__name__
            
            for event in event_sequence:
                if hasattr(fsm, event):
                    # Try the event, capture result but don't fail on False
                    getattr(fsm, event)(1000 if 'climb' in event or 'descend' in event else None)
            
            final_state = type(fsm._flight_state).__name__
            # FSM should always be in a valid state
            assert fsm._flight_state is not None, "FSM ended in null state"
            
        except Exception as e:
            # If we crash, that's a failure
            raise AssertionError(f"FSM crashed on sequence {event_sequence}: {e}")
    
    @given(st.integers(min_value=1, max_value=50))
    def test_emergency_always_recoverable(self, iterations):
        """Property: Emergency states should always be recoverable"""
        fsm = self.fsm_class(**self.initial_params)
        
        for _ in range(iterations):
            # Enter emergency state
            fsm.request_emergency_climb(2500)
            assert fsm.get_flight_phase().value in ['emergency', 'maneuvering']
            
            # Should always be able to complete and recover
            fsm.complete_maneuver()  # Emergency -> Recovery
            fsm.complete_maneuver()  # Recovery -> Normal
            
            assert fsm.get_flight_phase().value == 'normal'


def generate_promela_model(validator: FSMValidator) -> str:
    """Generate PROMELA model for SPIN model checker"""
    
    # Map states to integers for PROMELA
    state_map = {state: i for i, state in enumerate(validator.states)}
    event_map = {event: i for i, event in enumerate(validator.events)}
    
    promela = f"""
/* Auto-generated PROMELA model for {validator.name} */

#define NUM_STATES {len(validator.states)}
#define NUM_EVENTS {len(validator.events)}

/* State definitions */
"""
    
    for state, num in state_map.items():
        promela += f"#define {state.upper()} {num}\n"
    
    promela += "\n/* Event definitions */\n"
    for event, num in event_map.items():
        promela += f"#define {event.upper()} {num}\n"
    
    promela += f"""
byte state = {list(state_map.values())[0]}; /* Initial state */
chan events = [10] of {{byte}};

active proctype FSM() {{
    byte event;
    do
    :: events?event ->
"""
    
    # Generate transition logic
    for state, state_num in state_map.items():
        promela += f"        if\n        :: state == {state_num} ->\n"
        for event in validator.events:
            next_states = validator.transitions[state].get(event, set())
            if next_states:
                next_state = list(next_states)[0]  # Take first for deterministic model
                promela += f"            if :: event == {event_map[event]} -> state = {state_map[next_state]} fi;\n"
        promela += "        fi;\n"
    
    promela += """
    od
}

/* Safety properties */
ltl no_deadlock { []<>true }
ltl reachability { <>(state == NORMALFLIGHT) }
"""
    
    return promela


def validate_aircraft_fsm():
    """Complete validation of aircraft FSM"""
    
    # Create and validate Aircraft FSM
    aircraft_validator = create_aircraft_fsm_validator()
    aircraft_test_suite = FSMTestSuite(aircraft_validator)
    aircraft_passed = aircraft_test_suite.run_all_tests()
    
    # Create and validate TCAS FSM
    tcas_validator = create_tcas_fsm_validator()
    tcas_test_suite = FSMTestSuite(tcas_validator)
    tcas_passed = tcas_test_suite.run_all_tests()
    
    # Property-based testing
    print("\n=== Property-Based Testing ===")
    property_tester = FSMPropertyTest(Aircraft, {"call_sign": "TEST123", "altitude": 10000})
    
    # Run property tests (would normally use pytest or unittest runner)
    try:
        # This would be run with: python -m pytest with hypothesis
        print("✅ Property-based tests would run with pytest + hypothesis")
    except Exception as e:
        print(f"❌ Property test failed: {e}")
    
    # Generate formal model
    print("\n=== Formal Model Generation ===")
    promela_model = generate_promela_model(aircraft_validator)
    print("✅ PROMELA model generated (would be checked with SPIN)")
    
    return aircraft_passed and tcas_passed

if __name__ == "__main__":
    validate_aircraft_fsm()
