from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base

class MerchantApiKey(Base):
    __tablename__ = "merchant_api_keys"

    id = Column(Integer, primary_key=True, index=True)
    merchant_id = Column(Integer, ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    client_id = Column(String, unique=True, index=True, nullable=False)
    hashed_secret = Column(String, nullable=False)
    prefix = Column(String, nullable=False) 
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Add relationship to merchant
    merchant = relationship("Merchant", backref="api_keys")