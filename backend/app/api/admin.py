from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from sqlalchemy import update
from typing import List

from app.db.session import get_db
from app.models.user import User, Role, UserSession, RefreshToken
from app.models.merchant import Merchant
from app.models.invoice import Invoice, InvoiceStatus
from app.models.verification import VerificationRecord
from app.models.callback import CallbackJob, CallbackStatus
from app.models.subscription import SubscriptionPlan, Subscription
from app.api.deps import require_role
from app.schemas.auth import UserResponse
from app.schemas.admin import PlatformStatsResponse
from app.schemas.subscription import SubscriptionPlanResponse, SubscriptionPlanCreate, SubscriptionPlanUpdate

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

@router.get("/subscription-plans", response_model=List[SubscriptionPlanResponse], dependencies=[admin_dependency])
async def list_subscription_plans(db: AsyncSession = Depends(get_db)):
    """List all subscription plans, including inactive ones."""
    result = await db.execute(select(SubscriptionPlan))
    return result.scalars().all()

@router.get("/subscription-plans/{id}", response_model=SubscriptionPlanResponse, dependencies=[admin_dependency])
async def get_subscription_plan(id: int, db: AsyncSession = Depends(get_db)):
    """Retrieve a specific subscription plan by ID."""
    plan = await db.get(SubscriptionPlan, id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return plan

@router.post("/subscription-plans", response_model=SubscriptionPlanResponse, status_code=status.HTTP_201_CREATED, dependencies=[admin_dependency])
async def create_subscription_plan(plan_in: SubscriptionPlanCreate, db: AsyncSession = Depends(get_db)):
    """Create a new subscription plan."""
    # Enforce the unique constraint on 'tier'
    existing = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.tier == plan_in.tier))
    if existing.scalars().first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A plan with this tier already exists.")

    plan = SubscriptionPlan(**plan_in.model_dump())
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return plan

@router.patch("/subscription-plans/{id}", response_model=SubscriptionPlanResponse, dependencies=[admin_dependency])
async def update_subscription_plan(id: int, plan_in: SubscriptionPlanUpdate, db: AsyncSession = Depends(get_db)):
    """Edit an existing subscription plan."""
    plan = await db.get(SubscriptionPlan, id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    update_data = plan_in.model_dump(exclude_unset=True)
    
    # Check uniqueness if tier is being updated
    if "tier" in update_data and update_data["tier"] != plan.tier:
        existing = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.tier == update_data["tier"]))
        if existing.scalars().first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A plan with this tier already exists.")

    for key, value in update_data.items():
        setattr(plan, key, value)

    await db.commit()
    await db.refresh(plan)
    return plan

@router.patch("/subscription-plans/{id}/activate", response_model=SubscriptionPlanResponse, dependencies=[admin_dependency])
async def activate_subscription_plan(id: int, db: AsyncSession = Depends(get_db)):
    """Activate a subscription plan."""
    plan = await db.get(SubscriptionPlan, id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    
    plan.is_active = True
    await db.commit()
    await db.refresh(plan)
    return plan

@router.patch("/subscription-plans/{id}/deactivate", response_model=SubscriptionPlanResponse, dependencies=[admin_dependency])
async def deactivate_subscription_plan(id: int, db: AsyncSession = Depends(get_db)):
    """Deactivate a subscription plan (prevents new signups)."""
    plan = await db.get(SubscriptionPlan, id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    
    plan.is_active = False
    await db.commit()
    await db.refresh(plan)
    return plan

@router.delete("/subscription-plans/{id}", dependencies=[admin_dependency])
async def delete_subscription_plan(id: int, db: AsyncSession = Depends(get_db)):
    """
    Safely delete a subscription plan.
    If it has historical subscriptions, it is merely deactivated to preserve referential integrity.
    """
    plan = await db.get(SubscriptionPlan, id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    # Check for linked subscriptions
    linked_subs = await db.execute(select(Subscription).where(Subscription.plan_id == id))
    has_active_history = linked_subs.scalars().first() is not None

    if has_active_history:
        # Soft delete / Deactivate
        plan.is_active = False
        await db.commit()
        return {"message": "Plan has associated subscriptions. It was marked inactive instead of deleted.", "is_active": False}
    else:
        # Safe to hard delete
        await db.delete(plan)
        await db.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.get("/users", response_model=List[UserResponse], dependencies=[admin_dependency])
async def list_all_users(limit: int = 50, offset: int = 0, db: AsyncSession = Depends(get_db)):
    """Retrieves a paginated list of all platform users."""
    result = await db.execute(select(User).limit(limit).offset(offset))
    return result.scalars().all()

@router.patch("/users/{user_id}/status", response_model=UserResponse, dependencies=[admin_dependency])
async def toggle_user_status(user_id: int, is_active: bool, db: AsyncSession = Depends(get_db)):
    """Allows administrators to activate or deactivate a user account."""
    async with db.begin():
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        user.is_active = is_active
        
        # If disabling the user, forcefully invalidate all active sessions
        if not is_active:
            # 1. Deactivate sessions
            await db.execute(
                update(UserSession)
                .where(UserSession.user_id == user_id)
                .values(is_active=False)
            )
            
            # 2. Revoke associated refresh tokens by joining through UserSession
            await db.execute(
                update(RefreshToken)
                .where(
                    RefreshToken.session_id.in_(
                        select(UserSession.id).where(UserSession.user_id == user_id)
                    )
                )
                .values(is_revoked=True)
            )
            
    await db.refresh(user)
    return user