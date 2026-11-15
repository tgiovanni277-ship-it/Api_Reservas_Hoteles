from contextlib import contextmanager
import sqlite3

from flask import current_app


@contextmanager
def get_db():
    connection = sqlite3.connect(current_app.config["DATABASE"])
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_db(database_path):
    connection = sqlite3.connect(database_path)
    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS reservas_hotel (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                huesped TEXT NOT NULL,
                correo TEXT NOT NULL,
                habitacion TEXT NOT NULL,
                fecha_entrada TEXT NOT NULL,
                fecha_salida TEXT NOT NULL,
                numero_huespedes INTEGER NOT NULL CHECK (numero_huespedes > 0),
                estado TEXT NOT NULL CHECK (
                    estado IN ('pendiente', 'confirmada', 'cancelada')
                )
            )
            """
        )
        connection.commit()
    finally:
        connection.close()
