# Guía de Postman — API de reservas de hotel

## Preparar y ejecutar

1. Crea y activa el entorno Python, instala api/requirements.txt y copia `.env.example` a `.env` siguiendo el README.
2. Inicia la API con `python api/run.py`.
3. Crea una colección y añade la variable `base_url` con el valor `http://127.0.0.1:5000`. Las solicitudes de esta guía usan `{{base_url}}`.

La base `reservas_hotel.db` y la tabla `reservas_hotel` se crean al iniciar la API. Las credenciales son las que pusiste en `.env`.

## 1. Login y token

**POST** `{{base_url}}/login`

Body → raw → JSON:

```json
{
  "username": "YOUR_API_USERNAME",
  "clave": "YOUR_API_PASSWORD"
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

Ambas consultas requieren el token de la sección 1 en Authorization: Bearer {{token}}. Esto protege los datos personales de los huéspedes.

- **GET** `{{base_url}}/reservas` — lista todas las reservas.
- **GET** `{{base_url}}/reservas/{{id_reserva_1}}` — consulta una por id.

## 4. Actualizar

**PUT** `{{base_url}}/reservas/{{id_reserva_1}}`

Envía el objeto completo, por ejemplo cambia su estado a `confirmada` o el número de huéspedes. La respuesta esperada es `200`.

## 5. Eliminar

**DELETE** `{{base_url}}/reservas/{{id_reserva_1}}`

La respuesta esperada es `200`. Vuelve a hacer **GET** `/reservas`: debe permanecer la segunda reserva. Reinicia Flask y repite el GET para demostrar que SQLite conservó el dato.

## Pruebas de error que pide la guía

1. **Datos inválidos — esperado `400`:** intenta crear una reserva donde la salida sea anterior o igual a la entrada, con `numero_huespedes` igual a cero, o con una fecha como `20270421` (se exige `AAAA-MM-DD`).
2. **Habitación ocupada — esperado `409`:** con la reserva confirmada de la habitación `204` del ejemplo ya creada, intenta reservar la habitación `204` del `2027-04-22` al `2027-04-23`.
3. Sin token: intenta GET /reservas o POST /reservas sin Authorization; ambas deben responder 401.
4. **Id inexistente — esperado `404`:** consulta `GET /reservas/999999` (o elige un id que no exista).

Guarda capturas de login, las operaciones CRUD y estos cuatro errores para documentar la API de hotel.
