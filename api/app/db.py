from contextlib import contextmanager
import sqlite3

from flask import current_app


@contextmanager
def get_db():
    connection = sqlite3.connect(current_app.config["DATABASE"])
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
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
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                correo TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user' CHECK (role = 'user'),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
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
                ),
                user_id INTEGER REFERENCES usuarios(id) ON DELETE SET NULL
            )
            """
        )
        columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(reservas_hotel)")
        }
        if "user_id" not in columns:
            connection.execute(
                "ALTER TABLE reservas_hotel ADD COLUMN user_id INTEGER REFERENCES usuarios(id) ON DELETE SET NULL"
            )
        connection.commit()
    finally:
        connection.close()
