# File: app/api/invoices.py
from fastapi import APIRouter, Depends, HTTPException, status, Header, Response
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
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
from app.models.idempotency import IdempotencyKey
from app.api.deps import get_merchant_from_api_key
from app.core.config import settings

router = APIRouter(prefix="/v1/invoices", tags=["Invoice Service"])

@router.post("", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    invoice_in: InvoiceCreate,
    current_merchant: Merchant = Depends(get_merchant_from_api_key),
    db: AsyncSession = Depends(get_db),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key")
):
    """
    Create a new invoice. Supports idempotent requests to prevent duplicate 
    invoice generation on network retries.
    """
    # 1. Check for an existing Idempotency Key for this merchant
    if idempotency_key:
        stmt = select(IdempotencyKey).where(
            IdempotencyKey.idempotency_key == idempotency_key,
            IdempotencyKey.merchant_id == current_merchant.id
        )
        existing_key = (await db.execute(stmt)).scalars().first()
        
        # If found, short-circuit and return the cached response
        if existing_key:
            return JSONResponse(
                status_code=existing_key.response_status,
                content=existing_key.response_body
            )

    # 2. Standard Invoice Creation Logic
    # Generate a unique secure token for the checkout URL / reference
    invoice_token = secrets.token_urlsafe(16)
    
    new_invoice = Invoice(
        merchant_id=current_merchant.id,
        amount=invoice_in.amount,
        currency=invoice_in.currency,
        description=invoice_in.description,
        token=invoice_token,
        status="PENDING"
    )
    
    db.add(new_invoice)
    await db.commit()
    await db.refresh(new_invoice)
    
    final_invoice = new_invoice

    # Prepare the response data for both the API return and the idempotency cache
    response_data = jsonable_encoder(final_invoice)

    # 3. Save the Idempotency Key on successful creation
    if idempotency_key:
        db_idem_key = IdempotencyKey(
            merchant_id=current_merchant.id,
            idempotency_key=idempotency_key,
            response_status=status.HTTP_201_CREATED,
            response_body=response_data,
            expires_at=datetime.now(timezone.utc) + timedelta(days=1) # Keys expire after 24h
        )
        db.add(db_idem_key)
        await db.commit()

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