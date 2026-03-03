#!/usr/bin/env python3
"""
Enhanced DeclarativeState Example

Demonstrates the improved DeclarativeState with:
- Integrated logging
- Condition support from decorator metadata
- Enhanced error handling
- Async support with AsyncDeclarativeState
"""

import asyncio
import logging

from fast_fsm import (
    StateMachine,
    AsyncStateMachine,
    DeclarativeState,
    AsyncDeclarativeState,
    transition,
    Condition,
    AsyncCondition,
    configure_fsm_logging,
)


# Custom condition for demonstration
class SecurityCondition(Condition):
    def __init__(self, required_clearance: int):
        super().__init__(f"security_level_{required_clearance}")
        self.required_clearance = required_clearance

    def check(self, user_clearance=0, **kwargs):
        return user_clearance >= self.required_clearance


class TemperatureCondition(Condition):
    """Sync version for regular DeclarativeState"""

    def __init__(self, max_temp: float):
        super().__init__(f"temp_below_{max_temp}")
        self.max_temp = max_temp

    def check(self, temperature=20.0, **kwargs):
        return temperature < self.max_temp


class AsyncTemperatureCondition(AsyncCondition):
    """Async version for AsyncDeclarativeState"""

    def __init__(self, max_temp: float):
        super().__init__(f"async_temp_below_{max_temp}")
        self.max_temp = max_temp

    async def check_async(self, **kwargs):
        # Simulate async sensor reading
        await asyncio.sleep(0.1)
        current_temp = kwargs.get("temperature", 20.0)
        return current_temp < self.max_temp


# Declarative state with enhanced features
class SecurityGateState(DeclarativeState):
    """Security gate with declarative transition handlers"""

    def __init__(self, name: str):
        super().__init__(name)
        self.access_count = 0

    # Basic transition without condition
    @transition("reset")
    def handle_reset(self, **kwargs):
        """Reset the gate to default state"""
        self.access_count = 0
        print(f"🔄 Gate {self.name}: Reset completed")
        return True

    # Transition with security condition
    @transition("access_request", condition=SecurityCondition(3))
    def handle_access_request(self, user_clearance=0, user_name="Unknown", **kwargs):
        """Handle access request with security validation"""
        self.access_count += 1
        print(
            f"🔐 Gate {self.name}: Access granted to {user_name} (clearance {user_clearance})"
        )
        print(f"📊 Total accesses: {self.access_count}")
        return True

    # Transition with function condition
    @transition(
        "emergency_override",
        condition=lambda emergency_code=0, **kw: emergency_code == 911,
    )
    def handle_emergency(self, emergency_code=0, **kwargs):
        """Emergency override with inline condition"""
        print(
            f"🚨 Gate {self.name}: EMERGENCY OVERRIDE ACTIVATED! Code: {emergency_code}"
        )
        return True

    def on_enter(self, from_state, trigger, **kwargs):
        """Enhanced state entry with logging"""
        print(f"📍 Entering gate state: {self.name}")


# Async declarative state
class AsyncSensorState(AsyncDeclarativeState):
    """Async sensor monitoring state"""

    def __init__(self, name: str):
        super().__init__(name)
        self.sensor_readings = []

    # Sync transition with sync condition
    @transition("temperature_check", condition=TemperatureCondition(30.0))
    def handle_sync_temperature_check(self, temperature=20.0, **kwargs):
        """Sync temperature validation"""
        self.sensor_readings.append(temperature)
        print(f"🌡️  Sensor {self.name}: Temperature {temperature}°C recorded (sync)")
        return True

    # Async transition with async condition
    @transition("async_temperature_check", condition=AsyncTemperatureCondition(30.0))
    async def handle_async_temperature_check(self, temperature=20.0, **kwargs):
        """Async temperature validation"""
        await asyncio.sleep(0.05)  # Simulate processing time
        self.sensor_readings.append(temperature)
        print(f"🌡️  Sensor {self.name}: Temperature {temperature}°C recorded (async)")
        return True

    # Sync method in async state (still works)
    @transition("manual_reading")
    def handle_manual_reading(self, value=0.0, **kwargs):
        """Manual reading input (sync method)"""
        self.sensor_readings.append(value)
        print(f"📝 Sensor {self.name}: Manual reading {value} recorded")
        return True

    # Async method without condition
    @transition("calibrate")
    async def handle_calibration(self, **kwargs):
        """Async calibration procedure"""
        print(f"🔧 Sensor {self.name}: Starting calibration...")
        await asyncio.sleep(0.2)  # Simulate calibration time
        self.sensor_readings.clear()
        print(f"✅ Sensor {self.name}: Calibration complete")
        return True


