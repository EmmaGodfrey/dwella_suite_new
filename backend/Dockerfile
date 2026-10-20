FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app/backend

RUN addgroup --gid 1000 app \
    && adduser --uid 1000 --gid 1000 --disabled-password --gecos "" app

COPY backend/requirements.txt ./requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY backend/ ./
COPY deploy/backend-entrypoint.sh /app/backend-entrypoint.sh

RUN mkdir -p /app/backend/media /app/backend/staticfiles \
    && chown -R app:app /app/backend /app/backend-entrypoint.sh

USER app

EXPOSE 8000

ENTRYPOINT ["sh", "/app/backend-entrypoint.sh"]

