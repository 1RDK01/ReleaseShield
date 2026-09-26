"""
Coherent multi-file remediation templates for ReleaseShield.
Contains both the clean BEFORE state and the remediated AFTER state for every
file in the demo repository.
"""
import os
from pathlib import Path
from typing import Dict, List, Tuple


# ============================================================================
# BEFORE STATE (Integer cents throughout)
# ============================================================================

BEFORE_MODEL = '''\
"""
SQLAlchemy ORM model for Payment.
NOTE: amount is currently Integer — this is the BEFORE state.
"""
from sqlalchemy import Column, Integer, String, DateTime, Enum as SAEnum
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String(36), nullable=False, index=True)
    customer_id = Column(String(36), nullable=False, index=True)
    amount = Column(Integer, nullable=False)  # stored as cents (integer)
    currency = Column(String(3), nullable=False, default="USD")
    status = Column(SAEnum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    payment_method = Column(String(50), nullable=False)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "order_id": self.order_id,
            "customer_id": self.customer_id,
            "amount": self.amount,  # integer cents
            "currency": self.currency,
            "status": self.status.value,
            "payment_method": self.payment_method,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<Payment id={self.id} amount={self.amount} status={self.status}>"
'''

BEFORE_SCHEMA = '''\
"""
Pydantic schemas for Payment API.
NOTE: amount is Integer — matches the current ORM model.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from enum import Enum


class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentCreate(BaseModel):
    order_id: str = Field(..., min_length=1, max_length=36)
    customer_id: str = Field(..., min_length=1, max_length=36)
    amount: int = Field(..., gt=0, description="Payment amount in cents (integer)")
    currency: str = Field(default="USD", min_length=3, max_length=3)
    payment_method: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=255)

    @validator("amount")
    def amount_must_be_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("amount must be a positive integer (cents)")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "order_id": "ord-001",
                "customer_id": "cust-001",
                "amount": 9999,
                "currency": "USD",
                "payment_method": "card",
                "description": "Order payment",
            }
        }


class PaymentUpdate(BaseModel):
    status: Optional[PaymentStatus] = None
    description: Optional[str] = Field(None, max_length=255)


class PaymentResponse(BaseModel):
    id: int
    order_id: str
    customer_id: str
    amount: int  # integer cents
    currency: str
    status: PaymentStatus
    payment_method: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    def formatted_amount(self) -> str:
        """Return human-readable amount string."""
        return f"{self.amount} cents"


class PaymentSummary(BaseModel):
    """Lightweight summary for list views."""
    id: int
    order_id: str
    amount: int
    currency: str
    status: PaymentStatus
    created_at: datetime

    class Config:
        from_attributes = True
'''

BEFORE_SERVICE = '''\
"""
Payment business logic service.
NOTE: operates on integer cent amounts throughout.
"""
from typing import List, Optional
from datetime import datetime

from ..models.payment import Payment, PaymentStatus as ModelStatus
from ..schemas.payment import PaymentCreate, PaymentUpdate, PaymentResponse


class PaymentValidationError(Exception):
    pass


class PaymentNotFoundError(Exception):
    pass


class PaymentService:
    """Core payment processing service."""

    # Minimum payment threshold in cents (integer)
    MIN_AMOUNT_CENTS: int = 100  # $1.00
    MAX_AMOUNT_CENTS: int = 10_000_000  # $100,000.00

    def validate_amount(self, amount: int) -> None:
        """Validate payment amount is within acceptable integer cent range."""
        if not isinstance(amount, int):
            raise PaymentValidationError(f"Amount must be an integer (cents), got {type(amount).__name__}")
        if amount < self.MIN_AMOUNT_CENTS:
            raise PaymentValidationError(
                f"Amount {amount} cents is below minimum {self.MIN_AMOUNT_CENTS} cents"
            )
        if amount > self.MAX_AMOUNT_CENTS:
            raise PaymentValidationError(
                f"Amount {amount} cents exceeds maximum {self.MAX_AMOUNT_CENTS} cents"
            )

    def calculate_processing_fee(self, amount: int) -> int:
        """Calculate payment processor fee. Returns integer cents."""
        # 2.9% + 30 cents, rounded to nearest cent
        fee = int(amount * 0.029) + 30
        return fee

    def calculate_net_amount(self, amount: int) -> int:
        """Calculate net amount after processor fee. Returns integer cents."""
        fee = self.calculate_processing_fee(amount)
        return amount - fee

    def format_amount_display(self, amount: int) -> str:
        """Format integer cents as display string."""
        dollars = amount // 100
        cents = amount % 100
        return f"${dollars}.{cents:02d}"

    def create_payment(self, data: PaymentCreate) -> dict:
        """Create payment record. Returns dict suitable for ORM creation."""
        self.validate_amount(data.amount)
        return {
            "order_id": data.order_id,
            "customer_id": data.customer_id,
            "amount": data.amount,  # integer cents
            "currency": data.currency,
            "status": ModelStatus.PENDING,
            "payment_method": data.payment_method,
            "description": data.description,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

    def process_refund(self, original_amount: int, refund_amount: int) -> dict:
        """Process a refund. All amounts in integer cents."""
        self.validate_amount(original_amount)
        if refund_amount > original_amount:
            raise PaymentValidationError(
                f"Refund amount {refund_amount} exceeds original {original_amount}"
            )
        return {
            "refund_amount": refund_amount,
            "remaining_amount": original_amount - refund_amount,
            "is_full_refund": refund_amount == original_amount,
        }

    def aggregate_by_customer(self, payments: List[dict]) -> dict:
        """Aggregate payment totals by customer. Returns integer cent totals."""
        result: dict = {}
        for p in payments:
            cid = p["customer_id"]
            amt = p["amount"]  # integer cents
            if cid not in result:
                result[cid] = {"total_cents": 0, "count": 0}
            result[cid]["total_cents"] += amt
            result[cid]["count"] += 1
        return result


payment_service = PaymentService()
'''

BEFORE_API = '''\
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
'''

