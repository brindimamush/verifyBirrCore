from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal
from app.models.subscription import PlanTier, SubscriptionStatus

class SubscriptionPlanResponse(BaseModel):
    id: int
    tier: PlanTier
    name: str
    price: Decimal
    duration_days: int
    is_active: bool

    class Config:
        from_attributes = True

class SubscriptionRequest(BaseModel):
    plan_id: int
    auto_renew: bool = True

class SubscriptionResponse(BaseModel):
    id: int
    merchant_id: int
    plan_id: int
    status: SubscriptionStatus
    current_period_start: Optional[datetime]
    current_period_end: Optional[datetime]
    auto_renew: bool
    
    class Config:
        from_attributes = True

class SubscriptionCheckoutResponse(BaseModel):
    subscription: SubscriptionResponse
    verification_url: str
    token: str

class SubscriptionPlanCreate(BaseModel):
    tier: PlanTier
    name: str
    price: Decimal = Field(..., ge=0, decimal_places=2)
    duration_days: int = Field(..., gt=0)
    is_active: bool = True

class SubscriptionPlanUpdate(BaseModel):
    tier: Optional[PlanTier] = None
    name: Optional[str] = None
    price: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    duration_days: Optional[int] = Field(None, gt=0)