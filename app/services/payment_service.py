import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from app.repositories.payment_repo import PaymentRepository
from app.models.payment import Payment
from app.models.outbox import OutboxEvent
from app.schemas.payment import PaymentCreate


class PaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = PaymentRepository(db)

    async def process_payment_creation(self, idempotency_key: str, payment_in: PaymentCreate) -> Payment:
        """
        Атомарно создает платеж и событие outbox.
        Обрабатывает идемпотентность для предотвращения дублирования платежей.
        """
        # 1. Проверка идемпотентности (защита от дублей)
        existing_payment = await self.repo.get_by_idempotency_key(idempotency_key)
        if existing_payment:
            return existing_payment

        # 2. Создание объекта платежа
        new_payment = Payment(
            idempotency_key=idempotency_key,
            amount=payment_in.amount,
            currency=payment_in.currency,
            description=payment_in.description,
            metadata_info=payment_in.metadata_info,
            webhook_url=str(payment_in.webhook_url)
        )
        self.repo.add_payment(new_payment)

        # Делаем flush, чтобы получить сгенерированный ID платежа перед коммитом
        await self.db.flush()

        # 3. Создание события Outbox (Паттерн Outbox)
        outbox_event = OutboxEvent(
            event_type="payment.new",
            payload={"payment_id": str(new_payment.id)}
        )
        self.repo.add_outbox_event(outbox_event)

        # 4. Атомарный коммит транзакции
        try:
            await self.db.commit()
            await self.db.refresh(new_payment)
            return new_payment
        except IntegrityError:
            # Защита от состояния гонки: если два одинаковых запроса прошли первую проверку одновременно
            await self.db.rollback()
            return await self.repo.get_by_idempotency_key(idempotency_key)

    async def get_payment(self, payment_id: uuid.UUID) -> Payment | None:
        return await self.repo.get_by_id(payment_id)