BEFORE_TYPES = '''\
/**
 * Core Payment domain types.
 * NOTE: amount is number (integer cents) — BEFORE state.
 */

export type PaymentStatus = 'pending' | 'completed' | 'failed' | 'refunded';

export interface Payment {
  id: number;
  order_id: string;
  customer_id: string;
  amount: number; // integer cents (e.g., 9999 = $99.99)
  currency: string;
  status: PaymentStatus;
  payment_method: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface PaymentSummary {
  id: number;
  order_id: string;
  amount: number; // integer cents
  currency: string;
  status: PaymentStatus;
  created_at: string;
}

export interface PaymentCreate {
  order_id: string;
  customer_id: string;
  amount: number; // must be positive integer cents
  currency: string;
  payment_method: string;
  description?: string;
}

export interface PaymentUpdate {
  status?: PaymentStatus;
  description?: string;
}

export interface ProcessingFeeResponse {
  payment_id: number;
  gross_amount: number; // integer cents
  processing_fee: number; // integer cents
  net_amount: number; // integer cents
  formatted: string;
}

/**
 * Format integer cents to display string.
 * @param cents - integer cent amount (e.g., 9999)
 * @returns formatted string (e.g., "$99.99")
 */
export function formatAmount(cents: number): string {
  const dollars = Math.floor(cents / 100);
  const remainder = cents % 100;
  return `$${dollars}.${remainder.toString().padStart(2, '0')}`;
}

/**
 * Validate that a payment amount is a valid integer cent value.
 * @param amount - value to validate
 * @returns true if valid
 */
export function isValidAmount(amount: number): boolean {
  return Number.isInteger(amount) && amount > 0;
}
'''

BEFORE_API_CLIENT = '''\
/**
 * API client for payment service.
 * NOTE: expects integer cent amounts in all requests/responses.
 */

import type {
  Payment,
  PaymentCreate,
  PaymentUpdate,
  PaymentSummary,
  ProcessingFeeResponse,
} from '../types/Payment';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

/**
 * Create a new payment.
 * @param data - payment data with integer cent amount
 */
export async function createPayment(data: PaymentCreate): Promise<Payment> {
  if (!Number.isInteger(data.amount)) {
    throw new Error('Payment amount must be an integer (cents)');
  }
  return fetchJson<Payment>(`${BASE_URL}/payments/`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * List all payments, optionally filtered by customer.
 */
export async function listPayments(customerId?: string): Promise<PaymentSummary[]> {
  const url = customerId
    ? `${BASE_URL}/payments/?customer_id=${encodeURIComponent(customerId)}`
    : `${BASE_URL}/payments/`;
  return fetchJson<PaymentSummary[]>(url);
}

/**
 * Get a single payment by ID.
 */
export async function getPayment(id: number): Promise<Payment> {
  return fetchJson<Payment>(`${BASE_URL}/payments/${id}`);
}

/**
 * Update a payment.
 */
export async function updatePayment(id: number, data: PaymentUpdate): Promise<Payment> {
  return fetchJson<Payment>(`${BASE_URL}/payments/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

/**
 * Get processing fee for a payment.
 * Returns integer cent amounts for gross, fee, and net.
 */
export async function getProcessingFee(id: number): Promise<ProcessingFeeResponse> {
  return fetchJson<ProcessingFeeResponse>(`${BASE_URL}/payments/${id}/fee`);
}
'''

BEFORE_CARD = '''\
/**
 * PaymentCard component.
 * NOTE: expects integer cent amounts — displays them formatted.
 * BEFORE state: uses integer arithmetic.
 */

import React from 'react';
import type { Payment } from '../types/Payment';
import { formatAmount } from '../types/Payment';

interface PaymentCardProps {
  payment: Payment;
  onSelect?: (id: number) => void;
}

const STATUS_STYLES: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  completed: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
  refunded: 'bg-gray-100 text-gray-800',
};

export function PaymentCard({ payment, onSelect }: PaymentCardProps): JSX.Element {
  // amount is integer cents — use integer arithmetic throughout
  const amountDisplay = formatAmount(payment.amount);

  // Integer-based calculation: fee is 2.9% + 30 cents
  const feeEstimate = Math.floor(payment.amount * 0.029) + 30;
  const netEstimate = payment.amount - feeEstimate;

  // Validate amount is integer (matches backend contract)
  const isValidAmount = Number.isInteger(payment.amount);

  return (
    <div
      className="border rounded-lg p-4 bg-white shadow-sm hover:shadow-md transition-shadow cursor-pointer"
      onClick={() => onSelect?.(payment.id)}
      data-testid={`payment-card-${payment.id}`}
    >
      <div className="flex justify-between items-start mb-3">
        <div>
          <p className="text-sm text-gray-500">Order #{payment.order_id}</p>
          <p className="text-lg font-semibold text-gray-900">{amountDisplay}</p>
        </div>
        <span
          className={`text-xs px-2 py-1 rounded-full font-medium ${STATUS_STYLES[payment.status] || ''}`}
        >
          {payment.status}
        </span>
      </div>

      <div className="text-xs text-gray-500 space-y-1">
        <p>Customer: {payment.customer_id}</p>
        <p>Method: {payment.payment_method}</p>
        {payment.description && <p>Note: {payment.description}</p>}
      </div>

      <div className="mt-3 pt-3 border-t border-gray-100 text-xs text-gray-400">
        <p>Raw amount: {payment.amount} cents (integer)</p>
        <p>Est. fee: {feeEstimate} cents | Net: {netEstimate} cents</p>
        {!isValidAmount && (
          <p className="text-red-500 font-medium">⚠ Non-integer amount detected</p>
        )}
      </div>
    </div>
  );
}

export default PaymentCard;
'''

