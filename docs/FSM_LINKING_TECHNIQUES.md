# FSM Linking Techniques - Complete Guide

This guide covers all the major techniques for linking Finite State Machines (FSMs) together to create complex, coordinated systems.

## Overview

While FSMs are powerful individually, real-world systems often require multiple FSMs working together. There are **5 major techniques** for linking FSMs, each serving different architectural patterns and use cases.

## 1. 🔗 Condition-based Dependencies

FSM transitions depend on another FSM's current state.

### How it Works
```python
class CrossFSMCondition(Condition):
    def __init__(self, other_fsm: StateMachine, required_state: str):
        self.other_fsm = other_fsm
        self.required_state = required_state
    
    def check(self, *args, **kwargs) -> bool:
        return self.other_fsm.current_state_name == self.required_state

# Usage: Door can only open if alarm is disarmed
alarm_disarmed = CrossFSMCondition(alarm_fsm, 'disarmed')
door_fsm.add_transition('open', 'closed', 'open', condition=alarm_disarmed)
```

### Use Cases
- **Security Systems**: Door can only open when alarm is disarmed
- **Factory Production**: Assembly line can only start when materials are available
- **Industrial Control**: Machine can only start when both power and cooling are ready

### Benefits
- ✅ Real-time validation
- ✅ Loose coupling between FSMs
- ✅ Clear dependency relationships
- ✅ Easy to test and understand

## 2. 💫 Event Cascading

One FSM's state change triggers events in other FSMs through callbacks.

### How it Works
```python
def on_logout(to_state, trigger, *args, **kwargs):
    print("User logout triggered cart clear and payment reset")
    if shopping_cart.current_state_name != 'empty':
        shopping_cart.trigger('clear')
    if payment.current_state_name != 'idle':
        payment._current_state = payment._states['idle']

# Create state with cascade callback
logout_state = CallbackState('logged_out', on_enter=on_logout)
user_session.add_state(logout_state)
```

### Use Cases
- **E-commerce**: User logout clears cart and resets payment
- **Gaming**: Player death triggers inventory drop and respawn sequence
- **System Shutdown**: Stopping one service triggers cleanup in others

### Benefits
- ✅ Immediate action chains
- ✅ Centralized cascade logic
- ✅ Clean separation of concerns
- ✅ Predictable event ordering

## 3. 🏗️ Hierarchical Control

Parent FSM controls child FSMs (system controlling subsystems).

### How it Works
```python
def start_subsystems(from_state, trigger, *args, **kwargs):
    print("Starting all subsystems...")
    network_fsm.trigger('connect')
    database_fsm.trigger('start')
    api_fsm.trigger('start')

def stop_subsystems(from_state, trigger, *args, **kwargs):
    print("Stopping all subsystems...")
    api_fsm.trigger('stop')
    database_fsm.trigger('stop') 
    network_fsm.trigger('disconnect')

# Parent state controls children
running_state = CallbackState('running', on_enter=start_subsystems)
shutdown_state = CallbackState('shutdown', on_enter=stop_subsystems)
```

### Use Cases
- **System Architecture**: Main system controlling subsystems
- **Application Lifecycle**: App states controlling feature modules
- **Device Control**: Master controller managing peripheral devices

### Benefits
- ✅ Clear parent-child relationships
- ✅ Coordinated lifecycle management
- ✅ Centralized control logic
- ✅ Easy to reason about system states

## 4. 👁️ Observer Pattern

FSMs observe and react to each other's state changes dynamically.

### How it Works
```python
class FSMObserver:
    def __init__(self):
        self.observers: Dict[str, List[Callable]] = {}
    
    def subscribe(self, fsm_name: str, callback: Callable):
        if fsm_name not in self.observers:
            self.observers[fsm_name] = []
        self.observers[fsm_name].append(callback)
    
    def notify(self, fsm_name: str, old_state: str, new_state: str, trigger: str):
        if fsm_name in self.observers:
            for callback in self.observers[fsm_name]:
                callback(fsm_name, old_state, new_state, trigger)

class ObservableFSM(StateMachine):
    def trigger(self, trigger_name, *args, **kwargs):
        old_state = self.current_state_name
        result = super().trigger(trigger_name, *args, **kwargs)
        
        if result.success:
            new_state = self.current_state_name
            self.observer.notify(self.name, old_state, new_state, trigger_name)
        
        return result

# Usage
def temperature_observer(fsm_name, old_state, new_state, trigger):
    if new_state == 'critical':
        alarm_fsm.trigger('alert')

observer.subscribe('Temperature', temperature_observer)
```

### Use Cases
- **Monitoring Systems**: Temperature/pressure changes triggering alarms
- **Event-driven Architecture**: Components reacting to state changes
- **Real-time Systems**: Dynamic responses to changing conditions

### Benefits
- ✅ Loose coupling between FSMs
- ✅ Dynamic subscription/unsubscription
- ✅ Event-driven architecture
- ✅ Scalable to many FSMs

## 5. 🤝 Shared Context

FSMs coordinate through shared data/resources.

### How it Works
```python
class SharedContextDemo:
    def __init__(self):
        # Shared context
        self.shared_context = {
            'resource_pool': 100,
            'active_processes': 0,
            'system_load': 0.0
        }
    
    def can_allocate(*args, **kwargs):
        amount = kwargs.get('amount', 10)
        return self.shared_context['resource_pool'] >= amount
    
    def allocate_resources(from_state, trigger, amount=10, *args, **kwargs):
        if self.shared_context['resource_pool'] >= amount:
            self.shared_context['resource_pool'] -= amount
            self.shared_context['active_processes'] += 1
            # Update other FSMs based on shared state
            if self.shared_context['system_load'] > 0.8:
                monitor_fsm.trigger('escalate')

# FSMs use shared context for decisions
scheduler_fsm.add_transition('allocate', 'idle', 'allocating', condition=can_allocate)
```

