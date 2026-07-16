from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class ParsedReceiptData(BaseModel):
    payer_name: Optional[str] = None
    credited_party_name: Optional[str] = None
    credited_party_account: Optional[str] = None
    transaction_status: Optional[str] = None
    invoice_no: Optional[str] = None
    payment_date: Optional[str] = None
    settled_amount: Optional[str] = None
    total_paid_amount: Optional[str] = None

class VerificationRequest(BaseModel):
    token: str
    transaction_id: str
    parser_version: str
    parsed_data: ParsedReceiptData

class VerificationResponse(BaseModel):
    status: str
    reason: Optional[str] = None