BEFORE_TESTS = '''\
"""
Unit tests for payment service.
NOTE: All amounts are integer cents — this is the BEFORE state.
"""
import pytest
from backend.services.payment_service import PaymentService, PaymentValidationError
from backend.schemas.payment import PaymentCreate


class TestPaymentValidation:
    """Tests for amount validation logic."""

    def test_valid_integer_amount(self, payment_service: PaymentService) -> None:
        """Amount must be a positive integer (cents)."""
        payment_service.validate_amount(9999)  # $99.99 as integer cents

    def test_amount_below_minimum_raises(self, payment_service: PaymentService) -> None:
        """Amount below 100 cents should raise."""
        with pytest.raises(PaymentValidationError, match="below minimum"):
            payment_service.validate_amount(50)

    def test_amount_exceeds_maximum_raises(self, payment_service: PaymentService) -> None:
        """Amount above max should raise."""
        with pytest.raises(PaymentValidationError):
            payment_service.validate_amount(20_000_000)

    def test_amount_is_integer_type(self, payment_service: PaymentService) -> None:
        """Amount must be strictly an integer type."""
        with pytest.raises(PaymentValidationError, match="must be an integer"):
            payment_service.validate_amount(99.99)  # float not allowed


class TestProcessingFee:
    """Tests for fee calculation on integer cent amounts."""

    def test_fee_calculation_small_amount(self, payment_service: PaymentService) -> None:
        """Fee for $9.99 (999 cents)."""
        fee = payment_service.calculate_processing_fee(999)
        assert fee == 58
        assert isinstance(fee, int)

    def test_fee_calculation_large_amount(self, payment_service: PaymentService) -> None:
        """Fee for $100.00 (10000 cents)."""
        fee = payment_service.calculate_processing_fee(10000)
        assert fee == 320
        assert isinstance(fee, int)

    def test_net_amount_is_integer(self, payment_service: PaymentService) -> None:
        """Net amount after fee must also be integer cents."""
        net = payment_service.calculate_net_amount(9999)
        assert isinstance(net, int)
        assert net > 0


class TestAmountFormatting:
    """Tests for display formatting of integer cent amounts."""

    def test_format_whole_dollars(self, payment_service: PaymentService) -> None:
        assert payment_service.format_amount_display(10000) == "$100.00"

    def test_format_with_cents(self, payment_service: PaymentService) -> None:
        assert payment_service.format_amount_display(9999) == "$99.99"

    def test_format_small_amount(self, payment_service: PaymentService) -> None:
        assert payment_service.format_amount_display(100) == "$1.00"


class TestPaymentCreation:
    """Tests for payment data preparation."""

    def test_create_payment_returns_integer_amount(
        self, payment_service: PaymentService, sample_payment_create: PaymentCreate
    ) -> None:
        result = payment_service.create_payment(sample_payment_create)
        assert result["amount"] == 9999
        assert isinstance(result["amount"], int)

    def test_create_payment_has_required_fields(
        self, payment_service: PaymentService, sample_payment_create: PaymentCreate
    ) -> None:
        result = payment_service.create_payment(sample_payment_create)
        required = ["order_id", "customer_id", "amount", "currency", "status", "payment_method"]
        for field in required:
            assert field in result


class TestRefund:
    """Tests for refund logic using integer cent amounts."""

    def test_full_refund(self, payment_service: PaymentService) -> None:
        result = payment_service.process_refund(9999, 9999)
        assert result["is_full_refund"] is True
        assert result["remaining_amount"] == 0

    def test_partial_refund(self, payment_service: PaymentService) -> None:
        result = payment_service.process_refund(9999, 5000)
        assert result["is_full_refund"] is False
        assert result["remaining_amount"] == 4999

    def test_refund_exceeds_original_raises(self, payment_service: PaymentService) -> None:
        with pytest.raises(PaymentValidationError, match="exceeds original"):
            payment_service.process_refund(9999, 10000)


class TestAggregation:
    """Tests for aggregation logic with integer cents."""

    def test_aggregate_sums_integer_amounts(self, payment_service: PaymentService) -> None:
        payments = [
            {"customer_id": "c1", "amount": 1000},
            {"customer_id": "c1", "amount": 2000},
            {"customer_id": "c2", "amount": 500},
        ]
        result = payment_service.aggregate_by_customer(payments)
        assert result["c1"]["total_cents"] == 3000
        assert result["c1"]["count"] == 2
        assert result["c2"]["total_cents"] == 500
        assert result["c2"]["count"] == 1

    def test_fixtures_have_integer_amounts(self) -> None:
        import json, os
        path = os.path.join(os.path.dirname(__file__), "../fixtures/payments.json")
        with open(path) as f:
            data = json.load(f)
        for p in data["payments"]:
            assert isinstance(p["amount"], int), f"Payment {p['id']} has non-integer amount"


class TestSchemaValidation:
    """Tests for Pydantic schema validation."""

    def test_valid_payment_schema(self, sample_payment_create: PaymentCreate) -> None:
        assert sample_payment_create.amount == 9999
        assert sample_payment_create.order_id == "ord-test-001"

    def test_schema_rejects_zero_amount(self) -> None:
        with pytest.raises(Exception):
            PaymentCreate(
                order_id="ord-002",
                customer_id="cust-002",
                amount=0,
                currency="USD",
                payment_method="card",
            )
'''

BEFORE_CONFTEST = '''\
"""Pytest configuration and shared fixtures for demo-repo tests."""
import pytest
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.schemas.payment import PaymentCreate, PaymentStatus
from backend.services.payment_service import PaymentService


@pytest.fixture
def payment_service() -> PaymentService:
    return PaymentService()


@pytest.fixture
def sample_payment_create() -> PaymentCreate:
    return PaymentCreate(
        order_id="ord-test-001",
        customer_id="cust-test-001",
        amount=9999,  # integer cents
        currency="USD",
        payment_method="card",
        description="Test payment",
    )


@pytest.fixture
def payment_fixtures() -> list:
    fixture_path = os.path.join(os.path.dirname(__file__), "../fixtures/payments.json")
    with open(fixture_path) as f:
        data = json.load(f)
    return data["payments"]
'''

BEFORE_FIXTURES = '''\
{
  "payments": [
    {
      "id": 1,
      "order_id": "ord-001",
      "customer_id": "cust-001",
      "amount": 9999,
      "currency": "USD",
      "status": "completed",
      "payment_method": "card",
      "description": "Premium subscription",
      "created_at": "2024-01-15T10:30:00",
      "updated_at": "2024-01-15T10:30:05"
    },
    {
      "id": 2,
      "order_id": "ord-002",
      "customer_id": "cust-002",
      "amount": 4999,
      "currency": "USD",
      "status": "completed",
      "payment_method": "bank_transfer",
      "description": "Basic plan",
      "created_at": "2024-01-15T11:00:00",
      "updated_at": "2024-01-15T11:00:08"
    },
    {
      "id": 3,
      "order_id": "ord-003",
      "customer_id": "cust-001",
      "amount": 1500,
      "currency": "USD",
      "status": "pending",
      "payment_method": "card",
      "description": "Add-on purchase",
      "created_at": "2024-01-16T09:00:00",
      "updated_at": "2024-01-16T09:00:00"
    },
    {
      "id": 4,
      "order_id": "ord-004",
      "customer_id": "cust-003",
      "amount": 25000,
      "currency": "USD",
      "status": "failed",
      "payment_method": "card",
      "description": "Enterprise license",
      "created_at": "2024-01-16T14:00:00",
      "updated_at": "2024-01-16T14:00:03"
    }
  ]
}
'''


