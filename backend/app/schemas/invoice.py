# File: app/schemas/invoice.py
from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator
from typing import Optional, Dict
from datetime import datetime
from decimal import Decimal
from app.models.invoice import InvoiceStatus

class InvoiceCreate(BaseModel):
    amount: Decimal = Field(..., gt=0, max_digits=12, decimal_places=2, description="Expected transaction value")
    receiver: str = Field(..., min_length=2, max_length=100, description="Receiver identifier (phone/name)")
    callback_url: HttpUrl = Field(..., description="Webhook notification destination")
    expires_in_minutes: Optional[int] = Field(None, gt=5, le=10080, description="Expiry duration override")
    metadata: Dict[str, str] = Field(default_factory=dict, description="Custom parameters to associate")

    @field_validator('callback_url')
    def transform_url_to_str(cls, v):
        return str(v)

class InvoiceMetadataResponse(BaseModel):
    key: str
    value: str

    class Config:
        from_attributes = True

class InvoiceResponse(BaseModel):
    id: int
    merchant_id: int
    amount: Decimal
    receiver: str
    callback_url: str
    token: str
    status: InvoiceStatus
    verification_url: str
    expires_at: datetime
    created_at: datetime
    metadata: Dict[str, str] = Field(default_factory=dict)

    class Config:
        from_attributes = True

    @model_validator(mode='before')
    def structural_flatten(cls, data):
        # Flatten metadata rows into standard dictionary format dynamically
        if hasattr(data, "metadata_fields") and data.metadata_fields:
            data.metadata = {item.key: item.value for item in data.metadata_fields}
        elif isinstance(data, dict) and "metadata_fields" in data:
            data["metadata"] = {item["key"]: item["value"] for item in data["metadata_fields"]}
        return data

class PublicInvoiceLookup(BaseModel):
    amount: Decimal
    receiver: str
    token: str
    status: InvoiceStatus
    expires_at: datetime
    is_expired: bool

    class Config:
        from_attributes = True