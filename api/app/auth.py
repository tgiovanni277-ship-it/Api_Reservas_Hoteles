from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import Blueprint, current_app, g, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from app.db import get_db

auth_bp = Blueprint("auth", __name__)


def _issue_token(identity, status=200):
    now = datetime.now(timezone.utc)
    claims = {
        "user": identity["username"],
        "name": identity["name"],
        "email": identity.get("email"),
        "role": identity["role"],
        "user_id": identity.get("user_id"),
        "iat": now,
        "exp": now + timedelta(hours=current_app.config["TOKEN_HOURS"]),
    }
    token = jwt.encode(claims, current_app.config["SECRET_KEY"], algorithm="HS256")
    return jsonify({
        "token": token,
        "username": identity["username"],
        "name": identity["name"],
        "email": identity.get("email"),
        "role": identity["role"],
    }), status


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Envía un objeto JSON"}), 400

    name = data.get("huesped")
    email = data.get("correo")
    password = data.get("clave")
    if not isinstance(name, str) or not name.strip() or len(name.strip()) > 120:
        return jsonify({"error": "huesped debe tener entre 1 y 120 caracteres"}), 400
    if not isinstance(email, str) or "@" not in email or len(email) > 254:
        return jsonify({"error": "correo debe tener un formato válido"}), 400
    if not isinstance(password, str) or len(password) < 8 or len(password) > 128:
        return jsonify({"error": "La contraseña debe tener entre 8 y 128 caracteres"}), 400

    normalized_email = email.strip().lower()
    if normalized_email.startswith("@") or normalized_email.endswith("@"):
        return jsonify({"error": "correo debe tener un formato válido"}), 400

    try:
        with get_db() as connection:
            cursor = connection.execute(
                """
                INSERT INTO usuarios (nombre, correo, password_hash, role)
                VALUES (?, ?, ?, 'user')
                """,
                (name.strip(), normalized_email, generate_password_hash(password)),
            )
            user_id = cursor.lastrowid
    except Exception as error:
        if "UNIQUE constraint failed" in str(error):
            return jsonify({"error": "Ya existe una cuenta con ese correo"}), 409
        raise

    return _issue_token({
        "username": normalized_email,
        "name": name.strip(),
        "email": normalized_email,
        "role": "user",
        "user_id": user_id,
    }, status=201)


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Envía un objeto JSON"}), 400
    identifier = data.get("username")
    password = data.get("clave")
    if not isinstance(identifier, str) or not isinstance(password, str):
        return jsonify({"error": "usuario/correo y clave son obligatorios"}), 400

    if (
        identifier == current_app.config["API_USERNAME"]
        and password == current_app.config["API_PASSWORD"]
    ):
        return _issue_token({
            "username": identifier,
            "name": "Administración",
            "email": None,
            "role": "admin",
            "user_id": None,
        })

    email = identifier.strip().lower()
    with get_db() as connection:
        user = connection.execute(
            """
            SELECT id, nombre, correo, password_hash, role
            FROM usuarios
            WHERE correo = ?
            """,
            (email,),
        ).fetchone()

    if user is None or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Credenciales inválidas"}), 401

    return _issue_token({
        "username": user["correo"],
        "name": user["nombre"],
        "email": user["correo"],
        "role": user["role"],
        "user_id": user["id"],
    })


def token_required(view):
    @wraps(view)
    def decorated(*args, **kwargs):
        authorization = request.headers.get("Authorization", "")
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return jsonify({"error": "Usa Authorization: Bearer <token>"}), 401
        try:
            claims = jwt.decode(
                parts[1],
                current_app.config["SECRET_KEY"],
                algorithms=["HS256"],
                options={"require": ["exp", "user", "role"]},
            )
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expirado"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Token inválido"}), 401

        if claims.get("role") not in {"user", "admin"}:
            return jsonify({"error": "Rol inválido"}), 401
        g.current_user = claims
        return view(*args, **kwargs)
    return decorated


def admin_required(view):
    @wraps(view)
    @token_required
    def decorated(*args, **kwargs):
        if g.current_user["role"] != "admin":
            return jsonify({"error": "Esta operación requiere rol admin"}), 403
        return view(*args, **kwargs)
    return decorated
