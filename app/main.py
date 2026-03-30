from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI
from app.api.api import api_router
from app.core.broker import broker
from app.services.outbox_relay import relay_outbox_events


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Жизненный цикл приложения: действия при старте и остановке.
    """
    # 1. Подключаемся к RabbitMQ
    await broker.connect()

    # 2. Запускаем фоновую задачу отправки событий (Outbox Relay)
    relay_task = asyncio.create_task(relay_outbox_events())

    yield  # В этот момент приложение работает и принимает запросы

    # 3. При выключении сервера отменяем задачу и отключаемся от брокера
    relay_task.cancel()
    await broker.disconnect()


app = FastAPI(
    title="Асинхронный процессинг платежей",
    description="Микросервис для асинхронной обработки платежей с использованием паттерна Outbox.",
    version="1.0.0",
    lifespan=lifespan  # lifespan
)

app.include_router(api_router, prefix="/api/v1")
