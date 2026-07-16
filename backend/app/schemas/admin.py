from pydantic import BaseModel
from decimal import Decimal

class PlatformStatsResponse(BaseModel):
    total_users: int
    total_merchants: int
    total_revenue: Decimal
    successful_verifications: int
    failed_verifications: int
    pending_callbacks: int