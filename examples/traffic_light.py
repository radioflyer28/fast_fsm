#!/usr/bin/env python3
"""Tier 1: learn the smallest useful ``StateMachine`` and inspect results."""

from fast_fsm import State, StateMachine


def main() -> None:
    red = State("Red")
    traffic_light = StateMachine(red, name="TrafficLight")
    traffic_light.add_state(State("Green"))
    traffic_light.add_state(State("Yellow"))
    traffic_light.add_transition("timer", "Red", "Green")
    traffic_light.add_transition("timer", "Green", "Yellow")
    traffic_light.add_transition("timer", "Yellow", "Red")

    print(f"Initial: {traffic_light.current_state_name}")
    for _ in range(3):
        result = traffic_light.trigger("timer")
        print(
            f"{result.from_state} --{result.trigger}--> "
            f"{result.to_state}; current={traffic_light.current_state_name}"
        )

    rejected = traffic_light.trigger("unknown")
    print(f"Unknown trigger accepted? {rejected.success}; error={rejected.error}")


if __name__ == "__main__":
    main()
