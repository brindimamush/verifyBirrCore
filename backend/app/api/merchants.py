from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.db.session import get_db
from app.models.user import User, Role
from app.models.merchant import Merchant, MerchantProfile
from app.schemas.merchant import MerchantCreate, MerchantUpdate, MerchantResponse
from app.api.deps import get_current_user, require_role

router = APIRouter(prefix="/merchants", tags=["Merchants"])

@router.post("", response_model=MerchantResponse, status_code=status.HTTP_201_CREATED)
async def create_merchant(
    merchant_in: MerchantCreate,
    current_user: User = Depends(require_role([Role.MERCHANT, Role.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    # Enforce ownership validation: Ensure one merchant profile per user
    result = await db.execute(select(Merchant).where(Merchant.user_id == current_user.id))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Merchant profile already exists for this user")

    # Validate business email uniqueness
    email_check = await db.execute(
        select(MerchantProfile).where(MerchantProfile.business_email == merchant_in.business_email)
    )
    if email_check.scalars().first():
        raise HTTPException(status_code=400, detail="Business email already registered")

    # Create Merchant
    new_merchant = Merchant(user_id=current_user.id)
    db.add(new_merchant)
    await db.flush() # Flush to generate the merchant ID

    # Create associated Merchant Profile
    new_profile = MerchantProfile(
        merchant_id=new_merchant.id,
        business_name=merchant_in.business_name,
        business_email=merchant_in.business_email,
        phone_number=merchant_in.phone_number
    )
    db.add(new_profile)
    await db.commit()
    
    # Fetch final data with eager loaded profile
    stmt = select(Merchant).options(selectinload(Merchant.profile)).where(Merchant.id == new_merchant.id)
    final_result = await db.execute(stmt)
    return final_result.scalars().first()


@router.get("/me", response_model=MerchantResponse)
async def get_my_merchant(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Merchant).options(selectinload(Merchant.profile)).where(Merchant.user_id == current_user.id)
    result = await db.execute(stmt)
    merchant = result.scalars().first()
    
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant profile not found")
        
    return merchant


@router.patch("/me", response_model=MerchantResponse)
async def update_my_merchant(
    update_data: MerchantUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Merchant).options(selectinload(Merchant.profile)).where(Merchant.user_id == current_user.id)
    result = await db.execute(stmt)
    merchant = result.scalars().first()
    
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant profile not found")

    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(merchant.profile, key, value)
        
    await db.commit()
    
    # Refresh to return updated timestamps
    stmt = select(Merchant).options(selectinload(Merchant.profile)).where(Merchant.id == merchant.id)
    updated_result = await db.execute(stmt)
    return updated_result.scalars().first()


@router.get("/{id}", response_model=MerchantResponse)
async def get_merchant(
    id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Merchant).options(selectinload(Merchant.profile)).where(Merchant.id == id)
    result = await db.execute(stmt)
    merchant = result.scalars().first()
    
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")
        
    return merchant