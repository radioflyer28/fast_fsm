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
