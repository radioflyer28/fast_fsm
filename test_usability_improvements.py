#!/usr/bin/env python3
"""
Comprehensive test of FSM library usability improvements
"""

from fast_fsm import (
    State, StateMachine, FSMBuilder, 
    simple_fsm, quick_fsm, condition_builder,
    set_fsm_logging_level
)


def test_factory_methods():
    """Test factory methods for easy FSM creation"""
    print("=== Testing Factory Methods ===")
    
    # 1. Simple FSM creation
    print("1. Creating FSM from state names:")
    fsm1 = simple_fsm('idle', 'running', 'error', initial='idle', name='SimpleTest')
    print(f"   Created FSM with states: {fsm1.states}")
    print(f"   Current state: {fsm1.current_state_name}")
    
    # 2. Quick FSM from transitions
    print("\n2. Creating FSM from transition list:")
    fsm2 = quick_fsm('idle', [
        ('start', 'idle', 'running'),
        ('stop', 'running', 'idle'),
        ('error', 'running', 'error'),
        ('reset', 'error', 'idle')
    ], name='QuickTest')
    print(f"   Created FSM with {len(fsm2.states)} states")
    print(f"   Available triggers: {fsm2.triggers}")
    
    # 3. StateMachine class methods
    print("\n3. Using StateMachine.from_states():")
    fsm3 = StateMachine.from_states('waiting', 'processing', 'done', initial='waiting')
    print(f"   States: {fsm3.states}")
    
    return fsm2  # Use this for further testing


def test_enhanced_state_creation():
    """Test enhanced state creation"""
    print("\n=== Testing Enhanced State Creation ===")
    
    # Create states with inline callbacks
    idle_state = State.create('idle',
        on_enter=lambda from_state, trigger, *args, **kwargs: print(f"💤 Entering idle from {from_state.name if from_state else 'start'}"),
        on_exit=lambda to_state, trigger, *args, **kwargs: print(f"🚀 Leaving idle for {to_state.name}")
    )
    
    processing_state = State.create('processing',
        on_enter=lambda from_state, trigger, *args, **kwargs: print(f"⚙️ Processing started (args: {args})"),
        on_exit=lambda to_state, trigger, *args, **kwargs: print("✅ Processing finished")
    )
    
    # Build FSM with these states
    fsm = (FSMBuilder(idle_state, name='CallbackTest')
           .add_state(processing_state)
           .add_transition('start', 'idle', 'processing')
           .add_transition('complete', 'processing', 'idle')
           .build())
    
    print("Testing state callbacks:")
    fsm.trigger('start', 'priority_job', level=5)
    fsm.trigger('complete')
    
    return fsm


def test_enhanced_transitions():
    """Test enhanced transition methods"""
    print("\n=== Testing Enhanced Transitions ===")
    
    fsm = simple_fsm('idle', 'running', 'paused', 'error', initial='idle', name='TransitionTest')
    
    # 1. Bulk transitions
    print("1. Adding multiple transitions at once:")
    fsm.add_transitions([
        ('start', 'idle', 'running'),
        ('stop', 'running', 'idle'),
        ('pause', 'running', 'paused')
    ])
    
    # 2. Bidirectional transitions
    print("2. Adding bidirectional transitions:")
    fsm.add_bidirectional_transition('pause', 'resume', 'running', 'paused')
    
    # 3. Emergency transitions
    print("3. Adding emergency transition from all states:")
    fsm.add_emergency_transition('emergency_stop', 'error')
    
    print(f"   Total triggers: {len(fsm.triggers)}")
    print(f"   All triggers: {fsm.triggers}")
    
    # Test the transitions
    print("\nTesting transitions:")
    fsm.trigger('start')
    print(f"   After start: {fsm.current_state_name}")
    fsm.trigger('pause')
    print(f"   After pause: {fsm.current_state_name}")
    fsm.trigger('emergency_stop')
    print(f"   After emergency: {fsm.current_state_name}")
    
    return fsm


