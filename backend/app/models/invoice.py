# File: app/models/invoice.py
import enum
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base

class InvoiceStatus(str, enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    FAILED = "failed"

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    merchant_id = Column(Integer, ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    receiver = Column(String, nullable=False)
    callback_url = Column(String, nullable=False)
    token = Column(String, unique=True, index=True, nullable=False)
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.PENDING, nullable=False)
    
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    merchant = relationship("Merchant", backref="invoices")
    metadata_fields = relationship("InvoiceMetadata", back_populates="invoice", cascade="all, delete-orphan")

class InvoiceMetadata(Base):
    __tablename__ = "invoice_metadata"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    key = Column(String, nullable=False)
    value = Column(String, nullable=False)

    # Relationships
    invoice = relationship("Invoice", back_populates="metadata_fields")