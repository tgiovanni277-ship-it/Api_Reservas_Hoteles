# Reservas de hotel

Monorepo para el MVP de reservas. Vercel publica el frontend de Vite; Render ejecuta la API Flask; PostgreSQL en Supabase conserva usuarios y reservas. SQLite sigue disponible para desarrollo local sin `DATABASE_URL`.

## Estructura

    frontend/                 Interfaz Vite para Vercel
      src/main.js              Acceso por rol, calendario y portal de huésped
      src/style.css
      index.html
      package.json
      vite.config.js
    api/                       API Flask para Render
      app/
      Dockerfile
      .dockerignore
      requirements.txt
      run.py
    docs/
      despliegue_render.md
    .env.example
    README.md

## Desarrollo local

Requiere Python 3.10+ y Node.js LTS. Desde la raíz del repo:

    py -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install -r api\requirements.txt
    Copy-Item .env.example .env

Antes de iniciar, reemplaza en `.env` los marcadores de `API_SECRET_KEY`, `API_USERNAME` y `API_PASSWORD` por valores propios.

    python api\run.py

En otra terminal:

    cd frontend
    npm install
    Copy-Item .env.example .env
    npm run dev

Vite publica la interfaz en http://localhost:5173 y proxifica /login, /register, /reservas y /habitaciones a Flask en http://127.0.0.1:5000. La variable VITE_DEV_API_PROXY_TARGET permite cambiar el backend local.

## Roles y permisos

- Admin: entra con API_USERNAME y API_PASSWORD de la configuración del backend. Ve el calendario global, revisa solicitudes de huéspedes y confirma, crea, edita o elimina reservas.
- Huésped: crea una cuenta desde la pantalla de acceso. Las cuentas nuevas siempre reciben rol user. Puede solicitar reservas, consultar únicamente las propias y cancelarlas.
- El servidor decide el rol y lo incluye en el JWT. No hay selector de rol ni permisos confiados al navegador.
- Las contraseñas de huésped se guardan como hash. El token se mantiene en memoria del navegador y se pierde al cerrar sesión o recargar.
- Los registros antiguos de SQLite no tienen cuenta asociada y solo aparecen para admin.
- El inventario inicial contiene 80 habitaciones: 101–120, 201–220, 301–320 y 401–420.
- Huéspedes y admin consultan habitaciones libres según las fechas seleccionadas. Las solicitudes pendientes y confirmadas ocupan habitación; las canceladas liberan fechas.
- El calendario indica reservas registradas; la API es la autoridad para verificar disponibilidad al crear o actualizar una reserva.

## Despliegue

- Vercel: Root Directory frontend/, comando npm run build, salida dist/.
- Vercel: definir VITE_API_BASE_URL con la URL HTTPS de Flask en Render.
- Render Web Service: importar el repo de GitHub, usar `api/` como raíz de Docker y configurar `DATABASE_URL`, `API_USERNAME`, `API_PASSWORD`, `API_SECRET_KEY` y `CORS_ALLOWED_ORIGINS` como variables de entorno.
- CORS_ALLOWED_ORIGINS es una lista separada por comas de orígenes exactos, sin rutas. Incluye el dominio de producción Vercel y los previews autorizados. No usar * en producción.
- El despliegue de la API es manual con Docker y Render; no requiere GitHub Actions. Sigue [la guía de despliegue](docs/despliegue_render.md).

El navegador llama por HTTPS a Flask en Render; Flask administra autorización y accede a la base de datos. No conectar el frontend directamente a SQLite o PostgreSQL.

## Datos y reglas

SQLite local conserva las tablas `usuarios`, `reservas_hotel` y `habitaciones`. PostgreSQL crea el mismo esquema al arrancar cuando `DATABASE_URL` está definida. El inventario inicial se crea con 80 habitaciones y no elimina registros existentes. Reservas pendientes y confirmadas ocupan una habitación desde entrada incluida hasta salida excluida; las canceladas no bloquean. La API rechaza cruces con HTTP 409.

### Migrar la base SQLite existente a Supabase PostgreSQL

1. En Supabase, crea el proyecto y copia la URI PostgreSQL desde **Connect**.
2. Instala las dependencias actualizadas: `pip install -r api/requirements.txt`.
3. En `.env`, configura `DATABASE_URL` con la URI de Supabase. Para desarrollo local con SQLite, deja esa variable vacía.
4. Ejecuta desde la raíz: `python api/scripts/migrate_sqlite_to_postgres.py`. También puedes pasar otra ruta SQLite como argumento.
5. El script crea el esquema y las 80 habitaciones si hacen falta, copia usuarios y reservas preservando sus IDs y hashes de contraseña, ajusta las secuencias y deja intacto el archivo SQLite.
6. Arranca la API y verifica login, reservas e inventario. Haz una copia de seguridad antes de migrar datos importantes.

La URI es un secreto: no la pongas en Git, en el frontend ni en `VITE_API_BASE_URL`. En Render debe guardarse como variable protegida `DATABASE_URL`.

## Rutas principales

| Método | Ruta | Permiso |
|---|---|---|
| POST | /register | Público; crea cuenta de huésped |
| POST | /login | Público; responde con rol admin o user |
| GET | /health | Público; estado del servicio |
| GET | /habitaciones | Usuario autenticado; lista el inventario |
| GET | /habitaciones/disponibles?fecha_entrada=AAAA-MM-DD&fecha_salida=AAAA-MM-DD | Usuario autenticado; habitaciones libres en el rango |
| GET | /reservas | Admin: todas; user: propias |
| GET | /reservas/{id} | Admin: cualquiera; user: propia |
| POST | /reservas | Admin crea; user solicita en estado pendiente |
| PUT | /reservas/{id} | Solo admin |
| DELETE | /reservas/{id} | Admin elimina; user cancela la propia |

La guía de Postman está en docs/guia_postman.md y el resumen académico, en docs/ENTREGA.md.
