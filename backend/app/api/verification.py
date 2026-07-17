from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import re

from app.db.session import get_db
from app.models.invoice import Invoice, InvoiceStatus
from app.models.verification import VerificationRecord
from app.schemas.verification import VerificationRequest, VerificationResponse
from app.models.callback import CallbackJob
import structlog

router = APIRouter(tags=["Verification Engine"])
logger = structlog.get_logger()

@router.post("/verify", response_model=VerificationResponse, status_code=status.HTTP_200_OK)
async def verify_payment(
    request: VerificationRequest, 
    db: AsyncSession = Depends(get_db)
):
    # Helper to instantly terminate, log, and respond
    async def fail_verification(reason: str, invoice_id: int | None = None) -> VerificationResponse:
        logger.info("verification_failed", transaction_id=request.transaction_id, reason=reason)
        record = VerificationRecord(
            invoice_id=invoice_id,
            transaction_id=request.transaction_id,
            is_successful=False,
            reason=reason,
            raw_data=request.parsed_data.model_dump()
        )
        db.add(record)
        await db.commit()
        return VerificationResponse(status="Failed", reason=reason)

    async with db.begin():
    # 1. Validate token & 2. Validate invoice exists
        stmt = (select(Invoice).options(selectinload(Invoice.merchant)).where(Invoice.token == request.token).with_for_update())
        invoice = (await db.execute(stmt)).scalars().first()
    
    if not invoice:
        return await fail_verification("Invalid token or invoice not found.")

    # 3. Validate invoice status
    if invoice.status != InvoiceStatus.PENDING:
        return await fail_verification(f"Invoice is not pending (Current: {invoice.status.value}).", invoice.id)

    # 4. Validate expiration
    if invoice.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
        invoice.status = InvoiceStatus.EXPIRED
        await db.commit()
        return await fail_verification("Invoice has expired.", invoice.id)

    # 5. Validate merchant status
    if not invoice.merchant.is_active:
        return await fail_verification("Associated merchant account is inactive.", invoice.id)

    # 6. Validate TXN ID uniqueness (Anti-replay constraint)
    txn_stmt = select(VerificationRecord).where(
        VerificationRecord.transaction_id == request.transaction_id,
        VerificationRecord.is_successful == True
    )
    existing_txn = (await db.execute(txn_stmt)).scalars().first()
    
    if existing_txn:
        return await fail_verification("Transaction ID has already been utilized.", invoice.id)

    # 7. Validate amount
    amount_str = request.parsed_data.settled_amount or request.parsed_data.total_paid_amount
    if not amount_str:
        return await fail_verification("Missing amount in parsed receipt data.", invoice.id)

    # Clean the string (e.g., "150.75 ETB" -> "150.75")
    amount_match = re.search(r"[\d,]+\.?\d*", amount_str)
    if not amount_match:
        return await fail_verification(f"Failed to parse numerical amount from: {amount_str}", invoice.id)
        
    try:
        parsed_amount = Decimal(amount_match.group(0).replace(",", ""))
    except InvalidOperation:
        return await fail_verification("Invalid amount format detected.", invoice.id)

    if parsed_amount != invoice.amount:
        return await fail_verification(f"Amount mismatch. Expected {invoice.amount}, got {parsed_amount}.", invoice.id)

    # 8. Validate receiver
    parsed_receiver = request.parsed_data.credited_party_account or request.parsed_data.credited_party_name or ""
    if not parsed_receiver:
        return await fail_verification("Receiver details missing from receipt.", invoice.id)

    expected_clean = re.sub(r'\D', '', invoice.receiver)
    parsed_clean = re.sub(r'\D', '', parsed_receiver)

    # Check for direct numerical inclusion (e.g., 911... in 251911...) or name substring
    receiver_matched = (
        (expected_clean and expected_clean in parsed_clean) or
        (invoice.receiver.lower() in parsed_receiver.lower())
    )

    if not receiver_matched:
        return await fail_verification(f"Receiver mismatch. Expected {invoice.receiver}.", invoice.id)

    # 9. Validate payment status
    tx_status = (request.parsed_data.transaction_status or "").lower()
    if "completed" not in tx_status and "success" not in tx_status:
        return await fail_verification(f"Transaction not completed. Status: {tx_status}", invoice.id)

    # 10. Store verification result & Update Invoice
    invoice.status = InvoiceStatus.VERIFIED

    # Generate a stable event identifier using the invoice token and txn ID
    stable_event_id = f"evt_{invoice.token}_{request.transaction_id}"
    
    success_record = VerificationRecord(
        invoice_id=invoice.id,
        transaction_id=request.transaction_id,
        is_successful=True,
        reason="Verification passed.",
        raw_data=request.parsed_data.model_dump()
    )
    db.add(success_record)
    callback_payload = {
        "event_id": stable_event_id,
        "invoice_id": invoice.id,
        "token": invoice.token,
        "amount": float(invoice.amount),
        "transaction_id": request.transaction_id,
        "status": "VERIFIED",
        "metadata": {m.key: m.value for m in invoice.metadata_fields} if hasattr(invoice, 'metadata_fields') else {}
        }

    callback_job = CallbackJob(
        invoice_id=invoice.id,
        url=invoice.callback_url,
        payload=callback_payload
    )
    db.add(callback_job)
    await db.commit()

    logger.info("verification_success", transaction_id=request.transaction_id, invoice_id=invoice.id)
    
    return VerificationResponse(status="Verified", reason=None)

