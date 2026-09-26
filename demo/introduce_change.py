#!/usr/bin/env python3
"""
ReleaseShield Demo: Introduce the deliberate incomplete change.

This script modifies ONLY backend/models/payment.py to change
Payment.amount from Integer to Numeric(precision=10, scale=2).

This creates a repository-wide inconsistency that ReleaseShield
will discover and remediate using IBM Bob.

Usage:
    python demo/introduce_change.py [--repo-path ./demo-repo]

After running this script:
- backend/models/payment.py  → MODIFIED (Integer → Numeric)
- ALL OTHER FILES             → unchanged (inconsistent!)
- pytest tests/               → FAILS (isinstance int checks break)

Then run ReleaseShield to discover and fix the hidden impact.
"""

import os
import sys
import argparse
import shutil
from pathlib import Path

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

AFTER_MODEL = '''\
"""
SQLAlchemy ORM model for Payment.
DEVELOPER CHANGE: amount changed from Integer to Numeric(precision=10, scale=2)
to support decimal payment amounts (e.g., $99.95 stored as 99.95).

This is an INCOMPLETE change — other files still expect integer amounts.
ReleaseShield will discover and remediate the repository-wide impact.
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
    amount = Column(Numeric(precision=10, scale=2), nullable=False)  # CHANGED: decimal dollars
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
            "amount": float(self.amount) if self.amount is not None else None,  # decimal
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


def main():
    parser = argparse.ArgumentParser(description="Introduce the ReleaseShield demo change")
    parser.add_argument(
        "--repo-path",
        default=os.path.join(os.path.dirname(os.path.dirname(__file__)), "demo-repo"),
        help="Path to the demo repository",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without modifying files",
    )
    args = parser.parse_args()

    repo_path = Path(args.repo_path).resolve()
    model_path = repo_path / "backend" / "models" / "payment.py"

    print("=" * 60)
    print("ReleaseShield Demo — Introduce Deliberate Change")
    print("=" * 60)
    print(f"\nRepo:  {repo_path}")
    print(f"File:  {model_path}")
    print()

    if not repo_path.exists():
        print(f"ERROR: Demo repo not found at {repo_path}")
        print("Make sure you are running from the project root.")
        sys.exit(1)

    if not model_path.exists():
        print(f"ERROR: Model file not found at {model_path}")
        sys.exit(1)

    # Verify current content
    current = model_path.read_text(encoding="utf-8")
    if "Numeric(precision=10" in current:
        print("[WARN] Change already introduced.")
        print("   Run 'python demo/reset_demo.py' to restore BEFORE state first.")
        sys.exit(0)

    if "Column(Integer, nullable=False)" not in current:
        print("[WARN] Unexpected file content — may have been manually modified.")
        print("   Run 'python demo/reset_demo.py' to restore BEFORE state.")

    print("CHANGE:")
    print("  BEFORE: amount = Column(Integer, nullable=False)  # stored as cents")
    print("  AFTER:  amount = Column(Numeric(precision=10, scale=2), nullable=False)  # decimal dollars")
    print()
    print("This modifies ONLY one file.")
    print("7+ other files remain inconsistent — ReleaseShield will discover them.")
    print()

    if args.dry_run:
        print("[DRY RUN] No files were modified.")
        return

    # Back up original
    backup_path = model_path.with_suffix(".py.bak")
    shutil.copy2(model_path, backup_path)
    print(f"Backup:  {backup_path}")

    # Write the changed model
    model_path.write_text(AFTER_MODEL, encoding="utf-8")
    print(f"Modified: {model_path}")
    print()
    print("[OK] Change introduced.")
    print()
    print("NEXT STEPS:")
    print("  1. Open IBM Bob IDE and ensure workspace = demo-repo/")
    print("  2. Open ReleaseShield at http://localhost:3000")
    print("  3. Click 'Analyze Release Impact'")
    print("  4. Watch Bob discover the hidden repository-wide impact")
    print()
    print("To reset: python demo/reset_demo.py")


if __name__ == "__main__":
    main()
