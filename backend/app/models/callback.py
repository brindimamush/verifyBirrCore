import enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base

class CallbackStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    EXHAUSTED = "exhausted"

class CallbackJob(Base):
    __tablename__ = "callback_jobs"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    url = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(Enum(CallbackStatus, name="callbackstatus"), default=CallbackStatus.PENDING, nullable=False)
    next_attempt_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    attempt_count = Column(Integer, default=0, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    invoice = relationship("Invoice")
    attempts = relationship("CallbackAttempt", back_populates="job", cascade="all, delete-orphan")

class CallbackAttempt(Base):
    __tablename__ = "callback_attempts"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("callback_jobs.id", ondelete="CASCADE"), nullable=False)
    attempt_number = Column(Integer, nullable=False)
    status_code = Column(Integer, nullable=True)
    response_body = Column(String, nullable=True)
    error_message = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    job = relationship("CallbackJob", back_populates="attempts")