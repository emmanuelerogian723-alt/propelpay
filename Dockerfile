FROM python:3.11-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev curl && apt-get clean

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY backend/ .
COPY frontend/ ./frontend/

RUN mkdir -p uploads logs

EXPOSE 8000

CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --log-level info
