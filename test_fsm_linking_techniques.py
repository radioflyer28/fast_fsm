#!/usr/bin/env python3
"""
Additional techniques for linking FSMs together beyond condition-based dependencies
"""

from fast_fsm import StateMachine, State, CallbackState, simple_fsm
from typing import List, Dict, Callable


# Technique 1: Event Cascading - One FSM's transitions trigger events in others
class EventCascadingDemo:
    """FSMs that trigger events in each other through callbacks"""
    
    def __init__(self):
        # Create the FSMs
        self.user_session = simple_fsm('logged_out', 'logged_in', 'suspended', 
                                     initial='logged_out', name='UserSession')
        self.shopping_cart = simple_fsm('empty', 'has_items', 'checked_out', 
                                      initial='empty', name='ShoppingCart')
        self.payment = simple_fsm('idle', 'processing', 'completed', 'failed',
                                initial='idle', name='Payment')
        
        # Set up cascading events
        self._setup_cascading()
    
    def _setup_cascading(self):
        """Set up event cascading between FSMs"""
        
        # When user logs out, clear cart and reset payment
        def on_logout(to_state, trigger, *args, **kwargs):
            print("  🔄 User logout triggered cart clear and payment reset")
            if self.shopping_cart.current_state_name != 'empty':
                self.shopping_cart.trigger('clear')
            if self.payment.current_state_name != 'idle':
                # Force reset payment since we might not have a transition for current state
                self.payment._current_state = self.payment._states['idle']
        
        # Create logout state with callback
        logout_state = CallbackState('logged_out', on_enter=on_logout)
        self.user_session.add_state(logout_state)
        
        # Add transitions
        self.user_session.add_transitions([
            ('login', 'logged_out', 'logged_in'),
            ('logout', ['logged_in', 'suspended'], 'logged_out'),
            ('suspend', 'logged_in', 'suspended')
        ])
        
        self.shopping_cart.add_transitions([
            ('add_item', ['empty', 'has_items'], 'has_items'),
            ('checkout', 'has_items', 'checked_out'),
            ('clear', ['has_items', 'checked_out'], 'empty')
        ])
        
        self.payment.add_transitions([
            ('start', 'idle', 'processing'),
            ('complete', 'processing', 'completed'),
            ('fail', 'processing', 'failed'),
            ('reset', ['completed', 'failed'], 'idle')
        ])
    
    def demo(self):
        print("💫 Event Cascading Demo")
        print("=" * 30)
        
        # User logs in and adds items
        print("1. User logs in and adds items:")
        self.user_session.trigger('login')
        self.shopping_cart.trigger('add_item')
        self.shopping_cart.trigger('add_item')
        print(f"   Session: {self.user_session.current_state_name}")
        print(f"   Cart: {self.shopping_cart.current_state_name}")
        
        # User starts checkout
        print("\n2. User starts checkout:")
        self.shopping_cart.trigger('checkout')
        self.payment.trigger('start')
        print(f"   Cart: {self.shopping_cart.current_state_name}")
        print(f"   Payment: {self.payment.current_state_name}")
        
        # User logs out - triggers cascade
        print("\n3. User logs out (triggers cascade):")
        self.user_session.trigger('logout')
        print(f"   Session: {self.user_session.current_state_name}")
        print(f"   Cart: {self.shopping_cart.current_state_name}")
        print(f"   Payment: {self.payment.current_state_name}")


