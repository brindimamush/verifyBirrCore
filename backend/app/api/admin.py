from fastapi import APIRouter, Header, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from sqlalchemy import update, func, and_, or_, desc
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from app.core.config import settings
from pydantic import BaseModel
import secrets
from decimal import Decimal


from app.db.session import get_db
from app.models.user import User, Role, UserSession, RefreshToken
from app.models.merchant import Merchant
from app.models.idempotency import IdempotencyKey
from app.models.invoice import Invoice, InvoiceStatus
from app.models.verification import VerificationRecord
from app.models.callback import CallbackJob, CallbackStatus
from app.models.subscription import (
    SubscriptionPlan,
    Subscription,
    SubscriptionInvoice,
    SubscriptionStatus)
from app.api.deps import require_role
from app.schemas.auth import UserResponse
from app.schemas.merchant import MerchantResponse
from app.schemas.admin import PlatformStatsResponse
from app.schemas.subscription import (
    SubscriptionPlanResponse,
    SubscriptionPlanCreate, 
    SubscriptionPlanUpdate,
    SubscriptionWithDetailsResponse,
    SubscriptionInvoiceResponse,
    SubscriptionAnalyticsResponse,
    PlanRevenueResponse)

class PaginatedUsersResponse(BaseModel):
    items: List[UserResponse]
    total: int

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
async def list_subscription_plans(
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """List all subscription plans with optional filtering."""
    stmt = select(SubscriptionPlan)
    if not include_inactive:
        stmt = stmt.where(SubscriptionPlan.is_active == True)
    stmt = stmt.order_by(SubscriptionPlan.price.asc())
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/subscription-plans/{id}", response_model=SubscriptionPlanResponse, dependencies=[admin_dependency])
async def get_subscription_plan(id: int, db: AsyncSession = Depends(get_db)):
    """Retrieve a specific subscription plan by ID."""
    plan = await db.get(SubscriptionPlan, id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return plan

@router.post("/subscription-plans", response_model=SubscriptionPlanResponse, status_code=status.HTTP_201_CREATED, dependencies=[admin_dependency])
async def create_subscription_plan(
    plan_in: SubscriptionPlanCreate,
    db: AsyncSession = Depends(get_db),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key")
):
    """
    Create a new subscription plan with idempotency support.
    """
    # Check idempotency
    if idempotency_key:
        stmt = select(IdempotencyKey).where(
            IdempotencyKey.idempotency_key == idempotency_key,
            IdempotencyKey.merchant_id == settings.PLATFORM_MERCHANT_ID  # Admin actions use platform merchant
        )
        existing = (await db.execute(stmt)).scalars().first()
        if existing:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=existing.response_status,
                content=existing.response_body
            )

    # Validate tier uniqueness
    existing = await db.execute(
        select(SubscriptionPlan).where(SubscriptionPlan.tier == plan_in.tier)
    )
    if existing.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="A plan with this tier already exists."
        )

    plan = SubscriptionPlan(**plan_in.model_dump())
    db.add(plan)
    await db.commit()
    await db.refresh(plan)

    response_data = plan.model_dump()

    # Save idempotency key
    if idempotency_key:
        db_idem = IdempotencyKey(
            merchant_id=settings.PLATFORM_MERCHANT_ID,
            idempotency_key=idempotency_key,
            response_status=status.HTTP_201_CREATED,
            response_body=response_data,
            expires_at=datetime.now(timezone.utc) + timedelta(days=1)
        )
        db.add(db_idem)
        await db.commit()

    return plan