def demo_sync_declarative_state():
    """Demonstrate enhanced DeclarativeState with sync FSM"""
    print("🚀 Sync DeclarativeState Demo")
    print("=" * 50)

    # Enable logging to see enhanced features
    configure_fsm_logging(logging.DEBUG, "fast_fsm")

    # Create states
    locked = SecurityGateState("Locked")
    unlocked = SecurityGateState("Unlocked")

    # Build FSM
    fsm = StateMachine(locked, name="SecurityGate")
    fsm.add_state(unlocked)
    fsm.add_transition("access_request", "Locked", "Unlocked")
    fsm.add_transition("reset", "Unlocked", "Locked")
    fsm.add_transition("emergency_override", ["Locked", "Unlocked"], "Unlocked")

    print(f"Initial state: {fsm.current_state.name}")

    # Test scenarios
    print("\n--- Test 1: Low clearance access (should fail) ---")
    result = fsm.trigger("access_request", user_clearance=1, user_name="Bob")
    print(f"Result: {result.success}, Error: {result.error}")

    print("\n--- Test 2: High clearance access (should succeed) ---")
    result = fsm.trigger("access_request", user_clearance=5, user_name="Alice")
    print(f"Result: {result.success}, Current state: {fsm.current_state.name}")

    print("\n--- Test 3: Reset gate ---")
    result = fsm.trigger("reset")
    print(f"Result: {result.success}, Current state: {fsm.current_state.name}")

    print("\n--- Test 4: Emergency override ---")
    result = fsm.trigger("emergency_override", emergency_code=911)
    print(f"Result: {result.success}, Current state: {fsm.current_state.name}")


async def demo_async_declarative_state():
    """Demonstrate AsyncDeclarativeState with async FSM"""
    print("\n\n🚀 Async DeclarativeState Demo")
    print("=" * 50)

    # Create async states
    monitoring = AsyncSensorState("Monitoring")
    alert = AsyncSensorState("Alert")

    # Build async FSM
    fsm = AsyncStateMachine(monitoring, name="SensorSystem")
    fsm.add_state(alert)
    fsm.add_transition("temperature_check", "Monitoring", "Alert")
    fsm.add_transition("async_temperature_check", "Monitoring", "Alert")
    fsm.add_transition("calibrate", ["Monitoring", "Alert"], "Monitoring")
    fsm.add_transition("manual_reading", "Monitoring", "Monitoring")

    print(f"Initial state: {fsm.current_state.name}")

    # Test async scenarios
    print("\n--- Test 1: Sync condition in async context (should succeed) ---")
    result = await fsm.trigger_async("temperature_check", temperature=25.0)
    print(f"Result: {result.success}, Current state: {fsm.current_state.name}")

    print("\n--- Test 2: Async condition (should succeed) ---")
    result = await fsm.trigger_async("async_temperature_check", temperature=25.0)
    print(f"Result: {result.success}, Current state: {fsm.current_state.name}")

    print("\n--- Test 3: High temperature (should fail sync condition) ---")
    result = await fsm.trigger_async("temperature_check", temperature=35.0)
    print(f"Result: {result.success}, Error: {result.error}")

    print("\n--- Test 4: Manual reading (sync in async) ---")
    result = await fsm.trigger_async("manual_reading", value=22.5)
    print(f"Result: {result.success}")

    print("\n--- Test 5: Async calibration ---")
    result = await fsm.trigger_async("calibrate")
    print(f"Result: {result.success}, Current state: {fsm.current_state.name}")

    # Access sensor readings safely
    if hasattr(fsm.current_state, "sensor_readings"):
        print(f"\nFinal readings: {fsm.current_state.sensor_readings}")


async def main():
    """Run both demonstrations"""
    # Sync demo
    demo_sync_declarative_state()

    # Async demo
    await demo_async_declarative_state()

    print("\n" + "=" * 50)
    print("🎯 Key Features Demonstrated:")
    print("• Integrated logging with debug information")
    print("• Condition evaluation from @transition decorator")
    print("• Enhanced error handling and reporting")
    print("• Async method support in AsyncDeclarativeState")
    print("• Seamless integration with StateMachine/AsyncStateMachine")
    print("• Both sync and async conditions")


if __name__ == "__main__":
    asyncio.run(main())
