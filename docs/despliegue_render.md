# Desplegar la API en Render

Esta guía publica únicamente la API Flask que vive en `api/`. El frontend continúa en Vercel y PostgreSQL en Supabase. Render importa el repo desde GitHub y construye la imagen usando el `Dockerfile`; no usamos GitHub Actions.

## 1. Antes de abrir Render

- Confirma que los cambios que quieres desplegar estén en una rama de GitHub. Render solo recibe los commits que ya subiste; los cambios locales sin commit/push no aparecen allí.
- Dockerfile: `api/Dockerfile`. Render debe usar `api/` como raíz y contexto de build.
- Asegúrate de que Supabase PostgreSQL tenga el esquema y los datos que necesitas. Si vienes de SQLite, sigue primero la migración descrita en el README y configura `DATABASE_URL` en Render.

## 2. Crear el Web Service desde GitHub

1. En Render Dashboard elige **New → Web Service** y conecta GitHub.
2. Selecciona este repositorio y la rama que quieras publicar.
3. Configura:

   - **Root Directory:** `api`
   - **Language / Runtime:** `Docker`
   - **Dockerfile Path:** `Dockerfile`
   - **Docker Build Context:** `.`
   - **Health Check Path:** `/health`
   - **Auto-Deploy:** `Off` si quieres lanzar cada publicación manualmente desde Render.

El Dockerfile escucha en `0.0.0.0:$PORT`; Render usa el puerto `10000` por defecto. Render soporta servicios Docker y permite indicar la ruta del Dockerfile para monorepos. [Docker on Render](https://render.com/docs/docker) · [Monorepo support](https://render.com/docs/monorepo-support) · [Web services and ports](https://render.com/docs/web-services)

Elige el plan disponible que quieras para la demo y crea el servicio. Render construirá la imagen y mostrará el build en **Events/Logs**. Cuando termine, entrega un dominio HTTPS parecido a `https://api-reservas-hotel.onrender.com`.

## 3. Configurar el entorno

En **Environment** del servicio agrega:

- `DATABASE_URL`: URI PostgreSQL de Supabase.
- `API_SECRET_KEY`: secreto aleatorio para firmar JWT.
- `API_USERNAME` y `API_PASSWORD`: credenciales del administrador de prueba.
- `CORS_ALLOWED_ORIGINS`: origen exacto de Vercel, por ejemplo `https://tu-frontend.vercel.app`.
- `FLASK_DEBUG`: `0`.

Guarda los cambios y deja que Render despliegue la revisión con esta configuración. No subas `.env` a GitHub ni copies la URI de Supabase en el frontend.

## 4. Conectar Vercel

En el proyecto frontend de Vercel configura `VITE_API_BASE_URL` con el dominio HTTPS asignado a Render, sin una ruta al final. Vercel debe reconstruir el frontend después de guardar la variable.

El navegador llamará, por ejemplo, a:

- `https://api-reservas-hotel.onrender.com/health`
- `https://api-reservas-hotel.onrender.com/login`
- `https://api-reservas-hotel.onrender.com/reservas`
- `https://api-reservas-hotel.onrender.com/habitaciones/disponibles?fecha_entrada=AAAA-MM-DD&fecha_salida=AAAA-MM-DD`

Las rutas protegidas requieren el JWT en `Authorization: Bearer <token>`.

## 5. Verificar la publicación

Abre la URL `/health`. Debe responder JSON con `status: ok`. Después comprueba login, consulta de disponibilidad y creación de una reserva con el frontend o Postman. Si algo falla, mira los logs del último deploy en Render y confirma que las variables estén completas y que `CORS_ALLOWED_ORIGINS` coincida con Vercel.

## Consideraciones del plan gratuito

En el plan gratuito, un Web Service sin tráfico durante 15 minutos se duerme y puede tardar alrededor de un minuto en responder al primer request posterior. El sistema de archivos del servicio también es efímero; por eso las reservas deben estar en Supabase PostgreSQL, no en el SQLite del contenedor. [Render free instances](https://render.com/docs/free)

Render puede desplegar automáticamente cada push por defecto. La opción `Auto-Deploy: Off` permite conservar el flujo manual y no depender de un pipeline. [Deploys and auto-deploy settings](https://render.com/docs/deploys)
