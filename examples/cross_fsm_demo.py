#!/usr/bin/env python3
"""Tier 3: coordinate replaceable FSMs through cross-machine guards."""

from collections.abc import Iterable

from fast_fsm import FSMBuilder, State, StateMachine, condition_builder


def build_machine(
    name: str,
    state_names: Iterable[str],
    transitions: Iterable[tuple[str, str | list[str], str]],
) -> StateMachine:
    """Build one replaceable machine from caller-owned state objects."""
    states = {state_name: State(state_name) for state_name in state_names}
    initial_name = next(iter(states))
    builder = FSMBuilder(states[initial_name], name=name)
    for state_name, state in states.items():
        if state_name != initial_name:
            builder.add_state(state)
    for trigger, source, target in transitions:
        builder.add_transition(trigger, source, target)
    return builder.build()


class FactorySystem:
    """Own three independent machines and their explicit coordination rules."""

    def __init__(self) -> None:
        self.power = build_machine(
            "Power",
            ("Off", "On"),
            (("start", "Off", "On"), ("stop", "On", "Off")),
        )
        self.cooling = build_machine(
            "Cooling",
            ("Off", "On"),
            (("start", "Off", "On"), ("stop", "On", "Off")),
        )

        @condition_builder(
            name="utilities_ready", description="Power and cooling are both on"
        )
        def utilities_ready(**_context: object) -> bool:
            return self.power.is_in("On") and self.cooling.is_in("On")

        offline = State("Offline")
        ready = State("Ready")
        running = State("Running")
        self.production = (
            FSMBuilder(offline, name="Production")
            .add_state(ready)
            .add_state(running)
            .add_transition("prepare", "Offline", "Ready", condition=utilities_ready)
            .add_transition("run", "Ready", "Running")
            .add_transition("stop", ["Ready", "Running"], "Offline")
            .build()
        )

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
