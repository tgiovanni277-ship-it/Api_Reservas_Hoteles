# API de reservas de hotel

La API administra estancias hoteleras con Flask y SQLite. El JWT determina el rol admin o user; la API aplica permisos por ruta y limita a cada huésped a sus propias reservas. El frontend separado se despliega en Vercel.

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
| `POST` | `/register` | Crea cuenta de huésped con rol user; devuelve JWT |
| `GET` | `/reservas` | Admin: todas; huésped: propias; requiere JWT |
| `GET` | `/reservas/{id}` | Admin: cualquiera; huésped: propia; requiere JWT |
| `POST` | `/reservas` | Admin crea; huésped solicita pendiente; requiere JWT |
| `PUT` | `/reservas/{id}` | Actualiza una reserva; solo admin |
| `DELETE` | `/reservas/{id}` | Admin elimina; huésped cancela la propia |

Las fechas deben tener exactamente el formato `AAAA-MM-DD`. Las reservas pendientes y confirmadas ocupan la habitación en el intervalo desde la entrada (incluida) hasta la salida (excluida); si se solapan con otra reserva de la misma habitación, el servidor responde `409`. Las reservas canceladas no bloquean disponibilidad.

El servidor responde `400` si los datos no pasan las validaciones, `401` si las credenciales o el token faltan o son inválidos, `404` si el id no existe y `409` si la habitación ya está reservada para esas fechas. La guía completa de Postman está en `docs/guia_postman.md`.

## Frontend y despliegue

La interfaz y el calendario se desarrollan en frontend/ con Vite. En Vercel, configura frontend/ como Root Directory y VITE_API_BASE_URL con el dominio HTTPS de Flask en Azure. Configura CORS_ALLOWED_ORIGINS en la API con los dominios Vercel autorizados.

## Roles y acceso

El administrador inicia sesión con API_USERNAME y API_PASSWORD configurados en el backend; revisa las solicitudes pendientes de huéspedes y puede confirmarlas. El huésped se registra con correo y contraseña; el registro asigna siempre el rol user. El JWT firmado comunica el rol a Flask. Las consultas de huésped se filtran por user_id; el huésped solo puede solicitar y cancelar sus reservas. Los registros preexistentes de SQLite quedan sin propietario y solo son visibles para admin.

## Persistencia y ejecución

SQLite guarda los datos en `reservas_hotel.db`. La aplicación crea la tabla al arrancar y reutiliza ese archivo en reinicios. Instala dependencias con `pip install -r api/requirements.txt`, configura `.env` a partir de `.env.example` y ejecuta `python api/run.py`.
 Giovanni Torres
