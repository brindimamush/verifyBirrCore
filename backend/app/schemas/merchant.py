from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class MerchantProfileBase(BaseModel):
    business_name: str
    business_email: EmailStr
    phone_number: Optional[str] = None

class MerchantCreate(MerchantProfileBase):
    pass

class MerchantUpdate(BaseModel):
    business_name: Optional[str] = None
    business_email: Optional[EmailStr] = None
    phone_number: Optional[str] = None

class MerchantProfileResponse(MerchantProfileBase):
    id: int
    updated_at: datetime

    class Config:
        from_attributes = True

class MerchantResponse(BaseModel):
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    profile: Optional[MerchantProfileResponse] = None

    class Config:
        from_attributes = True