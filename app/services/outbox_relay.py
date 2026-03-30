import asyncio
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.outbox import OutboxEvent
from app.core.broker import broker


async def relay_outbox_events():
    """
    Фоновый процесс (Relay), который читает события из таблицы outbox_events
    и гарантированно отправляет их в RabbitMQ.
    """
    while True:
        try:
            async with AsyncSessionLocal() as db:
                # Берем пачку необработанных событий
                query = select(OutboxEvent).where(OutboxEvent.processed == False).limit(100)
                result = await db.execute(query)
                events = result.scalars().all()

                for event in events:
                    # Отправляем полезную нагрузку в очередь "payments.new"
                    await broker.publish(
                        event.payload,
                        queue="payments.new"
                    )
                    # Если отправка успешна, помечаем как обработанное
                    event.processed = True

                # Фиксируем изменения в базе
                if events:
                    await db.commit()

        except Exception as e:
            # Логируем ошибку, но не "роняем" процесс
            print(f"Ошибка в Outbox Relay: {e}")

        # Спим 2 секунды перед следующей проверкой
        await asyncio.sleep(2)
