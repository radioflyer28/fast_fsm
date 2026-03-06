# 🎓 Fast FSM Tutorial Mode

**Learn Fast FSM step by step, from beginner to expert**

This tutorial guides you through Fast FSM's capabilities in progressive complexity levels. Each level builds on the previous, so you can stop when you've learned what you need.

---

## 📊 Tutorial Roadmap

| Level | What You'll Learn | Time | When to Use |
|-------|------------------|------|-------------|
| **🟢 Level 1: Basics** | Create simple FSMs, transitions | 5 min | First-time users |
| **🟡 Level 2: Control** | Conditions, error handling | 10 min | Business logic needed |
| **🟠 Level 3: Advanced** | Callbacks, complex patterns | 15 min | Production applications |
| **🔴 Level 4: Expert** | Async, performance, validation | 20 min | High-performance systems |

---

## 🟢 Level 1: The Basics (5 minutes)

**Goal:** Create your first working FSM and understand core concepts.

### Step 1.1: Your First State Machine
```python
from fast_fsm import simple_fsm

# Create the simplest possible FSM
light = simple_fsm('off', 'on', initial='off', name='LightSwitch')

# Add a transition  
light.add_transition('flip', 'off', 'on')
light.add_transition('flip', 'on', 'off')

# Use it
print(f"Light is: {light.current_state}")  # off
light.trigger('flip')
print(f"Light is: {light.current_state}")  # on
```

**🎯 Key Concept:** FSMs have states and transitions. `trigger()` moves between states.

### Step 1.2: Understanding Results
```python
# trigger() returns a result object
result = light.trigger('flip')
print(f"Success: {result.success}")      # True
print(f"From: {result.from_state}")      # on  
print(f"To: {result.to_state}")          # off

# What happens with invalid transitions?
result = light.trigger('explode')
print(f"Success: {result.success}")      # False
print(f"Error: {result.error}")          # No transition 'explode' from state 'off'
```

**🎯 Key Concept:** Always check results. Failed transitions return helpful error messages.

### Step 1.3: Multiple States
```python
# Traffic light with 3 states
traffic = simple_fsm('red', 'yellow', 'green', initial='red', name='Traffic')

traffic.add_transition('timer', 'red', 'green')
traffic.add_transition('timer', 'green', 'yellow')  
traffic.add_transition('timer', 'yellow', 'red')

# Cycle through states
for i in range(6):
    print(f"Light: {traffic.current_state}")
    traffic.trigger('timer')
```

**🎯 Key Concept:** FSMs can have any number of states and transitions.

### ✅ Level 1 Complete!
**You now know:** Basic FSM creation, transitions, and result handling.
**Performance note:** These operations are O(1) - instant even with thousands of states.

---

## 🟡 Level 2: Adding Control (10 minutes)

**Goal:** Add business logic with conditions and handle errors gracefully.

### Step 2.1: Conditional Transitions
```python
from fast_fsm import StateMachine, State

def can_afford(price=0, money=0, **kwargs):
    return money >= price

# Vending machine
waiting = State('waiting')
dispensing = State('dispensing')

vending = StateMachine(waiting, name='VendingMachine')
vending.add_state(dispensing)

# Only dispense if customer has enough money
vending.add_transition('buy', 'waiting', 'dispensing', condition=can_afford)
vending.add_transition('complete', 'dispensing', 'waiting')

# Test with different amounts
result = vending.trigger('buy', price=150, money=100)
print(f"Purchase: {result.success}")  # False - not enough money

result = vending.trigger('buy', price=150, money=200)  
print(f"Purchase: {result.success}")  # True - enough money
```

**🎯 Key Concept:** Conditions control when transitions can happen. They receive all trigger arguments.

### Step 2.2: Complex Conditions
```python
def can_login(username="", password="", attempts=0, **kwargs):
    # Multiple checks in one condition
    valid_user = username == "admin"
    valid_pass = password == "secret"  
    not_locked = attempts < 3
    return valid_user and valid_pass and not_locked

# Login system
logged_out = State('logged_out')
logged_in = State('logged_in')
locked = State('locked')

auth = StateMachine(logged_out, name='AuthSystem')
auth.add_state(logged_in)
auth.add_state(locked)

auth.add_transition('login', 'logged_out', 'logged_in', condition=can_login)
auth.add_transition('logout', 'logged_in', 'logged_out')
auth.add_transition('lock', 'logged_out', 'locked')

# Test login attempts
auth.trigger('login', username="admin", password="wrong", attempts=1)
print(f"Status: {auth.current_state}")  # logged_out

auth.trigger('login', username="admin", password="secret", attempts=1)  
print(f"Status: {auth.current_state}")  # logged_in
```

