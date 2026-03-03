#!/usr/bin/env python3
"""
Enhanced FSMBuilder Example

Demonstrates the improved FSMBuilder with:
- Auto-detection of async requirements
- Explicit async/sync mode selection
- Mixed sync/async component handling
- Enhanced logging and validation
"""

import asyncio
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fast_fsm import (
    State,
    AsyncStateMachine,
    FSMBuilder,
    DeclarativeState,
    AsyncDeclarativeState,
    transition,
    Condition,
    AsyncCondition,
    configure_fsm_logging,
)


# Regular state
class RegularState(State):
    def on_enter(self, from_state, trigger, **kwargs):
        print(f"📍 Entered regular state: {self.name}")


# Sync declarative state
class SyncDeclarativeState(DeclarativeState):
    @transition("sync_action")
    def handle_sync_action(self, **kwargs):
        print(f"🔄 Sync action in {self.name}")
        return True


# Async declarative state
class AsyncDeclarativeState(AsyncDeclarativeState):
    @transition("async_action")
    async def handle_async_action(self, **kwargs):
        await asyncio.sleep(0.1)
        print(f"⚡ Async action in {self.name}")
        return True


# Sync condition
class SyncCondition(Condition):
    def __init__(self, required_value: int):
        super().__init__(f"sync_condition_{required_value}")
        self.required_value = required_value

    def check(self, value=0, **kwargs):
        return value >= self.required_value


# Async condition
class CustomAsyncCondition(AsyncCondition):
    def __init__(self, required_value: int):
        super().__init__(f"async_condition_{required_value}")
        self.required_value = required_value

    async def check_async(self, value=0, **kwargs):
        await asyncio.sleep(0.05)  # Simulate async check
        return value >= self.required_value


def demo_auto_detection():
    """Demonstrate automatic async detection"""
    print("🚀 FSMBuilder Auto-Detection Demo")
    print("=" * 50)

    # Enable logging to see detection
    configure_fsm_logging(logging.DEBUG, "fast_fsm")

    print("\n--- Test 1: Regular states (should be sync) ---")
    idle = RegularState("Idle")
    working = RegularState("Working")

    builder = FSMBuilder(idle, name="RegularFSM")
    builder.add_state(working)
    builder.add_transition("start", "Idle", "Working")

    print(f"Builder type: {builder.machine_type.__name__}")
    print(f"Is async: {builder.is_async}")
    fsm1 = builder.build()
    print(f"Built: {type(fsm1).__name__}")

    print("\n--- Test 2: Sync declarative state (should stay sync) ---")
    sync_state = SyncDeclarativeState("SyncState")

    builder2 = FSMBuilder(idle, name="SyncDeclarativeFSM")
    builder2.add_state(sync_state)
    builder2.add_transition("to_sync", "Idle", "SyncState")

    print(f"Builder type: {builder2.machine_type.__name__}")
    print(f"Is async: {builder2.is_async}")
    fsm2 = builder2.build()
    print(f"Built: {type(fsm2).__name__}")

    print("\n--- Test 3: Async declarative state (should become async) ---")
    async_state = AsyncDeclarativeState("AsyncState")

    builder3 = FSMBuilder(idle, name="AsyncDeclarativeFSM")
    builder3.add_state(async_state)
    builder3.add_transition("to_async", "Idle", "AsyncState")

    print(f"Builder type: {builder3.machine_type.__name__}")
    print(f"Is async: {builder3.is_async}")
    fsm3 = builder3.build()
    print(f"Built: {type(fsm3).__name__}")

    print("\n--- Test 4: Async condition (should become async) ---")
    async_condition = CustomAsyncCondition(5)

    builder4 = FSMBuilder(idle, name="AsyncConditionFSM")
    builder4.add_state(working)
    builder4.add_transition(
        "conditional_start", "Idle", "Working", condition=async_condition
    )

    print(f"Builder type: {builder4.machine_type.__name__}")
    print(f"Is async: {builder4.is_async}")
    fsm4 = builder4.build()
    print(f"Built: {type(fsm4).__name__}")


