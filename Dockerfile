FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for Docker layer caching
COPY backend/requirements.txt ./requirements.txt

# Install all Python deps - ALL packages have prebuilt wheels, no gcc needed
RUN pip install --upgrade pip --no-cache-dir && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ ./
COPY frontend/ ./frontend/

# Create runtime directories
RUN mkdir -p uploads logs

EXPOSE 8000

# Use shell form so $PORT gets expanded from Render's environment
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --log-level info
