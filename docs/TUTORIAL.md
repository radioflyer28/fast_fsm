# Fast FSM tutorial

This tutorial starts with the construction path used by the public examples:
create the states you own, describe the complete topology with `FSMBuilder`,
then build it once. Each lesson adds one flat-FSM concept. Stop at the first
level that solves your problem; the later sections are precise semantics, not a
requirement to make every machine complicated.

```{contents}
:local:
:depth: 2
```

## 1. Build a small machine

`FSMBuilder` is the primary API for a new programmatic machine. It makes the
initial state, additional states, and each edge visible at construction time.

```{testcode}
from fast_fsm import FSMBuilder, State

off = State("off")
on = State("on")
light = (
    FSMBuilder(off, name="Light")
    .add_state(on)
    .add_transition("flip", "off", "on")
    .add_transition("flip", "on", "off")
    .build()
)

result = light.trigger("flip")
print(result.success, result.from_state, result.to_state)
```

```{testoutput}
True off on
```

`trigger()` returns a `TransitionResult`. Read its public fields rather than
inferring a result from a state name or a diagram. An unknown trigger or an
otherwise ineligible transition is an ordinary unsuccessful result:

```{testcode}
from fast_fsm import FSMBuilder, State

idle = State("idle")
done = State("done")
machine = FSMBuilder(idle).add_state(done).add_transition("finish", "idle", "done").build()
result = machine.trigger("missing")
print(result.success, result.committed, result.rejected)
```

```{testoutput}
False False False
```

## 2. Put eligibility and priority in the FSM

Guards answer whether one candidate is eligible. If a trigger intentionally
has several candidates, give them explicit `priority=` values: lower exact
built-in integers run first. This keeps precedence in the finite topology
instead of duplicating it in caller-side `if`/`elif` routing.

```{testcode}
from fast_fsm import FSMBuilder, FuncCondition, State

flying = State("flying")
returning = State("returning")
emergency = State("emergency")
drone = (
    FSMBuilder(flying)
    .add_state(returning)
    .add_state(emergency)
    .add_transition(
        "telemetry_tick", "flying", "emergency",
        FuncCondition(lambda **t: t["critical_fault"]), priority=0,
    )
    .add_transition(
        "telemetry_tick", "flying", "returning",
        FuncCondition(lambda **t: not t["link_ok"]), priority=10,
    )
    .build()
)

result = drone.trigger("telemetry_tick", critical_fault=False, link_ok=False)
print(result.to_state, result.priority)
```

```{testoutput}
returning 10
```

A false guard is not an error: selection falls through to a lower-priority
candidate when one exists. A guard exception is different—it aborts selection
so a broken higher-priority safety rule is not silently treated as false.

## 3. Choose same-state lifecycle semantics explicitly

Two transitions may share the same source and destination state but still mean
different things. The default is **external**: exit and entry callbacks run,
and the state gets a new residency interval. Set `internal=True` for an
in-place update that commits and records a result without exit/entry re-entry.

```{testcode}
from fast_fsm import FSMBuilder, State

events = []
mission = State("mission")
machine = (
    FSMBuilder(mission)
    .on_enter("mission", lambda *_args, **_kwargs: events.append("enter"))
    .on_exit("mission", lambda *_args, **_kwargs: events.append("exit"))
    .add_transition("update", "mission", "mission", internal=True)
    .add_transition("restart", "mission", "mission")
    .build()
)

internal = machine.trigger("update")
external = machine.trigger("restart")
print(internal.internal, external.internal, events)
```

```{testoutput}
True False ['exit', 'enter']
```

The entry callback does not run at builder construction, so only the external
transition contributes the shown `exit`, `enter` lifecycle pair. Equal endpoint
names alone never tell you which mode was selected; inspect `result.internal`.

## 4. Model completion with an explicit final state

A state is final because it was declared `State(name, final=True)`, not because
it happens to have no outgoing edges. A non-final sink may represent an
incomplete topology that can be extended later; a final state records domain
completion and makes `is_terminated` true.

```{testcode}
from fast_fsm import FSMBuilder, State

start = State("start")
sink = State("sink")
complete = State("complete", final=True)
sink_machine = FSMBuilder(start).add_state(sink).add_transition("go", "start", "sink").build()
final_machine = FSMBuilder(start).add_state(complete).add_transition("finish", "start", "complete").build()

sink_machine.trigger("go")
final_machine.trigger("finish")
print(sink_machine.is_terminated, final_machine.is_terminated)
```

```{testoutput}
False True
```

After a final state commits, a trigger cannot start another workflow on that
machine. Create a new controller or machine for the next owned workflow.

## 5. Separate a false guard, an expected rejection, and a bug

A false guard means “this candidate is not eligible” and can fall through.
Raise `TransitionRejected("bounded-code")` inside a guard for a known terminal
domain outcome. It returns a non-committed result with `rejected=True` and the
public `rejection_code`. Any other exception is an unexpected failure, exposed
through `result.cause`; it is not a rejection and it must not be hidden as a
false guard.