# Technique 2: Hierarchical FSMs - Parent FSM controls child FSMs
class HierarchicalFSMDemo:
    """Parent FSM that contains and controls child FSMs"""
    
    def __init__(self):
        # Parent FSM - overall system state
        self.system = simple_fsm('startup', 'running', 'shutdown', 'maintenance',
                               initial='startup', name='System')
        
        # Child FSMs - subsystems
        self.network = simple_fsm('disconnected', 'connected', 'error',
                                initial='disconnected', name='Network')
        self.database = simple_fsm('offline', 'online', 'syncing',
                                 initial='offline', name='Database')
        self.api = simple_fsm('stopped', 'running', 'overloaded',
                            initial='stopped', name='API')
        
        # Track child FSMs
        self.subsystems = [self.network, self.database, self.api]
        
        self._setup_hierarchy()
    
    def _setup_hierarchy(self):
        """Set up hierarchical control"""
        
        # Parent state changes control child states
        def start_subsystems(from_state, trigger, *args, **kwargs):
            print("  🚀 Starting all subsystems...")
            self.network.trigger('connect')
            self.database.trigger('start')
            self.api.trigger('start')
        
        def stop_subsystems(from_state, trigger, *args, **kwargs):
            print("  🛑 Stopping all subsystems...")
            self.api.trigger('stop')
            self.database.trigger('stop') 
            self.network.trigger('disconnect')
        
        def maintenance_mode(from_state, trigger, *args, **kwargs):
            print("  🔧 Entering maintenance mode...")
            self.api.trigger('stop')
            if self.database.current_state_name == 'online':
                self.database.trigger('sync')
        
        # Create states with callbacks
        running_state = CallbackState('running', on_enter=start_subsystems)
        shutdown_state = CallbackState('shutdown', on_enter=stop_subsystems)
        maintenance_state = CallbackState('maintenance', on_enter=maintenance_mode)
        
        self.system.add_state(running_state)
        self.system.add_state(shutdown_state)
        self.system.add_state(maintenance_state)
        
        # Add parent transitions
        self.system.add_transitions([
            ('start', 'startup', 'running'),
            ('shutdown', ['running', 'maintenance'], 'shutdown'),
            ('maintain', 'running', 'maintenance'),
            ('resume', 'maintenance', 'running')
        ])
        
        # Add child transitions
        self.network.add_transitions([
            ('connect', 'disconnected', 'connected'),
            ('disconnect', ['connected', 'error'], 'disconnected'),
            ('error', 'connected', 'error')
        ])
        
        self.database.add_transitions([
            ('start', 'offline', 'online'),
            ('stop', ['online', 'syncing'], 'offline'),
            ('sync', 'online', 'syncing')
        ])
        
        self.api.add_transitions([
            ('start', 'stopped', 'running'),
            ('stop', ['running', 'overloaded'], 'stopped'),
            ('overload', 'running', 'overloaded')
        ])
    
    def get_system_status(self):
        """Get status of entire hierarchical system"""
        return {
            'system': self.system.current_state_name,
            'subsystems': {fsm.name: fsm.current_state_name for fsm in self.subsystems}
        }
    
    def demo(self):
        print("\n🏗️ Hierarchical FSM Demo")
        print("=" * 30)
        
        print("1. Initial state:")
        status = self.get_system_status()
        print(f"   System: {status['system']}")
        for name, state in status['subsystems'].items():
            print(f"   {name}: {state}")
        
        print("\n2. Start system (hierarchical activation):")
        self.system.trigger('start')
        status = self.get_system_status()
        print(f"   System: {status['system']}")
        for name, state in status['subsystems'].items():
            print(f"   {name}: {state}")
        
        print("\n3. Enter maintenance mode:")
        self.system.trigger('maintain')
        status = self.get_system_status()
        print(f"   System: {status['system']}")
        for name, state in status['subsystems'].items():
            print(f"   {name}: {state}")


# Technique 3: Observer Pattern - FSMs observe and react to each other
class FSMObserver:
    """Observer that watches FSM state changes and notifies others"""
    
    def __init__(self):
        self.observers: Dict[str, List[Callable]] = {}
    
    def subscribe(self, fsm_name: str, callback: Callable):
        """Subscribe to state changes of an FSM"""
        if fsm_name not in self.observers:
            self.observers[fsm_name] = []
        self.observers[fsm_name].append(callback)
    
    def notify(self, fsm_name: str, old_state: str, new_state: str, trigger: str):
        """Notify observers of state change"""
        if fsm_name in self.observers:
            for callback in self.observers[fsm_name]:
                callback(fsm_name, old_state, new_state, trigger)


class ObservableFSM(StateMachine):
    """FSM that notifies observers of state changes"""
    
    def __init__(self, initial_state, observer: FSMObserver, **kwargs):
        super().__init__(initial_state, **kwargs)
        self.observer = observer
    
    def trigger(self, trigger_name, *args, **kwargs):
        old_state = self.current_state_name
        result = super().trigger(trigger_name, *args, **kwargs)
        
        if result.success:
            new_state = self.current_state_name
            self.observer.notify(self.name, old_state, new_state, trigger_name)
        
        return result


