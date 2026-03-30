from faststream.rabbit import RabbitBroker
from app.core.config import settings

# Инициализируем брокер RabbitMQ
broker = RabbitBroker(settings.RABBITMQ_URL)
