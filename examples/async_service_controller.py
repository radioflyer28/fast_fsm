#!/usr/bin/env python3
"""Tier 4: coordinate concurrent async callers and lifecycle callbacks safely."""

import asyncio

from fast_fsm import AsyncStateMachine, State


async def main() -> None:
    machine = AsyncStateMachine(State("Stopped"), name="ServiceController")
    machine.add_state(State("Starting"))
    machine.add_state(State("Running"))
    machine.add_transition("start", "Stopped", "Starting")
    machine.add_transition("ready", "Starting", "Running")

    entered = asyncio.Event()
    release = asyncio.Event()

    async def initialize(_source: State, _trigger: str, **_context: object) -> None:
        print("lifecycle: initializing")
        entered.set()
        await release.wait()

    async def report_exit(target: State, trigger: str, **_context: object) -> None:
        await asyncio.sleep(0)
        print(f"lifecycle: leaving Starting for {target.name} via {trigger}")

    machine.on_enter_async("Starting", initialize)
    machine.on_exit_async("Starting", report_exit)
    print(f"can start={await machine.can_trigger_async('start')}")

    first = asyncio.create_task(machine.trigger_async("start"))
    await entered.wait()
    second = asyncio.create_task(machine.trigger_async("ready"))
    await asyncio.sleep(0)
    print(f"second caller waits={not second.done()}")
    release.set()

    started, running = await asyncio.gather(first, second)
    print(
        f"results={started.success},{running.success} state={machine.current_state_name}"
    )

    cancelled = asyncio.create_task(machine.trigger_async("missing"))
    cancelled.cancel()
    try:
        await cancelled
    except asyncio.CancelledError:
        print(f"cancelled caller left state={machine.current_state_name}")


if __name__ == "__main__":
    asyncio.run(main())