**🎯 Key Concept:** Conditions can be as complex as needed. They're just Python functions.

### Step 2.3: Safe Operations
```python
# safe_trigger won't throw exceptions
result = auth.safe_trigger('invalid_action')
print(f"Safe result: {result.success}")  # False
print(f"Error: {result.error}")          # Helpful error message

# Check before triggering
if auth.can_trigger('logout'):
    auth.trigger('logout')
    print("Logged out successfully")

# Exception-based alternative — raise_if_failed() raises TransitionError on failure
from fast_fsm import TransitionError
try:
    auth.trigger('logout').raise_if_failed()
except TransitionError as exc:
    print(f"Transition failed: {exc.result.error}")

# Chain directly when you need the destination
target = auth.trigger('login', user='alice').raise_if_failed().to_state
```

**🎯 Key Concept:** Use `safe_trigger()` / `can_trigger()` for result-based flow, or `raise_if_failed()` + `TransitionError` for exception-based flow.

### Step 2.4: Multiple Source States
```python
# Emergency transitions from multiple states
auth.add_transition('emergency_reset', ['logged_in', 'locked'], 'logged_out')

# Demonstrate from locked state — move there via the defined 'lock' transition
auth.trigger('lock')
auth.trigger('emergency_reset')
print(f"After reset: {auth.current_state}")  # logged_out
```

**🎯 Key Concept:** One transition can apply to multiple source states.

### ✅ Level 2 Complete!
**You now know:** Conditional logic, error handling, and multiple source transitions.
**Performance note:** Condition evaluation is O(1) and cached when possible.

---

## 🟠 Level 3: Advanced Patterns (15 minutes)

**Goal:** Use callbacks, build complex FSMs, and handle real-world scenarios.

### Step 3.1: State Callbacks
```python
from fast_fsm import State

# Track execution with callbacks
execution_log = []

def log_enter(from_state, trigger, *args, **kwargs):
    execution_log.append(f"Entered from {from_state.name if from_state else 'start'}")

def log_exit(to_state, trigger, *args, **kwargs):
    execution_log.append(f"Exiting to {to_state.name}")

# Create states with callbacks
processing = State.create(
    'processing',
    on_enter=log_enter,
    on_exit=log_exit
)

idle = State('idle')
done = State('done')

workflow = StateMachine(idle, name='Workflow')
workflow.add_state(processing)
workflow.add_state(done)

workflow.add_transition('start', 'idle', 'processing')
workflow.add_transition('finish', 'processing', 'done')

# Watch callbacks in action
workflow.trigger('start')
workflow.trigger('finish')

print("Execution log:")
for entry in execution_log:
    print(f"  {entry}")
```

**🎯 Key Concept:** Callbacks let you run code during state transitions. Perfect for logging, cleanup, notifications.

### Step 3.2: Builder Pattern for Complex FSMs
```python
from fast_fsm import FSMBuilder, State

# Complex order processing system
class OrderState(State):
    def on_enter(self, from_state, trigger, order_id=None, **kwargs):
        print(f"📦 Order {order_id}: Entered {self.name}")

def has_payment(payment_method=None, **kwargs):
    return payment_method is not None

def has_inventory(item_id=None, inventory=None, **kwargs):
    return inventory and inventory.get(item_id, 0) > 0

def can_ship(shipping_address=None, **kwargs):
    return shipping_address and len(shipping_address) > 10

# Build complex FSM with fluent interface
order_processor = (FSMBuilder(OrderState('pending'), name='OrderProcessor')
    .add_state(OrderState('payment_verified'))
    .add_state(OrderState('inventory_checked'))  
    .add_state(OrderState('ready_to_ship'))
    .add_state(OrderState('shipped'))
    .add_state(OrderState('cancelled'))
    
    # Happy path
    .add_transition('verify_payment', 'pending', 'payment_verified', condition=has_payment)
    .add_transition('check_inventory', 'payment_verified', 'inventory_checked', condition=has_inventory)
    .add_transition('prepare_shipping', 'inventory_checked', 'ready_to_ship', condition=can_ship)
    .add_transition('ship', 'ready_to_ship', 'shipped')
    
    # Error handling
    .add_transition('cancel', ['pending', 'payment_verified', 'inventory_checked'], 'cancelled')
    
    .build())

# Process an order
mock_inventory = {'WIDGET-123': 5}

result = order_processor.trigger('verify_payment', 
                                order_id='ORD-001', 
                                payment_method='credit_card')

result = order_processor.trigger('check_inventory', 
                                order_id='ORD-001',
                                item_id='WIDGET-123', 
                                inventory=mock_inventory)

result = order_processor.trigger('prepare_shipping',
                                order_id='ORD-001',
                                shipping_address='123 Main St, City, State 12345')

print(f"Order status: {order_processor.current_state}")
```