### Use Cases
- **Resource Management**: Multiple processes sharing CPU/memory
- **Load Balancing**: Distributing work based on current load
- **Inventory Systems**: Multiple consumers sharing stock

### Benefits
- ✅ Centralized resource management
- ✅ Real-time coordination
- ✅ Conflict resolution through shared state
- ✅ Efficient resource utilization

## Choosing the Right Technique

| Technique | Best For | Relationship Type | Coupling Level |
|-----------|----------|-------------------|----------------|
| **Conditions** | State dependencies | "Can only X if Y is in state Z" | Loose |
| **Cascading** | Action chains | "When X happens, do Y and Z" | Medium |
| **Hierarchical** | System control | "Parent controls children" | Tight |
| **Observer** | Reactive systems | "When X changes, Y reacts" | Loose |
| **Shared Context** | Resource coordination | "FSMs share and compete for resources" | Medium |

## Advanced Patterns

### Combining Techniques

You can combine multiple techniques for sophisticated architectures:

#### Hierarchical + Observer
```python
# Parent FSM observes children and makes decisions
class SmartParentFSM:
    def __init__(self):
        self.children = [child1_fsm, child2_fsm, child3_fsm]
        for child in self.children:
            child.subscribe_observer(self.child_state_changed)
    
    def child_state_changed(self, child_name, old_state, new_state, trigger):
        # Parent reacts to child state changes
        if new_state == 'error':
            self.trigger('child_error')
```

#### Shared Context + Conditions
```python
# Conditions check shared resources
@condition_builder(name="sufficient_memory", description="Check available memory")
def memory_available(*args, **kwargs):
    required = kwargs.get('memory_required', 100)
    return shared_context['available_memory'] >= required

process_fsm.add_transition('start', 'idle', 'running', condition=memory_available)
```

#### Cascading + Observer
```python
# Events cascade through an observer network
def critical_event_handler(fsm_name, old_state, new_state, trigger):
    if new_state == 'critical':
        # Cascade to multiple systems
        for emergency_fsm in emergency_systems:
            emergency_fsm.trigger('activate')

observer.subscribe('MainSystem', critical_event_handler)
```

## Implementation Guidelines

### 1. Start Simple
Begin with condition-based dependencies - they're the most straightforward and cover many use cases.

### 2. Consider Coupling
- **Loose coupling**: Conditions, Observer pattern
- **Medium coupling**: Cascading, Shared context
- **Tight coupling**: Hierarchical control

### 3. Think About Scalability
- Observer pattern scales well to many FSMs
- Shared context can become a bottleneck
- Hierarchical works best with clear parent-child relationships

### 4. Test Interactions
- Test FSMs individually first
- Then test interactions between pairs
- Finally test the complete system

### 5. Monitor Performance
- Condition checks happen on every transition
- Observer notifications can create cascades
- Shared context access should be efficient

## Example: Complete Multi-FSM System

Here's how you might combine techniques in a real system:

```python
class OrderProcessingSystem:
    def __init__(self):
        # Shared context for coordination
        self.shared_state = {
            'inventory': {'item1': 100, 'item2': 50},
            'active_orders': 0,
            'system_load': 0.0
        }
        
        # Create FSMs
        self.user_session = UserSessionFSM()
        self.order_fsm = OrderFSM()
        self.payment_fsm = PaymentFSM()
        self.inventory_fsm = InventoryFSM()
        
        # Set up relationships
        self._setup_conditions()      # For dependencies
        self._setup_cascading()       # For logout cleanup
        self._setup_observers()       # For monitoring
        self._setup_shared_context()  # For resource coordination
    
    def _setup_conditions(self):
        # Order can only be placed if user is logged in
        user_logged_in = CrossFSMCondition(self.user_session, 'logged_in')
        self.order_fsm.add_transition('place', 'draft', 'placed', condition=user_logged_in)
    
    def _setup_cascading(self):
        # User logout triggers order and payment cleanup
        def cleanup_on_logout(*args, **kwargs):
            self.order_fsm.trigger('cancel')
            self.payment_fsm.trigger('reset')
        
        logout_state = CallbackState('logged_out', on_enter=cleanup_on_logout)
        self.user_session.add_state(logout_state)
    
    def _setup_observers(self):
        # Monitor order completion to update inventory
        def order_observer(fsm_name, old_state, new_state, trigger):
            if new_state == 'completed':
                self.inventory_fsm.trigger('update_stock')
        
        self.observer.subscribe('Order', order_observer)
    
    def _setup_shared_context(self):
        # Inventory checks use shared state
        @condition_builder(name="stock_available", description="Check inventory")
        def stock_check(item, quantity, **kwargs):
            return self.shared_state['inventory'].get(item, 0) >= quantity
        
        self.order_fsm.add_transition('confirm', 'placed', 'confirmed', 
                                    condition=stock_check)
```

## Conclusion

FSM linking techniques provide powerful ways to create complex, coordinated systems:

- **Start with conditions** for basic dependencies
- **Add cascading** for action chains
- **Use hierarchical** for clear parent-child relationships
- **Implement observers** for event-driven architecture
- **Share context** for resource coordination

Choose techniques based on your specific needs, and don't hesitate to combine them for sophisticated architectures. The Fast FSM library supports all these patterns natively, making it easy to build robust multi-FSM systems.

## Further Reading

- [Fast FSM Usability Improvements](USABILITY_IMPROVEMENTS.md)
- [Performance Optimization Guide](PERFORMANCE_GUIDE.md) 
- [Advanced Patterns and Best Practices](ADVANCED_PATTERNS.md)
