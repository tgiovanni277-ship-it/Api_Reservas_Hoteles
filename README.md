# Reservas de hotel

Monorepo para el MVP de reservas. Vercel publica el frontend de Vite desde frontend/; Azure ejecutará la API Flask; PostgreSQL en Supabase se incorporará en la fase de migración de datos.

## Estructura

    frontend/                 Interfaz Vite para Vercel
      src/main.js              Acceso por rol, calendario y portal de huésped
      src/style.css
      index.html
      package.json
      vite.config.js
    api/                       API Flask para Azure
      app/
      requirements.txt
      run.py
    docs/
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

Vite publica la interfaz en http://localhost:5173 y proxifica /login, /register y /reservas a Flask en http://127.0.0.1:5000. La variable VITE_DEV_API_PROXY_TARGET permite cambiar el backend local.

## Roles y permisos

- Admin: entra con API_USERNAME y API_PASSWORD de la configuración del backend. Ve el calendario global, revisa solicitudes de huéspedes y confirma, crea, edita o elimina reservas.
- Huésped: crea una cuenta desde la pantalla de acceso. Las cuentas nuevas siempre reciben rol user. Puede solicitar reservas, consultar únicamente las propias y cancelarlas.
- El servidor decide el rol y lo incluye en el JWT. No hay selector de rol ni permisos confiados al navegador.
- Las contraseñas de huésped se guardan como hash. El token se mantiene en memoria del navegador y se pierde al cerrar sesión o recargar.
- Los registros antiguos de SQLite no tienen cuenta asociada y solo aparecen para admin.
- El calendario indica reservas registradas. Como aún no hay catálogo de habitaciones, no representa disponibilidad global ni permite elegir una habitación desde inventario.

## Despliegue

- Vercel: Root Directory frontend/, comando npm run build, salida dist/.
- Vercel: definir VITE_API_BASE_URL con la URL HTTPS de Flask en Azure.
- Azure Container Apps: configurar API_USERNAME, API_PASSWORD, API_SECRET_KEY y CORS_ALLOWED_ORIGINS como variables protegidas.
- CORS_ALLOWED_ORIGINS es una lista separada por comas de orígenes exactos, sin rutas. Incluye el dominio de producción Vercel y los previews autorizados. No usar * en producción.

El navegador llama por HTTPS a Flask; Flask administra autorización y accede a la base de datos. No conectar el frontend directamente a SQLite o PostgreSQL.

## Datos y reglas

SQLite local conserva la tabla reservas_hotel y agrega user_id para asociar las nuevas reservas a sus cuentas. La migración es aditiva: las filas existentes se conservan. Reservas pendientes y confirmadas ocupan una habitación desde entrada incluida hasta salida excluida; las canceladas no bloquean. La API rechaza cruces con HTTP 409.

## Rutas principales

| Método | Ruta | Permiso |
|---|---|---|
| POST | /register | Público; crea cuenta de huésped |
| POST | /login | Público; responde con rol admin o user |
| GET | /health | Público; estado del servicio |
| GET | /reservas | Admin: todas; user: propias |
| GET | /reservas/{id} | Admin: cualquiera; user: propia |
| POST | /reservas | Admin crea; user solicita en estado pendiente |
| PUT | /reservas/{id} | Solo admin |
| DELETE | /reservas/{id} | Admin elimina; user cancela la propia |

La guía de Postman está en docs/guia_postman.md y el resumen académico, en docs/ENTREGA.md.
