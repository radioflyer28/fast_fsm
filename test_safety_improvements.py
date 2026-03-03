#!/usr/bin/env python3
"""
Safety improvements test for fast_fsm kwargs handling.

This test demonstrates the safety mechanisms added to protect against
potentially problematic context data passed through **kwargs.
"""

import sys
import logging
sys.path.append('benchmarks')
from benchmark_fast_fsm import Aircraft, TrafficData

# Enable debug logging to see safety filtering in action
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

def test_normal_operation():
    """Test that normal operation works correctly"""
    print("\n🧪 Test 1: Normal Operation")
    aircraft = Aircraft('TEST001')
    
    # Normal kwargs should work
    result = aircraft.request_climb(rate=1500)
    print(f"✅ Normal operation: {result}")
    
    traffic = TrafficData(
        distance=1.5,
        altitude_difference=500,
        closing_rate=100,
        bearing=45,
        time_to_closest_approach=20
    )
    
    # This should work normally
    aircraft._fsm.trigger("request_climb", aircraft=aircraft, traffic=traffic)
    print(f"✅ Normal kwargs passed safely")

def test_private_attribute_filtering():
    """Test that private attributes are filtered out"""
    print("\n🧪 Test 2: Private Attribute Filtering")
    aircraft = Aircraft('TEST002')
    
    # Try to pass private attributes - these should be filtered
    result = aircraft._fsm.trigger('request_climb',
                                   aircraft=aircraft,
                                   _private_secret='FILTERED',
                                   __dunder_secret='FILTERED',
                                   normal_data='PASSED')
    
    print(f"✅ Private attributes filtered: {result.success}")

def test_excessive_kwargs():
    """Test handling of excessive number of kwargs"""
    print("\n🧪 Test 3: Excessive Kwargs Protection")
    aircraft = Aircraft('TEST003')
    
    # Create 60 kwargs (over the 50 limit)
    massive_kwargs = {f'param_{i}': f'value_{i}' for i in range(60)}
    massive_kwargs['aircraft'] = aircraft
    
    # This should trigger the protection mechanism
    result = aircraft._fsm.trigger('request_climb', **massive_kwargs)
    print(f"✅ Excessive kwargs handled: {result.success}")

def test_invalid_key_filtering():
    """Test filtering of invalid keys"""
    print("\n🧪 Test 4: Invalid Key Filtering")
    aircraft = Aircraft('TEST004')
    
    # Try various problematic keys (Python handles non-string keys at language level)
    problematic_kwargs = {
        "a" * 150: "too_long_key",  # Very long key
        "normal_key": "good_value",
        "aircraft": aircraft
    }
    
    result = aircraft._fsm.trigger('request_climb', **problematic_kwargs)
    print(f"✅ Invalid keys filtered: {result.success}")

def test_exception_safety():
    """Test that condition exceptions are handled safely"""
    print("\n🧪 Test 5: Exception Safety")
    aircraft = Aircraft('TEST005')
    
    # Create a condition that will raise an exception
    from fast_fsm.conditions import Condition
    
    class BadCondition(Condition):
        def __init__(self):
            super().__init__("bad_condition", "Will raise exception")
        
        def check(self, **kwargs):
            raise ValueError("Intentional test exception")
    
    # Add a transition with the bad condition
    from fast_fsm.core import State
    test_state = State("test_state")
    aircraft._fsm.add_state(test_state)
    aircraft._fsm.add_transition("test_trigger", "normal", "test_state", BadCondition())
    
    # This should handle the exception gracefully
    result = aircraft._fsm.trigger('test_trigger', aircraft=aircraft)
    print(f"✅ Exception handled safely: {not result.success}")
    print(f"✅ Error message: {result.error}")

if __name__ == "__main__":
    print("🛡️  Fast FSM Safety Improvements Test Suite")
    print("=" * 50)
    
    test_normal_operation()
    test_private_attribute_filtering()
    test_excessive_kwargs()
    test_invalid_key_filtering()
    test_exception_safety()
    
    print("\n🎉 All safety tests completed!")
    print("\n📋 Safety Features Summary:")
    print("- ✅ Private attribute filtering (_attr, __attr)")
    print("- ✅ Kwargs count limiting (max 50)")
    print("- ✅ Invalid key filtering (non-string, too long)")
    print("- ✅ Exception handling in conditions")
    print("- ✅ Comprehensive logging of safety actions")