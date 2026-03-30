import uuid
from decimal import Decimal
from enum import Enum as PyEnum
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Numeric, Enum, JSON, DateTime, func
from app.db.session import Base


class CurrencyEnum(str, PyEnum):
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"


class PaymentStatusEnum(str, PyEnum):
    pending = "pending"
    succeeded = "succeeded"
    failed = "failed"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    # Храним деньги в Decimal (Numeric(10, 2) - до 10 цифр всего, 2 после запятой)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[CurrencyEnum] = mapped_column(Enum(CurrencyEnum), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    # Называем metadata_info, так как слово metadata зарезервировано в SQLAlchemy
    metadata_info: Mapped[dict] = mapped_column(JSON, nullable=True)
    status: Mapped[PaymentStatusEnum] = mapped_column(Enum(PaymentStatusEnum), default=PaymentStatusEnum.pending,
                                                      nullable=False)

    # ГЛАВНАЯ ЗАЩИТА: уникальный ключ идемпотентности
    idempotency_key: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    webhook_url: Mapped[str] = mapped_column(String, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(),
                                                 onupdate=func.now())
