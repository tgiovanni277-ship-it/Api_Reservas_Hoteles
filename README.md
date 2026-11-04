# API de reservas de hotel

API REST en Flask para registrar y administrar estancias de un hotel. Guarda los datos en SQLite y conserva el inicio de sesión con JWT, conforme a la guía de personalización. Firebase no es necesario para esta API; el taller de Firebase es una práctica aparte.

## Estructura

    Custom_Api/
    ├── app/
    │   ├── __init__.py       # Configura Flask, SQLite y las rutas
    │   ├── auth.py           # Login y verificación de JWT
    │   ├── config.py         # Variables del servidor
    │   ├── db.py             # Conexión y tabla SQLite
    │   ├── reservas.py       # Cinco operaciones CRUD
    │   └── validacion.py     # Reglas de reservas hoteleras
    ├── docs/ENTREGA.md       # Resumen breve para entregar
    ├── guia_postman.md       # Pasos y evidencia de API
    ├── run.py
    └── requirements.txt

`api_reservas_citas.py`, `reservas_citas.db` y `Pruebas_Postman_API_reservas.*` son archivos de la versión anterior de citas. La API de hotel se inicia con `run.py`; no uses las pruebas antiguas como evidencia del hotel.

## Instalación en Windows

Desde la carpeta del proyecto:

    py -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    Copy-Item .env.example .env

Edita `.env` y define un usuario, una contraseña y una clave JWT propios. Luego inicia la API:

    python run.py

La API estará en `http://127.0.0.1:5000`. Al iniciar, crea `reservas_hotel.db` y la tabla `reservas_hotel` si aún no existen. Los datos persisten al reiniciar el servidor.

## Credenciales de desarrollo

Las credenciales se leen desde `.env`:

- `API_USERNAME`: usuario de login.
- `API_PASSWORD`: contraseña de login.
- `API_SECRET_KEY`: secreto con el que Flask firma los JWT.
- `API_TOKEN_HOURS`: vigencia del token.
- `API_DB_PATH`: ruta opcional de la base SQLite.

`.env` está excluido de Git. No subas contraseñas reales ni el secreto JWT al repositorio.

## Datos de cada reserva

La tabla SQLite `reservas_hotel` usa un `id` autoincremental y estos campos:

| Campo              | Tipo y regla                              |
| ------------------ | ----------------------------------------- |
| `huesped`          | Texto obligatorio                         |
| `correo`           | Correo obligatorio                        |
| `habitacion`       | Texto obligatorio                         |
| `fecha_entrada`    | Fecha `AAAA-MM-DD`                        |
| `fecha_salida`     | Fecha `AAAA-MM-DD` posterior a la entrada |
| `numero_huespedes` | Entero positivo                           |
| `estado`           | `pendiente`, `confirmada` o `cancelada`   |

## Rutas

| Método   | Ruta             | Acceso     | Acción                                   |
| -------- | ---------------- | ---------- | ---------------------------------------- |
| `POST`   | `/login`         | Público    | Verifica credenciales y entrega un JWT   |
| `GET`    | `/reservas`      | Público    | Lista las reservas                       |
| `GET`    | `/reservas/{id}` | Público    | Consulta una reserva                     |
| `POST`   | `/reservas`      | JWT Bearer | Crea una reserva                         |
| `PUT`    | `/reservas/{id}` | JWT Bearer | Reemplaza todos los datos de una reserva |
| `DELETE` | `/reservas/{id}` | JWT Bearer | Elimina una reserva                      |

Los errores previstos son `400` para datos inválidos, `401` para credenciales o token inválidos y `404` para un id inexistente.