class ObserverPatternDemo:
    """Demo of FSMs using observer pattern for coordination"""
    
    def __init__(self):
        self.observer = FSMObserver()
        
        # Create observable FSMs
        temperature_state = State('normal')
        pressure_state = State('normal') 
        alarm_state = State('off')
        
        self.temperature = ObservableFSM(temperature_state, self.observer, name='Temperature')
        self.pressure = ObservableFSM(pressure_state, self.observer, name='Pressure')
        self.alarm = ObservableFSM(alarm_state, self.observer, name='Alarm')
        
        self._setup_fsms()
        self._setup_observers()
    
    def _setup_fsms(self):
        """Set up the individual FSMs"""
        # Temperature FSM
        temp_states = [State('normal'), State('high'), State('critical')]
        for state in temp_states[1:]:  # Skip normal as it's already added
            self.temperature.add_state(state)
        
        self.temperature.add_transitions([
            ('heat_up', 'normal', 'high'),
            ('overheat', 'high', 'critical'),
            ('cool_down', ['high', 'critical'], 'normal')
        ])
        
        # Pressure FSM
        pressure_states = [State('normal'), State('high'), State('critical')]
        for state in pressure_states[1:]:
            self.pressure.add_state(state)
        
        self.pressure.add_transitions([
            ('increase', 'normal', 'high'),
            ('spike', 'high', 'critical'),
            ('normalize', ['high', 'critical'], 'normal')
        ])
        
        # Alarm FSM
        alarm_states = [State('off'), State('warning'), State('critical')]
        for state in alarm_states[1:]:
            self.alarm.add_state(state)
        
        self.alarm.add_transitions([
            ('warn', 'off', 'warning'),
            ('alert', ['off', 'warning'], 'critical'),
            ('silence', ['warning', 'critical'], 'off')
        ])
    
    def _setup_observers(self):
        """Set up observer relationships"""
        
        def temperature_observer(fsm_name, old_state, new_state, trigger):
            print(f"  📊 {fsm_name} changed: {old_state} → {new_state}")
            if new_state == 'high':
                print("    🔥 High temperature detected - triggering warning")
                self.alarm.trigger('warn')
            elif new_state == 'critical':
                print("    🚨 Critical temperature - triggering alarm")
                self.alarm.trigger('alert')
        
        def pressure_observer(fsm_name, old_state, new_state, trigger):
            print(f"  📊 {fsm_name} changed: {old_state} → {new_state}")
            if new_state == 'critical':
                print("    💥 Critical pressure - triggering alarm")
                self.alarm.trigger('alert')
        
        def alarm_observer(fsm_name, old_state, new_state, trigger):
            print(f"  📊 {fsm_name} changed: {old_state} → {new_state}")
            if new_state == 'critical':
                print("    🚨 CRITICAL ALARM ACTIVATED!")
        
        # Subscribe observers
        self.observer.subscribe('Temperature', temperature_observer)
        self.observer.subscribe('Pressure', pressure_observer)
        self.observer.subscribe('Alarm', alarm_observer)
    
    def get_status(self):
        return {
            'temperature': self.temperature.current_state_name,
            'pressure': self.pressure.current_state_name,
            'alarm': self.alarm.current_state_name
        }
    
    def demo(self):
        print("\n👁️ Observer Pattern Demo")
        print("=" * 30)
        
        print("1. Initial state:")
        status = self.get_status()
        for name, state in status.items():
            print(f"   {name}: {state}")
        
        print("\n2. Temperature increases (triggers chain reaction):")
        self.temperature.trigger('heat_up')
        status = self.get_status()
        for name, state in status.items():
            print(f"   {name}: {state}")
        
        print("\n3. Pressure spikes (triggers alarm):")
        self.pressure.trigger('increase')
        self.pressure.trigger('spike')
        status = self.get_status()
        for name, state in status.items():
            print(f"   {name}: {state}")


