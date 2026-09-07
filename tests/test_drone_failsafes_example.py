"""Regression checks for the drone safety example's telemetry boundary."""

import importlib.util
import sys
from pathlib import Path


def _load_example_module():
    """Load the runnable example without making ``examples`` a package."""
    path = Path(__file__).parents[1] / "examples" / "drone_failsafes.py"
    spec = importlib.util.spec_from_file_location("drone_failsafes_example", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _ready_sample(example, **overrides):
    """Return one normalized, pre-arm-safe sample with selected overrides."""
    values = {
        "battery_pct": 82,
        "gps_fix": True,
        "home_position_set": True,
        "propellers_clear": True,
        "geofence_loaded": True,
        "launch_area_clear": True,
    }
    values.update(overrides)
    return example.TelemetrySample(**values)


def _fly_to_mission(example, controller):
    """Prepare the simulated controller for an in-flight failsafe test."""
    controller.update_from_telemetry(_ready_sample(example))
    assert controller.perform_operator_action("arm").success
    assert controller.perform_operator_action("takeoff").success
    assert controller.perform_operator_action("begin_mission").success
    assert controller.current_state_name == "Mission"


def test_link_loss_guard_uses_the_policy_heartbeat_age():
    """A guard may use a temporal telemetry fact without selecting an event."""
    example = _load_example_module()
    now = [100.0]
    policy = example.TelemetryPolicy(clock=lambda: now[0])
    policy.observe(example.TelemetrySample(battery_pct=80, link_ok=True))

    assert not policy.heartbeat_older_than(5)
    assert not example.link_lost(telemetry_policy=policy)

    now[0] += 5.1

    assert policy.heartbeat_older_than(5)
    assert example.link_lost(telemetry_policy=policy)


def test_telemetry_policy_exposes_facts_without_routing_choices():
    """Telemetry provides observations and age facts, never an FSM decision."""
    example = _load_example_module()
    policy = example.TelemetryPolicy()
    sample = example.TelemetrySample(battery_pct=80)

    policy.observe(sample)

    assert policy.sample is sample
    assert isinstance(policy.heartbeat_older_than(5), bool)
    for forbidden_choice in (
        "choose_command",
        "choose_event",
        "choose_priority",
        "choose_state",
        "choose_transition",
    ):
        assert not hasattr(policy, forbidden_choice)


def test_controller_composes_a_replaceable_aircraft_adapter_not_an_fsm():
    """The simulated adapter stays outside the FSM inheritance hierarchy."""
    example = _load_example_module()
    aircraft = example.SimulatedAircraft()
    controller = example.DroneController(aircraft)

    assert controller._aircraft is aircraft
    assert not isinstance(aircraft, example.State)
    assert not issubclass(example.SimulatedAircraft, example.State)


def test_controller_observes_one_sample_and_dispatches_one_telemetry_tick():
    """A telemetry packet reaches the owned FSM once through one event name."""
    example = _load_example_module()

    class CountingPolicy(example.TelemetryPolicy):
        def __init__(self):
            super().__init__()
            self.observations = 0

        def observe(self, sample):
            self.observations += 1
            super().observe(sample)

    class CountingFsm:
        def __init__(self, fsm):
            self._fsm = fsm
            self.calls = []

        @property
        def current_state_name(self):
            return self._fsm.current_state_name

        def trigger(self, trigger, **kwargs):
            self.calls.append((trigger, kwargs))
            return self._fsm.trigger(trigger, **kwargs)

    policy = CountingPolicy()
    controller = example.DroneController(example.SimulatedAircraft(), policy)
    counting_fsm = CountingFsm(controller._fsm)
    controller._fsm = counting_fsm
    sample = _ready_sample(example)

    result = controller.update_from_telemetry(sample)

    assert policy.observations == 1
    assert len(counting_fsm.calls) == 1
    assert counting_fsm.calls[0][0] == "telemetry_tick"
    assert counting_fsm.calls[0][1]["telemetry_policy"] is policy
    assert not result.success


def test_critical_fault_wins_simultaneous_failsafes_and_commands_after_commit():
    """The priority-zero critical candidate alone reaches the command adapter."""
    example = _load_example_module()

    class RecordingAircraft:
        def __init__(self):
            self.commands = []
            self.states_when_commanded = []
            self.state_provider = None

        def _record(self, command):
            self.commands.append(command)
            self.states_when_commanded.append(self.state_provider())

        def command_arm_motors(self):
            self._record("command_arm_motors")

        def command_takeoff(self):
            self._record("command_takeoff")

        def command_start_mission(self):
            self._record("command_start_mission")

        def command_return_to_home(self):
            self._record("command_return_to_home")

        def command_begin_landing(self):
            self._record("command_begin_landing")

        def command_emergency_land(self):
            self._record("command_emergency_land")

        def command_disarm_motors(self):
            self._record("command_disarm_motors")

    aircraft = RecordingAircraft()
    controller = example.DroneController(aircraft)
    aircraft.state_provider = lambda: controller.current_state_name
    _fly_to_mission(example, controller)
    aircraft.commands.clear()
    aircraft.states_when_commanded.clear()

    result = controller.update_from_telemetry(
        _ready_sample(
            example,
            battery_pct=20,
            link_ok=False,
            critical_fault=True,
        )
    )

    assert result.success
    assert result.priority == 0
    assert controller.current_state_name == "EmergencyLanding"
    assert aircraft.commands == ["command_emergency_land"]
    assert aircraft.states_when_commanded == ["EmergencyLanding"]


def test_link_loss_beats_low_battery_and_ineligible_tick_issues_no_command():
    """A priority-ten link loss wins, while no eligible candidate is inert."""
    example = _load_example_module()
    aircraft = example.SimulatedAircraft()
    controller = example.DroneController(aircraft)
    _fly_to_mission(example, controller)
    aircraft.commands.clear()

    result = controller.update_from_telemetry(
        _ready_sample(example, battery_pct=20, link_ok=False)
    )

    assert result.success
    assert result.priority == 10
    assert controller.current_state_name == "ReturnHome"
    assert aircraft.commands == ["command_return_to_home"]

    result = controller.update_from_telemetry(_ready_sample(example, battery_pct=80))

    assert not result.success
    assert controller.current_state_name == "ReturnHome"
    assert aircraft.commands == ["command_return_to_home"]