def demo_explicit_mode():
    """Demonstrate explicit async/sync mode selection"""
    print("\n\n🎯 FSMBuilder Explicit Mode Demo")
    print("=" * 50)

    idle = RegularState("Idle")
    working = RegularState("Working")

    print("\n--- Test 1: Force async mode ---")
    builder_async = FSMBuilder(idle, async_mode=True, name="ForcedAsyncFSM")
    builder_async.add_state(working)
    builder_async.add_transition("start", "Idle", "Working")

    print(f"Builder type: {builder_async.machine_type.__name__}")
    fsm_async = builder_async.build()
    print(f"Built: {type(fsm_async).__name__}")

    print("\n--- Test 2: Force sync mode ---")
    builder_sync = FSMBuilder(idle, async_mode=False, name="ForcedSyncFSM")
    builder_sync.add_state(working)
    builder_sync.add_transition("start", "Idle", "Working")

    print(f"Builder type: {builder_sync.machine_type.__name__}")
    fsm_sync = builder_sync.build()
    print(f"Built: {type(fsm_sync).__name__}")

    print("\n--- Test 3: Force sync with async components (warnings expected) ---")
    async_state = AsyncDeclarativeState("AsyncState")
    async_condition = CustomAsyncCondition(5)

    builder_mixed = FSMBuilder(idle, async_mode=False, name="MixedFSM")
    builder_mixed.add_state(async_state)
    builder_mixed.add_transition(
        "to_async", "Idle", "AsyncState", condition=async_condition
    )

    print(f"Builder type: {builder_mixed.machine_type.__name__}")
    fsm_mixed = builder_mixed.build()
    print(f"Built: {type(fsm_mixed).__name__}")


def demo_fluent_api():
    """Demonstrate enhanced fluent API"""
    print("\n\n🔧 FSMBuilder Fluent API Demo")
    print("=" * 50)

    print("\n--- Test 1: Chained force_async() ---")
    fsm1 = (
        FSMBuilder(RegularState("Start"), name="ChainedAsync")
        .add_state(RegularState("Middle"))
        .add_state(RegularState("End"))
        .add_transition("next", "Start", "Middle")
        .add_transition("finish", "Middle", "End")
        .force_async()  # Force async mode
        .build()
    )

    print(f"Built: {type(fsm1).__name__}")

    print("\n--- Test 2: Auto-detect with mixed components ---")
    sync_condition = SyncCondition(3)
    async_condition = CustomAsyncCondition(7)

    fsm2 = (
        FSMBuilder(RegularState("Start"), name="MixedComponents")
        .add_state(SyncDeclarativeState("SyncState"))
        .add_state(AsyncDeclarativeState("AsyncState"))  # This will trigger async
        .add_transition("to_sync", "Start", "SyncState", condition=sync_condition)
        .add_transition(
            "to_async", "SyncState", "AsyncState", condition=async_condition
        )
        .build()
    )

    print(f"Built: {type(fsm2).__name__}")

    print("\n--- Test 3: Builder inspection ---")
    builder = (
        FSMBuilder(RegularState("Initial"), name="InspectionTest")
        .add_state(AsyncDeclarativeState("AsyncState"))
        .add_transition("go", "Initial", "AsyncState")
    )

    print(f"Builder before build: {builder}")
    print(f"Machine type: {builder.machine_type.__name__}")
    print(f"Is async: {builder.is_async}")

    fsm = builder.build()
    print(f"Builder after build: {builder}")
    print(f"Final FSM type: {type(fsm).__name__}")


async def demo_async_usage():
    """Demonstrate actual async FSM usage"""
    print("\n\n⚡ Async FSM Usage Demo")
    print("=" * 50)

    # Build async FSM
    monitoring = AsyncDeclarativeState("Monitoring")
    alert = AsyncDeclarativeState("Alert")

    fsm = (
        FSMBuilder(monitoring, name="AsyncSensorFSM")
        .add_state(alert)
        .add_transition("async_action", "Monitoring", "Alert")
        .build()
    )

    print(f"Built async FSM: {type(fsm).__name__}")
    print(f"Initial state: {fsm.current_state.name}")

    # Use async FSM
    if isinstance(fsm, AsyncStateMachine):
        result = await fsm.trigger_async("async_action")
        print(f"Async transition result: {result.success}")
        print(f"Current state: {fsm.current_state.name}")
    else:
        print("FSM is not async - cannot demonstrate async usage")


async def main():
    """Run all demonstrations"""
    demo_auto_detection()
    demo_explicit_mode()
    demo_fluent_api()
    await demo_async_usage()

    print("\n" + "=" * 50)
    print("🎯 Key FSMBuilder Enhancements:")
    print("• Auto-detection of async requirements")
    print("• Explicit async/sync mode control")
    print("• Enhanced logging and validation")
    print("• Backwards compatibility")
    print("• Fluent API with inspection capabilities")
    print("• Mixed sync/async component warnings")


if __name__ == "__main__":
    asyncio.run(main())
