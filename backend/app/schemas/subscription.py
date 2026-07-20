from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from app.models.subscription import PlanTier, SubscriptionStatus
from app.schemas.merchant import MerchantResponse
from app.schemas.invoice import InvoiceResponse

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

class SubscriptionWithDetailsResponse(BaseModel):
    id: int
    merchant_id: int
    plan_id: int
    status: SubscriptionStatus
    current_period_start: Optional[datetime]
    current_period_end: Optional[datetime]
    auto_renew: bool
    created_at: datetime
    updated_at: datetime
    
    merchant: Optional[MerchantResponse] = None
    plan: Optional[SubscriptionPlanResponse] = None
    invoices: Optional[List['SubscriptionInvoiceResponse']] = None
    
    class Config:
        from_attributes = True

class SubscriptionInvoiceResponse(BaseModel):
    id: int
    subscription_id: int
    invoice_id: int
    is_processed: bool
    created_at: datetime
    
    subscription: Optional[SubscriptionWithDetailsResponse] = None
    invoice: Optional[InvoiceResponse] = None
    
    class Config:
        from_attributes = True

class PlanRevenueResponse(BaseModel):
    plan_name: str
    tier: PlanTier
    total_revenue: Decimal

class SubscriptionAnalyticsResponse(BaseModel):
    total_active: int
    total_pending: int
    total_expired: int
    total_cancelled: int
    new_this_period: int
    total_revenue: Decimal
    conversion_rate: float
    revenue_by_plan: List[PlanRevenueResponse]
    period_start: datetime
    period_end: datetime

# Forward references
SubscriptionWithDetailsResponse.model_rebuild()
SubscriptionInvoiceResponse.model_rebuild()