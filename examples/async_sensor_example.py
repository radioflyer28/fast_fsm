#!/usr/bin/env python3
"""
Async Sensor Condition Example

This example demonstrates how to create and use asynchronous conditions
that can check real-time sensor data in a Fast FSM state machine.
"""

import asyncio
import random

from fast_fsm import State, AsyncStateMachine, AsyncCondition


# Example: Simulated sensor readers
class TemperatureSensor:
    """Simulated temperature sensor with realistic behavior"""

    def __init__(self, base_temp: float = 20.0):
        self.base_temp = base_temp
        self._last_reading = base_temp

    async def read_temperature(self) -> float:
        """Simulate reading temperature with network delay and noise"""
        # Simulate network delay
        await asyncio.sleep(0.1 + random.uniform(0, 0.2))

        # Simulate gradual temperature changes with noise
        change = random.uniform(-0.5, 0.5)
        self._last_reading += change

        # Add some random noise
        noise = random.uniform(-0.1, 0.1)
        return self._last_reading + noise


class PressureSensor:
    """Simulated pressure sensor"""

    def __init__(self, base_pressure: float = 1013.25):
        self.base_pressure = base_pressure
        self._last_reading = base_pressure

    async def read_pressure(self) -> float:
        """Simulate reading pressure"""
        await asyncio.sleep(0.05 + random.uniform(0, 0.1))

        # Simulate pressure variations
        change = random.uniform(-2, 2)
        self._last_reading += change
        return max(900, min(1100, self._last_reading))  # Realistic range


# Custom async condition classes
class TemperatureCondition(AsyncCondition):
    """Check if temperature is above threshold"""

    def __init__(self, sensor: TemperatureSensor, min_temp: float):
        super().__init__(
            name=f"temp_above_{min_temp}", description=f"Temperature >= {min_temp}°C"
        )
        self.sensor = sensor
        self.min_temp = min_temp

    async def check_async(self, **kwargs) -> bool:
        try:
            temp = await self.sensor.read_temperature()
            print(f"  🌡️  Temperature reading: {temp:.1f}°C (need >= {self.min_temp}°C)")
            return temp >= self.min_temp
        except Exception as e:
            print(f"  ❌ Temperature sensor error: {e}")
            return False


class CombinedSensorCondition(AsyncCondition):
    """Check multiple sensors simultaneously"""

    def __init__(
        self,
        temp_sensor: TemperatureSensor,
        pressure_sensor: PressureSensor,
        min_temp: float,
        max_pressure: float,
    ):
        super().__init__(
            name="combined_sensors",
            description=f"Temp >= {min_temp}°C AND Pressure <= {max_pressure} hPa",
        )
        self.temp_sensor = temp_sensor
        self.pressure_sensor = pressure_sensor
        self.min_temp = min_temp
        self.max_pressure = max_pressure

    async def check_async(self, **kwargs) -> bool:
        try:
            # Read both sensors concurrently
            temp_task = self.temp_sensor.read_temperature()
            pressure_task = self.pressure_sensor.read_pressure()

            temp, pressure = await asyncio.gather(temp_task, pressure_task)

            temp_ok = temp >= self.min_temp
            pressure_ok = pressure <= self.max_pressure

            print(f"  🌡️  Temperature: {temp:.1f}°C ({'✅' if temp_ok else '❌'})")
            print(
                f"  🔽 Pressure: {pressure:.1f} hPa ({'✅' if pressure_ok else '❌'})"
            )

            return temp_ok and pressure_ok
        except Exception as e:
            print(f"  ❌ Sensor error: {e}")
            return False


# Example state machine with sensor conditions
class EnvironmentState(State):
    """Base state for environment monitoring system"""

    def on_enter(self, from_state, trigger, **kwargs):
        print(f"  🔄 Entering {self.name} state")


class MonitoringState(EnvironmentState):
    def __init__(self):
        super().__init__("Monitoring")


class AlertState(EnvironmentState):
    def __init__(self):
        super().__init__("Alert")


class SafeState(EnvironmentState):
    def __init__(self):
        super().__init__("Safe")


async def demo_async_sensor_conditions():
    """Demonstrate async sensor conditions in action"""

    print("🚀 Async Sensor Condition Demo")
    print("=" * 50)

    # Create sensors
    temp_sensor = TemperatureSensor(base_temp=18.0)  # Start below threshold
    pressure_sensor = PressureSensor(base_pressure=1020.0)  # Start above threshold

    # Create states
    monitoring = MonitoringState()
    alert = AlertState()
    safe = SafeState()

    # Create sensor conditions
    temp_high = TemperatureCondition(temp_sensor, min_temp=25.0)
    temp_safe = TemperatureCondition(temp_sensor, min_temp=20.0)
    combined_safe = CombinedSensorCondition(
        temp_sensor, pressure_sensor, min_temp=22.0, max_pressure=1015.0
    )

    # Create FSM
    fsm = AsyncStateMachine(monitoring, name="EnvironmentMonitor")
    fsm.add_state(alert)
    fsm.add_state(safe)

    # Add transitions with async conditions
    fsm.add_transition("check_alert", "Monitoring", "Alert", condition=temp_high)
    fsm.add_transition(
        "check_safe", ["Monitoring", "Alert"], "Safe", condition=combined_safe
    )
    fsm.add_transition("check_monitor", "Safe", "Monitoring", condition=temp_safe)

    print(f"Initial state: {fsm.current_state_name}")

    # Simulate environmental changes over time
    for i in range(8):
        print(f"\n--- Cycle {i + 1} ---")

        # Gradually increase temperature to trigger conditions
        temp_sensor.base_temp += 1.0

        # Gradually decrease pressure
        pressure_sensor.base_pressure -= 1.5

        # Check various transitions
        print("Checking alert condition...")
        result = await fsm.trigger_async("check_alert")
        if not result.success:
            print(f"  Alert check: {result.error}")

        print("Checking safe condition...")
        result = await fsm.trigger_async("check_safe")
        if not result.success:
            print(f"  Safe check: {result.error}")

        print("Checking monitor condition...")
        result = await fsm.trigger_async("check_monitor")
        if not result.success:
            print(f"  Monitor check: {result.error}")

        print(f"Current state: {fsm.current_state_name}")

        # Brief pause between cycles
        await asyncio.sleep(0.5)

    print("\n🎯 Demo completed!")


if __name__ == "__main__":

    async def main():
        await demo_async_sensor_conditions()

        print("\n" + "=" * 50)
        print("📋 Key Features Demonstrated:")
        print("• Async sensor reading with network delays")
        print("• Real-time condition evaluation")
        print("• Concurrent sensor reading")
        print("• Error handling and timeouts")
        print("• Integration with Fast FSM state machines")
        print("• Custom async condition classes")

    # Run the demo
    asyncio.run(main())
