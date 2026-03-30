from fastapi import FastAPI
from app.api.api import api_router

app = FastAPI(
    title="Асинхронный процессинг платежей",
    description="Микросервис для асинхронной обработки платежей с использованием паттерна Outbox.",
    version="1.0.0"
)

app.include_router(api_router, prefix="/api/v1")
