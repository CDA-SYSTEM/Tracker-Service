import json
import logging
from collections.abc import Callable
from typing import Any

import pika

from src.domain.ports.event_consumer import EventConsumer

logger = logging.getLogger(__name__)

EXCHANGE_NAME = "cda.domain.events"
EXCHANGE_TYPE = "topic"


class RabbitMQEventConsumer(EventConsumer):

    def __init__(
        self,
        connection_params: pika.ConnectionParameters,
        queue_name: str = "tracker_service.queue",
    ) -> None:
        self._connection_params = connection_params
        self._queue_name = queue_name
        self._connection: pika.BlockingConnection | None = None
        self._channel: pika.adapters.blocking_connection.BlockingChannel | None = None

    def iniciar_consumo(
        self,
        routing_key: str,
        callback: Callable[[dict[str, Any]], None],
    ) -> None:
        self._connection = pika.BlockingConnection(self._connection_params)
        self._channel = self._connection.channel()
        self._channel.exchange_declare(
            exchange=EXCHANGE_NAME,
            exchange_type=EXCHANGE_TYPE,
            durable=True,
        )
        self._channel.queue_declare(queue=self._queue_name, durable=True)
        self._channel.queue_bind(
            queue=self._queue_name,
            exchange=EXCHANGE_NAME,
            routing_key=routing_key,
        )

        def _wrapper(
            _channel: Any,
            _method: Any,
            _properties: Any,
            body: bytes,
        ) -> None:
            try:
                datos = json.loads(body.decode("utf-8"))
                logger.info("Evento recibido con routing_key=%s", routing_key)
                callback(datos)
                _channel.basic_ack(delivery_tag=_method.delivery_tag)
            except Exception:
                logger.exception("Error procesando evento %s", routing_key)
                _channel.basic_nack(
                    delivery_tag=_method.delivery_tag,
                    requeue=False,
                )

        self._channel.basic_consume(
            queue=self._queue_name,
            on_message_callback=_wrapper,
        )
        logger.info(
            "Consumidor iniciado para %s con routing_key=%s",
            self._queue_name,
            routing_key,
        )
        self._channel.start_consuming()

    def detener(self) -> None:
        if self._channel is not None and self._channel.is_open:
            self._channel.stop_consuming()
        if self._connection is not None and self._connection.is_open:
            self._connection.close()
