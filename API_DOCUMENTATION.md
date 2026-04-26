# Pine Labs Payment Reconciliation - API Documentation

**Version:** 2.0.0  
**Base URL:** `http://localhost:8000` (Development) | `https://api.pinelabs.com` (Production)  
**API Standard:** RESTful  
**Data Format:** JSON

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Request/Response Format](#requestresponse-format)
4. [API Endpoints](#api-endpoints)
5. [Error Handling](#error-handling)
6. [Rate Limiting](#rate-limiting)
7. [Pagination](#pagination)
8. [Filtering & Sorting](#filtering--sorting)

---

## Overview

The Pine Labs Payment Reconciliation API provides a comprehensive system for managing merchant transactions, tracking payment events, and performing financial reconciliation with discrepancy detection.

### Core Features
- **Event Ingestion:** Ingest payment events with automatic merchant/transaction creation
- **Transaction Management:** Query and manage transactions with filtering and pagination
- **Reconciliation:** Generate reconciliation summaries and detect discrepancies
- **Idempotency:** Duplicate event requests are safely handled
- **Real-time Processing:** Events processed immediately upon receipt

### Use Cases
1. **Payment Tracking:** Monitor payment lifecycle from initiation to settlement
2. **Discrepancy Detection:** Identify unresolved payments, state inconsistencies, and duplicates
3. **Financial Reporting:** Generate reconciliation summaries by merchant and date
4. **Audit Trail:** Maintain complete event history for compliance

---

## Authentication

Currently, the API uses **API Key authentication** (configured for future enhancement).

### Secure Deployment

**For production, implement JWT authentication:**

```bash
# Add to requirements.txt
python-jose==3.3.0
passlib==1.7.4
python-multipart==0.0.6

# Generate secret key
python3 -c "from secrets import token_urlsafe; print(token_urlsafe(32))"
```

**Implementation:**
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthCredentials = Depends(security)):
    if credentials.credentials != VALID_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    return credentials.credentials
```

---

## Request/Response Format

### Standard Request Headers

```http
POST /events HTTP/1.1
Host: api.pinelabs.com
Content-Type: application/json
Accept: application/json
```

### Standard Response Headers

```http
HTTP/1.1 200 OK
Content-Type: application/json
X-Request-ID: 550e8400-e29b-41d4-a716-446655440000
X-Response-Time: 45ms
```

### Response Envelope

**Success Response:**
```json
{
  "status": "success",
  "code": 200,
  "data": { /* endpoint-specific data */ },
  "timestamp": "2026-04-26T10:00:00Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Error Response:**
```json
{
  "status": "error",
  "code": 422,
  "error": {
    "type": "validation_error",
    "message": "Input should be a valid datetime",
    "details": {
      "field": "timestamp",
      "value": "invalid-date",
      "hint": "Use ISO 8601 format: YYYY-MM-DDTHH:mm:ss"
    }
  },
  "timestamp": "2026-04-26T10:00:00Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

## API Endpoints

### 1. POST /events - Ingest Payment Event

**Description:** Record a payment event with automatic merchant and transaction creation.

**Request:**
```http
POST /events HTTP/1.1
Content-Type: application/json

{
  "event_id": "evt-001",
  "event_type": "payment_initiated",
  "merchant_id": "merchant_001",
  "merchant_name": "Tech Store",
  "transaction_id": "tx-001",
  "amount": 100.00,
  "currency": "USD",
  "timestamp": "2026-04-26T10:00:00",
  "metadata": {
    "order_id": "ORD-12345",
    "customer_id": "CUST-789"
  }
}
```

**Request Parameters:**

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| event_id | string | Yes | Unique event identifier | "evt-001" |
| event_type | enum | Yes | Type of event | "payment_initiated", "payment_processed", "payment_failed", "settled" |
| merchant_id | string | Yes | Merchant identifier | "merchant_001" |
| merchant_name | string | Yes | Merchant display name | "Tech Store" |
| transaction_id | string | Yes | Transaction identifier | "tx-001" |
| amount | number | Yes | Transaction amount | 100.00 |
| currency | string | Yes | ISO 4217 currency code | "USD", "EUR", "INR" |
| timestamp | datetime | Yes | ISO 8601 timestamp | "2026-04-26T10:00:00" |
| metadata | object | No | Additional event data | {"order_id": "ORD-12345"} |

**Response:**
```json
{
  "status": "success",
  "code": 201,
  "data": {
    "event_id": "evt-001",
    "event_type": "payment_initiated",
    "transaction_id": "tx-001",
    "merchant_id": "merchant_001",
    "amount": 100.00,
    "currency": "USD",
    "timestamp": "2026-04-26T10:00:00",
    "created_at": "2026-04-26T10:00:00.123456Z"
  },
  "timestamp": "2026-04-26T10:00:00Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Status Codes:**

| Code | Meaning |
|------|---------|
| 201 | Event created successfully |
| 422 | Validation error (invalid timestamp format, missing fields) |
| 500 | Server error |

**Idempotency:** Duplicate event_id returns the cached event (201 on first, 200 on retry).

**Example with cURL:**
```bash
curl -X POST "http://localhost:8000/events" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "evt-001",
    "event_type": "payment_initiated",
    "merchant_id": "merchant_001",
    "merchant_name": "Tech Store",
    "transaction_id": "tx-001",
    "amount": 100.00,
    "currency": "USD",
    "timestamp": "2026-04-26T10:00:00"
  }'
```

---

### 2. GET /transactions - List Transactions

**Description:** Retrieve paginated list of transactions with filtering and sorting.

**Request:**
```http
GET /transactions?merchant_id=merchant_001&status=processed&page=1&size=20&sort_by=created_at&sort_order=desc HTTP/1.1
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| merchant_id | string | - | Filter by merchant ID |
| status | enum | - | Filter by status: `initiated`, `processed`, `failed`, `settled` |
| start_date | date | - | Filter from date (YYYY-MM-DD) |
| end_date | date | - | Filter to date (YYYY-MM-DD) |
| page | integer | 1 | Page number (1-based) |
| size | integer | 20 | Items per page (max 100) |
| sort_by | enum | created_at | Sort field: `created_at`, `updated_at`, `amount` |
| sort_order | enum | asc | Sort direction: `asc`, `desc` |

**Response:**
```json
{
  "status": "success",
  "code": 200,
  "data": {
    "transactions": [
      {
        "transaction_id": "tx-001",
        "merchant_id": "merchant_001",
        "amount": 100.00,
        "currency": "USD",
        "status": "processed",
        "created_at": "2026-04-26T10:00:00Z",
        "updated_at": "2026-04-26T10:15:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "size": 20,
      "total": 10000,
      "total_pages": 500,
      "has_next": true,
      "has_prev": false
    }
  },
  "timestamp": "2026-04-26T10:00:00Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Examples:**

```bash
# Get all transactions
curl "http://localhost:8000/transactions"

# Filter by merchant
curl "http://localhost:8000/transactions?merchant_id=merchant_001"

# Filter by status
curl "http://localhost:8000/transactions?status=settled"

# Date range filter
curl "http://localhost:8000/transactions?start_date=2026-01-01&end_date=2026-04-26"

# Pagination
curl "http://localhost:8000/transactions?page=5&size=50"

# Sorting
curl "http://localhost:8000/transactions?sort_by=amount&sort_order=desc"

# Combined filters
curl "http://localhost:8000/transactions?merchant_id=merchant_001&status=processed&sort_by=created_at&sort_order=desc&page=1&size=20"
```

---

### 3. GET /transactions/{transaction_id} - Get Transaction Detail

**Description:** Retrieve detailed transaction information including related events and merchant data.

**Request:**
```http
GET /transactions/tx-001 HTTP/1.1
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| transaction_id | string | Transaction identifier |

**Response:**
```json
{
  "status": "success",
  "code": 200,
  "data": {
    "transaction_id": "tx-001",
    "merchant_id": "merchant_001",
    "merchant_name": "Tech Store",
    "amount": 100.00,
    "currency": "USD",
    "status": "processed",
    "created_at": "2026-04-26T10:00:00Z",
    "updated_at": "2026-04-26T10:15:00Z",
    "events": [
      {
        "event_id": "evt-001",
        "event_type": "payment_initiated",
        "timestamp": "2026-04-26T10:00:00Z",
        "amount": 100.00,
        "currency": "USD"
      },
      {
        "event_id": "evt-002",
        "event_type": "payment_processed",
        "timestamp": "2026-04-26T10:15:00Z",
        "amount": 100.00,
        "currency": "USD"
      }
    ]
  },
  "timestamp": "2026-04-26T10:00:00Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Status Codes:**

| Code | Meaning |
|------|---------|
| 200 | Transaction found |
| 404 | Transaction not found |

**Examples:**
```bash
curl "http://localhost:8000/transactions/tx-001"

# With jq for pretty printing
curl -s "http://localhost:8000/transactions/tx-001" | jq '.data.events'
```

---

### 4. GET /reconciliation/summary - Reconciliation Summary

**Description:** Generate reconciliation summary grouped by merchant, date, and status.

**Request:**
```http
GET /reconciliation/summary?start_date=2026-01-01&end_date=2026-04-26 HTTP/1.1
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| start_date | date | - | Summary from date (YYYY-MM-DD) |
| end_date | date | - | Summary to date (YYYY-MM-DD) |
| merchant_id | string | - | Filter by specific merchant |

**Response:**
```json
{
  "status": "success",
  "code": 200,
  "data": {
    "summary_period": {
      "start_date": "2026-01-01",
      "end_date": "2026-04-26",
      "total_days": 115
    },
    "summaries": [
      {
        "merchant_id": "merchant_001",
        "merchant_name": "Tech Store",
        "date": "2026-04-26",
        "status": "settled",
        "transaction_count": 42,
        "settlement_amount": 4200.00,
        "currency": "USD",
        "average_transaction": 100.00
      },
      {
        "merchant_id": "merchant_001",
        "merchant_name": "Tech Store",
        "date": "2026-04-26",
        "status": "processed",
        "transaction_count": 8,
        "settlement_amount": 800.00,
        "currency": "USD",
        "average_transaction": 100.00
      },
      {
        "merchant_id": "merchant_002",
        "merchant_name": "Fresh Basket",
        "date": "2026-04-26",
        "status": "settled",
        "transaction_count": 35,
        "settlement_amount": 5250.00,
        "currency": "USD",
        "average_transaction": 150.00
      }
    ],
    "totals": {
      "total_transactions": 85,
      "total_settled_amount": 9450.00,
      "total_pending_amount": 800.00,
      "total_failed_amount": 0.00
    }
  },
  "timestamp": "2026-04-26T10:00:00Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Examples:**
```bash
# Full summary
curl "http://localhost:8000/reconciliation/summary"

# Date range
curl "http://localhost:8000/reconciliation/summary?start_date=2026-04-20&end_date=2026-04-26"

# Specific merchant
curl "http://localhost:8000/reconciliation/summary?merchant_id=merchant_001"

# Combined
curl "http://localhost:8000/reconciliation/summary?merchant_id=merchant_001&start_date=2026-01-01&end_date=2026-04-26"
```

---

### 5. GET /reconciliation/discrepancies - Detect Discrepancies

**Description:** Identify payment discrepancies including unresolved settlements, state inconsistencies, and duplicate events.

**Request:**
```http
GET /reconciliation/discrepancies?severity=high HTTP/1.1
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| severity | enum | all | Filter by severity: `critical`, `high`, `medium`, `all` |
| merchant_id | string | - | Filter by merchant |
| start_date | date | - | Check from date |
| end_date | date | - | Check to date |

**Response:**
```json
{
  "status": "success",
  "code": 200,
  "data": {
    "total_discrepancies": 3,
    "by_type": {
      "unresolved_settlement": 1,
      "state_inconsistency": 1,
      "duplicate_events": 1
    },
    "discrepancies": [
      {
        "discrepancy_id": "disc-001",
        "type": "unresolved_settlement",
        "severity": "high",
        "transaction_id": "tx-042",
        "merchant_id": "merchant_001",
        "merchant_name": "Tech Store",
        "amount": 150.00,
        "currency": "USD",
        "last_status": "processed",
        "last_event_time": "2026-04-20T15:30:00Z",
        "days_unresolved": 6,
        "description": "Payment processed but not settled after 6 days"
      },
      {
        "discrepancy_id": "disc-002",
        "type": "state_inconsistency",
        "severity": "critical",
        "transaction_id": "tx-089",
        "merchant_id": "merchant_003",
        "merchant_name": "Electronics Hub",
        "amount": 250.00,
        "currency": "USD",
        "description": "Payment marked as settled despite failure event in history"
      },
      {
        "discrepancy_id": "disc-003",
        "type": "duplicate_events",
        "severity": "medium",
        "transaction_id": "tx-124",
        "merchant_id": "merchant_002",
        "merchant_name": "Fresh Basket",
        "amount": 200.00,
        "currency": "USD",
        "duplicate_event_ids": ["evt-0451", "evt-0452"],
        "description": "Multiple payment_initiated events for same transaction"
      }
    ]
  },
  "timestamp": "2026-04-26T10:00:00Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Discrepancy Types:**

| Type | Description | Resolution |
|------|-------------|-----------|
| unresolved_settlement | Processed payment not settled within SLA | Manual review and settlement |
| state_inconsistency | Conflicting event history | Audit trail review |
| duplicate_events | Multiple events for single transaction state | Event deduplication |

**Examples:**
```bash
# All discrepancies
curl "http://localhost:8000/reconciliation/discrepancies"

# Critical issues only
curl "http://localhost:8000/reconciliation/discrepancies?severity=critical"

# Merchant-specific
curl "http://localhost:8000/reconciliation/discrepancies?merchant_id=merchant_001"

# Date range
curl "http://localhost:8000/reconciliation/discrepancies?start_date=2026-04-01&end_date=2026-04-26"
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | Transaction retrieved |
| 201 | Created | Event ingested successfully |
| 400 | Bad Request | Missing required field |
| 422 | Validation Error | Invalid datetime format |
| 404 | Not Found | Transaction doesn't exist |
| 500 | Server Error | Database connection failure |
| 503 | Service Unavailable | Maintenance mode |

### Error Response Examples

**Validation Error (422):**
```json
{
  "status": "error",
  "code": 422,
  "error": {
    "type": "validation_error",
    "message": "Input should be a valid datetime",
    "details": {
      "field": "timestamp",
      "value": "2026-04-26 10:00:00",
      "hint": "Use ISO 8601 format: YYYY-MM-DDTHH:mm:ss"
    }
  }
}
```

**Not Found (404):**
```json
{
  "status": "error",
  "code": 404,
  "error": {
    "type": "not_found",
    "message": "Transaction not found",
    "details": {
      "transaction_id": "tx-999999"
    }
  }
}
```

**Server Error (500):**
```json
{
  "status": "error",
  "code": 500,
  "error": {
    "type": "database_error",
    "message": "Database connection failed",
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

---

## Rate Limiting

### Production Rate Limits

| Endpoint | Rate Limit | Window |
|----------|-----------|--------|
| POST /events | 1000 req | per minute |
| GET /transactions | 100 req | per minute |
| GET /reconciliation/* | 50 req | per minute |

### Rate Limit Headers

```http
HTTP/1.1 200 OK
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1698345600
```

### Rate Limit Exceeded

```json
{
  "status": "error",
  "code": 429,
  "error": {
    "type": "rate_limit_exceeded",
    "message": "Too many requests",
    "retry_after": 60
  }
}
```

**Handling Rate Limits:**
```python
import time
import requests

while True:
    response = requests.post("http://localhost:8000/events", json=event_data)
    
    if response.status_code == 429:
        retry_after = int(response.headers.get('Retry-After', 60))
        print(f"Rate limited. Retrying after {retry_after}s")
        time.sleep(retry_after)
    elif response.status_code == 201:
        print("Event created successfully")
        break
    else:
        raise Exception(f"Unexpected error: {response.status_code}")
```

---

## Pagination

### Pagination Parameters

```http
GET /transactions?page=1&size=20
```

| Parameter | Type | Range | Default |
|-----------|------|-------|---------|
| page | integer | 1+ | 1 |
| size | integer | 1-100 | 20 |

### Pagination Response

```json
{
  "data": {
    "transactions": [...],
    "pagination": {
      "page": 2,
      "size": 20,
      "total": 10000,
      "total_pages": 500,
      "has_next": true,
      "has_prev": true
    }
  }
}
```

### Pagination Examples

```bash
# Get second page
curl "http://localhost:8000/transactions?page=2&size=20"

# Get 50 items per page
curl "http://localhost:8000/transactions?page=1&size=50"

# Get last page for 10000 items
curl "http://localhost:8000/transactions?page=500&size=20"
```

---

## Filtering & Sorting

### Filtering Examples

**By Merchant:**
```bash
curl "http://localhost:8000/transactions?merchant_id=merchant_001"
```

**By Status:**
```bash
curl "http://localhost:8000/transactions?status=settled"
```

**By Date Range:**
```bash
curl "http://localhost:8000/transactions?start_date=2026-04-01&end_date=2026-04-26"
```

**Combined:**
```bash
curl "http://localhost:8000/transactions?merchant_id=merchant_001&status=processed&start_date=2026-04-01&end_date=2026-04-26"
```

### Sorting Examples

**By Created Date (Descending):**
```bash
curl "http://localhost:8000/transactions?sort_by=created_at&sort_order=desc"
```

**By Amount (Ascending):**
```bash
curl "http://localhost:8000/transactions?sort_by=amount&sort_order=asc"
```

**By Updated Date (Descending):**
```bash
curl "http://localhost:8000/transactions?sort_by=updated_at&sort_order=desc"
```

---

## SDK Usage Examples

### Python

```python
import requests
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

# Ingest event
event = {
    "event_id": "evt-001",
    "event_type": "payment_initiated",
    "merchant_id": "merchant_001",
    "merchant_name": "Tech Store",
    "transaction_id": "tx-001",
    "amount": 100.00,
    "currency": "USD",
    "timestamp": datetime.now().isoformat()
}

response = requests.post(f"{BASE_URL}/events", json=event)
print(response.json())

# List transactions
response = requests.get(
    f"{BASE_URL}/transactions",
    params={
        "merchant_id": "merchant_001",
        "status": "settled",
        "page": 1,
        "size": 20,
        "sort_by": "created_at",
        "sort_order": "desc"
    }
)
transactions = response.json()["data"]["transactions"]

# Get transaction detail
response = requests.get(f"{BASE_URL}/transactions/tx-001")
transaction = response.json()["data"]

# Get reconciliation summary
response = requests.get(
    f"{BASE_URL}/reconciliation/summary",
    params={
        "start_date": (datetime.now() - timedelta(days=30)).date(),
        "end_date": datetime.now().date()
    }
)
summary = response.json()["data"]["summaries"]

# Get discrepancies
response = requests.get(
    f"{BASE_URL}/reconciliation/discrepancies",
    params={"severity": "critical"}
)
discrepancies = response.json()["data"]["discrepancies"]
```

### JavaScript/Node.js

```javascript
const BASE_URL = 'http://localhost:8000';

// Ingest event
async function ingestEvent(event) {
  const response = await fetch(`${BASE_URL}/events`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(event)
  });
  return response.json();
}

// List transactions
async function getTransactions(filters = {}) {
  const params = new URLSearchParams(filters);
  const response = await fetch(`${BASE_URL}/transactions?${params}`);
  return response.json();
}

// Get transaction detail
async function getTransaction(transactionId) {
  const response = await fetch(`${BASE_URL}/transactions/${transactionId}`);
  return response.json();
}

// Get reconciliation summary
async function getReconciliationSummary(startDate, endDate) {
  const params = new URLSearchParams({ start_date: startDate, end_date: endDate });
  const response = await fetch(`${BASE_URL}/reconciliation/summary?${params}`);
  return response.json();
}

// Get discrepancies
async function getDiscrepancies(severity = 'all') {
  const params = new URLSearchParams({ severity });
  const response = await fetch(`${BASE_URL}/reconciliation/discrepancies?${params}`);
  return response.json();
}
```

---

**Document Version:** 2.0.0  
**Last Updated:** April 26, 2026  
**Maintained By:** Pine Labs API Team
