from flask import Blueprint, g, jsonify, request

from app.auth import admin_required, token_required
from app.db import get_db
from app.validacion import normalizar_reserva, validar_reserva_hotel

reservas_bp = Blueprint("reservas", __name__)


def habitacion_disponible(connection, reserva, excluir_id=None):
    consulta = """
        SELECT 1
        FROM reservas_hotel
        WHERE TRIM(habitacion) = TRIM(?) COLLATE NOCASE
          AND estado != 'cancelada'
          AND fecha_entrada < ?
          AND fecha_salida > ?
    """
    parametros = [
        reserva["habitacion"],
        reserva["fecha_salida"],
        reserva["fecha_entrada"],
    ]
    if excluir_id is not None:
        consulta += " AND id != ?"
        parametros.append(excluir_id)
    return connection.execute(consulta, parametros).fetchone() is None


def reserva_visible(connection, reserva_id):
    columns = """
        id, huesped, correo, habitacion, fecha_entrada, fecha_salida,
        numero_huespedes, estado
    """
    if g.current_user["role"] == "admin":
        return connection.execute(
            "SELECT " + columns + " FROM reservas_hotel WHERE id = ?",
            (reserva_id,),
        ).fetchone()
    return connection.execute(
        "SELECT " + columns + " FROM reservas_hotel WHERE id = ? AND user_id = ?",
        (reserva_id, g.current_user.get("user_id")),
    ).fetchone()


@reservas_bp.get("/reservas")
@token_required
def listar_reservas():
    with get_db() as connection:
        if g.current_user["role"] == "admin":
            rows = connection.execute(
                """
                SELECT id, huesped, correo, habitacion, fecha_entrada, fecha_salida,
                       numero_huespedes, estado
                FROM reservas_hotel ORDER BY fecha_entrada, id
                """
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT id, huesped, correo, habitacion, fecha_entrada, fecha_salida,
                       numero_huespedes, estado
                FROM reservas_hotel
                WHERE user_id = ?
                ORDER BY fecha_entrada, id
                """,
                (g.current_user.get("user_id"),),
            ).fetchall()
    return jsonify([dict(row) for row in rows]), 200


@reservas_bp.get("/reservas/<string:reserva_id>")
@token_required
def consultar_reserva(reserva_id):
    if not reserva_id.isdigit():
        return jsonify({"error": "Reserva de hotel no encontrada"}), 404
    with get_db() as connection:
        row = reserva_visible(connection, int(reserva_id))
    if row is None:
        return jsonify({"error": "Reserva de hotel no encontrada"}), 404
    return jsonify(dict(row)), 200


@reservas_bp.post("/reservas")
@token_required
def crear_reserva():
    incoming = request.get_json(silent=True)
    if not isinstance(incoming, dict):
        return jsonify({"error": "Envía un objeto JSON"}), 400

    if g.current_user["role"] == "user":
        data = {
            **incoming,
            "huesped": g.current_user["name"],
            "correo": g.current_user["email"],
            "estado": "pendiente",
        }
        owner_id = g.current_user.get("user_id")
    else:
        data = incoming
        owner_id = None

    error = validar_reserva_hotel(data)
    if error:
        return jsonify({"error": error}), 400
    reserva = normalizar_reserva(data)
    conflicto = False
    with get_db() as connection:
        connection.execute("BEGIN IMMEDIATE")
        if (
            reserva["estado"] != "cancelada"
            and not habitacion_disponible(connection, reserva)
        ):
            conflicto = True
        else:
            cursor = connection.execute(
                """
                INSERT INTO reservas_hotel (
                    huesped, correo, habitacion, fecha_entrada, fecha_salida,
                    numero_huespedes, estado, user_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    reserva["huesped"], reserva["correo"], reserva["habitacion"],
                    reserva["fecha_entrada"], reserva["fecha_salida"],
                    reserva["numero_huespedes"], reserva["estado"], owner_id,
                ),
            )
            new_id = cursor.lastrowid
    if conflicto:
        return jsonify({"error": "La habitación ya está reservada para esas fechas"}), 409
    return jsonify({"id": new_id, "message": "Reserva de hotel creada"}), 201


@reservas_bp.put("/reservas/<string:reserva_id>")
@admin_required
def actualizar_reserva(reserva_id):
    data = request.get_json(silent=True)
    error = validar_reserva_hotel(data)
    if error:
        return jsonify({"error": error}), 400
    if not reserva_id.isdigit():
        return jsonify({"error": "Reserva de hotel no encontrada"}), 404
    reserva = normalizar_reserva(data)
    conflicto = False
    no_encontrada = False
    with get_db() as connection:
        connection.execute("BEGIN IMMEDIATE")
        existente = connection.execute(
            "SELECT 1 FROM reservas_hotel WHERE id = ?", (int(reserva_id),)
        ).fetchone()
        if existente is None:
            no_encontrada = True
        elif reserva["estado"] != "cancelada" and not habitacion_disponible(
            connection, reserva, excluir_id=int(reserva_id)
        ):
            conflicto = True
        else:
            connection.execute(
                """
                UPDATE reservas_hotel
                SET huesped = ?, correo = ?, habitacion = ?, fecha_entrada = ?,
                    fecha_salida = ?, numero_huespedes = ?, estado = ?
                WHERE id = ?
                """,
                (
                    reserva["huesped"], reserva["correo"], reserva["habitacion"],
                    reserva["fecha_entrada"], reserva["fecha_salida"],
                    reserva["numero_huespedes"], reserva["estado"], int(reserva_id),
                ),
            )
    if no_encontrada:
        return jsonify({"error": "Reserva de hotel no encontrada"}), 404
    if conflicto:
        return jsonify({"error": "La habitación ya está reservada para esas fechas"}), 409
    return jsonify({"message": "Reserva de hotel actualizada"}), 200


@reservas_bp.delete("/reservas/<string:reserva_id>")
@token_required
def eliminar_reserva(reserva_id):
    if not reserva_id.isdigit():
        return jsonify({"error": "Reserva de hotel no encontrada"}), 404
    reserva_id = int(reserva_id)
    with get_db() as connection:
        reserva = reserva_visible(connection, reserva_id)
        if reserva is None:
            return jsonify({"error": "Reserva de hotel no encontrada"}), 404
        if g.current_user["role"] == "admin":
            connection.execute("DELETE FROM reservas_hotel WHERE id = ?", (reserva_id,))
            return jsonify({"message": "Reserva eliminada"}), 200
        connection.execute(
            "UPDATE reservas_hotel SET estado = 'cancelada' WHERE id = ?",
            (reserva_id,),
        )
    return jsonify({"message": "Reserva cancelada"}), 200
