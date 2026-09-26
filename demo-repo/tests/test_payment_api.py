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
