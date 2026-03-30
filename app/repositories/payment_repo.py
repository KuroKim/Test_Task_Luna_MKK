import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.payment import Payment
from app.models.outbox import OutboxEvent


class PaymentRepository:
    """
    Репозиторий для работы с базой данных (платежи и события outbox).
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_idempotency_key(self, key: str) -> Optional[Payment]:
        query = select(Payment).where(Payment.idempotency_key == key)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id(self, payment_id: uuid.UUID) -> Optional[Payment]:
        query = select(Payment).where(Payment.id == payment_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    def add_payment(self, payment: Payment) -> None:
        self.session.add(payment)

    def add_outbox_event(self, event: OutboxEvent) -> None:
        self.session.add(event)
