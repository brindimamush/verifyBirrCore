from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class BotMerchantRegisterRequest(BaseModel):
    telegram_id: int = Field(..., description="The unique Telegram user ID")
    phone_number: str = Field(..., description="Phone number shared via Telegram")
    telebirr_name: str = Field(..., min_length=2, description="Exact name on Telebirr app")
    telebirr_number: str = Field(
        ..., 
        pattern=r"^09\d{8}$", 
        description="Must be strictly 10 digits starting with 09"
    )
    business_name: str = Field(..., min_length=2)
    business_email: EmailStr = Field(...)

class BotSubscriptionRequest(BaseModel):
    telegram_id: int
    plan_id: int