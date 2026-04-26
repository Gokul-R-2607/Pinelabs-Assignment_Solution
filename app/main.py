from fastapi import FastAPI, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from . import crud, models, schemas, database
from typing import List, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Pine Labs Payment Reconciliation", version="2.0.0")

# Middleware to handle ngrok browser warning bypass
@app.middleware("http")
async def skip_ngrok_warning(request: Request, call_next):
    """Add ngrok-skip-browser-warning header to bypass ngrok browser warning page"""
    response = await call_next(request)
    response.headers["ngrok-skip-browser-warning"] = "69420"
    return response

@app.on_event("startup")
def init_db():
    try:
        database.Base.metadata.create_all(bind=database.engine)
        logger.info("DB initialized")
    except Exception as e:
        logger.error(f"DB init failed: {e}")

@app.post("/events", response_model=schemas.EventBase)
def ingest_event(event: schemas.EventCreate, db: Session = Depends(database.get_db)):
    if crud.get_event(db, event.event_id):
        logger.info(f"Event {event.event_id} already exists")
        return schemas.EventBase.model_validate(crud.get_event(db, event.event_id))
    
    merchant = crud.get_merchant(db, event.merchant_id)
    if not merchant:
        merchant = crud.create_merchant(db, schemas.MerchantBase(
            merchant_id=event.merchant_id,
            merchant_name=event.merchant_name
        ))
    
    transaction = crud.get_transaction(db, event.transaction_id)
    if not transaction:
        transaction = crud.create_transaction(db, schemas.TransactionBase(
            transaction_id=event.transaction_id,
            merchant_id=event.merchant_id,
            amount=event.amount,
            currency=event.currency,
            status="initiated",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        ))
    
    db_event = crud.create_event(db, event)
    
    if event.event_type == "payment_processed":
        crud.update_transaction_status(db, event.transaction_id, "processed")
    elif event.event_type == "payment_failed":
        crud.update_transaction_status(db, event.transaction_id, "failed")
    elif event.event_type == "settled":
        crud.update_transaction_status(db, event.transaction_id, "settled")
    
    return schemas.EventBase.model_validate(db_event)

@app.get("/transactions", response_model=schemas.TransactionList)
def list_transactions(
    merchant_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    sort_by: str = Query("created_at", regex="^(created_at|updated_at|amount)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(database.get_db)
):
    transactions, total = crud.get_transactions(db, merchant_id, status, start_date, end_date, page, size, sort_by, sort_order)
    return schemas.TransactionList(
        transactions=[schemas.TransactionBase.model_validate(t) for t in transactions],
        total=total,
        page=page,
        size=size
    )

@app.get("/transactions/{transaction_id}", response_model=schemas.TransactionDetail)
def get_transaction(transaction_id: str, db: Session = Depends(database.get_db)):
    transaction = crud.get_transaction_detail(db, transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return schemas.TransactionDetail.model_validate(transaction)

@app.get("/reconciliation/summary", response_model=List[schemas.ReconciliationSummary])
def get_reconciliation_summary(db: Session = Depends(database.get_db)):
    summaries = crud.get_reconciliation_summary(db)
    return [schemas.ReconciliationSummary(
        merchant_id=s["merchant_id"],
        date=s["date"],
        status=s["status"],
        transaction_count=s["transaction_count"],
        settlement_amount=s["settlement_amount"]
    ) for s in summaries]

@app.get("/reconciliation/discrepancies", response_model=List[schemas.Discrepancy])
def get_discrepancies(db: Session = Depends(database.get_db)):
    discrepancies = crud.get_discrepancies(db)
    return [schemas.Discrepancy(**d) for d in discrepancies]