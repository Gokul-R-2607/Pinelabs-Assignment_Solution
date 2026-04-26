from sqlalchemy.orm import Session
from . import models, schemas
from sqlalchemy import func
from datetime import datetime

def get_merchant(db: Session, merchant_id: str):
    return db.query(models.Merchant).filter(models.Merchant.merchant_id == merchant_id).first()

def create_merchant(db: Session, merchant: schemas.MerchantBase):
    db_merchant = models.Merchant(merchant_id=merchant.merchant_id, merchant_name=merchant.merchant_name)
    db.add(db_merchant)
    db.commit()
    db.refresh(db_merchant)
    return db_merchant

def get_transaction(db: Session, transaction_id: str):
    return db.query(models.Transaction).filter(models.Transaction.transaction_id == transaction_id).first()

def create_transaction(db: Session, transaction: schemas.TransactionBase):
    db_transaction = models.Transaction(
        transaction_id=transaction.transaction_id,
        merchant_id=transaction.merchant_id,
        amount=transaction.amount,
        currency=transaction.currency,
        status=transaction.status
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

def update_transaction_status(db: Session, transaction_id: str, status: str):
    db.query(models.Transaction).filter(models.Transaction.transaction_id == transaction_id).update({
        "status": status,
        "updated_at": datetime.utcnow()
    })
    db.commit()

def get_event(db: Session, event_id: str):
    return db.query(models.Event).filter(models.Event.event_id == event_id).first()

def create_event(db: Session, event: schemas.EventCreate):
    db_event = models.Event(
        event_id=event.event_id,
        event_type=event.event_type,
        transaction_id=event.transaction_id,
        merchant_id=event.merchant_id,
        amount=event.amount,
        currency=event.currency,
        timestamp=event.timestamp
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

def get_transactions(db: Session, merchant_id: str = None, status: str = None, start_date: datetime = None, 
                     end_date: datetime = None, page: int = 1, size: int = 10, sort_by: str = "created_at", sort_order: str = "desc"):
    query = db.query(models.Transaction)
    if merchant_id:
        query = query.filter(models.Transaction.merchant_id == merchant_id)
    if status:
        query = query.filter(models.Transaction.status == status)
    if start_date:
        query = query.filter(models.Transaction.created_at >= start_date)
    if end_date:
        query = query.filter(models.Transaction.created_at <= end_date)
    
    total = query.count()
    if sort_order == "desc":
        query = query.order_by(getattr(models.Transaction, sort_by).desc())
    else:
        query = query.order_by(getattr(models.Transaction, sort_by).asc())
    
    transactions = query.offset((page - 1) * size).limit(size).all()
    return transactions, total

def get_transaction_detail(db: Session, transaction_id: str):
    return db.query(models.Transaction).filter(models.Transaction.transaction_id == transaction_id).first()

def get_reconciliation_summary(db: Session):
    results = db.query(
        models.Transaction.merchant_id,
        func.date(models.Transaction.created_at).label("date"),
        models.Transaction.status,
        func.count(models.Transaction.transaction_id).label("transaction_count"),
        func.sum(models.Transaction.amount).label("settlement_amount")
    ).group_by(
        models.Transaction.merchant_id,
        func.date(models.Transaction.created_at),
        models.Transaction.status
    ).all()
    
    return [{
        "merchant_id": r[0],
        "date": str(r[1]),
        "status": r[2],
        "transaction_count": r[3],
        "settlement_amount": r[4] or 0
    } for r in results]

def get_discrepancies(db: Session):
    discrepancies = []
    transactions = db.query(models.Transaction).all()
    
    for transaction in transactions:
        events = sorted(transaction.events, key=lambda e: e.timestamp)
        if not events:
            continue
        
        latest_event = events[-1]
        
        # Check if processed but not settled
        if transaction.status == "processed" and not any(e.event_type == "settled" for e in events):
            discrepancies.append({
                "transaction_id": transaction.transaction_id,
                "discrepancy_type": "Unresolved Settlement",
                "discrepancy_details": f"Payment processed but not settled. Latest event: {latest_event.event_type}"
            })
        # Check if settled despite failed attempt
        elif transaction.status == "settled" and any(e.event_type == "payment_failed" for e in events):
            discrepancies.append({
                "transaction_id": transaction.transaction_id,
                "discrepancy_type": "State Inconsistency",
                "discrepancy_details": "Payment marked settled despite failed attempt"
            })
        # Check for duplicate events causing conflicts
        elif len([e for e in events if e.event_type == "payment_initiated"]) > 1:
            discrepancies.append({
                "transaction_id": transaction.transaction_id,
                "discrepancy_type": "Duplicate Events",
                "discrepancy_details": f"Multiple initiation events detected ({len([e for e in events if e.event_type == 'payment_initiated'])} times)"
            })
    
    return discrepancies