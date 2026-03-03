# Fast FSM Usability Improvements

This document outlines the comprehensive usability improvements made to the Fast FSM library to make it more developer-friendly and easier to use.

## 🚀 Factory Methods for Quick FSM Creation

### StateMachine.from_states(states, name)
Create an FSM from a list of state names:
```python
fsm = StateMachine.from_states(['idle', 'running', 'error'], name='QuickFSM')
```

### StateMachine.quick_build(name, transitions)
Create an FSM from a transition configuration:
```python
fsm = StateMachine.quick_build('Traffic', [
    ('red', 'timer', 'green'),
    ('green', 'timer', 'yellow'),
    ('yellow', 'timer', 'red')
])
```

### simple_fsm(states, transitions, initial=None, name=None)
Convenience function for rapid FSM creation:
```python
fsm = simple_fsm(
    states=['waiting', 'processing', 'done'],
    transitions=[
        ('waiting', 'start', 'processing'),
        ('processing', 'complete', 'done')
    ],
    initial='waiting'
)
```

### quick_fsm(name, states, initial=None)
Create FSM with auto-generated transitions:
```python
fsm = quick_fsm('OrderProcessor', ['pending', 'processing', 'shipped'])
```

## 🎭 Enhanced State Creation

### State.create() Factory Method
Create states with enhanced options:
```python
state = State.create(
    'processing',
    enter_actions=[lambda: print("Starting work")],
    exit_actions=[lambda: print("Work done")]
)
```

### CallbackState Class
Define states with inline callbacks:
```python
processing = CallbackState(
    'processing',
    on_enter=lambda *args: print(f"Processing {args}"),
    on_exit=lambda: print("Done processing")
)
```

## 🔄 Bulk Transition Operations

### add_transitions()
Add multiple transitions at once:
```python
fsm.add_transitions([
    ('idle', 'start', 'running'),
    ('running', 'pause', 'paused'),
    ('paused', 'resume', 'running')
])
```

### add_bidirectional_transition()
Create two-way transitions:
```python
fsm.add_bidirectional_transition('running', 'paused', 'pause', 'resume')
```

### add_emergency_transition()
Add emergency transition from all states:
```python
fsm.add_emergency_transition('emergency_stop', 'error')
```

## 🔍 Rich Introspection Methods

### Query Methods
- `fsm.states` - Get all state names
- `fsm.triggers` - Get all trigger names
- `fsm.get_available_triggers()` - Get triggers from current state
- `fsm.get_reachable_states()` - Get states reachable from current state
- `fsm.transition_exists(trigger, from_state=None)` - Check if transition exists

### Debug Methods
- `fsm.debug_info()` - Get comprehensive debug information
- `fsm.print_debug_info()` - Print debug info to console
- `fsm.validate_transition_completeness()` - Find dead ends and unreachable states

## 🛡️ Safe Operations and Error Handling

### safe_trigger()
Exception-safe triggering with detailed error reporting:
```python
success, error = fsm.safe_trigger('start')
if not success:
    print(f"Transition failed: {error}")
```

### Enhanced Error Messages
All operations now provide clear, actionable error messages with context about what went wrong and why.

## 🎯 Condition Helpers

### condition_builder Decorator
Create conditions with metadata:
```python
@condition_builder("has_fuel", "Check if fuel level > 10")
def fuel_check(fuel_level):
    return fuel_level > 10

fsm.add_transition('idle', 'start', 'running', conditions=[fuel_check])
```

## 🔧 Enhanced Argument Support

All condition and callback functions now support both `*args` and `**kwargs`:
```python
# Conditions can accept any arguments
def check_level(level, threshold=10, *args, **kwargs):
    return level > threshold

# Callbacks too
def on_enter(state_name, *extra_args, **context):
    print(f"Entering {state_name} with {extra_args}")
```

## 📊 Usage Examples

### Complete Example: Order Processing System
```python
from fast_fsm import simple_fsm, CallbackState, condition_builder

# Create states with callbacks
pending = CallbackState('pending', 
    on_enter=lambda: print("Order received"))
processing = CallbackState('processing',
    on_enter=lambda order_id: print(f"Processing order {order_id}"))
shipped = CallbackState('shipped',
    on_enter=lambda: print("Order shipped"))

# Define conditions
@condition_builder("has_inventory", "Check inventory availability")
def check_inventory(item_count):
    return item_count > 0

# Create FSM
fsm = StateMachine.from_states(['pending', 'processing', 'shipped'])
fsm.add_state(pending)
fsm.add_state(processing) 
fsm.add_state(shipped)

# Add transitions with conditions
fsm.add_transition('pending', 'process', 'processing', 
                  conditions=[check_inventory])
fsm.add_transition('processing', 'ship', 'shipped')
fsm.add_emergency_transition('cancel', 'cancelled')

# Use the FSM safely
success, error = fsm.safe_trigger('process', 5)  # item_count=5
if success:
    print(f"Current state: {fsm.current_state}")
else:
    print(f"Failed: {error}")
```

## 🎉 Benefits

These improvements make the Fast FSM library:

1. **Faster to prototype** - Factory methods and quick builders
2. **More intuitive** - Enhanced state creation and bulk operations  
3. **Easier to debug** - Rich introspection and debug methods
4. **More robust** - Safe operations and better error handling
5. **More flexible** - Enhanced argument passing throughout
6. **Better documented** - Clear error messages and metadata support

The library now provides multiple levels of abstraction, from quick prototyping functions to detailed control over every aspect of the FSM behavior.
