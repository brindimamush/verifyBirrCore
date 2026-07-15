from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
import secrets

from app.db.session import get_db
from app.models.user import User, Role
from app.models.merchant import Merchant
from app.models.api_key import MerchantApiKey
from app.schemas.api_key import ApiKeyCreate, ApiKeyResponse, ApiKeyCreateResponse
from app.api.deps import get_current_user, require_role
from app.core.security import get_password_hash

router = APIRouter(prefix="/apikeys", tags=["API Keys"])

@router.post("", response_model=ApiKeyCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    key_in: ApiKeyCreate,
    current_user: User = Depends(require_role([Role.MERCHANT])),
    db: AsyncSession = Depends(get_db)
):
    # Verify merchant profile exists
    result = await db.execute(select(Merchant).where(Merchant.user_id == current_user.id))
    merchant = result.scalars().first()
    if not merchant:
        raise HTTPException(status_code=403, detail="Merchant profile required to generate API keys.")

    # Generate cryptographically secure key parts
    client_id = secrets.token_urlsafe(16)
    secret = secrets.token_urlsafe(32)
    
    plaintext_key = f"sk_{client_id}_{secret}"
    display_prefix = f"sk_{client_id[:4]}...{secret[-4:]}"
    hashed_secret = get_password_hash(secret)

    db_api_key = MerchantApiKey(
        merchant_id=merchant.id,
        name=key_in.name,
        client_id=client_id,
        hashed_secret=hashed_secret,
        prefix=display_prefix,
        expires_at=key_in.expires_at
    )

    db.add(db_api_key)
    await db.commit()
    await db.refresh(db_api_key)

    response_data = ApiKeyCreateResponse.model_validate(db_api_key)
    response_data.plaintext_key = plaintext_key
    
    return response_data

@router.get("", response_model=List[ApiKeyResponse])
async def list_api_keys(
    current_user: User = Depends(require_role([Role.MERCHANT])),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Merchant).where(Merchant.user_id == current_user.id))
    merchant = result.scalars().first()
    if not merchant:
        raise HTTPException(status_code=403, detail="Merchant profile required.")

    keys_result = await db.execute(
        select(MerchantApiKey).where(MerchantApiKey.merchant_id == merchant.id)
    )
    return keys_result.scalars().all()

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    id: int,
    current_user: User = Depends(require_role([Role.MERCHANT])),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Merchant).where(Merchant.user_id == current_user.id))
    merchant = result.scalars().first()
    if not merchant:
        raise HTTPException(status_code=403, detail="Merchant profile required.")

    key_result = await db.execute(
        select(MerchantApiKey).where(
            MerchantApiKey.id == id,
            MerchantApiKey.merchant_id == merchant.id
        )
    )
    db_api_key = key_result.scalars().first()

    if not db_api_key:
        raise HTTPException(status_code=404, detail="API key not found.")

    db_api_key.is_revoked = True
    await db.commit()
    return None