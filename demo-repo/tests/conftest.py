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
