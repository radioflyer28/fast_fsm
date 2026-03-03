#!/usr/bin/env python3
"""
Cross-FSM Dependencies Demo

Demonstrates patterns where multiple FSMs depend on each other's states:
- Cross-FSM conditions (security system)
- State-dependent transitions (factory production line)
- Coordinated multi-FSM systems (power + cooling + machine)
"""

from fast_fsm import StateMachine, Condition, simple_fsm, condition_builder


class CrossFSMCondition(Condition):
    """Condition that checks the state of another FSM"""

    def __init__(self, other_fsm: StateMachine, required_state: str, name: str = ""):
        if not name:
            name = f"{other_fsm.name}_in_{required_state}"
        super().__init__(
            name, f"Check if {other_fsm.name} is in state '{required_state}'"
        )
        self.other_fsm = other_fsm
        self.required_state = required_state

    def check(self, *args, **kwargs) -> bool:
        is_in_state = self.other_fsm.current_state_name == self.required_state
        print(
            f"  Checking {self.other_fsm.name} state: "
            f"{self.other_fsm.current_state_name} == {self.required_state}? {is_in_state}"
        )
        return is_in_state


def demo_security_system():
    """Demo: Security system where door can only open if alarm is disarmed"""
    print("--- Security System Demo ---")

    # Alarm system FSM
    alarm = simple_fsm(
        "armed", "disarmed", "triggered", initial="armed", name="AlarmSystem"
    )
    alarm.add_transitions(
        [
            ("disarm", "armed", "disarmed"),
            ("arm", "disarmed", "armed"),
            ("trigger", "armed", "triggered"),
            ("reset", "triggered", "disarmed"),
        ]
    )

    # Door system FSM — can only open when alarm is disarmed
    door = simple_fsm("closed", "open", initial="closed", name="DoorSystem")
    alarm_disarmed = CrossFSMCondition(alarm, "disarmed", "alarm_disarmed")
    door.add_transition("open", "closed", "open", condition=alarm_disarmed)
    door.add_transition("close", "open", "closed")

    print(f"Alarm: {alarm.current_state_name}, Door: {door.current_state_name}")

    # Try to open door while alarm is armed
    result = door.trigger("open")
    print(f"Open door (alarm armed): success={result.success}")

    # Disarm alarm, then open door
    alarm.trigger("disarm")
    result = door.trigger("open")
    print(f"Open door (alarm disarmed): success={result.success}")

    # Close door after re-arming
    alarm.trigger("arm")
    door.trigger("close")
    print(f"Final — Alarm: {alarm.current_state_name}, Door: {door.current_state_name}")


def demo_factory_production():
    """Demo: Production line depends on material availability"""
    print("\n--- Factory Production Demo ---")

    # Material supply FSM
    supply = simple_fsm(
        "empty", "low", "full", initial="full", name="MaterialSupply"
    )
    supply.add_transitions(
        [
            ("consume", "full", "low"),
            ("consume", "low", "empty"),
            ("refill", ["empty", "low"], "full"),
        ]
    )

    # Production line FSM
    production = simple_fsm(
        "idle", "producing", "blocked", initial="idle", name="ProductionLine"
    )

    @condition_builder(
        name="materials_available", description="Check if materials are not empty"
    )
    def has_materials(*args, **kwargs):
        available = supply.current_state_name != "empty"
        print(f"  Material check: {supply.current_state_name} != empty? {available}")
        return available

    production.add_transition("start", "idle", "producing", condition=has_materials)
    production.add_transition("complete", "producing", "idle")
    production.add_transition("block", "producing", "blocked")
    production.add_transition("unblock", "blocked", "idle")

    # Start with full materials
    result = production.trigger("start")
    print(f"Start production (full): success={result.success}")

    # Consume all materials
    supply.trigger("consume")  # full -> low
    supply.trigger("consume")  # low -> empty
    production.trigger("complete")

    # Try to restart — should fail
    result = production.trigger("start")
    print(f"Start production (empty): success={result.success}")

    # Refill and restart
    supply.trigger("refill")
    result = production.trigger("start")
    print(f"Start production (refilled): success={result.success}")


class CoordinatedFSM:
    """Helper class to coordinate multiple FSMs"""

    def __init__(self, *fsms):
        self.fsms = {fsm.name: fsm for fsm in fsms}
        self.fsm_list = list(fsms)

    def get_states(self) -> dict:
        return {name: fsm.current_state_name for name, fsm in self.fsms.items()}

    def print_status(self):
        for name, fsm in self.fsms.items():
            print(f"  {name}: {fsm.current_state_name}")


def demo_coordinated_system():
    """Demo: Multiple FSMs coordinated via cross-FSM conditions"""
    print("\n--- Coordinated System Demo ---")

    power = simple_fsm("off", "on", "overload", initial="off", name="PowerSystem")
    power.add_transitions(
        [
            ("turn_on", "off", "on"),
            ("turn_off", ["on", "overload"], "off"),
            ("overload", "on", "overload"),
        ]
    )

    cooling = simple_fsm(
        "stopped", "running", "failed", initial="stopped", name="CoolingSystem"
    )
    cooling.add_transitions(
        [
            ("start", "stopped", "running"),
            ("stop", "running", "stopped"),
            ("fail", "running", "failed"),
            ("repair", "failed", "stopped"),
        ]
    )

    machine = simple_fsm(
        "offline", "ready", "working", "error", initial="offline", name="Machine"
    )

    @condition_builder(
        name="systems_ready", description="Power on and cooling running"
    )
    def systems_ready(*args, **kwargs):
        power_ok = power.current_state_name == "on"
        cooling_ok = cooling.current_state_name == "running"
        ready = power_ok and cooling_ok
        print(
            f"  Systems check: Power={power.current_state_name}, "
            f"Cooling={cooling.current_state_name}, Ready={ready}"
        )
        return ready

    machine.add_transition("startup", "offline", "ready", condition=systems_ready)
    machine.add_transition("start_work", "ready", "working")
    machine.add_transition("stop_work", "working", "ready")
    machine.add_transition("shutdown", ["ready", "working"], "offline")
    machine.add_transition("error", ["ready", "working"], "error")
    machine.add_transition("reset", "error", "offline")

    coordinator = CoordinatedFSM(power, cooling, machine)

    # Try to start machine without subsystems
    result = machine.trigger("startup")
    print(f"Startup (no power/cooling): success={result.success}")

    # Turn on power only — still not enough
    power.trigger("turn_on")
    result = machine.trigger("startup")
    print(f"Startup (power only): success={result.success}")

    # Start cooling too
    cooling.trigger("start")
    result = machine.trigger("startup")
    print(f"Startup (all systems): success={result.success}")

    coordinator.print_status()

    # Begin work
    machine.trigger("start_work")
    print(f"Machine working: {machine.current_state_name}")


def main():
    """Run all cross-FSM demos"""
    print("Cross-FSM Dependencies Demo")
    print("=" * 50)
    demo_security_system()
    demo_factory_production()
    demo_coordinated_system()
    print("\n" + "=" * 50)
    print("Key Patterns Demonstrated:")
    print("  - Cross-FSM conditions")
    print("  - State-dependent transitions")
    print("  - Coordinated multi-FSM systems")
    print("  - Real-time dependency checking")


if __name__ == "__main__":
    main()