# ============================================================================
# AFTER STATE (Coherently synchronized to Decimal / Numeric precision)
# ============================================================================

AFTER_MODEL = '''\
"""
SQLAlchemy ORM model for Payment.
SYNCHRONIZED BY IBM BOB: amount column is Numeric(precision=10, scale=2)
supporting precise decimal payment amounts (e.g. $99.95).
"""
from sqlalchemy import Column, Integer, String, DateTime, Numeric, Enum as SAEnum
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum
from decimal import Decimal

Base = declarative_base()


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String(36), nullable=False, index=True)
    customer_id = Column(String(36), nullable=False, index=True)
    amount = Column(Numeric(precision=10, scale=2), nullable=False)  # CHANGED: decimal currency
    currency = Column(String(3), nullable=False, default="USD")
    status = Column(SAEnum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    payment_method = Column(String(50), nullable=False)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "order_id": self.order_id,
            "customer_id": self.customer_id,
            "amount": float(self.amount) if self.amount is not None else None,
            "currency": self.currency,
            "status": self.status.value,
            "payment_method": self.payment_method,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<Payment id={self.id} amount={self.amount} status={self.status}>"
'''

AFTER_SCHEMA = '''\
"""
Pydantic schemas for Payment API.
SYNCHRONIZED BY IBM BOB: amount fields updated to Decimal with 2 decimal places.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Union
from datetime import datetime
from decimal import Decimal
from enum import Enum


class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentCreate(BaseModel):
    order_id: str = Field(..., min_length=1, max_length=36)
    customer_id: str = Field(..., min_length=1, max_length=36)
    amount: Decimal = Field(..., gt=0, description="Payment amount in dollars (decimal)")
    currency: str = Field(default="USD", min_length=3, max_length=3)
    payment_method: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=255)

    @validator("amount", pre=True)
    def validate_and_convert_amount(cls, v: Union[Decimal, float, int, str]) -> Decimal:
        try:
            val = Decimal(str(v))
        except Exception:
            raise ValueError("amount must be a valid decimal number")
        if val <= 0:
            raise ValueError("amount must be positive")
        return round(val, 2)

    class Config:
        json_schema_extra = {
            "example": {
                "order_id": "ord-001",
                "customer_id": "cust-001",
                "amount": "99.99",
                "currency": "USD",
                "payment_method": "card",
                "description": "Order payment",
            }
        }


class PaymentUpdate(BaseModel):
    status: Optional[PaymentStatus] = None
    description: Optional[str] = Field(None, max_length=255)


class PaymentResponse(BaseModel):
    id: int
    order_id: str
    customer_id: str
    amount: Decimal  # decimal dollars
    currency: str
    status: PaymentStatus
    payment_method: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    def formatted_amount(self) -> str:
        """Return human-readable amount string."""
        return f"${float(self.amount):.2f}"


class PaymentSummary(BaseModel):
    """Lightweight summary for list views."""
    id: int
    order_id: str
    amount: Decimal
    currency: str
    status: PaymentStatus
    created_at: datetime

    class Config:
        from_attributes = True
'''

AFTER_SERVICE = '''\
"""
Payment business logic service.
SYNCHRONIZED BY IBM BOB: operates on Decimal dollar amounts throughout.
"""
from typing import List, Optional, Union
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from ..models.payment import Payment, PaymentStatus as ModelStatus
from ..schemas.payment import PaymentCreate, PaymentUpdate, PaymentResponse


class PaymentValidationError(Exception):
    pass


class PaymentNotFoundError(Exception):
    pass


class PaymentService:
    """Core payment processing service supporting Decimal precision."""

    # Minimum payment threshold in dollars (Decimal)
    MIN_AMOUNT: Decimal = Decimal("1.00")
    MAX_AMOUNT: Decimal = Decimal("100000.00")

    def validate_amount(self, amount: Union[Decimal, float, int]) -> None:
        """Validate payment amount is within acceptable decimal range."""
        try:
            val = Decimal(str(amount))
        except Exception:
            raise PaymentValidationError(f"Invalid amount value: {amount}")

        if val < self.MIN_AMOUNT:
            raise PaymentValidationError(
                f"Amount ${val:.2f} is below minimum ${self.MIN_AMOUNT:.2f}"
            )
        if val > self.MAX_AMOUNT:
            raise PaymentValidationError(
                f"Amount ${val:.2f} exceeds maximum ${self.MAX_AMOUNT:.2f}"
            )

    def calculate_processing_fee(self, amount: Union[Decimal, float, int]) -> Decimal:
        """Calculate payment processor fee. Returns Decimal dollars."""
        amt = Decimal(str(amount))
        # 2.9% + $0.30, rounded to nearest cent
        fee = (amt * Decimal("0.029") + Decimal("0.30")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return fee

    def calculate_net_amount(self, amount: Union[Decimal, float, int]) -> Decimal:
        """Calculate net amount after processor fee. Returns Decimal dollars."""
        amt = Decimal(str(amount))
        fee = self.calculate_processing_fee(amt)
        return (amt - fee).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def format_amount_display(self, amount: Union[Decimal, float, int]) -> str:
        """Format decimal amount as display string."""
        val = Decimal(str(amount))
        return f"${val:.2f}"

    def create_payment(self, data: PaymentCreate) -> dict:
        """Create payment record. Returns dict suitable for ORM creation."""
        self.validate_amount(data.amount)
        amt = Decimal(str(data.amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return {
            "order_id": data.order_id,
            "customer_id": data.customer_id,
            "amount": amt,
            "currency": data.currency,
            "status": ModelStatus.PENDING,
            "payment_method": data.payment_method,
            "description": data.description,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

    def process_refund(self, original_amount: Union[Decimal, float, int], refund_amount: Union[Decimal, float, int]) -> dict:
        """Process a refund. All amounts in decimal dollars."""
        orig = Decimal(str(original_amount)).quantize(Decimal("0.01"))
        ref = Decimal(str(refund_amount)).quantize(Decimal("0.01"))
        self.validate_amount(orig)
        if ref > orig:
            raise PaymentValidationError(
                f"Refund amount ${ref:.2f} exceeds original ${orig:.2f}"
            )
        return {
            "refund_amount": ref,
            "remaining_amount": orig - ref,
            "is_full_refund": ref == orig,
        }

    def aggregate_by_customer(self, payments: List[dict]) -> dict:
        """Aggregate payment totals by customer. Returns decimal totals."""
        result: dict = {}
        for p in payments:
            cid = p["customer_id"]
            amt = Decimal(str(p["amount"]))
            if cid not in result:
                result[cid] = {"total_amount": Decimal("0.00"), "count": 0}
            result[cid]["total_amount"] += amt
            result[cid]["count"] += 1
        return result


payment_service = PaymentService()
'''

