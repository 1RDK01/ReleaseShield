#!/usr/bin/env python3
"""
ReleaseShield Demo: Reset to clean BEFORE state.

Restores all demo-repo files to their original (Integer amount) state,
allowing the demonstration to be repeated cleanly.

Usage:
    python demo/reset_demo.py [--repo-path ./demo-repo]
"""

import os
import sys
import argparse
import shutil
from pathlib import Path


# The original BEFORE-state model
ORIGINAL_MODEL = '''\
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

ORIGINAL_SCHEMA = '''\
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

ORIGINAL_SERVICE = '''\
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

ORIGINAL_FIXTURES = '''\
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


def main():
    parser = argparse.ArgumentParser(description="Reset demo-repo to BEFORE state")
    parser.add_argument(
        "--repo-path",
        default=os.path.join(os.path.dirname(os.path.dirname(__file__)), "demo-repo"),
    )
    args = parser.parse_args()

    repo_path = Path(args.repo_path).resolve()
    print("=" * 60)
    print("ReleaseShield Demo — Reset to BEFORE State")
    print("=" * 60)
    print(f"\nRepo: {repo_path}\n")

    # Import apply_reset from backend templates if available
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from backend.remediation_templates import apply_reset
        restored_files = apply_reset(str(repo_path))
        for rf in restored_files:
            print(f"  [OK] Restored: {rf}")
        restored = len(restored_files)
    except Exception as e:
        # Fallback manual restore
        files_to_restore = [
            (repo_path / "backend" / "models" / "payment.py", ORIGINAL_MODEL),
            (repo_path / "backend" / "schemas" / "payment.py", ORIGINAL_SCHEMA),
            (repo_path / "backend" / "services" / "payment_service.py", ORIGINAL_SERVICE),
            (repo_path / "fixtures" / "payments.json", ORIGINAL_FIXTURES),
        ]
        restored = 0
        for path, content in files_to_restore:
            if path.exists():
                path.write_text(content, encoding="utf-8")
                print(f"  [OK] Restored: {path.relative_to(repo_path)}")
                restored += 1
            else:
                print(f"  [WARN] Not found: {path.relative_to(repo_path)}")

    # Remove backup files and migration 002 if present
    for bak in repo_path.rglob("*.py.bak"):
        bak.unlink()
        print(f"  [OK] Removed:  {bak.relative_to(repo_path)}")

    mig2 = repo_path / "migrations" / "002_update_payment_amount_to_numeric.sql"
    if mig2.exists():
        mig2.unlink()
        print("  [OK] Removed:  migrations/002_update_payment_amount_to_numeric.sql")

    print(f"\n[OK] Reset complete. {restored} files restored to BEFORE state.")
    print()
    print("VERIFY:")
    print(f"  cd {repo_path}")
    print("  pytest tests/ -v")
    print("  (All tests should pass)")


if __name__ == "__main__":
    main()
