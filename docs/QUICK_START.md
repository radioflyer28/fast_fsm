# 🚀 Fast FSM - Quick Start Guide

**Get up and running with Fast FSM in under 5 minutes!**

Fast FSM is a high-performance finite state machine library that's both blazingly fast (250K+ transitions/sec) and easy to use. This guide shows you the quickest path from zero to a working FSM.

## 📦 Installation

**Requires Python ≥ 3.10.** The only runtime dependency is `mypy-extensions ≥ 1.0`.

```bash
# Clone the repository
git clone <repository-url>
cd fast_fsm

# Install dependencies (if using uv)
uv sync

# Or with pip
pip install -e .
```

## 🎯 Your First FSM (30 seconds)

Let's create a simple traffic light in just a few lines:

```python
from fast_fsm import simple_fsm

# Create a traffic light FSM
traffic = simple_fsm(
    'red', 'yellow', 'green',  # states
    initial='red',
    name='TrafficLight'
)

# Add transitions
traffic.add_transition('timer', 'red', 'green')
traffic.add_transition('timer', 'green', 'yellow') 
traffic.add_transition('timer', 'yellow', 'red')

# Use it!
print(f"Current: {traffic.current_state}")  # red
traffic.trigger('timer')
print(f"Current: {traffic.current_state}")  # green
traffic.trigger('timer')  
print(f"Current: {traffic.current_state}")  # yellow
```

**🎉 Congratulations!** You just created your first Fast FSM.

## 🔄 Common Patterns (2 minutes)

### Pattern 1: Quick Build from Transitions
Perfect when you know all your transitions upfront:

```python
from fast_fsm import StateMachine

# Define all transitions at once
order_fsm = StateMachine.quick_build(
    initial_state='pending',
    transitions=[
        ('pay', 'pending', 'paid'),
        ('process', 'paid', 'processing'),
        ('ship', 'processing', 'shipped'),
        ('deliver', 'shipped', 'delivered')
    ],
    name='OrderProcessor'
)

# Process an order
order_fsm.trigger('pay')
order_fsm.trigger('process')
print(f"Order status: {order_fsm.current_state}")  # processing
```

### Pattern 2: Conditional Transitions
Add business logic with conditions:

```python
from fast_fsm import StateMachine, State

def has_inventory(item_count=0, **kwargs):
    return item_count > 0

# Create states
pending = State('pending')
processing = State('processing')

fsm = StateMachine(pending, name='InventoryCheck')
fsm.add_state(processing)

# Add conditional transition
fsm.add_transition('process', 'pending', 'processing', condition=has_inventory)

# Not enough inventory — transition fails, FSM stays in 'pending'
result = fsm.trigger('process', item_count=0)
print(f"Success: {result.success}")  # False
print(f"Error: {result.error}")

# With stock — transition succeeds
result = fsm.trigger('process', item_count=5)
print(f"Success: {result.success}")  # True
```

### Pattern 3: State Callbacks
Run code when entering/exiting states:

```python
from fast_fsm import State

# Create states with callbacks
def on_enter_processing(*args, **kwargs):
    print("🔄 Started processing...")

def on_exit_processing(*args, **kwargs):
    print("✅ Processing complete!")

processing = State.create(
    'processing',
    on_enter=on_enter_processing,
    on_exit=on_exit_processing
)

idle = State('idle')
done = State('done')

fsm = StateMachine(idle, name='CallbackDemo')
fsm.add_state(processing)
fsm.add_state(done)
fsm.add_transition('start', 'idle', 'processing')
fsm.add_transition('finish', 'processing', 'done')

fsm.trigger('start')   # Prints: 🔄 Started processing...
fsm.trigger('finish')  # Prints: ✅ Processing complete!
```

### Pattern 4: Checking Active State
Use `is_in()` to query the current state by name or object:

```python
from fast_fsm import StateMachine, State

idle = State('idle')
running = State('running')

fsm = StateMachine(idle, name='Check')
fsm.add_state(running)
fsm.add_transition('start', 'idle', 'running')
fsm.add_transition('stop', 'running', 'idle')

# String check — convenient for most cases
assert fsm.is_in('idle')       # True
assert not fsm.is_in('running')

# Object-identity check — useful when you hold a reference
assert fsm.is_in(idle)         # True — identity comparison

fsm.trigger('start')
assert fsm.is_in('running')
assert fsm.is_in(running)      # True
assert not fsm.is_in(idle)
```

Both forms are O(1).

### Pattern 5: Listeners (Observer Pattern)
Watch transitions without touching FSM logic:

