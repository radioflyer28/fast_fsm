#!/usr/bin/env python3
"""Tier 3: compare FSMBuilder sync, auto-async, and forced-sync modes."""

import asyncio

from fast_fsm import AsyncCondition, AsyncStateMachine, FSMBuilder, State


class ServiceReady(AsyncCondition):
    __slots__ = ()

    def __init__(self) -> None:
        super().__init__("service_ready")

    async def check_async(self, ready: bool = False, **_context: object) -> bool:
        await asyncio.sleep(0)
        return ready


async def main() -> None:
    sync_machine = (
        FSMBuilder(State("Idle"), name="SyncWorker")
        .add_state(State("Running"))
        .add_transition("start", "Idle", "Running")
        .build()
    )
    print(f"ordinary components -> {type(sync_machine).__name__}")
    sync_machine.trigger("start").raise_if_failed()

    async_machine = (
        FSMBuilder(State("Idle"), name="AsyncWorker")
        .add_state(State("Running"))
        .add_transition("start", "Idle", "Running", condition=ServiceReady())
        .build()
    )
    print(f"async guard -> {type(async_machine).__name__}")
    assert isinstance(async_machine, AsyncStateMachine)
    await async_machine.trigger_async("start", ready=True)

    forced_sync = (
        FSMBuilder(State("Idle"), async_mode=False, name="InvalidWorker")
        .add_state(State("Running"))
        .add_transition("start", "Idle", "Running", condition=ServiceReady())
    )
    try:
        forced_sync.build()
    except RuntimeError as error:
        print(f"forced sync rejected async component: {error}")


if __name__ == "__main__":
    asyncio.run(main())
