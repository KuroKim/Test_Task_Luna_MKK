from fastapi import APIRouter
from app.api.v1.endpoints import payments

api_router = APIRouter()
api_router.include_router(payments.router, prefix="/payments", tags=["Платежи (Payments)"])
