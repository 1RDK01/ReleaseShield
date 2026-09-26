# Demo Repository: Payment Service

This is the **demo repository** for ReleaseShield. It contains a realistic enterprise
payment/order system that demonstrates repository-wide change impact.

## Structure

```
demo-repo/
├── backend/
│   ├── api/payments.py          # FastAPI endpoints
│   ├── models/payment.py        # SQLAlchemy ORM model
│   ├── schemas/payment.py       # Pydantic validation schemas
│   ├── services/payment_service.py  # Business logic
│   └── main.py                  # FastAPI app
├── frontend/
│   └── src/
│       ├── types/Payment.ts     # TypeScript domain types
│       ├── api/payments.ts      # API client
│       └── components/
│           ├── PaymentCard.tsx
│           └── PaymentCard.test.tsx
├── tests/
│   ├── test_payments.py         # Unit tests
│   └── test_payment_api.py      # Integration tests
├── fixtures/payments.json       # Test/demo fixtures
├── migrations/001_create_payments.sql
└── requirements.txt
```

## Current State (BEFORE change)

The `amount` field is stored as **integer cents** throughout:
- Database: `INTEGER` column
- ORM: `Column(Integer)`
- Pydantic schema: `amount: int`
- Service: validates `isinstance(amount, int)`
- TypeScript types: `amount: number` with `Number.isInteger()` checks
- Tests: assert `isinstance(amount, int)`
- Fixtures: integer values like `9999`

## The Deliberate Change

When `demo/introduce_change.py` runs, it modifies only:
- `backend/models/payment.py`: changes `Integer` → `Numeric(precision=10, scale=2)`

This creates silent incompatibilities in 7+ additional files — which ReleaseShield discovers.

## Running Tests (BEFORE state)

```bash
cd demo-repo
pip install -r requirements.txt
pytest tests/ -v
```

All 18 tests should pass in the BEFORE state.
