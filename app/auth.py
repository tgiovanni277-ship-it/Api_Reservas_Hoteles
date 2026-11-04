from functools import wraps
from datetime import datetime, timedelta, timezone

import jwt
from flask import Blueprint, current_app, g, jsonify, request

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Envía un objeto JSON"}), 400
    username = data.get("username")
    password = data.get("clave")
    if not isinstance(username, str) or not isinstance(password, str):
        return jsonify({"error": "username y clave son obligatorios"}), 400
    if (
        username != current_app.config["API_USERNAME"]
        or password != current_app.config["API_PASSWORD"]
    ):
        return jsonify({"error": "Credenciales inválidas"}), 401

    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "user": username,
            "iat": now,
            "exp": now + timedelta(hours=current_app.config["TOKEN_HOURS"]),
        },
        current_app.config["SECRET_KEY"],
        algorithm="HS256",
    )
    return jsonify({
        "token": token,
        "username": username,
    }), 200


def token_required(view):
    @wraps(view)
    def decorated(*args, **kwargs):
        authorization = request.headers.get("Authorization", "")
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return jsonify({"error": "Usa Authorization: Bearer <token>"}), 401
        try:
            g.jwt_payload = jwt.decode(
                parts[1],
                current_app.config["SECRET_KEY"],
                algorithms=["HS256"],
                options={"require": ["exp", "user"]},
            )
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expirado"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Token inválido"}), 401
        return view(*args, **kwargs)
    return decorated


@auth_bp.get("/auth/me")
@token_required
def current_user():
    return jsonify({"username": g.jwt_payload["user"]}), 200
