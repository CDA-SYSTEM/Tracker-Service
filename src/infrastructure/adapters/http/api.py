from typing import TYPE_CHECKING

from flask import Blueprint, current_app, jsonify
from flasgger import swag_from

if TYPE_CHECKING:
    from src.domain.ports.repositories import (
        ClienteRepository,
        PlanillaRepository,
        VehiculoRepository,
    )

from src.infrastructure.adapters.http.middleware import registrar_middleware

api_bp = Blueprint("api", __name__, url_prefix="/api")
registrar_middleware(api_bp)


@api_bp.route("/clientes", methods=["GET"])
@swag_from({
    "tags": ["Clientes"],
    "summary": "Listar todos los clientes",
    "responses": {
        "200": {
            "description": "Lista de clientes",
            "schema": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "nombres": {"type": "string"},
                        "documento": {"type": "string"},
                        "total_vehiculos": {"type": "integer"},
                    },
                },
            },
        },
    },
    "security": [{"ApiKeyAuth": []}],
})
def listar_clientes():
    from flask import current_app
    repo: ClienteRepository = current_app.extensions["cliente_repo"]
    clientes = repo.listar()
    resultado = []
    for c in clientes:
        total_v = repo.contar_vehiculos(c.id)
        resultado.append({
            "id": c.id,
            "nombres": c.nombres,
            "documento": c.documento,
            "total_vehiculos": total_v,
        })
    return jsonify(resultado), 200


@api_bp.route("/clientes/<cliente_id>", methods=["GET"])
@swag_from({
    "tags": ["Clientes"],
    "summary": "Obtener cliente por ID",
    "parameters": [
        {"name": "cliente_id", "in": "path", "type": "string", "required": True},
    ],
    "responses": {
        "200": {"description": "Cliente encontrado"},
        "404": {"description": "Cliente no encontrado"},
    },
    "security": [{"ApiKeyAuth": []}],
})
def obtener_cliente(cliente_id: str):
    from flask import current_app
    repo: ClienteRepository = current_app.extensions["cliente_repo"]
    cliente = repo.obtener_por_id(cliente_id)
    if cliente is None:
        return jsonify({"error": "Cliente no encontrado"}), 404
    total_v = repo.contar_vehiculos(cliente.id)
    return jsonify({
        "id": cliente.id,
        "nombres": cliente.nombres,
        "documento": cliente.documento,
        "total_vehiculos": total_v,
    }), 200


@api_bp.route("/clientes/<cliente_id>/vehiculos", methods=["GET"])
@swag_from({
    "tags": ["Clientes"],
    "summary": "Listar vehículos de un cliente",
    "parameters": [
        {"name": "cliente_id", "in": "path", "type": "string", "required": True},
    ],
    "responses": {
        "200": {"description": "Vehículos del cliente"},
        "404": {"description": "Cliente no encontrado"},
    },
    "security": [{"ApiKeyAuth": []}],
})
def listar_vehiculos_cliente(cliente_id: str):
    from flask import current_app
    cliente_repo: ClienteRepository = current_app.extensions["cliente_repo"]
    vehiculo_repo: VehiculoRepository = current_app.extensions["vehiculo_repo"]
    if cliente_repo.obtener_por_id(cliente_id) is None:
        return jsonify({"error": "Cliente no encontrado"}), 404
    vehiculos = vehiculo_repo.obtener_por_cliente(cliente_id)
    return jsonify([
        {
            "placa": v.placa,
            "marca": v.marca,
            "cliente_id": v.cliente_id,
        }
        for v in vehiculos
    ]), 200


@api_bp.route("/vehiculos", methods=["GET"])
@swag_from({
    "tags": ["Vehículos"],
    "summary": "Listar todos los vehículos",
    "responses": {
        "200": {"description": "Lista de vehículos"},
    },
    "security": [{"ApiKeyAuth": []}],
})
def listar_vehiculos():
    from flask import current_app
    repo: VehiculoRepository = current_app.extensions["vehiculo_repo"]
    vehiculos = repo.listar()
    return jsonify([
        {
            "placa": v.placa,
            "marca": v.marca,
            "cliente_id": v.cliente_id,
        }
        for v in vehiculos
    ]), 200


@api_bp.route("/vehiculos/<placa>", methods=["GET"])
@swag_from({
    "tags": ["Vehículos"],
    "summary": "Obtener vehículo por placa",
    "parameters": [
        {"name": "placa", "in": "path", "type": "string", "required": True},
    ],
    "responses": {
        "200": {"description": "Vehículo encontrado"},
        "404": {"description": "Vehículo no encontrado"},
    },
    "security": [{"ApiKeyAuth": []}],
})
def obtener_vehiculo(placa: str):
    from flask import current_app
    repo: VehiculoRepository = current_app.extensions["vehiculo_repo"]
    vehiculo = repo.obtener_por_placa(placa)
    if vehiculo is None:
        return jsonify({"error": "Vehículo no encontrado"}), 404
    return jsonify({
        "placa": vehiculo.placa,
        "marca": vehiculo.marca,
        "cliente_id": vehiculo.cliente_id,
    }), 200


@api_bp.route("/vehiculos/<placa>/planillas", methods=["GET"])
@swag_from({
    "tags": ["Vehículos"],
    "summary": "Listar planillas de inspección de un vehículo",
    "parameters": [
        {"name": "placa", "in": "path", "type": "string", "required": True},
    ],
    "responses": {
        "200": {"description": "Planillas del vehículo"},
    },
    "security": [{"ApiKeyAuth": []}],
})
def listar_planillas_vehiculo(placa: str):
    from flask import current_app
    repo: PlanillaRepository = current_app.extensions["planilla_repo"]
    planillas = repo.obtener_por_vehiculo(placa)
    return jsonify([
        {
            "id": p.id,
            "vehiculo_placa": p.vehiculo_placa,
        }
        for p in planillas
    ]), 200


@api_bp.route("/planillas", methods=["GET"])
@swag_from({
    "tags": ["Planillas"],
    "summary": "Listar todas las planillas de inspección",
    "responses": {
        "200": {"description": "Lista de planillas"},
    },
    "security": [{"ApiKeyAuth": []}],
})
def listar_planillas():
    from flask import current_app
    repo: PlanillaRepository = current_app.extensions["planilla_repo"]
    planillas = repo.listar()
    return jsonify([
        {
            "id": p.id,
            "vehiculo_placa": p.vehiculo_placa,
        }
        for p in planillas
    ]), 200


@api_bp.route("/planillas/<planilla_id>", methods=["GET"])
@swag_from({
    "tags": ["Planillas"],
    "summary": "Obtener planilla con sus defectos",
    "parameters": [
        {"name": "planilla_id", "in": "path", "type": "string", "required": True},
    ],
    "responses": {
        "200": {"description": "Planilla con defectos"},
        "404": {"description": "Planilla no encontrada"},
    },
    "security": [{"ApiKeyAuth": []}],
})
def obtener_planilla(planilla_id: str):
    from flask import current_app
    repo: PlanillaRepository = current_app.extensions["planilla_repo"]
    planilla = repo.obtener_por_id(planilla_id)
    if planilla is None:
        return jsonify({"error": "Planilla no encontrada"}), 404
    defectos = repo.obtener_defectos(planilla_id)
    return jsonify({
        "id": planilla.id,
        "vehiculo_placa": planilla.vehiculo_placa,
        "defectos": [d.codigo_ntc5375 for d in defectos],
    }), 200
