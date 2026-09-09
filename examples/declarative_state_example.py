#!/usr/bin/env python3
"""Tier 2: colocate sync and async event handlers with declarative states."""

import asyncio

from fast_fsm import (
    AsyncDeclarativeState,
    AsyncStateMachine,
    DeclarativeState,
    StateMachine,
    transition,
)


class LockedDoor(DeclarativeState):
    @transition("unlock", condition=lambda *, pin="", **_: pin == "1234")
    def unlock(self, *, user: str, **_context: object) -> bool:
        print(f"sync handler authorized {user}")
        return True


class UnlockedDoor(DeclarativeState):
    @transition("lock")
    def lock(self, **_context: object) -> bool:
        print("sync handler secured door")
        return True


class DisconnectedService(AsyncDeclarativeState):
    @transition("connect")
    async def connect(self, *, endpoint: str, **_context: object) -> bool:
        await asyncio.sleep(0)
        print(f"async handler connected to {endpoint}")
        return True


class ConnectedService(AsyncDeclarativeState):
    @transition("disconnect")
    async def disconnect(self, **_context: object) -> bool:
        await asyncio.sleep(0)
        print("async handler disconnected")
        return True


def sync_demo() -> None:
    door = StateMachine(LockedDoor("Locked"), name="Door")
    door.add_state(UnlockedDoor("Unlocked"))
    door.add_transition("unlock", "Locked", "Unlocked")
    door.add_transition("lock", "Unlocked", "Locked")

    denied = door.trigger("unlock", user="Ada", pin="0000")
    print(f"bad pin={denied.success}")
    door.trigger("unlock", user="Ada", pin="1234").raise_if_failed()
    door.trigger("lock").raise_if_failed()


async def async_demo() -> None:
    service = AsyncStateMachine(DisconnectedService("Disconnected"), name="Service")
    service.add_state(ConnectedService("Connected"))
    service.add_transition("connect", "Disconnected", "Connected")
    service.add_transition("disconnect", "Connected", "Disconnected")

    await service.trigger_async("connect", endpoint="cache.local")
    await service.trigger_async("disconnect")


async def main() -> None:
    sync_demo()
    await async_demo()


if __name__ == "__main__":
    asyncio.run(main())