**🎯 Key Concept:** Builder pattern creates complex FSMs with clean, readable code.

### Step 3.3: Bulk Operations
```python
# Add multiple transitions at once
transitions = [
    ('event1', 'state_a', 'state_b'),
    ('event2', 'state_b', 'state_c'), 
    ('event3', 'state_c', 'state_a'),
    ('reset', ['state_a', 'state_b', 'state_c'], 'state_a')
]

# Quick build from transition list
bulk_fsm = StateMachine.quick_build(
    initial_state='state_a',
    transitions=transitions,
    name='BulkDemo'
)

print(f"States: {bulk_fsm.states}")
print(f"Can trigger 'event1': {bulk_fsm.can_trigger('event1')}")
```

**🎯 Key Concept:** Bulk operations speed up FSM construction for complex systems.

### Step 3.4: Emergency and Bidirectional Transitions
```python
# Add emergency transitions (from any state to target)
order_processor.add_emergency_transition('system_shutdown', 'cancelled')

# Add bidirectional transitions (A <-> B)
maintenance = State('maintenance')
order_processor.add_state(maintenance)
order_processor.add_bidirectional_transition('enter_maintenance', 'exit_maintenance', 
                                           'ready_to_ship', 'maintenance')

# Test emergency transition
order_processor.trigger('system_shutdown')
print(f"Emergency state: {order_processor.current_state}")  # cancelled
```

**🎯 Key Concept:** Special transition types handle common patterns efficiently.

### ✅ Level 3 Complete!
**You now know:** Callbacks, builder pattern, bulk operations, and special transitions.
**Performance note:** Builder pattern has no runtime overhead - all optimization happens at build time.

---

## 🔴 Level 4: Expert Features (20 minutes)

**Goal:** Handle async operations, optimize performance, and validate complex systems.

### Step 4.1: Async State Machines
```python
import asyncio
from fast_fsm import AsyncStateMachine, AsyncCondition, State

class DatabaseCheck(AsyncCondition):
    def __init__(self, table_name):
        super().__init__(f"check_{table_name}")
        self.table_name = table_name
    
    async def check_async(self, user_id=None, **kwargs):
        # Simulate async database call
        await asyncio.sleep(0.1)  
        # Mock: user exists in database
        return user_id and user_id.startswith('user_')

class APICall(AsyncCondition):
    def __init__(self, endpoint):
        super().__init__(f"api_{endpoint}")
        self.endpoint = endpoint
    
    async def check_async(self, **kwargs):
        # Simulate async API call
        await asyncio.sleep(0.2)
        return True  # Mock success

async def async_demo():
    # Create async FSM
    initializing = State('initializing')
    validating = State('validating') 
    processing = State('processing')
    complete = State('complete')
    
    async_fsm = AsyncStateMachine(initializing, name='AsyncProcessor')
    async_fsm.add_state(validating)
    async_fsm.add_state(processing)
    async_fsm.add_state(complete)
    
    # Add async transitions
    async_fsm.add_transition('validate', 'initializing', 'validating', 
                           condition=DatabaseCheck('users'))
    async_fsm.add_transition('process', 'validating', 'processing',
                           condition=APICall('process_data'))
    async_fsm.add_transition('finish', 'processing', 'complete')
    
    # Execute async transitions
    print(f"Starting: {async_fsm.current_state}")
    
    result = await async_fsm.trigger_async('validate', user_id='user_123')
    print(f"After validate: {async_fsm.current_state}, Success: {result.success}")
    
    result = await async_fsm.trigger_async('process')
    print(f"After process: {async_fsm.current_state}, Success: {result.success}")
    
    result = await async_fsm.trigger_async('finish')
    print(f"Final: {async_fsm.current_state}, Success: {result.success}")

# Run the async demo
asyncio.run(async_demo())
```

