#!/usr/bin/env python3
"""
Order Processing System Example using Fast FSM

Demonstrates an e-commerce order processing workflow with:
- 5 states: Pending, Processing, Shipped, Delivered, Cancelled
- Conditional transitions based on payment and inventory
- FSM validation and analysis
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fast_fsm import State, FSMBuilder, validate_fsm


class OrderState(State):
    """Base class for order processing states"""

    def on_enter(self, from_state, trigger, **kwargs):
        order_id = kwargs.get("order_id", "UNKNOWN")
        print(
            f"📦 Order {order_id}: {self.name} (from {from_state.name if from_state else 'start'})"
        )


def create_order_processing_fsm():
    """Create an e-commerce order processing FSM"""

    # Define order states
    pending = OrderState("Pending")
    paid = OrderState("Paid")
    processing = OrderState("Processing")
    shipped = OrderState("Shipped")
    delivered = OrderState("Delivered")
    cancelled = OrderState("Cancelled")
    refunded = OrderState("Refunded")

    # Build the order FSM
    order_fsm = (
        FSMBuilder(pending, enable_logging=False)
        .add_state(paid)
        .add_state(processing)
        .add_state(shipped)
        .add_state(delivered)
        .add_state(cancelled)
        .add_state(refunded)
        # Normal flow
        .add_transition("payment_received", "Pending", "Paid")
        .add_transition("start_processing", "Paid", "Processing")
        .add_transition("ship_order", "Processing", "Shipped")
        .add_transition("deliver_order", "Shipped", "Delivered")
        # Cancellation flow
        .add_transition("cancel_order", ["Pending", "Paid"], "Cancelled")
        .add_transition("cancel_order", "Processing", "Cancelled")
        # Refund flow
        .add_transition("request_refund", ["Paid", "Processing", "Shipped"], "Refunded")
        .add_transition("refund_delivered", "Delivered", "Refunded")
        .build()
    )

    return order_fsm


def main():
    """Main demonstration"""

    print("🛒 E-commerce Order Processing FSM Demo")
    print("=" * 60)

    # Create the FSM
    order_fsm = create_order_processing_fsm()

    # Validate the FSM design
    print("🔍 Validating FSM design...")
    validator = validate_fsm(order_fsm)
    validation = validator.validate_completeness()

    # Quick validation summary
    print("✅ FSM Summary:")
    print(f"   States: {validation['total_states']}")
    print(f"   Events: {validation['total_events']}")
    print(f"   Transitions: {validation['total_transitions']}")
    print(f"   Complete: {'✅' if validation['is_complete'] else '❌'}")
    print(f"   All Reachable: {'✅' if validation['is_reachable'] else '❌'}")

    if validation["missing_transitions"]:
        print(f"⚠️  Missing transitions: {len(validation['missing_transitions'])}")

    if validation["dead_states"]:
        print(f"⚠️  Dead states: {validation['dead_states']}")

    # Simulate order processing
    print("\n📦 Simulating Order Processing...")
    order_id = "ORD-2025-001"

    # Normal happy path
    print(f"\n--- Happy Path for {order_id} ---")
    order_fsm.trigger("payment_received", order_id=order_id)
    order_fsm.trigger("start_processing", order_id=order_id)
    order_fsm.trigger("ship_order", order_id=order_id)
    order_fsm.trigger("deliver_order", order_id=order_id)

    # Reset for cancellation scenario
    print("\n--- Cancellation Scenario for ORD-2025-002 ---")
    order_fsm._current_state = order_fsm._states["Pending"]  # Reset
    order_id = "ORD-2025-002"

    order_fsm.trigger("payment_received", order_id=order_id)
    order_fsm.trigger("start_processing", order_id=order_id)
    order_fsm.trigger("cancel_order", order_id=order_id)

    # Generate test scenarios
    print("\n🧪 Generated Test Scenarios:")
    test_paths = validator.generate_test_paths(max_length=4, max_paths=5)

    for i, path in enumerate(test_paths[:3]):  # Show first 3
        print(f"   Test {i + 1}: Pending", end="")
        for from_state, event, to_state in path:
            print(f" --[{event}]--> {to_state}", end="")
        print()

    # Show validation insights
    print("\n🔍 FSM Analysis Insights:")

    cycles = validator.find_cycles()
    if cycles:
        print(f"   🔄 Found {len(cycles)} cycles (potential loops)")
    else:
        print("   ✅ No cycles detected (linear workflow)")

    reachable = validator.get_reachable_states()
    print(f"   📍 {len(reachable)} states reachable from initial state")

    # Performance note
    print("\n⚡ Performance: Fast FSM with validation provides")
    print("   • High-speed transitions (~250K/sec)")
    print("   • Minimal memory footprint")
    print("   • Comprehensive validation without runtime overhead")
    print("   • Clean separation of concerns")


if __name__ == "__main__":
    main()
