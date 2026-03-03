#!/usr/bin/env python3
"""
Traffic Light System Example using Fast FSM

Demonstrates a complete traffic light state machine with:
- 3 states: Red, Yellow, Green
- Timer-based transitions
- Emergency override functionality
"""

from fast_fsm import State, FSMBuilder


class TrafficLightState(State):
    """Base class for traffic light states"""

    pass


class RedState(TrafficLightState):
    def __init__(self):
        super().__init__("Red")

    def on_enter(self, from_state, trigger, **kwargs):
        print(f"🔴 Red light ON (from {from_state.name if from_state else 'start'})")


class YellowState(TrafficLightState):
    def __init__(self):
        super().__init__("Yellow")

    def on_enter(self, from_state, trigger, **kwargs):
        print(f"🟡 Yellow light ON (from {from_state.name if from_state else 'start'})")


class GreenState(TrafficLightState):
    def __init__(self):
        super().__init__("Green")

    def on_enter(self, from_state, trigger, **kwargs):
        print(f"🟢 Green light ON (from {from_state.name if from_state else 'start'})")


def main():
    """Run the traffic light demo"""
    print("🚀 Fast FSM Library - Traffic Light Demo")
    print("=" * 50)

    # Build the traffic light FSM
    red = RedState()
    yellow = YellowState()
    green = GreenState()

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