```{testcode}
from fast_fsm import FSMBuilder, FuncCondition, State, TransitionRejected

idle = State("idle")
next_state = State("next")

def reject_if_conflicting(*, conflicting=False, **_):
    if conflicting:
        raise TransitionRejected("navigation-conflict")
    return False

machine = (
    FSMBuilder(idle)
    .add_state(next_state)
    .add_transition("go", "idle", "next", FuncCondition(reject_if_conflicting), priority=0)
    .add_transition("go", "idle", "next", priority=10)
    .build()
)

ordinary = machine.trigger("go", conflicting=False)
print(ordinary.success, ordinary.committed, ordinary.rejected)

blocked = FSMBuilder(idle).add_state(next_state).add_transition(
    "go", "idle", "next", FuncCondition(reject_if_conflicting)
).build().trigger("go", conflicting=True)
print(blocked.success, blocked.committed, blocked.rejected, blocked.rejection_code)
```

```{testoutput}
True True False
False False True navigation-conflict
```

See the [core API semantic contrasts](api/core.md#flat-fsm-semantic-contrasts)
for a compact executable example that also shows an unexpected failure.

## 6. Use diagnostics after the topology is clear

Runtime selection should stay small and direct. Analysis is opt-in design-time
work: use the validator and visualization tools to inspect a finished topology,
not to decide what a dispatch should do. Diagnostics can expose finality,
transition modes, and expected-rejection facts, but never change transition
eligibility or priority.

For a compact example, see [Diagnostics and visualization](examples/index.md#diagnostics_and_visualizationpy--design-time-tooling).

## 7. Learn the controller-owned drone workflow

The [drone failsafes example](examples/index.md#drone_failsafespy--controller-owned-telemetry)
combines the earlier ideas in one deterministic integration story:

- `DroneController` owns the machine and a replaceable aircraft-command adapter.
- Every normalized telemetry sample produces one `telemetry_tick`; its guards,
  including failsafe precedence, live in the FSM.
- `TelemetryPolicy` retains only observable facts such as heartbeat age. It does
  not decide state-dependent transitions.
- Mission demonstrates both internal updates and external re-entry. Landing is
  explicit finality, and a navigation conflict is an expected rejection.
- Aircraft commands are attached to destination entry callbacks, so they run
  only after a successful transition commits.

The script is deterministic training software, not hardware, certification, or
real-time flight-control guidance. It has an independent smoke test; the Sphinx
gallery inclusion only displays the source.

## 8. Supported advanced construction paths

`FSMBuilder` is the starting point when your application declares a new
topology. The following paths are supported but serve distinct advanced roles:

- Direct `StateMachine` or `AsyncStateMachine` construction is for intentional
  incremental topology control.
- `FSMBuilder` automatically selects `AsyncStateMachine` when it receives an
  `AsyncCondition`; use `trigger_async()` on the resulting async machine.
- `StateMachine.from_dict()` reconstructs serialized topology. It is a
  persistence adapter, not an alternative general-purpose builder.
- Declarative state classes are supported when state-local handlers make the
  topology easier to read; they are not deprecated.

## 9. Migrate the four historical convenience helpers

`simple_fsm`, `quick_fsm`, `StateMachine.quick_build`, and
`StateMachine.from_states` each emit one compatibility warning per call through
v0.5.x. They will be removed no earlier than v0.6.0. New code should make the
same construction explicit with `FSMBuilder`:

| Warned helper | Builder replacement |
| --- | --- |
| `simple_fsm` | `FSMBuilder(State("idle"))` plus `.add_state(...)` |
| `quick_fsm` | `FSMBuilder(State("idle"))` plus one `.add_transition(...)` per edge |
| `StateMachine.quick_build` | `FSMBuilder(initial_state)` plus explicit states and transitions |
| `StateMachine.from_states` | `FSMBuilder(State("idle"))` plus `.add_state(...)` for a named state-only topology |

These warnings do **not** deprecate direct constructors, `from_dict()`, or
declarative state APIs. For complete executable migration snippets, see
[Compatibility migration](../README.md#compatibility-migration) and
[Quick Start](QUICK_START.md#construction-roles).

## 10. Artifact and performance proof

Fast FSM preserves a direct O(1) singleton dispatch path when new semantics
are unused. The supported durable floor is measured on a fresh installed
compiled artifact; feature costs for finality, self-transition mode, and
rejection are recorded as separate environment-labelled observations. Do not
generalize a local timing result into a universal speed claim.

Before a release candidate is accepted, the same fixed semantic oracle checks
pure source, fresh native core, installed pure and compiled wheels, and release
artifacts with exact origin and build-intent checks. The normal contributor
workflow uses `uv.lock` and `uv sync --locked`; it does not require a custom
cache, offline mode, or a particular `uv` patch release.

## Where next?

- [Examples](examples/index.md) for runnable, feature-focused scripts.
- [Core API](api/core.md) for exact result fields and lifecycle contracts.
- [Conditions API](api/conditions.md) for reusable guard composition.
- [Validation API](api/validation.md) for design-time graph analysis.
