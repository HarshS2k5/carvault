# Shipping integration, courier tracking updates, delivery OTP, and auto-release timer
import random
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from app.models.order import Order, OrderState, ShippingRecord
from app.services.state_machine import transition_order_state

def generate_delivery_otp():
    # 6-digit delivery OTP sent to buyer via SMS
    return f"{random.randint(100000, 999999)}"

async def update_tracking_status(order_id: str, courier_status: str, db: AsyncSession):
    # Courier webhook adapter (Delhivery / Shiprocket tracking events)
    order = await db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if not order.shipping:
        order.shipping = ShippingRecord(order_id=order.id, status=courier_status)
    else:
        order.shipping.status = courier_status

    if courier_status == "DELIVERED" and order.current_state == OrderState.SHIPPED:
        # Auto-trigger delivery and start 48-hour inspection countdown
        order.shipping.delivered_at = datetime.now(timezone.utc)
        await transition_order_state(order, OrderState.DELIVERED, "COURIER_WEBHOOK", db=db)
        await transition_order_state(order, OrderState.INSPECTION_WINDOW, "SYSTEM_TIMER", db=db)

    await db.commit()
    return order

async def process_expired_inspection_windows(db: AsyncSession) -> int:
    # Background worker task: checks all orders where the 48-hour window expired with no dispute raised
    now_utc = datetime.now(timezone.utc)
    stmt = select(Order).where(
        Order.current_state == OrderState.INSPECTION_WINDOW,
        Order.inspection_window_ends_at <= now_utc
    )
    res = await db.execute(stmt)
    expired_orders = res.scalars().all()

    auto_released_count = 0
    for order in expired_orders:
        await transition_order_state(
            order=order,
            target_state=OrderState.RELEASED,
            trigger_source="SYSTEM_TIMER",
            metadata={"reason": "INSPECTION_WINDOW_EXPIRED_NO_DISPUTE"},
            db=db
        )
        auto_released_count += 1

    return auto_released_count
