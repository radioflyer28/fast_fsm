"""
Test file for async examples and demonstrations.
Contains example async conditions and states that don't belong in the core library.
"""
import asyncio
from typing import Callable, Awaitable
from fast_fsm import AsyncCondition, AsyncStateMachine, State


class SensorCondition(AsyncCondition):
    """
    Example async condition for checking real-time sensor data.
    This is a demonstration of how to create custom async conditions.
    """
    __slots__ = ('sensor_reader', 'threshold', 'timeout')
    
    def __init__(self, sensor_reader: Callable[[], Awaitable[float]], 
                 threshold: float, 
                 name: str = "sensor_check",
                 description: str = "",
                 timeout: float = 1.0):
        """
        Create a sensor condition.
        
        Args:
            sensor_reader: Async function that reads sensor data
            threshold: Threshold value to compare against
            name: Name for this condition
            description: Description of what this condition checks
            timeout: Maximum time to wait for sensor reading (seconds)
        """
        if not description:
            description = f"Sensor reading >= {threshold}"
        super().__init__(name, description)
        self.sensor_reader = sensor_reader
        self.threshold = threshold
        self.timeout = timeout
    
    async def check_async(self, *args, **kwargs) -> bool:
        """Check if sensor reading meets threshold"""
        try:
            # Read sensor data with timeout
            sensor_value = await asyncio.wait_for(
                self.sensor_reader(), 
                timeout=self.timeout
            )
            return sensor_value >= self.threshold
        except asyncio.TimeoutError:
            # Sensor read timed out
            return False
        except Exception:
            # Sensor read failed
            return False


async def mock_temperature_sensor() -> float:
    """Mock sensor that returns random temperature readings"""
    await asyncio.sleep(0.1)  # Simulate sensor read time
    import random
    return random.uniform(15.0, 35.0)


async def mock_pressure_sensor() -> float:
    """Mock sensor that returns random pressure readings"""
    await asyncio.sleep(0.05)  # Simulate faster sensor
    import random
    return random.uniform(900.0, 1100.0)


async def test_sensor_condition():
    """Test the SensorCondition with mock sensors"""
    print("🌡️ Testing SensorCondition with mock sensors")
    
    # Create temperature condition
    temp_condition = SensorCondition(
        sensor_reader=mock_temperature_sensor,
        threshold=20.0,
        name="temp_ok",
        description="Temperature above 20°C"
    )
    
    # Create pressure condition
    pressure_condition = SensorCondition(
        sensor_reader=mock_pressure_sensor,
        threshold=1000.0,
        name="pressure_ok", 
        description="Pressure above 1000 hPa"
    )
    
    # Test conditions multiple times
    for i in range(5):
        temp_ok = await temp_condition.check_async()
        pressure_ok = await pressure_condition.check_async()
        
        print(f"  Test {i+1}: Temperature OK: {temp_ok}, Pressure OK: {pressure_ok}")
        
        # Simulate some delay between readings
        await asyncio.sleep(0.2)


async def test_async_fsm_with_sensors():
    """Test AsyncStateMachine with sensor conditions"""
    print("\n🤖 Testing AsyncStateMachine with sensor conditions")
    
    # Create states
    idle = State('idle')
    monitoring = State('monitoring') 
    alert = State('alert')
    
    # Create FSM
    fsm = AsyncStateMachine(idle, name='SensorMonitor')
    fsm.add_state(monitoring)
    fsm.add_state(alert)
    
    # Create sensor conditions
    temp_condition = SensorCondition(
        mock_temperature_sensor,
        threshold=25.0,
        name="temp_high"
    )
    
    # Add transitions with sensor conditions
    fsm.add_transition('start_monitoring', 'idle', 'monitoring')
    fsm.add_transition('temperature_alert', 'monitoring', 'alert', temp_condition)
    fsm.add_transition('reset', ['monitoring', 'alert'], 'idle')
    
    # Test the FSM
    print(f"  Initial state: {fsm.current_state_name}")
    
    # Start monitoring
    result = await fsm.trigger_async('start_monitoring')
    print(f"  After start_monitoring: {fsm.current_state_name} (success: {result.success})")
    
    # Try temperature alert several times
    for i in range(3):
        result = await fsm.trigger_async('temperature_alert')
        print(f"  Temperature alert attempt {i+1}: {fsm.current_state_name} (success: {result.success})")
        
        if result.success:
            # Reset if we went to alert
            await fsm.trigger_async('reset')
            await fsm.trigger_async('start_monitoring')
        
        await asyncio.sleep(0.3)


if __name__ == "__main__":
    print("🚀 Async Examples Demo")
    print("=" * 50)
    
    # Run the tests
    asyncio.run(test_sensor_condition())
    asyncio.run(test_async_fsm_with_sensors())
    
    print("\n✅ Async examples completed!")
