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
