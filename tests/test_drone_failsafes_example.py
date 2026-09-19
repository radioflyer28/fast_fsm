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


class _RecordingAircraft:
    """Capture adapter effects and the committed state that caused each one."""

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


def test_example_uses_builtin_ordered_entry_callbacks_without_state_subclassing():
    """Plain states delegate reporting and commands to the builder callback API."""
    example = _load_example_module()
    controller = example.DroneController(example.SimulatedAircraft())
    fsm = controller._fsm

    assert all(type(state) is example.State for state in fsm._states.values())
    assert len(fsm._state_enter_callbacks["PreArm"]) == 1
    for state_name in (
        "Armed",
        "Takeoff",
        "Mission",
        "ReturnHome",
        "Landing",
        "EmergencyLanding",
        "Landed",
        "EmergencyLanded",
    ):
        assert len(fsm._state_enter_callbacks[state_name]) == 2


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
    assert result.rejected is False
    assert result.rejection_code is None
    assert controller.current_state_name == "ReturnHome"
    assert aircraft.commands == ["command_return_to_home"]


def test_telemetry_tick_distinguishes_internal_and_external_mission_self_modes():
    """One event makes the FSM own self-mode selection and its lifecycle effects."""
    example = _load_example_module()
    now = [0.0]
    aircraft = _RecordingAircraft()
    controller = example.DroneController(
        aircraft,
        example.TelemetryPolicy(clock=lambda: now[0]),
        fsm_clock=lambda: now[0],
    )
    aircraft.state_provider = lambda: controller.current_state_name
    _fly_to_mission(example, controller)
    aircraft.commands.clear()
    aircraft.states_when_commanded.clear()
    mission_entered_at = controller._fsm._state_entered_at

    now[0] = 5.0
    internal = controller.update_from_telemetry(_ready_sample(example))

    assert internal.success is True
    assert internal.committed is True
    assert internal.priority == 60
    assert internal.internal is True
    assert controller._fsm._state_entered_at == mission_entered_at
    assert aircraft.commands == []
    assert controller._fsm.history[-1].internal is True

    now[0] = 12.0
    external = controller.update_from_telemetry(
        _ready_sample(example, reenter_mission=True)
    )

    assert external.success is True
    assert external.committed is True
    assert external.priority == 50
    assert external.internal is False
    assert controller._fsm._state_entered_at == 12.0
    assert aircraft.commands == ["command_start_mission"]
    assert aircraft.states_when_commanded == ["Mission"]
    assert controller._fsm.history[-1].internal is False


def test_normal_and_emergency_landings_are_final_and_require_new_controllers():
    """Touchdown ends each flight without reopening a final state."""
    example = _load_example_module()
    normal_aircraft = _RecordingAircraft()
    normal = example.DroneController(normal_aircraft)
    normal_aircraft.state_provider = lambda: normal.current_state_name
    _fly_to_mission(example, normal)
    normal_aircraft.commands.clear()
    normal_aircraft.states_when_commanded.clear()

    assert (
        normal.update_from_telemetry(_ready_sample(example, battery_pct=20)).priority
        == 20
    )
    assert normal.update_from_telemetry(
        _ready_sample(example, home_reached=True)
    ).success
    touchdown = normal.update_from_telemetry(_ready_sample(example, on_ground=True))

    assert touchdown.success is True
    assert normal.current_state_name == "Landed"
    assert normal._fsm.is_terminated is True
    assert normal_aircraft.commands[-1] == "command_disarm_motors"
    assert normal_aircraft.states_when_commanded[-1] == "Landed"
    commands_before_final_attempt = list(normal_aircraft.commands)
    post_final = normal.perform_operator_action("prepare_next_flight")
    assert post_final.success is False
    assert normal.current_state_name == "Landed"
    assert normal_aircraft.commands == commands_before_final_attempt

    emergency_aircraft = _RecordingAircraft()
    emergency = example.DroneController(emergency_aircraft)
    emergency_aircraft.state_provider = lambda: emergency.current_state_name
    _fly_to_mission(example, emergency)
    emergency_aircraft.commands.clear()
    emergency_aircraft.states_when_commanded.clear()

    assert (
        emergency.update_from_telemetry(
            _ready_sample(example, critical_fault=True)
        ).priority
        == 0
    )
    emergency_touchdown = emergency.update_from_telemetry(
        _ready_sample(example, on_ground=True)
    )

    assert emergency_touchdown.success is True
    assert emergency.current_state_name == "EmergencyLanded"
    assert emergency._fsm.is_terminated is True
    assert emergency_aircraft.commands == [
        "command_emergency_land",
        "command_disarm_motors",
    ]
    assert emergency_aircraft.states_when_commanded == [
        "EmergencyLanding",
        "EmergencyLanded",
    ]


def test_false_navigation_guard_falls_through_to_the_internal_mission_update():
    """A false tutorial candidate advances to the later eligible candidate."""
    example = _load_example_module()
    aircraft = _RecordingAircraft()
    controller = example.DroneController(aircraft)
    aircraft.state_provider = lambda: controller.current_state_name
    _fly_to_mission(example, controller)
    aircraft.commands.clear()
    aircraft.states_when_commanded.clear()

    result = controller.update_from_telemetry(_ready_sample(example))

    assert result.success is True
    assert result.rejected is False
    assert result.rejection_code is None
    assert result.priority == 60
    assert result.internal is True
    assert aircraft.commands == []


def test_navigation_conflict_rejects_without_committing_or_exposing_payload(capsys):
    """A bounded rejection aborts candidate selection and leaves effects inert."""
    example = _load_example_module()
    aircraft = _RecordingAircraft()
    controller = example.DroneController(aircraft)
    aircraft.state_provider = lambda: controller.current_state_name
    _fly_to_mission(example, controller)
    aircraft.commands.clear()
    aircraft.states_when_commanded.clear()
    history_before = list(controller._fsm.history)
    capsys.readouterr()

    result = controller.update_from_telemetry(
        _ready_sample(example, navigation_conflict=True, reenter_mission=True)
    )
    transcript = capsys.readouterr().out

    assert result.success is False
    assert result.rejected is True
    assert result.rejection_code == "navigation-conflict"
    assert result.committed is False
    assert result.priority == 40
    assert result.stage == "guard"
    assert controller.current_state_name == "Mission"
    assert controller._fsm.history == history_before
    assert aircraft.commands == []
    assert aircraft.states_when_commanded == []
    assert "expected rejection: navigation-conflict" in transcript
    assert "Transition rejected:" not in transcript
    assert "TelemetrySample" not in transcript


def test_safety_failsafe_outranks_navigation_conflict_rejection():
    """Tutorial policy cannot hide a selected safety transition."""
    example = _load_example_module()
    aircraft = _RecordingAircraft()
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
            navigation_conflict=True,
        )
    )

    assert result.success is True
    assert result.rejected is False
    assert result.priority == 0
    assert controller.current_state_name == "EmergencyLanding"
    assert aircraft.commands == ["command_emergency_land"]
    assert aircraft.states_when_commanded == ["EmergencyLanding"]
