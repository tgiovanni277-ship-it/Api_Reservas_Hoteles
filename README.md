# Reservas de hotel

Monorepo para el MVP de reservas. El frontend está separado de la API: Vercel publica frontend/, Flask expone la API para Azure y Supabase se incorporará como PostgreSQL en una fase posterior.

## Estructura

    API-Reservas-Hotel/
    ├── frontend/              # Vite: interfaz y calendario, despliegue en Vercel
    │   ├── src/main.js
    │   ├── src/style.css
    │   ├── index.html
    │   └── vite.config.js
    ├── api/                    # API Flask, preparada para Azure
    │   ├── app/
    │   ├── requirements.txt
    │   └── run.py
    ├── docs/
    ├── .env.example            # variables locales de la API
    ├── .gitignore
    └── README.md

## Desarrollo local

Requiere Python 3.10+ y Node.js LTS. En la raíz del repo, configura primero el backend:

    py -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install -r api\requirements.txt
    Copy-Item .env.example .env

Completa .env con credenciales de desarrollo locales; luego inicia Flask en una terminal:

    python api\run.py

En otra terminal instala e inicia el frontend:

    cd frontend
    npm install
    Copy-Item .env.example .env
    npm run dev

Vite publica la interfaz en http://localhost:5173 y envía /login y /reservas al backend local en http://127.0.0.1:5000. La variable opcional VITE_DEV_API_PROXY_TARGET permite cambiar el destino del proxy. Flask también responde en /health.

## Despliegue

- Vercel: importa el repositorio y fija frontend/ como Root Directory. El proyecto ejecuta npm run build y publica dist/.
- Azure Container Apps: construye la API usando api/ como contexto Docker; configura allí los secretos del backend y CORS_ALLOWED_ORIGINS.
- Frontend de Vercel: define VITE_API_BASE_URL con la URL HTTPS de la API en Azure antes de construir.
- CORS de Flask: CORS_ALLOWED_ORIGINS es una lista separada por comas de orígenes completos, sin rutas. Añade el dominio de producción de Vercel y los previews concretos que necesites, además de localhost durante desarrollo. No uses * en producción.

El frontend nunca se conecta directamente a SQLite o PostgreSQL. En producción, el navegador llama por HTTPS a Flask en Azure; Flask conecta a PostgreSQL administrado en Supabase cuando se complete esa migración.

## Variables de entorno

El .env de la raíz se usa solo para desarrollo de la API y está ignorado por Git. .env.example contiene marcadores de posición. frontend/.env.example documenta la URL pública que Vite incorpora durante el build; esa URL no es un secreto.

- API: API_USERNAME, API_PASSWORD, API_SECRET_KEY, API_TOKEN_HOURS, API_DB_PATH, FLASK_DEBUG, CORS_ALLOWED_ORIGINS.
- Frontend: VITE_API_BASE_URL (vacía en local para usar el proxy de Vite).

No subas contraseñas, tokens, claves o cadenas de conexión a Git.

## Modelo y reglas de reserva

SQLite local conserva la tabla reservas_hotel; las reservas pendientes y confirmadas ocupan una habitación desde la fecha de entrada (incluida) hasta la salida (excluida). Las canceladas no bloquean. Una colisión devuelve HTTP 409. El calendario mensual muestra ocupación registrada y distingue entradas, salidas y reservas canceladas; aún no existe inventario de habitaciones para afirmar disponibilidad global.

## Rutas principales

| Método | Ruta | Acceso | Acción |
|---|---|---|---|
| GET | /health | Público | Estado del servicio, sin datos de huéspedes |
| POST | /login | Público | Valida credenciales y devuelve JWT |
| GET | /reservas | JWT Bearer | Lista reservas |
| GET | /reservas/{id} | JWT Bearer | Consulta una reserva |
| POST | /reservas | JWT Bearer | Crea una reserva |
| PUT | /reservas/{id} | JWT Bearer | Actualiza una reserva |
| DELETE | /reservas/{id} | JWT Bearer | Elimina una reserva |

La guía de solicitudes está en docs/guia_postman.md; el resumen académico, en docs/ENTREGA.md.
