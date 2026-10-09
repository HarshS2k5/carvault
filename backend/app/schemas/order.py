# Pydantic schemas for Orders, State Transitions, and Courier Shipping
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.models.order import OrderState

class OrderCreateRequest(BaseModel):
    listing_id: str
    shipping_fee_paise: int = 0

class OrderStateTransitionResponse(BaseModel):
    id: str
    from_state: OrderState
    to_state: OrderState
    trigger_source: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ShippingRecordResponse(BaseModel):
    id: str
    courier_partner: str
    tracking_id: Optional[str]
    status: str
    shipped_at: Optional[datetime]
    delivered_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

class OrderResponse(BaseModel):
    id: str
    listing_id: str
    buyer_id: str
    seller_id: str
    current_state: OrderState
    item_price_paise: int
    item_price_rupees: float
    shipping_fee_paise: int
    commission_rate_bps: int
    commission_paise: int
    commission_rupees: float
    seller_payable_paise: int
    seller_payable_rupees: float
    total_buyer_paid_paise: int
    total_buyer_paid_rupees: float
    gateway_order_id: Optional[str]
    gateway_payment_id: Optional[str]
    inspection_window_ends_at: Optional[datetime]
    created_at: datetime
    shipping: Optional[ShippingRecordResponse] = None
    transitions: List[OrderStateTransitionResponse] = []

    model_config = ConfigDict(from_attributes=True)

class ShipOrderRequest(BaseModel):
    courier_partner: str = "DELHIVERY"
    tracking_id: str = Field(..., min_length=4)
    packing_video_url: Optional[str] = None

class DeliveryConfirmRequest(BaseModel):
    delivery_otp: str = Field(..., min_length=4, max_length=6)

class DisputeOpenRequest(BaseModel):
    reason: str = Field(..., min_length=10, description="Detailed description of issue (fake car, damaged blister, wrong item)")
    unboxing_video_url: Optional[str] = None
