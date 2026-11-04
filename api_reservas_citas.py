from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from functools import wraps
import os
from pathlib import Path
import sqlite3

import jwt
from flask import Flask, jsonify, request


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get(
    'API_SECRET_KEY', 'clave-demo-cambiar-antes-de-publicar'
)
USERS = {
    os.environ.get('API_USERNAME', 'teacher'):
        os.environ.get('API_PASSWORD', 'demo123')
}
DB_PATH = Path(os.environ.get(
    'API_DB_PATH', str(Path(__file__).resolve().with_name('reservas_citas.db'))
))
ESTADOS_PERMITIDOS = {'pendiente', 'confirmada', 'cancelada'}


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS reservas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente TEXT NOT NULL,
                servicio TEXT NOT NULL,
                fecha_hora TEXT NOT NULL,
                duracion_minutos INTEGER NOT NULL
                    CHECK (duracion_minutos BETWEEN 1 AND 480),
                estado TEXT NOT NULL
                    CHECK (estado IN ('pendiente', 'confirmada', 'cancelada'))
            )
        ''')


def token_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth = request.headers.get('Authorization', '')
        parts = auth.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return jsonify({'error': 'Usa Authorization: Bearer <token>'}), 401
        try:
            jwt.decode(
                parts[1], app.config['SECRET_KEY'], algorithms=['HS256'],
                options={'require': ['exp', 'user']}
            )
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expirado'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token inválido'}), 401
        return func(*args, **kwargs)
    return wrapper


def validar_reserva(data):
    if not isinstance(data, dict):
        return 'Envía un objeto JSON'

    for field in ('cliente', 'servicio'):
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            return f'{field} debe ser un texto no vacío'

    fecha_hora = data.get('fecha_hora')
    if not isinstance(fecha_hora, str):
        return 'fecha_hora debe ser una fecha ISO 8601 con zona horaria'
    try:
        parsed = datetime.fromisoformat(fecha_hora.replace('Z', '+00:00'))
    except ValueError:
        return 'fecha_hora debe tener formato ISO 8601, por ejemplo 2027-04-21T10:30:00-05:00'
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return 'fecha_hora debe incluir zona horaria, por ejemplo -05:00 o Z'

    duracion = data.get('duracion_minutos')
    if type(duracion) is not int or not 1 <= duracion <= 480:
        return 'duracion_minutos debe ser un entero entre 1 y 480'

    estado = data.get('estado')
    if not isinstance(estado, str) or estado not in ESTADOS_PERMITIDOS:
        return 'estado debe ser pendiente, confirmada o cancelada'
    return None


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'error': 'Envía un objeto JSON'}), 400
    username = data.get('username')
    password = data.get('clave')
    if not isinstance(username, str) or not isinstance(password, str):
        return jsonify({'error': 'username y clave son obligatorios'}), 400
    if USERS.get(username) != password:
        return jsonify({'error': 'Credenciales inválidas'}), 401

    token = jwt.encode({
        'user': username,
        'exp': datetime.now(timezone.utc).replace(microsecond=0)
            + timedelta(hours=1)
    }, app.config['SECRET_KEY'], algorithm='HS256')
    return jsonify({'token': token}), 200


@app.route('/')
def root():
    return jsonify({
        'message': 'API de reservas de citas',
        'recurso': '/reservas'
    }), 200


@app.route('/reservas', methods=['GET'])
def listar_reservas():
    with get_db() as conn:
        rows = conn.execute('SELECT * FROM reservas ORDER BY id').fetchall()
    return jsonify([dict(row) for row in rows]), 200


@app.route('/reservas/<int:reserva_id>', methods=['GET'])
def consultar_reserva(reserva_id):
    with get_db() as conn:
        row = conn.execute(
            'SELECT * FROM reservas WHERE id = ?', (reserva_id,)
        ).fetchone()
    if row is None:
        return jsonify({'error': 'Reserva no encontrada'}), 404
    return jsonify(dict(row)), 200


@app.route('/reservas', methods=['POST'])
@token_required
def crear_reserva():
    data = request.get_json(silent=True)
    error = validar_reserva(data)
    if error:
        return jsonify({'error': error}), 400
    with get_db() as conn:
        cursor = conn.execute('''
            INSERT INTO reservas
                (cliente, servicio, fecha_hora, duracion_minutos, estado)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            data['cliente'].strip(), data['servicio'].strip(),
            data['fecha_hora'], data['duracion_minutos'], data['estado']
        ))
        new_id = cursor.lastrowid
    return jsonify({'id': new_id, 'message': 'Reserva creada'}), 201


@app.route('/reservas/<int:reserva_id>', methods=['PUT'])
@token_required
def actualizar_reserva(reserva_id):
    data = request.get_json(silent=True)
    error = validar_reserva(data)
    if error:
        return jsonify({'error': error}), 400
    with get_db() as conn:
        row = conn.execute(
            'SELECT id FROM reservas WHERE id = ?', (reserva_id,)
        ).fetchone()
        if row is None:
            return jsonify({'error': 'Reserva no encontrada'}), 404
        conn.execute('''
            UPDATE reservas
            SET cliente = ?, servicio = ?, fecha_hora = ?,
                duracion_minutos = ?, estado = ?
            WHERE id = ?
        ''', (
            data['cliente'].strip(), data['servicio'].strip(),
            data['fecha_hora'], data['duracion_minutos'], data['estado'],
            reserva_id
        ))
    return jsonify({'message': 'Reserva actualizada'}), 200


@app.route('/reservas/<int:reserva_id>', methods=['DELETE'])
@token_required
def eliminar_reserva(reserva_id):
    with get_db() as conn:
        cursor = conn.execute(
            'DELETE FROM reservas WHERE id = ?', (reserva_id,)
        )
        if cursor.rowcount == 0:
            return jsonify({'error': 'Reserva no encontrada'}), 404
    return jsonify({'message': 'Reserva eliminada'}), 200


if __name__ == '__main__':
    init_db()
    app.run(debug=os.environ.get('FLASK_DEBUG') == '1')

