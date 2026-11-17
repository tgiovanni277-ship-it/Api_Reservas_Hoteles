FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    API_DB_PATH=/tmp/reservas_hotel.db \
    PORT=10000

WORKDIR /app

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt \
    && addgroup --system app \
    && adduser --system --ingroup app app

COPY --chown=app:app app ./app
COPY --chown=app:app run.py ./run.py

USER app
EXPOSE 10000

CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:${PORT:-10000} --workers 2 --access-logfile - --error-logfile - run:app"]