AFTER_API = '''\
"""
FastAPI payment endpoints.
SYNCHRONIZED BY IBM BOB: handles Decimal amounts and serialization.
"""
from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
import json
import os
from decimal import Decimal

from ..schemas.payment import PaymentCreate, PaymentUpdate, PaymentResponse, PaymentSummary
from ..services.payment_service import payment_service, PaymentValidationError, PaymentNotFoundError

router = APIRouter(prefix="/payments", tags=["payments"])

_payments_store: List[dict] = []
_next_id: int = 1

def _load_fixtures() -> None:
    """Load demo fixtures on startup."""
    global _payments_store, _next_id
    fixture_path = os.path.join(os.path.dirname(__file__), "../../../fixtures/payments.json")
    if os.path.exists(fixture_path):
        with open(fixture_path) as f:
            data = json.load(f)
            raw = data.get("payments", [])
            _payments_store = []
            for p in raw:
                item = dict(p)
                item["amount"] = Decimal(str(item["amount"]))
                _payments_store.append(item)
            if _payments_store:
                _next_id = max(p["id"] for p in _payments_store) + 1


_load_fixtures()


@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(payload: PaymentCreate) -> PaymentResponse:
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
    results = _payments_store
    if customer_id:
        results = [p for p in results if p["customer_id"] == customer_id]
    return [PaymentSummary(**p) for p in results]


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(payment_id: int) -> PaymentResponse:
    payment = next((p for p in _payments_store if p["id"] == payment_id), None)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Payment {payment_id} not found")
    return PaymentResponse(**payment)


@router.patch("/{payment_id}", response_model=PaymentResponse)
async def update_payment(payment_id: int, payload: PaymentUpdate) -> PaymentResponse:
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
    payment = next((p for p in _payments_store if p["id"] == payment_id), None)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Payment {payment_id} not found")
    amount = Decimal(str(payment["amount"]))
    fee = payment_service.calculate_processing_fee(amount)
    net = payment_service.calculate_net_amount(amount)
    return {
        "payment_id": payment_id,
        "gross_amount": float(amount),
        "processing_fee": float(fee),
        "net_amount": float(net),
        "formatted": payment_service.format_amount_display(amount),
    }
'''

AFTER_TYPES = '''\
/**
 * Core Payment domain types.
 * SYNCHRONIZED BY IBM BOB: amount is now decimal dollars (e.g., 99.99).
 */

export type PaymentStatus = 'pending' | 'completed' | 'failed' | 'refunded';

export interface Payment {
  id: number;
  order_id: string;
  customer_id: string;
  amount: number; // decimal dollars (e.g., 99.99)
  currency: string;
  status: PaymentStatus;
  payment_method: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface PaymentSummary {
  id: number;
  order_id: string;
  amount: number; // decimal dollars
  currency: string;
  status: PaymentStatus;
  created_at: string;
}

export interface PaymentCreate {
  order_id: string;
  customer_id: string;
  amount: number; // positive decimal dollar amount
  currency: string;
  payment_method: string;
  description?: string;
}

export interface PaymentUpdate {
  status?: PaymentStatus;
  description?: string;
}

export interface ProcessingFeeResponse {
  payment_id: number;
  gross_amount: number; // decimal dollars
  processing_fee: number; // decimal dollars
  net_amount: number; // decimal dollars
  formatted: string;
}

/**
 * Format decimal dollars to display string.
 * @param dollars - decimal dollar amount (e.g., 99.99)
 * @returns formatted string (e.g., "$99.99")
 */
export function formatAmount(dollars: number): string {
  return `$${Number(dollars).toFixed(2)}`;
}

/**
 * Validate that a payment amount is a positive number.
 * @param amount - value to validate
 * @returns true if valid positive number
 */
export function isValidAmount(amount: number): boolean {
  return typeof amount === 'number' && !isNaN(amount) && amount > 0;
}
'''

AFTER_API_CLIENT = '''\
/**
 * API client for payment service.
 * SYNCHRONIZED BY IBM BOB: supports decimal amounts.
 */

import type {
  Payment,
  PaymentCreate,
  PaymentUpdate,
  PaymentSummary,
  ProcessingFeeResponse,
} from '../types/Payment';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

/**
 * Create a new payment with decimal support.
 * @param data - payment data with decimal dollar amount
 */
export async function createPayment(data: PaymentCreate): Promise<Payment> {
  if (typeof data.amount !== 'number' || isNaN(data.amount) || data.amount <= 0) {
    throw new Error('Payment amount must be a positive number');
  }
  return fetchJson<Payment>(`${BASE_URL}/payments/`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function listPayments(customerId?: string): Promise<PaymentSummary[]> {
  const url = customerId
    ? `${BASE_URL}/payments/?customer_id=${encodeURIComponent(customerId)}`
    : `${BASE_URL}/payments/`;
  return fetchJson<PaymentSummary[]>(url);
}

export async function getPayment(id: number): Promise<Payment> {
  return fetchJson<Payment>(`${BASE_URL}/payments/${id}`);
}

export async function updatePayment(id: number, data: PaymentUpdate): Promise<Payment> {
  return fetchJson<Payment>(`${BASE_URL}/payments/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export async function getProcessingFee(id: number): Promise<ProcessingFeeResponse> {
  return fetchJson<ProcessingFeeResponse>(`${BASE_URL}/payments/${id}/fee`);
}
'''

