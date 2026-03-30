
# Async Payment Processor

Микросервис для асинхронной обработки платежей с гарантиями доставки (Reliability) и защитой от дублей.

## 🚀 Особенности архитектуры

- **Outbox Pattern:** Гарантированная доставка событий в RabbitMQ. Создание платежа и запись события в таблицу `outbox_events` происходят в единой транзакции БД. Отдельный фоновый процесс (Relay) читает таблицу и отправляет сообщения в брокер.
- **Идемпотентность (Idempotency):** Защита от дублирования платежей (например, при повторном клике или обрыве сети) реализована на уровне базы данных (`UNIQUE` индекс) с обработкой `IntegrityError`.
- **Exponential Backoff & Retry:** Воркер делает 3 попытки отправки Webhook-уведомления с нарастающей задержкой (2с -> 4с).
- **Dead Letter Queue (DLQ):** Если webhook-сервер клиента окончательно недоступен, сообщение безопасно переносится в очередь `payments.dlq` для ручного разбора.
- **FastStream:** Современный и быстрый фреймворк для работы с RabbitMQ.

## 🛠 Технологический стек
- Python 3.12, FastAPI, Pydantic v2
- PostgreSQL 15, SQLAlchemy 2.0 (Async), Alembic
- RabbitMQ, FastStream
- Docker, Docker Compose

## ⚡️ Запуск проекта

Проект полностью контейнеризирован. Для запуска достаточно одной команды.

1. **Клонируйте репозиторий:**
   ```bash
   git clone https://github.com/KuroKim/Test_Task_Luna_MKK
   cd Test_Task_Luna_MKK
   ```

2. **Запустите Docker Compose:**
   ```bash
   docker-compose up --build -d
   ```
   *Контейнер `api` автоматически дождется поднятия БД и применит все миграции Alembic.*

3. **Доступные сервисы:**
   - **Swagger UI (API):**[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
   - **RabbitMQ Management:**[http://127.0.0.1:15672](http://127.0.0.1:15672) (login: `rmuser`, password: `rmpassword`)

## 🧪 Как тестировать

Для всех запросов к API необходим заголовок `X-API-Key`.
**Тестовый ключ:** `my_super_secret_api_key`

1. Откройте Swagger UI и нажмите кнопку **Authorize**, введите ключ.
2. Выполните `POST /api/v1/payments/`, указав уникальный заголовок `Idempotency-Key` (например, `test-pay-1`).
3. В теле запроса укажите `webhook_url` (рекомендуется использовать временный URL с [webhook.site](https://webhook.site/)).
4. Убедитесь, что API моментально возвращает `202 Accepted`.
5. Посмотрите логи воркера, чтобы увидеть процесс эмуляции и отправки вебхука:
   ```bash
   docker-compose logs -f worker
   ```
