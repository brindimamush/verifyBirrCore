# File: app/api/invoices.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone, timedelta
import secrets
from typing import List

from app.db.session import get_db
from app.models.merchant import Merchant
from app.models.invoice import Invoice, InvoiceMetadata, InvoiceStatus
from app.schemas.invoice import InvoiceCreate, InvoiceResponse, PublicInvoiceLookup
from app.api.deps import get_merchant_from_api_key
from app.core.config import settings

router = APIRouter(prefix="/v1/invoices", tags=["Invoice Service"])

@router.post("", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    invoice_in: InvoiceCreate,
    current_merchant: Merchant = Depends(get_merchant_from_api_key),
    db: AsyncSession = Depends(get_db)
):
    # Calculate explicit expiration time window
    expiry_minutes = invoice_in.expires_in_minutes or settings.DEFAULT_INVOICE_EXPIRE_MINUTES
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=expiry_minutes)

    # Generate non-guessable secure URL tokens safely decoupling primary database sequences
    secure_token = secrets.token_urlsafe(16)
    verification_url = f"{settings.BASE_VERIFICATION_URL}/{secure_token}"

    db_invoice = Invoice(
        merchant_id=current_merchant.id,
        amount=invoice_in.amount,
        receiver=invoice_in.receiver,
        callback_url=invoice_in.callback_url,
        token=secure_token,
        status=InvoiceStatus.PENDING,
        expires_at=expires_at
    )
    db.add(db_invoice)
    await db.flush()  # Extract structural model IDs securely

    # Map transaction metadata dynamically
    if invoice_in.metadata:
        metadata_records = [
            InvoiceMetadata(invoice_id=db_invoice.id, key=k, value=str(v))
            for k, v in invoice_in.metadata.items()
        ]
        db.add_all(metadata_records)

    await db.commit()

    # Eager load relationships for response schema serialization parsing
    stmt = (
        select(Invoice)
        .options(selectinload(Invoice.metadata_fields))
        .where(Invoice.id == db_invoice.id)
    )
    result = await db.execute(stmt)
    final_invoice = result.scalars().first()
    
    # Attach tracking values dynamically onto database model attributes
    final_invoice.verification_url = verification_url
    return final_invoice

@router.get("/{id}", response_model=InvoiceResponse)
async def get_invoice_by_id(
    id: int,
    current_merchant: Merchant = Depends(get_merchant_from_api_key),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Invoice)
        .options(selectinload(Invoice.metadata_fields))
        .where(Invoice.id == id, Invoice.merchant_id == current_merchant.id)
    )
    result = await db.execute(stmt)
    invoice = result.scalars().first()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice resource not found under merchant namespace")

    # Evaluate live expiration status windows inline during execution
    if invoice.status == InvoiceStatus.PENDING and invoice.expires_at < datetime.now(timezone.utc):
        invoice.status = InvoiceStatus.EXPIRED
        await db.commit()

    invoice.verification_url = f"{settings.BASE_VERIFICATION_URL}/{invoice.token}"
    return invoice

@router.get("/token/{token}", response_model=PublicInvoiceLookup)
async def get_invoice_by_public_token(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    # Fully public lookup used by client automation; exposes no sensitive database mapping identifiers
    stmt = select(Invoice).where(Invoice.token == token)
    result = await db.execute(stmt)
    invoice = result.scalars().first()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invalid payment verification token parameter")

    # Process and record expiration on execution hits
    is_expired = invoice.expires_at < datetime.now(timezone.utc)
    if invoice.status == InvoiceStatus.PENDING and is_expired:
        invoice.status = InvoiceStatus.EXPIRED
        await db.commit()

    return PublicInvoiceLookup(
        amount=invoice.amount,
        receiver=invoice.receiver,
        token=invoice.token,
        status=invoice.status,
        expires_at=invoice.expires_at,
        is_expired=is_expired
    )