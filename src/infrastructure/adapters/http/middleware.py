import os
from functools import wraps

from flask import current_app, jsonify, request


def _api_key_valida() -> bool:
    api_key_config = os.environ.get("API_KEY", "")
    if not api_key_config:
        return True
    header_key = request.headers.get("X-API-Key", "")
    return header_key == api_key_config


def requerir_api_key(f):
    @wraps(f)
    def decorada(*args, **kwargs):
        if not _api_key_valida():
            return jsonify({"error": "No autorizado"}), 401
        return f(*args, **kwargs)
    return decorada


def registrar_middleware(blueprint):
    @blueprint.before_request
    def validar_api_key():
        api_key_config = os.environ.get("API_KEY", "")
        if not api_key_config:
            return
        header_key = request.headers.get("X-API-Key", "")
        if header_key != api_key_config:
            return jsonify({"error": "No autorizado"}), 401