@router.patch("/subscription-plans/{id}", response_model=SubscriptionPlanResponse, dependencies=[admin_dependency])
async def update_subscription_plan(
    id: int, 
    plan_in: SubscriptionPlanUpdate, 
    db: AsyncSession = Depends(get_db)
):
    """Edit an existing subscription plan."""
    plan = await db.get(SubscriptionPlan, id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    update_data = plan_in.model_dump(exclude_unset=True)
    
    # Check uniqueness if tier is being updated
    if "tier" in update_data and update_data["tier"] != plan.tier:
        existing = await db.execute(
            select(SubscriptionPlan).where(
                SubscriptionPlan.tier == update_data["tier"],
                SubscriptionPlan.id != id
            )
        )
        if existing.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="A plan with this tier already exists."
            )

    for key, value in update_data.items():
        setattr(plan, key, value)

    await db.commit()
    await db.refresh(plan)
    return plan

# @router.patch("/subscription-plans/{id}/activate", response_model=SubscriptionPlanResponse, dependencies=[admin_dependency])
# async def activate_subscription_plan(id: int, db: AsyncSession = Depends(get_db)):
#     """Activate a subscription plan."""
#     plan = await db.get(SubscriptionPlan, id)
#     if not plan:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    
#     plan.is_active = True
#     await db.commit()
#     await db.refresh(plan)
#     return plan

# @router.patch("/subscription-plans/{id}/deactivate", response_model=SubscriptionPlanResponse, dependencies=[admin_dependency])
# async def deactivate_subscription_plan(id: int, db: AsyncSession = Depends(get_db)):
#     """Deactivate a subscription plan (prevents new signups)."""
#     plan = await db.get(SubscriptionPlan, id)
#     if not plan:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    
#     plan.is_active = False
#     await db.commit()
#     await db.refresh(plan)
#     return plan

@router.patch("/subscription-plans/{id}/toggle-status", response_model=SubscriptionPlanResponse, dependencies=[admin_dependency])
async def toggle_subscription_plan_status(
    id: int, 
    is_active: bool,
    db: AsyncSession = Depends(get_db)
):
    """Activate or deactivate a subscription plan."""
    plan = await db.get(SubscriptionPlan, id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    
    # Check if plan has active subscriptions before deactivation
    if not is_active:
        active_subs = await db.execute(
            select(Subscription).where(
                Subscription.plan_id == id,
                Subscription.status == SubscriptionStatus.ACTIVE
            )
        )
        if active_subs.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate plan with active subscriptions. Cancel or expire them first."
            )
    
    plan.is_active = is_active
    await db.commit()
    await db.refresh(plan)
    return plan

@router.delete("/subscription-plans/{id}", dependencies=[admin_dependency])
async def delete_subscription_plan(id: int, db: AsyncSession = Depends(get_db)):
    """
    Safely delete a subscription plan.
    If it has historical subscriptions, it is merely deactivated.
    """
    plan = await db.get(SubscriptionPlan, id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    # Check for any subscriptions (historical or active)
    linked_subs = await db.execute(
        select(Subscription).where(Subscription.plan_id == id)
    )
    has_history = linked_subs.scalars().first() is not None

    if has_history:
        # Soft delete - deactivate
        plan.is_active = False
        await db.commit()
        return {
            "message": "Plan has associated subscriptions. It was marked inactive instead of deleted.",
            "is_active": False
        }
    else:
        # Hard delete
        await db.delete(plan)
        await db.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)

# ============ Merchant Subscriptions Management ============

