from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

class EventBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    event_id: str
    event_type: str
    transaction_id: str
    merchant_id: str
    amount: float
    currency: str
    timestamp: datetime

class MerchantBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    merchant_id: str
    merchant_name: str

class TransactionBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    transaction_id: str
    merchant_id: str
    amount: float
    currency: str
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class TransactionDetail(TransactionBase):
    merchant: MerchantBase
    events: List[EventBase]

class EventCreate(BaseModel):
    event_id: str
    event_type: str
    transaction_id: str
    merchant_id: str
    merchant_name: str
    amount: float
    currency: str
    timestamp: datetime

class TransactionList(BaseModel):
    transactions: List[TransactionBase]
    total: int
    page: int
    size: int

class ReconciliationSummary(BaseModel):
    merchant_id: str
    date: str
    status: str
    transaction_count: int
    settlement_amount: float

class Discrepancy(BaseModel):
    transaction_id: str
    discrepancy_type: str
    discrepancy_details: str

# Backward compatibility aliases
SettlementLogCreate = EventCreate
PartnerBase = MerchantBase
PaymentBase = TransactionBase
PaymentDetail = TransactionDetail
SettlementLogBase = EventBase
PaymentList = TransactionList
ReconciliationReport = ReconciliationSummary
PaymentAnomalies = Discrepancy