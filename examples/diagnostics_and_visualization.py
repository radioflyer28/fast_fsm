#!/usr/bin/env python3
"""Tier 4: validate, compare, bound, and render FSM topology."""

import json

from fast_fsm import (
    DiagnosticBudgetExceeded,
    DiagnosticLimits,
    State,
    StateMachine,
    compare_fsms,
    fsm_lint,
    quick_health_check,
    to_json,
    to_mermaid,
    to_mermaid_document,
    to_plantuml,
    validate_and_score,
)


def build_machine(*, corrected: bool) -> StateMachine:
    machine = StateMachine(State("Idle"), name="Corrected" if corrected else "Draft")
    machine.add_state(State("Running"))
    machine.add_state(State("Done"))
    machine.add_state(State("Abandoned"))
    machine.add_transition("start", "Idle", "Running")
    machine.add_transition("finish", "Running", "Done")
    if corrected:
        machine.add_transition("abandon", ["Idle", "Running"], "Abandoned")
        machine.add_transition("restart", ["Done", "Abandoned"], "Idle")
    return machine


def excerpt(label: str, value: str, lines: int = 4) -> None:
    print(f"{label}:\n" + "\n".join(value.splitlines()[:lines]))


def main() -> None:
    draft = build_machine(corrected=False)
    corrected = build_machine(corrected=True)
    print(
        f"health draft={quick_health_check(draft)} corrected={quick_health_check(corrected)}"
    )
    print(f"corrected score={validate_and_score(corrected)['overall_score']}")
    print(f"best={compare_fsms(draft, corrected)['best_fsm']}")
    fsm_lint(draft)

    excerpt("mermaid", to_mermaid(corrected))
    excerpt("plantuml", to_plantuml(corrected))
    excerpt("document", to_mermaid_document(corrected))
    payload = to_json(corrected)
    print(f"json topology states={len(payload['topology']['states'])}")
    json.dumps(payload)

    try:
        to_json(corrected, limits=DiagnosticLimits(max_results=0))
    except DiagnosticBudgetExceeded as error:
        print(
            "bounded diagnostic stopped at "
            f"{error.status.exhausted_dimension}/{error.status.exhausted_stage}"
        )


if __name__ == "__main__":
    main()