# Technique 4: Shared State/Context - FSMs share common data
class SharedContextDemo:
    """FSMs that coordinate through shared context/state"""
    
    def __init__(self):
        # Shared context
        self.shared_context = {
            'resource_pool': 100,
            'active_processes': 0,
            'system_load': 0.0
        }
        
        # Create FSMs that share this context
        self.scheduler = simple_fsm('idle', 'allocating', 'full', initial='idle', name='Scheduler')
        self.monitor = simple_fsm('normal', 'warning', 'critical', initial='normal', name='Monitor')
        self.balancer = simple_fsm('balanced', 'rebalancing', initial='balanced', name='LoadBalancer')
        
        self._setup_shared_behavior()
    
    def _setup_shared_behavior(self):
        """Set up FSMs to use shared context"""
        
        # Scheduler allocates resources
        def allocate_resources(from_state, trigger, amount=10, *args, **kwargs):
            if self.shared_context['resource_pool'] >= amount:
                self.shared_context['resource_pool'] -= amount
                self.shared_context['active_processes'] += 1
                self.shared_context['system_load'] = 1.0 - (self.shared_context['resource_pool'] / 100)
                print(f"  💼 Allocated {amount} resources. Pool: {self.shared_context['resource_pool']}, Load: {self.shared_context['system_load']:.2f}")
                
                # Update other FSMs based on shared state
                if self.shared_context['system_load'] > 0.8:
                    print("    ⚠️ High load detected - monitor escalating")
                    self.monitor.trigger('escalate')
                if self.shared_context['resource_pool'] < 20:
                    print("    🔄 Low resources - starting rebalancing")
                    self.balancer.trigger('rebalance')
        
        def release_resources(from_state, trigger, amount=10, *args, **kwargs):
            self.shared_context['resource_pool'] += amount
            self.shared_context['active_processes'] = max(0, self.shared_context['active_processes'] - 1)
            self.shared_context['system_load'] = 1.0 - (self.shared_context['resource_pool'] / 100)
            print(f"  💼 Released {amount} resources. Pool: {self.shared_context['resource_pool']}, Load: {self.shared_context['system_load']:.2f}")
        
        # Create states with shared context behaviors
        allocating_state = CallbackState('allocating', on_enter=allocate_resources)
        idle_state = CallbackState('idle', on_enter=release_resources)
        
        self.scheduler.add_state(allocating_state)
        self.scheduler.add_state(idle_state)
        
        # Add transitions with shared context conditions
        def can_allocate(*args, **kwargs):
            amount = kwargs.get('amount', 10)
            can_alloc = self.shared_context['resource_pool'] >= amount
            print(f"  🤔 Can allocate {amount}? Pool={self.shared_context['resource_pool']}, Answer={can_alloc}")
            return can_alloc
        
        self.scheduler.add_transitions([
            ('allocate', 'idle', 'allocating'),
            ('complete', 'allocating', 'idle'),
            ('block', 'idle', 'full')
        ])
        
        # Add condition to allocation
        from fast_fsm import FuncCondition
        can_allocate_condition = FuncCondition(can_allocate, "resource_check")
        
        # Fix the allocation transition
        self.scheduler._transitions['idle']['allocate']['condition'] = can_allocate_condition
        
        self.monitor.add_transitions([
            ('escalate', 'normal', 'warning'),
            ('critical', 'warning', 'critical'),
            ('normalize', ['warning', 'critical'], 'normal')
        ])
        
        self.balancer.add_transitions([
            ('rebalance', 'balanced', 'rebalancing'),
            ('complete', 'rebalancing', 'balanced')
        ])
    
    def demo(self):
        print("\n🤝 Shared Context Demo")
        print("=" * 30)
        
        print("1. Initial shared state:")
        print(f"   Context: {self.shared_context}")
        
        print("\n2. Allocate resources multiple times:")
        for i in range(3):
            print(f"\n   Allocation {i+1}:")
            self.scheduler.trigger('allocate', amount=30)
            self.scheduler.trigger('complete')
        
        print(f"\n   Final context: {self.shared_context}")
        print(f"   Monitor state: {self.monitor.current_state_name}")
        print(f"   Balancer state: {self.balancer.current_state_name}")


def main():
    """Demonstrate all FSM linking techniques"""
    print("🔗 FSM Linking Techniques Beyond Conditions")
    print("=" * 50)
    
    # Run all demos
    EventCascadingDemo().demo()
    HierarchicalFSMDemo().demo()
    ObserverPatternDemo().demo()
    SharedContextDemo().demo()
    
    print("\n" + "=" * 50)
    print("✅ All FSM linking techniques demonstrated!")
    
    print("\n🎯 Summary of Techniques:")
    print("   1️⃣ Condition-based Dependencies (previous demo)")
    print("   2️⃣ Event Cascading - FSMs trigger events in others")
    print("   3️⃣ Hierarchical Control - Parent FSM controls children")
    print("   4️⃣ Observer Pattern - FSMs react to each other's changes")
    print("   5️⃣ Shared Context - FSMs coordinate through shared data")
    
    print("\n💡 Choose the right technique based on your needs:")
    print("   • Conditions: When transitions depend on other FSM states")
    print("   • Cascading: When one event should trigger multiple actions")
    print("   • Hierarchical: When you have clear parent-child relationships")
    print("   • Observer: When FSMs need to react to changes dynamically")
    print("   • Shared Context: When FSMs coordinate through common resources")


if __name__ == '__main__':
    main()
