#!/usr/bin/env python3
"""Tier 1: build a workflow with fluent callbacks, fan-out, and reset."""

from collections.abc import Callable

from fast_fsm import FSMBuilder, State


def report_entry(label: str) -> Callable[..., None]:
    def report(from_state: State | None, trigger: str, **context: object) -> None:
        source = from_state.name if from_state else "start"
        print(f"order={context.get('order_id')} {source} --{trigger}--> {label}")

    return report


def create_order_fsm():
    states = [
        State("Pending"),
        State("Paid"),
        State("Processing"),
        State("Shipped"),
        State("Delivered"),
        State("Cancelled"),
    ]
    builder = FSMBuilder(states[0], name="OrderWorkflow")
    for state in states[1:]:
        builder.add_state(state)

    builder.add_transition("pay", "Pending", "Paid")
    builder.add_transition("process", "Paid", "Processing")
    builder.add_transition("ship", "Processing", "Shipped")
    builder.add_transition("deliver", "Shipped", "Delivered")
    builder.add_transition("cancel", ["Pending", "Paid", "Processing"], "Cancelled")
    for state in states:
        builder.on_enter(state.name, report_entry(state.name))
    builder.on_enter("Shipped", lambda *_args, **_kwargs: print("notification=sent"))
    return builder.build()


def main() -> None:
    orders = create_order_fsm()
    for trigger in ("pay", "process", "ship", "deliver"):
        orders.trigger(trigger, order_id="A-100").raise_if_failed()

    orders.reset()
    orders.trigger("pay", order_id="A-101").raise_if_failed()
    orders.trigger("cancel", order_id="A-101").raise_if_failed()
    rejected = orders.trigger("ship", order_id="A-101")
    print(
        f"Ship cancelled order? {rejected.success}; state={orders.current_state_name}"
    )


if __name__ == "__main__":
    main()