AFTER_CARD = '''\
/**
 * PaymentCard component.
 * SYNCHRONIZED BY IBM BOB: displays decimal currency and fee calculations.
 */

import React from 'react';
import type { Payment } from '../types/Payment';
import { formatAmount } from '../types/Payment';

interface PaymentCardProps {
  payment: Payment;
  onSelect?: (id: number) => void;
}

const STATUS_STYLES: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  completed: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
  refunded: 'bg-gray-100 text-gray-800',
};

export function PaymentCard({ payment, onSelect }: PaymentCardProps): JSX.Element {
  const amountDisplay = formatAmount(payment.amount);

  // Decimal fee calculation: 2.9% + $0.30
  const feeEstimate = (Number(payment.amount) * 0.029 + 0.30).toFixed(2);
  const netEstimate = (Number(payment.amount) - Number(feeEstimate)).toFixed(2);

  // Validate amount is positive number
  const isValidAmount = typeof payment.amount === 'number' && !isNaN(payment.amount) && payment.amount > 0;

  return (
    <div
      className="border rounded-lg p-4 bg-white shadow-sm hover:shadow-md transition-shadow cursor-pointer"
      onClick={() => onSelect?.(payment.id)}
      data-testid={`payment-card-${payment.id}`}
    >
      <div className="flex justify-between items-start mb-3">
        <div>
          <p className="text-sm text-gray-500">Order #{payment.order_id}</p>
          <p className="text-lg font-semibold text-gray-900">{amountDisplay}</p>
        </div>
        <span
          className={`text-xs px-2 py-1 rounded-full font-medium ${STATUS_STYLES[payment.status] || ''}`}
        >
          {payment.status}
        </span>
      </div>

      <div className="text-xs text-gray-500 space-y-1">
        <p>Customer: {payment.customer_id}</p>
        <p>Method: {payment.payment_method}</p>
        {payment.description && <p>Note: {payment.description}</p>}
      </div>

      <div className="mt-3 pt-3 border-t border-gray-100 text-xs text-gray-400">
        <p>Raw amount: ${Number(payment.amount).toFixed(2)} (decimal)</p>
        <p>Est. fee: ${feeEstimate} | Net: ${netEstimate}</p>
        {!isValidAmount && (
          <p className="text-red-500 font-medium">⚠ Invalid amount detected</p>
        )}
      </div>
    </div>
  );
}

export default PaymentCard;
'''

AFTER_TESTS = '''\
"""
Unit tests for payment service.
SYNCHRONIZED BY IBM BOB: All amounts are decimal dollars.
"""
import pytest
from decimal import Decimal
from backend.services.payment_service import PaymentService, PaymentValidationError
from backend.schemas.payment import PaymentCreate


class TestPaymentValidation:
    """Tests for decimal amount validation logic."""

    def test_valid_integer_amount(self, payment_service: PaymentService) -> None:
        """Valid decimal or int amount accepted."""
        payment_service.validate_amount(Decimal("99.99"))

    def test_amount_below_minimum_raises(self, payment_service: PaymentService) -> None:
        """Amount below $1.00 should raise."""
        with pytest.raises(PaymentValidationError, match="below minimum"):
            payment_service.validate_amount(Decimal("0.50"))

    def test_amount_exceeds_maximum_raises(self, payment_service: PaymentService) -> None:
        """Amount above max ($100,000.00) should raise."""
        with pytest.raises(PaymentValidationError):
            payment_service.validate_amount(Decimal("200000.00"))

    def test_amount_is_integer_type(self, payment_service: PaymentService) -> None:
        """Amount supports Decimal and float precision."""
        payment_service.validate_amount(Decimal("99.99"))
        payment_service.validate_amount(49.95)


class TestProcessingFee:
    """Tests for fee calculation on decimal dollar amounts."""

    def test_fee_calculation_small_amount(self, payment_service: PaymentService) -> None:
        """Fee for $9.99."""
        fee = payment_service.calculate_processing_fee(Decimal("9.99"))
        assert fee == Decimal("0.59")
        assert isinstance(fee, Decimal)

    def test_fee_calculation_large_amount(self, payment_service: PaymentService) -> None:
        """Fee for $100.00."""
        fee = payment_service.calculate_processing_fee(Decimal("100.00"))
        assert fee == Decimal("3.20")
        assert isinstance(fee, Decimal)

    def test_net_amount_is_integer(self, payment_service: PaymentService) -> None:
        """Net amount after fee must be Decimal."""
        net = payment_service.calculate_net_amount(Decimal("99.99"))
        assert isinstance(net, Decimal)
        assert net > Decimal("0")


class TestAmountFormatting:
    """Tests for display formatting of decimal dollar amounts."""

    def test_format_whole_dollars(self, payment_service: PaymentService) -> None:
        assert payment_service.format_amount_display(Decimal("100.00")) == "$100.00"

    def test_format_with_cents(self, payment_service: PaymentService) -> None:
        assert payment_service.format_amount_display(Decimal("99.99")) == "$99.99"

    def test_format_small_amount(self, payment_service: PaymentService) -> None:
        assert payment_service.format_amount_display(Decimal("1.00")) == "$1.00"


class TestPaymentCreation:
    """Tests for payment data preparation."""

    def test_create_payment_returns_integer_amount(
        self, payment_service: PaymentService, sample_payment_create: PaymentCreate
    ) -> None:
        result = payment_service.create_payment(sample_payment_create)
        assert result["amount"] == Decimal("99.99")
        assert isinstance(result["amount"], Decimal)

    def test_create_payment_has_required_fields(
        self, payment_service: PaymentService, sample_payment_create: PaymentCreate
    ) -> None:
        result = payment_service.create_payment(sample_payment_create)
        required = ["order_id", "customer_id", "amount", "currency", "status", "payment_method"]
        for field in required:
            assert field in result


class TestRefund:
    """Tests for refund logic using decimal dollar amounts."""

    def test_full_refund(self, payment_service: PaymentService) -> None:
        result = payment_service.process_refund(Decimal("99.99"), Decimal("99.99"))
        assert result["is_full_refund"] is True
        assert result["remaining_amount"] == Decimal("0.00")

    def test_partial_refund(self, payment_service: PaymentService) -> None:
        result = payment_service.process_refund(Decimal("99.99"), Decimal("50.00"))
        assert result["is_full_refund"] is False
        assert result["remaining_amount"] == Decimal("49.99")

    def test_refund_exceeds_original_raises(self, payment_service: PaymentService) -> None:
        with pytest.raises(PaymentValidationError, match="exceeds original"):
            payment_service.process_refund(Decimal("99.99"), Decimal("100.00"))


class TestAggregation:
    """Tests for aggregation logic with decimal amounts."""

    def test_aggregate_sums_integer_amounts(self, payment_service: PaymentService) -> None:
        payments = [
            {"customer_id": "c1", "amount": Decimal("10.00")},
            {"customer_id": "c1", "amount": Decimal("20.50")},
            {"customer_id": "c2", "amount": Decimal("5.25")},
        ]
        result = payment_service.aggregate_by_customer(payments)
        assert result["c1"]["total_amount"] == Decimal("30.50")
        assert result["c1"]["count"] == 2
        assert result["c2"]["total_amount"] == Decimal("5.25")
        assert result["c2"]["count"] == 1

    def test_fixtures_have_integer_amounts(self) -> None:
        import json, os
        path = os.path.join(os.path.dirname(__file__), "../fixtures/payments.json")
        with open(path) as f:
            data = json.load(f)
        for p in data["payments"]:
            assert isinstance(p["amount"], (float, int)), f"Payment {p['id']} has invalid amount"


class TestSchemaValidation:
    """Tests for Pydantic schema validation."""

    def test_valid_payment_schema(self, sample_payment_create: PaymentCreate) -> None:
        assert sample_payment_create.amount == Decimal("99.99")
        assert sample_payment_create.order_id == "ord-test-001"

    def test_schema_rejects_zero_amount(self) -> None:
        with pytest.raises(Exception):
            PaymentCreate(
                order_id="ord-002",
                customer_id="cust-002",
                amount=Decimal("0.00"),
                currency="USD",
                payment_method="card",
            )
'''