@router.get("/subscriptions", response_model=List[SubscriptionWithDetailsResponse], dependencies=[admin_dependency])
async def list_all_subscriptions(
    status: Optional[SubscriptionStatus] = None,
    plan_id: Optional[int] = None,
    merchant_id: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve paginated list of all subscriptions with filtering options.
    """
    stmt = select(Subscription).options(
        selectinload(Subscription.merchant),
        selectinload(Subscription.merchant).selectinload(Merchant.profile),
        selectinload(Subscription.plan)
    )
    
    # Apply filters
    if status:
        stmt = stmt.where(Subscription.status == status)
    if plan_id:
        stmt = stmt.where(Subscription.plan_id == plan_id)
    if merchant_id:
        stmt = stmt.where(Subscription.merchant_id == merchant_id)
    
    stmt = stmt.order_by(desc(Subscription.created_at)).limit(limit).offset(offset)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/subscriptions/{id}", response_model=SubscriptionWithDetailsResponse, dependencies=[admin_dependency])
async def get_subscription_details(id: int, db: AsyncSession = Depends(get_db)):
    """Get detailed information about a specific subscription."""
    stmt = select(Subscription).options(
        selectinload(Subscription.merchant),
        selectinload(Subscription.merchant).selectinload(Merchant.profile),
        selectinload(Subscription.plan),
        selectinload(Subscription.invoices).selectinload(SubscriptionInvoice.invoice)
    ).where(Subscription.id == id)
    
    result = await db.execute(stmt)
    subscription = result.scalars().first()
    
    if not subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    
    return subscription

@router.patch("/subscriptions/{id}/status", response_model=SubscriptionWithDetailsResponse, dependencies=[admin_dependency])
async def update_subscription_status(
    id: int,
    status: SubscriptionStatus,
    db: AsyncSession = Depends(get_db)
):
    """
    Admin endpoint to manually update subscription status.
    Useful for support cases or manual intervention.
    """
    subscription = await db.get(Subscription, id)
    if not subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    
    subscription.status = status
    
    # If activating, set period dates if not set
    if status == SubscriptionStatus.ACTIVE:
        now = datetime.now(timezone.utc)
        if not subscription.current_period_start:
            subscription.current_period_start = now
        if not subscription.current_period_end:
            plan = await db.get(SubscriptionPlan, subscription.plan_id)
            if plan:
                subscription.current_period_end = now + timedelta(days=plan.duration_days)
    
    await db.commit()
    await db.refresh(subscription)
    return subscription

@router.post("/subscriptions/{id}/renew", response_model=SubscriptionWithDetailsResponse, dependencies=[admin_dependency])
async def admin_renew_subscription(
    id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Manually renew a subscription. Creates a new invoice for the renewal.
    """
    subscription = await db.get(Subscription, id)
    if not subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    
    if subscription.status not in [SubscriptionStatus.ACTIVE, SubscriptionStatus.EXPIRED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot renew subscription with status: {subscription.status.value}"
        )
    
    plan = await db.get(SubscriptionPlan, subscription.plan_id)
    if not plan or not plan.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Associated plan is not active or does not exist"
        )
    
    # Create renewal invoice
    secure_token = secrets.token_urlsafe(16)
    invoice = Invoice(
        merchant_id=settings.PLATFORM_MERCHANT_ID,
        amount=plan.price,
        receiver=settings.ADMIN_TELEBIRR_NUMBER,
        callback_url=f"{settings.BASE_API_URL}/v1/subscriptions/internal/webhook",
        token=secure_token,
        status=InvoiceStatus.PENDING,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.DEFAULT_INVOICE_EXPIRE_MINUTES)
    )
    db.add(invoice)
    await db.flush()
    
    # Link to subscription
    sub_invoice = SubscriptionInvoice(
        subscription_id=subscription.id,
        invoice_id=invoice.id
    )
    db.add(sub_invoice)
    
    # Update subscription if it was expired
    if subscription.status == SubscriptionStatus.EXPIRED:
        subscription.status = SubscriptionStatus.PENDING
    
    await db.commit()
    await db.refresh(subscription)
    return subscription

# ============ Subscription Invoices ============

