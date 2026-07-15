from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ApiKeyCreate(BaseModel):
    name: str = Field(..., description="An identifier for the key (e.g., 'Production Gateway')")
    expires_at: Optional[datetime] = None

class ApiKeyResponse(BaseModel):
    id: int
    name: str
    prefix: str
    is_revoked: bool
    created_at: datetime
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True

class ApiKeyCreateResponse(ApiKeyResponse):
    plaintext_key: str = Field(..., description="The plaintext API key. Displayed only once.")