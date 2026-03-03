#!/usr/bin/env python3
"""
Example of FSMs that depend on each other's states
"""

from fast_fsm import StateMachine, Condition, simple_fsm, condition_builder


class CrossFSMCondition(Condition):
    """Condition that checks the state of another FSM"""
    
    def __init__(self, other_fsm: StateMachine, required_state: str, name: str = ""):
        if not name:
            name = f"{other_fsm.name}_in_{required_state}"
        super().__init__(name, f"Check if {other_fsm.name} is in state '{required_state}'")
        self.other_fsm = other_fsm
        self.required_state = required_state
    
    def check(self, *args, **kwargs) -> bool:
        is_in_state = self.other_fsm.current_state_name == self.required_state
        print(f"  🔍 Checking {self.other_fsm.name} state: {self.other_fsm.current_state_name} == {self.required_state}? {is_in_state}")
        return is_in_state


def demo_security_system():
    """Demo: Security system where door can only open if alarm is disarmed"""
    print("🚨 Security System Demo")
    print("=" * 40)
    
    # Create alarm system FSM
    alarm = simple_fsm('armed', 'disarmed', 'triggered', initial='armed', name='AlarmSystem')
    alarm.add_transitions([
        ('disarm', 'armed', 'disarmed'),
        ('arm', 'disarmed', 'armed'),
        ('trigger', 'armed', 'triggered'),
        ('reset', 'triggered', 'disarmed')
    ])
    
    # Create door system FSM
    door = simple_fsm('closed', 'open', initial='closed', name='DoorSystem')
    
    # Door can only open if alarm is disarmed
    alarm_disarmed = CrossFSMCondition(alarm, 'disarmed', 'alarm_disarmed')
    door.add_transition('open', 'closed', 'open', condition=alarm_disarmed)
    door.add_transition('close', 'open', 'closed')
    
    print(f"Initial state - Alarm: {alarm.current_state_name}, Door: {door.current_state_name}")
    
    # Try to open door while alarm is armed
    print("\n1. Try to open door while alarm is armed:")
    result = door.trigger('open')
    print(f"   Result: {result.success} - {result.error if not result.success else 'Success'}")
    print(f"   Door state: {door.current_state_name}")
    
    # Disarm alarm and try again
    print("\n2. Disarm alarm and try to open door:")
    alarm.trigger('disarm')
    print(f"   Alarm disarmed: {alarm.current_state_name}")
    result = door.trigger('open')
    print(f"   Door open result: {result.success}")
    print(f"   Door state: {door.current_state_name}")
    
    # Arm alarm while door is open (door should still work)
    print("\n3. Arm alarm while door is open:")
    alarm.trigger('arm')
    print(f"   Alarm state: {alarm.current_state_name}")
    door.trigger('close')
    print(f"   Door closed: {door.current_state_name}")
    
    return alarm, door


def demo_factory_production():
    """Demo: Production line where assembly depends on material availability"""
    print("\n🏭 Factory Production Demo")
    print("=" * 40)
    
    # Material supply FSM
    supply = simple_fsm('empty', 'low', 'full', initial='full', name='MaterialSupply')
    supply.add_transitions([
        ('consume', 'full', 'low'),
        ('consume', 'low', 'empty'),
        ('refill', ['empty', 'low'], 'full')
    ])
    
    # Production line FSM
    production = simple_fsm('idle', 'producing', 'blocked', initial='idle', name='ProductionLine')
    
    # Production can only start if materials are available (not empty)
    @condition_builder(name="materials_available", description="Check if materials are not empty")
    def has_materials(*args, **kwargs):
        available = supply.current_state_name != 'empty'
        print(f"  📦 Material check: {supply.current_state_name} != empty? {available}")
        return available
    
    # Add transitions with cross-FSM dependency
    production.add_transition('start', 'idle', 'producing', condition=has_materials)
    production.add_transition('complete', 'producing', 'idle')
    production.add_transition('block', 'producing', 'blocked')  # When materials run out
    production.add_transition('unblock', 'blocked', 'idle')
    
    print(f"Initial - Supply: {supply.current_state_name}, Production: {production.current_state_name}")
    
    # Start production with full materials
    print("\n1. Start production with full materials:")
    result = production.trigger('start')
    print(f"   Production started: {result.success}")
    print(f"   Production state: {production.current_state_name}")
    
    # Consume materials while producing
    print("\n2. Consume materials during production:")
    supply.trigger('consume')  # full -> low
    print(f"   Supply after consumption: {supply.current_state_name}")
    supply.trigger('consume')  # low -> empty
    print(f"   Supply after more consumption: {supply.current_state_name}")
    
    # Complete current production
    production.trigger('complete')
    print(f"   Production completed: {production.current_state_name}")
    
    # Try to start again with empty materials
    print("\n3. Try to start production with empty materials:")
    result = production.trigger('start')
    print(f"   Start result: {result.success} - {result.error if not result.success else 'Success'}")
    
    # Refill and try again
    print("\n4. Refill materials and start production:")
    supply.trigger('refill')
    print(f"   Supply refilled: {supply.current_state_name}")
    result = production.trigger('start')
    print(f"   Production started: {result.success}")
    
    return supply, production


