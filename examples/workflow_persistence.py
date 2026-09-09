#!/usr/bin/env python3
"""Tier 4: observe, snapshot, clone, and serialize a guarded workflow."""

import json

from fast_fsm import FuncCondition, State, StateMachine


class AuditListener:
    def after_transition(
        self, source: State, target: State, trigger: str, **_context: object
    ) -> None:
        print(f"audit {source.name} --{trigger}--> {target.name}")


def build_workflow() -> StateMachine:
    ready = FuncCondition(
        lambda *, approved=False, **_: approved,
        name="approved",
    )
    return StateMachine.from_dict(
        {
            "name": "PublishWorkflow",
            "initial": "Draft",
            "states": ["Draft", "Review", "Published"],
            "transitions": [
                {"trigger": "submit", "from": "Draft", "to": "Review"},
                {
                    "trigger": "publish",
                    "from": "Review",
                    "to": "Published",
                    "condition_ref": "approved",
                },
            ],
        },
        conditions={"approved": ready},
    )


def main() -> None:
    workflow = build_workflow()
    workflow.enable_history(max_entries=5)
    workflow.add_listener(AuditListener())
    workflow.after_transition(
        lambda source, target, trigger, **_: print(
            f"callback current={target.name} trigger={trigger}"
        )
    )
    workflow.on_failed(
        lambda trigger, from_state, error, **_: print(
            f"rejected state={from_state} trigger={trigger}: {error}"
        )
    )

    workflow.trigger("submit").raise_if_failed()
    saved_state = workflow.snapshot()
    workflow.trigger("publish", approved=False)
    workflow.trigger("publish", approved=True).raise_if_failed()
    print(
        "history="
        + ", ".join(f"{row.from_state}->{row.to_state}" for row in workflow.history)
    )

    workflow.restore(saved_state)
    clone = workflow.clone()
    clone.trigger("submit").raise_if_failed()
    clone.trigger("publish", approved=True).raise_if_failed()
    print(f"restored={workflow.current_state_name} clone={clone.current_state_name}")

    topology_json = json.dumps(workflow.to_dict(), sort_keys=True)
    restored = StateMachine.from_dict(
        json.loads(topology_json),
        conditions={"approved": lambda *, approved=False, **_: approved},
    )
    result = restored.trigger("submit")
    result.raise_if_failed()
    restored.trigger("publish", approved=True).raise_if_failed()
    print(f"roundtrip={restored.current_state_name}")


if __name__ == "__main__":
    main()
