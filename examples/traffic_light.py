#!/usr/bin/env python3
"""
Traffic Light System Example using Fast FSM

Demonstrates a complete traffic light state machine with:
- 3 states: Red, Yellow, Green
- Timer-based transitions
- Emergency override functionality
"""

from collections.abc import Callable

from fast_fsm import FSMBuilder, State


def announce_light(symbol: str, label: str) -> Callable[..., None]:
    """Create an inline callback for :meth:`State.create`."""

    def announce(from_state: State | None, _trigger: str, *_, **__) -> None:
        source = from_state.name if from_state else "start"
        print(f"{symbol} {label} light ON (from {source})")

    return announce


def main():
    """Run the traffic light demo"""
    print("🚀 Fast FSM Library - Traffic Light Demo")
    print("=" * 50)

    # Build the traffic light FSM
    red = State.create("Red", on_enter=announce_light("🔴", "Red"))
    yellow = State.create("Yellow", on_enter=announce_light("🟡", "Yellow"))
    green = State.create("Green", on_enter=announce_light("🟢", "Green"))

    traffic_light = (
        FSMBuilder(red, name="TrafficLight")
        .add_state(yellow)
        .add_state(green)
        .add_transition("timer", "Red", "Green")
        .add_transition("timer", "Green", "Yellow")
        .add_transition("timer", "Yellow", "Red")
        .add_transition("emergency", ["Green", "Yellow", "Red"], "Red")
        .build()
    )

    print("🚦 Traffic Light State Machine Demo")
    print(f"Current state: {traffic_light.current_state_name}")

    # Test normal cycle
    print("\n--- Normal Traffic Light Cycle ---")
    traffic_light.trigger("timer")  # Red -> Green
    traffic_light.trigger("timer")  # Green -> Yellow
    traffic_light.trigger("timer")  # Yellow -> Red

    # Test emergency
    print("\n--- Emergency Override ---")
    traffic_light.trigger("timer")  # Red -> Green
    traffic_light.trigger("emergency")  # Green -> Red (emergency)

    print(f"\nFinal state: {traffic_light.current_state_name}")


if __name__ == "__main__":
    main()
