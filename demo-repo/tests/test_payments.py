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
