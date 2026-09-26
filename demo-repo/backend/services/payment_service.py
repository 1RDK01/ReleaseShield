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
