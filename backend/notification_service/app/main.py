"""Notification service.

В production-архитектуре уведомления отправляются асинхронно через RabbitMQ.
В бета-версии при недоступности брокера сервис корректно деградирует в локальную обработку.
"""

import json
import os
from datetime import datetime, timezone

from fastapi import FastAPI, Query

# FastAPI application for notifications.
app = FastAPI(title="Notification Service")

# RabbitMQ configuration from environment.
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "")
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE", "notifications")


def _publish_to_rabbitmq(payload: dict) -> tuple[bool, str]:
    """Try publishing notification to RabbitMQ.

    Returns:
        tuple[bool, str]: success flag and delivery mode description.
    """
    if not RABBITMQ_URL:
        return False, "local-fallback(no-rabbitmq-url)"

    try:
        import pika  # type: ignore
    except Exception:
        return False, "local-fallback(pika-not-installed)"

    try:
        params = pika.URLParameters(RABBITMQ_URL)
        connection = pika.BlockingConnection(params)
        channel = connection.channel()
        channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
        channel.basic_publish(
            exchange="",
            routing_key=RABBITMQ_QUEUE,
            body=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            properties=pika.BasicProperties(delivery_mode=2),
        )
        connection.close()
        return True, "rabbitmq"
    except Exception as exc:
        # Системная ошибка допускается в бета, но обрабатывается с fallback.
        return False, f"local-fallback(rabbitmq-error:{type(exc).__name__})"


@app.get("/health")
def healthcheck():
    """Basic liveness endpoint with delivery backend info."""
    return {
        "status": "ok",
        "notification_backend": "rabbitmq" if RABBITMQ_URL else "local-fallback",
        "queue": RABBITMQ_QUEUE,
    }


@app.get("/notify")
def notify(event: str = Query(default="order_created", min_length=3)):
    """Prepare notification and send async via RabbitMQ when possible."""
    payload = {
        "event": event,
        "notification": "Событие обработано",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    delivered, mode = _publish_to_rabbitmq(payload)
    payload["delivery_mode"] = mode
    payload["delivered"] = delivered
    return payload
