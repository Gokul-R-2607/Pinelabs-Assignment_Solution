from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

class Merchant(Base):
    __tablename__ = "merchants"

    merchant_id = Column(String, primary_key=True, index=True)
    merchant_name = Column(String, index=True)

    transactions = relationship("Transaction", back_populates="merchant")

class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(String, primary_key=True, index=True)
    merchant_id = Column(String, ForeignKey("merchants.merchant_id"))
    amount = Column(Float)
    currency = Column(String)
    status = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    merchant = relationship("Merchant", back_populates="transactions")
    events = relationship("Event", back_populates="transaction")

class Event(Base):
    __tablename__ = "events"

    event_id = Column(String, primary_key=True, index=True)
    event_type = Column(String, index=True)
    transaction_id = Column(String, ForeignKey("transactions.transaction_id"))
    merchant_id = Column(String)
    amount = Column(Float)
    currency = Column(String)
    timestamp = Column(DateTime)

    transaction = relationship("Transaction", back_populates="events")