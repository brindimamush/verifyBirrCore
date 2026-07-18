from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timezone, timedelta
import secrets

from app.db.session import get_db
from app.models.user import User, Role
from app.models.api_key import MerchantApiKey
from app.core.security import get_password_hash
from app.models.merchant import Merchant
from app.models.invoice import Invoice, InvoiceStatus
from app.models.subscription import Subscription, SubscriptionPlan, SubscriptionInvoice, SubscriptionStatus
from app.schemas.subscription import SubscriptionPlanResponse, SubscriptionRequest, SubscriptionCheckoutResponse, SubscriptionResponse
from app.api.deps import get_current_user, require_role
from app.core.config import settings

router = APIRouter(prefix="/v1/subscriptions", tags=["Subscriptions"])

@router.get("/plans", response_model=list[SubscriptionPlanResponse])
async def list_active_plans(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.is_active == True))
    return result.scalars().all()

@router.post("/subscribe", response_model=SubscriptionCheckoutResponse)
async def create_subscription(
    req: SubscriptionRequest,
    current_user: User = Depends(require_role([Role.MERCHANT])),
    db: AsyncSession = Depends(get_db)
):
    # 1. Get current merchant
    merchant_result = await db.execute(select(Merchant).where(Merchant.user_id == current_user.id))
    merchant = merchant_result.scalars().first()
    if not merchant:
        raise HTTPException(status_code=403, detail="Merchant profile required.")

    # 2. Validate requested plan
    plan_result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == req.plan_id))
    plan = plan_result.scalars().first()
    if not plan or not plan.is_active:
        raise HTTPException(status_code=404, detail="Subscription plan not found or inactive.")

    # 3. Create the pending Subscription record
    subscription = Subscription(
        merchant_id=merchant.id,
        plan_id=plan.id,
        status=SubscriptionStatus.PENDING,
        auto_renew=req.auto_renew
    )
    db.add(subscription)
    await db.flush()

    # 4. Generate the Invoice (Platform acting as the merchant)
    secure_token = secrets.token_urlsafe(16)
    verification_url = f"{settings.BASE_VERIFICATION_URL}/{secure_token}"
    
    # The callback points to our internal webhook endpoint
    internal_callback = f"{settings.BASE_API_URL}/v1/subscriptions/internal/webhook"
    
    invoice = Invoice(
        merchant_id=settings.PLATFORM_MERCHANT_ID,
        amount=plan.price,
        receiver="PLATFORM_SYSTEM", 
        callback_url=internal_callback,
        token=secure_token,
        status=InvoiceStatus.PENDING,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.DEFAULT_INVOICE_EXPIRE_MINUTES)
    )
    db.add(invoice)
    await db.flush()

    # 5. Link Invoice to Subscription
    sub_invoice = SubscriptionInvoice(
        subscription_id=subscription.id,
        invoice_id=invoice.id
    )
    db.add(sub_invoice)
    await db.commit()
    await db.refresh(subscription)

    return SubscriptionCheckoutResponse(
        subscription=subscription,
        verification_url=verification_url,
        token=secure_token
    )

@router.post("/internal/webhook", include_in_schema=False)
async def subscription_payment_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Internal endpoint called by the callback_worker.py when a subscription invoice is VERIFIED.
    Requires signature validation in a real production environment.
    """
    payload = await request.json()
    
    if payload.get("status") != "VERIFIED":
        return {"message": "Ignored non-verified status"}

    invoice_id = payload.get("invoice_id")
    
    # Find the linked subscription
    stmt = select(SubscriptionInvoice).where(SubscriptionInvoice.invoice_id == invoice_id)
    result = await db.execute(stmt)
    sub_link = result.scalars().first()
    
    if not sub_link:
        raise HTTPException(status_code=404, detail="Subscription link not found.")

    if sub_link.is_processed:
        return {"status": "Already processed", "message": "Ignored duplicate webhook delivery."}
    # Fetch Subscription and Plan to calculate expiration
    sub_stmt = (select(Subscription).where(Subscription.id == sub_link.subscription_id).with_for_update())
    sub_result = await db.execute(sub_stmt)
    subscription = sub_result.scalars().first()
    
    plan_stmt = select(SubscriptionPlan).where(SubscriptionPlan.id == subscription.plan_id)
    plan = (await db.execute(plan_stmt)).scalars().first()

    # Activate subscription and extend time
    now = datetime.now(timezone.utc)
    subscription.status = SubscriptionStatus.ACTIVE
    
    # If renewing an active subscription, add to the end date. Otherwise, start now.
    if subscription.current_period_end and subscription.current_period_end > now:
        subscription.current_period_end += timedelta(days=plan.duration_days)
    else:
        subscription.current_period_start = now
        subscription.current_period_end = now + timedelta(days=plan.duration_days)

    sub_link.is_processed = True
    existing_key = await db.execute(
        select(MerchantApiKey).where(
            MerchantApiKey.merchant_id == subscription.merchant_id,
            MerchantApiKey.is_revoked == False
        )
    )
    if not existing_key.scalars().first():
        client_id = secrets.token_urlsafe(16)
        secret = secrets.token_urlsafe(32)
        plaintext_key = f"sk_{client_id}_{secret}" # The bot must fetch/display this somewhere securely
        display_prefix = f"sk_{client_id[:4]}...{secret[-4:]}"
        
        db_api_key = MerchantApiKey(
            merchant_id=subscription.merchant_id,
            name=f"Auto-generated for {plan.name}",
            client_id=client_id,
            hashed_secret=get_password_hash(secret),
            prefix=display_prefix
        )
        db.add(db_api_key)
        # Note: You can emit an event or save the plaintext_key to a temporary table
        # so the bot can fetch it immediately after the webhook completes.
    await db.commit()
    return {"status": "Subscription activated successfully"}