**🎯 Key Concept:** AsyncStateMachine handles async conditions transparently. Perfect for I/O operations.

### Step 4.2: Performance Optimization
```python
import time
from fast_fsm import State, StateMachine

# Performance test: Create large FSM
def performance_demo():
    print("🚀 Performance Demo")
    
    # Create FSM with many states (still fast!)
    num_states = 1000
    states = [State(f'state_{i}') for i in range(num_states)]
    
    perf_fsm = StateMachine(states[0], name='PerfTest')
    
    # Add all states - O(1) per operation
    start_time = time.perf_counter()
    for state in states[1:]:
        perf_fsm.add_state(state)
    add_time = time.perf_counter() - start_time
    
    # Add many transitions - O(1) per operation  
    start_time = time.perf_counter()
    for i in range(num_states - 1):
        perf_fsm.add_transition(f'next_{i}', f'state_{i}', f'state_{i+1}')
    transition_time = time.perf_counter() - start_time
    
    # Test transition speed - O(1) per trigger
    start_time = time.perf_counter()
    for i in range(100):  # 100 transitions
        trigger_name = f'next_{i % (num_states - 1)}'
        if perf_fsm.can_trigger(trigger_name):
            perf_fsm.trigger(trigger_name)
    trigger_time = time.perf_counter() - start_time
    
    print(f"Added {num_states} states in {add_time*1000:.2f}ms")
    print(f"Added {num_states-1} transitions in {transition_time*1000:.2f}ms") 
    print(f"Executed 100 transitions in {trigger_time*1000:.2f}ms")
    print(f"Transition rate: {100/trigger_time:.0f} transitions/sec")

performance_demo()
```

**🎯 Key Concept:** Fast FSM maintains O(1) performance even with thousands of states/transitions.

### Step 4.3: Advanced Builder with Auto-Detection
```python
from fast_fsm import FSMBuilder, AsyncCondition

class SmartSensor(AsyncCondition):
    async def check_async(self, **kwargs):
        await asyncio.sleep(0.1)
        return True

# Builder auto-detects async requirements
smart_fsm = (FSMBuilder(State('monitoring'), name='SmartSystem')
    .add_state(State('alerting'))
    .add_state(State('responding'))
    .add_transition('check', 'monitoring', 'alerting', condition=SmartSensor())
    .add_transition('respond', 'alerting', 'responding')
    .build())  # Automatically creates AsyncStateMachine!

print(f"Auto-detected type: {type(smart_fsm).__name__}")  # AsyncStateMachine

# You can also force the type
sync_fsm = (FSMBuilder(State('start'), name='ForcedSync')
    .add_state(State('end'))
    .add_transition('go', 'start', 'end')
    .force_sync()  # Force StateMachine even if async components added
    .build())

print(f"Forced type: {type(sync_fsm).__name__}")  # StateMachine
```

**🎯 Key Concept:** FSMBuilder intelligently chooses the right machine type based on your components.

### Step 4.4: Validation and Testing
```python
from fast_fsm.validation import validate_fsm, quick_validation_report

# Create a complex FSM for validation
complex_fsm = (FSMBuilder(State('start'), name='ComplexSystem')
    .add_state(State('processing'))
    .add_state(State('waiting'))
    .add_state(State('error'))
    .add_state(State('complete'))
    .add_state(State('isolated'))  # This will be unreachable
    
    # Add transitions
    .add_transition('begin', 'start', 'processing')
    .add_transition('wait', 'processing', 'waiting')
    .add_transition('resume', 'waiting', 'processing') 
    .add_transition('error_out', 'processing', 'error')
    .add_transition('recover', 'error', 'processing')
    .add_transition('finish', 'processing', 'complete')
    # Note: 'isolated' state has no transitions to/from it
    
    .build())

# Quick validation report
print("📋 Quick Validation Report:")
quick_validation_report(complex_fsm)

# Detailed validation
print("\n🔍 Detailed Validation:")
validator = validate_fsm(complex_fsm)

# Check completeness
completeness = validator.validate_completeness()
print(f"Complete FSM: {completeness['is_complete']}")
print(f"Unreachable states: {completeness['unreachable_states']}")
print(f"Dead end states: {completeness['dead_states']}")

# Generate test scenarios
print(f"\n🧪 Generated Test Scenarios:")
test_paths = validator.generate_test_paths(max_length=4)
for i, path in enumerate(test_paths[:3]):
    scenario = " -> ".join([f"{s}[{e}]" for s, e, _ in path])
    print(f"Scenario {i+1}: {scenario}")

# Check determinism
determinism = validator.check_determinism()
print(f"\nDeterministic: {determinism['is_deterministic']}")
if not determinism['is_deterministic']:
    for pair in determinism['non_deterministic_transitions']:
        print(f"Conflict: {pair}")
```

