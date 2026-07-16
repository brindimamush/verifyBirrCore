from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from typing import List

from app.db.session import get_db
from app.models.user import User, Role
from app.models.merchant import Merchant
from app.models.invoice import Invoice, InvoiceStatus
from app.models.verification import VerificationRecord
from app.models.callback import CallbackJob, CallbackStatus
from app.api.deps import require_role
from app.schemas.auth import UserResponse
from app.schemas.admin import PlatformStatsResponse

router = APIRouter(prefix="/v1/admin", tags=["Admin Dashboard"])

# Secure the entire router by requiring the ADMIN role
admin_dependency = Depends(require_role([Role.ADMIN]))

@router.get("/stats", response_model=PlatformStatsResponse, dependencies=[admin_dependency])
async def get_platform_stats(db: AsyncSession = Depends(get_db)):
    """
    Returns aggregated platform data including total revenue, active merchants, 
    and verification health metrics.
    """
    # 1. Total Users
    users_count = await db.scalar(select(func.count(User.id)))
    
    # 2. Total Merchants
    merchants_count = await db.scalar(select(func.count(Merchant.id)))
    
    # 3. Total Revenue (Calculated from VERIFIED invoices only)
    revenue = await db.scalar(
        select(func.sum(Invoice.amount))
        .where(Invoice.status == InvoiceStatus.VERIFIED)
    )
    
    # 4. Verifications (Successful vs Failed)
    success_verifs = await db.scalar(
        select(func.count(VerificationRecord.id))
        .where(VerificationRecord.is_successful == True)
    )
    failed_verifs = await db.scalar(
        select(func.count(VerificationRecord.id))
        .where(VerificationRecord.is_successful == False)
    )
    
    # 5. Pending Callbacks (Queue depth monitoring)
    pending_callbacks = await db.scalar(
        select(func.count(CallbackJob.id))
        .where(CallbackJob.status == CallbackStatus.PENDING)
    )
    
    return PlatformStatsResponse(
        total_users=users_count or 0,
        total_merchants=merchants_count or 0,
        total_revenue=revenue or 0,
        successful_verifications=success_verifs or 0,
        failed_verifications=failed_verifs or 0,
        pending_callbacks=pending_callbacks or 0
    )

@router.get("/users", response_model=List[UserResponse], dependencies=[admin_dependency])
async def list_all_users(limit: int = 50, offset: int = 0, db: AsyncSession = Depends(get_db)):
    """Retrieves a paginated list of all platform users."""
    result = await db.execute(select(User).limit(limit).offset(offset))
    return result.scalars().all()

@router.patch("/users/{user_id}/status", response_model=UserResponse, dependencies=[admin_dependency])
async def toggle_user_status(user_id: int, is_active: bool, db: AsyncSession = Depends(get_db)):
    """Allows administrators to activate or deactivate a user account."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    user.is_active = is_active
    await db.commit()
    await db.refresh(user)
    
    return user