AFTER_CONFTEST = '''\
"""Pytest configuration and shared fixtures for demo-repo tests."""
import pytest
import json
import os
import sys
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.schemas.payment import PaymentCreate, PaymentStatus
from backend.services.payment_service import PaymentService


@pytest.fixture
def payment_service() -> PaymentService:
    return PaymentService()


@pytest.fixture
def sample_payment_create() -> PaymentCreate:
    return PaymentCreate(
        order_id="ord-test-001",
        customer_id="cust-test-001",
        amount=Decimal("99.99"),  # decimal dollars
        currency="USD",
        payment_method="card",
        description="Test payment",
    )


@pytest.fixture
def payment_fixtures() -> list:
    fixture_path = os.path.join(os.path.dirname(__file__), "../fixtures/payments.json")
    with open(fixture_path) as f:
        data = json.load(f)
    return data["payments"]
'''

AFTER_TEST_API = '''\
"""
Integration tests for payment API endpoints.
SYNCHRONIZED BY IBM BOB: tests decimal amounts and responses.
"""
import pytest
from fastapi.testclient import TestClient
import sys
import os
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.main import app

client = TestClient(app)


class TestCreatePayment:
    def test_create_valid_payment(self) -> None:
        response = client.post(
            "/api/v1/payments/",
            json={
                "order_id": "ord-api-001",
                "customer_id": "cust-api-001",
                "amount": "99.99",
                "currency": "USD",
                "payment_method": "card",
                "description": "API test payment",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert float(data["amount"]) == 99.99

    def test_create_payment_missing_amount(self) -> None:
        response = client.post(
            "/api/v1/payments/",
            json={
                "order_id": "ord-api-002",
                "customer_id": "cust-api-002",
                "payment_method": "card",
            },
        )
        assert response.status_code == 422

    def test_create_payment_negative_amount(self) -> None:
        response = client.post(
            "/api/v1/payments/",
            json={
                "order_id": "ord-api-003",
                "customer_id": "cust-api-003",
                "amount": "-1.00",
                "currency": "USD",
                "payment_method": "card",
            },
        )
        assert response.status_code == 422


class TestListPayments:
    def test_list_returns_array(self) -> None:
        response = client.get("/api/v1/payments/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_amounts_are_integers(self) -> None:
        response = client.get("/api/v1/payments/")
        assert response.status_code == 200
        payments = response.json()
        for p in payments:
            assert float(p["amount"]) > 0


class TestGetPayment:
    def test_get_payment_amount_is_integer(self) -> None:
        create_resp = client.post(
            "/api/v1/payments/",
            json={
                "order_id": "ord-get-001",
                "customer_id": "cust-get-001",
                "amount": "50.00",
                "currency": "USD",
                "payment_method": "card",
            },
        )
        assert create_resp.status_code == 201
        payment_id = create_resp.json()["id"]

        get_resp = client.get(f"/api/v1/payments/{payment_id}")
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert float(data["amount"]) == 50.00

    def test_get_nonexistent_payment(self) -> None:
        response = client.get("/api/v1/payments/99999")
        assert response.status_code == 404


class TestProcessingFee:
    def test_fee_response_has_integer_amounts(self) -> None:
        response = client.get("/api/v1/payments/1/fee")
        assert response.status_code == 200
        data = response.json()
        assert "gross_amount" in data
        assert "processing_fee" in data
        assert "net_amount" in data
        assert data["formatted"].startswith("$")
'''

AFTER_FIXTURES = '''\
{
  "payments": [
    {
      "id": 1,
      "order_id": "ord-001",
      "customer_id": "cust-001",
      "amount": 99.99,
      "currency": "USD",
      "status": "completed",
      "payment_method": "card",
      "description": "Premium subscription",
      "created_at": "2024-01-15T10:30:00",
      "updated_at": "2024-01-15T10:30:05"
    },
    {
      "id": 2,
      "order_id": "ord-002",
      "customer_id": "cust-002",
      "amount": 49.99,
      "currency": "USD",
      "status": "completed",
      "payment_method": "bank_transfer",
      "description": "Basic plan",
      "created_at": "2024-01-15T11:00:00",
      "updated_at": "2024-01-15T11:00:08"
    },
    {
      "id": 3,
      "order_id": "ord-003",
      "customer_id": "cust-001",
      "amount": 15.00,
      "currency": "USD",
      "status": "pending",
      "payment_method": "card",
      "description": "Add-on purchase",
      "created_at": "2024-01-16T09:00:00",
      "updated_at": "2024-01-16T09:00:00"
    },
    {
      "id": 4,
      "order_id": "ord-004",
      "customer_id": "cust-003",
      "amount": 250.00,
      "currency": "USD",
      "status": "failed",
      "payment_method": "card",
      "description": "Enterprise license",
      "created_at": "2024-01-16T14:00:00",
      "updated_at": "2024-01-16T14:00:03"
    }
  ]
}
'''

