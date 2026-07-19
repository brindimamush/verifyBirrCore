from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timezone, timedelta
import secrets
import uuid

from app.db.session import get_db
from app.models.user import User, Role
from app.models.merchant import Merchant, MerchantProfile
from app.models.subscription import Subscription, SubscriptionPlan, SubscriptionStatus, SubscriptionInvoice
from app.models.invoice import Invoice, InvoiceStatus
from app.models.idempotency import IdempotencyKey
from app.schemas.bot import BotMerchantRegisterRequest, BotSubscriptionRequest
from app.schemas.subscription import SubscriptionCheckoutResponse
from app.core.security import get_password_hash
from app.core.config import settings

router = APIRouter(prefix="/v1/bot", tags=["Telegram Bot Integration"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def bot_register_merchant(
    req: BotMerchantRegisterRequest,
    db: AsyncSession = Depends(get_db),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key")
):
    """Registers a merchant securely via the Telegram bot."""
    
    # 1. Check idempotency first
    if idempotency_key:
        stmt = select(IdempotencyKey).where(
            IdempotencyKey.idempotency_key == idempotency_key
        )
        existing = (await db.execute(stmt)).scalars().first()
        if existing:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=existing.response_status,
                content=existing.response_body
            )

    # 2. Pre-flight checks
    email_check = await db.execute(
        select(MerchantProfile).where(MerchantProfile.business_email == req.business_email)
    )
    if email_check.scalars().first():
        raise HTTPException(status_code=400, detail="Business email already registered.")

    tg_check = await db.execute(
        select(MerchantProfile).where(MerchantProfile.telegram_id == req.telegram_id)
    )
    if tg_check.scalars().first():
        raise HTTPException(status_code=400, detail="Telegram ID already registered.")

    # 3. Generate random password
    random_password = secrets.token_urlsafe(32)

    # 4. Create all records in a single transaction
    try:
        # Create User
        new_user = User(
            email=req.business_email,
            hashed_password=get_password_hash(random_password),
            role=Role.MERCHANT
        )
        db.add(new_user)
        await db.flush()  # Get user.id without committing

        # Create Merchant
        new_merchant = Merchant(user_id=new_user.id)
        db.add(new_merchant)
        await db.flush()  # Get merchant.id without committing

        # Create MerchantProfile
        new_profile = MerchantProfile(
            merchant_id=new_merchant.id,
            business_name=req.business_name,
            business_email=req.business_email,
            phone_number=req.phone_number,
            telegram_id=req.telegram_id,
            telebirr_name=req.telebirr_name,
            telebirr_number=req.telebirr_number
        )
        db.add(new_profile)
        
        # 5. COMMIT everything
        await db.commit()
        await db.refresh(new_merchant)
        
        # Prepare response
        response_data = {
            "status": "success",
            "message": "Merchant registered successfully.",
            "merchant_id": new_merchant.id
        }

        # 6. Save idempotency key
        if idempotency_key:
            # Find merchant_id for idempotency record
            merchant_for_idem = await db.execute(
                select(Merchant).where(Merchant.id == new_merchant.id)
            )
            merchant_obj = merchant_for_idem.scalars().first()
            
            db_idem = IdempotencyKey(
                merchant_id=merchant_obj.id,
                idempotency_key=idempotency_key,
                response_status=201,
                response_body=response_data,
                expires_at=datetime.now(timezone.utc) + timedelta(days=1)
            )
            db.add(db_idem)
            await db.commit()

        return response_data

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@router.post("/subscribe", response_model=SubscriptionCheckoutResponse)
async def bot_create_subscription(
    req: BotSubscriptionRequest,
    db: AsyncSession = Depends(get_db)
):
    """Generates a subscription invoice for a bot-registered merchant."""

    # 1. Resolve merchant by Telegram ID
    stmt = (
        select(Merchant)
        .join(MerchantProfile)
        .where(MerchantProfile.telegram_id == req.telegram_id)
    )
    result = await db.execute(stmt)
    merchant = result.scalars().first()

    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found. Register first.")

    # 2. Validate requested plan
    plan_result = await db.execute(
        select(SubscriptionPlan).where(SubscriptionPlan.id == req.plan_id)
    )
    plan = plan_result.scalars().first()
    if not plan or not plan.is_active:
        raise HTTPException(status_code=404, detail="Plan not found or inactive.")

    try:
        # 3. Create Subscription
        subscription = Subscription(
            merchant_id=merchant.id,
            plan_id=plan.id,
            status=SubscriptionStatus.PENDING,
            auto_renew=True
        )
        db.add(subscription)
        await db.flush()

        # 4. Generate Invoice
        secure_token = secrets.token_urlsafe(16)
        verification_url = f"{settings.BASE_VERIFICATION_URL}/{secure_token}"
        internal_callback = f"{settings.BASE_API_URL}/v1/subscriptions/internal/webhook"

        invoice = Invoice(
            merchant_id=settings.PLATFORM_MERCHANT_ID,
            amount=plan.price,
            receiver=settings.ADMIN_TELEBIRR_NUMBER,
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
        
        # 6. Commit
        await db.commit()
        await db.refresh(subscription)

        return SubscriptionCheckoutResponse(
            subscription=subscription,
            verification_url=verification_url,
            token=secure_token
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Subscription failed: {str(e)}")
    
@router.get("/check-status/{telegram_id}")
async def check_merchant_status(
    telegram_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Check if a merchant is registered by Telegram ID."""
    stmt = select(MerchantProfile).where(
        MerchantProfile.telegram_id == telegram_id
    )
    result = await db.execute(stmt)
    profile = result.scalars().first()
    
    if profile:
        # Also check if merchant is active
        merchant_stmt = select(Merchant).where(
            Merchant.id == profile.merchant_id,
            Merchant.is_active == True
        )
        merchant_result = await db.execute(merchant_stmt)
        merchant = merchant_result.scalars().first()
        
        if merchant:
            return {
                "is_registered": True,
                "merchant_id": merchant.id,
                "business_name": profile.business_name,
                "business_email": profile.business_email
            }
    
    return {
        "is_registered": False,
        "message": "Merchant not found"
    }