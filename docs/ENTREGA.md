# API de reservas de hotel

La API administra estancias hoteleras con Flask y SQLite. El acceso de escritura se protege con JWT firmado por la propia API.

## Tabla `reservas_hotel`

| Campo | Tipo y regla |
|---|---|
| `id` | Entero autoincremental, clave primaria |
| `huesped` | Texto obligatorio |
| `correo` | Texto obligatorio con formato de correo básico |
| `habitacion` | Texto obligatorio |
| `fecha_entrada` | Fecha ISO `AAAA-MM-DD` |
| `fecha_salida` | Fecha ISO posterior a `fecha_entrada` |
| `numero_huespedes` | Entero mayor que cero |
| `estado` | `pendiente`, `confirmada` o `cancelada` |

## Rutas

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/login` | Recibe `username` y `clave`; devuelve un JWT |
| `GET` | `/reservas` | Lista todas las reservas |
| `GET` | `/reservas/{id}` | Consulta una reserva por id |
| `POST` | `/reservas` | Crea una reserva; requiere JWT Bearer |
| `PUT` | `/reservas/{id}` | Actualiza una reserva; requiere JWT Bearer |
| `DELETE` | `/reservas/{id}` | Elimina una reserva; requiere JWT Bearer |

El servidor responde `400` si los datos no pasan las validaciones, `401` si las credenciales o el token faltan o son inválidos y `404` si el id no existe. La guía completa de Postman está en `guia_postman.md`.

## Persistencia y ejecución

SQLite guarda los datos en `reservas_hotel.db`. La aplicación crea la tabla al arrancar y reutiliza ese archivo en reinicios. Instala dependencias con `pip install -r requirements.txt`, configura `.env` a partir de `.env.example` y ejecuta `python run.py`.


