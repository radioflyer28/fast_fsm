#!/usr/bin/env python3
"""Tier 3: coordinate replaceable FSMs through cross-machine guards."""

from fast_fsm import StateMachine, condition_builder, simple_fsm


class FactorySystem:
    """Own three independent machines and their explicit coordination rules."""

    def __init__(self) -> None:
        self.power = simple_fsm("Off", "On", initial="Off", name="Power")
        self.power.add_transition("start", "Off", "On")
        self.power.add_transition("stop", "On", "Off")

        self.cooling = simple_fsm("Off", "On", initial="Off", name="Cooling")
        self.cooling.add_transition("start", "Off", "On")
        self.cooling.add_transition("stop", "On", "Off")

        self.production = simple_fsm(
            "Offline", "Ready", "Running", initial="Offline", name="Production"
        )

        @condition_builder(
            name="utilities_ready", description="Power and cooling are both on"
        )
        def utilities_ready(**_context: object) -> bool:
            return self.power.is_in("On") and self.cooling.is_in("On")

        self.production.add_transition(
            "prepare", "Offline", "Ready", condition=utilities_ready
        )
        self.production.add_transition("run", "Ready", "Running")
        self.production.add_transition("stop", ["Ready", "Running"], "Offline")

    def start_utilities(self) -> None:
        self.power.trigger("start").raise_if_failed()
        self.cooling.trigger("start").raise_if_failed()

    def stop_cooling_safely(self) -> None:
        """Coordinate a deliberate cascade at the system boundary."""
        if not self.production.is_in("Offline"):
            self.production.trigger("stop").raise_if_failed()
        self.cooling.trigger("stop").raise_if_failed()

    def status(self) -> dict[str, str]:
        machines: tuple[StateMachine, ...] = (
            self.power,
            self.cooling,
            self.production,
        )
        return {machine.name: machine.current_state_name for machine in machines}


def main() -> None:
    factory = FactorySystem()
    blocked = factory.production.trigger("prepare")
    print(f"prepare without utilities={blocked.success}")

    factory.start_utilities()
    factory.production.trigger("prepare").raise_if_failed()
    factory.production.trigger("run").raise_if_failed()
    print(f"running={factory.status()}")

    factory.stop_cooling_safely()
    print(f"safe shutdown={factory.status()}")


if __name__ == "__main__":
    main()
