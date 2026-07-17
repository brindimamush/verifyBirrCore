from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base
from sqlalchemy import Index

class VerificationRecord(Base):
    __tablename__ = "verification_records"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True)
    transaction_id = Column(String, index=True, nullable=False)
    is_successful = Column(Boolean, nullable=False)
    reason = Column(String, nullable=True)
    raw_data = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    invoice = relationship("Invoice")
    __table_args__ = (
        Index(
            'ix_unique_successful_transaction', 
            'transaction_id', 
            unique=True, 
            postgresql_where=(is_successful == True)
        ),
    )