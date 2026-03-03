#!/usr/bin/env python3
"""
Test script to verify *args support in conditions and transitions
"""

from fast_fsm import State, StateMachine, FuncCondition


class SimpleState(State):
    def on_enter(self, from_state, trigger, *args, **kwargs):
        print(f"Entering {self.name} with args={args}, kwargs={kwargs}")
    
    def on_exit(self, to_state, trigger, *args, **kwargs):
        print(f"Exiting {self.name} with args={args}, kwargs={kwargs}")


def test_basic_args_support():
    """Test basic *args support with conditions"""
    print("=== Testing *args support ===")
    
    # Create states
    idle = SimpleState('idle')
    running = SimpleState('running')
    
    # Create FSM
    fsm = StateMachine(idle, name='TestFSM')
    fsm.add_state(running)
    
    # Test 1: Function condition with *args
    def fuel_check(fuel_level, *args, **kwargs):
        print(f"  Fuel check: fuel_level={fuel_level}, args={args}, kwargs={kwargs}")
        return fuel_level > 0
    
    fsm.add_transition('start', 'idle', 'running', condition=fuel_check)
    
    # Test with positional arguments
    print("\n1. Testing with positional arguments:")
    result = fsm.trigger('start', 50)  # fuel_level=50
    print(f"   Result: {result.success}")
    print(f"   Current state: {fsm.current_state_name}")
    
    # Reset
    fsm._current_state = idle
    
    # Test with mixed args and kwargs
    print("\n2. Testing with mixed args and kwargs:")
    result = fsm.trigger('start', 75, engine_temp=180, oil_pressure=45)
    print(f"   Result: {result.success}")
    print(f"   Current state: {fsm.current_state_name}")
    
    # Reset
    fsm._current_state = idle
    
    # Test 3: FuncCondition directly
    print("\n3. Testing FuncCondition directly:")
    def complex_condition(threshold, safety_margin, *args, **kwargs):
        temp = kwargs.get('temperature', 0)
        print(f"  Complex check: threshold={threshold}, safety_margin={safety_margin}")
        print(f"                 temperature={temp}, args={args}, kwargs={kwargs}")
        return temp < (threshold - safety_margin)
    
    # Add transition with explicit FuncCondition
    func_cond = FuncCondition(complex_condition, "temperature_safety")
    fsm.add_transition('cool_down', 'running', 'idle', condition=func_cond)
    
    # Reset to running state
    fsm._current_state = running
    
    result = fsm.trigger('cool_down', 100, 10, temperature=85, pressure=30)
    print(f"   Result: {result.success}")
    print(f"   Current state: {fsm.current_state_name}")


def test_lambda_with_args():
    """Test lambda conditions with *args"""
    print("\n=== Testing lambda conditions ===")
    
    idle = SimpleState('idle')
    active = SimpleState('active')
    
    fsm = StateMachine(idle, name='LambdaFSM')
    fsm.add_state(active)
    
    # Lambda that uses first positional argument
    fsm.add_transition('activate', 'idle', 'active', 
                      condition=lambda level, *args, **kwargs: level >= 5)
    
    print("Testing lambda with args:")
    result = fsm.trigger('activate', 7, extra_arg="test")
    print(f"   Result: {result.success}")
    print(f"   Current state: {fsm.current_state_name}")


def test_condition_class_with_args():
    """Test custom Condition class with *args"""
    print("\n=== Testing custom Condition class ===")
    
    from fast_fsm import Condition
    
    class RangeCondition(Condition):
        def __init__(self, min_val, max_val):
            super().__init__(f"range_{min_val}_{max_val}", f"Value between {min_val} and {max_val}")
            self.min_val = min_val
            self.max_val = max_val
        
        def check(self, value, *args, **kwargs):
            print(f"  Range check: value={value}, args={args}, kwargs={kwargs}")
            print(f"              range=[{self.min_val}, {self.max_val}]")
            return self.min_val <= value <= self.max_val
    
    idle = SimpleState('idle')
    normal = SimpleState('normal')
    
    fsm = StateMachine(idle, name='RangeFSM')
    fsm.add_state(normal)
    
    range_cond = RangeCondition(10, 100)
    fsm.add_transition('check_range', 'idle', 'normal', condition=range_cond)
    
    print("Testing custom condition with args:")
    result = fsm.trigger('check_range', 50, extra="data", mode="test")
    print(f"   Result: {result.success}")
    print(f"   Current state: {fsm.current_state_name}")


if __name__ == '__main__':
    test_basic_args_support()
    test_lambda_with_args()
    test_condition_class_with_args()
    
    print("\n=== All tests completed ===")
