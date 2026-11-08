from flask import Blueprint, jsonify, request

from app.auth import token_required
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


@reservas_bp.get("/reservas")
def listar_reservas():
    with get_db() as connection:
        rows = connection.execute(
            "SELECT * FROM reservas_hotel ORDER BY id"
        ).fetchall()
    return jsonify([dict(row) for row in rows]), 200


@reservas_bp.get("/reservas/<string:reserva_id>")
def consultar_reserva(reserva_id):
    if not reserva_id.isdigit():
        return jsonify({"error": "Reserva de hotel no encontrada"}), 404
    with get_db() as connection:
        row = connection.execute(
            "SELECT * FROM reservas_hotel WHERE id = ?", (int(reserva_id),)
        ).fetchone()
    if row is None:
        return jsonify({"error": "Reserva de hotel no encontrada"}), 404
    return jsonify(dict(row)), 200


@reservas_bp.post("/reservas")
@token_required
def crear_reserva():
    data = request.get_json(silent=True)
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
                    numero_huespedes, estado
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    reserva["huesped"], reserva["correo"], reserva["habitacion"],
                    reserva["fecha_entrada"], reserva["fecha_salida"],
                    reserva["numero_huespedes"], reserva["estado"],
                ),
            )
            new_id = cursor.lastrowid
    if conflicto:
        return jsonify({"error": "La habitación ya está reservada para esas fechas"}), 409
    return jsonify({"id": new_id, "message": "Reserva de hotel creada"}), 201


@reservas_bp.put("/reservas/<string:reserva_id>")
@token_required
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
    with get_db() as connection:
        cursor = connection.execute(
            "DELETE FROM reservas_hotel WHERE id = ?", (int(reserva_id),)
        )
        if cursor.rowcount == 0:
            return jsonify({"error": "Reserva de hotel no encontrada"}), 404
    return jsonify({"message": "Reserva de hotel eliminada"}), 200

