import uuid
from decimal import Decimal
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl
from app.models.payment import CurrencyEnum, PaymentStatusEnum


class PaymentCreate(BaseModel):
    amount: Decimal = Field(..., gt=0, description="Amount must be greater than 0")
    currency: CurrencyEnum
    description: Optional[str] = Field(None, max_length=255)
    metadata_info: Optional[Dict[str, Any]] = Field(None,
                                                    alias="metadata")  # alias позволяет клиенту присылать поле "metadata"
    webhook_url: HttpUrl


class PaymentResponse(BaseModel):
    payment_id: uuid.UUID = Field(alias="id")
    status: PaymentStatusEnum
    created_at: datetime

    class Config:
        populate_by_name = True
        from_attributes = True


class PaymentDetailResponse(PaymentResponse):
    amount: Decimal
    currency: CurrencyEnum
    description: Optional[str]
    metadata_info: Optional[Dict[str, Any]] = Field(None, alias="metadata")
    webhook_url: str
    updated_at: datetime
