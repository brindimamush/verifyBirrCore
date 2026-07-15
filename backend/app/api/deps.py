from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from jose import jwt, JWTError
from app.db.session import get_db
from app.models.user import User, Role
from app.models.api_key import MerchantApiKey
from app.models.merchant import Merchant
from app.core.config import settings
from app.core.security import verify_password

from datetime import datetime, timezone

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_merchant_from_api_key(
    api_key: str = Depends(api_key_header),
    db: AsyncSession = Depends(get_db)
) -> Merchant:
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API Key header (X-API-Key)")

    try:
        parts = api_key.split("_")
        if len(parts) != 3 or parts[0] != "sk":
            raise ValueError()
        client_id = parts[1]
        secret = parts[2]
    except (ValueError, IndexError):
        raise HTTPException(status_code=401, detail="Invalid API Key format")

    result = await db.execute(select(MerchantApiKey).where(MerchantApiKey.client_id == client_id))
    db_key = result.scalars().first()

    if not db_key:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    if db_key.is_revoked:
        raise HTTPException(status_code=401, detail="API Key has been revoked")

    if db_key.expires_at and db_key.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
        raise HTTPException(status_code=401, detail="API Key has expired")

    if not verify_password(secret, db_key.hashed_secret):
        raise HTTPException(status_code=401, detail="Invalid API Key credentials")

    merchant_result = await db.execute(select(Merchant).where(Merchant.id == db_key.merchant_id))
    merchant = merchant_result.scalars().first()

    if not merchant or not merchant.is_active:
        raise HTTPException(status_code=401, detail="Inactive or missing merchant account")

    return merchant

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalars().first()
    
    if user is None or not user.is_active:
        raise credentials_exception
        
    return user

def require_role(allowed_roles: list[Role]):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action"
            )
        return current_user
    return role_checker