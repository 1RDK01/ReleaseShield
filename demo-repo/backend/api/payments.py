"""
FastAPI payment endpoints.
"""
from fastapi import APIRouter, HTTPException, status
from typing import List
import json
import os

from ..schemas.payment import PaymentCreate, PaymentUpdate, PaymentResponse, PaymentSummary
from ..services.payment_service import payment_service, PaymentValidationError, PaymentNotFoundError

router = APIRouter(prefix="/payments", tags=["payments"])

# In-memory store for demo purposes
_payments_store: List[dict] = []
_next_id: int = 1

def _load_fixtures() -> None:
    """Load demo fixtures on startup."""
    global _payments_store, _next_id
    fixture_path = os.path.join(os.path.dirname(__file__), "../../../fixtures/payments.json")
    if os.path.exists(fixture_path):
        with open(fixture_path) as f:
            data = json.load(f)
            _payments_store = data.get("payments", [])
            if _payments_store:
                _next_id = max(p["id"] for p in _payments_store) + 1


_load_fixtures()


@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(payload: PaymentCreate) -> PaymentResponse:
    """Create a new payment."""
    global _next_id
    try:
        payment_data = payment_service.create_payment(payload)
        payment_data["id"] = _next_id
        _next_id += 1
        _payments_store.append(payment_data)
        return PaymentResponse(**payment_data)
    except PaymentValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("/", response_model=List[PaymentSummary])
async def list_payments(customer_id: str = None) -> List[PaymentSummary]:
    """List all payments, optionally filtered by customer."""
    results = _payments_store
    if customer_id:
        results = [p for p in results if p["customer_id"] == customer_id]
    return [PaymentSummary(**p) for p in results]


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(payment_id: int) -> PaymentResponse:
    """Get a single payment by ID."""
    payment = next((p for p in _payments_store if p["id"] == payment_id), None)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Payment {payment_id} not found")
    return PaymentResponse(**payment)


@router.patch("/{payment_id}", response_model=PaymentResponse)
async def update_payment(payment_id: int, payload: PaymentUpdate) -> PaymentResponse:
    """Update payment status or description."""
    payment = next((p for p in _payments_store if p["id"] == payment_id), None)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Payment {payment_id} not found")
    if payload.status:
        payment["status"] = payload.status.value
    if payload.description is not None:
        payment["description"] = payload.description
    return PaymentResponse(**payment)


@router.get("/{payment_id}/fee")
async def get_processing_fee(payment_id: int) -> dict:
    """Calculate processing fee for a payment."""
    payment = next((p for p in _payments_store if p["id"] == payment_id), None)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Payment {payment_id} not found")
    amount: int = payment["amount"]
    fee = payment_service.calculate_processing_fee(amount)
    net = payment_service.calculate_net_amount(amount)
    return {
        "payment_id": payment_id,
        "gross_amount": amount,
        "processing_fee": fee,
        "net_amount": net,
        "formatted": payment_service.format_amount_display(amount),
    }
