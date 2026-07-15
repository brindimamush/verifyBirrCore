from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timedelta
from app.db.session import get_db
from app.models.user import User, UserSession, RefreshToken
from app.schemas.auth import UserCreate, TokenResponse, UserResponse, RefreshTokenRequest
from app.core.security import get_password_hash, verify_password, create_access_token, generate_refresh_token
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check for existing email
    result = await db.execute(select(User).where(User.email == user_in.email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")
        
    new_user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password)
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

@router.post("/login", response_model=TokenResponse)
async def login(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    # Validate user
    result = await db.execute(select(User).where(User.email == user_in.email))
    user = result.scalars().first()
    
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
        
    # Create Session
    session = UserSession(user_id=user.id)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    
    # Generate Tokens
    access_token = create_access_token(subject=user.id, role=user.role)
    refresh_token_str = generate_refresh_token()
    
    # Store Refresh Token
    db_refresh_token = RefreshToken(
        session_id=session.id,
        token=refresh_token_str,
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    db.add(db_refresh_token)
    await db.commit()
    
    return {"access_token": access_token, "refresh_token": refresh_token_str}

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest, 
    db: AsyncSession = Depends(get_db)
):
    # 1. Find the refresh token in the database
    result = await db.execute(
        select(RefreshToken)
        .where(RefreshToken.token == request.refresh_token)
    )
    db_token = result.scalars().first()

    # 2. Validate token existence, expiration, and revocation status
    if not db_token:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    if db_token.is_revoked:
        raise HTTPException(status_code=401, detail="Refresh token has been revoked")
    if db_token.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Refresh token has expired")

    # 3. Verify the associated session is still active
    session_result = await db.execute(
        select(UserSession).where(UserSession.id == db_token.session_id)
    )
    user_session = session_result.scalars().first()
    
    if not user_session or not user_session.is_active:
        raise HTTPException(status_code=401, detail="Session is no longer active")

    # 4. Get the user for token generation
    user_result = await db.execute(
        select(User).where(User.id == user_session.user_id)
    )
    user = user_result.scalars().first()

    # 5. Token Rotation: Revoke the old refresh token
    db_token.is_revoked = True

    # 6. Generate new tokens
    access_token = create_access_token(subject=user.id, role=user.role)
    new_refresh_token_str = generate_refresh_token()
    
    new_db_refresh_token = RefreshToken(
        session_id=user_session.id,
        token=new_refresh_token_str,
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    
    db.add(new_db_refresh_token)
    await db.commit()

    return {"access_token": access_token, "refresh_token": new_refresh_token_str}

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: RefreshTokenRequest, 
    db: AsyncSession = Depends(get_db)
):
    # Find the token
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token == request.refresh_token)
    )
    db_token = result.scalars().first()

    if db_token:
        # Revoke the specific token
        db_token.is_revoked = True
        
        # Invalidate the entire session to revoke access completely
        session_result = await db.execute(
            select(UserSession).where(UserSession.id == db_token.session_id)
        )
        user_session = session_result.scalars().first()
        if user_session:
            user_session.is_active = False
            
        await db.commit()
        
    return None