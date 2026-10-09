# Strict order and escrow state machine governing fund lifecycle
# Enforces that ONLY backend transitions state and EVERY change is immutably audited.
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.models.order import Order, OrderState, OrderStateTransition
from app.models.audit import SystemAuditLog
from app.core.config import settings

# Explicit map of strictly permitted transitions
ALLOWED_TRANSITIONS = {
    OrderState.CREATED: [OrderState.PAID_HELD, OrderState.CANCELLED],
    OrderState.PAID_HELD: [OrderState.SHIPPED, OrderState.CANCELLED, OrderState.DISPUTED],
    OrderState.SHIPPED: [OrderState.DELIVERED, OrderState.DISPUTED],
    OrderState.DELIVERED: [OrderState.INSPECTION_WINDOW, OrderState.DISPUTED],
    OrderState.INSPECTION_WINDOW: [OrderState.RELEASED, OrderState.DISPUTED],
    OrderState.DISPUTED: [OrderState.RELEASED, OrderState.REFUNDED],
    OrderState.CANCELLED: [OrderState.REFUNDED],
    OrderState.RELEASED: [], # Terminal state
    OrderState.REFUNDED: [], # Terminal state
}

async def transition_order_state(
    order: Order,
    target_state: OrderState,
    trigger_source: str, # 'BUYER', 'SELLER', 'ADMIN', 'SYSTEM_TIMER', 'WEBHOOK'
    triggered_by_id: str = None,
    metadata: dict = None,
    db: AsyncSession = None
) -> Order:
    # Verifies validity of transition, updates order timestamps, and writes immutable audit entry
    current_state = order.current_state

    # 1. State Invariant Validation: check if jump is mathematically allowed
    allowed_next_states = ALLOWED_TRANSITIONS.get(current_state, [])
    if target_state not in allowed_next_states:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Illegal state transition from '{current_state.value}' to '{target_state.value}'. Permitted: {[s.value for s in allowed_next_states]}"
        )

    # 2. Side-effect handling per state
    now_utc = datetime.now(timezone.utc)
    if target_state == OrderState.INSPECTION_WINDOW:
        # Start 48-hour buyer inspection window countdown
        order.inspection_window_ends_at = now_utc + timedelta(hours=settings.INSPECTION_WINDOW_HOURS)
    elif target_state == OrderState.RELEASED:
        # Payout release to seller bank account
        order.released_at = now_utc
        from app.services.ledger_service import record_escrow_payout_release_ledger
        await record_escrow_payout_release_ledger(order, db)
    elif target_state == OrderState.REFUNDED:
        # Refund payment returned to buyer
        order.refunded_at = now_utc
        from app.services.ledger_service import record_order_refund_ledger
        await record_order_refund_ledger(order, order.gateway_payment_id or "REFUND_GATEWAY", db)

    # 3. Update order current state
    order.current_state = target_state

    # 4. Log immutable state transition record
    transition_record = OrderStateTransition(
        order_id=order.id,
        from_state=current_state,
        to_state=target_state,
        triggered_by=triggered_by_id,
        trigger_source=trigger_source,
        transition_metadata=metadata or {}
    )
    db.add(transition_record)

    # 5. Log to system audit trail
    audit_entry = SystemAuditLog(
        actor_id=triggered_by_id,
        action_type=f"ORDER_STATE_{target_state.value}",
        resource_type="ORDER",
        resource_id=order.id,
        details={
            "from_state": current_state.value,
            "to_state": target_state.value,
            "trigger_source": trigger_source,
            "metadata": metadata or {}
        }
    )
    db.add(audit_entry)

    await db.commit()
    await db.refresh(order)
    return order
