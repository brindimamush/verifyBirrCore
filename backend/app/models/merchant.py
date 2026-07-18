from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, BigInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base

class Merchant(Base):
    __tablename__ = "merchants"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    profile = relationship("MerchantProfile", back_populates="merchant", uselist=False, cascade="all, delete-orphan")

class MerchantProfile(Base):
    __tablename__ = "merchant_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    merchant_id = Column(Integer, ForeignKey("merchants.id", ondelete="CASCADE"), unique=True, nullable=False)
    business_name = Column(String, nullable=False)
    business_email = Column(String, unique=True, index=True, nullable=False)
    phone_number = Column(String, nullable=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    telebirr_name = Column(String, nullable=False)
    telebirr_number = Column(String, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    merchant = relationship("Merchant", back_populates="profile")