class CoordinatedFSM:
    """Helper class to coordinate multiple FSMs"""
    
    def __init__(self, *fsms):
        self.fsms = {fsm.name: fsm for fsm in fsms}
        self.fsm_list = list(fsms)
    
    def get_state(self, fsm_name: str) -> str:
        """Get the current state of a named FSM"""
        return self.fsms[fsm_name].current_state_name
    
    def trigger_all(self, trigger: str, *args, **kwargs):
        """Trigger the same event on all FSMs"""
        results = {}
        for fsm in self.fsm_list:
            if fsm.transition_exists(trigger):
                results[fsm.name] = fsm.trigger(trigger, *args, **kwargs)
        return results
    
    def get_states(self) -> dict:
        """Get all FSM states"""
        return {name: fsm.current_state_name for name, fsm in self.fsms.items()}
    
    def print_status(self):
        """Print status of all FSMs"""
        print("📊 System Status:")
        for name, fsm in self.fsms.items():
            print(f"   {name}: {fsm.current_state_name}")


def demo_coordinated_system():
    """Demo: Multiple FSMs working together with coordination"""
    print("\n🎭 Coordinated System Demo")
    print("=" * 40)
    
    # Create multiple FSMs
    power = simple_fsm('off', 'on', 'overload', initial='off', name='PowerSystem')
    power.add_transitions([
        ('turn_on', 'off', 'on'),
        ('turn_off', ['on', 'overload'], 'off'),
        ('overload', 'on', 'overload')
    ])
    
    cooling = simple_fsm('stopped', 'running', 'failed', initial='stopped', name='CoolingSystem')
    cooling.add_transitions([
        ('start', 'stopped', 'running'),
        ('stop', 'running', 'stopped'),
        ('fail', 'running', 'failed'),
        ('repair', 'failed', 'stopped')
    ])
    
    machine = simple_fsm('offline', 'ready', 'working', 'error', initial='offline', name='Machine')
    
    # Machine can only be ready if power is on AND cooling is running
    @condition_builder(name="systems_ready", description="Power on and cooling running")
    def systems_ready(*args, **kwargs):
        power_ok = power.current_state_name == 'on'
        cooling_ok = cooling.current_state_name == 'running'
        ready = power_ok and cooling_ok
        print(f"  ⚡ Systems check: Power={power.current_state_name}, Cooling={cooling.current_state_name}, Ready={ready}")
        return ready
    
    machine.add_transition('startup', 'offline', 'ready', condition=systems_ready)
    machine.add_transition('start_work', 'ready', 'working')
    machine.add_transition('stop_work', 'working', 'ready')
    machine.add_transition('shutdown', ['ready', 'working'], 'offline')
    machine.add_transition('error', ['ready', 'working'], 'error')
    machine.add_transition('reset', 'error', 'offline')
    
    # Create coordinator
    coordinator = CoordinatedFSM(power, cooling, machine)
    
    print("Initial state:")
    coordinator.print_status()
    
    # Try to start machine without systems
    print("\n1. Try to start machine without power/cooling:")
    result = machine.trigger('startup')
    print(f"   Startup result: {result.success} - {result.error if not result.success else 'Success'}")
    
    # Start power only
    print("\n2. Turn on power only:")
    power.trigger('turn_on')
    coordinator.print_status()
    result = machine.trigger('startup')
    print(f"   Startup result: {result.success} - {result.error if not result.success else 'Success'}")
    
    # Start cooling too
    print("\n3. Start cooling system:")
    cooling.trigger('start')
    coordinator.print_status()
    result = machine.trigger('startup')
    print(f"   Startup result: {result.success}")
    coordinator.print_status()
    
    # Start working
    print("\n4. Begin work:")
    machine.trigger('start_work')
    coordinator.print_status()
    
    return coordinator


def main():
    """Run all cross-FSM demos"""
    print("🤝 Cross-FSM Dependencies Demo")
    print("=" * 50)
    
    # Run demos
    demo_security_system()
    demo_factory_production()
    demo_coordinated_system()
    
    print("\n" + "=" * 50)
    print("✅ Cross-FSM dependency patterns demonstrated!")
    
    print("\n🎯 Key Patterns:")
    print("   ✅ Cross-FSM conditions")
    print("   ✅ State-dependent transitions")
    print("   ✅ Coordinated multi-FSM systems")
    print("   ✅ Real-time dependency checking")


if __name__ == '__main__':
    main()