```python
from fast_fsm import StateMachine

class TransitionLogger:
    """Log every successful transition."""
    def after_transition(self, source, target, trigger, **kwargs):
        print(f"  {source.name} --[{trigger}]--> {target.name}")

class History:
    """Record full transition history."""
    def __init__(self):
        self.log = []

    def after_transition(self, source, target, trigger, **kwargs):
        self.log.append((source.name, trigger, target.name))

fsm = StateMachine.quick_build(
    "idle",
    [("start", "idle", "running"), ("stop", "running", "idle")],
    name="Demo",
)

hist = History()
fsm.add_listener(TransitionLogger(), hist)

fsm.trigger("start")  # prints: idle --[start]--> running
fsm.trigger("stop")   # prints: running --[stop]--> idle

print(hist.log)  # [('idle', 'start', 'running'), ('running', 'stop', 'idle')]
```

Each listener can implement any combination of:
- `on_exit_state(source, target, trigger, **kwargs)` — called after the state's own `on_exit`
- `on_enter_state(target, source, trigger, **kwargs)` — called after the state's own `on_enter`
- `after_transition(source, target, trigger, **kwargs)` — called last, once per successful trigger

Listener exceptions are logged and **never crash the FSM**. Zero overhead when no
listeners are registered.

### Pattern 6: Typed Constants with StrEnum *(Python 3.11+)*

Avoid scattered magic strings by defining states and triggers as `StrEnum`
members. Because `StrEnum` *is* a `str`, every fast_fsm API that accepts a
string accepts a `StrEnum` value directly — no conversion needed.
On Python 3.10, use `class MyState(str, Enum)` instead.

```{testcode}
from enum import StrEnum
from fast_fsm import StateMachine

class OrderState(StrEnum):
    PENDING = "pending"
    PAID    = "paid"
    SHIPPED = "shipped"

class OrderTrigger(StrEnum):
    PAY  = "pay"
    SHIP = "ship"

order_fsm = StateMachine.quick_build(
    OrderState.PENDING,
    [
        (OrderTrigger.PAY,  OrderState.PENDING, OrderState.PAID),
        (OrderTrigger.SHIP, OrderState.PAID,    OrderState.SHIPPED),
    ],
    name="OrderFSM",
)

order_fsm.trigger(OrderTrigger.PAY)
print(order_fsm.current_state_name)

assert order_fsm.is_in(OrderState.PAID)  # StrEnum == str

match order_fsm.current_state_name:
    case OrderState.PAID:
        print("Payment confirmed")
    case OrderState.SHIPPED:
        print("Order shipped")
```

```{testoutput}
paid
Payment confirmed
```

### Pattern 7: Error-handling with `raise_if_failed()`

By default `trigger()` returns a `TransitionResult` and never raises. Use
`raise_if_failed()` when you prefer exception-based control flow:

```python
from fast_fsm import StateMachine, TransitionError

fsm = StateMachine.quick_build(
    "idle",
    [("start", "idle", "running"), ("stop", "running", "idle")],
    name="Demo",
)

# Chaining — raises TransitionError if the trigger failed
try:
    fsm.trigger("start").raise_if_failed()
except TransitionError as exc:
    print(f"Failed: {exc.result.error}")

# One-liner when you also need the destination state
target = fsm.trigger("stop").raise_if_failed().to_state
print(target)  # "idle"
```

### Pattern 8: Runtime State Control

`snapshot()`/`restore()` persist current state across sessions. `clone()` spins
up an independent copy from the same topology. `force_state()`/`reset()` bypass
guards — useful in tests.

```python
# Snapshot & restore (JSON/pickle safe)
snap = fsm.snapshot()        # {"state": "idle", "version": 1}
# ... time passes ...
fsm.restore(snap)            # teleports back; callbacks fire

# Clone — same topology, fresh start, empty listeners
worker = fsm.clone()

# Force & reset — bypass guards
fsm.force_state("running")   # useful in tests / error recovery
fsm.reset()                  # returns to initial_state_name

# Programmatic callbacks (attach after construction)
fsm.on_enter("running", lambda from_s, t, **kw: print("→ running"))
fsm.on_exit("running",  lambda to_s,   t, **kw: print("← running"))

# Build from a dict / JSON / YAML config
config = {
    "initial": "idle",
    "transitions": [
        {"trigger": "start",  "from": "idle",    "to": "running"},
        {"trigger": "stop",   "from": "running", "to": "idle"},
    ],
}
fsm2 = StateMachine.from_dict(config, name="FromConfig")
# Attach guards at construction with conditions={trigger_name: condition}:
# fsm2 = StateMachine.from_dict(config, conditions={"start": FuncCondition(guard_fn)})
```

## 🎓 Next Steps (Choose Your Path)

