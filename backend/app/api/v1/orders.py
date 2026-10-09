# Order lifecycle, shipment dispatch, delivery OTP, and inspection acceptance endpoints
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.listing import Listing, ListingStatus
from app.models.order import Order, OrderState, ShippingRecord
from app.schemas.order import (
    OrderCreateRequest, OrderResponse,
    ShipOrderRequest, DeliveryConfirmRequest, DisputeOpenRequest
)
from app.services.payment_service import calculate_order_financials
from app.services.state_machine import transition_order_state

router = APIRouter()

def serialize_order(order: Order) -> OrderResponse:
    # Formats database order model into clean API response
    return OrderResponse(
        id=order.id,
        listing_id=order.listing_id,
        buyer_id=order.buyer_id,
        seller_id=order.seller_id,
        current_state=order.current_state,
        item_price_paise=order.item_price_paise,
        item_price_rupees=order.item_price_paise / 100.0,
        shipping_fee_paise=order.shipping_fee_paise,
        commission_rate_bps=order.commission_rate_bps,
        commission_paise=order.commission_paise,
        commission_rupees=order.commission_paise / 100.0,
        seller_payable_paise=order.seller_payable_paise,
        seller_payable_rupees=order.seller_payable_paise / 100.0,
        total_buyer_paid_paise=order.total_buyer_paid_paise,
        total_buyer_paid_rupees=order.total_buyer_paid_paise / 100.0,
        gateway_order_id=order.gateway_order_id,
        gateway_payment_id=order.gateway_payment_id,
        inspection_window_ends_at=order.inspection_window_ends_at,
        created_at=order.created_at,
        shipping=order.shipping,
        transitions=order.transitions or []
    )

@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: OrderCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Initializes purchase order for an approved listing and reserves escrow transaction
    listing = await db.get(Listing, payload.listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.status != ListingStatus.APPROVED:
        raise HTTPException(status_code=400, detail="Only approved listings can be purchased")
    if listing.seller_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot purchase your own listing")

    # Compute platform commission and seller payable amounts
    fin = calculate_order_financials(
        item_price_paise=listing.price_paise,
        shipping_fee_paise=payload.shipping_fee_paise
    )

    # Initialize order in CREATED state
    order = Order(
        listing_id=listing.id,
        buyer_id=current_user.id,
        seller_id=listing.seller_id,
        current_state=OrderState.CREATED,
        item_price_paise=fin["item_price_paise"],
        shipping_fee_paise=fin["shipping_fee_paise"],
        commission_rate_bps=fin["commission_rate_bps"],
        commission_paise=fin["commission_paise"],
        min_platform_fee_paise=fin["min_platform_fee_paise"],
        seller_payable_paise=fin["seller_payable_paise"],
        total_buyer_paid_paise=fin["total_buyer_paid_paise"],
        gateway_order_id=f"order_rzp_{listing.id[:8]}_{current_user.id[:4]}"
    )
    db.add(order)

    # Mark listing as SOLD so nobody else can initiate checkout
    listing.status = ListingStatus.SOLD

    await db.commit()
    await db.refresh(order)
    return serialize_order(order)

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Returns order details with complete transition audit history
    order = await db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if current_user.id not in [order.buyer_id, order.seller_id] and current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Unauthorized to view this order")
    return serialize_order(order)

@router.post("/{order_id}/ship", response_model=OrderResponse)
async def ship_order(
    order_id: str,
    payload: ShipOrderRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Seller records courier tracking number and transitions order to SHIPPED
    order = await db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.seller_id != current_user.id and current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Only seller can mark order as shipped")

    # Update or create shipping record
    if not order.shipping:
        ship_rec = ShippingRecord(
            order_id=order.id,
            courier_partner=payload.courier_partner,
            tracking_id=payload.tracking_id,
            seller_packing_video_url=payload.packing_video_url,
            status="IN_TRANSIT"
        )
        db.add(ship_rec)
    else:
        order.shipping.tracking_id = payload.tracking_id
        order.shipping.status = "IN_TRANSIT"

    # State transition: PAID_HELD -> SHIPPED
    order = await transition_order_state(
        order=order,
        target_state=OrderState.SHIPPED,
        trigger_source="SELLER",
        triggered_by_id=current_user.id,
        metadata={"tracking_id": payload.tracking_id, "courier": payload.courier_partner},
        db=db
    )
    return serialize_order(order)

@router.post("/{order_id}/deliver", response_model=OrderResponse)
async def confirm_delivery(
    order_id: str,
    payload: DeliveryConfirmRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Courier / buyer delivery OTP verification: transitions SHIPPED -> DELIVERED -> INSPECTION_WINDOW
    order = await db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # First move SHIPPED -> DELIVERED
    order = await transition_order_state(
        order=order,
        target_state=OrderState.DELIVERED,
        trigger_source="BUYER",
        triggered_by_id=current_user.id,
        metadata={"otp_entered": payload.delivery_otp},
        db=db
    )

    # Automatically transition to INSPECTION_WINDOW to trigger 48-hour hold timer
    order = await transition_order_state(
        order=order,
        target_state=OrderState.INSPECTION_WINDOW,
        trigger_source="SYSTEM_TIMER",
        metadata={"inspection_hours": 48},
        db=db
    )
    return serialize_order(order)

@router.post("/{order_id}/accept", response_model=OrderResponse)
async def accept_inspection(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Buyer confirms die-cast condition during inspection window, releasing funds immediately
    order = await db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.buyer_id != current_user.id and current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Only buyer can accept inspection")

    order = await transition_order_state(
        order=order,
        target_state=OrderState.RELEASED,
        trigger_source="BUYER",
        triggered_by_id=current_user.id,
        metadata={"action": "BUYER_ACCEPTED_INSPECTION"},
        db=db
    )
    return serialize_order(order)

@router.post("/{order_id}/dispute", response_model=OrderResponse)
async def open_dispute(
    order_id: str,
    payload: DisputeOpenRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Freezes payout and marks order as DISPUTED
    order = await db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.buyer_id != current_user.id and current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Only buyer can raise an escrow dispute")

    order = await transition_order_state(
        order=order,
        target_state=OrderState.DISPUTED,
        trigger_source="BUYER",
        triggered_by_id=current_user.id,
        metadata={"reason": payload.reason, "unboxing_video_url": payload.unboxing_video_url},
        db=db
    )
    return serialize_order(order)