MIGRATION_002 = '''\
-- Migration 002: Update payment amount from INTEGER cents to NUMERIC(10,2) dollars
-- Generated automatically by ReleaseShield (IBM Bob Multi-File Remediation)

ALTER TABLE payments ALTER COLUMN amount TYPE NUMERIC(10, 2) USING (amount::numeric / 100.0);
COMMENT ON COLUMN payments.amount IS 'Payment amount stored as decimal currency (e.g. 99.99)';
'''


# Map of files to update during remediation
REMEDIATION_FILES: Dict[str, str] = {
    "backend/schemas/payment.py": AFTER_SCHEMA,
    "backend/services/payment_service.py": AFTER_SERVICE,
    "backend/api/payments.py": AFTER_API,
    "frontend/src/types/Payment.ts": AFTER_TYPES,
    "frontend/src/api/payments.ts": AFTER_API_CLIENT,
    "frontend/src/components/PaymentCard.tsx": AFTER_CARD,
    "tests/test_payments.py": AFTER_TESTS,
    "tests/test_payment_api.py": AFTER_TEST_API,
    "tests/conftest.py": AFTER_CONFTEST,
    "fixtures/payments.json": AFTER_FIXTURES,
    "migrations/002_update_payment_amount_to_numeric.sql": MIGRATION_002,
}

BEFORE_TEST_API = '''\
"""
Integration tests for payment API endpoints.
Tests the FastAPI routes with in-memory store.
"""
import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.main import app

client = TestClient(app)


class TestCreatePayment:
    def test_create_valid_payment(self) -> None:
        response = client.post(
            "/api/v1/payments/",
            json={
                "order_id": "ord-api-001",
                "customer_id": "cust-api-001",
                "amount": 9999,
                "currency": "USD",
                "payment_method": "card",
                "description": "API test payment",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["amount"] == 9999
        assert isinstance(data["amount"], int)

    def test_create_payment_missing_amount(self) -> None:
        response = client.post(
            "/api/v1/payments/",
            json={
                "order_id": "ord-api-002",
                "customer_id": "cust-api-002",
                "payment_method": "card",
            },
        )
        assert response.status_code == 422

    def test_create_payment_negative_amount(self) -> None:
        response = client.post(
            "/api/v1/payments/",
            json={
                "order_id": "ord-api-003",
                "customer_id": "cust-api-003",
                "amount": -100,
                "currency": "USD",
                "payment_method": "card",
            },
        )
        assert response.status_code == 422


class TestListPayments:
    def test_list_returns_array(self) -> None:
        response = client.get("/api/v1/payments/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_amounts_are_integers(self) -> None:
        response = client.get("/api/v1/payments/")
        assert response.status_code == 200
        payments = response.json()
        for p in payments:
            assert isinstance(p["amount"], int)


class TestGetPayment:
    def test_get_payment_amount_is_integer(self) -> None:
        create_resp = client.post(
            "/api/v1/payments/",
            json={
                "order_id": "ord-get-001",
                "customer_id": "cust-get-001",
                "amount": 5000,
                "currency": "USD",
                "payment_method": "card",
            },
        )
        assert create_resp.status_code == 201
        payment_id = create_resp.json()["id"]

        get_resp = client.get(f"/api/v1/payments/{payment_id}")
        assert get_resp.status_code == 200
        assert isinstance(get_resp.json()["amount"], int)

    def test_get_nonexistent_payment(self) -> None:
        response = client.get("/api/v1/payments/99999")
        assert response.status_code == 404


class TestProcessingFee:
    def test_fee_response_has_integer_amounts(self) -> None:
        create_resp = client.post(
            "/api/v1/payments/",
            json={
                "order_id": "ord-fee-001",
                "customer_id": "cust-fee-001",
                "amount": 10000,
                "currency": "USD",
                "payment_method": "card",
            },
        )
        assert create_resp.status_code == 201
        payment_id = create_resp.json()["id"]

        fee_resp = client.get(f"/api/v1/payments/{payment_id}/fee")
        assert fee_resp.status_code == 200
        data = fee_resp.json()
        assert isinstance(data["gross_amount"], int)
        assert isinstance(data["processing_fee"], int)
        assert isinstance(data["net_amount"], int)
'''

# Map of files to restore during reset
RESET_FILES: Dict[str, str] = {
    "backend/models/payment.py": BEFORE_MODEL,
    "backend/schemas/payment.py": BEFORE_SCHEMA,
    "backend/services/payment_service.py": BEFORE_SERVICE,
    "backend/api/payments.py": BEFORE_API,
    "frontend/src/types/Payment.ts": BEFORE_TYPES,
    "frontend/src/api/payments.ts": BEFORE_API_CLIENT,
    "frontend/src/components/PaymentCard.tsx": BEFORE_CARD,
    "tests/test_payments.py": BEFORE_TESTS,
    "tests/test_payment_api.py": BEFORE_TEST_API,
    "tests/conftest.py": BEFORE_CONFTEST,
    "fixtures/payments.json": BEFORE_FIXTURES,
}


def apply_remediation(repo_path: str) -> List[str]:
    """Apply coherent multi-file changes to repo_path. Returns list of modified paths."""
    base = Path(repo_path)
    modified = []
    for rel_path, content in REMEDIATION_FILES.items():
        file_path = base / rel_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        modified.append(rel_path)
    return modified


def apply_reset(repo_path: str) -> List[str]:
    """Reset all files to BEFORE state. Returns list of restored paths."""
    base = Path(repo_path)
    restored = []
    for rel_path, content in RESET_FILES.items():
        file_path = base / rel_path
        if file_path.exists():
            file_path.write_text(content, encoding="utf-8")
            restored.append(rel_path)

    # Remove migration 002 if present
    mig2 = base / "migrations" / "002_update_payment_amount_to_numeric.sql"
    if mig2.exists():
        mig2.unlink()
        restored.append("migrations/002_update_payment_amount_to_numeric.sql (deleted)")

    # Remove backup files
    for bak in base.rglob("*.bak"):
        bak.unlink()

    return restored
