import uuid
import asyncio
import random
from httpx import AsyncClient
from pydantic import BaseModel
from faststream import FastStream
from faststream.rabbit import RabbitBroker
from app.db.session import AsyncSessionLocal
from app.models.payment import Payment, PaymentStatusEnum
from app.core.config import settings

# Подключаемся к RabbitMQ
broker = RabbitBroker(settings.RABBITMQ_URL)
app = FastStream(broker)


class PaymentMessage(BaseModel):
    """Схема сообщения, которое мы ждем из RabbitMQ"""
    payment_id: str


async def send_webhook_with_retry(url: str, payload: dict, max_retries: int = 3) -> bool:
    """
    Отправляет Webhook с экспоненциальной задержкой (Exponential Backoff).
    Возвращает True, если успешно, False — если все 3 попытки провалились.
    """
    async with AsyncClient() as client:
        for attempt in range(1, max_retries + 1):
            try:
                # Таймаут 5 сек, чтобы не висеть вечно, если сервер клиента "мертв"
                response = await client.post(url, json=payload, timeout=5.0)
                response.raise_for_status()  # Проверка, что статус 2xx
                print(f"[WEBHOOK] ✅ Успешно отправлено на {url} (попытка {attempt})")
                return True
            except Exception as e:
                print(f"[WEBHOOK] ⚠️ Ошибка отправки на {url}: {e}")
                if attempt < max_retries:
                    delay = 2 ** attempt  # Экспоненциальная задержка: 2 сек, 4 сек...
                    print(f"[WEBHOOK] ⏳ Ждем {delay} сек. перед повтором...")
                    await asyncio.sleep(delay)
    return False


@broker.subscriber("payments.new")
async def process_payment(msg: PaymentMessage):
    """
    Главный обработчик. Читает очередь, эмулирует банк и шлет вебхук.
    """
    print(f"\n[WORKER] 📥 Получено сообщение для платежа: {msg.payment_id}")

    async with AsyncSessionLocal() as db:
        # Ищем платеж в базе
        payment_uuid = uuid.UUID(msg.payment_id)
        payment = await db.get(Payment, payment_uuid)

        if not payment or payment.status != PaymentStatusEnum.pending:
            print(f"[WORKER] ❌ Платеж {msg.payment_id} не найден или уже обработан.")
            return

        # 1. Эмуляция обработки в банковском шлюзе (2-5 сек)
        processing_time = random.uniform(2.0, 5.0)
        print(f"[WORKER] 🏦 Эмуляция обработки в банке ({processing_time:.1f} сек)...")
        await asyncio.sleep(processing_time)

        # 2. Шанс успеха 90%
        is_success = random.random() < 0.9
        payment.status = PaymentStatusEnum.succeeded if is_success else PaymentStatusEnum.failed
        await db.commit()
        print(f"[WORKER] 💾 Платеж завершен. Новый статус: {payment.status.value}")

        # 3. Отправка Webhook уведомления клиенту
        webhook_payload = {
            "payment_id": str(payment.id),
            "status": payment.status.value,
            "amount": float(payment.amount),
            "currency": payment.currency.value,
            "metadata": payment.metadata_info
        }

        is_webhook_sent = await send_webhook_with_retry(payment.webhook_url, webhook_payload)

        # 4. Dead Letter Queue (DLQ)
        # Если после 3 попыток вебхук не дошел, отправляем сообщение в очередь "мертвых писем"
        if not is_webhook_sent:
            print(f"[DLQ] 💀 Webhook окончательно недоступен. Переносим {msg.payment_id} в DLQ.")
            await broker.publish(
                {"payment_id": msg.payment_id, "reason": "webhook_failed", "url": payment.webhook_url},
                queue="payments.dlq"
            )
