from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timezone, timedelta
import secrets

from app.db.session import get_db
from app.models.user import User, Role
from app.models.merchant import Merchant, MerchantProfile
from app.models.subscription import Subscription, SubscriptionPlan, SubscriptionStatus, SubscriptionInvoice
from app.models.invoice import Invoice, InvoiceStatus
from app.schemas.bot import BotMerchantRegisterRequest, BotSubscriptionRequest
from app.schemas.subscription import SubscriptionCheckoutResponse
from app.core.security import get_password_hash
from app.core.config import settings

router = APIRouter(prefix="/v1/bot", tags=["Telegram Bot Integration"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def bot_register_merchant(req: BotMerchantRegisterRequest, db: AsyncSession = Depends(get_db)):
    """Registers a merchant securely via the Telegram bot in a single transaction."""
    
    # Pre-flight checks
    email_check = await db.execute(select(MerchantProfile).where(MerchantProfile.business_email == req.business_email))
    if email_check.scalars().first():
        raise HTTPException(status_code=400, detail="Business email already registered.")

    tg_check = await db.execute(select(MerchantProfile).where(MerchantProfile.telegram_id == req.telegram_id))
    if tg_check.scalars().first():
        raise HTTPException(status_code=400, detail="Telegram ID already registered.")

    # Generate a strong random password since the bot handles auth implicitly
    random_password = secrets.token_urlsafe(32)

    # ACID Transaction Block
    async with db.begin():
        # 1. Create System User
        new_user = User(
            email=req.business_email,
            hashed_password=get_password_hash(random_password),
            role=Role.MERCHANT
        )
        db.add(new_user)
        await db.flush()

        # 2. Create Merchant Link
        new_merchant = Merchant(user_id=new_user.id)
        db.add(new_merchant)
        await db.flush()

        # 3. Create Merchant Profile
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
    
    return {"status": "success", "message": "Merchant registered successfully.", "merchant_id": new_merchant.id}

@router.post("/subscribe", response_model=SubscriptionCheckoutResponse)
async def bot_create_subscription(req: BotSubscriptionRequest, db: AsyncSession = Depends(get_db)):
    """Generates a subscription invoice for a bot-registered merchant, payable to the Admin."""
    
    # 1. Resolve merchant by Telegram ID
    stmt = select(Merchant).join(MerchantProfile).where(MerchantProfile.telegram_id == req.telegram_id)
    merchant = (await db.execute(stmt)).scalars().first()
    
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found. Register first.")

    # 2. Validate requested plan
    plan = (await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == req.plan_id))).scalars().first()
    if not plan or not plan.is_active:
        raise HTTPException(status_code=404, detail="Plan not found or inactive.")

    async with db.begin():
        # 3. Create Subscription
        subscription = Subscription(
            merchant_id=merchant.id,
            plan_id=plan.id,
            status=SubscriptionStatus.PENDING,
            auto_renew=True
        )
        db.add(subscription)
        await db.flush()

        # 4. Generate Invoice (Payable to Admin's Telebirr)
        secure_token = secrets.token_urlsafe(16)
        verification_url = f"{settings.BASE_VERIFICATION_URL}/{secure_token}"
        internal_callback = f"{settings.BASE_API_URL}/v1/subscriptions/internal/webhook"
        
        invoice = Invoice(
            merchant_id=settings.PLATFORM_MERCHANT_ID,
            amount=plan.price,
            receiver=settings.ADMIN_TELEBIRR_NUMBER, # Set to Admin's configured number
            callback_url=internal_callback,
            token=secure_token,
            status=InvoiceStatus.PENDING,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.DEFAULT_INVOICE_EXPIRE_MINUTES)
        )
        db.add(invoice)
        await db.flush()

        # 5. Link Invoice
        sub_invoice = SubscriptionInvoice(subscription_id=subscription.id, invoice_id=invoice.id)
        db.add(sub_invoice)

    return SubscriptionCheckoutResponse(
        subscription=subscription,
        verification_url=verification_url,
        token=secure_token
    )