def test_introspection():
    """Test introspection and query methods"""
    print("\n=== Testing Introspection Methods ===")
    
    fsm = quick_fsm('idle', [
        ('start', 'idle', 'running'),
        ('pause', 'running', 'paused'),
        ('resume', 'paused', 'running'),
        ('stop', ['running', 'paused'], 'idle'),
        ('error', 'running', 'error')
    ], name='IntrospectionTest')
    
    # Test query methods
    print("1. Query methods:")
    print(f"   All states: {fsm.states}")
    print(f"   All triggers: {fsm.triggers}")
    print(f"   Available from current state: {fsm.get_available_triggers()}")
    print(f"   Reachable from current state: {fsm.get_reachable_states()}")
    
    # Test transition existence
    print("\n2. Transition existence checks:")
    print(f"   Can 'start' from 'idle': {fsm.transition_exists('start', 'idle')}")
    print(f"   Can 'stop' from 'idle': {fsm.transition_exists('stop', 'idle')}")
    print(f"   Can 'start' from current state: {fsm.transition_exists('start')}")
    
    # Debug info
    print("\n3. Debug information:")
    fsm.print_debug_info()
    
    # Validation
    print("\n4. Quick validation:")
    issues = fsm.validate_transition_completeness()
    print(f"   Dead end states: {issues['dead_end_states']}")
    print(f"   Unreachable states: {issues['unreachable_states']}")
    
    return fsm


def test_condition_helpers():
    """Test condition builder helpers"""
    print("\n=== Testing Condition Helpers ===")
    
    # Create conditions with decorator
    @condition_builder(name="has_fuel", description="Check if fuel level is sufficient")
    def fuel_check(fuel_level, **kwargs):
        return fuel_level > 0
    
    @condition_builder(name="temperature_ok", description="Check temperature is within range")
    def temp_check(temperature=0, **kwargs):
        return 0 <= temperature <= 100
    
    # Create FSM with these conditions
    fsm = simple_fsm('idle', 'running', 'overheated', initial='idle', name='ConditionTest')
    fsm.add_transition('start', 'idle', 'running', condition=fuel_check)
    fsm.add_transition('overheat', 'running', 'overheated', 
                      condition=lambda temperature=0, **kwargs: temperature > 90)
    
    print("Testing conditions:")
    
    # Test with sufficient fuel
    result1 = fsm.trigger('start', fuel_level=50)
    print(f"   Start with fuel=50: {result1.success}")
    
    # Reset and test without fuel
    fsm._current_state = fsm._states['idle']
    result2 = fsm.trigger('start', fuel_level=0)
    print(f"   Start with fuel=0: {result2.success} - {result2.error}")
    
    return fsm


def test_error_handling():
    """Test enhanced error handling"""
    print("\n=== Testing Error Handling ===")
    
    fsm = simple_fsm('idle', 'running', initial='idle', name='ErrorTest')
    fsm.add_transition('start', 'idle', 'running')
    
    # Test safe trigger
    print("1. Testing safe_trigger:")
    result1 = fsm.safe_trigger('start')
    print(f"   Valid trigger: success={result1.success}")
    
    result2 = fsm.safe_trigger('invalid_trigger')
    print(f"   Invalid trigger: success={result2.success}, error='{result2.error}'")
    
    # Test with exception in condition
    def failing_condition(**kwargs):
        raise ValueError("Condition failed!")
    
    fsm.add_transition('fail', 'running', 'idle', condition=failing_condition)
    
    result3 = fsm.safe_trigger('fail')
    print(f"   Failing condition: success={result3.success}")
    
    return fsm


def main():
    """Run all usability tests"""
    print("🚀 Fast FSM Library - Usability Improvements Demo")
    print("=" * 60)
    
    # Enable basic logging to see transitions
    set_fsm_logging_level('basic')
    
    # Run all tests
    test_factory_methods()
    test_enhanced_state_creation()
    test_enhanced_transitions()
    test_introspection()
    test_condition_helpers()
    test_error_handling()
    
    print("\n" + "=" * 60)
    print("✅ All usability improvements demonstrated successfully!")
    
    # Show a comparison
    print("\n🎯 Key Usability Improvements:")
    print("   ✅ Factory methods for quick FSM creation")
    print("   ✅ Enhanced state creation with inline callbacks")
    print("   ✅ Bulk transition operations")
    print("   ✅ Bidirectional and emergency transitions")
    print("   ✅ Rich introspection and query methods")
    print("   ✅ Debug information and validation")
    print("   ✅ Condition builder decorators")
    print("   ✅ Safe trigger operations")
    print("   ✅ Enhanced error reporting")


if __name__ == '__main__':
    main()
