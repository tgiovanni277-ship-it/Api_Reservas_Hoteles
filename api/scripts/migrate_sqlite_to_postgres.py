import argparse
import os
from pathlib import Path
import sqlite3
import sys

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row


ROOT_DIR = Path(__file__).resolve().parents[2]
API_DIR = ROOT_DIR / "api"
sys.path.insert(0, str(API_DIR))
load_dotenv(ROOT_DIR / ".env")

from app.db import init_db  # noqa: E402


def table_exists(connection, table_name):
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone() is not None


def migrate_users(source, target):
    if not table_exists(source, "usuarios"):
        return 0
    rows = [dict(row) for row in source.execute("SELECT * FROM usuarios")]
    for row in rows:
        target.execute(
            """
            INSERT INTO usuarios (id, nombre, correo, password_hash, role, created_at)
            OVERRIDING SYSTEM VALUE
            VALUES (%(id)s, %(nombre)s, %(correo)s, %(password_hash)s, %(role)s, %(created_at)s)
            ON CONFLICT (id) DO UPDATE SET
                nombre = EXCLUDED.nombre,
                correo = EXCLUDED.correo,
                password_hash = EXCLUDED.password_hash,
                role = EXCLUDED.role,
                created_at = EXCLUDED.created_at
            """,
            row,
        )
    return len(rows)


def migrate_reservations(source, target):
    if not table_exists(source, "reservas_hotel"):
        return 0
    columns = {
        row[1] for row in source.execute("PRAGMA table_info(reservas_hotel)")
    }
    rows = [dict(row) for row in source.execute("SELECT * FROM reservas_hotel")]
    for row in rows:
        row.setdefault("user_id", None)
        if "user_id" not in columns:
            row["user_id"] = None
        target.execute(
            """
            INSERT INTO reservas_hotel (
                id, huesped, correo, habitacion, fecha_entrada, fecha_salida,
                numero_huespedes, estado, user_id
            ) OVERRIDING SYSTEM VALUE VALUES (
                %(id)s, %(huesped)s, %(correo)s, %(habitacion)s,
                %(fecha_entrada)s, %(fecha_salida)s, %(numero_huespedes)s,
                %(estado)s, %(user_id)s
            )
            ON CONFLICT (id) DO UPDATE SET
                huesped = EXCLUDED.huesped,
                correo = EXCLUDED.correo,
                habitacion = EXCLUDED.habitacion,
                fecha_entrada = EXCLUDED.fecha_entrada,
                fecha_salida = EXCLUDED.fecha_salida,
                numero_huespedes = EXCLUDED.numero_huespedes,
                estado = EXCLUDED.estado,
                user_id = EXCLUDED.user_id
            """,
            row,
        )
    return len(rows)


def sync_identity_sequences(target):
    for table in ("usuarios", "reservas_hotel", "habitaciones"):
        target.execute(
            f"""
            SELECT setval(
                pg_get_serial_sequence('{table}', 'id'),
                COALESCE(MAX(id), 1),
                MAX(id) IS NOT NULL
            ) FROM {table}
            """
        )


def main():
    parser = argparse.ArgumentParser(
        description="Copia usuarios y reservas de SQLite a Supabase PostgreSQL."
    )
    parser.add_argument(
        "source",
        nargs="?",
        default=str(ROOT_DIR / "reservas_hotel.db"),
        help="Ruta a la base SQLite de origen (por defecto: reservas_hotel.db).",
    )
    args = parser.parse_args()
    source_path = Path(args.source).resolve()
    database_url = os.getenv("DATABASE_URL", "").strip()
    if database_url.startswith("postgres://"):
        database_url = "postgresql://" + database_url[len("postgres://"):]
    if not database_url:
        parser.error("Configura DATABASE_URL en .env con la URI de PostgreSQL de Supabase.")
    if not source_path.is_file():
        parser.error(f"No existe la base SQLite de origen: {source_path}")

    init_db(database_url=database_url)
    source = sqlite3.connect(source_path)
    source.row_factory = sqlite3.Row
    try:
        with psycopg.connect(database_url, row_factory=dict_row) as target:
            users = migrate_users(source, target)
            reservations = migrate_reservations(source, target)
            sync_identity_sequences(target)
    finally:
        source.close()

    print(f"Migración completada: {users} usuario(s), {reservations} reserva(s).")
    print("La base SQLite original no se modificó.")


if __name__ == "__main__":
    main()