**🎯 Key Concept:** Validation helps catch design issues before deployment. Use it for complex systems.

### Step 4.5: Memory and Performance Monitoring
```python
import sys
from fast_fsm import StateMachine, State

def memory_demo():
    print("💾 Memory Efficiency Demo")
    
    # Compare with/without slots
    class RegularState:
        def __init__(self, name):
            self.name = name
    
    # Create equivalent states
    fast_state = State('test')
    regular_state = RegularState('test')
    
    # Check memory usage (approximate)
    fast_size = sys.getsizeof(fast_state)
    regular_size = sys.getsizeof(regular_state) + sys.getsizeof(regular_state.__dict__)
    
    print(f"Fast FSM State: {fast_size} bytes")
    print(f"Regular State: {regular_size} bytes") 
    print(f"Memory savings: {regular_size/fast_size:.1f}x more efficient")
    
    # Test with many states
    num_states = 1000
    fast_states = [State(f'state_{i}') for i in range(num_states)]
    total_fast = sum(sys.getsizeof(s) for s in fast_states)
    
    regular_states = [RegularState(f'state_{i}') for i in range(num_states)]
    total_regular = sum(sys.getsizeof(s) + sys.getsizeof(s.__dict__) for s in regular_states)
    
    print(f"\n{num_states} Fast States: {total_fast/1024:.1f} KB")
    print(f"{num_states} Regular States: {total_regular/1024:.1f} KB")
    print(f"Total savings: {total_regular/total_fast:.1f}x more efficient")

memory_demo()
```

**🎯 Key Concept:** Slots optimization provides massive memory savings, especially important for large systems.

### ✅ Level 4 Complete!
**You now know:** Async operations, performance optimization, auto-detection, validation, and memory efficiency.
**Performance note:** All advanced features maintain O(1) performance characteristics.

---

## 🏆 Graduation: You're Now a Fast FSM Expert!

**Congratulations!** You've mastered all levels of Fast FSM. You now know:

### 🟢 **Level 1 Skills:** Basic FSM creation and transitions
### 🟡 **Level 2 Skills:** Conditional logic and error handling  
### 🟠 **Level 3 Skills:** Callbacks, builder pattern, complex scenarios
### 🔴 **Level 4 Skills:** Async operations, performance optimization, validation

## 🎯 Next Steps

### **For Real Projects:**
1. Start with Level 1-2 for MVP
2. Add Level 3 features as complexity grows
3. Use Level 4 for production systems

### **Performance Guidelines:**
- **Small FSMs** (< 10 states): Any approach works
- **Medium FSMs** (10-100 states): Use builder pattern
- **Large FSMs** (100+ states): Add validation and performance monitoring
- **Async FSMs**: Always use AsyncStateMachine for I/O operations

### **Common Patterns by Use Case:**
- **Web APIs**: Level 2 (conditions for validation)
- **Game AI**: Level 3 (callbacks for actions) 
- **IoT Devices**: Level 4 (async sensors, memory optimization)
- **Trading Systems**: Level 4 (performance critical)
- **Workflow Engines**: Level 3-4 (complex logic, validation)

## 📚 Additional Resources

- **[QUICK_START.md](QUICK_START.md)** - Fast reference guide
- **[README.md](README.md)** - Complete API documentation  
- **[examples/](examples/)** - Real-world examples
- **[USABILITY_IMPROVEMENTS.md](USABILITY_IMPROVEMENTS.md)** - Advanced features
- **Run `python verify_readme.py`** - See all examples working

## 🚀 Go Build Something Amazing!

You now have the knowledge to build high-performance, maintainable state machines for any use case. Fast FSM gives you the tools - use them to create something awesome!

**Remember:** Start simple, add complexity only when needed, and always measure performance for critical applications.

**Happy state machining!** 🎉