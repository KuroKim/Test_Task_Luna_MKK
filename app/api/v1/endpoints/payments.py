import uuid
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.api.deps import verify_api_key
from app.schemas.payment import PaymentCreate, PaymentResponse, PaymentDetailResponse
from app.services.payment_service import PaymentService

# Все эндпоинты в этом роутере требуют наличия заголовка X-API-Key
router = APIRouter(dependencies=[Depends(verify_api_key)])


@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_payment(
        payment_in: PaymentCreate,
        idempotency_key: str = Header(..., alias="Idempotency-Key",
                                      description="Уникальный ключ для защиты от двойных списаний"),
        db: AsyncSession = Depends(get_db)
):
    """
    Асинхронно инициирует процесс платежа.
    Возвращает 202 Accepted, сигнализируя, что запрос принят в очередь на обработку.
    """
    service = PaymentService(db)
    payment = await service.process_payment_creation(idempotency_key, payment_in)
    return payment


@router.get("/{payment_id}", response_model=PaymentDetailResponse)
async def get_payment(
        payment_id: uuid.UUID,
        db: AsyncSession = Depends(get_db)
):
    """
    Возвращает детальную информацию о конкретном платеже.
    """
    service = PaymentService(db)
    payment = await service.get_payment(payment_id)

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Платеж не найден"
        )
    return payment
