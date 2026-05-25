import json
import logging
import os
import threading
from typing import Any

import pika
from flask import Flask
from neo4j import GraphDatabase

from flasgger import Swagger

from src.infrastructure.adapters.http.api import api_bp
from src.infrastructure.adapters.http.health import health_bp
from src.infrastructure.adapters.neo4j.repositorio_cliente import (
    Neo4jClienteRepository,
)
from src.infrastructure.adapters.neo4j.repositorio_planilla import (
    Neo4jPlanillaRepository,
)
from src.infrastructure.adapters.neo4j.repositorio_vehiculo import (
    Neo4jVehiculoRepository,
)
from src.infrastructure.adapters.rabbitmq.consumidor import (
    EXCHANGE_NAME,
    EXCHANGE_TYPE,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def _rabbitmq_params() -> pika.ConnectionParameters | pika.URLParameters:
    uri = os.environ.get("RABBITMQ_URI")
    if uri:
        return pika.URLParameters(uri)

    host = os.environ.get("RABBITMQ_HOST", "100.94.204.56")
    port = int(os.environ.get("RABBITMQ_PORT", "5672"))
    user = os.environ.get("RABBITMQ_USER", "guest")
    password = os.environ.get("RABBITMQ_PASSWORD", "guest")

    credentials = pika.PlainCredentials(user, password)
    return pika.ConnectionParameters(
        host=host,
        port=port,
        credentials=credentials,
        heartbeat=600,
        blocked_connection_timeout=300,
    )


def _rabbitmq_queue() -> str:
    return os.environ.get("RABBITMQ_QUEUE", "tracker_service.queue")


def _neo4j_config() -> dict[str, Any]:
    return {
        "uri": os.environ.get("NEO4J_URI", "bolt://100.94.204.56:7687"),
        "user": os.environ.get("NEO4J_USER", "neo4j"),
        "password": os.environ.get("NEO4J_PASSWORD", "password"),
    }


def create_app() -> Flask:
    app = Flask(__name__)

    neo4j_cfg = _neo4j_config()
    driver = GraphDatabase.driver(
        neo4j_cfg["uri"],
        auth=(neo4j_cfg["user"], neo4j_cfg["password"]),
    )
    app.extensions["neo4j_driver"] = driver

    cliente_repo = Neo4jClienteRepository(driver)
    vehiculo_repo = Neo4jVehiculoRepository(driver)
    planilla_repo = Neo4jPlanillaRepository(driver)

    app.extensions["cliente_repo"] = cliente_repo
    app.extensions["vehiculo_repo"] = vehiculo_repo
    app.extensions["planilla_repo"] = planilla_repo

    app.extensions["rabbitmq_params"] = _rabbitmq_params()
    app.extensions["rabbitmq_queue"] = _rabbitmq_queue()

    app.register_blueprint(health_bp)
    app.register_blueprint(api_bp)

    Swagger(app, template={
        "swagger": "2.0",
        "info": {
            "title": "Tracker Service - Trazabilidad CDA",
            "description": "API de consulta del grafo relacional de Clientes, Vehículos y Planillas de inspección. Proyección de datos del sistema CDA.",
            "version": "1.0.0",
        },
        "basePath": "/api",
        "schemes": ["http", "https"],
        "securityDefinitions": {
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "description": "Ingresa la API Key si está configurada en el entorno. Si no hay API Key configurada, este campo puede dejarse vacío.",
            },
        },
        "security": [{"ApiKeyAuth": []}],
    })

    return app


def _iniciar_consumo_rabbitmq(app: Flask) -> None:
    connection_params: pika.ConnectionParameters = app.extensions["rabbitmq_params"]
    queue_name: str = app.extensions["rabbitmq_queue"]
    cliente_repo: Neo4jClienteRepository = app.extensions["cliente_repo"]
    vehiculo_repo: Neo4jVehiculoRepository = app.extensions["vehiculo_repo"]
    planilla_repo: Neo4jPlanillaRepository = app.extensions["planilla_repo"]

    def procesar_cliente_registro(datos: dict[str, Any]) -> None:
        from src.domain.models.cliente import Cliente

        cliente = Cliente(
            id=datos["id"],
            nombres=datos["nombres"],
            documento=datos["documento"],
        )
        cliente_repo.crear(cliente)
        logger.info("Cliente %s creado en el grafo", cliente.id)

    def procesar_vehiculo_registro(datos: dict[str, Any]) -> None:
        from src.application.use_cases.procesar_evento_vehiculo import (
            ProcesarEventoVehiculoCreado,
        )

        use_case = ProcesarEventoVehiculoCreado(cliente_repo, vehiculo_repo)
        use_case.ejecutar(datos)
        logger.info("Vehículo %s creado en el grafo", datos["placa"])

    def procesar_planilla_completada(datos: dict[str, Any]) -> None:
        from src.domain.models.defecto import Defecto
        from src.domain.models.planilla import Planilla

        defectos = tuple(
            Defecto(codigo_ntc5375=d["codigo_ntc5375"])
            for d in datos.get("defectos", [])
        )
        planilla = Planilla(
            id=datos["id"],
            vehiculo_placa=datos["vehiculo_placa"],
            defectos=defectos,
        )
        planilla_repo.crear(planilla)
        logger.info("Planilla %s creada en el grafo", planilla.id)

    bindings = {
        "cliente.registro.creado": procesar_cliente_registro,
        "vehiculo.registro.creado": procesar_vehiculo_registro,
        "inspeccion.planilla.completada": procesar_planilla_completada,
    }

    connection = pika.BlockingConnection(connection_params)
    channel = connection.channel()
    channel.exchange_declare(
        exchange=EXCHANGE_NAME,
        exchange_type=EXCHANGE_TYPE,
        durable=True,
    )

    channel.queue_declare(queue=queue_name, durable=True)
    for routing_key in bindings:
        channel.queue_bind(
            queue=queue_name,
            exchange=EXCHANGE_NAME,
            routing_key=routing_key,
        )

    def on_message(
        _channel: Any,
        _method: Any,
        _properties: Any,
        body: bytes,
    ) -> None:
        try:
            datos = json.loads(body.decode("utf-8"))
            routing_key = _method.routing_key
            logger.info("Evento recibido con routing_key=%s", routing_key)
            callback = bindings.get(routing_key)
            if callback is None:
                logger.warning("No hay handler para routing_key=%s", routing_key)
                _channel.basic_nack(delivery_tag=_method.delivery_tag, requeue=False)
                return
            callback(datos)
            _channel.basic_ack(delivery_tag=_method.delivery_tag)
        except Exception:
            logger.exception("Error procesando evento %s", _method.routing_key)
            _channel.basic_nack(
                delivery_tag=_method.delivery_tag,
                requeue=False,
            )

    channel.basic_consume(
        queue=queue_name,
        on_message_callback=on_message,
    )

    logger.info("Iniciando consumo de eventos en %s ...", queue_name)
    channel.start_consuming()


def main() -> None:
    app = create_app()

    rabbitmq_thread = threading.Thread(
        target=_iniciar_consumo_rabbitmq,
        args=(app,),
        daemon=True,
    )
    rabbitmq_thread.start()

    host = os.environ.get("FLASK_HOST", "0.0.0.0")
    port = int(os.environ.get("FLASK_PORT", "5000"))
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    main()