### 🚀 **I want to build something NOW** → [Real-World Examples](#real-world-examples)
### 🔧 **I need more control** → [Builder Pattern Guide](#builder-pattern-guide)  
### 🌐 **I need async support** → [Async FSM Guide](#async-fsm-guide)
### 📊 **I care about performance** → [Performance Guide](#performance-guide)
### 🔍 **I want validation** → [Validation Guide](#validation-guide)

## 📋 Real-World Examples

### E-commerce Order Processing
```python
from fast_fsm import StateMachine, State

class OrderState(State):
    def on_enter(self, from_state, trigger, order_id=None, **kwargs):
        print(f"📦 Order {order_id}: {self.name}")

# Build the FSM with typed states from the start
from fast_fsm import FSMBuilder
_ost = {n: OrderState(n) for n in ['pending', 'paid', 'processing', 'shipped', 'delivered', 'cancelled']}
order_fsm = (FSMBuilder(_ost['pending'], name='OrderProcessor')
    .add_state(_ost['paid'])
    .add_state(_ost['processing'])
    .add_state(_ost['shipped'])
    .add_state(_ost['delivered'])
    .add_state(_ost['cancelled'])
    .add_transition('payment_received', 'pending', 'paid')
    .add_transition('start_processing', 'paid', 'processing')
    .add_transition('ship_order', 'processing', 'shipped')
    .add_transition('deliver_order', 'shipped', 'delivered')
    .add_transition('cancel_order', ['pending', 'paid'], 'cancelled')
    .build())

# Process an order
order_fsm.trigger('payment_received', order_id="ORD-001")
order_fsm.trigger('start_processing', order_id="ORD-001")
order_fsm.trigger('ship_order', order_id="ORD-001")
```

### Game Character AI
```python
from fast_fsm import StateMachine, State

def low_health(health=100, **kwargs):
    return health < 30

def enemy_nearby(enemy_distance=100, **kwargs):
    return enemy_distance < 10

# Character states
patrol = State('patrol')
chase = State('chase')
flee = State('flee')

ai_fsm = StateMachine(patrol, name='CharacterAI')
ai_fsm.add_state(chase)
ai_fsm.add_state(flee)

# AI behavior transitions
ai_fsm.add_transition('spot_enemy', 'patrol', 'chase', condition=enemy_nearby)
ai_fsm.add_transition('lose_enemy', 'chase', 'patrol')
ai_fsm.add_transition('take_damage', ['patrol', 'chase'], 'flee', condition=low_health)
ai_fsm.add_transition('heal_up', 'flee', 'patrol')

# Test the AI
ai_fsm.trigger('spot_enemy', enemy_distance=5)    # patrol -> chase
ai_fsm.trigger('take_damage', health=20)          # chase -> flee
```

## 🔧 Builder Pattern Guide

For complex FSMs, use the builder pattern:

```python
from fast_fsm import FSMBuilder, State, Condition

class InventoryCondition(Condition):
    def __init__(self, min_stock):
        super().__init__(f"inventory>={min_stock}")
        self.min_stock = min_stock
    
    def check(self, stock=0, **kwargs):
        return stock >= self.min_stock

# Build complex FSM with fluent interface
warehouse_fsm = (FSMBuilder(State('receiving'), name='Warehouse')
    .add_state(State('storing'))
    .add_state(State('picking'))
    .add_state(State('shipping'))
    .add_state(State('out_of_stock'))
    
    # Normal flow
    .add_transition('store', 'receiving', 'storing')
    .add_transition('fulfill_order', 'storing', 'picking', 
                   condition=InventoryCondition(min_stock=1))
    .add_transition('ship', 'picking', 'shipping')
    .add_transition('restock', 'shipping', 'receiving')
    
    # Error handling
    .add_transition('stock_out', 'storing', 'out_of_stock')
    .add_transition('emergency_restock', 'out_of_stock', 'receiving')
    
    # Per-state callbacks registered in the same fluent chain:
    .on_enter('picking', lambda from_s, t, **kw: print(f"Picking order (from {from_s.name})"))
    .on_exit('shipping', lambda to_s, t, **kw: print(f"Shipment dispatched → {to_s.name}"))
    
    .build())

# Use the warehouse FSM
warehouse_fsm.trigger('store')
warehouse_fsm.trigger('fulfill_order', stock=5)  # Success
print(f"Warehouse state: {warehouse_fsm.current_state}")  # picking
```

## 🌐 Async FSM Guide

For async operations (sensors, APIs, etc.):

