# Guía de Postman — API de reservas de hotel

## Preparar y ejecutar

1. Crea y activa el entorno Python, instala `requirements.txt` y copia `.env.example` a `.env` siguiendo el README.
2. Inicia la API con `python run.py`.
3. Crea una colección y añade la variable `base_url` con el valor `http://127.0.0.1:5000`. Las solicitudes de esta guía usan `{{base_url}}`.

La base `reservas_hotel.db` y la tabla `reservas_hotel` se crean al iniciar la API. Las credenciales son las que pusiste en `.env`.

## 1. Login y token

**POST** `{{base_url}}/login`

Body → raw → JSON:

```json
{
  "username": "teacher",
  "clave": "demo123"
}
```

Usa los valores de `API_USERNAME` y `API_PASSWORD` de tu `.env`. La respuesta incluye `token`. Guárdalo como variable de colección `token` o pégalo en las operaciones protegidas:

```text
Authorization: Bearer {{token}}
```

## 2. Crear dos reservas

En cada petición usa `Content-Type: application/json` y el token Bearer.

**POST** `{{base_url}}/reservas`

Reserva 1:

```json
{
  "huesped": "Laura Gómez",
  "correo": "laura@example.com",
  "habitacion": "204",
  "fecha_entrada": "2027-04-21",
  "fecha_salida": "2027-04-24",
  "numero_huespedes": 2,
  "estado": "confirmada"
}
```

Reserva 2:

```json
{
  "huesped": "Andrés Ruiz",
  "correo": "andres@example.com",
  "habitacion": "108",
  "fecha_entrada": "2027-05-02",
  "fecha_salida": "2027-05-04",
  "numero_huespedes": 1,
  "estado": "pendiente"
}
```

Cada respuesta `201` devuelve el `id` autoincremental de SQLite. Anota ambos ids para las siguientes solicitudes.

## 3. Listar y consultar

- **GET** `{{base_url}}/reservas` — lista todas las reservas.
- **GET** `{{base_url}}/reservas/{{id_reserva_1}}` — consulta una por id.

## 4. Actualizar

**PUT** `{{base_url}}/reservas/{{id_reserva_1}}`

Envía el objeto completo, por ejemplo cambia su estado a `confirmada` o el número de huéspedes. La respuesta esperada es `200`.

## 5. Eliminar

**DELETE** `{{base_url}}/reservas/{{id_reserva_1}}`

La respuesta esperada es `200`. Vuelve a hacer **GET** `/reservas`: debe permanecer la segunda reserva. Reinicia Flask y repite el GET para demostrar que SQLite conservó el dato.

## Pruebas de error que pide la guía

1. **Datos inválidos — esperado `400`:** intenta crear una reserva donde la salida sea anterior o igual a la entrada, o con `numero_huespedes` igual a cero.
2. **Sin token — esperado `401`:** intenta `POST /reservas` sin el encabezado Authorization.
3. **Id inexistente — esperado `404`:** consulta `GET /reservas/999999` (o elige un id que no exista).

Guarda capturas de login, las cinco operaciones CRUD y estos tres errores. Las capturas y el documento `Pruebas_Postman_API_reservas.*` existentes son de la versión de citas, no de la API de hotel.
