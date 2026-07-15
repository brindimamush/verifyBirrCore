from pwdlib import PasswordHash
from jose import jwt
from datetime import datetime, timedelta
from app.core.config import settings
import secrets

# Initialize Argon2 password hasher
password_hash = PasswordHash.recommended()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return password_hash.hash(password)

def create_access_token(subject: str | int, role: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject), "role": role}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")

def generate_refresh_token() -> str:
    return secrets.token_urlsafe(32)