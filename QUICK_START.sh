#!/bin/bash
# Quick Start Guide - Pine Labs Payment Reconciliation v2.0

## 1. Start Server
echo "Starting Pine Labs Payment Reconciliation Service..."
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000

## Service will be available at:
## - API: http://localhost:8000
## - Docs: http://localhost:8000/docs

---

## 2. Ingest an Event (Example)
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "evt-20260425-001",
    "event_type": "payment_initiated",
    "transaction_id": "tx-20260425-001",
    "merchant_id": "merchant_001",
    "merchant_name": "Tech Store",
    "amount": 10000.0,
    "currency": "INR",
    "timestamp": "2026-04-25T10:00:00"
  }'

---

## 3. List All Transactions
curl "http://localhost:8000/transactions"

---

## 4. Get Payment Detail
curl "http://localhost:8000/payments/pr-20260425-001"

---

## 5. Get Reconciliation Report
curl "http://localhost:8000/reconciliation/report"

---

## 6. Check for Anomalies
curl "http://localhost:8000/anomalies"

---

## 7. Run Tests
python3 test_edge_cases.py

---

## Documentation Files
- README.md              - Service overview
- API_REFERENCE.md      - Complete API documentation
- REFACTORING_SUMMARY.md - What changed in v2.0
- VALIDATION_REPORT.md  - Test results & quality metrics
- test_edge_cases.py    - Comprehensive test suite (32 tests)

---

## Quick Tips
- All endpoints support JSON
- Datetime format: ISO 8601 (2026-04-25T10:00:00)
- Max page size: 100 records
- Common currencies: INR, USD, EUR, GBP
- Payment states: initiated, processed, failed, settled

---
