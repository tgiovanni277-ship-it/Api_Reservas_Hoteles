<div align="center">

# 🏨 Reservas de hotel

**MVP de reservas hoteleras con portal para huéspedes y panel de administración.**

[Ver demo](https://frontend-rho-one-25.vercel.app/) · [Guía de despliegue](docs/despliegue_render.md) · [Guía de Postman](docs/guia_postman.md)

![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Flask 3](https://img.shields.io/badge/Flask-3.x-000000?logo=flask&logoColor=white)
![Vite 6](https://img.shields.io/badge/Vite-6-646CFF?logo=vite&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supabase-4169E1?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-API-2496ED?logo=docker&logoColor=white)
![Render](https://img.shields.io/badge/Render-API-46E3B7?logo=render&logoColor=black)
![Vercel](https://img.shields.io/badge/Vercel-Frontend-000000?logo=vercel&logoColor=white)

</div>

## Qué incluye

- **Portal de huéspedes:** registro, inicio de sesión, consulta de habitaciones disponibles, solicitud de reservas y cancelación de reservas propias.
- **Panel de administración:** calendario global, revisión y confirmación de solicitudes, y gestión de reservas.
- **Control de disponibilidad:** el inventario inicial tiene 80 habitaciones (101–120, 201–220, 301–320 y 401–420). La API comprueba disponibilidad antes de crear o actualizar una reserva.
- **Acceso por rol:** la API asigna y valida los roles `admin` y `user` mediante JWT. Las contraseñas de huéspedes se almacenan como hash.

## Arquitectura

~~~text
Navegador → Frontend Vite (Vercel) → API Flask (Render) → PostgreSQL (Supabase)
~~~

El frontend llama a la API por HTTPS; solo la API accede a la base de datos. Para desarrollo local, Flask puede usar SQLite si `DATABASE_URL` está vacía. La API se empaqueta con Docker y se publica manualmente en Render, sin GitHub Actions.

| Directorio | Contenido |
| --- | --- |
| `frontend/` | Interfaz Vite y configuración de Vercel |
| `api/` | API Flask, Dockerfile y script de migración |
| `docs/` | Guías de despliegue, Postman y entrega |

## Desarrollo local

**Requisitos:** Python 3.10 o superior y Node.js LTS. Los comandos siguientes usan PowerShell y se ejecutan desde la raíz del repositorio.

1. Prepara el entorno de la API:

   ~~~powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r api\requirements.txt
   Copy-Item .env.example .env
   ~~~

2. En `.env`, sustituye los valores de ejemplo de `API_SECRET_KEY`, `API_USERNAME` y `API_PASSWORD`. Deja `DATABASE_URL` vacía para usar SQLite local. Inicia Flask:

   ~~~powershell
   python api\run.py
   ~~~

3. En otra terminal, inicia el frontend:

   ~~~powershell
   cd frontend
   npm install
   Copy-Item .env.example .env
   npm run dev
   ~~~

Abre [http://localhost:5173](http://localhost:5173). Vite redirige `/login`, `/register`, `/reservas` y `/habitaciones` a Flask en `http://127.0.0.1:5000`. Si la API usa otra dirección local, configura `VITE_DEV_API_PROXY_TARGET` antes de iniciar Vite.

### Variables de entorno

| Variable | Dónde | Uso |
| --- | --- | --- |
| `API_SECRET_KEY` | API | Clave obligatoria para firmar JWT |
| `API_USERNAME` / `API_PASSWORD` | API | Credenciales obligatorias de administración |
| `DATABASE_URL` | API | URI PostgreSQL de Supabase; vacía para SQLite local |
| `CORS_ALLOWED_ORIGINS` | API | Orígenes del frontend permitidos, separados por comas |
| `VITE_API_BASE_URL` | Frontend en Vercel | URL HTTPS pública de la API en Render |
| `API_TOKEN_HOURS` | API, opcional | Duración del token; por defecto, 1 hora |
| `API_DB_PATH` | API local, opcional | Ruta del archivo SQLite |

Los archivos `.env.example` de la raíz y de `frontend/` contienen la configuración de referencia. No publiques `.env`, contraseñas ni la URI de PostgreSQL. Las variables `VITE_*` se incorporan al código del navegador; `VITE_API_BASE_URL` debe contener únicamente la URL pública de la API.

## Reservas y permisos

- Una cuenta nueva recibe el rol `user`. El administrador accede con las credenciales configuradas en la API.
- El huésped consulta y cancela únicamente sus propias reservas; el administrador gestiona todas. Los registros antiguos de SQLite sin cuenta asociada solo aparecen en el panel de administración.
- Las reservas `pendiente` y `confirmada` ocupan la habitación desde la fecha de entrada, incluida, hasta la fecha de salida, excluida. Las reservas canceladas liberan esas fechas.
- Si una reserva se cruza con otra para la misma habitación, la API responde con HTTP `409`. El calendario ayuda a visualizar las reservas; la validación final ocurre en la API.

## API principal

Las rutas protegidas requieren `Authorization: Bearer <token>`.

| Método | Ruta | Acceso |
| --- | --- | --- |
| `POST` | `/register` | Público; crea una cuenta de huésped |
| `POST` | `/login` | Público; inicia sesión |
| `GET` | `/health` | Público; estado del servicio |
| `GET` | `/habitaciones` | Usuario autenticado; inventario |
| `GET` | `/habitaciones/disponibles?fecha_entrada=AAAA-MM-DD&fecha_salida=AAAA-MM-DD` | Usuario autenticado; disponibilidad |
| `GET` | `/reservas` | Administrador: todas; huésped: propias |
| `GET` | `/reservas/{id}` | Administrador: cualquiera; huésped: propia |
| `POST` | `/reservas` | Administrador: crea; huésped: solicita |
| `PUT` | `/reservas/{id}` | Solo administrador |
| `DELETE` | `/reservas/{id}` | Administrador: elimina; huésped: cancela la propia |

Consulta la [guía de Postman](docs/guia_postman.md) para ejemplos de peticiones.

## Despliegue

1. **Supabase:** crea una base PostgreSQL y obtén su URI desde **Connect**. Guárdala como `DATABASE_URL` únicamente en la API.
2. **Render:** crea un Web Service Docker desde el repositorio, con `api` como directorio raíz, `Dockerfile` como Dockerfile, `.` como contexto de construcción y `/health` como ruta de salud. Configura `DATABASE_URL`, `API_SECRET_KEY`, `API_USERNAME`, `API_PASSWORD` y `CORS_ALLOWED_ORIGINS`.
3. **Vercel:** usa `frontend` como directorio raíz, `npm run build` como comando de construcción y `dist` como salida. Configura `VITE_API_BASE_URL` con la URL HTTPS de Render, sin ruta final.
4. **Verifica:** comprueba `/health`, el inicio de sesión, la disponibilidad y el guardado de una reserva desde el frontend.

Para mantener el despliegue manual de la API, desactiva **Auto-Deploy** en Render. La [guía de despliegue](docs/despliegue_render.md) detalla la configuración y las comprobaciones. El almacenamiento del contenedor de Render es efímero: usa PostgreSQL para los datos de producción.

### Migrar datos de SQLite a PostgreSQL

Si ya tienes datos locales que deseas conservar:

1. Haz una copia de seguridad del archivo SQLite y configura `DATABASE_URL` en tu `.env` local con la URI de Supabase.
2. Instala las dependencias con `pip install -r api/requirements.txt`.
3. Ejecuta `python api/scripts/migrate_sqlite_to_postgres.py` desde la raíz. Puedes pasar otra ruta SQLite como argumento.
4. Comprueba en PostgreSQL los usuarios, las reservas y el inventario antes de usar la API en producción.

El script conserva los IDs y hashes de contraseña, ajusta las secuencias y no modifica el archivo SQLite de origen.

## Documentación

- [Despliegue en Render, Supabase y Vercel](docs/despliegue_render.md)
- [Guía de pruebas con Postman](docs/guia_postman.md)
- [Resumen de la entrega](docs/ENTREGA.md)
- [Evidencias en Postman (PDF)](docs/Evidencias%20en%20POSTMAN.pdf)