@router.get("/subscription-invoices", response_model=List[SubscriptionInvoiceResponse], dependencies=[admin_dependency])
async def list_subscription_invoices(
    subscription_id: Optional[int] = None,
    is_processed: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    List all subscription invoices with optional filtering.
    """
    stmt = select(SubscriptionInvoice).options(
        selectinload(SubscriptionInvoice.subscription),
        selectinload(SubscriptionInvoice.invoice)
    )
    
    if subscription_id:
        stmt = stmt.where(SubscriptionInvoice.subscription_id == subscription_id)
    if is_processed is not None:
        stmt = stmt.where(SubscriptionInvoice.is_processed == is_processed)
    
    stmt = stmt.order_by(desc(SubscriptionInvoice.created_at)).limit(limit).offset(offset)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/subscription-invoices/{id}", response_model=SubscriptionInvoiceResponse, dependencies=[admin_dependency])
async def get_subscription_invoice(id: int, db: AsyncSession = Depends(get_db)):
    """Get details of a specific subscription invoice."""
    stmt = select(SubscriptionInvoice).options(
        selectinload(SubscriptionInvoice.subscription),
        selectinload(SubscriptionInvoice.invoice)
    ).where(SubscriptionInvoice.id == id)
    
    result = await db.execute(stmt)
    invoice = result.scalars().first()
    
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription invoice not found")
    
    return invoice

# ============ Subscription Analytics ============

@router.get("/subscription-analytics", response_model=SubscriptionAnalyticsResponse, dependencies=[admin_dependency])
async def get_subscription_analytics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive subscription analytics including revenue by plan and key metrics.
    """
    # Set default date range (last 30 days if not specified)
    if not end_date:
        end_date = datetime.now(timezone.utc)
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    # 1. Total subscriptions by status
    status_counts = await db.execute(
        select(
            Subscription.status,
            func.count(Subscription.id).label('count')
        ).group_by(Subscription.status)
    )
    status_counts_dict = {row[0].value: row[1] for row in status_counts.all()}
    
    # 2. Revenue by plan (for VERIFIED invoices in date range)
    revenue_by_plan = await db.execute(
        select(
            SubscriptionPlan.name,
            SubscriptionPlan.tier,
            func.sum(Invoice.amount).label('total_revenue')
        )
        .join(Subscription, Subscription.plan_id == SubscriptionPlan.id)
        .join(SubscriptionInvoice, SubscriptionInvoice.subscription_id == Subscription.id)
        .join(Invoice, Invoice.id == SubscriptionInvoice.invoice_id)
        .where(
            Invoice.status == InvoiceStatus.VERIFIED,
            Invoice.created_at.between(start_date, end_date)
        )
        .group_by(SubscriptionPlan.id, SubscriptionPlan.name, SubscriptionPlan.tier)
        .order_by(func.sum(Invoice.amount).desc())
    )
    
    revenue_plans = [
        PlanRevenueResponse(
            plan_name=row[0],
            tier=row[1],
            total_revenue=row[2] or Decimal('0.00')
        )
        for row in revenue_by_plan.all()
    ]
    
    # 3. Total revenue for the period
    total_revenue = await db.scalar(
        select(func.sum(Invoice.amount))
        .join(SubscriptionInvoice, SubscriptionInvoice.invoice_id == Invoice.id)
        .where(
            Invoice.status == InvoiceStatus.VERIFIED,
            Invoice.created_at.between(start_date, end_date)
        )
    )
    
    # 4. Active subscriptions count
    active_count = await db.scalar(
        select(func.count(Subscription.id))
        .where(Subscription.status == SubscriptionStatus.ACTIVE)
    )
    
    # 5. New subscriptions in period
    new_count = await db.scalar(
        select(func.count(Subscription.id))
        .where(Subscription.created_at.between(start_date, end_date))
    )
    
    # 6. Conversion rate (invoices paid vs created)
    total_invoices = await db.scalar(
        select(func.count(SubscriptionInvoice.id))
        .where(SubscriptionInvoice.created_at.between(start_date, end_date))
    )
    
    paid_invoices = await db.scalar(
        select(func.count(SubscriptionInvoice.id))
        .join(Invoice, Invoice.id == SubscriptionInvoice.invoice_id)
        .where(
            Invoice.status == InvoiceStatus.VERIFIED,
            SubscriptionInvoice.created_at.between(start_date, end_date)
        )
    )
    
    conversion_rate = (paid_invoices / total_invoices * 100) if total_invoices > 0 else 0
    
    return SubscriptionAnalyticsResponse(
        total_active=active_count or 0,
        total_pending=status_counts_dict.get('pending', 0),
        total_expired=status_counts_dict.get('expired', 0),
        total_cancelled=status_counts_dict.get('cancelled', 0),
        new_this_period=new_count or 0,
        total_revenue=total_revenue or Decimal('0.00'),
        conversion_rate=round(conversion_rate, 2),
        revenue_by_plan=revenue_plans,
        period_start=start_date,
        period_end=end_date
    )

@router.get("/users", response_model=PaginatedUsersResponse, dependencies=[admin_dependency])
async def list_all_users(
    page: int = 0, 
    limit: int = 50, 
    search: str = None, 
    db: AsyncSession = Depends(get_db)
):
    """Retrieves a paginated and searchable list of all platform users."""
    # Convert frontend 0-indexed page to database offset
    offset = page * limit
    
    # Base queries
    stmt = select(User)
    count_stmt = select(func.count(User.id))
    
    # Handle the optional search filter if text is provided
    if search:
        # Adjust 'email' or 'username' depending on your actual User model attributes
        search_filter = User.email.ilike(f"%{search}%")
        stmt = stmt.where(search_filter)
        count_stmt = count_stmt.where(search_filter)
        
    # Get total count matching the query
    total_count = await db.scalar(count_stmt)
    
    # Fetch paginated items
    result = await db.execute(stmt.limit(limit).offset(offset))
    users = result.scalars().all()
    
    # Return the exact object structure the frontend expects
    return {
        "items": users,
        "total": total_count or 0
    }

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

@router.get("/merchants", response_model=List[MerchantResponse], dependencies=[admin_dependency])
async def list_all_merchants(limit: int = 50, offset: int = 0, db: AsyncSession = Depends(get_db)):
    """
    Retrieves a paginated list of all system merchants with profiles eagerly loaded.
    """
    stmt = (
        select(Merchant)
        .options(selectinload(Merchant.profile))
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.patch("/merchants/{merchant_id}/status", response_model=MerchantResponse, dependencies=[admin_dependency])
async def toggle_merchant_status(merchant_id: int, is_active: bool, db: AsyncSession = Depends(get_db)):
    """
    Toggles a merchant's active status. 
    Guarantees ACID compliance: If a merchant is deactivated, all linked sessions 
    and refresh tokens are invalidated inside a single atomic transaction block.
    """
    # Enforce atomic transaction boundaries manually
    async with db.begin():
        # 1. Fetch merchant row with pessimistic locking to avoid race conditions
        stmt = (
            select(Merchant)
            .options(selectinload(Merchant.profile))
            .where(Merchant.id == merchant_id)
            .with_for_update()
        )
        result = await db.execute(stmt)
        merchant = result.scalars().first()
        
        if not merchant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Merchant not found")
        
        # 2. Apply status update
        merchant.is_active = is_active
        
        # 3. Cascading Security Invalidation: If deactivated, drop all active auth footprints
        if not is_active:
            user_id = merchant.user_id
            
            # Deactivate all active sessions for the merchant's underlying user
            await db.execute(
                update(UserSession)
                .where(UserSession.user_id == user_id)
                .values(is_active=False)
            )
            
            # Revoke all sub-tier refresh tokens belonging to those sessions
            await db.execute(
                update(RefreshToken)
                .where(
                    RefreshToken.session_id.in_(
                        select(UserSession.id).where(UserSession.user_id == user_id)
                    )
                )
                .values(is_revoked=True)
            )
            
    # Context manager closes 'async with db.begin()', executing an atomic COMMIT or ROLLBACK if an error occurs.
    await db.refresh(merchant)
    return merchant