```python
import asyncio
from fast_fsm import AsyncStateMachine, AsyncCondition, State

class TemperatureSensor(AsyncCondition):
    def __init__(self, threshold):
        super().__init__(f"temp>={threshold}")
        self.threshold = threshold
    
    async def check_async(self, **kwargs):
        # Simulate async sensor reading
        await asyncio.sleep(0.1)
        temperature = 75  # Mock sensor value
        return temperature >= self.threshold

# Create async FSM
async def main():
    monitoring = State('monitoring')
    alert = State('alert')
    
    fsm = AsyncStateMachine(monitoring, name='TempMonitor')
    fsm.add_state(alert)
    fsm.add_transition('check_temp', 'monitoring', 'alert', 
                      condition=TemperatureSensor(threshold=80))
    
    # Trigger async transition
    result = await fsm.trigger_async('check_temp')
    print(f"Alert triggered: {result.success}")

# Run async FSM
asyncio.run(main())
```

## 📊 Performance Guide

Fast FSM is optimized for speed and memory:

### Memory Optimization
- Uses `__slots__` for 1000x better memory efficiency
- Direct state references (no string lookups)
- ~0.2KB memory footprint vs 25-40KB for alternatives

### Speed Optimization  
- 250K+ transitions per second
- O(1) transition lookup
- Minimal function call overhead
- Optional features don't impact performance

### Performance Tips
```python
# ✅ Good: Use state objects when possible
state1 = State('state1')
fsm.add_transition('go', state1, 'state2')  # O(1) lookup

# ✅ Good: Pre-create conditions for reuse
inventory_check = InventoryCondition(min_stock=1)
fsm.add_transition('process', 'pending', 'processing', condition=inventory_check)

# ⚠️ Slower: Creating conditions every time
fsm.add_transition('process', 'pending', 'processing', 
                  condition=lambda stock=0: stock >= 1)  # Creates new FuncCondition each time
```

## 🔍 Validation Guide

Optional validation for complex FSMs:

```python
from fast_fsm.validation import validate_fsm, quick_validation_report

# Quick validation
quick_validation_report(fsm)

# Detailed analysis
validator = validate_fsm(fsm)
completeness = validator.validate_completeness()
print(f"Complete: {completeness['is_complete']}")
print(f"Unreachable states: {completeness['unreachable_states']}")

# Generate test scenarios
test_paths = validator.generate_test_paths(max_length=5)
for path in test_paths[:3]:
    print("Test scenario:", " -> ".join([f"{s}[{e}]" for s, e, _ in path]))
```

## 🎯 Common Gotchas & Solutions

### 1. **Callbacks Not Called**
```python
# ❌ Wrong: Regular State doesn't support constructor callbacks
state = State('processing', on_enter=my_callback)  # Error!

# ✅ Right: Use State.create() or CallbackState
state = State.create('processing', on_enter=my_callback)
# OR
from fast_fsm import CallbackState
state = CallbackState('processing', on_enter=my_callback)
# OR: attach callbacks directly to the machine after construction
fsm.on_enter('processing', my_callback)   # fires after the state's own on_enter
fsm.on_exit('processing',  my_other_cb)
```

### 2. **Condition Not Working**
```python
# ❌ Wrong: Condition doesn't receive arguments
def check_health():  # Missing *args, **kwargs
    return health > 0

# ✅ Right: Always accept arguments
def check_health(*args, **kwargs):
    health = kwargs.get('health', 100)
    return health > 0
```

### 3. **Async/Sync Mismatch**
```python
# ❌ Wrong: Using AsyncCondition with regular StateMachine — now raises TypeError
async_condition = MyAsyncCondition()
fsm = StateMachine(state)
fsm.add_transition('go', 'a', 'b', condition=async_condition)  # TypeError!

# ✅ Right: Use AsyncStateMachine for async conditions
fsm = AsyncStateMachine(state)  # Now async conditions work
# OR let FSMBuilder auto-detect
fsm = FSMBuilder(state).add_transition('go', 'a', 'b', condition=async_condition).build()
```

## 🏁 You're Ready!

**Congratulations!** You now know:
- ✅ How to create FSMs quickly with `simple_fsm()`
- ✅ How to use conditions for business logic
- ✅ How to add state callbacks
- ✅ When to use the builder pattern
- ✅ How to handle async operations
- ✅ Performance optimization techniques
- ✅ How to validate complex FSMs

**Next Steps:**
- Browse the [examples/](examples/) directory for more real-world scenarios
- Check out [README.md](README.md) for complete API documentation
- Run `python verify_readme.py` to see all examples in action
- Explore [USABILITY_IMPROVEMENTS.md](USABILITY_IMPROVEMENTS.md) for advanced features

**Need help?** The library has comprehensive type hints and clear error messages to guide you.

**Happy state machining!** 🚀